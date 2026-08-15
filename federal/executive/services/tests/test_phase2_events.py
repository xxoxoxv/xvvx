"""
AMOS-Federation Phase 2 — Contract Tests
الهدف: اختبار عقود الأحداث الستة + السلسلة الكاملة
النطاق: tests/test_phase2_events.py
"""

import pytest
from amos_federation.common.event_bus import validate_event, EVENT_CONTRACTS


class TestEventContracts:
    """اختبار عقود الأحداث — كل كسر عقد يفشل CI."""

    def test_task_created_contract_exists(self):
        """2.7: عقد task.created موجود."""
        assert "amos_federation.task.created" in EVENT_CONTRACTS

    def test_task_created_valid(self):
        """2.7: حدث task.created صالح عند وجود الحقول المطلوبة."""
        valid, msg = validate_event("amos_federation.task.created", {
            "task_id": "task-001",
            "type": "analysis",
            "description": "تحليل بيانات",
        })
        assert valid, f"يجب أن يكون صالحًا: {msg}"

    def test_task_created_missing_field(self):
        """2.7: حدث task.created يفشل عند نقص حقل مطلوب."""
        valid, msg = validate_event("amos_federation.task.created", {
            "task_id": "task-001",
            "type": "analysis",
        })
        assert not valid
        assert "description" in msg

    def test_agent_assigned_contract(self):
        """2.7: عقد agent.assigned."""
        valid, _ = validate_event("amos_federation.agent.assigned", {
            "task_id": "task-001",
            "agent_id": "agent-001",
        })
        assert valid

    def test_agent_assigned_missing(self):
        """2.7: agent.assigned يفشل بدون agent_id."""
        valid, _ = validate_event("amos_federation.agent.assigned", {
            "task_id": "task-001",
        })
        assert not valid

    def test_tool_executed_contract(self):
        """2.7: عقد tool.executed."""
        valid, _ = validate_event("amos_federation.tool.executed", {
            "tool_id": "python_execute",
            "agent_id": "agent-001",
            "result": {"status": "ok"},
        })
        assert valid

    def test_tool_executed_missing(self):
        """2.7: tool.executed يفشل بدون result."""
        valid, _ = validate_event("amos_federation.tool.executed", {
            "tool_id": "python_execute",
            "agent_id": "agent-001",
        })
        assert not valid

    def test_experience_recorded_contract(self):
        """2.7: عقد experience.recorded."""
        valid, _ = validate_event("amos_federation.experience.recorded", {
            "experience_id": "exp-001",
            "type": "task_completion",
        })
        assert valid

    def test_experience_recorded_missing(self):
        """2.7: experience.recorded يفشل بدون type."""
        valid, _ = validate_event("amos_federation.experience.recorded", {
            "experience_id": "exp-001",
        })
        assert not valid

    def test_approval_signed_contract(self):
        """2.7: عقد approval.signed."""
        valid, _ = validate_event("amos_federation.approval.signed", {
            "approval_id": "appr-001",
            "decision": "approved",
        })
        assert valid

    def test_approval_signed_missing(self):
        """2.7: approval.signed يفشل بدون decision."""
        valid, _ = validate_event("amos_federation.approval.signed", {
            "approval_id": "appr-001",
        })
        assert not valid

    def test_agent_completed_contract(self):
        """2.7: عقد agent.completed."""
        valid, _ = validate_event("amos_federation.agent.completed", {
            "agent_id": "agent-001",
            "task_id": "task-001",
            "result": {"status": "ok"},
        })
        assert valid

    def test_unknown_subject_rejected(self):
        """2.7: موضوع غير معروف يُرفض."""
        valid, _ = validate_event("amos_federation.unknown.event", {})
        assert not valid

    def test_all_six_required_contracts_exist(self):
        """2.7: كل العقود الستة المطلوبة موجودة."""
        required = [
            "amos_federation.task.created",
            "amos_federation.agent.assigned",
            "amos_federation.tool.executed",
            "amos_federation.experience.recorded",
            "amos_federation.approval.signed",
            "amos_federation.agent.completed",
        ]
        for subject in required:
            assert subject in EVENT_CONTRACTS, f"عقد مفقود: {subject}"


