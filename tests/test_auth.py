import os

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_auth.db"

from app.main import app  # noqa: E402
from app import models  # noqa: E402
from app.auth import get_password_hash  # noqa: E402
from app.database import Base, engine, SessionLocal  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_user(username: str, password: str = "secret", role: str = "user"):
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


def login(client: TestClient, username: str, password: str):
    return client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def test_login_and_refresh_rotation():
    create_user("alice", password="pw123", role=models.UserRole.USER.value)
    client = TestClient(app)

    res = login(client, "alice", "pw123")
    assert res.status_code == 200
    tokens = res.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    refreshed = client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["access_token"] != tokens["access_token"]

    # Rotated refresh token cannot be reused
    reused = client.post(
        "/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reused.status_code == 401


def test_admin_guard_blocks_non_admin():
    create_user(
        "viewer",
        password="pw123",
        role=models.UserRole.VIEWER.value,
    )
    create_user(
        "admin",
        password="pw123",
        role=models.UserRole.ADMIN.value,
    )
    client = TestClient(app)

    viewer_login = login(client, "viewer", "pw123").json()
    res_viewer = client.get(
        "/api/auth/admin/ping",
        headers={"Authorization": f"Bearer {viewer_login['access_token']}"},
    )
    assert res_viewer.status_code == 403

    admin_login = login(client, "admin", "pw123").json()
    res_admin = client.get(
        "/api/auth/admin/ping",
        headers={"Authorization": f"Bearer {admin_login['access_token']}"},
    )
    assert res_admin.status_code == 200
    assert res_admin.json()["status"] == "ok"
