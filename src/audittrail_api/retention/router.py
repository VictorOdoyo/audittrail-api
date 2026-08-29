"""Administrative retention-policy endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from audittrail_api.api.dependencies import AdminAccess, Session
from audittrail_api.organizations.models import Organization
from audittrail_api.retention.models import RetentionPolicy
from audittrail_api.retention.schemas import RetentionPolicyRead, RetentionPolicyUpdate

router = APIRouter(prefix="/organizations", tags=["retention"])


@router.get("/{organization_id}/retention", response_model=RetentionPolicyRead)
async def get_retention_policy(
    organization_id: UUID,
    session: Session,
    _: AdminAccess,
) -> RetentionPolicy:
    policy = await session.scalar(
        select(RetentionPolicy).where(RetentionPolicy.organization_id == organization_id)
    )
    if policy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Retention policy was not found.")
    return policy


@router.put("/{organization_id}/retention", response_model=RetentionPolicyRead)
async def update_retention_policy(
    organization_id: UUID,
    payload: RetentionPolicyUpdate,
    session: Session,
    _: AdminAccess,
) -> RetentionPolicy:
    if await session.get(Organization, organization_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization was not found.")
    policy = await session.scalar(
        select(RetentionPolicy).where(RetentionPolicy.organization_id == organization_id)
    )
    if policy is None:
        policy = RetentionPolicy(organization_id=organization_id, **payload.model_dump())
        session.add(policy)
    else:
        for field, value in payload.model_dump().items():
            setattr(policy, field, value)
    await session.commit()
    await session.refresh(policy)
    return policy
