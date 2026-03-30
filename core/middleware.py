import time
import uuid
import logging
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import asyncio

from fastapi import HTTPException

from core.request_context import set_request_id, get_request_id
from core.request_context import get_prediction_time_ms

logger = logging.getLogger("ckdci.middleware")


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        req_id = str(uuid.uuid4())
        set_request_id(req_id)
        start = time.time()
        client = request.client.host if request.client is not None else None
        logger.info("request.start", extra={"request_id": req_id, "method": request.method, "path": request.url.path, "client": client})

        try:
            response = await call_next(request)
        except Exception as exc:
            # Log exception with request id
            logger.exception("request.error", extra={"request_id": req_id, "method": request.method, "path": request.url.path})
            raise

        duration = time.time() - start
        response.headers["X-Request-ID"] = req_id
        pred_ms = get_prediction_time_ms()
        extra = {"request_id": req_id, "method": request.method, "path": request.url.path, "status": response.status_code, "duration": duration}
        if pred_ms is not None:
            extra["prediction_time_ms"] = pred_ms
        logger.info("request.complete", extra=extra)
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with large Content-Length headers to avoid huge uploads.

    Default limit 1MB; can be adjusted by setting environment variable MAX_REQUEST_SIZE.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        max_bytes = 1 * 1024 * 1024
        try:
            import os

            v = int(os.getenv("MAX_REQUEST_SIZE", "1048576"))
            max_bytes = v
        except Exception:
            pass

        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > max_bytes:
                    raise HTTPException(status_code=413, detail="Request body too large")
            except ValueError:
                pass

        return await call_next(request)


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Enforce a per-request timeout using asyncio.wait_for."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import os

        try:
            timeout = float(os.getenv("REQUEST_TIMEOUT", "30"))
        except Exception:
            timeout = 30.0

        try:
            return await asyncio.wait_for(call_next(request), timeout=timeout)
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Request timed out")
