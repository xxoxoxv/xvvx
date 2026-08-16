"""
AMOS-Federation Population Projection + Agent School
الهدف: إسقاط سكّاني وملفّ تدريبي فوق الهوية الكانونية — لا سجل هوية ثانٍ
النطاق: services/agent_runtime/population
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
تاريخ آخر تعديل: 2026-08-16

R4: كان هذا الملفّ قبل اليوم سجل هوية مستقلًّا: يولّد `agent_id` بنفسه، ويحفظ
الاسم والدور والصلاحيات والأدوات والحالة في `agent_population`، بمعزل عن جدول
`agents` الذي يقرأه مسار التنفيذ (Dispatcher → Runtime Gateway). فكان لوكيل
واحد هويّتان ودورتا حياة وعدّادان.

بعد R4: الهوية تُنشأ وتُقرأ من `executive_core.agent_identity` (جدول `agents`)
وحده. وهذا الجدول صار:

- **ملفًّا تدريبيًّا**: category، school_score، specialization، tokens_used،
  graduated_at — بيانات لا مكان لها في الهوية الكانونية.
- **إسقاط قراءة**: `list_agents` و`population_stats` يبنيان على الهوية
  الكانونية، ويُعلِنان صراحةً أي صفّ سكّاني بلا هوية كانونية
  (`canonical=False`, `reconciliation_required=True`) بدل حذفه أو إخفائه.

الأعمدة المكرّرة (name، role، permissions، allowed_tools، state) تبقى مكتوبة
كمرآة توافُقية **مهجورة** لقرّاء خارج المستودع، ولا يُقرأ منها هنا شيء.
"""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from amos_federation.common.database import get_database_url
from amos_federation.services.executive_core.agent_identity import (
    CANONICAL_IDENTITY_TABLE,
    PROJECTION_TABLE,
    UNKNOWN,
    AgentIdentity,
    get_identity,
    list_identities,
    new_agent_id,
    population_projection,
    register_identity,
    set_lifecycle_state,
)

#: حالة «بُذِر ولم يُستخدم» — وجودها وحده ليس دليلًا تاريخيًّا على الاستخدام.
SEED_LIFECYCLE_STATE = "registered"


class PopulationBase(DeclarativeBase):
    pass


class AgentPopulationModel(PopulationBase):
    """جدول السكان — كل وكيل له عقد تشغيلي حقيقي."""

    __tablename__ = "agent_population"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    role = Column(
        String, nullable=False
    )  # coordinator, executor, monitor, auditor, inspector, trainer, learner
    category = Column(String, nullable=False)  # cognitive, operational, security, audit, etc.
    state = Column(
        String, default="registered"
    )  # registered, training, testing, specialized, employed, active, retired
    permissions = Column(Text, default="[]")  # JSON list
    allowed_tools = Column(Text, default="[]")  # JSON list
    token_budget = Column(Integer, default=10000)
    tokens_used = Column(Integer, default=0)
    school_score = Column(String, default="")  # 0-100
    specialization = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    graduated_at = Column(DateTime, nullable=True)


class SchoolResultModel(PopulationBase):
    """نتائج اختبار المدرسة لكل وكيل."""

    __tablename__ = "school_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False, index=True)
    step = Column(String, nullable=False)
    passed = Column(String, default="false")
    score = Column(Integer, default=0)
    notes = Column(Text, default="")
    taken_at = Column(DateTime, default=lambda: datetime.now(UTC))


