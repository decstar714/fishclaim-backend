from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
    build_refresh_token,
    create_access_token,
    get_password_hash,
    persist_refresh_token,
    rotate_refresh_token,
    verify_password,
)
from ..deps import get_current_user, require_roles

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.User)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(models.User)
        .filter(
            (models.User.email == user_in.email)
            | (models.User.username == user_in.username)
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email or username already in use")

    user = models.User(
        email=user_in.email,
        username=user_in.username,
        display_name=user_in.display_name or user_in.username,
        password_hash=get_password_hash(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.TokenPair)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.username == form_data.username)
        .first()
    )
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        user=user, expires_delta=access_token_expires
    )
    refresh_raw, refresh_model = build_refresh_token(
        user=user, expires_delta=refresh_token_expires
    )
    persist_refresh_token(db, refresh_model)

    return schemas.TokenPair(access_token=access_token, refresh_token=refresh_raw)


@router.post("/refresh", response_model=schemas.TokenPair)
def refresh_tokens(
    payload: schemas.RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    try:
        user, new_refresh_raw = rotate_refresh_token(db, payload.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = create_access_token(
        user=user, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return schemas.TokenPair(access_token=access_token, refresh_token=new_refresh_raw)


@router.get("/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/admin/ping")
def admin_healthcheck(
    _: models.User = Depends(require_roles(models.UserRole.ADMIN.value)),
):
    return {"status": "ok"}
