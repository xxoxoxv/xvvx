"""
اختبارات النماذج الحقيقية (Phase 5)
الهدف: التحقق من caching، cost tracking الدائم، benchmark
النطاق: services/model_gateway/model_layer
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import pytest

from amos_federation.services.model_gateway.model_layer import (
    ModelLayer,
    get_model_layer,
)


@pytest.fixture
def layer():
    """طبقة نموذج جديدة لكل اختبار."""
    return ModelLayer()


# === 5.4: Cost Tracking حقيقي ===


def test_cost_tracking_persistent() -> None:
    """التكلفة تُسجل دائمًا في DB."""
    layer = ModelLayer()
    layer.log_cost("inv-test-001", "claude-sonnet-4", 500, 0.0075, 120, "external")
    summary = layer.get_cost_summary()
    assert summary["total_invocations"] >= 1
    assert summary["total_cost_usd"] > 0


def test_cost_tracking_survives_restart() -> None:
    """سجل التكلفة يبقى بعد إعادة التشغيل."""
    layer1 = ModelLayer()
    layer1.log_cost("inv-persist-001", "local-fallback", 100, 0.0, 50, "local")
    count1 = layer1.get_cost_summary()["total_invocations"]

    layer2 = ModelLayer()
    count2 = layer2.get_cost_summary()["total_invocations"]
    assert count2 == count1


def test_cost_computation_real() -> None:
    """حساب التكلفة حقيقي."""
    layer = ModelLayer()
    # Claude Sonnet 4: input $0.003/1K, output $0.015/1K
    cost = layer.compute_cost("claude-sonnet-4", input_tokens=1000, output_tokens=500)
    expected = (1000 / 1000) * 0.003 + (500 / 1000) * 0.015
    assert abs(cost - round(expected, 6)) < 0.0001


def test_cost_computation_local_zero() -> None:
    """النموذج المحلي مجاني."""
    layer = ModelLayer()
    cost = layer.compute_cost("local-fallback", 1000, 1000)
    assert cost == 0.0


def test_cost_summary_by_model() -> None:
    """ملخص التكلفة مفصّل لكل نموذج."""
    layer = ModelLayer()
    layer.log_cost("inv-1", "claude-sonnet-4", 100, 0.0015, 50, "external")
    layer.log_cost("inv-2", "local-fallback", 50, 0.0, 10, "local")
    summary = layer.get_cost_summary()
    assert "claude-sonnet-4" in summary["by_model"]
    assert "local-fallback" in summary["by_model"]


# === 5.5: Model Caching ===


def test_model_cache_hit() -> None:
    """نفس السؤال يُعاد من الذاكرة المؤقتة."""
    layer = ModelLayer()
    # استدعاء أول
    result1 = layer.invoke_with_cache("ما هو Python؟", "local-model", 100)
    assert result1["cached"] is False

    # استدعاء ثاني — يجب أن يكون من الذاكرة
    result2 = layer.invoke_with_cache("ما هو Python؟", "local-model", 100)
    assert result2["cached"] is True
    assert result2["cost_usd"] == 0.0
    assert result2["latency_ms"] == 0


def test_model_cache_miss_different_prompt() -> None:
    """طلب مختلف لا يصيب الذاكرة."""
    layer = ModelLayer()
    layer.invoke_with_cache("سؤال 1", "local-model", 100)
    result = layer.invoke_with_cache("سؤال مختلف", "local-model", 100)
    assert result["cached"] is False


def test_model_cache_different_models() -> None:
    """نفس السؤال لنماذج مختلفة يُخزَّن separately."""
    layer = ModelLayer()
    layer.invoke_with_cache("سؤال مشترك", "model-a", 100)
    result_a = layer.invoke_with_cache("سؤال مشترك", "model-a", 100)
    result_b = layer.invoke_with_cache("سؤال مشترك", "model-b", 100)
    assert result_a["cached"] is True
    assert result_b["cached"] is False


def test_model_cache_persists() -> None:
    """ذاكرة التخزين المؤقت تبقى بعد إعادة التشغيل."""
    layer1 = ModelLayer()
    layer1.invoke_with_cache("اختبار بقاء", "local-model", 100)

    layer2 = ModelLayer()
    result = layer2.invoke_with_cache("اختبار بقاء", "local-model", 100)
    assert result["cached"] is True


# === 5.6: Benchmark ===


def test_benchmark_models() -> None:
    """مقارنة أداء النماذج."""
    layer = ModelLayer()
    prompts = ["سؤال 1", "سؤال 2", "سؤال 3"]
    models = ["local-fallback", "local-model"]
    result = layer.benchmark_models(prompts, models)
    assert "results" in result
    assert "local-fallback" in result["results"]
    assert "local-model" in result["results"]
    assert result["results"]["local-fallback"]["run_count"] == 3


def test_benchmark_shows_cache_effect() -> None:
    """الـ benchmark يظهر تأثير الذاكرة المؤقتة."""
    layer = ModelLayer()
    # استدعاء مسبق لتعبئة الذاكرة
    layer.invoke_with_cache("سؤال مشترك", "local-model", 100)
    # benchmark مع نفس السؤال
    result = layer.benchmark_models(["سؤال مشترك"], ["local-model"])
    assert result["results"]["local-model"]["cache_hits"] >= 1


# === invoke_with_cache integration ===


def test_invoke_returns_real_response() -> None:
    """invoke_with_cache يعيد استجابة حقيقية."""
    layer = ModelLayer()
    result = layer.invoke_with_cache("اختبار", "local-fallback", 100)
    assert "text" in result
    assert len(result["text"]) > 0
    assert result["tokens"] > 0
    assert "invocation_id" in result


def test_invoke_custom_function() -> None:
    """دالة استدعاء مخصصة تعمل."""
    layer = ModelLayer()

    def my_fn(prompt, model, max_tokens):
        return f"رد مخصص على: {prompt}", 10

    result = layer.invoke_with_cache("اختبار مخصص", "custom-model", 100, invoke_fn=my_fn)
    assert "رد مخصص" in result["text"]
    assert result["tokens"] == 10


def test_get_model_layer_singleton() -> None:
    """get_model_layer يعيد نفس النسخة."""
    l1 = get_model_layer()
    l2 = get_model_layer()
    assert l1 is l2
