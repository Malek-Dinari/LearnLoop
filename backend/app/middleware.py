"""HTTP middleware: request ID injection + structured access logging.

IMPORTANT: BaseHTTPMiddleware buffers streaming responses — SSE endpoints
must be skipped to avoid breaking the quiz generation stream.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Path fragments that identify SSE streaming endpoints.
# Any URL containing one of these strings bypasses the middleware body buffer.
_SSE_PATH_FRAGMENTS = ("/stream",)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add X-Request-ID header and log method / path / status / duration."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip SSE endpoints — BaseHTTPMiddleware buffers the response body,
        # which would prevent the client from receiving events progressively.
        if any(frag in request.url.path for frag in _SSE_PATH_FRAGMENTS):
            return await call_next(request)

        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start = time.perf_counter()

        response: Response = await call_next(request)

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "%s %s → %d (%.1fms) [%s]",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            request_id,
        )

        return response
