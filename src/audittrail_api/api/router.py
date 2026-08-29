"""Top-level API router."""

from fastapi import APIRouter

from audittrail_api.auth.router import router as auth_router
from audittrail_api.events.router import router as events_router
from audittrail_api.exports.router import router as exports_router
from audittrail_api.identity.auth_router import router as identity_auth_router
from audittrail_api.identity.membership_router import router as membership_router
from audittrail_api.identity.user_router import router as user_router
from audittrail_api.organizations.router import router as organizations_router
from audittrail_api.retention.router import router as retention_router

router = APIRouter(prefix="/api/v1")
router.include_router(organizations_router)
router.include_router(auth_router)
router.include_router(events_router)
router.include_router(retention_router)
router.include_router(exports_router)
router.include_router(user_router)
router.include_router(identity_auth_router)
router.include_router(membership_router)
