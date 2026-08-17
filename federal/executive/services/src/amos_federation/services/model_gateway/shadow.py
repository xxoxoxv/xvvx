"""
AMOS-Federation Shadow Testing Framework
الهدف: تشغيل نموذجين بالتوازي (ألفا + بيتا) ومقارنة النتائج
النطاق: model-gateway (shadow)
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import time
import uuid
from datetime import UTC, datetime
from typing import Any, Protocol


class ShadowStore(Protocol):
    """عقد تخزين نتائج Shadow Testing."""

    def record(self, result: dict[str, Any]) -> dict[str, Any]:
        """تسجيل نتيجة shadow."""

    def list_all(self, limit: int = 50) -> list[dict[str, Any]]:
        """عرض النتائج."""

    def get(self, shadow_id: str) -> dict[str, Any] | None:
        """إرجاع نتيجة بالمعرّف."""


class InMemoryShadowStore:
    """ذاكرة نتائج shadow خفيفة."""

    def __init__(self) -> None:
        self._results: list[dict[str, Any]] = []

    def record(self, result: dict[str, Any]) -> dict[str, Any]:
        """تسجيل نتيجة shadow مع مقارنة."""
        shadow_id = f"shadow-{uuid.uuid4()}"
        timestamp = datetime.now(UTC).isoformat()

        alpha = result.get("alpha", {})
        beta = result.get("beta", {})

        # مقارنة حتمية
        alpha_text = alpha.get("text", "")
        beta_text = beta.get("text", "")
        text_match = alpha_text == beta_text
        text_similarity = _text_similarity(alpha_text, beta_text)

        latency_diff = alpha.get("latency_ms", 0) - beta.get("latency_ms", 0)
        token_diff = alpha.get("tokens_used", 0) - beta.get("tokens_used", 0)

        record = {
            "shadow_id": shadow_id,
            "timestamp": timestamp,
            "prompt": result.get("prompt", ""),
            "alpha": alpha,
            "beta": beta,
            "comparison": {
                "text_match": text_match,
                "text_similarity": round(text_similarity, 4),
                "latency_diff_ms": latency_diff,
                "token_diff": token_diff,
            },
            "metrics": {
                "alpha_quality": round(text_similarity, 4),
                "beta_latency": beta.get("latency_ms", 0),
                "alpha_latency": alpha.get("latency_ms", 0),
                "cost_diff": token_diff * 0.0001,
            },
        }
        self._results.append(record)
        return record

    def list_all(self, limit: int = 50) -> list[dict[str, Any]]:
        """عرض النتائج."""
        return self._results[:limit]

    def get(self, shadow_id: str) -> dict[str, Any] | None:
        """إرجاع نتيجة بالمعرّف."""
        for r in self._results:
            if r["shadow_id"] == shadow_id:
                return r
        return None

    def count(self) -> int:
        """عدد النتائج."""
        return len(self._results)

    def summary(self) -> dict[str, Any]:
        """ملخص إحصائي."""
        if not self._results:
            return {"total": 0, "avg_similarity": 0.0, "avg_latency_diff": 0}
        similarities = [r["comparison"]["text_similarity"] for r in self._results]
        latency_diffs = [r["comparison"]["latency_diff_ms"] for r in self._results]
        return {
            "total": len(self._results),
            "avg_similarity": round(sum(similarities) / len(similarities), 4),
            "avg_latency_diff_ms": round(sum(latency_diffs) / len(latency_diffs), 2),
        }


def _text_similarity(text_a: str, text_b: str) -> float:
    """حساب تشابه نصي بنسبة تداخل الكلمات (Jaccard)."""
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def _alpha_response(prompt: str) -> dict[str, Any]:
    """استجابة ألفا (النموذج الأساسي)."""
    start = time.monotonic()
    text = f"[alpha] تمت معالجة: {prompt[:150]}"
    latency = int((time.monotonic() - start) * 1000)
    return {
        "text": text,
        "model_used": "alpha-local",
        "tokens_used": len(text.split()),
        "latency_ms": latency,
    }


def _beta_response(prompt: str) -> dict[str, Any]:
    """استجابة بيتا (النموذج المرشح)."""
    start = time.monotonic()
    text = f"[beta] تمت معالجة الطلب: {prompt[:150]}"
    latency = int((time.monotonic() - start) * 1000) + 5  # بيتا أبطأ قليلاً
    return {
        "text": text,
        "model_used": "beta-candidate",
        "tokens_used": len(text.split()),
        "latency_ms": latency,
    }


def run_shadow_test(prompt: str) -> dict[str, Any]:
    """تشغيل اختبار shadow: توجيه الطلب لكلا النموذجين ومقارنة النتائج."""
    alpha = _alpha_response(prompt)
    beta = _beta_response(prompt)
    store = InMemoryShadowStore()
    return store.record({"prompt": prompt, "alpha": alpha, "beta": beta})
