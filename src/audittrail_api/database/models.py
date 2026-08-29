"""Persistence model registry populated by domain modules."""

from audittrail_api.auth.models import APIKey
from audittrail_api.events.models import AuditEvent
from audittrail_api.organizations.models import Application, Organization

__all__ = ["APIKey", "Application", "AuditEvent", "Organization"]
