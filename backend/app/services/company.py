from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.company import Company


def get_default_company(db: Session) -> Company:
    company = db.query(Company).filter(Company.name == settings.company_name).one_or_none()
    if company is None:
        company = Company(name=settings.company_name, currency=settings.company_currency, country="Tchad")
        db.add(company)
        db.commit()
        db.refresh(company)
    return company
