import hashlib
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from . import models

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Be defensive: if hash is malformed (e.g. old seed user), just treat as invalid
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user: models.User, expires_delta: Optional[timedelta] = None
) -> str:
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {
        "sub": str(user.id),
        "type": "access",
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def build_refresh_token(
    user: models.User,
    expires_delta: Optional[timedelta] = None,
) -> Tuple[str, models.RefreshToken]:
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_token(raw_token)
    expires_at = datetime.utcnow() + (
        expires_delta or timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    )
    token_model = models.RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    return raw_token, token_model


def persist_refresh_token(db: Session, token_model: models.RefreshToken) -> None:
    db.add(token_model)
    db.commit()
    db.refresh(token_model)


def rotate_refresh_token(
    db: Session, raw_refresh_token: str
) -> Tuple[models.User, str]:
    token_hash = hash_token(raw_refresh_token)
    stored = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == token_hash)
        .one_or_none()
    )
    now = datetime.utcnow()
    if (
        stored is None
        or stored.revoked
        or stored.expires_at < now
        or stored.user is None
    ):
        raise ValueError("Invalid or expired refresh token")

    stored.revoked = True
    user = stored.user
    new_raw, new_model = build_refresh_token(user)
    stored.replaced_by_token_hash = new_model.token_hash
    db.add_all([stored, new_model])
    db.commit()
    db.refresh(new_model)
    return user, new_raw
