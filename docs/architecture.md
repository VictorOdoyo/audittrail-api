# Architecture

AuditTrail API is a modular monolith with explicit domain boundaries. It runs as one API process
and one worker process, backed by PostgreSQL and Redis in production-like environments.

## Trust boundaries

- Administrative endpoints require a separate management credential.
- Ingestion credentials are scoped to one organization and application.
- Raw API-key secrets are returned once and only a derived digest is stored.
- All event queries are constrained by organization and application ownership.
- Audit event payloads are immutable after acceptance.

## Runtime flow

1. The API validates request contracts and authentication.
2. Domain services apply authorization and business invariants.
3. Repositories perform transactional persistence.
4. Background work is queued only after durable state is committed.
5. Health endpoints expose dependency readiness without leaking secrets.

SQLite keeps initial local startup self-contained. PostgreSQL is the deployment database and is
used by the Docker and integration-test profiles.
