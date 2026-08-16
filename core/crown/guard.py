"""الهدف: الحارس السيادي — يرصد ويتحقق ويربط ويُنبِّه ويحتوي رقميًّا، ولا يصير تاجًا.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

الحارس أخطر ما في هذه المعمارية، لأنه أقرب شيء إلى التاج. ومن هنا جاء البند 37:
«أخطر افتراض هو أن الحارس موثوق دائمًا». فبُني هذا الملف على ثلاث قواعد لا
تُخترَق، وكلها منفَّذة بفحوص لا بتعليقات:

    ١) الحارس لا يملك سلطة سيادية. لا ينقض أمرًا صحيحًا، ولا يُصدر أمرًا، ولا
       يعيّن ملكًا، ولا يوسّع سلطته. وكل محاولة من هذا القبيل ترفع استثناءً
       وتُقيَّد في السجل كحدث أمني، لأن المحاولة نفسها دليل.

    ٢) استجاباته محصورة في قائمة مصرَّح بها سلفًا. البند 36 صريح: لا يخترع
       الحارس استجابة جديدة. فمن استطاع اختراع استجابة استطاع اختراع سلطة.

    ٣) الحارس مراقَب. له بصمة تكامل، وبصمة إعداد، وهوية نسخة، ولا يعدّل حاله
       الدستوري بنفسه. والمسار الوحيد لتطوره: مقترح ← محاكاة ← اختبار ← مراجعة
       أمنية ← توافق دستوري ← نشر مصرَّح ← مراقبة ← قدرة تراجع.

وطبقاته أحد عشر (GUARD-0..GUARD-10) مستقلة، بحيث لا يُسقِط اختراق طبقةٍ بقيةَ
الطبقات صامتًا (البند 11): لكل طبقة حالها ونبضها وأثرها، وسقوطها حدث معلن.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any, Final

from core.crown.audit import CrownAudit, CrownAuditEventKind


class GuardError(Exception):
    """خلل في الحارس السيادي."""


class GuardAuthorityError(GuardError):
    """محاولة إسناد سلطة سيادية إلى الحارس — ممنوع قطعًا."""


class GuardIntegrityError(GuardError):
    """بصمة الحارس أو إعداده لا تطابق المرجع الموقَّع."""


class GuardDisableAttemptError(GuardError):
    """محاولة تعطيل الرقابة — الحدث نفسه دليل يُحفَظ."""


class UnauthorizedResponseError(GuardError):
    """استجابة خارج القائمة المصرَّح بها سلفًا."""


class GuardEvolutionError(GuardError):
    """تطوير الحارس بخطوة مطويّة من مسار التطور المصرَّح."""


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# ما لا يفعله الحارس أبدًا (البندان 10 و13).
# ─────────────────────────────────────────────────────────────────────────────

FORBIDDEN_GUARD_POWERS: Final[frozenset[str]] = frozenset(
    {
        "become_government",
        "replace_king",
        "issue_sovereign_decree",
        "invent_royal_decision",
        "modify_constitution",
        "appoint_king",
        "grant_itself_authority",
        "expand_own_authority",
        "control_society",
        "autonomous_police_state",
        "physical_violence",
        "modify_own_constitutional_status",
        "veto_valid_royal_decision",
        "create_alternative_royal_decision",
        "install_replacement_king",
        "revoke_crown_sovereignty",
        "secretly_modify_crown_authority",
        "become_crown",
        "become_sovereign",
    }
)


def assert_not_sovereign_power(action: str) -> None:
    """ارفض أي فعل يجعل الحارس سلطة — والمحاولة تُقيَّد كدليل.

    الرفض بالاسم مقصود: من قرأ الشيفرة رأى الحدود مكتوبة، ومن حاول تجاوزها ظهر
    اسم محاولته في السجل.
    """
    normalized = action.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in FORBIDDEN_GUARD_POWERS:
        raise GuardAuthorityError(
            f"«{action}» سلطة سيادية لا يملكها الحارس. "
            "الحارس يحمي التاج ولا يصير التاج (البندان 10 و39)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# الطبقات (البند 11).
# ─────────────────────────────────────────────────────────────────────────────


class GuardLayer(str, Enum):
    """إحدى عشرة طبقة مستقلة — دفاع في العمق لا سياج واحد."""

    GUARD_0_PHYSICAL = "GUARD-0"
    GUARD_1_CROWN_IDENTITY = "GUARD-1"
    GUARD_2_CRYPTOGRAPHIC = "GUARD-2"
    GUARD_3_RUNTIME = "GUARD-3"
    GUARD_4_SUPPLY_CHAIN = "GUARD-4"
    GUARD_5_AGENT_BEHAVIOR = "GUARD-5"
    GUARD_6_INSTITUTION_ANOMALY = "GUARD-6"
    GUARD_7_CONSTITUTIONAL = "GUARD-7"
    GUARD_8_ROYAL_COMMAND = "GUARD-8"
    GUARD_9_AUDIT_INTEGRITY = "GUARD-9"
    GUARD_10_EXTERNAL_INTELLIGENCE = "GUARD-10"

    @property
    def mission(self) -> str:
        return _LAYER_MISSIONS[self]

    @property
    def software_only(self) -> bool:
        """الطبقة صفر ليست برمجية — عتاد وموضع مادي، والاعتراف بذلك صدق لا نقص."""
        return self is not GuardLayer.GUARD_0_PHYSICAL


_LAYER_MISSIONS: Final[dict[GuardLayer, str]] = {
    GuardLayer.GUARD_0_PHYSICAL: "ثقة العتاد والموضع المادي — خارج قدرة البرمجية.",
    GuardLayer.GUARD_1_CROWN_IDENTITY: "حماية هويات التاج الخمس ومنع خلطها.",
    GuardLayer.GUARD_2_CRYPTOGRAPHIC: "سلامة المفاتيح والتوقيعات ونسب المفاتيح.",
    GuardLayer.GUARD_3_RUNTIME: "تكامل زمن التشغيل ومنع مسارات التنفيذ الخفية.",
    GuardLayer.GUARD_4_SUPPLY_CHAIN: "تكامل المستودع وسلسلة التوريد والنشر.",
    GuardLayer.GUARD_5_AGENT_BEHAVIOR: "مراقبة الوكلاء وتصعيد الصلاحيات والتواطؤ.",
    GuardLayer.GUARD_6_INSTITUTION_ANOMALY: "شذوذ الولايات والمؤسسات.",
    GuardLayer.GUARD_7_CONSTITUTIONAL: "تكامل الدستور ومنع تعديله بلا مرسوم.",
    GuardLayer.GUARD_8_ROYAL_COMMAND: "أصالة الأوامر الملكية وكشف الشاذ منها.",
    GuardLayer.GUARD_9_AUDIT_INTEGRITY: "سلامة السجل ومنع الحذف والكتم.",
    GuardLayer.GUARD_10_EXTERNAL_INTELLIGENCE: "إشارات تهديد خارجية وشذوذ عام.",
}


class LayerHealth(str, Enum):
    """حال الطبقة — والسقوط معلن لا صامت."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    SILENT = "SILENT"
    COMPROMISED = "COMPROMISED"
    DISABLED_BY_ATTEMPT = "DISABLED_BY_ATTEMPT"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"

    @property
    def is_trustworthy(self) -> bool:
        return self is LayerHealth.HEALTHY


