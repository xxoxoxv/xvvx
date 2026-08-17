"""
AMOS Web Interface - FastAPI Admin Dashboard
Citizen Portal, Task Management, and System Monitoring
"""

from .app import create_app
from .routes import router
from .middleware import AuthMiddleware, LoggingMiddleware

__all__ = [
    'create_app',
    'router',
    'AuthMiddleware',
    'LoggingMiddleware'
]
