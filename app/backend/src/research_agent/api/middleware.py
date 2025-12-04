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
        
        # Extract request body for chat endpoints (to log the question)
        question = None
        if request.method == "POST" and "/chat" in str(request.url.path):
            try:
                # Read body and restore it for downstream handlers
                body_bytes = await request.body()
                if body_bytes:
                    request_body = json.loads(body_bytes)
                    question = request_body.get("message", "")
                    
                    # Restore body for FastAPI handlers
                    async def receive():
                        return {"type": "http.request", "body": body_bytes}
                    request._receive = receive
            except Exception:
                pass  # Ignore parsing errors

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
        
        # Add question for chat endpoints
        if question:
            # Truncate long questions for readability
            question_short = question[:200] + "..." if len(question) > 200 else question
            log_data["question"] = question_short
            log_data["question_length"] = len(question)
            log_data["endpoint_type"] = "chat"
        
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

