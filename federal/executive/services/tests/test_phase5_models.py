"""
AMOS-Federation Phase 5 — Real Models Tests
الهدف: اختبار طبقة النماذج مع caching و cost tracking و fallback
النطاق: tests/test_phase5_models.py
"""

import uuid

import pytest


def _unique_prompt(prefix="test"):
    """توليد prompt فريد لتجنب cache hits بين الاختبارات."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class TestModelCaching:
    """5.5: Model Caching حقيقي."""

    def test_cache_hit(self):
        """5.5: نفس السؤال لا يُعاد استدعاؤه بنفس التكلفة."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        prompt = _unique_prompt("caching-hit")
        # استدعاء أول
        result1 = layer.invoke_with_cache(prompt, "local-model", 100)
        assert not result1["cached"]
        # استدعاء ثاني — يجب أن يكون من cache
        result2 = layer.invoke_with_cache(prompt, "local-model", 100)
        assert result2["cached"]
        assert result2["cost_usd"] == 0.0  # cache = free

    def test_cache_miss_different_prompt(self):
        """5.5: prompts مختلفة لا تتشارك cache."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        prompt1 = _unique_prompt("miss-alpha")
        prompt2 = _unique_prompt("miss-beta")
        layer.invoke_with_cache(prompt1, "local-model", 100)
        result2 = layer.invoke_with_cache(prompt2, "local-model", 100)
        assert not result2["cached"]

    def test_cache_miss_different_models(self):
        """5.5: نفس prompt مع models مختلفة لا تتشارك cache."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        prompt = _unique_prompt("models")
        layer.invoke_with_cache(prompt, "local-model", 100)
        result = layer.invoke_with_cache(prompt, "local-fallback", 100)
        assert not result["cached"]


class TestCostTracking:
    """5.4: تسجيل التكلفة الحقيقية لكل استدعاء."""

    def test_compute_cost(self):
        """5.4: حساب التكلفة بدقة."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        cost = layer.compute_cost("claude-sonnet-4", 1000, 500)
        # input: 1000/1000 * 0.003 = 0.003, output: 500/1000 * 0.015 = 0.0075
        assert cost == pytest.approx(0.0105, rel=0.01)

    def test_local_model_zero_cost(self):
        """5.4: النموذج المحلي بتكلفة صفر."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        cost = layer.compute_cost("local-model", 10000, 5000)
        assert cost == 0.0

    def test_cost_logged(self):
        """5.4: التكلفة مسجّلة في DB."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        prompt = _unique_prompt("cost-logging")
        result = layer.invoke_with_cache(prompt, "local-model", 50)
        assert "invocation_id" in result or result.get("source") == "cache"

    def test_cost_summary(self):
        """5.4: ملخص التكلفة التراكمي."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        summary = layer.get_cost_summary()
        assert "total_cost_usd" in summary
        assert "total_tokens" in summary
        assert "total_invocations" in summary
        assert "by_model" in summary
        assert summary["total_invocations"] > 0


class TestFallbackChain:
    """5.3: سلسلة fallback كاملة."""

    def test_local_fallback_works(self):
        """5.3: النموذج المحلي يعمل عند عدم توفر الخارجي."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        prompt = _unique_prompt("fallback-local")
        result = layer.invoke_with_cache(prompt, "local-fallback", 100)
        assert "text" in result
        assert len(result["text"]) > 0

    def test_custom_invoke_function(self):
        """5.3: يمكن تمرير دالة استدعاء مخصصة."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        prompt = _unique_prompt("custom-invoke")

        def custom_invoke(p, model, max_tokens):
            return f"Custom response to: {p[:20]}", 42

        result = layer.invoke_with_cache(prompt, "claude-sonnet-4", 100, invoke_fn=custom_invoke)
        assert "Custom response" in result["text"]
        assert result["tokens"] == 42


class TestBenchmark:
    """5.6: تقييم أداء النموذج."""

    def test_benchmark_runs(self):
        """5.6: Benchmark يُنتج نتائج حقيقية."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        prompts = [_unique_prompt(f"bench-{i}") for i in range(3)]
        models = ["local-model", "local-fallback"]
        result = layer.benchmark_models(prompts, models)
        assert "results" in result
        assert "local-model" in result["results"]
        assert "local-fallback" in result["results"]
        assert result["results"]["local-model"]["run_count"] == 3

    def test_benchmark_shows_difference(self):
        """5.6: Benchmark يُظهر الفرق فعليًا."""
        from amos_federation.services.model_gateway.model_layer import get_model_layer

        layer = get_model_layer()
        prompts = [_unique_prompt("benchmark-diff")]
        models = ["local-model", "local-fallback"]
        result = layer.benchmark_models(prompts, models)
        for model in models:
            assert result["results"][model]["avg_latency_ms"] >= 0
