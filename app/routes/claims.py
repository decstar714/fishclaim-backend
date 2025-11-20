from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles

router = APIRouter(prefix="/claims", tags=["claims"])
_reviewer_only = require_roles(models.UserRole.ADMIN.value, models.UserRole.REVIEWER.value)


def evaluate_claim_for_catch(db: Session, catch: models.Catch):
    current_claim: models.Claim | None = (
        db.query(models.Claim)
        .filter(
            models.Claim.zone_id == catch.zone_id,
            models.Claim.species_id == catch.species_id,
            models.Claim.is_active == True,
        )
        .one_or_none()
    )

    if current_claim and current_claim.length_cm >= catch.length_cm:
        return

    if current_claim:
        current_claim.is_active = False
        current_claim.revoked_at = datetime.utcnow()

    new_claim = models.Claim(
        user_id=catch.user_id,
        water_id=catch.water_id,
        zone_id=catch.zone_id,
        species_id=catch.species_id,
        catch_id=catch.id,
        length_cm=catch.length_cm,
        is_active=True,
        status=models.ClaimStatus.APPROVED.value,
    )
    db.add(new_claim)
    db.commit()


@router.get("/zone/{zone_id}", response_model=list[schemas.Claim])
def get_zone_claims(zone_id: int, db: Session = Depends(get_db)):
    claims = (
        db.query(models.Claim)
        .filter(
            and_(
                models.Claim.zone_id == zone_id,
            )
        )
        .order_by(models.Claim.created_at.desc())
        .all()
    )
    return claims


@router.post("/{claim_id}/status", response_model=schemas.Claim)
def update_claim_status(
    claim_id: int,
    status_in: schemas.ClaimStatusUpdate,
    db: Session = Depends(get_db),
    reviewer: models.User = Depends(_reviewer_only),
):
    claim = db.get(models.Claim, claim_id)
    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found")

    try:
        new_status = models.ClaimStatus(status_in.status)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    claim.status = new_status.value
    claim.review_notes = status_in.review_notes
    claim.reviewed_by_user_id = reviewer.id
    claim.reviewed_at = datetime.utcnow()
    claim.is_active = new_status == models.ClaimStatus.APPROVED
    if new_status != models.ClaimStatus.APPROVED:
        claim.revoked_at = datetime.utcnow()
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim
