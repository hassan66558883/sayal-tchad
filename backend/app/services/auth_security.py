"""Brute-force login protection: after MAX_FAILED_ATTEMPTS wrong
passwords in a row, the account is locked for LOCKOUT_MINUTES - even
against the correct password - so a script guessing passwords cannot
simply retry forever. A successful login always resets the counter.
"""

from datetime import datetime, timedelta, timezone

from app.models.user import User

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def is_locked(user: User) -> bool:
    return user.locked_until is not None and user.locked_until > datetime.now(timezone.utc)


def record_failed_login(user: User) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)


def record_successful_login(user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
