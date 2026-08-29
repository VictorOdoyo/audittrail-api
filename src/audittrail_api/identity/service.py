"""Transactional user identity workflows."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from audittrail_api.database.mixins import utc_now
from audittrail_api.identity.models import User
from audittrail_api.identity.passwords import (
    consume_dummy_verification,
    hash_password,
    verify_password,
)
from audittrail_api.identity.schemas import UserCreate


class DuplicateEmailError(ValueError):
    pass


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    user = User(
        email=str(payload.email).lower(),
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise DuplicateEmailError("A user with this email already exists.") from exc
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await session.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        consume_dummy_verification(password)
        return None
    valid, replacement_hash = verify_password(password, user.password_hash)
    if not valid or not user.is_active:
        return None
    if replacement_hash:
        user.password_hash = replacement_hash
    user.last_login_at = utc_now()
    await session.commit()
    await session.refresh(user)
    return user
