"""Persistence model registry populated by domain modules."""

from audittrail_api.organizations.models import Application, Organization

__all__ = ["Application", "Organization"]
