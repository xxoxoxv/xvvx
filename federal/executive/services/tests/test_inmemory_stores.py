"""
اختبارات مخازن الذاكرة (In-Memory Stores)
الهدف: رفع تغطية الأفرع لوحدات store/catalog غير المغطاة
النطاق: critic/evaluation/memory_service/tool_registry
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import pytest

from amos_federation.common.schemas import ToolManifestModel
from amos_federation.services.critic.store import InMemoryCriticStore
from amos_federation.services.evaluation.store import InMemoryExperienceStore
from amos_federation.services.memory_service.store import (
    InMemoryVectorStore,
    _keyword_similarity,
    _tokenize,
)
from amos_federation.services.tool_registry.catalog import (
    TOOL_CATALOG,
    get_catalog_stats,
    list_all_tools,
    list_tools_by_category,
)
from amos_federation.services.tool_registry.store import InMemoryToolStore


# =============================================================================
# Critic Store
# =============================================================================
class TestInMemoryCriticStore:
    def test_review_generates_id_when_missing(self) -> None:
        store = InMemoryCriticStore()
        rec = store.review({"quality_score": 0.9})
        assert rec["review_id"].startswith("rev-")
        assert rec["approved"] is False
        assert rec["feedback"] == ""
        assert rec["criteria"] == {}

    def test_review_uses_provided_id(self) -> None:
        store = InMemoryCriticStore()
        rec = store.review({"review_id": "rev-1", "quality_score": 0.8})
        assert rec["review_id"] == "rev-1"

    def test_get_found_and_not_found(self) -> None:
        store = InMemoryCriticStore()
        store.review({"review_id": "rev-1", "quality_score": 0.5})
        assert store.get("rev-1") is not None
        assert store.get("rev-missing") is None

    def test_list_all_no_filters(self) -> None:
        store = InMemoryCriticStore()
        store.review({"review_id": "r1", "task_id": "t1", "quality_score": 0.9})
        store.review({"review_id": "r2", "task_id": "t2", "quality_score": 0.4})
        assert len(store.list_all()) == 2

    def test_list_all_filter_by_task_id(self) -> None:
        store = InMemoryCriticStore()
        store.review({"review_id": "r1", "task_id": "t1", "quality_score": 0.9})
        store.review({"review_id": "r2", "task_id": "t2", "quality_score": 0.4})
        assert len(store.list_all(task_id="t1")) == 1

    def test_list_all_filter_by_min_score(self) -> None:
        store = InMemoryCriticStore()
        store.review({"review_id": "r1", "quality_score": 0.9})
        store.review({"review_id": "r2", "quality_score": 0.4})
        store.review({"review_id": "r3", "quality_score": None})
        assert len(store.list_all(min_score=0.5)) == 1

    def test_list_all_limit(self) -> None:
        store = InMemoryCriticStore()
        for i in range(5):
            store.review({"review_id": f"r{i}", "quality_score": 0.5})
        assert len(store.list_all(limit=2)) == 2

    def test_count(self) -> None:
        store = InMemoryCriticStore()
        store.review({"quality_score": 0.5})
        store.review({"quality_score": 0.6})
        assert store.count() == 2

    def test_average_score_empty_and_with_values(self) -> None:
        store = InMemoryCriticStore()
        assert store.average_score() == 0.0
        store.review({"quality_score": 0.8})
        store.review({"quality_score": 0.4})
        assert store.average_score() == pytest.approx(0.6)
        store.review({"quality_score": None})
        assert store.average_score() == pytest.approx(0.6)


# =============================================================================
# Experience Store
# =============================================================================
class TestInMemoryExperienceStore:
    def test_record_generates_id_when_missing(self) -> None:
        store = InMemoryExperienceStore()
        rec = store.record({"type": "success"})
        assert rec["experience_id"].startswith("exp-")
        assert rec["provenance"]["source"] == "live_operation"
        assert rec["provenance"]["verified"] is True

    def test_record_uses_provided_id_and_provenance(self) -> None:
        store = InMemoryExperienceStore()
        rec = store.record({"experience_id": "exp-1", "provenance": {"source": "imported"}})
        assert rec["experience_id"] == "exp-1"
        assert rec["provenance"]["source"] == "imported"

    def test_get_found_and_not_found(self) -> None:
        store = InMemoryExperienceStore()
        store.record({"experience_id": "exp-1", "type": "success"})
        assert store.get("exp-1") is not None
        assert store.get("exp-missing") is None

    def test_list_all_no_filters(self) -> None:
        store = InMemoryExperienceStore()
        store.record({"type": "success"})
        store.record({"type": "failure"})
        assert len(store.list_all()) == 2

    def test_list_all_filter_by_type(self) -> None:
        store = InMemoryExperienceStore()
        store.record({"type": "success"})
        store.record({"type": "failure"})
        assert len(store.list_all(exp_type="failure")) == 1

    def test_list_all_filter_by_agent(self) -> None:
        store = InMemoryExperienceStore()
        store.record({"agent_id": "a1"})
        store.record({"agent_id": "a2"})
        assert len(store.list_all(agent_id="a1")) == 1

    def test_list_all_filter_by_min_score(self) -> None:
        store = InMemoryExperienceStore()
        store.record({"quality_score": 0.9})
        store.record({"quality_score": 0.4})
        store.record({"quality_score": None})
        assert len(store.list_all(min_score=0.5)) == 1

    def test_count_and_by_type(self) -> None:
        store = InMemoryExperienceStore()
        store.record({"type": "success"})
        store.record({"type": "success"})
        store.record({"type": "failure"})
        assert store.count() == 3
        assert store.by_type() == {"success": 2, "failure": 1}


# =============================================================================
# Memory Vector Store
# =============================================================================
class TestInMemoryVectorStore:
    def test_tokenize(self) -> None:
        assert _tokenize("Hello world a") == ["hello", "world"]
        assert _tokenize("") == []

    def test_keyword_similarity_edges(self) -> None:
        assert _keyword_similarity([], ["a"]) == 0.0
        assert _keyword_similarity(["a"], []) == 0.0
        assert _keyword_similarity(["a"], ["b"]) == 0.0
        assert _keyword_similarity(["a", "b"], ["a", "b"]) == 1.0
        assert 0.0 < _keyword_similarity(["a", "b"], ["a"]) < 1.0

    def test_store_new_and_update_existing(self) -> None:
        store = InMemoryVectorStore()
        store.store("k1", {"content": "alpha beta"})
        store.store("k1", {"content": "gamma delta"})  # update existing
        assert store.count() == 1

    def test_query_with_and_without_match(self) -> None:
        store = InMemoryVectorStore()
        store.store("k1", {"content": "alpha beta"})
        store.store("k2", {"content": "gamma delta"})
        assert len(store.query("alpha")) == 1
        assert store.query("alpha")[0]["key"] == "k1"
        assert len(store.query("zzz none")) == 0

    def test_query_with_tenant_filter(self) -> None:
        store = InMemoryVectorStore()
        store.store("k1", {"content": "alpha"}, tenant_id="t1")
        store.store("k2", {"content": "alpha"}, tenant_id="t2")
        # tenant filter excludes other-tenant items
        assert len(store.query("alpha", tenant_id="t1")) == 1

    def test_get_found_in_index_and_fallback_and_missing(self) -> None:
        store = InMemoryVectorStore()
        store.store("k1", {"content": "alpha"})
        # found in index
        assert store.get("k1") is not None
        # fallback global search (same key, found)
        assert store.get("k1", tenant_id="other") is not None
        # missing
        assert store.get("missing-key") is None

    def test_count_with_tenant(self) -> None:
        store = InMemoryVectorStore()
        store.store("k1", {"content": "alpha"}, tenant_id="t1")
        store.store("k2", {"content": "beta"}, tenant_id="t2")
        store.store("k3", {"content": "gamma"})  # global
        assert store.count() == 3
        assert store.count(tenant_id="t1") == 2  # t1 + global(None)


# =============================================================================
# Tool Catalog
# =============================================================================
class TestToolCatalog:
    def test_get_catalog_stats(self) -> None:
        stats = get_catalog_stats()
        assert stats["total_tools"] == len(TOOL_CATALOG)
        assert "data_extraction" in stats["categories"]
        assert stats["risk_levels"]["low"] > 0
        assert len(stats["category_names"]) == 12

    def test_list_tools_by_category(self) -> None:
        tools = list_tools_by_category("data_extraction")
        assert len(tools) > 0
        assert all(t["category"] == "data_extraction" for t in tools)

    def test_list_tools_by_category_empty(self) -> None:
        assert list_tools_by_category("nonexistent") == []

    def test_list_all_tools(self) -> None:
        tools = list_all_tools()
        assert len(tools) == len(TOOL_CATALOG)
        assert all("tool_id" in t for t in tools)


# =============================================================================
# Tool Registry Store
# =============================================================================
class TestInMemoryToolStore:
    def _manifest(self, tid: str = "tool-1", name: str = "Search Tool") -> ToolManifestModel:
        return ToolManifestModel(tool_id=tid, name=name, risk_level="low")

    def test_register_and_get(self) -> None:
        store = InMemoryToolStore()
        tool = store.register(self._manifest())
        assert tool.tool_id == "tool-1"
        assert store.get("tool-1") is not None
        assert store.get("missing") is None

    def test_list_all(self) -> None:
        store = InMemoryToolStore()
        store.register(self._manifest("a", "Alpha Tool"))
        store.register(self._manifest("b", "Beta Tool"))
        assert len(store.list_all()) >= 2

    def test_resolve_by_overlap_and_substring(self) -> None:
        store = InMemoryToolStore()
        store.register(self._manifest("search", "Search Engine"))
        store.register(self._manifest("calc", "Calculator"))
        # overlap match (word "search" in name)
        results = store.resolve("search")
        assert any(r.tool_id == "search" for r in results)
        # substring match ("calc" in tool_text)
        results = store.resolve("calc tool")
        assert any(r.tool_id == "calc" for r in results)
        # no match
        assert store.resolve("zzz none") == []

    def test_seed_from_yaml_absent_safe(self) -> None:
        # Initializing without a yaml file must not raise (safe fallback)
        store = InMemoryToolStore()
        assert store.list_all() is not None
