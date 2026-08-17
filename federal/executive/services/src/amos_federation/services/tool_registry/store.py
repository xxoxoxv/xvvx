"""
AMOS-Federation Tool Registry Store
الهدف: تجريد تخزين الأدوات مع بديل ذاكرة آمن وبذور من tool-index.yaml
النطاق: tool-registry
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from pathlib import Path
from typing import Protocol

from amos_federation.common.schemas import ToolManifestModel


class ToolStore(Protocol):
    """عقد تخزين الأدوات الذي تعتمد عليه واجهات tool-registry."""

    def register(self, tool: ToolManifestModel) -> ToolManifestModel:
        """تسجيل أداة جديدة أو تحديثها."""

    def get(self, tool_id: str) -> ToolManifestModel | None:
        """إرجاع أداة بالمعرّف أو None."""

    def list_all(self) -> list[ToolManifestModel]:
        """إرجاع كل الأدوات المسجلة."""

    def resolve(self, query: str, limit: int = 5) -> list[ToolManifestModel]:
        """حل استعلام نصي إلى أدوات مطابقة بالكلمات المفتاحية."""


class InMemoryToolStore:
    """تنفيذ بسيط معزول في الذاكرة مع مطابقة كلمات مفتاحية حتمية."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolManifestModel] = {}
        self._seed_from_yaml()

    def _seed_from_yaml(self) -> None:
        """تحميل الأدوات الأولية من tool-index.yaml إن وُجد."""
        try:
            import yaml

            for parent in Path(__file__).resolve().parents:
                candidate = parent / "tools" / "registry" / "tool-index.yaml"
                if candidate.exists():
                    data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
                    for entry in data.get("tools", []):
                        tool = ToolManifestModel(
                            tool_id=entry["id"],
                            name=entry["name"],
                            version=entry.get("version", "1.0.0"),
                            risk_level=entry.get("risk_level", "low"),
                            input_schema=entry.get("input_schema", {}),
                            output_schema=entry.get("output_schema", {}),
                        )
                        self._tools[tool.tool_id] = tool
                    break
        except Exception:
            pass  # بديل آمن عند غياب yaml أو الملف

    def register(self, tool: ToolManifestModel) -> ToolManifestModel:
        self._tools[tool.tool_id] = tool
        return tool

    def get(self, tool_id: str) -> ToolManifestModel | None:
        return self._tools.get(tool_id)

    def list_all(self) -> list[ToolManifestModel]:
        return list(self._tools.values())

    def resolve(self, query: str, limit: int = 5) -> list[ToolManifestModel]:
        """مطابقة كلمات مفتاحية حتمية: تطابق اسم الأداة أو معرّفها مع الاستعلام."""
        query_lower = query.lower()
        words = set(query_lower.split())
        scored: list[tuple[int, ToolManifestModel]] = []
        for tool in self._tools.values():
            tool_text = f"{tool.tool_id} {tool.name}".lower()
            tool_words = set(tool_text.split())
            overlap = len(words & tool_words)
            if overlap > 0 or any(w in tool_text for w in words):
                scored.append((overlap, tool))
        scored.sort(key=lambda pair: (-pair[0], pair[1].tool_id))
        return [tool for _, tool in scored[:limit]]