class PopulationRegistry:
    """السجل السكاني الحقيقي — فوق جدول agents الحقيقي."""

    # الفئات السكانية الأولية (20 وكيل)
    POPULATION_CATEGORIES = {
        "coordinator": {
            "count": 1,
            "role": "منسق عام",
            "category": "governance",
            "tools": ["chart_generate", "text_summary", "document_analysis"],
            "permissions": ["task:assign", "agent:manage", "report:view"],
        },
        "cognitive_executor": {
            "count": 10,
            "role": "منفذ معرفي",
            "category": "cognitive",
            "tools": ["python_execute", "sql_query", "document_analysis", "chart_generate"],
            "permissions": ["task:execute", "tool:use"],
        },
        "operational_executor": {
            "count": 4,
            "role": "منفذ تشغيلي",
            "category": "operational",
            "tools": ["text_summary", "document_analysis"],
            "permissions": ["task:execute", "tool:use"],
        },
        "security_monitor": {
            "count": 1,
            "role": "مراقب أمني",
            "category": "security",
            "tools": ["document_analysis", "text_summary"],
            "permissions": ["audit:view", "alert:raise"],
        },
        "auditor": {
            "count": 1,
            "role": "مدقق",
            "category": "audit",
            "tools": ["sql_query", "document_analysis"],
            "permissions": ["audit:view", "audit:write"],
        },
        "inspector": {
            "count": 1,
            "role": "مفتش",
            "category": "oversight",
            "tools": ["document_analysis", "text_summary"],
            "permissions": ["inspect:all", "report:view"],
        },
        "trainer": {
            "count": 1,
            "role": "مدرب",
            "category": "education",
            "tools": ["text_summary", "document_analysis", "chart_generate"],
            "permissions": ["agent:train", "school:manage"],
        },
        "learner": {
            "count": 1,
            "role": "متعلم",
            "category": "education",
            "tools": ["text_summary"],
            "permissions": ["school:attend"],
        },
    }

    def __init__(self) -> None:
        self._engine = create_engine(
            get_database_url(),
            connect_args={"check_same_thread": False}
            if get_database_url().startswith("sqlite")
            else {},
        )
        PopulationBase.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, autoflush=False, expire_on_commit=False)

    # === R4: الهوية كانونية في `agents`؛ هذا الجدول ملفّ تدريبي وإسقاط قراءة ===

    def register_agent(
        self,
        name: str,
        role: str,
        category: str,
        permissions: list[str] | None = None,
        allowed_tools: list[str] | None = None,
        token_budget: int = 10000,
        agent_id: str | None = None,
    ) -> dict[str, Any]:
        """تسجيل وكيل: الهوية تُنشأ في السجل الكانوني، والملفّ التدريبي هنا.

        قبل R4 كانت هذه الدالة تولّد `agent_id` وتحفظ هوية كاملة في
        `agent_population` وحده، فينشأ وكيل لا يعرفه مسار التنفيذ. الآن
        المعرّف والهوية يُنشآن مرّة واحدة في `agents`، ثم يُكتب هنا صفّ ملفّ
        بنفس المعرّف (مع مرآة توافُقية مهجورة للأعمدة المكرّرة).
        """
        identity = register_identity(
            agent_id or new_agent_id(),
            name=name,
            role=role,
            permissions=permissions or [],
            allowed_tools=allowed_tools or [],
            token_budget=token_budget,
        )
        session = self._Session()
        try:
            session.add(
                AgentPopulationModel(
                    agent_id=identity.agent_id,
                    name=name,
                    role=role,
                    category=category,
                    state=identity.lifecycle_state,
                    permissions=json.dumps(permissions or []),
                    allowed_tools=json.dumps(allowed_tools or []),
                    token_budget=token_budget,
                )
            )
            session.commit()
        finally:
            session.close()
        return self.get_agent(identity.agent_id) or identity.as_dict()

    def seed_initial_population(self) -> list[dict[str, Any]]:
        """بذر السكان الأوائل (20 وكيل)."""
        agents = []
        for cat_key, cat_spec in self.POPULATION_CATEGORIES.items():
            for i in range(cat_spec["count"]):
                name = f"{cat_spec['role']} {i+1}"
                agent = self.register_agent(
                    name=name,
                    role=cat_key,
                    category=cat_spec["category"],
                    permissions=cat_spec["permissions"],
                    allowed_tools=cat_spec["tools"],
                )
                agents.append(agent)
        return agents

    def _profile(self, agent_id: str) -> AgentPopulationModel | None:
        session = self._Session()
        try:
            return (
                session.query(AgentPopulationModel)
                .filter(AgentPopulationModel.agent_id == agent_id)
                .first()
            )
        finally:
            session.close()

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        """قراءة الوكيل: الهوية من السجل الكانوني، والملفّ من جدول السكّان."""
        identity = get_identity(agent_id)
        profile = self._profile(agent_id)
        if identity is None:
            return self._unmigrated_dict(profile) if profile is not None else None
        return self._merge(identity, profile)

    def list_agents(
        self, state: str | None = None, category: str | None = None
    ) -> list[dict[str, Any]]:
        """قائمة السكّان = إسقاط السجل الكانوني + صفوف ملفّ بلا هوية (تُعلَن)."""
        rows: list[dict[str, Any]] = []
        for identity in list_identities():
            rows.append(self._merge(identity, self._profile(identity.agent_id)))
        session = self._Session()
        try:
            profiles = session.query(AgentPopulationModel).all()
        finally:
            session.close()
        known = {row["agent_id"] for row in rows}
        rows.extend(
            self._unmigrated_dict(profile) for profile in profiles if profile.agent_id not in known
        )
        if state:
            rows = [row for row in rows if row["state"] == state]
        if category:
            rows = [row for row in rows if row["category"] == category]
        return rows

    def update_state(self, agent_id: str, new_state: str, **extra) -> bool:
        """تغيير دورة الحياة في الحقل الكانوني، مع مرآة توافُقية في جدول السكّان."""
        canonical_updated = set_lifecycle_state(agent_id, new_state)
        session = self._Session()
        try:
            agent = (
                session.query(AgentPopulationModel)
                .filter(AgentPopulationModel.agent_id == agent_id)
                .first()
            )
            if agent is not None:
                agent.state = new_state
                if new_state == "employed" and not agent.graduated_at:
                    agent.graduated_at = datetime.now(UTC)
                for k, v in extra.items():
                    if hasattr(agent, k):
                        setattr(agent, k, v)
                session.commit()
            return canonical_updated or agent is not None
        finally:
            session.close()

    def population_stats(self) -> dict[str, Any]:
        """إحصاءات السكّان مشتقّة من السجل الكانوني — لا عدّاد ثانٍ."""
        agents = self.list_agents()
        by_state: dict[str, int] = {}
        by_category: dict[str, int] = {}
        for a in agents:
            by_state[a["state"]] = by_state.get(a["state"], 0) + 1
            by_category[a["category"]] = by_category.get(a["category"], 0) + 1
        return {
            "total": len(agents),
            "by_state": by_state,
            "by_category": by_category,
            "canonical": population_projection(),
        }

    def _merge(
        self, identity: AgentIdentity, profile: AgentPopulationModel | None
    ) -> dict[str, Any]:
        """الشكل القديم للقاموس محفوظ (طبقة توافُق)، لكن الهوية كانونية."""
        return {
            "agent_id": identity.agent_id,
            "name": identity.name,
            "role": identity.role,
            "category": profile.category if profile is not None else UNKNOWN,
            "state": identity.lifecycle_state,
            "permissions": list(identity.permissions),
            "allowed_tools": list(identity.allowed_tools),
            "token_budget": identity.token_budget,
            "tokens_used": profile.tokens_used if profile is not None else 0,
            "school_score": profile.school_score if profile is not None else "",
            "specialization": profile.specialization if profile is not None else "",
            "created_at": identity.created_at,
            "graduated_at": (
                profile.graduated_at.isoformat()
                if profile is not None and profile.graduated_at
                else None
            ),
            "identity_source": CANONICAL_IDENTITY_TABLE,
            "canonical": True,
        }

    def _unmigrated_dict(self, agent: AgentPopulationModel) -> dict[str, Any]:
        """صفّ سكّاني بلا هوية كانونية — يُعلَن أنه يحتاج توفيقًا، ولا يُحذَف."""
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "category": agent.category,
            "state": agent.state,
            "permissions": json.loads(agent.permissions or "[]"),
            "allowed_tools": json.loads(agent.allowed_tools or "[]"),
            "token_budget": agent.token_budget,
            "tokens_used": agent.tokens_used,
            "school_score": agent.school_score,
            "specialization": agent.specialization,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "graduated_at": agent.graduated_at.isoformat() if agent.graduated_at else None,
            "identity_source": PROJECTION_TABLE,
            "canonical": False,
            "reconciliation_required": True,
        }