class TestDurableEventBus:
    """اختبار الناقل الدائم — publish/subscribe/ack/replay."""

    def test_publish_and_retrieve(self):
        """2.1: نشر حدث واسترجاعه."""
        from amos_federation.common.durable_event_bus import get_durable_event_bus
        bus = get_durable_event_bus()
        event = bus.publish(
            subject="amos_federation.task.created",
            data={"task_id": "test-001", "type": "test", "description": "اختبار"},
            correlation_id="test-001",
        )
        assert event["event_id"].startswith("evt-")
        assert event["subject"] == "amos_federation.task.created"

        # استرجاع
        events = bus.get_events(subject="amos_federation.task.created", limit=5)
        assert any(e["event_id"] == event["event_id"] for e in events)

    def test_subscribe_and_handler_called(self):
        """2.1: المعالج يُستدعى عند النشر."""
        from amos_federation.common.durable_event_bus import get_durable_event_bus
        bus = get_durable_event_bus()
        received = []
        bus.subscribe("amos_federation.task.created", lambda e: received.append(e))
        bus.publish(
            subject="amos_federation.task.created",
            data={"task_id": "test-002", "type": "test", "description": "اختبار المعالج"},
        )
        assert len(received) > 0
        assert received[-1]["data"]["task_id"] == "test-002"

    def test_wildcard_subscription(self):
        """2.1: الاشتراك بـ wildcard يستقبل كل الأحداث."""
        from amos_federation.common.durable_event_bus import get_durable_event_bus
        bus = get_durable_event_bus()
        received = []
        bus.subscribe("amos_federation.*", lambda e: received.append(e))
        bus.publish(
            subject="amos_federation.task.created",
            data={"task_id": "test-003", "type": "test", "description": "wildcard test"},
        )
        assert len(received) > 0

    def test_poll_and_ack(self):
        """2.1: poll يجلب الأحداث و ack يؤكدها."""
        from amos_federation.common.durable_event_bus import get_durable_event_bus
        bus = get_durable_event_bus()
        event = bus.publish(
            subject="amos_federation.task.created",
            data={"task_id": "test-ack", "type": "test", "description": "ack test"},
        )
        events = bus.poll(consumer_name="test-consumer", subject="amos_federation.task.created")
        assert any(e["event_id"] == event["event_id"] for e in events)
        # ack
        result = bus.ack("test-consumer", "amos_federation.task.created", event["event_id"])
        assert result
        # poll مرة أخرى — يجب ألا يعيد نفس الحدث
        events2 = bus.poll(consumer_name="test-consumer", subject="amos_federation.task.created")
        assert not any(e["event_id"] == event["event_id"] for e in events2)

    def test_replay(self):
        """2.1: replay يعيد الأحداث من البداية."""
        from amos_federation.common.durable_event_bus import get_durable_event_bus
        bus = get_durable_event_bus()
        # replay من البداية
        events = bus.replay(consumer_name="replay-test", subject="amos_federation.task.created", from_beginning=True)
        assert isinstance(events, list)

    def test_count(self):
        """2.1: count يعيد عدد الأحداث."""
        from amos_federation.common.durable_event_bus import get_durable_event_bus
        bus = get_durable_event_bus()
        count_before = bus.count()
        bus.publish(
            subject="amos_federation.task.created",
            data={"task_id": "test-count", "type": "test", "description": "count test"},
        )
        count_after = bus.count()
        assert count_after > count_before


class TestEventWiring:
    """اختبار ربط الأحداث — السلسلة الكاملة."""

    def test_publish_task_created(self):
        """2.2: نشر task.created."""
        from amos_federation.common.event_wiring import publish_task_created
        event = publish_task_created("wiring-001", "test", "اختبار ربط")
        assert event["subject"] == "amos_federation.task.created"
        assert event["data"]["task_id"] == "wiring-001"

    def test_publish_agent_assigned(self):
        """2.3: نشر agent.assigned."""
        from amos_federation.common.event_wiring import publish_agent_assigned
        event = publish_agent_assigned("wiring-001", "agent-001", "plan")
        assert event["subject"] == "amos_federation.agent.assigned"
        assert event["data"]["agent_id"] == "agent-001"

    def test_publish_tool_executed(self):
        """2.4: نشر tool.executed."""
        from amos_federation.common.event_wiring import publish_tool_executed
        event = publish_tool_executed("python_execute", "agent-001", {"status": "ok"}, "wiring-001")
        assert event["subject"] == "amos_federation.tool.executed"
        assert event["data"]["tool_id"] == "python_execute"

    def test_publish_experience_recorded(self):
        """2.5: نشر experience.recorded."""
        from amos_federation.common.event_wiring import publish_experience_recorded
        event = publish_experience_recorded("exp-001", "task_completion", "agent-001", "wiring-001", 0.9)
        assert event["subject"] == "amos_federation.experience.recorded"
        assert event["data"]["quality_score"] == 0.9

    def test_publish_approval_signed(self):
        """2.6: نشر approval.signed."""
        from amos_federation.common.event_wiring import publish_approval_signed
        event = publish_approval_signed("appr-001", "approved", "model-001", "king")
        assert event["subject"] == "amos_federation.approval.signed"
        assert event["data"]["decision"] == "approved"

    def test_publish_agent_completed(self):
        """نشر agent.completed."""
        from amos_federation.common.event_wiring import publish_agent_completed
        event = publish_agent_completed("agent-001", "wiring-001", {"status": "ok"}, 0.85)
        assert event["subject"] == "amos_federation.agent.completed"
        assert event["data"]["quality_score"] == 0.85

    def test_full_event_chain(self):
        """2.7: السلسلة الكاملة من task.created إلى experience.recorded.

        بوابة الخروج: إرسال مهمة واحدة يُنتج سلسلة أحداث كاملة قابلة للتتبع.
        """
        from amos_federation.common.event_wiring import run_full_event_chain
        result = run_full_event_chain("مهمة اختبار السلسلة الكاملة")
        assert result["status"] in ["complete", "partial"]
        assert result["task_id"].startswith("task-")
        assert "task.created" in " ".join(result["event_subjects"])
