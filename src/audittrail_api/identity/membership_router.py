"""Organization membership provisioning and role management."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from audittrail_api.api.dependencies import AdminAccess, Session
from audittrail_api.identity.models import Membership, User
from audittrail_api.identity.schemas import MembershipCreate, MembershipRead
from audittrail_api.organizations.models import Organization

router = APIRouter(prefix="/organizations", tags=["memberships"])


@router.post(
    "/{organization_id}/members",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
)
async def bootstrap_membership(
    organization_id: UUID,
    payload: MembershipCreate,
    session: Session,
    _: AdminAccess,
) -> Membership:
    if await session.get(Organization, organization_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization was not found.")
    if await session.get(User, payload.user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User was not found.")
    membership = Membership(
        organization_id=organization_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    session.add(membership)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "The user already belongs to this organization.",
        ) from exc
    await session.refresh(membership)
    return membership