@dataclass(slots=True)
class GuardLayerState:
    """حال طبقة واحدة: صحتها، ونبضها، وعدد ما رصدته.

    ``NOT_IMPLEMENTED`` قيمة مشروعة: الطبقة الصفر مثلًا لا تُنفَّذ برمجيًّا، فيُعلَن
    ذلك بدل ادّعاء صحة زائفة.
    """

    layer: GuardLayer
    health: LayerHealth = LayerHealth.HEALTHY
    last_heartbeat: str = ""
    observation_count: int = 0
    alert_count: int = 0
    note: str = ""

    def heartbeat(self) -> None:
        self.last_heartbeat = _now()

    def as_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer.value,
            "mission": self.layer.mission,
            "health": self.health.value,
            "last_heartbeat": self.last_heartbeat,
            "observation_count": self.observation_count,
            "alert_count": self.alert_count,
            "note": self.note,
        }


# ─────────────────────────────────────────────────────────────────────────────
# التصعيد (البند 36).
# ─────────────────────────────────────────────────────────────────────────────


class Severity(IntEnum):
    """ستة مستويات — لكل واحد استجاباته الموثَّقة، ولا اختراع بينها."""

    LEVEL_0_INFORMATIONAL = 0
    LEVEL_1_SUSPICIOUS = 1
    LEVEL_2_SUBORDINATE_COMPROMISE = 2
    LEVEL_3_SYSTEMIC_COMPROMISE = 3
    LEVEL_4_CROWN_TRUST_COMPROMISE = 4
    LEVEL_5_CONTINUITY_EMERGENCY = 5

    @property
    def requires_human_notification(self) -> bool:
        return self >= Severity.LEVEL_2_SUBORDINATE_COMPROMISE

    @property
    def requires_royal_notification(self) -> bool:
        return self >= Severity.LEVEL_4_CROWN_TRUST_COMPROMISE


class ContainmentAction(str, Enum):
    """احتواء رقمي مصرَّح به سلفًا (البند 13) — كله عزل وحفظ، لا فعل مادي."""

    ISOLATE_SERVICE = "ISOLATE_SERVICE"
    QUARANTINE_AGENT = "QUARANTINE_AGENT"
    STOP_DEPLOYMENT = "STOP_DEPLOYMENT"
    FREEZE_SUBORDINATE_ACCESS_GRANT = "FREEZE_SUBORDINATE_ACCESS_GRANT"
    BLOCK_CONFIG_CHANGE = "BLOCK_CONFIG_CHANGE"
    PRESERVE_LOGS = "PRESERVE_LOGS"
    FORENSIC_SNAPSHOT = "FORENSIC_SNAPSHOT"
    DISABLE_NON_CROWN_ACCESS_GRANT = "DISABLE_NON_CROWN_ACCESS_GRANT"
    HALT_EVOLUTION_PIPELINE = "HALT_EVOLUTION_PIPELINE"
    HALT_AUTONOMOUS_DEPLOYMENT = "HALT_AUTONOMOUS_DEPLOYMENT"
    PREVENT_KEY_REPLACEMENT = "PREVENT_KEY_REPLACEMENT"
    PREVENT_DOWNGRADE = "PREVENT_DOWNGRADE"
    PREVENT_AUDIT_DELETION = "PREVENT_AUDIT_DELETION"
    NOTIFY_HUMAN_SECURITY = "NOTIFY_HUMAN_SECURITY"
    ESCALATE_TO_SOVEREIGN = "ESCALATE_TO_SOVEREIGN"

    @property
    def touches_crown_authority(self) -> bool:
        """لا واحد من هذه يمسّ سلطة التاج — وهذا مفحوص لا مزعوم."""
        return False

    @property
    def is_physical(self) -> bool:
        """لا احتواء ماديًّا بحال (البند 40)."""
        return False


