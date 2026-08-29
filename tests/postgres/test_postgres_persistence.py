from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select

from audittrail_api.config import get_settings
from audittrail_api.database.session import session_factory
from audittrail_api.events.models import AuditEvent
from audittrail_api.organizations.models import Application, Organization

pytestmark = pytest.mark.postgres


@pytest.mark.asyncio
async def test_postgres_persists_uuid_relations_and_json_queries() -> None:
    if not get_settings().database_url.startswith("postgresql"):
        pytest.skip("PostgreSQL service is not configured")

    suffix = uuid4().hex[:10]
    organization = Organization(name="Postgres Contract", slug=f"postgres-{suffix}")
    application = Application(name="Contract Source", slug="contract", organization=organization)
    event = AuditEvent(
        organization_id=organization.id,
        application_id=application.id,
        external_id=uuid4(),
        occurred_at=datetime.now(UTC),
        actor_type="service",
        actor_id="postgres-contract",
        action="contract.checked",
        resource_type="database",
        resource_id=suffix,
        event_metadata={"severity": "critical", "attempt": 1},
        content_hash="a" * 64,
        event_hash="b" * 64,
    )

    async with session_factory() as session:
        session.add(organization)
        await session.flush()
        session.add(application)
        await session.flush()
        event.organization_id = organization.id
        event.application_id = application.id
        session.add(event)
        await session.commit()

        count = await session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.organization_id == organization.id,
                AuditEvent.event_metadata["severity"].as_string() == "critical",
            )
        )
        assert count == 1

        await session.execute(delete(AuditEvent).where(AuditEvent.id == event.id))
        await session.execute(delete(Application).where(Application.id == application.id))
        await session.execute(delete(Organization).where(Organization.id == organization.id))
        await session.commit()
