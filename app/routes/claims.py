from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/claims", tags=["claims"])


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

    new_claim = models.Claim(
        user_id=catch.user_id,
        water_id=catch.water_id,
        zone_id=catch.zone_id,
        species_id=catch.species_id,
        catch_id=catch.id,
        length_cm=catch.length_cm,
        is_active=True,
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
                models.Claim.is_active == True,
            )
        )
        .all()
    )
    return claims

