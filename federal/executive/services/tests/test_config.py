"""
اختبارات الإعدادات
الهدف: التحقق من قراءة الإعدادات الافتراضية
النطاق: common/config.py
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""
from amos_federation.common.config import Settings


class TestSettings:
    def test_default_values(self):
        """الإعدادات الافتراضية صحيحة"""
        s = Settings()
        assert s.app_name == "amos-federation"
        assert s.postgres_port == 5432
        assert s.redis_port == 6379

    def test_postgres_dsn(self):
        """DSN يحتوي على كل المكونات"""
        s = Settings()
        dsn = s.postgres_dsn
        assert "postgresql://" in dsn
        assert "5432" in dsn
        assert "amos_federation" in dsn

    def test_redis_url(self):
        """Redis URL صحيح"""
        s = Settings()
        assert s.redis_url.startswith("redis://")
