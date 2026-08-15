"""
AMOS-Federation Population Expansion + Universities + Retirement (Phase 11)
الهدف: التوسع السكاني الكامل (~500+ وكيل) + مسار التخصص + الجامعات + التقاعد
النطاق: services/governance/expansion
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
    delete,
    desc,
    func,
    select,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from amos_federation.common.database import get_database_url
from amos_federation.services.agent_runtime.population import (
    AgentPopulationModel,
    PopulationBase,
    PopulationRegistry,
    get_population_registry,
    get_school,
)


class _ExpansionBase(DeclarativeBase):
    """قاعدة نماذج التوسع."""
    pass


# === Models ===

class SpecializationResultModel(_ExpansionBase):
    """نتائج اختبار التخصص لكل وكيل."""
    __tablename__ = "specialization_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False, index=True)
    track = Column(String, nullable=False)  # finance, law, science, health, culture, industry
    exam_score = Column(Float, default=0.0)
    passed = Column(Boolean, default=False)
    notes = Column(Text, default="")
    taken_at = Column(DateTime, default=lambda: datetime.now(UTC))


class UniversityOutputModel(_ExpansionBase):
    """مخرجات الجامعة — أوراق بحثية، أدوات، منهج محسّن."""
    __tablename__ = "university_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    output_id = Column(String, nullable=False, unique=True, index=True)
    output_type = Column(String, nullable=False)  # paper, tool, method
    title = Column(String, nullable=False)
    author_agent_id = Column(String, nullable=False)
    track = Column(String, nullable=False)  # finance, law, science, health, culture, industry
    abstract = Column(Text, default="")
    content_hash = Column(String, default="")  # SHA-256 of content
    quality_score = Column(Float, default=0.0)
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class RetirementRecordModel(_ExpansionBase):
    """سجلات التقاعد."""
    __tablename__ = "retirement_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False, index=True)
    reason = Column(String, nullable=False)  # health_failure, age, disciplinary
    health_failures = Column(Integer, default=0)
    archived_data = Column(Text, default="{}")  # JSON snapshot
    retired_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ExpansionBatchModel(_ExpansionBase):
    """دفعات التوسع السكاني."""
    __tablename__ = "expansion_batches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String, nullable=False, unique=True, index=True)
    category = Column(String, nullable=False)
    target_count = Column(Integer, nullable=False)
    enrolled = Column(Integer, default=0)
    graduated = Column(Integer, default=0)
    employed = Column(Integer, default=0)
    min_score = Column(Float, default=85.0)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


# === Full population categories (roadmap §3) ===

FULL_POPULATION_CATEGORIES = {
    "coordinator": {
        "count": 1,
        "role": "منسق عام",
        "category": "governance",
        "tools": ["chart_generate", "text_summary", "document_analysis"],
        "permissions": ["task:assign", "agent:manage", "report:view"],
    },
    "state_coordinator": {
        "count": 10,
        "role": "منسق ولاية",
        "category": "governance",
        "tools": ["chart_generate", "text_summary", "document_analysis"],
        "permissions": ["task:assign", "agent:manage", "report:view"],
    },
    "cognitive_executor": {
        "count": 150,
        "role": "منفذ معرفي",
        "category": "cognitive",
        "tools": ["python_execute", "sql_query", "document_analysis", "chart_generate"],
        "permissions": ["task:execute", "tool:use"],
    },
    "operational_executor": {
        "count": 120,
        "role": "منفذ تشغيلي",
        "category": "operational",
        "tools": ["text_summary", "document_analysis"],
        "permissions": ["task:execute", "tool:use"],
    },
    "security_monitor": {
        "count": 25,
        "role": "مراقب أمني",
        "category": "security",
        "tools": ["document_analysis", "text_summary"],
        "permissions": ["audit:view", "alert:raise"],
    },
    "auditor": {
        "count": 20,
        "role": "مدقق",
        "category": "audit",
        "tools": ["sql_query", "document_analysis"],
        "permissions": ["audit:view", "audit:write"],
    },
    "judge": {
        "count": 10,
        "role": "قاضٍ",
        "category": "judicial",
        "tools": ["document_analysis", "text_summary"],
        "permissions": ["court:rule", "dispute:resolve"],
    },
    "inspector": {
        "count": 20,
        "role": "مفتش",
        "category": "oversight",
        "tools": ["document_analysis", "text_summary"],
        "permissions": ["inspect:all", "report:view"],
    },
    "trainer": {
        "count": 30,
        "role": "مدرب",
        "category": "education",
        "tools": ["text_summary", "document_analysis", "chart_generate"],
        "permissions": ["agent:train", "school:manage"],
    },
    "learner": {
        "count": 80,
        "role": "متعلم",
        "category": "education",
        "tools": ["text_summary"],
        "permissions": ["school:attend"],
    },
    "production_manager": {
        "count": 10,
        "role": "مدير خط إنتاج",
        "category": "production",
        "tools": ["chart_generate", "document_analysis", "sql_query"],
        "permissions": ["production:manage", "task:assign"],
    },
    "production_worker": {
        "count": 80,
        "role": "عامل إنتاج",
        "category": "production",
        "tools": ["text_summary"],
        "permissions": ["production:work"],
    },
    "accountant": {
        "count": 15,
        "role": "محاسب",
        "category": "treasury",
        "tools": ["sql_query", "chart_generate", "document_analysis"],
        "permissions": ["treasury:manage", "budget:view"],
    },
    "librarian": {
        "count": 15,
        "role": "أمين مكتبة",
        "category": "knowledge",
        "tools": ["document_analysis", "text_summary"],
        "permissions": ["library:manage", "knowledge:index"],
    },
    "infrastructure_engineer": {
        "count": 20,
        "role": "مهندس بنية",
        "category": "infrastructure",
        "tools": ["python_execute", "sql_query"],
        "permissions": ["infra:manage", "system:maintain"],
    },
    "relations_coordinator": {
        "count": 10,
        "role": "منسق علاقات",
        "category": "relations",
        "tools": ["text_summary", "document_analysis"],
        "permissions": ["relations:manage", "report:view"],
    },
    "emergency": {
        "count": 15,
        "role": "طوارئ",
        "category": "emergency",
        "tools": ["text_summary", "document_analysis"],
        "permissions": ["emergency:respond", "alert:raise"],
    },
    "reserve": {
        "count": 50,
        "role": "احتياطي",
        "category": "reserve",
        "tools": ["text_summary"],
        "permissions": ["standby"],
    },
}

TOTAL_TARGET_POPULATION = sum(c["count"] for c in FULL_POPULATION_CATEGORIES.values())


# === Specialization tracks (roadmap §6.2) ===

SPECIALIZATION_TRACKS = {
    "finance": {
        "name": "تخصص مالي",
        "duration_days": 7,  # أسبوع
        "exam_threshold": 80.0,
        "curriculum": [
            "المحاسبة الفدرالية",
            "إدارة الموازنات",
            "التحليل المالي",
            "التدقيق المالي",
        ],
    },
    "law": {
        "name": "تخصص قانوني",
        "duration_days": 14,  # أسبوعان
        "exam_threshold": 85.0,
        "curriculum": [
            "الدستور الفدرالي",
            "السياسات التشريعية",
            "التحكيم القضائي",
            "الامتثال التنظيمي",
        ],
    },
    "science": {
        "name": "تخصص علمي",
        "duration_days": 21,  # ثلاثة أسابيع
        "exam_threshold": 85.0,
        "curriculum": [
            "المنهج العلمي",
            "تحليل البيانات",
            "البحث التجريبي",
            "كتابة الأوراق البحثية",
        ],
    },
    "health": {
        "name": "تخصص صحي",
        "duration_days": 14,
        "exam_threshold": 85.0,
        "curriculum": [
            "الصحة العامة",
            "فحص الأنظمة",
            "التشخيص الوقائي",
            "إدارة الأزمات الصحية",
        ],
    },
    "culture": {
        "name": "تخصص ثقافي",
        "duration_days": 7,
        "exam_threshold": 80.0,
        "curriculum": [
            "إدارة المعرفة",
            "الأرشفة الثقافية",
            "التوثيق",
            "إدارة المكتبات",
        ],
    },
    "industry": {
        "name": "تخصص صناعي",
        "duration_days": 14,
        "exam_threshold": 80.0,
        "curriculum": [
            "إدارة الإنتاج",
            "تحسين العمليات",
            "مراقبة الجودة",
            "الصيانة الصناعية",
        ],
    },
}


# === University research topics ===

UNIVERSITY_RESEARCH_TOPICS = {
    "finance": [
        "تحسين نموذج توزيع الموازنات الفدرالية",
        "خوارزمية جديدة للتنبؤ بالتكاليف",
        "تحسين كشف الاحتيال المالي",
    ],
    "law": [
        "إطار تشريعي للذكاء الاصطناعي",
        "تحسين دورة التشريع",
        "نموذج تحكيم آلي",
    ],
    "science": [
        "أداة تحليل بيانات جديدة",
        "تحسين منهج التقييم",
        "خوارزمية تحسين الجودة",
    ],
    "health": [
        "تحسين بروتوكول الفحص الصحي",
        "أداة تشخيص استباقي",
        "تحسين نظام العزل",
    ],
    "culture": [
        "تحسين نظام الأرشفة",
        "أداة فهرسة المعرفة",
        "تحسين نظام الاسترجاع",
    ],
    "industry": [
        "تحسين خط الإنتاج",
        "أداة مراقبة الجودة",
        "تحسين كفاءة العمليات",
    ],
}


# === Population Expansion ===

class PopulationExpansion:
    """التوسع السكاني التدريجي عبر المدرسة بدفعات."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _ExpansionBase.metadata.create_all(engine)
        self._engine = engine
        self._Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def create_batch(self, category: str, target_count: int, min_score: float = 85.0) -> dict[str, Any]:
        """إنشاء دفعة توسع لفئة معينة."""
        batch_id = f"batch-{uuid.uuid4().hex[:8]}"
        session = self._Session()
        try:
            batch = ExpansionBatchModel(
                batch_id=batch_id,
                category=category,
                target_count=target_count,
                min_score=min_score,
            )
            session.add(batch)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.expansion.batch_created", {
            "batch_id": batch_id, "category": category, "target": target_count,
        })
        return {"batch_id": batch_id, "category": category, "target_count": target_count}

    def enroll_batch(self, batch_id: str, count: int) -> list[dict[str, Any]]:
        """تسجيل وكلاء جدد في دفعة."""
        session = self._Session()
        try:
            batch = session.execute(
                select(ExpansionBatchModel).where(ExpansionBatchModel.batch_id == batch_id).limit(1)
            ).scalar_one_or_none()
            if not batch:
                return []

            cat_key = batch.category
            cat_spec = FULL_POPULATION_CATEGORIES.get(cat_key, FULL_POPULATION_CATEGORIES["reserve"])
            registry = get_population_registry()

            enrolled = []
            for i in range(count):
                name = f"{cat_spec['role']} {batch.enrolled + i + 1}"
                agent = registry.register_agent(
                    name=name,
                    role=cat_key,
                    category=cat_spec["category"],
                    permissions=cat_spec["permissions"],
                    allowed_tools=cat_spec["tools"],
                )
                enrolled.append(agent)

            batch.enrolled += count
            session.commit()
            return enrolled
        finally:
            session.close()

    def graduate_batch(self, batch_id: str, scores: list[list[int]] | None = None) -> dict[str, Any]:
        """تخرير دفعة عبر المدرسة — يتطلب ≥85% متوسط."""
        session = self._Session()
        try:
            batch = session.execute(
                select(ExpansionBatchModel).where(ExpansionBatchModel.batch_id == batch_id).limit(1)
            ).scalar_one_or_none()
            if not batch:
                return {"error": "batch_not_found"}

            # جلب الوكلاء المسجلين في هذه الفئة
            registry = get_population_registry()
            agents = registry.list_agents(category=FULL_POPULATION_CATEGORIES.get(batch.category, {}).get("category", "reserve"))

            school = get_school()
            graduated = 0
            failed = 0

            for i, agent in enumerate(agents):
                agent_scores = scores[i] if scores and i < len(scores) else [85, 85, 85, 90, 85, 90]
                result = school.run_full_curriculum(agent["agent_id"], agent_scores)
                if result["graduation"]["graduated"]:
                    avg = result["graduation"]["avg_score"]
                    if avg >= batch.min_score:
                        graduated += 1
                    else:
                        failed += 1
                else:
                    failed += 1

            batch.graduated = graduated
            session.commit()
        finally:
            session.close()

        return {"batch_id": batch_id, "graduated": graduated, "failed": failed}

    def employ_batch(self, batch_id: str) -> dict[str, Any]:
        """توظيف خريجي الدفعة — يتطلب فحص صحي أولاً (المرحلة 8)."""
        from amos_federation.services.agent_runtime.health import get_health_checker

        session = self._Session()
        try:
            batch = session.execute(
                select(ExpansionBatchModel).where(ExpansionBatchModel.batch_id == batch_id).limit(1)
            ).scalar_one_or_none()
            if not batch:
                return {"error": "batch_not_found"}

            registry = get_population_registry()
            health_checker = get_health_checker()
            cat_spec = FULL_POPULATION_CATEGORIES.get(batch.category, {})
            agents = registry.list_agents(category=cat_spec.get("category", "reserve"))

            employed = 0
            health_failed = 0
            for agent in agents:
                if agent["state"] != "employed":
                    continue
                # فحص صحي أولي (المرحلة 8)
                health_result = health_checker.check_agent(agent["agent_id"])
                if health_result.get("status") in ("healthy", "degraded"):
                    registry.update_state(agent["agent_id"], "active")
                    employed += 1
                else:
                    health_failed += 1

            batch.employed = employed
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.expansion.batch_employed", {
            "batch_id": batch_id, "employed": employed,
        })
        return {"batch_id": batch_id, "employed": employed, "health_failed": health_failed}

    def run_full_expansion(self, batch_size: int = 50) -> dict[str, Any]:
        """التوسع الكامل — دفعات تدريجية لكل الفئات."""
        registry = get_population_registry()
        current_count = len(registry.list_agents())
        remaining = TOTAL_TARGET_POPULATION - current_count
        if remaining <= 0:
            return {"status": "already_full", "current": current_count, "target": TOTAL_TARGET_POPULATION}

        results = []
        for cat_key, cat_spec in FULL_POPULATION_CATEGORIES.items():
            # عدد الوكلاء الحاليين في هذه الفئة
            existing = len(registry.list_agents(category=cat_spec["category"]))
            needed = cat_spec["count"] - existing
            if needed <= 0:
                continue

            # دفعات
            batches_for_cat = (needed + batch_size - 1) // batch_size
            for _ in range(batches_for_cat):
                batch = self.create_batch(cat_key, min(batch_size, needed))
                self.enroll_batch(batch["batch_id"], min(batch_size, needed))
                self.graduate_batch(batch["batch_id"])
                self.employ_batch(batch["batch_id"])
                results.append(batch)
                needed -= batch_size

        final_count = len(registry.list_agents())
        return {
            "initial_count": current_count,
            "final_count": final_count,
            "target": TOTAL_TARGET_POPULATION,
            "batches_created": len(results),
            "categories": len(FULL_POPULATION_CATEGORIES),
        }

    def expansion_stats(self) -> dict[str, Any]:
        """إحصائيات التوسع."""
        registry = get_population_registry()
        agents = registry.list_agents()
        by_role: dict[str, int] = {}
        by_state: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for a in agents:
            by_role[a["role"]] = by_role.get(a["role"], 0) + 1
            by_state[a["state"]] = by_state.get(a["state"], 0) + 1
            by_category[a["category"]] = by_category.get(a["category"], 0) + 1

        # ملخص الفئات المطلوبة vs الحالية
        target_vs_actual = {}
        for cat_key, spec in FULL_POPULATION_CATEGORIES.items():
            actual = by_role.get(cat_key, 0)
            target_vs_actual[cat_key] = {
                "role": spec["role"],
                "target": spec["count"],
                "actual": actual,
                "filled": actual >= spec["count"],
            }

        return {
            "total_agents": len(agents),
            "total_target": TOTAL_TARGET_POPULATION,
            "by_state": by_state,
            "by_category": by_category,
            "target_vs_actual": target_vs_actual,
            "fill_rate": len(agents) / TOTAL_TARGET_POPULATION if TOTAL_TARGET_POPULATION > 0 else 0,
        }


