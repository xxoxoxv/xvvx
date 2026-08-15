"""
اختبارات نظام الأحداث (Event Bus)
الهدف: التحقق من نشر وتخزين واشتراك الأحداث + عقود الأحداث
النطاق: common/event_bus
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from amos_federation.common.event_bus import (
    EVENT_CONTRACTS,
    EventBus,
    get_event_bus,
    validate_event,
)


def test_publish_and_retrieve_event() -> None:
    """نشر حدث واسترجاعه من المخزن."""
    bus = EventBus()
    bus.publish("amos_federation.task.created", {
        "task_id": "evt-test-001",
        "type": "analysis",
        "description": "تحليل بيانات",
    })
    events = bus.get_events("amos_federation.task.created")
    assert len(events) > 0
    last = events[0]
    assert last["data"]["task_id"] == "evt-test-001"


def test_event_persistence_across_instances() -> None:
    """الأحداث تبقى بعد إنشاء نسخة جديدة."""
    bus1 = EventBus()
    bus1.publish("amos_federation.task.created", {
        "task_id": "persist-evt-001",
        "type": "report",
        "description": "تقرير",
    })
    bus2 = EventBus()
    events = bus2.get_events("amos_federation.task.created")
    found = [e for e in events if e["data"].get("task_id") == "persist-evt-001"]
    assert len(found) == 1


def test_subscription_handler_called() -> None:
    """المعالج المسجّل يُستدعى عند النشر."""
    bus = EventBus()
    received: list[dict] = []
    bus.subscribe("amos_federation.test.subject", lambda data: received.append(data))
    bus.publish("amos_federation.test.subject", {"message": "hello"})
    assert len(received) == 1
    assert received[0]["message"] == "hello"


def test_multiple_handlers_called() -> None:
    """عدة معالجات يُستدعون لنفس الحدث."""
    bus = EventBus()
    results1: list[dict] = []
    results2: list[dict] = []
    bus.subscribe("amos_federation.multi.test", lambda d: results1.append(d))
    bus.subscribe("amos_federation.multi.test", lambda d: results2.append(d))
    bus.publish("amos_federation.multi.test", {"x": 1})
    assert len(results1) == 1
    assert len(results2) == 1


def test_wildcard_subscription() -> None:
    """الاشتراك بـ wildcard يلتقط كل الأحداث تحت البادئة."""
    bus = EventBus()
    received: list[dict] = []
    bus.subscribe("amos_federation.task.*", lambda d: received.append(d))
    bus.publish("amos_federation.task.created", {"task_id": "w1", "type": "x", "description": "y"})
    bus.publish("amos_federation.task.planned", {"task_id": "w2", "plan": []})
    assert len(received) == 2


def test_event_count() -> None:
    """عدد الأحداث يعمل."""
    bus = EventBus()
    initial = bus.count("amos_federation.count.test")
    bus.publish("amos_federation.count.test", {"n": 1})
    bus.publish("amos_federation.count.test", {"n": 2})
    assert bus.count("amos_federation.count.test") == initial + 2


def test_handler_failure_doesnt_block_publish() -> None:
    """فشل معالج لا يوقف النشر."""
    bus = EventBus()
    def bad_handler(data):
        raise ValueError("خطأ مقصود")
    bus.subscribe("amos_federation.fault.test", bad_handler)
    # لا يجب أن يرمي استثناء
    result = bus.publish("amos_federation.fault.test", {"ok": True})
    assert result["event_id"] is not None


def test_get_event_bus_singleton() -> None:
    """get_event_bus يعيد نفس النسخة."""
    bus1 = get_event_bus()
    bus2 = get_event_bus()
    assert bus1 is bus2


# === Contract Tests ===

def test_all_event_contracts_defined() -> None:
    """كل عقود الأحداث معرّفة."""
    expected_subjects = [
        "amos_federation.task.created",
        "amos_federation.task.planned",
        "amos_federation.agent.assigned",
        "amos_federation.agent.started",
        "amos_federation.tool.executed",
        "amos_federation.agent.completed",
        "amos_federation.experience.recorded",
        "amos_federation.memory.stored",
        "amos_federation.model.invoked",
        "amos_federation.critic.reviewed",
        "amos_federation.approval.signed",
        "amos_federation.policy.checked",
    ]
    for subject in expected_subjects:
        assert subject in EVENT_CONTRACTS, f"عقد مفقود: {subject}"


def test_validate_valid_event() -> None:
    """التحقق من حدث صالح."""
    valid, msg = validate_event("amos_federation.task.created", {
        "task_id": "t1",
        "type": "analysis",
        "description": "تحليل",
    })
    assert valid is True
    assert msg == "صالح"


def test_validate_missing_required_field() -> None:
    """التحقق من حدث ينقصه حقل مطلوب."""
    valid, msg = validate_event("amos_federation.task.created", {
        "task_id": "t1",
        "type": "analysis",
        # description مفقود
    })
    assert valid is False
    assert "description" in msg


def test_validate_unknown_subject() -> None:
    """التحقق من حدث بعقد غير معروف."""
    valid, msg = validate_event("amos_federation.unknown.event", {"x": 1})
    assert valid is False


def test_contract_schema_drift_detection() -> None:
    """اكتشاف انحراف المخطط: حقل مطلوب مفقود يفشل التحقق."""
    # محاولة نشر حدث ناقص
    valid, msg = validate_event("amos_federation.experience.recorded", {
        "experience_id": "e1",
        # type مفقود
    })
    assert valid is False
    assert "type" in msg


def test_full_event_chain_task_to_experience() -> None:
    """سلسلة أحداث كاملة من task.created حتى experience.recorded."""
    bus = EventBus()

    # 1. task.created
    bus.publish("amos_federation.task.created", {
        "task_id": "chain-001", "type": "analysis", "description": "سلسلة اختبار",
    })
    # 2. task.planned
    bus.publish("amos_federation.task.planned", {
        "task_id": "chain-001", "plan": [{"step": 1}],
    })
    # 3. agent.assigned
    bus.publish("amos_federation.agent.assigned", {
        "task_id": "chain-001", "agent_id": "worker-1",
    })
    # 4. tool.executed
    bus.publish("amos_federation.tool.executed", {
        "tool_id": "sql_query", "agent_id": "worker-1", "result": {"rows": 10},
    })
    # 5. agent.completed
    bus.publish("amos_federation.agent.completed", {
        "agent_id": "worker-1", "task_id": "chain-001", "result": {"status": "done"},
    })
    # 6. experience.recorded
    bus.publish("amos_federation.experience.recorded", {
        "experience_id": "exp-chain-001", "type": "success",
    })

    # التحقق من تخزين كل الأحداث
    all_events = bus.get_events(limit=100)
    subjects = [e["subject"] for e in all_events]
    assert "amos_federation.task.created" in subjects
    assert "amos_federation.task.planned" in subjects
    assert "amos_federation.agent.assigned" in subjects
    assert "amos_federation.tool.executed" in subjects
    assert "amos_federation.agent.completed" in subjects
    assert "amos_federation.experience.recorded" in subjects
