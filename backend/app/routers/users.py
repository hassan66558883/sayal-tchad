from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.models.user import Role, User
from app.schemas.auth import UserCreate, UserRead

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
):
    return db.query(User).all()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
):
    if db.query(User).filter(User.email == payload.email).count():
        raise HTTPException(status_code=400, detail="Cet email est deja utilise.")
    roles = db.query(Role).filter(Role.code.in_(payload.role_codes)).all()
    found_codes = {r.code for r in roles}
    unknown = set(payload.role_codes) - found_codes
    if unknown:
        raise HTTPException(status_code=400, detail=f"Roles inconnus : {', '.join(sorted(unknown))}")
    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        roles=roles,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserRead)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if user_id != current_user.id and not current_user.is_superuser and not current_user.has_role("direction_generale"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acces refuse.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return user