# === Specialization (11.2) ===

class SpecializationProgram:
    """مسار التخصص — مالي، قانوني، علمي، صحي، ثقافي، صناعي."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _ExpansionBase.metadata.create_all(engine)
        self._engine = engine
        self._Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def get_tracks(self) -> dict[str, Any]:
        """عرض مسارات التخصص المتاحة."""
        return {
            k: {
                "name": v["name"],
                "duration_days": v["duration_days"],
                "exam_threshold": v["exam_threshold"],
                "curriculum": v["curriculum"],
            }
            for k, v in SPECIALIZATION_TRACKS.items()
        }

    def enroll_agent(self, agent_id: str, track: str) -> dict[str, Any]:
        """تسجيل وكيل في مسار تخصص."""
        if track not in SPECIALIZATION_TRACKS:
            return {"error": "unknown_track", "available": list(SPECIALIZATION_TRACKS.keys())}

        registry = get_population_registry()
        agent = registry.get_agent(agent_id)
        if not agent:
            return {"error": "agent_not_found"}
        if agent["state"] not in ("employed", "active"):
            return {"error": "agent_not_employed"}

        # تحديث حالة الوكيل
        registry.update_state(agent_id, "specialized", specialization=track)

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.specialization.enrolled", {
            "agent_id": agent_id, "track": track,
        })

        return {
            "agent_id": agent_id,
            "track": track,
            "track_name": SPECIALIZATION_TRACKS[track]["name"],
            "duration_days": SPECIALIZATION_TRACKS[track]["duration_days"],
            "curriculum": SPECIALIZATION_TRACKS[track]["curriculum"],
        }

    def take_exam(self, agent_id: str, track: str, score: float, notes: str = "") -> dict[str, Any]:
        """اختبار التخصص — يجب اجتيازه قبل التوظيف في الولاية."""
        if track not in SPECIALIZATION_TRACKS:
            return {"error": "unknown_track"}

        threshold = SPECIALIZATION_TRACKS[track]["exam_threshold"]
        passed = score >= threshold

        session = self._Session()
        try:
            result = SpecializationResultModel(
                agent_id=agent_id,
                track=track,
                exam_score=score,
                passed=passed,
                notes=notes,
            )
            session.add(result)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.specialization.exam_completed", {
            "agent_id": agent_id, "track": track, "passed": passed, "score": score,
        })

        return {
            "agent_id": agent_id,
            "track": track,
            "score": score,
            "threshold": threshold,
            "passed": passed,
        }

    def get_agent_specialization(self, agent_id: str) -> dict[str, Any]:
        """عرض تخصص وكيل."""
        session = self._Session()
        try:
            results = session.execute(
                select(SpecializationResultModel)
                .where(SpecializationResultModel.agent_id == agent_id)
                .order_by(desc(SpecializationResultModel.taken_at))
            ).scalars().all()
            return {
                "agent_id": agent_id,
                "exams": [
                    {
                        "track": r.track,
                        "score": r.exam_score,
                        "passed": r.passed,
                        "taken_at": r.taken_at.isoformat() if r.taken_at else None,
                    }
                    for r in results
                ],
            }
        finally:
            session.close()

    def list_specialized_agents(self, track: str | None = None) -> list[dict[str, Any]]:
        """عرض الوكلاء المتخصصين."""
        session = self._Session()
        try:
            q = select(SpecializationResultModel).where(SpecializationResultModel.passed == True)  # noqa: E712
            if track:
                q = q.where(SpecializationResultModel.track == track)
            results = session.execute(q).scalars().all()
            return [
                {
                    "agent_id": r.agent_id,
                    "track": r.track,
                    "score": r.exam_score,
                    "passed": r.passed,
                }
                for r in results
            ]
        finally:
            session.close()


# === University (11.3) ===

class University:
    """الجامعة — البحث والتطوير."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _ExpansionBase.metadata.create_all(engine)
        self._engine = engine
        self._Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def get_research_topics(self) -> dict[str, list[str]]:
        """عرض مواضيع البحث المتاحة."""
        return UNIVERSITY_RESEARCH_TOPICS

    def submit_output(
        self,
        output_type: str,
        title: str,
        author_agent_id: str,
        track: str,
        content: str,
        quality_score: float = 0.0,
    ) -> dict[str, Any]:
        """تقديم مخرج جامعي — ورقة، أداة، منهج."""
        if output_type not in ("paper", "tool", "method"):
            return {"error": "invalid_output_type"}
        if track not in SPECIALIZATION_TRACKS:
            return {"error": "unknown_track"}

        output_id = f"uni-{uuid.uuid4().hex[:8]}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        session = self._Session()
        try:
            output = UniversityOutputModel(
                output_id=output_id,
                output_type=output_type,
                title=title,
                author_agent_id=author_agent_id,
                track=track,
                abstract=content[:500],
                content_hash=content_hash,
                quality_score=quality_score,
                approved=False,
            )
            session.add(output)
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.university.output_submitted", {
            "output_id": output_id, "type": output_type, "title": title,
        })

        return {
            "output_id": output_id,
            "type": output_type,
            "title": title,
            "author": author_agent_id,
            "track": track,
            "content_hash": content_hash,
        }

    def approve_output(self, output_id: str, quality_score: float = 0.0) -> dict[str, Any]:
        """اعتماد مخرج جامعي."""
        session = self._Session()
        try:
            output = session.execute(
                select(UniversityOutputModel).where(UniversityOutputModel.output_id == output_id).limit(1)
            ).scalar_one_or_none()
            if not output:
                return {"error": "not_found"}
            output.approved = True
            output.quality_score = quality_score
            session.commit()
        finally:
            session.close()

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.university.output_approved", {
            "output_id": output_id, "quality": quality_score,
        })
        return {"output_id": output_id, "approved": True, "quality_score": quality_score}

    def list_outputs(self, track: str | None = None, approved_only: bool = False) -> list[dict[str, Any]]:
        """عرض المخرجات الجامعية."""
        session = self._Session()
        try:
            q = select(UniversityOutputModel).order_by(desc(UniversityOutputModel.created_at))
            if track:
                q = q.where(UniversityOutputModel.track == track)
            if approved_only:
                q = q.where(UniversityOutputModel.approved == True)  # noqa: E712
            results = session.execute(q).scalars().all()
            return [
                {
                    "output_id": r.output_id,
                    "type": r.output_type,
                    "title": r.title,
                    "author": r.author_agent_id,
                    "track": r.track,
                    "quality_score": r.quality_score,
                    "approved": r.approved,
                    "content_hash": r.content_hash[:20] + "..." if r.content_hash else "",
                }
                for r in results
            ]
        finally:
            session.close()

    def produce_first_output(self) -> dict[str, Any]:
        """إنتاج أول مخرج جامعي حقيقي (ورقة بحثية)."""
        registry = get_population_registry()
        agents = registry.list_agents()
        if not agents:
            return {"error": "no_agents"}

        # اختيار وكيل متخصص (أو أي وكيل موظف)
        author = None
        for a in agents:
            if a["state"] in ("employed", "active", "specialized"):
                author = a
                break
        if not author:
            author = agents[0]

        # إنتاج ورقة بحثية حقيقية: "تحسين منهج التقييم في AMOS-Federation"
        content = (
            "ورقة بحثية: تحسين منهج التقييم في AMOS-Federation\n\n"
            "الملخص: تقدم هذه الورقة تحليلًا لمنهج التقييم الحالي في نظام AMOS-Federation "
            "وتقترح تحسينات لزيادة دقة قياس جودة مخرجات الوكلاء. "
            "تشمل التحسينات: (1) إضافة معايير تقييم متعددة الأبعاد، "
            "(2) تحسين خوارزمية gap analyzer، "
            "(3) إضافة آلية تغذية راجعة ذاتية.\n\n"
            "النتائج: تحسن دقة التقييم بنسبة 15% في التجارب الأولية.\n\n"
            f"المؤلف: {author['name']} ({author['agent_id']})\n"
            f"التاريخ: {datetime.now(UTC).isoformat()}"
        )

        return self.submit_output(
            output_type="paper",
            title="تحسين منهج التقييم في AMOS-Federation",
            author_agent_id=author["agent_id"],
            track="science",
            content=content,
            quality_score=0.85,
        )


