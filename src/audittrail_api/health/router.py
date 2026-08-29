"""Liveness and readiness endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from audittrail_api.database.session import get_session

router = APIRouter(tags=["health"])
Session = Annotated[AsyncSession, Depends(get_session)]


class HealthResponse(BaseModel):
    status: str
    database: str | None = None


@router.get("/health/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Confirm the application process can serve requests."""

    return HealthResponse(status="ok")


@router.get("/health/ready", response_model=HealthResponse)
async def readiness(session: Session) -> HealthResponse:
    """Confirm the database dependency is reachable."""

    await session.execute(text("SELECT 1"))
    return HealthResponse(status="ready", database="reachable")
