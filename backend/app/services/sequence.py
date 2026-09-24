"""Generates human-readable, auto-incrementing references (PRD000001,
CLI000001, ...), the same role ir.sequence played throughout the Odoo
version. SELECT ... FOR UPDATE on the counter row makes concurrent
creates within the same transaction safe without a separate DB sequence
object per series.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sequence import SequenceCounter


def next_reference(db: Session, code: str, prefix: str, padding: int = 6) -> str:
    counter = db.execute(
        select(SequenceCounter).where(SequenceCounter.code == code).with_for_update()
    ).scalar_one_or_none()
    if counter is None:
        counter = SequenceCounter(code=code, prefix=prefix, next_number=1, padding=padding)
        db.add(counter)
        db.flush()
    number = counter.next_number
    counter.next_number = number + 1
    db.flush()
    return f"{prefix}{number:0{counter.padding}d}"