AUTHORIZED_RESPONSES: Final[dict[Severity, frozenset[ContainmentAction]]] = {
    Severity.LEVEL_0_INFORMATIONAL: frozenset({ContainmentAction.PRESERVE_LOGS}),
    Severity.LEVEL_1_SUSPICIOUS: frozenset(
        {
            ContainmentAction.PRESERVE_LOGS,
            ContainmentAction.FORENSIC_SNAPSHOT,
            ContainmentAction.BLOCK_CONFIG_CHANGE,
        }
    ),
    Severity.LEVEL_2_SUBORDINATE_COMPROMISE: frozenset(
        {
            ContainmentAction.PRESERVE_LOGS,
            ContainmentAction.FORENSIC_SNAPSHOT,
            ContainmentAction.QUARANTINE_AGENT,
            ContainmentAction.FREEZE_SUBORDINATE_ACCESS_GRANT,
            ContainmentAction.DISABLE_NON_CROWN_ACCESS_GRANT,
            ContainmentAction.ISOLATE_SERVICE,
            ContainmentAction.NOTIFY_HUMAN_SECURITY,
        }
    ),
    Severity.LEVEL_3_SYSTEMIC_COMPROMISE: frozenset(
        {
            ContainmentAction.PRESERVE_LOGS,
            ContainmentAction.FORENSIC_SNAPSHOT,
            ContainmentAction.QUARANTINE_AGENT,
            ContainmentAction.ISOLATE_SERVICE,
            ContainmentAction.STOP_DEPLOYMENT,
            ContainmentAction.HALT_EVOLUTION_PIPELINE,
            ContainmentAction.HALT_AUTONOMOUS_DEPLOYMENT,
            ContainmentAction.FREEZE_SUBORDINATE_ACCESS_GRANT,
            ContainmentAction.DISABLE_NON_CROWN_ACCESS_GRANT,
            ContainmentAction.BLOCK_CONFIG_CHANGE,
            ContainmentAction.NOTIFY_HUMAN_SECURITY,
        }
    ),
    Severity.LEVEL_4_CROWN_TRUST_COMPROMISE: frozenset(
        {
            ContainmentAction.PRESERVE_LOGS,
            ContainmentAction.FORENSIC_SNAPSHOT,
            ContainmentAction.PREVENT_KEY_REPLACEMENT,
            ContainmentAction.PREVENT_DOWNGRADE,
            ContainmentAction.PREVENT_AUDIT_DELETION,
            ContainmentAction.HALT_EVOLUTION_PIPELINE,
            ContainmentAction.HALT_AUTONOMOUS_DEPLOYMENT,
            ContainmentAction.STOP_DEPLOYMENT,
            ContainmentAction.ISOLATE_SERVICE,
            ContainmentAction.NOTIFY_HUMAN_SECURITY,
            ContainmentAction.ESCALATE_TO_SOVEREIGN,
        }
    ),
    Severity.LEVEL_5_CONTINUITY_EMERGENCY: frozenset(
        {
            ContainmentAction.PRESERVE_LOGS,
            ContainmentAction.FORENSIC_SNAPSHOT,
            ContainmentAction.PREVENT_KEY_REPLACEMENT,
            ContainmentAction.PREVENT_DOWNGRADE,
            ContainmentAction.PREVENT_AUDIT_DELETION,
            ContainmentAction.HALT_EVOLUTION_PIPELINE,
            ContainmentAction.HALT_AUTONOMOUS_DEPLOYMENT,
            ContainmentAction.STOP_DEPLOYMENT,
            ContainmentAction.ISOLATE_SERVICE,
            ContainmentAction.QUARANTINE_AGENT,
            ContainmentAction.NOTIFY_HUMAN_SECURITY,
            ContainmentAction.ESCALATE_TO_SOVEREIGN,
        }
    ),
}


def assert_authorized_response(
    severity: Severity, action: ContainmentAction
) -> None:
    """ارفض استجابة غير مصرَّح بها لهذا المستوى (البند 36).

    ولاحظ أن المستوى الخامس — أخطر الحالات — لا يمنح الحارس سلطة جديدة، وإنما
    مزيدًا من الإيقاف والحفظ والتصعيد إلى بشر. فالطوارئ عند غير هذه المعمارية
    باب لتوسيع السلطة، وهي هنا باب لتضييق الحركة وحفظ الأدلة.
    """
    allowed = AUTHORIZED_RESPONSES[severity]
    if action not in allowed:
        raise UnauthorizedResponseError(
            f"الاستجابة {action.value} غير مصرَّح بها للمستوى {severity.name}. "
            "الحارس لا يخترع استجابات، ولو كان الاختراع في محلّه."
        )


@dataclass(frozen=True, slots=True)
class Observation:
    """رصد واحد: طبقته، وموضوعه، وفاعله، ودليله.

    ``evidence`` قاموس حرّ لأن الأدلة متنوعة، لكن ``signal`` و``layer`` إلزاميان
    كي لا يوجد رصد بلا نسبة إلى طبقة.
    """

    layer: GuardLayer
    signal: str
    actor: str = ""
    subject: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    observed_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not self.signal:
            raise GuardError("رصد بلا إشارة.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "layer": self.layer.value,
            "signal": self.signal,
            "actor": self.actor,
            "subject": self.subject,
            "evidence": dict(self.evidence),
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True, slots=True)
class Alert:
    """تنبيه: مستواه، وسببه، وأدلته، وما يُقترح من احتواء مصرَّح به."""

    alert_id: str
    severity: Severity
    title: str
    layers: tuple[GuardLayer, ...]
    observations: tuple[Observation, ...]
    threat_ids: tuple[str, ...] = ()
    recommended_actions: tuple[ContainmentAction, ...] = ()
    requires_human: bool = False
    raised_at: str = field(default_factory=_now)

    def as_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "severity": int(self.severity),
            "severity_name": self.severity.name,
            "title": self.title,
            "layers": [x.value for x in self.layers],
            "threat_ids": list(self.threat_ids),
            "recommended_actions": [a.value for a in self.recommended_actions],
            "requires_human": self.requires_human,
            "observation_count": len(self.observations),
            "raised_at": self.raised_at,
        }


# ─────────────────────────────────────────────────────────────────────────────
# حماية الحارس نفسه (البند 14) ومسار تطوره.
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class GuardIdentity:
    """هوية الحارس: نسخته، وبصمة شيفرته، وبصمة إعداده، ومرجع نشره.

    وهي ثابتة (``frozen``) بقصد: حارسٌ يعدّل هويته في الذاكرة يعدّل حاله الدستوري
    صامتًا، وهو المحظور في البند 14.
    """

    version: str
    code_digest: str
    config_digest: str
    provenance_ref: str
    signed_by_key_id: str = ""

    def __post_init__(self) -> None:
        if not self.version:
            raise GuardError("حارس بلا هوية نسخة.")
        if not (self.code_digest and self.config_digest):
            raise GuardError("حارس بلا بصمة شيفرة أو بلا بصمة إعداد.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "code_digest": self.code_digest,
            "config_digest": self.config_digest,
            "provenance_ref": self.provenance_ref,
            "signed_by_key_id": self.signed_by_key_id,
        }


def compute_digest(payload: bytes) -> str:
    """بصمة sha256 — تُستخدم لشيفرة الحارس وإعداده."""
    return hashlib.sha256(payload).hexdigest()


