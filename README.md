# AuditTrail API

AuditTrail API is a production-oriented service for receiving, searching, and verifying
multi-tenant audit events. It is designed for security-sensitive applications that need a
durable record of who performed an action, what changed, and where the event originated.

The project currently includes a FastAPI application factory, asynchronous SQLAlchemy database
lifecycle, environment-driven configuration, and liveness and readiness checks. Organization,
application, API-key, and event workflows are developed as independent domain modules.

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

Local development uses SQLite by default. Copy `.env.example` to `.env` when you need to override
configuration. Production-like PostgreSQL and Redis services will be available through Docker
Compose as those modules are introduced.

## Architecture

The codebase follows a modular-monolith structure. Domain packages own their API routes, schemas,
services, and persistence models, while shared database and configuration modules remain small.
This keeps local development simple while preserving boundaries that can later support separate
workers or services.

See [docs/architecture.md](docs/architecture.md) for design decisions and trust boundaries.

## License

Released under the MIT License.
