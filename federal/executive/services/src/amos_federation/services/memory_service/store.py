"""
AMOS-Federation Memory Store
الهدف: تجريد تخزين الذاكرة مع بديل ذاكرة آمن ومطابقة كلمات مفتاحية
النطاق: memory-service
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import hashlib
import math
import re
from collections import defaultdict
from typing import Any, Protocol

from amos_federation.common.schemas import MemoryQuery, MemoryStore as MemoryStoreModel


class MemoryBackend(Protocol):
    """عقد خلفية تخزين الذاكرة."""

    def store(self, key: str, value: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        """حفظ عنصر ذاكرة وإرجاعه."""

    def query(self, query: str, tenant_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """البحث في الذاكرة بنص استعلام."""

    def get(self, key: str, tenant_id: str | None = None) -> dict[str, Any] | None:
        """إرجاع عنصر بالمفتاح."""


def _tokenize(text: str) -> list[str]:
    """تقسيم النص إلى كلمات صغيرة للمطابقة."""
    return [w.lower() for w in re.findall(r"\w+", text) if len(w) >= 2]


def _keyword_similarity(query_words: list[str], doc_words: list[str]) -> float:
    """حساب تشابه كلمات مفتاحية كنسبة Jaccard معدّلة."""
    if not query_words or not doc_words:
        return 0.0
    q_set = set(query_words)
    d_set = set(doc_words)
    intersection = len(q_set & d_set)
    if intersection == 0:
        return 0.0
    union = len(q_set | d_set)
    return intersection / union


class InMemoryVectorStore:
    """ذاكرة متجهية خفيفة مع مطابقة كلمات مفتاحية حتمية."""

    def __init__(self) -> None:
        self._items: list[dict[str, Any]] = []
        self._index: dict[str, dict[str, Any]] = defaultdict(dict)

    def store(self, key: str, value: dict[str, Any], tenant_id: str | None = None) -> dict[str, Any]:
        """حفظ عنصر ذاكرة مع فهرسة كلمات مفتاحية."""
        text = f"{key} {value.get('content', '')} {value.get('summary', '')}"
        item = {
            "key": key,
            "value": value,
            "tenant_id": tenant_id,
            "tokens": _tokenize(text),
            "item_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
        }
        # تحديث إن وُجد سابق بنفس المفتاح
        existing = next((i for i, x in enumerate(self._items) if x["key"] == key and x.get("tenant_id") == tenant_id), None)
        if existing is not None:
            self._items[existing] = item
        else:
            self._items.append(item)
        tenant_key = tenant_id or "_global"
        self._index[tenant_key][key] = item
        return {"key": key, "value": value, "tenant_id": tenant_id}

    def query(self, query: str, tenant_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """البحث في الذاكرة بتشابه الكلمات المفتاحية."""
        query_words = _tokenize(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for item in self._items:
            if tenant_id and item.get("tenant_id") not in (tenant_id, None):
                continue
            score = _keyword_similarity(query_words, item["tokens"])
            if score > 0:
                scored.append((score, {"key": item["key"], "value": item["value"], "score": round(score, 4)}))
        scored.sort(key=lambda pair: (-pair[0], pair[1]["key"]))
        return [item for _, item in scored[:limit]]

    def get(self, key: str, tenant_id: str | None = None) -> dict[str, Any] | None:
        """إرجاع عنصر بالمفتاح."""
        tenant_key = tenant_id or "_global"
        item = self._index[tenant_key].get(key)
        if item:
            return {"key": item["key"], "value": item["value"], "tenant_id": item.get("tenant_id")}
        # بحث عام
        for item in self._items:
            if item["key"] == key:
                return {"key": item["key"], "value": item["value"], "tenant_id": item.get("tenant_id")}
        return None

    def count(self, tenant_id: str | None = None) -> int:
        """عدد العناصر المخزنة."""
        if tenant_id is None:
            return len(self._items)
        return sum(1 for item in self._items if item.get("tenant_id") in (tenant_id, None))
