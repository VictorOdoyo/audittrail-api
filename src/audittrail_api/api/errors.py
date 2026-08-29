"""Consistent, non-leaking API error responses."""

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    request_id: str
    errors: list[dict[str, Any]] | None = None


def request_id_from(request: Request) -> str:
    return str(getattr(request.state, "request_id", "unavailable"))


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
    problem = ProblemDetail(
        title="Request failed",
        status=exc.status_code,
        detail=detail,
        request_id=request_id_from(request),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(exclude_none=True),
        headers=exc.headers,
        media_type="application/problem+json",
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    errors = [
        {
            "location": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "code": error["type"],
        }
        for error in exc.errors()
    ]
    problem = ProblemDetail(
        title="Validation failed",
        status=422,
        detail="One or more request fields are invalid.",
        request_id=request_id_from(request),
        errors=errors,
    )
    return JSONResponse(
        status_code=422,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
