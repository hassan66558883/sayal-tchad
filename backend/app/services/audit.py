"""Generic audit logging, mirroring the original seyal.audit.mixin design:
any model inheriting AuditedMixin gets one AuditLog row per insert/update/
delete automatically, without each router needing to remember to log it.

Implemented via a single Session-level after_flush listener (registered
once at app startup) rather than per-mapper events, since AuditedMixin
itself is not a mapped class - inspecting session.new/dirty/deleted lets
one listener cover every current and future audited model.
"""

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.mixins import AuditedMixin

_registered = False


def _record_name(instance) -> str | None:
    for attr in ("name", "reference", "label", "code"):
        value = getattr(instance, attr, None)
        if value:
            return str(value)
    return None


def _log(session: Session, instance, action: str) -> None:
    user_id = session.info.get("current_user_id")
    session.add(
        AuditLog(
            user_id=user_id,
            action=action,
            model_name=type(instance).__tablename__,
            record_id=instance.id,
            record_name=_record_name(instance),
        )
    )


def _after_flush(session: Session, _flush_context) -> None:
    for instance in session.new:
        if isinstance(instance, AuditedMixin) and not isinstance(instance, AuditLog):
            _log(session, instance, "create")
    for instance in session.dirty:
        if isinstance(instance, AuditedMixin) and session.is_modified(instance, include_collections=False):
            _log(session, instance, "update")
    for instance in session.deleted:
        if isinstance(instance, AuditedMixin):
            _log(session, instance, "delete")


def register_audit_listeners() -> None:
    global _registered
    if _registered:
        return
    event.listen(Session, "after_flush", _after_flush)
    _registered = True
