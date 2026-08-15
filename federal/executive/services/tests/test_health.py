"""
اختبارات صحة الخدمات
الهدف: التحقق من health وready للخدمات التسع دون بنية خارجية
النطاق: جميع تطبيقات الخدمات
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from importlib import import_module

import pytest
from fastapi.testclient import TestClient

from amos_federation.common.registry import SERVICES

PACKAGE_BY_SERVICE = {name: name.replace("-", "_") for name in SERVICES}


@pytest.mark.parametrize("service_name", SERVICES)
def test_health_and_ready_for_every_service(service_name: str) -> None:
    """كل خدمة مسجلة تعرض صحّة وجاهزية ومعلومات ميناء صحيحة."""
    module = import_module(f"amos_federation.services.{PACKAGE_BY_SERVICE[service_name]}.main")
    client = TestClient(module.app)
    health = client.get("/health")
    ready = client.get("/ready")
    root = client.get("/")
    assert health.status_code == 200
    assert health.json() == {"status": "healthy", "service": service_name}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "service": service_name}
    assert root.json()["port"] == SERVICES[service_name]["port"]
    assert health.headers["X-Request-ID"]
