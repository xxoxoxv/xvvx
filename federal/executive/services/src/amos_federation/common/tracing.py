"""
AMOS-Federation OpenTelemetry Tracing
الهدف: تتبع موزع لكل الطلبات عبر الخدمات عند توفر حزم OpenTelemetry
النطاق: كل الخدمات
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Any


def setup_tracing(
    service_name: str = "amos-federation", otlp_endpoint: str = "http://localhost:4317"
) -> Any | None:
    """إعداد OpenTelemetry اختياريًا وإرجاع tracer أو None في البيئة الخفيفة."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        return None
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)


def get_tracer(name: str = "amos-federation") -> Any | None:
    """الحصول على tracer متاح أو None عندما لا تكون مكتبة OpenTelemetry مثبّتة."""
    try:
        from opentelemetry import trace
    except ImportError:
        return None
    return trace.get_tracer(name)
