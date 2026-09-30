import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_LOG = defaultdict(list)  # {ip: [timestamps]}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory sliding-window rate limiter.
    Not production/distributed-grade, but prevents accidental hammering
    of external APIs (Open-Meteo/USGS) during testing or a live demo.
    """
    def __init__(self, app, max_requests=100, window_seconds=60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        REQUEST_LOG[client_ip] = [t for t in REQUEST_LOG[client_ip] if t > window_start]

        if len(REQUEST_LOG[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "message": f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s."
                }
            )

        REQUEST_LOG[client_ip].append(now)
        return await call_next(request)