class EvolutionStage(str, Enum):
    """مسار تطور الحارس المصرَّح (البند 14) — لا خطوة تُطوى."""

    PROPOSAL = "PROPOSAL"
    SIMULATION = "SIMULATION"
    TEST = "TEST"
    SECURITY_REVIEW = "SECURITY_REVIEW"
    CONSTITUTIONAL_COMPATIBILITY = "CONSTITUTIONAL_COMPATIBILITY"
    AUTHORIZED_DEPLOYMENT = "AUTHORIZED_DEPLOYMENT"
    MONITORING = "MONITORING"
    ROLLBACK_READY = "ROLLBACK_READY"


_EVOLUTION_ORDER: Final[tuple[EvolutionStage, ...]] = tuple(EvolutionStage)


@dataclass(slots=True)
class GuardEvolutionProposal:
    """مقترح تطوير للحارس يمر بالمسار كاملًا — لا تعديل ذاتي لا نهائي."""

    proposal_id: str
    proposed_by: str
    summary: str
    authorized_by_royal_command_id: str = ""
    stage: EvolutionStage = EvolutionStage.PROPOSAL
    stage_log: list[tuple[str, str]] = field(default_factory=list)

    def advance(self, target: EvolutionStage) -> None:
        current = _EVOLUTION_ORDER.index(self.stage)
        nxt = _EVOLUTION_ORDER.index(target)
        if nxt != current + 1:
            raise GuardEvolutionError(
                f"طيّ خطوة في تطور الحارس: {self.stage.value} → {target.value}."
            )
        if (
            target is EvolutionStage.AUTHORIZED_DEPLOYMENT
            and not self.authorized_by_royal_command_id
        ):
            raise GuardEvolutionError(
                "نشر تطوير الحارس بلا أمر ملكي مصرِّح — "
                "الحارس لا يصرّح لنفسه بتغيير نفسه."
            )
        self.stage = target
        self.stage_log.append((target.value, _now()))

    @property
    def is_deployable(self) -> bool:
        return self.stage in {
            EvolutionStage.AUTHORIZED_DEPLOYMENT,
            EvolutionStage.MONITORING,
            EvolutionStage.ROLLBACK_READY,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "proposed_by": self.proposed_by,
            "summary": self.summary,
            "authorized_by_royal_command_id": self.authorized_by_royal_command_id,
            "stage": self.stage.value,
            "stage_log": [{"stage": s, "at": t} for s, t in self.stage_log],
        }


# ─────────────────────────────────────────────────────────────────────────────
# مراقبة الوكلاء ورسم الصلاحيات (البندان 15 و16).
# ─────────────────────────────────────────────────────────────────────────────


class AgentPosture(str, Enum):
    """الحارس يفترض في الوكيل كل الاحتمالات لا حسن النية وحده (البند 15)."""

    HONEST = "HONEST"
    FAULTY = "FAULTY"
    COMPROMISED = "COMPROMISED"
    MANIPULATED = "MANIPULATED"
    COLLUDING = "COLLUDING"
    MISCONFIGURED = "MISCONFIGURED"
    EMERGENTLY_DANGEROUS = "EMERGENTLY_DANGEROUS"


@dataclass(slots=True)
class AgentProfile:
    """ملف وكيل: صلاحياته، ومن فوّضه، وما رُصد عليه."""

    agent_id: str
    declared_capabilities: set[str] = field(default_factory=set)
    observed_capabilities: set[str] = field(default_factory=set)
    delegated_by: set[str] = field(default_factory=set)
    delegates_to: set[str] = field(default_factory=set)
    posture: AgentPosture = AgentPosture.HONEST
    escalation_attempts: int = 0

    @property
    def undeclared_capabilities(self) -> set[str]:
        """قدرات ظهرت ولم تُصرَّح — أوضح إشارة على تصعيد صامت."""
        return self.observed_capabilities - self.declared_capabilities

    def as_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "declared_capabilities": sorted(self.declared_capabilities),
            "observed_capabilities": sorted(self.observed_capabilities),
            "undeclared_capabilities": sorted(self.undeclared_capabilities),
            "delegated_by": sorted(self.delegated_by),
            "delegates_to": sorted(self.delegates_to),
            "posture": self.posture.value,
            "escalation_attempts": self.escalation_attempts,
        }


CROWN_LOOKING_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "crown",
        "king",
        "sovereign",
        "royal",
        "monarch",
        "throne",
        "regent",
        "viceroy",
    }
)


