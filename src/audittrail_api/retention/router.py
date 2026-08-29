"""Administrative retention-policy endpoints."""

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from audittrail_api.api.dependencies import AdminAccess, Session
from audittrail_api.database.mixins import utc_now
from audittrail_api.organizations.models import Organization
from audittrail_api.retention.models import RetentionPolicy
from audittrail_api.retention.schemas import (
    ApplicationRetentionPreview,
    RetentionPolicyRead,
    RetentionPolicyUpdate,
    RetentionPreview,
)
from audittrail_api.retention.service import build_retention_plan

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


@router.get("/{organization_id}/retention/preview", response_model=RetentionPreview)
async def preview_retention(
    organization_id: UUID,
    session: Session,
    _: AdminAccess,
) -> RetentionPreview:
    policy = await session.scalar(
        select(RetentionPolicy).where(RetentionPolicy.organization_id == organization_id)
    )
    if policy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Retention policy was not found.")
    cutoff_at = utc_now() - timedelta(days=policy.retention_days)
    plans = (
        [] if policy.legal_hold else await build_retention_plan(session, organization_id, cutoff_at)
    )
    applications = [
        ApplicationRetentionPreview(
            application_id=plan.application_id,
            candidate_count=len(plan.event_ids),
            anchor_hash=plan.anchor_hash,
        )
        for plan in plans
    ]
    return RetentionPreview(
        organization_id=organization_id,
        cutoff_at=cutoff_at,
        legal_hold=policy.legal_hold,
        candidate_count=sum(item.candidate_count for item in applications),
        applications=applications,
    )


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
