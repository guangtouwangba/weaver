"""API middleware."""

import json
import time
from typing import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from research_agent.shared.utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with structured data for Grafana."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Note: We don't read request body here because it conflicts with
        # BaseHTTPMiddleware's internal state, especially for streaming endpoints.
        # The question content will be logged at the endpoint level if needed.
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        # Log response with structured JSON data for Grafana parsing
        duration = time.time() - start_time
        duration_ms = round(duration * 1000, 2)
        
        # Build structured log data as JSON
        log_data = {
            "method": request.method,
            "path": str(request.url.path),
            "status_code": response.status_code,
            "duration_seconds": round(duration, 3),
            "duration_ms": duration_ms,
        }
        
        # Mark chat endpoints for filtering in Grafana
        if "/chat" in str(request.url.path):
            log_data["endpoint_type"] = "chat"
            if "/stream" in str(request.url.path):
                log_data["endpoint_type"] = "chat_stream"
        
        # Log as JSON for easier parsing in Grafana
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code} duration={duration:.3f}s | "
            f"JSON: {json.dumps(log_data, ensure_ascii=False)}"
        )

        return response


def setup_middleware(app: FastAPI) -> None:
    """Set up middleware for the FastAPI app."""
    app.add_middleware(LoggingMiddleware)