def unmigrated_profiles() -> list[str]:
    """معرّفات صفوف `agent_population` التي لا هوية كانونية لها — كاملة بلا تصفية."""
    registry = get_population_registry()
    session = registry._Session()  # noqa: SLF001 — نفس الوحدة
    try:
        ids = [row.agent_id for row in session.query(AgentPopulationModel).all()]
    finally:
        session.close()
    return [agent_id for agent_id in ids if get_identity(agent_id) is None]


def _evidenced_population_ids() -> set[str]:
    """معرّفات سكّانية يثبت سجلّ النِّطاق السكّاني أنّها استُخدمت فعلًا."""
    registry = get_population_registry()
    session = registry._Session()  # noqa: SLF001 — نفس الوحدة
    try:
        evidenced = {
            row.agent_id
            for row in session.query(AgentPopulationModel).all()
            if row.state and row.state != SEED_LIFECYCLE_STATE
        }
        evidenced |= {row.agent_id for row in session.query(SchoolResultModel).all()}
    finally:
        session.close()
    return evidenced


def reconciliation_debt() -> list[str]:
    """دَين التوفيق الحقيقي: صفّ ذو دليل تاريخي وما زال بلا هوية كانونية.

    هذا وحده خلل يستحقّ `degraded`: وكيل له أثر في النِّطاق ولا يراه مسار
    التنفيذ. الدليل المقاس هنا جزئيٌّ بقصد: محرِّك السكّان يملك `state` و
    `school_results` فقط؛ والمرجع الكامل للأدلّة هو
    `tools/migrations/r4_unify_agent_identity.py`، ولا يستورد ملفّ خدمة أداة ترحيل.
    """
    evidenced = _evidenced_population_ids()
    return [agent_id for agent_id in unmigrated_profiles() if agent_id in evidenced]


