"""
AMOS-Federation Service Application Factory
الهدف: إنشاء تطبيقات FastAPI موحدة ومهيأة للرصد والصحة
النطاق: كل خدمات AMOS-Federation الخلفية
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import uuid
from collections.abc import Iterable

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse

from amos_federation.common.config import settings
from amos_federation.common.logging import setup_logging
from amos_federation.common.schemas import HealthResponse, ReadyResponse
from amos_federation.common.tracing import setup_tracing


def _instrument_application(app: FastAPI) -> None:
    """إضافة OpenTelemetry FastAPI اختياريًا دون جعل التشغيل مرهونًا بالحزمة."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:
        return
    FastAPIInstrumentor.instrument_app(app)


def create_service_app(
    service_name: str,
    port: int,
    description: str,
    routers: Iterable[APIRouter] | None = None,
) -> FastAPI:
    """إنشاء تطبيق خدمة موحد مع مسارات الصحة والجاهزية ومعرّف الطلب."""
    setup_logging(service_name, settings.debug)
    setup_tracing(service_name, settings.otlp_endpoint)
    app = FastAPI(title=f"AMOS-Federation {service_name}", description=description, version="1.0.0")
    app.state.service_name = service_name
    app.state.service_port = port

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/health", response_model=HealthResponse, tags=["operational"])
    async def health() -> HealthResponse:
        return HealthResponse(service=service_name)

    @app.get("/ready", response_model=ReadyResponse, tags=["operational"])
    async def ready() -> ReadyResponse:
        return ReadyResponse(service=service_name)

    @app.get("/", tags=["operational"])
    async def service_information() -> JSONResponse:
        return JSONResponse({"service": service_name, "port": port, "status": "healthy"})

    for router in routers or []:
        app.include_router(router)
    _instrument_application(app)
    return app
