import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_claim_lifecycle.db"

from app.main import app  # noqa: E402
from app import models  # noqa: E402
from app.auth import get_password_hash  # noqa: E402
from app.database import Base, engine, SessionLocal  # noqa: E402
from app.routes.claims import evaluate_claim_for_catch  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_user(username: str, password: str = "pw123", role: str = models.UserRole.USER.value):
    db = SessionLocal()
    user = models.User(
        email=f"{username}@example.com",
        username=username,
        password_hash=get_password_hash(password),
        display_name=username,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def create_world():
    db = SessionLocal()
    water = models.Water(name="Test River", type="river", region="XX")
    db.add(water)
    db.flush()
    zone = models.Zone(water_id=water.id, name="Test Zone", order_index=1)
    db.add(zone)
    db.flush()
    species = models.Species(common_name="Test Fish", scientific_name="Fishus testus")
    db.add(species)
    db.commit()
    db.refresh(zone)
    db.refresh(species)
    db.refresh(water)
    db.close()
    return water, zone, species


def login(client: TestClient, username: str, password: str):
    return client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def test_claim_created_as_approved():
    angler = create_user("angler")
    water, zone, species = create_world()
    db = SessionLocal()
    catch = models.Catch(
        user_id=angler.id,
        water_id=water.id,
        zone_id=zone.id,
        species_id=species.id,
        length_cm=15.0,
    )
    db.add(catch)
    db.commit()
    db.refresh(catch)

    evaluate_claim_for_catch(db, catch)
    claim = db.query(models.Claim).one()
    assert claim.status == models.ClaimStatus.APPROVED.value
    assert claim.is_active is True
    db.close()


def test_reviewer_can_reject_claim():
    angler = create_user("angler")
    reviewer = create_user("reviewer", role=models.UserRole.REVIEWER.value)
    water, zone, species = create_world()
    db = SessionLocal()
    catch = models.Catch(
        user_id=angler.id,
        water_id=water.id,
        zone_id=zone.id,
        species_id=species.id,
        length_cm=20.0,
    )
    db.add(catch)
    db.commit()
    db.refresh(catch)
    evaluate_claim_for_catch(db, catch)
    claim = db.query(models.Claim).one()
    db.close()

    client = TestClient(app)
    reviewer_tokens = login(client, reviewer.username, "pw123").json()

    res = client.post(
        f"/api/claims/{claim.id}/status",
        json={"status": "rejected", "review_notes": "Too small"},
        headers={"Authorization": f"Bearer {reviewer_tokens['access_token']}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "rejected"
    assert data["is_active"] is False
    assert data["review_notes"] == "Too small"
    assert data["reviewed_by_user_id"] == reviewer.id
