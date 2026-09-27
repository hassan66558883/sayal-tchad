from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserRead
from app.services.auth_security import LOCKOUT_MINUTES, is_locked, record_failed_login, record_successful_login

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    invalid_credentials = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou mot de passe incorrect.",
    )
    user = db.query(User).filter(User.email == form_data.username).one_or_none()
    if user is None or not user.active:
        raise invalid_credentials
    if is_locked(user):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Compte verrouille suite a trop de tentatives. Reessayez dans {LOCKOUT_MINUTES} minutes.",
        )
    if not verify_password(form_data.password, user.hashed_password):
        record_failed_login(user)
        db.commit()
        raise invalid_credentials
    record_successful_login(user)
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token(subject=str(user.id))
    return Token(access_token=token)


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