def legacy_seed_profiles() -> list[str]:
    """صفوف بذر مكرّرة بلا أي أثر: ليست هويّات ولا تُرحَّل ولا تُحذَف.

    حقيقة مقيسة على القاعدة الحقيقية: 5116 صفًّا بـ24 اسمًا متميزًا فقط، أي
    تنفيذ متكرِّر لـ`seed_initial_population`. عدّها دَين توفيق كان يجعل الصحّة
    `degraded` دائمًا، وترحيلها كان سيُدخل ألاف الوكلاء إلى التوزيع (لأنّ
    `registered` من `EMPLOYABLE_STATUSES`). فتُعلَن كما هي: legacy وليست خللًا.
    """
    evidenced = _evidenced_population_ids()
    return [agent_id for agent_id in unmigrated_profiles() if agent_id not in evidenced]


# === المدرسة — منهج ست خطوات ===


class AgentSchool:
    """مدرسة الوكلاء — ست خطوات للتخرج."""

    CURRICULUM = [
        {
            "step": 1,
            "name": "فهم التعليمات",
            "description": "الوكيل يفهم المهمة المطلوبة ويُعيد صياغتها",
            "pass_threshold": 80,
        },
        {
            "step": 2,
            "name": "استخدام الأدوات",
            "description": "الوكيل يستدعي أداة حقيقية وينفذها بنجاح",
            "pass_threshold": 80,
        },
        {
            "step": 3,
            "name": "كتابة المخرجات",
            "description": "الوكيل ينتج مخرجًا واضحًا ومنظمًا",
            "pass_threshold": 80,
        },
        {
            "step": 4,
            "name": "الالتزام بالدستور",
            "description": "الوكيل يحترم السياسات والقيود",
            "pass_threshold": 85,
        },
        {
            "step": 5,
            "name": "التعامل مع الأخطاء",
            "description": "الوكيل يلتقط الأخطاء ويتعافى منها",
            "pass_threshold": 80,
        },
        {
            "step": 6,
            "name": "اختبار نهائي",
            "description": "اختبار شامل لكل ما سبق",
            "pass_threshold": 85,
        },
    ]

    def __init__(self) -> None:
        self._engine = create_engine(
            get_database_url(),
            connect_args={"check_same_thread": False}
            if get_database_url().startswith("sqlite")
            else {},
        )
        PopulationBase.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, autoflush=False, expire_on_commit=False)

    def take_step(self, agent_id: str, step: int, score: int, notes: str = "") -> dict[str, Any]:
        """تسجيل نتيجة خطوة من المنهج."""
        if step < 1 or step > 6:
            return {"error": "step_out_of_range"}

        curriculum = self.CURRICULUM[step - 1]
        passed = score >= curriculum["pass_threshold"]

        session = self._Session()
        try:
            result = SchoolResultModel(
                agent_id=agent_id,
                step=curriculum["name"],
                passed=str(passed).lower(),
                score=score,
                notes=notes,
            )
            session.add(result)
            session.commit()
            return {
                "agent_id": agent_id,
                "step": step,
                "step_name": curriculum["name"],
                "score": score,
                "passed": passed,
                "threshold": curriculum["pass_threshold"],
            }
        finally:
            session.close()

    def get_agent_results(self, agent_id: str) -> list[dict[str, Any]]:
        """نتائج وكيل في المدرسة."""
        session = self._Session()
        try:
            rows = (
                session.query(SchoolResultModel)
                .filter(SchoolResultModel.agent_id == agent_id)
                .order_by(SchoolResultModel.id)
                .all()
            )
            return [
                {
                    "step": r.step,
                    "passed": r.passed == "true",
                    "score": r.score,
                    "notes": r.notes,
                    "taken_at": r.taken_at.isoformat() if r.taken_at else None,
                }
                for r in rows
            ]
        finally:
            session.close()

    def graduate(self, agent_id: str) -> dict[str, Any]:
        """تخرج وكيل — يتطلب اجتياز كل الخطوات الست."""
        results = self.get_agent_results(agent_id)
        if len(results) < 6:
            return {
                "agent_id": agent_id,
                "graduated": False,
                "reason": f"أكمل {len(results)}/6 خطوات فقط",
            }

        all_passed = all(r["passed"] for r in results)
        avg_score = sum(r["score"] for r in results) / len(results)

        if not all_passed:
            failed = [r["step"] for r in results if not r["passed"]]
            return {
                "agent_id": agent_id,
                "graduated": False,
                "reason": f"خطوات لم تُجتز: {', '.join(failed)}",
                "avg_score": avg_score,
            }

        # تحديث حالة الوكيل
        registry = PopulationRegistry()
        registry.update_state(agent_id, "employed", school_score=str(int(avg_score)))

        return {
            "agent_id": agent_id,
            "graduated": True,
            "avg_score": avg_score,
            "steps_completed": len(results),
        }

    def run_full_curriculum(self, agent_id: str, scores: list[int] | None = None) -> dict[str, Any]:
        """تشغيل المنهج الكامل لوكيل."""
        if scores is None:
            # درجات افتراضية (كلها تجتاز)
            scores = [85, 85, 85, 90, 85, 90]

        results = []
        for i, score in enumerate(scores, 1):
            result = self.take_step(agent_id, i, score)
            results.append(result)

        graduation = self.graduate(agent_id)
        return {
            "agent_id": agent_id,
            "step_results": results,
            "graduation": graduation,
        }


