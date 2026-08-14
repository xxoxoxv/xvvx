"""
AMOS-Federation OpenTelemetry Tracing
الهدف: تتبع موزع لكل الطلبات عبر الخدمات
النطاق: كل الخدمات
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing(service_name: str = "amos-federation", otlp_endpoint: str = "http://localhost:4317"):
    """إعداد OpenTelemetry tracing مع OTLP exporter."""
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)


def get_tracer(name: str = "amos-federation"):
    """الحصول على tracer."""
    return trace.get_tracer(name)
