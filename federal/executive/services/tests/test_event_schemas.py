"""
اختبارات مخططات الأحداث
الهدف: التحقق من قبول حدث صحيح ورفض حدث ناقص
النطاق: common/event_schemas.py
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from amos_federation.common.event_schemas import validate_event


def valid_task_event() -> dict[str, object]:
    """إنشاء مثال متوافق مع عقد task.created المسجل."""
    return {
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "timestamp": "2026-08-15T00:00:00Z",
        "event_type": "task.created",
        "source": "api-gateway",
        "data": {
            "task_id": "task-001",
            "type": "analysis",
            "description": "تحليل المبيعات",
            "priority": "high",
            "domain": "finance",
        },
        "chain_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    }


def test_validate_event_accepts_correct_payload() -> None:
    """المخطط يقبل الحدث الكامل المتوافق."""
    assert validate_event("task.created", valid_task_event())


def test_validate_event_rejects_missing_required_field() -> None:
    """المخطط يرفض الحدث عند غياب حقل مطلوب."""
    payload = valid_task_event()
    del payload["data"]
    assert not validate_event("task.created", payload)