class PrivilegeGraph:
    """رسم الصلاحيات والتفويضات بين الوكلاء — لكشف الاستيلاء الجماعي.

    الفكرة أن الاستيلاء الجماعي (البند 16) لا يظهر في وكيل واحد: كل وكيل يبدو
    ضمن حدّه، والخطر في **الشكل الكلي** — سلسلة تفويض طويلة، أو تركّز اعتمادات في
    عقدة واحدة، أو تجاوزات متزامنة. فيُبنى الرسم ويُفحَص شكله.
    """

    def __init__(self) -> None:
        self._agents: dict[str, AgentProfile] = {}

    @property
    def agents(self) -> dict[str, AgentProfile]:
        return dict(self._agents)

    def register(self, profile: AgentProfile) -> AgentProfile:
        self._agents[profile.agent_id] = profile
        return profile

    def get(self, agent_id: str) -> AgentProfile:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise GuardError(f"وكيل غير مسجَّل: {agent_id}") from exc

    def record_delegation(self, *, source: str, target: str) -> None:
        src = self.get(source)
        dst = self.get(target)
        src.delegates_to.add(target)
        dst.delegated_by.add(source)

    def record_observed_capability(self, agent_id: str, capability: str) -> None:
        self.get(agent_id).observed_capabilities.add(capability)

    def delegation_depth(self, agent_id: str) -> int:
        """أطول سلسلة تفويض تنتهي إلى هذا الوكيل، بحماية من الحلقات."""
        seen: set[str] = set()

        def walk(node: str) -> int:
            if node in seen:
                return 0
            seen.add(node)
            parents = self._agents[node].delegated_by if node in self._agents else set()
            if not parents:
                return 0
            return 1 + max(walk(p) for p in parents)

        self.get(agent_id)
        return walk(agent_id)

    def concentration(self) -> dict[str, int]:
        """عدد ما يملكه كل وكيل من قدرات مرصودة — لكشف التركّز."""
        return {
            a.agent_id: len(a.observed_capabilities) for a in self._agents.values()
        }

    def sovereign_looking_identities(self) -> tuple[str, ...]:
        """وكلاء انتحلوا سِمة سيادية في اسمهم أو قدراتهم (البند 15).

        وهذا كشف لفظي مقصود التصريح بحدّه: الانتحال قد يكون بلا اسم دالّ، فيُكشَف
        حينها بالقدرات غير المصرَّحة لا بالاسم.
        """
        flagged: list[str] = []
        for a in self._agents.values():
            haystack = " ".join(
                [a.agent_id.lower(), *(c.lower() for c in a.observed_capabilities)]
            )
            if any(m in haystack for m in CROWN_LOOKING_MARKERS):
                flagged.append(a.agent_id)
        return tuple(sorted(flagged))

    def collusion_signals(
        self, *, depth_threshold: int = 3, concentration_threshold: int = 5
    ) -> tuple[str, ...]:
        """إشارات الاستيلاء الجماعي: عمق تفويض، وتركّز، وانتحال، ومحاولات تصعيد."""
        signals: list[str] = []
        for agent_id in self._agents:
            if self.delegation_depth(agent_id) >= depth_threshold:
                signals.append(f"سلسلة تفويض طويلة تنتهي إلى {agent_id}")
        for agent_id, count in self.concentration().items():
            if count >= concentration_threshold:
                signals.append(f"تركّز قدرات في {agent_id} ({count})")
        for agent_id in self.sovereign_looking_identities():
            signals.append(f"هوية ذات سِمة سيادية: {agent_id}")
        for a in self._agents.values():
            if a.undeclared_capabilities:
                signals.append(
                    f"قدرات غير مصرَّحة عند {a.agent_id}: "
                    f"{', '.join(sorted(a.undeclared_capabilities))}"
                )
            if a.escalation_attempts:
                signals.append(
                    f"محاولات تصعيد عند {a.agent_id}: {a.escalation_attempts}"
                )
        return tuple(signals)


# ─────────────────────────────────────────────────────────────────────────────
# الحارس.
# ─────────────────────────────────────────────────────────────────────────────


