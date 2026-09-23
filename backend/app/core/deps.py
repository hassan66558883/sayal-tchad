from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_error
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_error
    user = db.get(User, int(user_id))
    if user is None or not user.active:
        raise credentials_error
    # Stashed so app.services.audit's after_flush listener can attribute
    # any create/update/delete on this session to the acting user.
    db.info["current_user_id"] = user.id
    return user


def require_roles(*role_codes: str):
    """FastAPI dependency: 403s unless the user is a superuser or holds
    at least one of the given role codes. Mirrors the Odoo version's
    per-model res.groups restriction, applied per-route instead.
    """

    def _check(user: User = Depends(get_current_user)) -> User:
        if user.is_superuser:
            return user
        if not any(user.has_role(code) for code in role_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acces refuse : role metier requis manquant.",
            )
        return user

    return _check
