from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.notifications import get_notifications

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def read_notifications(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    return get_notifications(db)
