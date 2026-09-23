from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditedMixin(TimestampMixin):
    """Marks a model for automatic seyal.audit.log-style tracking.

    Models mixing this in get created_by/updated_by columns, and are
    included in the SQLAlchemy event listeners registered in
    app.services.audit (which write one AuditLog row per insert/update/
    delete), mirroring the Odoo version's seyal.audit.mixin without
    needing every router to remember to call it manually.
    """

    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    updated_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
