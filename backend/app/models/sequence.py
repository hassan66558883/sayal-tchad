from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SequenceCounter(Base):
    """Backing store for app.services.sequence.next_reference(): one row
    per reference series (e.g. "product" -> "PRD000001", "PRD000002", ...).
    """

    __tablename__ = "sequence_counters"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    prefix: Mapped[str] = mapped_column(String(20))
    next_number: Mapped[int] = mapped_column(default=1)
    padding: Mapped[int] = mapped_column(default=6)
