"""Management endpoints for tenants and source applications."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from audittrail_api.api.dependencies import AdminAccess, Session
from audittrail_api.organizations.models import Application, Organization
from audittrail_api.organizations.schemas import (
    ApplicationCreate,
    ApplicationRead,
    OrganizationCreate,
    OrganizationRead,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post("", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    session: Session,
    _: AdminAccess,
) -> Organization:
    organization = Organization(**payload.model_dump())
    session.add(organization)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Organization slug already exists.") from exc
    await session.refresh(organization)
    return organization


@router.get("", response_model=list[OrganizationRead])
async def list_organizations(
    session: Session,
    _: AdminAccess,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[Organization]:
    result = await session.scalars(select(Organization).order_by(Organization.name).limit(limit))
    return list(result)


@router.post(
    "/{organization_id}/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    organization_id: UUID,
    payload: ApplicationCreate,
    session: Session,
    _: AdminAccess,
) -> Application:
    if await session.get(Organization, organization_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organization was not found.")
    application = Application(organization_id=organization_id, **payload.model_dump())
    session.add(application)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Application slug already exists in this organization.",
        ) from exc
    await session.refresh(application)
    return application


@router.get("/{organization_id}/applications", response_model=list[ApplicationRead])
async def list_applications(
    organization_id: UUID,
    session: Session,
    _: AdminAccess,
) -> list[Application]:
    result = await session.scalars(
        select(Application)
        .where(Application.organization_id == organization_id)
        .order_by(Application.name)
    )
    return list(result)
