# Operations Guide

This guide covers production configuration, Kubernetes rollout, health checks, retention, and
dead-letter recovery. Replace every example hostname and secret before deployment.

## Release gate

Run the same checks enforced by CI:

```bash
uv sync --locked --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest --cov=audittrail_api
uv run alembic upgrade head
```

The PostgreSQL CI job applies every migration to PostgreSQL 17 and executes dialect-specific UUID,
relationship, transaction, and JSON-query checks. The container job separately verifies that the
runtime image builds from the lockfile.

## Kubernetes rollout

Create a real secret from `deploy/kubernetes/secret.example.yaml`; never apply the example values.
The export claim requests `ReadWriteMany`, so select a storage class that supports concurrent API
and worker mounts.

```bash
kubectl apply -f deploy/kubernetes/namespace.yaml
kubectl apply -f path/to/audittrail-secrets.yaml
kubectl apply -f deploy/kubernetes/configmap.yaml
kubectl apply -f deploy/kubernetes/exports-pvc.yaml
kubectl apply -f deploy/kubernetes/api-deployment.yaml
kubectl apply -f deploy/kubernetes/api-service.yaml
kubectl apply -f deploy/kubernetes/worker-deployment.yaml
kubectl apply -f deploy/kubernetes/ingress.yaml
kubectl apply -f deploy/kubernetes/autoscaling.yaml
kubectl apply -f deploy/kubernetes/disruption-budgets.yaml
```

Pin image digests in controlled environments. The API init container applies migrations before
pods become ready. Run only one migration job during high-risk schema releases if the migration is
not safe to execute concurrently.

## Health and metrics

- `GET /health/live` verifies that the process can answer HTTP requests.
- `GET /health/ready` checks PostgreSQL and Redis when rate limiting is enabled.
- `GET /metrics` exposes Prometheus data and requires the management bearer token.

Alert on sustained readiness failures, elevated request latency, HTTP 429 growth, worker queue
depth, failed Celery tasks, and increases in pending dead letters.

## Dead-letter recovery

Terminal Celery failures are stored once per task ID with JSON-safe arguments and the latest error.
Inspect pending records with the management token:

```bash
curl http://audittrail.example.com/api/v1/dead-letters?status=pending \
  -H "Authorization: Bearer $AUDITTRAIL_ADMIN_TOKEN"
```

Correct the underlying dependency or data problem before replay. Only explicitly allowlisted,
idempotent task types can be retried:

```bash
curl -X POST http://audittrail.example.com/api/v1/dead-letters/RECORD_ID/retry \
  -H "Authorization: Bearer $AUDITTRAIL_ADMIN_TOKEN"
```

The record is marked `retried` in the same request that dispatches the replacement task. A second
replay returns HTTP 409, preventing accidental duplicate execution.

## Retention execution

Use the retention preview before starting a run. Legal holds block deletion. Execution removes
only a contiguous, chain-safe event prefix and writes a checkpoint so subsequent integrity checks
can verify the surviving chain against its prior anchor. Investigate any failed run before retrying
or changing the policy.

## Rollback

Roll application deployments back with Kubernetes only when the prior image supports the current
database schema. Database downgrades are an explicit operator decision: back up PostgreSQL, stop
writers and workers, review the Alembic downgrade, and test restoration before changing production.
