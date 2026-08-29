"""Management endpoints for human users."""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from audittrail_api.api.dependencies import AdminAccess, Session
from audittrail_api.identity.models import User
from audittrail_api.identity.schemas import UserCreate, UserRead
from audittrail_api.identity.service import DuplicateEmailError, create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def provision_user(
    payload: UserCreate,
    session: Session,
    _: AdminAccess,
) -> User:
    try:
        return await create_user(session, payload)
    except DuplicateEmailError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.get("", response_model=list[UserRead])
async def list_users(
    session: Session,
    _: AdminAccess,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[User]:
    users = await session.scalars(select(User).order_by(User.email).limit(limit))
    return list(users)