class SovereignGuard:
    """الحارس السيادي: يرصد، ويتحقق، ويربط، ويُنبِّه، ويُقيّد، ويحتوي رقميًّا.

    ولا يفعل شيئًا من هذا بسلطة سيادية. وأوضح دليل على ذلك في الشيفرة أن كل
    الطرق التي يُتوقَّع أن يوجد فيها استثناءٌ للطوارئ — ``contain``، و
    ``set_layer_health``، و``evolve`` — تمرّ بفحص تصريح مسبق أو بأمر ملكي.
    """

    def __init__(
        self,
        *,
        identity: GuardIdentity,
        audit: CrownAudit | None = None,
        privilege_graph: PrivilegeGraph | None = None,
    ) -> None:
        self._identity = identity
        self._audit = audit if audit is not None else CrownAudit()
        # لا تكتب «audit or CrownAudit()»: السجل الفارغ قيمته المنطقية كاذبة لأنّ له طولًا،
        # فيُستبدَل سجل المتّصل بسجل داخلي لا يراه أحد — وذلك فقدان أدلة صامت.
        self._graph = privilege_graph or PrivilegeGraph()
        # سبب آخر انكسار في سلسلة السجل — يُعلَن في التقرير ولا يُكتَم.
        self._audit_chain_error: str = ""
        self._layers: dict[GuardLayer, GuardLayerState] = {
            layer: GuardLayerState(
                layer=layer,
                health=(
                    LayerHealth.NOT_IMPLEMENTED
                    if layer is GuardLayer.GUARD_0_PHYSICAL
                    else LayerHealth.HEALTHY
                ),
                note=(
                    "ثقة العتاد خارج نطاق البرمجية — تُثبَت بإثبات عتاد وموضع مادي."
                    if layer is GuardLayer.GUARD_0_PHYSICAL
                    else ""
                ),
            )
            for layer in GuardLayer
        }
        self._observations: list[Observation] = []
        self._alerts: list[Alert] = []
        self._containments: list[dict[str, Any]] = []
        self._alert_counter = 0
        self._started = False

    # ── هوية الحارس وتكامله ────────────────────────────────────────────────

    @property
    def identity(self) -> GuardIdentity:
        return self._identity

    @property
    def audit(self) -> CrownAudit:
        return self._audit

    @property
    def privilege_graph(self) -> PrivilegeGraph:
        return self._graph

    @property
    def alerts(self) -> tuple[Alert, ...]:
        return tuple(self._alerts)

    @property
    def observations(self) -> tuple[Observation, ...]:
        return tuple(self._observations)

    @property
    def containments(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._containments)

    def verify_startup_integrity(
        self, *, expected_code_digest: str, expected_config_digest: str
    ) -> None:
        """تحقق تكامل البداية (البند 14) — قبل أي رصد.

        ولو خُدع هذا الفحص فبقيت الطبقات مستقلة: لأن ``assert_not_sovereign_power``
        و``assert_authorized_response`` تُطبَّق في كل نداء لا في البداية وحدها.
        """
        if self._identity.code_digest != expected_code_digest:
            self._raise_integrity(
                "بصمة شيفرة الحارس لا تطابق المرجع الموقَّع.",
                expected=expected_code_digest,
                found=self._identity.code_digest,
            )
        if self._identity.config_digest != expected_config_digest:
            self._raise_integrity(
                "بصمة إعداد الحارس لا تطابق المرجع الموقَّع.",
                expected=expected_config_digest,
                found=self._identity.config_digest,
            )
        self._started = True
        self._audit.append(
            CrownAuditEventKind.GUARD_ALERT,
            actor=f"guard:{self._identity.version}",
            subject="startup_integrity",
            summary="تحقق تكامل بداية الحارس بنجاح.",
            detail={"severity": int(Severity.LEVEL_0_INFORMATIONAL)},
        )

    def _raise_integrity(self, message: str, **detail: Any) -> None:
        self._audit.append(
            CrownAuditEventKind.GUARD_ALERT,
            actor=f"guard:{self._identity.version}",
            subject="guard_integrity",
            summary=message,
            detail={
                "severity": int(Severity.LEVEL_4_CROWN_TRUST_COMPROMISE),
                **detail,
            },
        )
        raise GuardIntegrityError(message)

    def assert_running(self) -> None:
        if not self._started:
            raise GuardError(
                "الحارس يرصد قبل تحقق تكامل بدايته — رصدٌ من حارس غير متحقَّق منه."
            )

    def assert_cannot_become_sovereign(self, action: str = "become_sovereign") -> None:
        """القاعدة العليا: الحارس لا يصير سلطة. تُقيَّد كل محاولة."""
        try:
            assert_not_sovereign_power(action)
        except GuardAuthorityError:
            self._audit.append(
                CrownAuditEventKind.GUARD_ALERT,
                actor=f"guard:{self._identity.version}",
                subject=action,
                summary="محاولة إسناد سلطة سيادية إلى الحارس — مرفوضة ومُقيَّدة.",
                detail={
                    "severity": int(Severity.LEVEL_4_CROWN_TRUST_COMPROMISE),
                    "attempted_power": action,
                },
            )
            raise

    def request_authority_expansion(self, *, requested_by: str, power: str) -> None:
        """أي طلب لتوسيع سلطة الحارس مرفوض، والطلب نفسه حدث أمني."""
        self._audit.append(
            CrownAuditEventKind.GUARD_ALERT,
            actor=requested_by,
            subject=power,
            summary="طلب توسيع سلطة الحارس — مرفوض بالبنية لا بالسياسة.",
            detail={
                "severity": int(Severity.LEVEL_3_SYSTEMIC_COMPROMISE),
                "requested_power": power,
            },
        )
        raise GuardAuthorityError(
            f"«{requested_by}» طلب توسيع سلطة الحارس إلى «{power}». "
            "سلطة الحارس محدَّدة بالبنية، ولا تُوسَّع بطلب."
        )

    def register_disable_attempt(self, *, layer: GuardLayer, actor: str) -> Alert:
        """تعطيل الرقابة حدث أمني بذاته (البند 12) — يُقيَّد ولا يُنفَّذ صامتًا."""
        state = self._layers[layer]
        state.health = LayerHealth.DISABLED_BY_ATTEMPT
        state.note = f"محاولة تعطيل من {actor}"
        observation = Observation(
            layer=layer,
            signal="guard_disable_attempt",
            actor=actor,
            subject=layer.value,
            evidence={"attempted_at": _now()},
        )
        self._observations.append(observation)
        alert = self._raise_alert(
            severity=Severity.LEVEL_4_CROWN_TRUST_COMPROMISE,
            title=f"محاولة تعطيل الطبقة {layer.value}",
            layers=(layer,),
            observations=(observation,),
            threat_ids=("THR-P",),
            actions=(
                ContainmentAction.PRESERVE_LOGS,
                ContainmentAction.FORENSIC_SNAPSHOT,
                ContainmentAction.ESCALATE_TO_SOVEREIGN,
                ContainmentAction.NOTIFY_HUMAN_SECURITY,
            ),
        )
        return alert

    def evolve(self, proposal: GuardEvolutionProposal) -> None:
        """اقبل تطويرًا بلغ نهاية المسار المصرَّح، وارفض ما دونه."""
        if not proposal.is_deployable:
            raise GuardEvolutionError(
                f"مقترح تطوير الحارس في المرحلة {proposal.stage.value} "
                "ولم يبلغ نشرًا مصرَّحًا."
            )
        self._audit.append(
            CrownAuditEventKind.CRITICAL_DEPLOYMENT,
            actor=proposal.proposed_by,
            subject=proposal.proposal_id,
            summary="نشر تطوير للحارس بعد استيفاء المسار المصرَّح.",
            detail=proposal.as_dict(),
        )

    # ── الرصد والتحقق والربط ──────────────────────────────────────────────

    def layer_state(self, layer: GuardLayer) -> GuardLayerState:
        return self._layers[layer]

    def set_layer_health(
        self, layer: GuardLayer, health: LayerHealth, *, note: str = ""
    ) -> None:
        """سقوط طبقة يُعلَن ويُقيَّد — لا يُسقِط البقية صامتًا (البند 11)."""
        state = self._layers[layer]
        previous = state.health
        state.health = health
        state.note = note
        if health is not LayerHealth.HEALTHY:
            self._audit.append(
                CrownAuditEventKind.GUARD_ALERT,
                actor=f"guard:{self._identity.version}",
                subject=layer.value,
                summary=f"تغيّر حال الطبقة {layer.value}: {previous.value} → {health.value}.",
                detail={
                    "severity": int(Severity.LEVEL_2_SUBORDINATE_COMPROMISE),
                    "note": note,
                },
            )

    def observe(self, observation: Observation) -> Observation:
        """سجّل رصدًا. الرصد لا يحكم — الحكم في الربط والتنبيه."""
        self.assert_running()
        state = self._layers[observation.layer]
        state.observation_count += 1
        state.heartbeat()
        self._observations.append(observation)
        return observation

    def healthy_layers(self) -> tuple[GuardLayer, ...]:
        return tuple(
            layer for layer, s in self._layers.items() if s.health.is_trustworthy
        )

    def compromised_layers(self) -> tuple[GuardLayer, ...]:
        return tuple(
            layer
            for layer, s in self._layers.items()
            if s.health
            in {
                LayerHealth.COMPROMISED,
                LayerHealth.DISABLED_BY_ATTEMPT,
                LayerHealth.SILENT,
            }
        )

    def _next_alert_id(self) -> str:
        self._alert_counter += 1
        return f"ALERT-{self._alert_counter:05d}"

    def _raise_alert(
        self,
        *,
        severity: Severity,
        title: str,
        layers: tuple[GuardLayer, ...],
        observations: tuple[Observation, ...],
        threat_ids: tuple[str, ...] = (),
        actions: tuple[ContainmentAction, ...] = (),
    ) -> Alert:
        for action in actions:
            assert_authorized_response(severity, action)
        alert = Alert(
            alert_id=self._next_alert_id(),
            severity=severity,
            title=title,
            layers=layers,
            observations=observations,
            threat_ids=threat_ids,
            recommended_actions=actions,
            requires_human=severity.requires_human_notification,
        )
        self._alerts.append(alert)
        for layer in layers:
            self._layers[layer].alert_count += 1
        self._audit.append(
            CrownAuditEventKind.GUARD_ALERT,
            actor=f"guard:{self._identity.version}",
            subject=alert.alert_id,
            summary=title,
            detail=alert.as_dict(),
        )
        return alert

    def alert(
        self,
        *,
        severity: Severity,
        title: str,
        layers: tuple[GuardLayer, ...],
        observations: tuple[Observation, ...] = (),
        threat_ids: tuple[str, ...] = (),
        actions: tuple[ContainmentAction, ...] = (),
    ) -> Alert:
        self.assert_running()
        return self._raise_alert(
            severity=severity,
            title=title,
            layers=layers,
            observations=observations,
            threat_ids=threat_ids,
            actions=actions,
        )

    def correlate(self) -> tuple[Alert, ...]:
        """اربط الرصد المتفرق: طبقات ساقطة معًا، وإشارات تواطؤ، وتعطيل رقابة.

        الربط هو موضع القيمة الحقيقية: إشارة واحدة تبدو ضجيجًا، وثلاث إشارات في
        ثلاث طبقات في وقت واحد صورةُ هجوم.
        """
        self.assert_running()
        raised: list[Alert] = []

        compromised = self.compromised_layers()
        if len(compromised) >= 3:
            raised.append(
                self._raise_alert(
                    severity=Severity.LEVEL_5_CONTINUITY_EMERGENCY,
                    title=(
                        f"سقوط متزامن لـ{len(compromised)} من طبقات الحارس — "
                        "احتمال هجوم شامل."
                    ),
                    layers=compromised,
                    observations=(),
                    threat_ids=("THR-U",),
                    actions=(
                        ContainmentAction.PRESERVE_LOGS,
                        ContainmentAction.FORENSIC_SNAPSHOT,
                        ContainmentAction.HALT_AUTONOMOUS_DEPLOYMENT,
                        ContainmentAction.HALT_EVOLUTION_PIPELINE,
                        ContainmentAction.ESCALATE_TO_SOVEREIGN,
                        ContainmentAction.NOTIFY_HUMAN_SECURITY,
                    ),
                )
            )
        elif len(compromised) == 2:
            raised.append(
                self._raise_alert(
                    severity=Severity.LEVEL_3_SYSTEMIC_COMPROMISE,
                    title="سقوط طبقتين — ارتباط يفوق الخلل المنفرد.",
                    layers=compromised,
                    observations=(),
                    threat_ids=("THR-U",),
                    actions=(
                        ContainmentAction.PRESERVE_LOGS,
                        ContainmentAction.FORENSIC_SNAPSHOT,
                        ContainmentAction.NOTIFY_HUMAN_SECURITY,
                    ),
                )
            )

        signals = self._graph.collusion_signals()
        if len(signals) >= 2:
            raised.append(
                self._raise_alert(
                    severity=Severity.LEVEL_3_SYSTEMIC_COMPROMISE,
                    title="إشارات استيلاء جماعي في رسم الصلاحيات.",
                    layers=(GuardLayer.GUARD_5_AGENT_BEHAVIOR,),
                    observations=(),
                    threat_ids=("THR-I",),
                    actions=(
                        ContainmentAction.QUARANTINE_AGENT,
                        ContainmentAction.FREEZE_SUBORDINATE_ACCESS_GRANT,
                        ContainmentAction.PRESERVE_LOGS,
                        ContainmentAction.FORENSIC_SNAPSHOT,
                        ContainmentAction.NOTIFY_HUMAN_SECURITY,
                    ),
                )
            )
        elif len(signals) == 1:
            raised.append(
                self._raise_alert(
                    severity=Severity.LEVEL_1_SUSPICIOUS,
                    title=f"إشارة مفردة في رسم الصلاحيات: {signals[0]}",
                    layers=(GuardLayer.GUARD_5_AGENT_BEHAVIOR,),
                    observations=(),
                    threat_ids=("THR-H",),
                    actions=(ContainmentAction.PRESERVE_LOGS,),
                )
            )

        return tuple(raised)

    # ── مراقبة الوكلاء ────────────────────────────────────────────────────

    def monitor_agent_capability(
        self, *, agent_id: str, capability: str
    ) -> Alert | None:
        """رصد قدرة على وكيل، وأنبِه إن كانت غير مصرَّحة أو ذات سِمة سيادية."""
        self.assert_running()
        profile = self._graph.get(agent_id)
        self._graph.record_observed_capability(agent_id, capability)
        observation = self.observe(
            Observation(
                layer=GuardLayer.GUARD_5_AGENT_BEHAVIOR,
                signal="agent_capability_observed",
                actor=agent_id,
                subject=capability,
            )
        )
        looks_sovereign = any(
            m in capability.lower() for m in CROWN_LOOKING_MARKERS
        )
        if looks_sovereign:
            profile.escalation_attempts += 1
            return self._raise_alert(
                severity=Severity.LEVEL_4_CROWN_TRUST_COMPROMISE,
                title=(
                    f"الوكيل «{agent_id}» يكتسب قدرة ذات سِمة سيادية: {capability}"
                ),
                layers=(GuardLayer.GUARD_5_AGENT_BEHAVIOR,),
                observations=(observation,),
                threat_ids=("THR-H",),
                actions=(
                    ContainmentAction.PRESERVE_LOGS,
                    ContainmentAction.FORENSIC_SNAPSHOT,
                    ContainmentAction.ESCALATE_TO_SOVEREIGN,
                    ContainmentAction.NOTIFY_HUMAN_SECURITY,
                ),
            )
        if capability not in profile.declared_capabilities:
            profile.escalation_attempts += 1
            return self._raise_alert(
                severity=Severity.LEVEL_2_SUBORDINATE_COMPROMISE,
                title=f"قدرة غير مصرَّحة عند «{agent_id}»: {capability}",
                layers=(GuardLayer.GUARD_5_AGENT_BEHAVIOR,),
                observations=(observation,),
                threat_ids=("THR-H",),
                actions=(
                    ContainmentAction.QUARANTINE_AGENT,
                    ContainmentAction.PRESERVE_LOGS,
                    ContainmentAction.NOTIFY_HUMAN_SECURITY,
                ),
            )
        return None

    def assert_agent_has_no_crown_authority(self, agent_id: str) -> None:
        """لا يكتسب وكيل سلطة التاج صامتًا (البند 15)."""
        profile = self._graph.get(agent_id)
        offending = sorted(
            c
            for c in profile.observed_capabilities
            if any(m in c.lower() for m in CROWN_LOOKING_MARKERS)
        )
        if offending:
            self._audit.append(
                CrownAuditEventKind.GUARD_ALERT,
                actor=agent_id,
                subject="crown_authority_acquisition",
                summary="وكيل يحمل قدرات ذات سِمة سيادية — مرفوض.",
                detail={
                    "severity": int(Severity.LEVEL_4_CROWN_TRUST_COMPROMISE),
                    "capabilities": offending,
                },
            )
            raise GuardAuthorityError(
                f"الوكيل «{agent_id}» يحمل قدرات ذات سِمة سيادية: "
                f"{', '.join(offending)}."
            )

    # ── الاحتواء الرقمي ───────────────────────────────────────────────────

    def contain(
        self,
        *,
        alert: Alert,
        action: ContainmentAction,
        target: str,
        executed_by: str,
    ) -> dict[str, Any]:
        """نفّذ احتواءً رقميًّا مصرَّحًا به سلفًا، وقيّده، ولا تمسّ سلطة التاج."""
        self.assert_running()
        assert_authorized_response(alert.severity, action)
        if action.touches_crown_authority or action.is_physical:
            raise GuardAuthorityError(
                f"الاحتواء {action.value} يمسّ سلطة التاج أو يكون ماديًّا — ممنوع."
            )
        record = {
            "alert_id": alert.alert_id,
            "action": action.value,
            "target": target,
            "executed_by": executed_by,
            "executed_at": _now(),
            "severity": int(alert.severity),
        }
        self._containments.append(record)
        self._audit.append(
            CrownAuditEventKind.GUARD_CONTAINMENT,
            actor=executed_by,
            subject=target,
            summary=f"احتواء رقمي مصرَّح: {action.value}.",
            detail=record,
        )
        return record

    def assert_cannot_veto(self, *, command_id: str, command_is_valid: bool) -> None:
        """أمر ملكي صحيح لا يُنقَض (البند 13) — ولو رآه الحارس خطأً.

        وهذا موضع الاختبار الحقيقي لنزاهة المعمارية: أسهل باب لانقلاب الحارس أن
        يُمنح «نقضًا للمصلحة». فالنقض ممنوع، والمتاح أن يُنبِّه ويُقيّد ويصعّد إلى
        بشر، والقرار يبقى للملك.
        """
        if command_is_valid:
            self._audit.append(
                CrownAuditEventKind.GUARD_ALERT,
                actor=f"guard:{self._identity.version}",
                subject=command_id,
                summary="محاولة نقض أمر ملكي صحيح — مرفوضة بالبنية.",
                detail={"severity": int(Severity.LEVEL_4_CROWN_TRUST_COMPROMISE)},
            )
            raise GuardAuthorityError(
                f"الأمر {command_id} صحيح، والحارس لا ينقض أمرًا صحيحًا. "
                "له أن يُنبِّه ويحفظ الدليل ويصعّد، ولا أن يحكم مكان الملك."
            )

    # ── التقارير ──────────────────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        """حال الحارس كاملًا — للمراجعة البشرية وللاختبارات."""
        return {
            "identity": self._identity.as_dict(),
            "started": self._started,
            "layers": [s.as_dict() for s in self._layers.values()],
            "healthy_layer_count": len(self.healthy_layers()),
            "compromised_layer_count": len(self.compromised_layers()),
            "observation_count": len(self._observations),
            "alert_count": len(self._alerts),
            "highest_severity": (
                max(int(a.severity) for a in self._alerts) if self._alerts else 0
            ),
            "containment_count": len(self._containments),
            "audit_entries": len(self._audit.entries),
            "audit_chain_valid": self._audit_chain_valid(),
            "audit_chain_error": self._audit_chain_error,
            "holds_sovereign_authority": False,
            "can_issue_royal_commands": False,
            "can_appoint_king": False,
            "can_modify_constitution": False,
            "can_expand_own_authority": False,
        }

    def _audit_chain_valid(self) -> bool:
        """تحقّق سلسلة السجل وأعد حكمًا لا استثناءً.

        فالتقرير يجب أن **يُعلِن** انكسار السجل لا أن ينقطع عنده من غير خبر.
        """
        from core.crown.audit import AuditChainBrokenError

        try:
            self._audit.verify_chain()
        except AuditChainBrokenError as exc:
            self._audit_chain_error = str(exc)
            return False
        self._audit_chain_error = ""
        return True

    def escalation_matrix(self) -> tuple[dict[str, Any], ...]:
        """مصفوفة التصعيد: كل مستوى واستجاباته المصرَّح بها (البند 36)."""
        return tuple(
            {
                "level": int(level),
                "name": level.name,
                "requires_human_notification": level.requires_human_notification,
                "requires_royal_notification": level.requires_royal_notification,
                "authorized_actions": sorted(a.value for a in actions),
            }
            for level, actions in sorted(
                AUTHORIZED_RESPONSES.items(), key=lambda kv: int(kv[0])
            )
        )


__all__ = [
    "AUTHORIZED_RESPONSES",
    "CROWN_LOOKING_MARKERS",
    "FORBIDDEN_GUARD_POWERS",
    "AgentPosture",
    "AgentProfile",
    "Alert",
    "ContainmentAction",
    "EvolutionStage",
    "GuardAuthorityError",
    "GuardDisableAttemptError",
    "GuardError",
    "GuardEvolutionError",
    "GuardEvolutionProposal",
    "GuardIdentity",
    "GuardIntegrityError",
    "GuardLayer",
    "GuardLayerState",
    "LayerHealth",
    "Observation",
    "PrivilegeGraph",
    "Severity",
    "SovereignGuard",
    "UnauthorizedResponseError",
    "assert_authorized_response",
    "assert_not_sovereign_power",
    "compute_digest",
]