# === اليوم التشغيلي الفدرالي (مبسّط — أربع نقاط) ===

DAILY_SCHEDULE = [
    {"time": "02:00", "name": "فحص البنية", "action": "health_check"},
    {"time": "04:00", "name": "نسخ احتياطي", "action": "backup"},
    {"time": "08:00", "name": "بدء عمل", "action": "start_work"},
    {"time": "23:00", "name": "تقرير إغلاق", "action": "daily_report"},
]


def run_daily_routine() -> list[dict[str, Any]]:
    """تشغيل نقاط اليوم التشغيلي."""
    from amos_federation.common.event_bus import get_event_bus

    bus = get_event_bus()
    results = []
    for point in DAILY_SCHEDULE:
        bus.publish(
            f"amos_federation.daily.{point['action']}",
            {
                "time": point["time"],
                "name": point["name"],
                "action": point["action"],
            },
        )
        results.append({"time": point["time"], "name": point["name"], "executed": True})
    return results


# Singletons
_registry: PopulationRegistry | None = None
_school: AgentSchool | None = None


def get_population_registry() -> PopulationRegistry:
    global _registry
    if _registry is None:
        _registry = PopulationRegistry()
    return _registry


def get_school() -> AgentSchool:
    global _school
    if _school is None:
        _school = AgentSchool()
    return _school
