# Security policy

## Reporting a vulnerability

Please do not open a public issue for suspected vulnerabilities. Use GitHub's private vulnerability
reporting feature for this repository and include the affected endpoint, reproduction conditions,
impact, and any suggested mitigation.

## Supported version

Security fixes currently target the latest commit on `main`.

## Security assumptions

- Management tokens and API-key peppers are supplied through a secret manager in production.
- TLS is terminated by the deployment ingress or reverse proxy.
- PostgreSQL and Redis are not exposed to the public internet.
- Export storage is private and protected by the same application authorization boundary.
- Production schema changes are applied through reviewed Alembic migrations.

The Compose credentials are development-only and must never be reused in a deployed environment.
