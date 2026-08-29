# Changelog

All notable changes to this project are documented in this file.

## 1.0.0 - 2026-08-29

### Added

- Multi-tenant organizations, source applications, scoped API keys, JWT users, and role-based
  organization memberships.
- Idempotent single and batch ingestion with tenant-scoped search, cursor pagination, and
  tamper-evident per-application hash chains.
- JSON and CSV exports, Celery execution, retry policies, durable dead letters, and guarded replay.
- Retention previews, legal holds, asynchronous execution, and chain integrity checkpoints.
- Redis-backed rate limits, request correlation, structured logs, Prometheus metrics, and
  dependency-aware health endpoints.
- Alembic migrations, PostgreSQL integration tests, Docker Compose, Kubernetes workloads,
  autoscaling, disruption budgets, and GitHub Actions quality gates.

### Security

- Argon2 password hashing, short-lived signed JWTs, constant-time management-token checks, API-key
  hashing with a server-side pepper, explicit production secret validation, and non-root containers.
