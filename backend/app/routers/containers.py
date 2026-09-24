from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.import_ import Container
from app.models.user import User
from app.schemas.import_ import ContainerCreate, ContainerRead

PURCHASE_MANAGERS = ("achats", "direction_generale")

router = APIRouter(prefix="/api/containers", tags=["containers"])


@router.get("", response_model=list[ContainerRead])
def list_containers(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Container).all()


@router.post("", response_model=ContainerRead, status_code=status.HTTP_201_CREATED)
def create_container(
    payload: ContainerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*PURCHASE_MANAGERS)),
):
    if db.query(Container).filter(Container.number == payload.number).count():
        raise HTTPException(status_code=400, detail="Ce numero de conteneur existe deja.")
    container = Container(**payload.model_dump())
    db.add(container)
    db.commit()
    db.refresh(container)
    return container
