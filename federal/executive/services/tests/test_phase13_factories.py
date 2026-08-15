"""
AMOS-Federation Phase 13 — Federal Factories Tests
الهدف: اختبار المصانع الأربعة
النطاق: tests/test_phase13_factories.py
"""

import pytest


class TestFinancialReportFactory:
    """13.1: مصنع التقارير المالية."""

    def test_start_production(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("financial_report")
        result = factory.start_production("تقرير مالي Q3 2026", "agent-finance-1")
        assert result["started"] is True
        assert "extract" in result["pipeline"]

    def test_complete_step(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("financial_report")
        prod = factory.start_production("تقرير اختبار", "agent-1")
        result = factory.complete_step(prod["product_id"], "extract", "بيانات مستخرجة", 90)
        assert result["steps_completed"] == 1

    def test_full_pipeline(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("financial_report")
        result = factory.run_full_pipeline("تقرير شامل", "agent-finance-1")
        assert result["status"] == "published"
        assert result["steps_completed"] == 6  # extract, clean, analyze, write, review, publish


class TestContentFactory:
    """13.2: مصنع المحتوى."""

    def test_start_production(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("content")
        result = factory.start_production("مقال عن الفدرالية", "agent-culture-1")
        assert result["started"] is True

    def test_full_pipeline(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("content")
        result = factory.run_full_pipeline("مقال ثقافي", "agent-culture-1")
        assert result["status"] == "published"
        assert result["steps_completed"] == 5  # research, draft, edit, review, publish


class TestResearchFactory:
    """13.3: مصنع الأبحاث."""

    def test_start_production(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("research")
        result = factory.start_production("بحث: تأثير الفدرالية الرقمية", "agent-science-1")
        assert result["started"] is True

    def test_full_pipeline(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("research")
        result = factory.run_full_pipeline("ورقة بحثية", "agent-science-1")
        assert result["status"] == "published"
        assert result["steps_completed"] == 7  # question, literature, methodology, experiment, write, review, publish


class TestSecurityFactory:
    """13.4: مصنع المراقبة الأمنية."""

    def test_start_production(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("security")
        result = factory.start_production("تقرير أمني شهري", "agent-law-1")
        assert result["started"] is True

    def test_full_pipeline(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("security")
        result = factory.run_full_pipeline("تقرير تهديدات", "agent-law-1")
        assert result["status"] == "published"
        assert result["steps_completed"] == 6  # collect_logs, analyze, detect_threats, assess, report, publish


class TestFactoryRegistry:
    """13.6: سجل المصانع."""

    def test_list_factories(self):
        from amos_federation.services.governance.factories import get_factory_registry
        registry = get_factory_registry()
        factories = registry.list_factories()
        assert len(factories) >= 4

    def test_assign_manager(self):
        from amos_federation.services.governance.factories import get_factory_registry
        registry = get_factory_registry()
        result = registry.assign_manager("financial_report", "agent-manager-1")
        assert result["assigned"] is True


class TestFactoryProducts:
    """مخرجات المصانع."""

    def test_list_products(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("financial_report")
        factory.run_full_pipeline("منتج اختبار قائمة", "agent-1")
        products = factory.list_products()
        assert len(products) > 0

    def test_get_product(self):
        from amos_federation.services.governance.factories import get_factory
        factory = get_factory("content")
        result = factory.run_full_pipeline("منتج للاسترجاع", "agent-1")
        product = factory.get_product(result["product_id"])
        assert product is not None
        assert product["title"] == "منتج للاسترجاع"
        assert len(product["pipeline_steps"]) > 0
