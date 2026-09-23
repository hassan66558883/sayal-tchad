"""Seeds the fixed set of business roles and the default company. Run once
per database (idempotent - safe to call on every app startup).
"""

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import Role, User
from app.services.company import get_default_company

ROLES: list[tuple[str, str]] = [
    ("direction_generale", "Direction generale"),
    ("achats", "Achats"),
    ("ventes", "Ventes"),
    ("stock", "Stock / Entrepot"),
    ("logistique", "Logistique / Distribution"),
    ("chauffeur", "Chauffeur"),
    ("comptable", "Comptable / Finance"),
    ("caissier", "Caissier"),
    ("rh", "Ressources humaines"),
    ("responsable_agence", "Responsable d'agence"),
]


def seed(db: Session) -> None:
    get_default_company(db)
    existing = {r.code for r in db.query(Role).all()}
    for code, label in ROLES:
        if code not in existing:
            db.add(Role(code=code, label=label))
    db.commit()

    if settings.admin_bootstrap_email and settings.admin_bootstrap_password:
        has_superuser = db.query(User).filter(User.is_superuser.is_(True)).count() > 0
        if not has_superuser:
            db.add(
                User(
                    name="Administrateur",
                    email=settings.admin_bootstrap_email,
                    hashed_password=hash_password(settings.admin_bootstrap_password),
                    is_superuser=True,
                )
            )
            db.commit()
