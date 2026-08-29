# API map

Interactive OpenAPI documentation is served at `/docs`; the machine-readable schema is available
at `/openapi.json`.

## Management authentication

Management endpoints require `Authorization: Bearer <AUDITTRAIL_ADMIN_TOKEN>`.

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/organizations` | Create an organization |
| GET | `/api/v1/organizations` | List organizations |
| POST | `/api/v1/organizations/{id}/applications` | Register an event source |
| GET | `/api/v1/organizations/{id}/applications` | List event sources |
| POST | `/api/v1/applications/{id}/api-keys` | Issue a scoped API key |
| GET | `/api/v1/applications/{id}/api-keys` | List key metadata |
| DELETE | `/api/v1/applications/{id}/api-keys/{key_id}` | Revoke a key |
| GET | `/api/v1/organizations/{id}/retention` | Read retention policy |
| PUT | `/api/v1/organizations/{id}/retention` | Create or update retention policy |

## Application authentication

Application endpoints require `X-API-Key`. Every key is bound to one source application.

| Method | Path | Required scope | Purpose |
| --- | --- | --- | --- |
| POST | `/api/v1/events` | `events:write` | Ingest one event |
| POST | `/api/v1/events/batch` | `events:write` | Ingest up to 100 events |
| GET | `/api/v1/events` | `events:read` | Search application events |
| GET | `/api/v1/events/{id}` | `events:read` | Retrieve one event |
| GET | `/api/v1/events/verify-chain` | `events:read` | Verify application hash chain |
| POST | `/api/v1/exports` | `exports:write` | Request a JSON or CSV export |
| GET | `/api/v1/exports/{id}` | `exports:write` | Read export status |
| GET | `/api/v1/exports/{id}/download` | `exports:write` | Download a completed export |

## Operational endpoints

`/health/live` confirms the process is serving requests. `/health/ready` also checks database
connectivity. Responses include `X-Request-ID`; callers may provide their own bounded identifier.
