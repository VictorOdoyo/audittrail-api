"""Organization membership provisioning and role management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from audittrail_api.api.dependencies import AdminAccess, Session
from audittrail_api.identity.dependencies import require_roles
from audittrail_api.identity.models import Membership, User
from audittrail_api.identity.schemas import (
    MembershipCreate,
    MembershipRead,
    MembershipUpdate,
)
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


@router.get("/{organization_id}/members", response_model=list[MembershipRead])
async def list_memberships(
    organization_id: UUID,
    session: Session,
    _: Annotated[
        Membership,
        Depends(require_roles("owner", "administrator", "auditor")),
    ],
) -> list[Membership]:
    memberships = await session.scalars(
        select(Membership)
        .where(Membership.organization_id == organization_id)
        .order_by(Membership.created_at)
    )
    return list(memberships)


@router.patch(
    "/{organization_id}/members/{membership_id}",
    response_model=MembershipRead,
)
async def update_membership_role(
    organization_id: UUID,
    membership_id: UUID,
    payload: MembershipUpdate,
    session: Session,
    _: Annotated[Membership, Depends(require_roles("owner"))],
) -> Membership:
    membership = await session.scalar(
        select(Membership).where(
            Membership.id == membership_id,
            Membership.organization_id == organization_id,
        )
    )
    if membership is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Membership was not found.")
    membership.role = payload.role
    await session.commit()
    await session.refresh(membership)
    return membership
