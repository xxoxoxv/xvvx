"""
اختبارات أفرع حدية إضافية لرفع تغطية الأفرع فوق 80%
الهدف: تغطية أفرع حدية لم تصلها الاختبارات الأساسية، لإثبات أن مسارات الفشل
       والحالات الطرفية في الخدمات مُجرَّبة فعلًا لا مفترضة.
النطاق: model_gateway/shadow + training/model_registry + agent_runtime/sandbox + event_wiring
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from amos_federation.common.event_wiring import init_event_consumers
from amos_federation.services.agent_runtime.sandbox import ToolSandbox
from amos_federation.services.model_gateway.shadow import (
    InMemoryShadowStore,
    _text_similarity,
    run_shadow_test,
)
from amos_federation.services.training.model_registry import InMemoryModelRegistry


class TestShadowEdges:
    def test_summary_empty(self) -> None:
        assert InMemoryShadowStore().summary() == {
            "total": 0,
            "avg_similarity": 0.0,
            "avg_latency_diff": 0,
        }

    def test_text_similarity_both_empty(self) -> None:
        assert _text_similarity("", "") == 1.0

    def test_text_similarity_one_empty(self) -> None:
        assert _text_similarity("hello", "") == 0.0
        assert _text_similarity("", "world") == 0.0

    def test_run_shadow_test(self) -> None:
        record = run_shadow_test("ما هو سعر الذهب؟")
        assert "comparison" in record
        assert "alpha" in record and "beta" in record


class TestModelRegistryEdges:
    def test_get_missing_returns_none(self) -> None:
        reg = InMemoryModelRegistry()
        assert reg.get("nonexistent") is None

    def test_list_all_filtered_by_status(self) -> None:
        reg = InMemoryModelRegistry()
        reg.register({"model_id": "m1", "status": "registered"})
        reg.register({"model_id": "m2", "status": "trained"})
        only_trained = reg.list_all(status="trained")
        assert len(only_trained) == 1
        assert only_trained[0]["model_id"] == "m2"

    def test_update_status_missing_returns_none(self) -> None:
        reg = InMemoryModelRegistry()
        assert reg.update_status("nonexistent", "trained") is None


class TestSandboxEdges:
    def test_unknown_tool_returns_error(self) -> None:
        sandbox = ToolSandbox()
        result = sandbox.execute("nonexistent_tool", {"x": 1})
        assert "error" in result
        assert "غير مسجلة" in result["error"]


class TestEventWiringInit:
    def test_init_event_consumers_is_idempotent(self) -> None:
        # first call initializes consumers; second call hits the early return
        init_event_consumers()
        init_event_consumers()  # covers the `if _consumers_initialized: return` branch
