"""Request correlation middleware."""

from collections.abc import Awaitable, Callable
from uuid import uuid4

from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach a bounded correlation identifier to request state and response headers."""

    supplied = request.headers.get(REQUEST_ID_HEADER, "").strip()
    request_id = supplied if supplied and len(supplied) <= 100 else str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response
