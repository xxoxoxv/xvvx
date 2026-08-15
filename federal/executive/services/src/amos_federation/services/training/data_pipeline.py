"""
AMOS-Federation Data Collection Pipeline
الهدف: استخراج وتنظيف وتوازن بيانات التدريب من سجل الخبرات
النطاق: training (data pipeline)
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any, Protocol


class DataPipeline(Protocol):
    """عقد خط معالجة بيانات التدريب."""

    def collect(self, experiences: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """استخراج عينات من الخبرات."""

    def balance(self, samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """موازنة العينات حسب النوع."""

    def deduplicate(self, samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """إزالة التكرارات."""

    def create_bom(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        """إنشاء Data BOM (Bill of Materials)."""


class InMemoryDataPipeline:
    """خط معالجة بيانات خفيف."""

    def __init__(self) -> None:
        self._datasets: list[dict[str, Any]] = []

    def collect(self, experiences: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """استخراج عينات قابلة للتدريب من سجل الخبرات."""
        samples: list[dict[str, Any]] = []
        for exp in experiences:
            outcome = exp.get("outcome", {})
            sample = {
                "sample_id": f"sample-{uuid.uuid4()}",
                "source_experience": exp.get("experience_id"),
                "type": exp.get("type", "success"),
                "input": outcome.get("input", ""),
                "output": outcome.get("output", ""),
                "domain": outcome.get("domain", "unknown"),
                "quality_score": exp.get("quality_score"),
                "agent_id": exp.get("agent_id"),
                "model_used": exp.get("model_used"),
                "timestamp": exp.get("created_at"),
            }
            # تجاهل العينات الفارغة
            if sample["input"] or sample["output"]:
                samples.append(sample)
        return samples

    def balance(
        self, samples: list[dict[str, Any]], target_per_type: int = 50
    ) -> list[dict[str, Any]]:
        """موازنة العينات بحيث لا يطغى نوع على آخر."""
        by_type: dict[str, list[dict[str, Any]]] = {}
        for s in samples:
            t = s["type"]
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(s)

        balanced: list[dict[str, Any]] = []
        for t, group in by_type.items():
            # أخذ أول target_per_type عينة من كل نوع
            balanced.extend(group[:target_per_type])
        return balanced

    def deduplicate(self, samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """إزالة العينات المكررة بناءً على hash المدخلات والمخرجات."""
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for s in samples:
            key = hashlib.sha256(
                f"{s['input']}:{s['output']}".encode()
            ).hexdigest()
            if key not in seen:
                seen.add(key)
                unique.append(s)
        return unique

    def create_bom(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        """إنشاء Data BOM (Bill of Materials) للبيانات."""
        by_type: dict[str, int] = {}
        by_domain: dict[str, int] = {}
        for s in samples:
            by_type[s["type"]] = by_type.get(s["type"], 0) + 1
            by_domain[s["domain"]] = by_domain.get(s["domain"], 0) + 1

        return {
            "bom_id": f"bom-{uuid.uuid4()}",
            "created_at": datetime.now(UTC).isoformat(),
            "total_samples": len(samples),
            "by_type": by_type,
            "by_domain": by_domain,
            "hash": hashlib.sha256(
                str(sorted(by_type.items())).encode()
            ).hexdigest()[:16],
            "version": "1.0",
        }

    def create_dataset(
        self, experiences: list[dict[str, Any]], target_per_type: int = 50
    ) -> dict[str, Any]:
        """خط كامل: استخراج → تنظيف → موازنة → BOM."""
        collected = self.collect(experiences)
        deduped = self.deduplicate(collected)
        balanced = self.balance(deduped, target_per_type)
        bom = self.create_bom(balanced)
        dataset = {
            "dataset_id": f"ds-{uuid.uuid4()}",
            "created_at": datetime.now(UTC).isoformat(),
            "bom": bom,
            "sample_count": len(balanced),
            "samples": balanced,
            "status": "ready",
        }
        self._datasets.append(dataset)
        return dataset

    def list_datasets(self, limit: int = 50) -> list[dict[str, Any]]:
        """عرض البيانات."""
        return [
            {k: v for k, v in d.items() if k != "samples"}
            for d in self._datasets[:limit]
        ]

    def get_dataset(self, dataset_id: str) -> dict[str, Any] | None:
        """إرجاع بيانات بالمعرّف."""
        for d in self._datasets:
            if d["dataset_id"] == dataset_id:
                return d
        return None
