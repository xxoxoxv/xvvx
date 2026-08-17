"""
Middleware for AMOS Web Interface
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging


logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware for API requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health checks and public endpoints
        if request.url.path in ["/health", "/api/system/health"]:
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header:
            # For demo purposes, allow requests without auth
            # In production, validate JWT tokens here
            return await call_next(request)
        
        # Validate token (implement JWT validation here)
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            # TODO: Validate token
            # if not validate_token(token):
            #     return JSONResponse(
            #         status_code=401,
            #         content={"detail": "Invalid token"}
            #     )
        
        return await call_next(request)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {duration:.3f}s"
        )
        
        # Add timing header
        response.headers["X-Process-Time"] = str(duration)
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts = {}
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        
        # Simple in-memory rate limiting (use Redis in production)
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = []
        
        now = time.time()
        minute_ago = now - 60
        
        # Remove old requests
        self.request_counts[client_ip] = [
            t for t in self.request_counts[client_ip] if t > minute_ago
        ]
        
        # Check rate limit
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"}
            )
        
        # Record this request
        self.request_counts[client_ip].append(now)
        
        return await call_next(request)
