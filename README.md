# AuditTrail API

AuditTrail API is a production-oriented service for receiving, searching, exporting, and
verifying multi-tenant audit events. It is designed for security-sensitive applications that need
a durable record of who performed an action, what changed, and where the event originated.

## Capabilities

- Organization and source-application provisioning
- Scoped API keys whose raw secrets are returned only once
- Single and bounded-batch event ingestion
- Idempotent retries with conflicting-payload detection
- Per-application SHA-256 hash chains and integrity verification
- Tenant-scoped filtering and cursor pagination
- Persisted JSON and CSV export jobs
- Inline local exports and retrying Celery worker dispatch in Docker
- Retention windows and legal holds
- Consistent problem responses and request correlation IDs
- Liveness, readiness, migrations, coverage enforcement, and container CI

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop for the PostgreSQL and Redis development stack

## Local development

```bash
uv sync
uv run audittrail-api
```

OpenAPI documentation is available at `http://127.0.0.1:8000/docs`.

Run the quality checks:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest --cov=audittrail_api
```

Local development uses SQLite and inline export generation by default. No private credentials or
external services are required.

## Docker development stack

Start the API, PostgreSQL, Redis, and Celery worker:

```bash
docker compose up --build
```

The API is available on `http://localhost:8000`. Docker uses the management token
`local-compose-admin-token`; it is intentionally limited to the local Compose profile.

## Five-minute walkthrough

Create an organization:

```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Authorization: Bearer local-compose-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Northstar Security","slug":"northstar-security"}'
```

Use the returned organization ID to create an application, then issue a key:

```bash
curl -X POST http://localhost:8000/api/v1/organizations/ORG_ID/applications \
  -H "Authorization: Bearer local-compose-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Access Console","slug":"access-console"}'

curl -X POST http://localhost:8000/api/v1/applications/APP_ID/api-keys \
  -H "Authorization: Bearer local-compose-admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Production writer","scopes":["events:write","events:read","exports:write"]}'
```

Store the returned `secret`; it cannot be retrieved again. Submit an event using that secret:

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "X-API-Key: API_KEY_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"169d0dc4-9c0d-44f5-9a23-34f4aa1583e0",
    "occurred_at":"2026-08-29T12:00:00Z",
    "actor_type":"user",
    "actor_id":"user-42",
    "action":"invoice.approved",
    "resource_type":"invoice",
    "resource_id":"inv-100",
    "metadata":{"amount":7500,"currency":"USD"}
  }'
```

## Database migrations

Production disables automatic schema creation. Apply migrations before starting the API:

```bash
uv run alembic upgrade head
```

Create a migration after changing models:

```bash
uv run alembic revision --autogenerate -m "describe the schema change"
```

## Architecture

The codebase follows a modular-monolith structure. Domain packages own their API routes, schemas,
services, and persistence models, while shared database and configuration modules remain small.
This keeps local development simple while preserving boundaries that can later support separate
workers or services.

See [docs/architecture.md](docs/architecture.md) for design decisions and trust boundaries and
[docs/api.md](docs/api.md) for the endpoint map and authentication requirements.

## Production configuration

Set at least these environment variables:

- `AUDITTRAIL_ENVIRONMENT=production`
- `AUDITTRAIL_DATABASE_URL`
- `AUDITTRAIL_ADMIN_TOKEN`
- `AUDITTRAIL_API_KEY_PEPPER`
- `AUDITTRAIL_AUTO_CREATE_SCHEMA=false`
- `AUDITTRAIL_REDIS_URL`
- `AUDITTRAIL_EXPORT_DISPATCH_MODE=celery`

The application refuses known development secrets and automatic schema creation in production.

## License

Released under the MIT License.
