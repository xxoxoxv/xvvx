"""
AMOS-Federation Critic Store
الهدف: تخزين مراجعات النتائج مع درجات الجودة والتغذية الراجعة
النطاق: critic
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import uuid
from datetime import UTC, datetime
from typing import Any, Protocol


class CriticStore(Protocol):
    """عقد تخزين مراجعات الناقد."""

    def review(self, review_data: dict[str, Any]) -> dict[str, Any]:
        """تسجيل مراجعة جديدة."""

    def get(self, review_id: str) -> dict[str, Any] | None:
        """إرجاع مراجعة بالمعرّف."""

    def list_all(
        self,
        task_id: str | None = None,
        min_score: float | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """عرض المراجعات مع فلترة."""


class InMemoryCriticStore:
    """ذاكرة مراجعات خفيفة مع فلترة."""

    def __init__(self) -> None:
        self._reviews: list[dict[str, Any]] = []

    def review(self, review_data: dict[str, Any]) -> dict[str, Any]:
        """تسجيل مراجعة جديدة مع درجة جودة وتغذية راجعة."""
        review_id = review_data.get("review_id") or f"rev-{uuid.uuid4()}"
        timestamp = datetime.now(UTC).isoformat()
        record = {
            "review_id": review_id,
            "task_id": review_data.get("task_id"),
            "agent_id": review_data.get("agent_id"),
            "quality_score": review_data.get("quality_score"),
            "feedback": review_data.get("feedback", ""),
            "approved": review_data.get("approved", False),
            "criteria": review_data.get("criteria", {}),
            "created_at": timestamp,
        }
        self._reviews.append(record)
        return record

    def get(self, review_id: str) -> dict[str, Any] | None:
        """إرجاع مراجعة بالمعرّف."""
        for rev in self._reviews:
            if rev["review_id"] == review_id:
                return rev
        return None

    def list_all(
        self,
        task_id: str | None = None,
        min_score: float | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """عرض المراجعات مع فلترة."""
        results = self._reviews
        if task_id:
            results = [r for r in results if r.get("task_id") == task_id]
        if min_score is not None:
            results = [
                r
                for r in results
                if r.get("quality_score") is not None and r["quality_score"] >= min_score
            ]
        return results[:limit]

    def count(self) -> int:
        """عدد المراجعات."""
        return len(self._reviews)

    def average_score(self) -> float:
        """متوسط درجات الجودة."""
        scores = [r["quality_score"] for r in self._reviews if r.get("quality_score") is not None]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)
