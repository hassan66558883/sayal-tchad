from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)

user_branches = Table(
    "user_branches",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("branch_id", ForeignKey("branches.id"), primary_key=True),
)


class Role(Base):
    """Business roles, seeded once (see app.services.seed). Fixed set of
    10 codes matching the original role list: direction_generale, achats,
    ventes, stock, logistique, chauffeur, comptable, caissier, rh,
    responsable_agence.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    label: Mapped[str] = mapped_column(String(255))


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    roles = relationship("Role", secondary=user_roles)
    branches = relationship("Branch", secondary=user_branches)

    def has_role(self, code: str) -> bool:
        return any(r.code == code for r in self.roles)
