"""
اختبارات النماذج الأساسية
الهدف: التحقق من بنية قاعدة البيانات
النطاق: common/database.py
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import uuid

from amos_federation.common.database import generate_uuid


class TestDatabaseUtils:
    def test_uuid_generation(self):
        """توليد UUID ينتج UUID صالح"""
        u = generate_uuid()
        assert isinstance(u, uuid.UUID)
        assert str(u)  # يمكن تحويله لنص

    def test_uuid_uniqueness(self):
        """كل UUID فريد"""
        u1 = generate_uuid()
        u2 = generate_uuid()
        assert u1 != u2

    def test_uuid_version(self):
        """UUID الإصدار 4 (عشوائي)"""
        u = generate_uuid()
        assert u.version == 4
