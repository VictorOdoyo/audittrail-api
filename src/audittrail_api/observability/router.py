"""Operational metrics endpoint."""

from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from audittrail_api.api.dependencies import AdminAccess

router = APIRouter(tags=["operations"])


@router.get("/metrics", include_in_schema=False)
async def metrics(_: AdminAccess) -> Response:
    """Return Prometheus exposition data to authenticated scrapers."""

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
