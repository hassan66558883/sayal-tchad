from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_roles
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogRead

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    model_name: str | None = Query(default=None),
    record_id: int | None = Query(default=None),
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles("direction_generale")),
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if model_name:
        stmt = stmt.where(AuditLog.model_name == model_name)
    if record_id is not None:
        stmt = stmt.where(AuditLog.record_id == record_id)
    return db.execute(stmt).scalars().all()
