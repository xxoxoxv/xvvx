"""
AMOS-Federation Service Registry
الهدف: مصدر الحقيقة الموحد لأسماء الخدمات ومنافذها ومسؤولياتها
النطاق: الخدمات التسع الخلفية في خريطة الخدمات
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import TypedDict


class ServiceDefinition(TypedDict):
    """البيانات التشغيلية الثابتة لخدمة واحدة."""

    name: str
    port: int
    responsibility: str
    store: str
    slo: str


SERVICES: dict[str, ServiceDefinition] = {
    "api-gateway": {
        "name": "api-gateway",
        "port": 8000,
        "responsibility": "استقبال الطلبات + auth",
        "store": "Redis",
        "slo": "p99 < 100ms",
    },
    "orchestrator": {
        "name": "orchestrator",
        "port": 8001,
        "responsibility": "التخطيط + توزيع المهام",
        "store": "PostgreSQL",
        "slo": "p99 < 500ms",
    },
    "agent-runtime": {
        "name": "agent-runtime",
        "port": 8002,
        "responsibility": "تنفيذ الوكلاء",
        "store": "Redis",
        "slo": "حسب المهمة",
    },
    "tool-registry": {
        "name": "tool-registry",
        "port": 8003,
        "responsibility": "إدارة الأدوات",
        "store": "PostgreSQL",
        "slo": "p99 < 50ms",
    },
    "model-gateway": {
        "name": "model-gateway",
        "port": 8004,
        "responsibility": "توجيه النماذج",
        "store": "Redis",
        "slo": "p99 < 5s",
    },
    "memory-service": {
        "name": "memory-service",
        "port": 8005,
        "responsibility": "الذاكرة",
        "store": "Redis + Qdrant",
        "slo": "p99 < 200ms",
    },
    "evaluation": {
        "name": "evaluation",
        "port": 8006,
        "responsibility": "تقييم النماذج",
        "store": "PostgreSQL",
        "slo": "حسب التقييم",
    },
    "critic": {
        "name": "critic",
        "port": 8007,
        "responsibility": "مراجعة النتائج",
        "store": "PostgreSQL",
        "slo": "p99 < 10s",
    },
    "governance": {
        "name": "governance",
        "port": 8009,
        "responsibility": "السياسات + Kill Switch",
        "store": "PostgreSQL",
        "slo": "p99 < 100ms",
    },
}
