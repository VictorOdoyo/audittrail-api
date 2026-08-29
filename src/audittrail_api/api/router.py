"""Top-level API router."""

from fastapi import APIRouter

from audittrail_api.organizations.router import router as organizations_router

router = APIRouter(prefix="/api/v1")
router.include_router(organizations_router)
