# Contributing

## Development workflow

1. Create a focused branch from `main`.
2. Run `uv sync` to install the locked environment.
3. Keep domain behavior inside its owning package under `src/audittrail_api`.
4. Add tests for successful behavior, authorization, validation, and failure recovery.
5. Run all local quality checks before opening a pull request.

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest --cov=audittrail_api
```

Schema changes require an Alembic migration that upgrades from the current head and downgrades
cleanly. Do not include secrets, generated export files, local databases, or unrelated refactors.

Commit messages should describe one reviewable behavior, for example:

```text
feat: reject conflicting idempotent event retries
test: cover revoked ingestion credentials
docs: explain production migration workflow
```
