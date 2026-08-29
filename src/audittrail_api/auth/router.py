"""Administrative API-key lifecycle endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from audittrail_api.api.dependencies import AdminAccess, RuntimeSettings, Session
from audittrail_api.auth.models import APIKey
from audittrail_api.auth.schemas import APIKeyCreate, APIKeyIssued, APIKeyRead
from audittrail_api.auth.security import generate_api_key
from audittrail_api.database.mixins import utc_now
from audittrail_api.organizations.models import Application

router = APIRouter(prefix="/applications", tags=["api keys"])


@router.post(
    "/{application_id}/api-keys",
    response_model=APIKeyIssued,
    status_code=status.HTTP_201_CREATED,
)
async def issue_api_key(
    application_id: UUID,
    payload: APIKeyCreate,
    session: Session,
    settings: RuntimeSettings,
    _: AdminAccess,
) -> APIKeyIssued:
    application = await session.get(Application, application_id)
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Application was not found.")
    generated = generate_api_key(settings.api_key_pepper)
    stored_key = APIKey(
        organization_id=application.organization_id,
        application_id=application.id,
        name=payload.name,
        prefix=generated.prefix,
        secret_digest=generated.digest,
        scopes=list(payload.scopes),
    )
    session.add(stored_key)
    await session.commit()
    await session.refresh(stored_key)
    return APIKeyIssued(
        id=stored_key.id,
        name=stored_key.name,
        prefix=stored_key.prefix,
        scopes=stored_key.scopes,
        secret=generated.raw,
        created_at=stored_key.created_at,
    )


@router.get("/{application_id}/api-keys", response_model=list[APIKeyRead])
async def list_api_keys(
    application_id: UUID,
    session: Session,
    _: AdminAccess,
) -> list[APIKey]:
    keys = await session.scalars(
        select(APIKey).where(APIKey.application_id == application_id).order_by(APIKey.created_at)
    )
    return list(keys)


@router.delete("/{application_id}/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    application_id: UUID,
    key_id: UUID,
    session: Session,
    _: AdminAccess,
) -> None:
    stored_key = await session.scalar(
        select(APIKey).where(APIKey.id == key_id, APIKey.application_id == application_id)
    )
    if stored_key is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key was not found.")
    if stored_key.revoked_at is None:
        stored_key.revoked_at = utc_now()
        await session.commit()