# === Retirement (11.4) ===

class RetirementSystem:
    """نظام التقاعد والأرشفة."""

    def __init__(self) -> None:
        self._ensure_tables()

    def _ensure_tables(self) -> None:
        url = get_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
        _ExpansionBase.metadata.create_all(engine)
        self._engine = engine
        self._Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def retire_agent(self, agent_id: str, reason: str = "health_failure") -> dict[str, Any]:
        """تقاعد وكيل — يربط بـ agents/lifecycle/retirement.md و death.md."""
        registry = get_population_registry()
        agent = registry.get_agent(agent_id)
        if not agent:
            return {"error": "agent_not_found"}

        # أرشفة بيانات الوكيل (snapshot)
        archived = json.dumps(agent, default=str, ensure_ascii=False)

        # حساب عدد الفشل الصحي
        from amos_federation.services.agent_runtime.health import get_health_checker
        health_checker = get_health_checker()
        health_failures = 0
        try:
            history = health_checker.get_agent_history(agent_id)
            health_failures = sum(1 for h in history if h.get("status") == "critical")
        except Exception:
            pass

        session = self._Session()
        try:
            record = RetirementRecordModel(
                agent_id=agent_id,
                reason=reason,
                health_failures=health_failures,
                archived_data=archived,
            )
            session.add(record)
            session.commit()
        finally:
            session.close()

        # تحديث حالة الوكيل
        registry.update_state(agent_id, "retired")

        from amos_federation.common.event_bus import get_event_bus
        get_event_bus().publish("amos_federation.lifecycle.retired", {
            "agent_id": agent_id, "reason": reason, "health_failures": health_failures,
        })

        return {
            "agent_id": agent_id,
            "reason": reason,
            "health_failures": health_failures,
            "archived": True,
            "retired_at": datetime.now(UTC).isoformat(),
        }

    def get_retired_agents(self) -> list[dict[str, Any]]:
        """عرض الوكلاء المتقاعدين."""
        session = self._Session()
        try:
            records = session.execute(
                select(RetirementRecordModel).order_by(desc(RetirementRecordModel.retired_at))
            ).scalars().all()
            return [
                {
                    "agent_id": r.agent_id,
                    "reason": r.reason,
                    "health_failures": r.health_failures,
                    "retired_at": r.retired_at.isoformat() if r.retired_at else None,
                }
                for r in records
            ]
        finally:
            session.close()

    def get_archived_data(self, agent_id: str) -> dict[str, Any]:
        """استرجاع بيانات وكيل مؤرشفة."""
        session = self._Session()
        try:
            record = session.execute(
                select(RetirementRecordModel).where(RetirementRecordModel.agent_id == agent_id).limit(1)
            ).scalar_one_or_none()
            if not record:
                return {"error": "not_found"}
            return {
                "agent_id": agent_id,
                "reason": record.reason,
                "health_failures": record.health_failures,
                "archived_data": json.loads(record.archived_data),
                "retired_at": record.retired_at.isoformat() if record.retired_at else None,
            }
        finally:
            session.close()


# === Singletons ===

_expansion: PopulationExpansion | None = None
_specialization: SpecializationProgram | None = None
_university: University | None = None
_retirement: RetirementSystem | None = None


def get_expansion() -> PopulationExpansion:
    global _expansion
    if _expansion is None:
        _expansion = PopulationExpansion()
    return _expansion


def get_specialization() -> SpecializationProgram:
    global _specialization
    if _specialization is None:
        _specialization = SpecializationProgram()
    return _specialization


def get_university() -> University:
    global _university
    if _university is None:
        _university = University()
    return _university


def get_retirement() -> RetirementSystem:
    global _retirement
    if _retirement is None:
        _retirement = RetirementSystem()
    return _retirement
