"""Row-level branch scoping, mirroring the Odoo version's ir.rule pattern:
a user holding ONLY the responsable_agence role (not direction_generale,
not superuser) sees only records tied to a branch they're assigned to -
and sees nothing at all if they have no branch assigned (secure-by-default,
same philosophy documented throughout the original project). Every other
role keeps the wider access already granted by its own route dependency.
"""

from sqlalchemy import Select
from sqlalchemy.orm import InstrumentedAttribute

from app.models.user import User

RESTRICTED_ROLE = "responsable_agence"
UNRESTRICTED_ROLES = {"direction_generale"}


def is_branch_restricted(user: User) -> bool:
    if user.is_superuser:
        return False
    role_codes = {r.code for r in user.roles}
    return RESTRICTED_ROLE in role_codes and not (role_codes & UNRESTRICTED_ROLES)


def scope_by_branch(stmt: Select, branch_id_column: InstrumentedAttribute, user: User) -> Select:
    if not is_branch_restricted(user):
        return stmt
    branch_ids = [b.id for b in user.branches]
    if not branch_ids:
        return stmt.where(branch_id_column.in_([]))  # no assignment -> sees nothing
    return stmt.where(branch_id_column.in_(branch_ids))
