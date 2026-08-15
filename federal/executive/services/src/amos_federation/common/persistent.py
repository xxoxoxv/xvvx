"""
AMOS-Federation Persistent Stores
الهدف: تخزين دائم بـ SQLAlchemy (SQLite/PostgreSQL) بدلاً من In-Memory
النطاق: common/persistent
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from amos_federation.common.database import (
    AgentModel,
    AuditEntryModel,
    Base,
    ExperienceModel,
    MemoryModel,
    ReviewModel,
    TaskModel,
    ToolModel,
    get_engine,
    get_session_factory,
    init_db,
)
from amos_federation.common.schemas import ToolManifestModel

# تهيئة قاعدة البيانات عند الاستيراد
init_db()


class PersistentToolStore:
    """تخزين الأدوات الدائم بـ SQLAlchemy."""

    def __init__(self) -> None:
        self._seed_from_yaml()

    def _seed_from_yaml(self) -> None:
        """تحميل الأدوات الأولية من tool-index.yaml إن وُجد ولم تُسجَّل بعد."""
        try:
            import yaml
            from pathlib import Path

            SessionLocal = get_session_factory()
            session = SessionLocal()
            try:
                if session.query(ToolModel).count() > 0:
                    return
                for parent in Path(__file__).resolve().parents:
                    candidate = parent / "tools" / "registry" / "tool-index.yaml"
                    if candidate.exists():
                        data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
                        for entry in data.get("tools", []):
                            tool = ToolModel(
                                id=entry["id"],
                                name=entry["name"],
                                description=entry.get("description", ""),
                                category=entry.get("category", "general"),
                                keywords=entry.get("keywords", []),
                                permissions_required=entry.get("permissions_required", []),
                            )
                            session.merge(tool)
                        session.commit()
                        break
            finally:
                session.close()
        except Exception:
            pass

    def register(self, tool: ToolManifestModel) -> ToolManifestModel:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            db_tool = ToolModel(
                id=tool.tool_id,
                name=tool.name,
                description="",
                category="general",
                keywords=[],
                permissions_required=[],
            )
            session.merge(db_tool)
            session.commit()
            return tool
        finally:
            session.close()

    def get(self, tool_id: str) -> ToolManifestModel | None:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            row = session.query(ToolModel).filter(ToolModel.id == tool_id).first()
            if row is None:
                return None
            return ToolManifestModel(
                tool_id=row.id,
                name=row.name,
                version="1.0.0",
                risk_level="low",
                input_schema={},
                output_schema={},
            )
        finally:
            session.close()

    def list_all(self) -> list[ToolManifestModel]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            rows = session.query(ToolModel).all()
            return [
                ToolManifestModel(
                    tool_id=row.id,
                    name=row.name,
                    version="1.0.0",
                    risk_level="low",
                    input_schema={},
                    output_schema={},
                )
                for row in rows
            ]
        finally:
            session.close()

    def resolve(self, query: str, limit: int = 5) -> list[ToolManifestModel]:
        query_lower = query.lower()
        words = set(query_lower.split())
        all_tools = self.list_all()
        scored: list[tuple[int, ToolManifestModel]] = []
        for tool in all_tools:
            tool_text = f"{tool.tool_id} {tool.name}".lower()
            tool_words = set(tool_text.split())
            overlap = len(words & tool_words)
            if overlap > 0 or any(w in tool_text for w in words):
                scored.append((overlap, tool))
        scored.sort(key=lambda pair: (-pair[0], pair[1].tool_id))
        return [tool for _, tool in scored[:limit]]


class PersistentTaskStore:
    """تخزين المهام الدائم."""

    def create(self, task_id: str, task_type: str, description: str, tenant_id: str = "default") -> dict[str, Any]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            task = TaskModel(
                id=task_id,
                type=task_type,
                description=description,
                status="created",
                tenant_id=tenant_id,
            )
            session.merge(task)
            session.commit()
            return {"id": task_id, "type": task_type, "description": description, "status": "created"}
        finally:
            session.close()

    def get(self, task_id: str) -> dict[str, Any] | None:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            row = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if row is None:
                return None
            return {
                "id": row.id,
                "type": row.type,
                "description": row.description,
                "status": row.status,
                "assigned_agent": row.assigned_agent,
                "plan": row.plan or [],
                "result": row.result or {},
            }
        finally:
            session.close()

    def list_all(self, limit: int = 50) -> list[dict[str, Any]]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            rows = session.query(TaskModel).limit(limit).all()
            return [
                {"id": r.id, "type": r.type, "description": r.description, "status": r.status}
                for r in rows
            ]
        finally:
            session.close()

    def update_status(self, task_id: str, status: str) -> None:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            row = session.query(TaskModel).filter(TaskModel.id == task_id).first()
            if row:
                row.status = status
                session.commit()
        finally:
            session.close()


class PersistentMemoryStore:
    """تخزين الذاكرة الدائم بـ SQLAlchemy."""

    def store(self, key: str, value: str | dict, keywords: list[str] | None = None, tenant_id: str | None = None) -> dict[str, Any]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            if tenant_id is None:
                tenant_id = "default"
            # تسلسل dict إلى JSON string
            if isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False)
            mem = MemoryModel(
                key=key,
                value=value,
                keywords=keywords or [],
                tenant_id=tenant_id,
            )
            session.merge(mem)
            session.commit()
            return {"key": key, "value": value, "keywords": keywords or [], "stored": True}
        finally:
            session.close()

    def get(self, key: str) -> dict[str, Any] | None:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            row = session.query(MemoryModel).filter(MemoryModel.key == key).first()
            if row is None:
                return None
            return {"key": row.key, "value": row.value, "keywords": row.keywords or []}
        finally:
            session.close()

    def query(self, query_text: str, limit: int = 5, tenant_id: str | None = None) -> list[dict[str, Any]]:
        """بحث بكلمات مفتاحية مع تشابه Jaccard."""
        if tenant_id is None:
            tenant_id = "default"
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            rows = session.query(MemoryModel).filter(MemoryModel.tenant_id == tenant_id).all()
            query_words = set(query_text.lower().split())
            scored: list[tuple[float, dict[str, Any]]] = []
            for row in rows:
                # تحليل القيمة: قد تكون JSON string أو نص عادي
                value_text = row.value
                try:
                    parsed = json.loads(value_text)
                    if isinstance(parsed, dict):
                        value_text = " ".join(str(v) for v in parsed.values())
                except (json.JSONDecodeError, TypeError):
                    pass
                mem_words = set((row.keywords or []) + value_text.lower().split())
                if not query_words or not mem_words:
                    continue
                intersection = len(query_words & mem_words)
                union = len(query_words | mem_words)
                similarity = intersection / union if union > 0 else 0.0
                if similarity > 0:
                    scored.append((similarity, {"key": row.key, "value": row.value, "keywords": row.keywords or []}))
            scored.sort(key=lambda x: -x[0])
            return [item for _, item in scored[:limit]]
        finally:
            session.close()

    def stats(self) -> dict[str, Any]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            count = session.query(MemoryModel).count()
            return {"total_entries": count}
        finally:
            session.close()


class PersistentExperienceStore:
    """تخزين الخبرات الدائم."""

    def record(self, data: dict[str, Any]) -> dict[str, Any]:
        exp_id = data.get("experience_id") or f"exp-{uuid.uuid4()}"
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            provenance = data.get("provenance", {})
            if not provenance:
                provenance = {"source": "api", "recorded_at": datetime.now(UTC).isoformat()}
            elif "recorded_at" not in provenance:
                provenance["recorded_at"] = datetime.now(UTC).isoformat()
            exp = ExperienceModel(
                id=exp_id,
                type=data.get("type", "success"),
                task_id=data.get("task_id"),
                agent_id=data.get("agent_id"),
                model_used=data.get("model_used"),
                outcome=data.get("outcome", {}),
                quality_score=data.get("quality_score"),
                provenance=provenance,
                tenant_id="default",
            )
            session.merge(exp)
            session.commit()
            return {**data, "experience_id": exp_id, "provenance": provenance}
        finally:
            session.close()

    def get(self, exp_id: str) -> dict[str, Any] | None:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            row = session.query(ExperienceModel).filter(ExperienceModel.id == exp_id).first()
            if row is None:
                return None
            return {
                "experience_id": row.id,
                "type": row.type,
                "task_id": row.task_id,
                "agent_id": row.agent_id,
                "model_used": row.model_used,
                "outcome": row.outcome or {},
                "quality_score": row.quality_score,
                "provenance": row.provenance or {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        finally:
            session.close()

    def list_all(self, exp_type: str | None = None, agent_id: str | None = None,
                 min_score: float | None = None, limit: int = 50) -> list[dict[str, Any]]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            q = session.query(ExperienceModel)
            if exp_type:
                q = q.filter(ExperienceModel.type == exp_type)
            if agent_id:
                q = q.filter(ExperienceModel.agent_id == agent_id)
            if min_score is not None:
                q = q.filter(ExperienceModel.quality_score >= min_score)
            rows = q.limit(limit).all()
            return [
                {
                    "experience_id": r.id,
                    "type": r.type,
                    "task_id": r.task_id,
                    "agent_id": r.agent_id,
                    "quality_score": r.quality_score,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        finally:
            session.close()

    def count(self) -> int:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            return session.query(ExperienceModel).count()
        finally:
            session.close()

    def by_type(self) -> dict[str, int]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            rows = session.query(ExperienceModel).all()
            counts: dict[str, int] = {}
            for r in rows:
                counts[r.type] = counts.get(r.type, 0) + 1
            return counts
        finally:
            session.close()


class PersistentCriticStore:
    """تخزين مراجعات الناقد الدائم."""

    def review(self, data: dict[str, Any]) -> dict[str, Any]:
        rev_id = data.get("review_id") or f"rev-{uuid.uuid4()}"
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            rev = ReviewModel(
                id=rev_id,
                task_id=data.get("task_id"),
                agent_id=data.get("agent_id"),
                quality_score=data.get("quality_score", 0.0),
                feedback=data.get("feedback", ""),
                approved=data.get("approved", False),
                criteria=data.get("criteria", {}),
            )
            session.merge(rev)
            session.commit()
            return {
                "review_id": rev_id,
                "task_id": data.get("task_id"),
                "agent_id": data.get("agent_id"),
                "quality_score": data.get("quality_score"),
                "feedback": data.get("feedback", ""),
                "approved": data.get("approved", False),
                "criteria": data.get("criteria", {}),
                "created_at": datetime.now(UTC).isoformat(),
            }
        finally:
            session.close()

    def get(self, rev_id: str) -> dict[str, Any] | None:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            row = session.query(ReviewModel).filter(ReviewModel.id == rev_id).first()
            if row is None:
                return None
            return {
                "review_id": row.id,
                "task_id": row.task_id,
                "agent_id": row.agent_id,
                "quality_score": row.quality_score,
                "feedback": row.feedback,
                "approved": row.approved,
                "criteria": row.criteria or {},
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        finally:
            session.close()

    def list_all(self, task_id: str | None = None, min_score: float | None = None,
                 limit: int = 50) -> list[dict[str, Any]]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            q = session.query(ReviewModel)
            if task_id:
                q = q.filter(ReviewModel.task_id == task_id)
            if min_score is not None:
                q = q.filter(ReviewModel.quality_score >= min_score)
            rows = q.limit(limit).all()
            return [
                {
                    "review_id": r.id,
                    "task_id": r.task_id,
                    "agent_id": r.agent_id,
                    "quality_score": r.quality_score,
                    "feedback": r.feedback,
                    "approved": r.approved,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        finally:
            session.close()

    def count(self) -> int:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            return session.query(ReviewModel).count()
        finally:
            session.close()

    def average_score(self) -> float:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            rows = session.query(ReviewModel).all()
            scores = [r.quality_score for r in rows if r.quality_score is not None]
            if not scores:
                return 0.0
            return sum(scores) / len(scores)
        finally:
            session.close()


class PersistentAuditStore:
    """تخزين سجل التدقيق الدائم بـ hash chain."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def append(self, action: str, actor: str, details: dict[str, Any]) -> dict[str, Any]:
        import hashlib
        rev_id = f"audit-{uuid.uuid4()}"
        prev_hash = "0" * 64
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            last = session.query(AuditEntryModel).order_by(AuditEntryModel.created_at.desc()).first()
            if last:
                prev_hash = last.hash
            entry_data = f"{prev_hash}:{action}:{actor}:{details}"
            current_hash = hashlib.sha256(entry_data.encode()).hexdigest()
            entry = AuditEntryModel(
                id=rev_id,
                action=action,
                actor=actor,
                details=details,
                prev_hash=prev_hash,
                hash=current_hash,
            )
            session.add(entry)
            session.commit()
            return {
                "audit_id": rev_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "action": action,
                "actor": actor,
                "details": details,
                "prev_hash": prev_hash,
                "hash": current_hash,
            }
        finally:
            session.close()

    def list_all(self, limit: int = 50) -> list[dict[str, Any]]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            rows = session.query(AuditEntryModel).order_by(AuditEntryModel.created_at.desc()).limit(limit).all()
            return [
                {
                    "audit_id": r.id,
                    "timestamp": r.created_at.isoformat() if r.created_at else None,
                    "action": r.action,
                    "actor": r.actor,
                    "details": r.details or {},
                    "prev_hash": r.prev_hash,
                    "hash": r.hash,
                }
                for r in rows
            ]
        finally:
            session.close()

    def verify_chain(self) -> dict[str, Any]:
        SessionLocal = get_session_factory()
        session = SessionLocal()
        try:
            rows = session.query(AuditEntryModel).order_by(AuditEntryModel.created_at).all()
            if not rows:
                return {"valid": True, "entries": 0, "message": "السجل فارغ"}
            prev_hash = "0" * 64
            for entry in rows:
                if entry.prev_hash != prev_hash:
                    return {"valid": False, "entries": len(rows), "message": "السلسلة مكسورة"}
                prev_hash = entry.hash
            return {"valid": True, "entries": len(rows), "message": "السلسلة سليمة"}
        finally:
            session.close()
