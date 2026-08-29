FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN groupadd --system audittrail && useradd --system --gid audittrail audittrail
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --locked --no-dev

USER audittrail
EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "audittrail_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
