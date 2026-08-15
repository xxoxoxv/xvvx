"""
AMOS-Federation Phase 12 — Federal States Tests
الهدف: اختبار الولايات التسع كوحدات معزولة
النطاق: tests/test_phase12_states.py
"""


class TestStateRuntime:
    """12.1: State Runtime — كل ولاية وحدة تشغيل معزولة."""

    def test_nine_states_initialized(self):
        """12.1: الولايات التسع مهيأة."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        states = runtime.list_states()
        assert len(states) >= 9

    def test_get_state(self):
        """12.1: استرجاع ولاية."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        state = runtime.get_state("finance")
        assert state is not None
        assert state["state_id"] == "finance"
        assert state["status"] == "active"

    def test_get_nonexistent_state(self):
        """12.1: ولاية غير موجودة."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        state = runtime.get_state("nonexistent")
        assert state is None


class TestStateIsolation:
    """12.1-12.7: عزل الولايات."""

    def test_assign_agent_to_state(self):
        """12.6: تعيين وكيل في ولاية."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        result = runtime.assign_agent("finance", "agent-test-finance-1", "worker")
        assert result["assigned"] is True

    def test_get_state_agents(self):
        """12.6: وكلاء ولاية معينة."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        runtime.assign_agent("science", "agent-test-science-1", "researcher")
        agents = runtime.get_state_agents("science")
        assert len(agents) > 0

    def test_isolation_no_overlap(self):
        """12.1: ولاية المال لا تصل تقنيًا لأدوات ولاية الصحة."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        # تعيين وكلاء مختلفين لكل ولاية
        runtime.assign_agent("finance", "agent-iso-finance", "worker")
        runtime.assign_agent("health", "agent-iso-health", "worker")
        result = runtime.check_isolation("finance")
        # لا يجب أن يكون هناك تداخل
        assert "overlapping_agents" in result

    def test_suspend_state(self):
        """12.7: إيقاف ولاية لا يؤثر على البقية."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        # إيقاف ولاية
        result = runtime.suspend_state("trade", reason="اختبار الإيقاف")
        assert result["status"] == "suspended"
        # بقية الولايات نشطة
        states = runtime.list_states()
        active_states = [s for s in states if s["status"] == "active" and s["state_id"] != "trade"]
        assert len(active_states) >= 8
        # إعادة تفعيل
        runtime.reactivate_state("trade")

    def test_suspend_does_not_affect_others(self):
        """12.7: إيقاف ولاية واحدة لا يكسر الأخرى."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        runtime.suspend_state("culture", reason="اختبار العزل")
        science = runtime.get_state("science")
        assert science["status"] == "active"
        runtime.reactivate_state("culture")


class TestFederalMessageBus:
    """12.3: Federal Message Bus بين الولايات."""

    def test_send_message_approved(self):
        """12.3: رسالة بين ولايتين نشطتين تُوافق عليها."""
        from amos_federation.services.governance.state_runtime import get_federal_message_bus

        bus = get_federal_message_bus()
        result = bus.send_message("finance", "science", "تعاون بحثي", "طلب تعاون")
        assert result["policy_check"] == "approved"
        assert result["delivered"] is True

    def test_send_message_denied_suspended(self):
        """12.3: رسالة لولاية موقوفة تُرفض."""
        from amos_federation.services.governance.state_runtime import (
            get_federal_message_bus,
            get_state_runtime,
        )

        runtime = get_state_runtime()
        bus = get_federal_message_bus()
        runtime.suspend_state("trade", reason="اختبار")
        result = bus.send_message("finance", "trade", "رسالة", "اختبار")
        assert result["policy_check"] == "denied"
        runtime.reactivate_state("trade")

    def test_get_received_messages(self):
        """12.3: استقبال رسائل ولاية."""
        from amos_federation.services.governance.state_runtime import get_federal_message_bus

        bus = get_federal_message_bus()
        bus.send_message("science", "health", "بحث طبي", "طلب بيانات")
        msgs = bus.get_messages("health", direction="received")
        assert len(msgs) > 0

    def test_get_sent_messages(self):
        """12.3: رسائل المرسلة من ولاية."""
        from amos_federation.services.governance.state_runtime import get_federal_message_bus

        bus = get_federal_message_bus()
        bus.send_message("law", "science", "استشارة قانونية", "طلب")
        msgs = bus.get_messages("law", direction="sent")
        assert len(msgs) > 0


class TestBudgetAllocation:
    """12.4: Federal Budget Allocation."""

    def test_allocate_budget(self):
        """12.4: توزيع ميزانية على ولاية."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        result = runtime.allocate_budget("science", "500", "تمويل بحثي")
        assert result["allocated"] == 500
        assert result["new_budget"] > result["previous_budget"]


class TestNewStateRegistration:
    """12.8: إضافة ولاية جديدة بلا تعديل الدستور."""

    def test_register_new_state(self):
        """12.8: ولاية جديدة تُسجل بدون لمس الدستور."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        result = runtime.register_state(
            "experimental_tenth",
            "ولاية تجريبية عاشرة",
            "experimental",
            budget="100",
        )
        assert result["registered"] is True
        assert result["state_id"] == "experimental_tenth"

    def test_duplicate_state_rejected(self):
        """12.8: لا يمكن تسجيل ولاية موجودة."""
        from amos_federation.services.governance.state_runtime import get_state_runtime

        runtime = get_state_runtime()
        result = runtime.register_state("finance", "مكرر", "finance")
        assert "error" in result


class TestStateAdminStructure:
    """12.6: البنية الإدارية الموحدة."""

    def test_admin_structure_has_nine_roles(self):
        """12.6: البنية الإدارية لها 9 أدوار."""
        from amos_federation.services.governance.state_runtime import STATE_ADMIN_STRUCTURE

        assert len(STATE_ADMIN_STRUCTURE) == 9
        assert "coordinator" in STATE_ADMIN_STRUCTURE
        assert "council" in STATE_ADMIN_STRUCTURE
        assert "judge" in STATE_ADMIN_STRUCTURE
        assert "worker" in STATE_ADMIN_STRUCTURE

    def test_total_agents_per_state(self):
        """12.6: كل ولاية تستوعب ~22 وكيل."""
        from amos_federation.services.governance.state_runtime import STATE_ADMIN_STRUCTURE

        total = sum(spec["count"] for spec in STATE_ADMIN_STRUCTURE.values())
        assert total == 22  # 1+3+1+1+1+10+1+3+1
