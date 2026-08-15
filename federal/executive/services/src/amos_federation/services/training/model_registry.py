"""
AMOS-Federation Model Registry
الهدف: تسجيل وإدارة النماذج المدربة مع Model Cards
النطاق: training (model registry)
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import uuid
from datetime import UTC, datetime
from typing import Any, Protocol


class ModelRegistryStore(Protocol):
    """عقد تخزين النماذج."""

    def register(self, model_data: dict[str, Any]) -> dict[str, Any]:
        """تسجيل نموذج جديد."""

    def get(self, model_id: str) -> dict[str, Any] | None:
        """إرجاع نموذج بالمعرّف."""

    def list_all(self, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """عرض النماذج."""

    def update_status(self, model_id: str, status: str) -> dict[str, Any] | None:
        """تحديث حالة نموذج."""


class InMemoryModelRegistry:
    """ذاكرة نماذج خفيفة مع Model Cards."""

    def __init__(self) -> None:
        self._models: list[dict[str, Any]] = []

    def register(self, model_data: dict[str, Any]) -> dict[str, Any]:
        """تسجيل نموذج جديد مع Model Card تلقائي."""
        model_id = model_data.get("model_id") or f"model-{uuid.uuid4()}"
        timestamp = datetime.now(UTC).isoformat()

        # إنشاء Model Card
        model_card = {
            "model_id": model_id,
            "name": model_data.get("name", "unnamed"),
            "version": model_data.get("version", "1.0"),
            "base_model": model_data.get("base_model", "unknown"),
            "training_dataset": model_data.get("dataset_id"),
            "training_date": timestamp,
            "training_method": model_data.get("training_method", "LoRA"),
            "hyperparameters": model_data.get("hyperparameters", {}),
            "metrics": model_data.get("metrics", {}),
            "description": model_data.get("description", ""),
            "license": model_data.get("license", "proprietary"),
            "intended_use": model_data.get("intended_use", ""),
            "limitations": model_data.get("limitations", []),
            "knowledge_injection": model_data.get("knowledge_injection", False),
        }

        record = {
            "model_id": model_id,
            "model_card": model_card,
            "status": model_data.get("status", "registered"),
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        self._models.append(record)
        return record

    def get(self, model_id: str) -> dict[str, Any] | None:
        """إرجاع نموذج بالمعرّف."""
        for m in self._models:
            if m["model_id"] == model_id:
                return m
        return None

    def list_all(
        self, status: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """عرض النماذج مع فلترة اختيارية."""
        results = self._models
        if status:
            results = [m for m in results if m["status"] == status]
        return results[:limit]

    def update_status(self, model_id: str, new_status: str) -> dict[str, Any] | None:
        """تحديث حالة نموذج (registered → trained → evaluated → promoted)."""
        for m in self._models:
            if m["model_id"] == model_id:
                m["status"] = new_status
                m["updated_at"] = datetime.now(UTC).isoformat()
                return m
        return None

    def count(self) -> int:
        """عدد النماذج."""
        return len(self._models)
