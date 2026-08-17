"""
AMOS-Federation Experience Store
الهدف: تخزين الخبرات (نجاح/فشل/فجوة) مع تتبع المصدر
النطاق: evaluation + experience
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import uuid
from datetime import UTC, datetime
from typing import Any, Protocol


class ExperienceBackend(Protocol):
    """عقد خلفية تخزين الخبرات."""

    def record(self, experience: dict[str, Any]) -> dict[str, Any]:
        """تسجيل خبرة جديدة."""

    def get(self, experience_id: str) -> dict[str, Any] | None:
        """إرجاع خبرة بالمعرّف."""

    def list_all(
        self,
        exp_type: str | None = None,
        agent_id: str | None = None,
        min_score: float | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """عرض الخبرات مع فلترة."""


class InMemoryExperienceStore:
    """ذاكرة خبرات خفيفة مع فلترة وتتبع مصدر."""

    def __init__(self) -> None:
        self._experiences: list[dict[str, Any]] = []

    def record(self, experience: dict[str, Any]) -> dict[str, Any]:
        """تسجيل خبرة جديدة مع توقيت ومصدر."""
        exp_id = experience.get("experience_id") or f"exp-{uuid.uuid4()}"
        timestamp = datetime.now(UTC).isoformat()

        provenance = experience.get("provenance", {})
        if not provenance:
            provenance = {"source": "live_operation", "verified": True, "recorded_at": timestamp}

        record = {
            "experience_id": exp_id,
            "task_id": experience.get("task_id"),
            "type": experience.get("type", "success"),
            "agent_id": experience.get("agent_id"),
            "model_used": experience.get("model_used"),
            "outcome": experience.get("outcome", {}),
            "quality_score": experience.get("quality_score"),
            "provenance": provenance,
            "created_at": timestamp,
        }
        self._experiences.append(record)
        return record

    def get(self, experience_id: str) -> dict[str, Any] | None:
        """إرجاع خبرة بالمعرّف."""
        for exp in self._experiences:
            if exp["experience_id"] == experience_id:
                return exp
        return None

    def list_all(
        self,
        exp_type: str | None = None,
        agent_id: str | None = None,
        min_score: float | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """عرض الخبرات مع فلترة اختيارية."""
        results = self._experiences
        if exp_type:
            results = [e for e in results if e["type"] == exp_type]
        if agent_id:
            results = [e for e in results if e.get("agent_id") == agent_id]
        if min_score is not None:
            results = [
                e
                for e in results
                if e.get("quality_score") is not None and e["quality_score"] >= min_score
            ]
        return results[:limit]

    def count(self) -> int:
        """عدد الخبرات المخزنة."""
        return len(self._experiences)

    def by_type(self) -> dict[str, int]:
        """توزيع الخبرات حسب النوع."""
        counts: dict[str, int] = {}
        for exp in self._experiences:
            t = exp["type"]
            counts[t] = counts.get(t, 0) + 1
        return counts
