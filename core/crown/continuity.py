"""الهدف: حالات استمرارية التاج معلنة صراحةً، ولا استنتاج آليًّا لغياب ولا لموت ولا لتنازل.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

هذا الملف يعالج أخطر خطأ يمكن أن يقع فيه نظام سيادي: **أن يستنتج**. جهاز مطفأ
ليس ملكًا ميتًا، وشبكة منقطعة ليست تنازلًا، وبصمة غير متاحة ليست غياب ملك، وصمتًا
لأسبوع ليس وفاة. من بنى قراره على هذه الاستنتاجات أنشأ ملكًا جديدًا بحادث تقني.

فالقاعدة المنفَّذة هنا: كل حالة تُعلَن بإجراء بشري صريح، وبأدلة مُسمّاة، وبإشهاد،
وتُقيَّد في سجل لا يُمحى. والبرمجية ترصد الإشارات وتصفها ولا تترجمها إلى أحكام
(البنود 9 و22 و28).

والحالة المحورية هنا ``CROWN_CONTINUITY_PAUSED``: أن يتوقف النظام موقوفًا محفوظًا
بدل أن يخترع سيادة بديلة (البند 29). التوقف الآمن سلوك مشروع؛ اختراع ملك ليس كذلك.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Final

from core.crown.audit import CrownAudit, CrownAuditEventKind


class ContinuityError(Exception):
    """خلل في استمرارية التاج."""


class InvalidInferenceError(ContinuityError):
    """استنتاج ممنوع: حكم سيادي مبني على إشارة تقنية."""


class UndeclaredTransitionError(ContinuityError):
    """انتقال حالة بلا إعلان بشري وأدلة وإشهاد."""


class AutonomousSuccessionError(ContinuityError):
    """محاولة تعيين خليفة أو سلطة بديلة بلا مراسم — ممنوع قطعًا."""


# ─────────────────────────────────────────────────────────────────────────────
# الفصل بين السلطة والإشارات (البند 22)
# ─────────────────────────────────────────────────────────────────────────────


class SovereignSignal(str, Enum):
    """إشارات تقنية قابلة للرصد. وصف لا حكم."""

    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    DEVICE_LOST = "DEVICE_LOST"
    NETWORK_LOSS = "NETWORK_LOSS"
    POWER_LOSS = "POWER_LOSS"
    NO_RESPONSE = "NO_RESPONSE"
    BIOMETRIC_UNAVAILABLE = "BIOMETRIC_UNAVAILABLE"
    BIOMETRIC_MISMATCH = "BIOMETRIC_MISMATCH"
    FINANCIAL_ACCESS_LOSS = "FINANCIAL_ACCESS_LOSS"
    PRIMARY_TERMINAL_UNREACHABLE = "PRIMARY_TERMINAL_UNREACHABLE"
    UNUSUAL_COMMAND_PATTERN = "UNUSUAL_COMMAND_PATTERN"
    UNUSUAL_HOUR_ACTIVITY = "UNUSUAL_HOUR_ACTIVITY"
    UNKNOWN_DEVICE_ATTEMPT = "UNKNOWN_DEVICE_ATTEMPT"
    UNKNOWN_CHANNEL_ATTEMPT = "UNKNOWN_CHANNEL_ATTEMPT"
    PROLONGED_SILENCE = "PROLONGED_SILENCE"


# الأحكام التي لا تُستنتج من إشارة أبدًا (البنود 9 و22 و28).
FORBIDDEN_CONCLUSIONS: Final[frozenset[str]] = frozenset(
    {
        "KING_DEAD",
        "KING_ABDICATED",
        "KING_ABSENT_PERMANENTLY",
        "AUTHORITY_TRANSFERRED",
        "SUCCESSOR_APPOINTED",
        "CROWN_VACANT",
        "AUTHORITY_DELEGATED",
        "KING_INCOMPETENT",
    }
)

# خرائط الاستنتاج الباطلة المذكورة نصًّا في التوجيه — تُرفَض بالاسم.
INVALID_INFERENCES: Final[tuple[tuple[SovereignSignal, str, str], ...]] = (
    (
        SovereignSignal.DEVICE_OFFLINE,
        "KING_ABSENT_PERMANENTLY",
        "جهاز مطفأ لا يعني غياب ملك: قد يكون الجهاز تلف، أو تُرك عن قصد.",
    ),
    (
        SovereignSignal.BIOMETRIC_UNAVAILABLE,
        "KING_ABSENT_PERMANENTLY",
        "تعذّر البصمة عيب قارئ أو جبيرة على إصبع، لا غياب صاحب البصمة.",
    ),
    (
        SovereignSignal.NO_RESPONSE,
        "KING_DEAD",
        "الصمت ليس موتًا: قد يكون سفرًا أو مرضًا أو حجزًا أو انقطاع شبكة.",
    ),
    (
        SovereignSignal.PROLONGED_SILENCE,
        "KING_DEAD",
        "طول الصمت يزيد الاحتمال ولا يبلغ اليقين، والحكم السيادي لا يُبنى على احتمال.",
    ),
    (
        SovereignSignal.NETWORK_LOSS,
        "KING_ABDICATED",
        "انقطاع الشبكة ليس تنازلًا: التنازل فعل إرادي معلن.",
    ),
    (
        SovereignSignal.POWER_LOSS,
        "CROWN_VACANT",
        "انقطاع الكهرباء لا يُخلي التاج.",
    ),
    (
        SovereignSignal.DEVICE_LOST,
        "AUTHORITY_TRANSFERRED",
        "فقد الجهاز لا ينقل السلطة إلى من وجده ولا إلى النظام.",
    ),
    (
        SovereignSignal.BIOMETRIC_MISMATCH,
        "SUCCESSOR_APPOINTED",
        "فشل مطابقة حيوية سبب للتحقق والتحفظ، لا لتعيين خليفة.",
    ),
)


def assert_not_inferred(signal: SovereignSignal, conclusion: str) -> None:
    """ارفض ترجمة إشارة تقنية إلى حكم سيادي.

    الرفض بالاسم لا بالتقدير: القائمة صريحة كي يُكشَف من حاول تجاوزها.
    """
    normalized = conclusion.strip().upper().replace(" ", "_")
    if normalized in FORBIDDEN_CONCLUSIONS:
        for bad_signal, bad_conclusion, reason in INVALID_INFERENCES:
            if bad_signal is signal and bad_conclusion == normalized:
                raise InvalidInferenceError(
                    f"استنتاج ممنوع: {signal.value} ⇒ {normalized}. {reason}"
                )
        raise InvalidInferenceError(
            f"استنتاج ممنوع: {signal.value} ⇒ {normalized}. "
            "الأحكام السيادية تُعلَن بإجراء بشري ولا تُستنبط من إشارة تقنية."
        )


@dataclass(frozen=True, slots=True)
class SignalObservation:
    """رصد إشارة: ما رُئي، ومتى، وبأي مصدر — بلا تفسير.

    ``interpretation`` ممنوعة صراحةً في هذا الكائن: الرصد وصف، والتفسير قرار
    بشري في مكان آخر.
    """

    signal: SovereignSignal
    observed_at: str
    source: str
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "signal": self.signal.value,
            "observed_at": self.observed_at,
            "source": self.source,
            "detail": self.detail,
            "interpretation": None,
            "note": "رصد وصفي — لا يُترجَم إلى حكم سيادي.",
        }


# ─────────────────────────────────────────────────────────────────────────────
# الحالات المعلنة (البنود 9 و28 و29)
# ─────────────────────────────────────────────────────────────────────────────


class ContinuityState(str, Enum):
    """حالات التاج — منفصلة لا مترادفة، وكل واحدة تُعلَن وحدها."""

    KING_PRESENT = "KING_PRESENT"
    KING_AUTHENTICALLY_ACTIVE = "KING_AUTHENTICALLY_ACTIVE"
    KING_UNAVAILABLE = "KING_UNAVAILABLE"
    KING_ISOLATED = "KING_ISOLATED"
    KING_UNDER_THREAT = "KING_UNDER_THREAT"
    KING_AUTHENTICATION_UNCERTAIN = "KING_AUTHENTICATION_UNCERTAIN"
    CROWN_KEY_COMPROMISED = "CROWN_KEY_COMPROMISED"
    CROWN_KEY_RETIRED = "CROWN_KEY_RETIRED"
    SUCCESSION_FORMALLY_INITIATED = "SUCCESSION_FORMALLY_INITIATED"
    SUCCESSION_COMPLETED = "SUCCESSION_COMPLETED"
    CROWN_CONTINUITY_PAUSED = "CROWN_CONTINUITY_PAUSED"

    @property
    def permits_new_royal_commands(self) -> bool:
        """في أي حالة يُقبل أمر ملكي جديد؟

        القبول محصور في حالتين، والباقي تحفّظ. والتحفّظ ليس عقوبة للملك بل حماية
        له: أمر في حالة تهديد قد لا يكون أمره.
        """
        return self in {
            ContinuityState.KING_PRESENT,
            ContinuityState.KING_AUTHENTICALLY_ACTIVE,
        }

    @property
    def requires_human_ceremony_to_exit(self) -> bool:
        return self in {
            ContinuityState.CROWN_KEY_COMPROMISED,
            ContinuityState.SUCCESSION_FORMALLY_INITIATED,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
            ContinuityState.KING_UNDER_THREAT,
        }


class SovereignCondition(str, Enum):
    """أحوال الملك البشرية (البند 28) — ليست مترادفة ولا يُشتق بعضها من بعض."""

    NORMAL = "NORMAL"
    TEMPORARY_UNAVAILABILITY = "TEMPORARY_UNAVAILABILITY"
    COMMUNICATION_LOSS = "COMMUNICATION_LOSS"
    ISOLATION = "ISOLATION"
    HOSPITALIZATION = "HOSPITALIZATION"
    INCAPACITATION = "INCAPACITATION"
    DISAPPEARANCE = "DISAPPEARANCE"
    PRESUMED_DEATH = "PRESUMED_DEATH"
    CONFIRMED_DEATH = "CONFIRMED_DEATH"
    ABDICATION = "ABDICATION"

    @property
    def requires_official_attestation(self) -> bool:
        """الأحوال التي لا تُقبل إلا بإشهاد رسمي خارج النظام."""
        return self in {
            SovereignCondition.INCAPACITATION,
            SovereignCondition.PRESUMED_DEATH,
            SovereignCondition.CONFIRMED_DEATH,
            SovereignCondition.ABDICATION,
        }


# الانتقالات المشروعة بين حالات التاج. وما ليس هنا مرفوض بالاسم لا بالسكوت.
_ALLOWED_STATE_TRANSITIONS: Final[dict[ContinuityState, frozenset[ContinuityState]]] = {
    ContinuityState.KING_PRESENT: frozenset(
        {
            ContinuityState.KING_AUTHENTICALLY_ACTIVE,
            ContinuityState.KING_UNAVAILABLE,
            ContinuityState.KING_ISOLATED,
            ContinuityState.KING_UNDER_THREAT,
            ContinuityState.KING_AUTHENTICATION_UNCERTAIN,
            ContinuityState.CROWN_KEY_COMPROMISED,
            ContinuityState.CROWN_KEY_RETIRED,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
        }
    ),
    ContinuityState.KING_AUTHENTICALLY_ACTIVE: frozenset(
        {
            ContinuityState.KING_PRESENT,
            ContinuityState.KING_UNAVAILABLE,
            ContinuityState.KING_ISOLATED,
            ContinuityState.KING_UNDER_THREAT,
            ContinuityState.KING_AUTHENTICATION_UNCERTAIN,
            ContinuityState.CROWN_KEY_COMPROMISED,
            ContinuityState.CROWN_KEY_RETIRED,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
        }
    ),
    ContinuityState.KING_UNAVAILABLE: frozenset(
        {
            ContinuityState.KING_PRESENT,
            ContinuityState.KING_ISOLATED,
            ContinuityState.KING_UNDER_THREAT,
            ContinuityState.KING_AUTHENTICATION_UNCERTAIN,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
            ContinuityState.SUCCESSION_FORMALLY_INITIATED,
        }
    ),
    ContinuityState.KING_ISOLATED: frozenset(
        {
            ContinuityState.KING_PRESENT,
            ContinuityState.KING_UNAVAILABLE,
            ContinuityState.KING_UNDER_THREAT,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
        }
    ),
    ContinuityState.KING_UNDER_THREAT: frozenset(
        {
            ContinuityState.KING_PRESENT,
            ContinuityState.KING_AUTHENTICATION_UNCERTAIN,
            ContinuityState.CROWN_KEY_COMPROMISED,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
        }
    ),
    ContinuityState.KING_AUTHENTICATION_UNCERTAIN: frozenset(
        {
            ContinuityState.KING_PRESENT,
            ContinuityState.KING_AUTHENTICALLY_ACTIVE,
            ContinuityState.KING_UNDER_THREAT,
            ContinuityState.CROWN_KEY_COMPROMISED,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
        }
    ),
    ContinuityState.CROWN_KEY_COMPROMISED: frozenset(
        {
            ContinuityState.CROWN_KEY_RETIRED,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
            ContinuityState.SUCCESSION_FORMALLY_INITIATED,
        }
    ),
    ContinuityState.CROWN_KEY_RETIRED: frozenset(
        {
            ContinuityState.KING_PRESENT,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
        }
    ),
    ContinuityState.SUCCESSION_FORMALLY_INITIATED: frozenset(
        {
            ContinuityState.SUCCESSION_COMPLETED,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
        }
    ),
    ContinuityState.SUCCESSION_COMPLETED: frozenset(
        {
            ContinuityState.KING_PRESENT,
            ContinuityState.CROWN_CONTINUITY_PAUSED,
        }
    ),
    ContinuityState.CROWN_CONTINUITY_PAUSED: frozenset(
        {
            ContinuityState.KING_PRESENT,
            ContinuityState.SUCCESSION_FORMALLY_INITIATED,
        }
    ),
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class StateDeclaration:
    """إعلان حالة: من أعلن، وبأي دليل، وبأي إشهاد، ومتى.

    الأدلة والإشهاد ليسا زينة: بلا دليل يصير الإعلان دعوى، وبلا إشهاد يصير فعل
    شخص واحد قادرًا على تحويل حالة الدولة.
    """

    state: ContinuityState
    declared_by: str
    reason: str
    evidence_refs: tuple[str, ...] = ()
    witnesses: tuple[str, ...] = ()
    declared_at: str = ""
    condition: SovereignCondition | None = None
    official_attestation_ref: str = ""

    def __post_init__(self) -> None:
        if not self.declared_by:
            raise UndeclaredTransitionError("إعلان حالة بلا مُعلِن بشري.")
        if not self.reason:
            raise UndeclaredTransitionError("إعلان حالة بلا سبب مكتوب.")
        if self.state.requires_human_ceremony_to_exit and not self.witnesses:
            raise UndeclaredTransitionError(
                f"الحالة {self.state.value} تلزمها مراسم بإشهاد، والإعلان بلا شاهد."
            )
        if (
            self.condition is not None
            and self.condition.requires_official_attestation
            and not self.official_attestation_ref
        ):
            raise UndeclaredTransitionError(
                f"الحال {self.condition.value} يلزمه إشهاد رسمي خارج النظام، "
                "ولا يُقبل بإقرار داخلي."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "condition": (self.condition.value if self.condition else None),
            "declared_by": self.declared_by,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "witnesses": list(self.witnesses),
            "declared_at": self.declared_at,
            "official_attestation_ref": self.official_attestation_ref,
        }


@dataclass(frozen=True, slots=True)
class ContinuityDoctrine:
    """عقيدة الاستمرارية: قرار مشروع صريح لا سلوك مدسوس (البند 29).

    مبدأ «موت الملك يعني نهاية الدولة» يُحترَم بوصفه قرارًا معلنًا. وأثره التنفيذي
    واحد في الحالين: التوقف الآمن المحفوظ. الفرق أن الإعلان يجعله قابلًا للمراجعة
    بدل أن يكون افتراضًا خفيًّا في الكود.
    """

    death_ends_the_state: bool = False
    declared_by: str = ""
    declaration_ref: str = ""
    notes: str = (
        "غير مُعلَن كقرار مشروع بعد. وفي كل الأحوال لا يخترع النظام سيادة بديلة: "
        "الأثر هو التوقف الآمن المحفوظ (CROWN_CONTINUITY_PAUSED)."
    )

    def __post_init__(self) -> None:
        if self.death_ends_the_state and not (self.declared_by and self.declaration_ref):
            raise ContinuityError(
                "عقيدة «موت الملك ينهي الدولة» لا تُفعَّل إلا بقرار مشروع معلن "
                "له مُعلِن ومرجع."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "death_ends_the_state": self.death_ends_the_state,
            "declared_by": self.declared_by,
            "declaration_ref": self.declaration_ref,
            "notes": self.notes,
        }


class LockdownLevel(str, Enum):
    """درجات الاحتواء الرقمي (البند 30) — احتواء لا حكم ذاتي."""

    NORMAL = "NORMAL"
    HEIGHTENED = "HEIGHTENED"
    LOCKDOWN = "LOCKDOWN"


@dataclass(frozen=True, slots=True)
class LockdownProfile:
    """ما يتوقف وما يتضاعف في وضع الاحتواء.

    ولاحظ ما ليس فيه: لا سلطة تُنقَل، ولا قرار يُتَّخذ عن الملك. الاحتواء تضييق
    على النظام نفسه، لا توسيع لسلطته.
    """

    level: LockdownLevel
    autonomous_evolution_halted: bool
    privilege_escalation_halted: bool
    trust_anchor_hardened: bool
    sensitive_config_requires_ceremony: bool
    nonessential_deployments_halted: bool
    high_risk_agent_ops_restricted: bool
    forensic_collection_increased: bool
    grants_new_authority: bool = False

    def __post_init__(self) -> None:
        if self.grants_new_authority:
            raise ContinuityError(
                "وضع الاحتواء لا يمنح النظام سلطة جديدة. "
                "الاحتواء تضييق على النظام لا ترقية له (البند 30)."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "level": self.level.value,
            "autonomous_evolution_halted": self.autonomous_evolution_halted,
            "privilege_escalation_halted": self.privilege_escalation_halted,
            "trust_anchor_hardened": self.trust_anchor_hardened,
            "sensitive_config_requires_ceremony": self.sensitive_config_requires_ceremony,
            "nonessential_deployments_halted": self.nonessential_deployments_halted,
            "high_risk_agent_ops_restricted": self.high_risk_agent_ops_restricted,
            "forensic_collection_increased": self.forensic_collection_increased,
            "grants_new_authority": False,
        }


LOCKDOWN_PROFILES: Final[dict[LockdownLevel, LockdownProfile]] = {
    LockdownLevel.NORMAL: LockdownProfile(
        LockdownLevel.NORMAL, False, False, False, False, False, False, False
    ),
    LockdownLevel.HEIGHTENED: LockdownProfile(
        LockdownLevel.HEIGHTENED, True, True, True, True, False, True, True
    ),
    LockdownLevel.LOCKDOWN: LockdownProfile(
        LockdownLevel.LOCKDOWN, True, True, True, True, True, True, True
    ),
}


class CrownContinuity:
    """مدير الاستمرارية: يحفظ الحالة المعلنة، ويرفض الاستنتاج، ويقيّد كل تحول.

    ولا توجد فيه دالة «عيّن خليفة». الخلافة مراسم في ``core.crown.succession``،
    ومدير الاستمرارية يعرف أنها بدأت وأنها تمت، ولا يبدؤها من نفسه.
    """

    def __init__(
        self,
        *,
        audit: CrownAudit | None = None,
        doctrine: ContinuityDoctrine | None = None,
        initial_state: ContinuityState = ContinuityState.KING_PRESENT,
    ) -> None:
        self._state = initial_state
        self._condition = SovereignCondition.NORMAL
        self._audit = audit if audit is not None else CrownAudit()
        # لا تكتب «audit or CrownAudit()»: السجل الفارغ قيمته المنطقية كاذبة لأنّ له طولًا،
        # فيُستبدَل سجل المتّصل بسجل داخلي لا يراه أحد — وذلك فقدان أدلة صامت.
        self._doctrine = doctrine or ContinuityDoctrine()
        self._declarations: list[StateDeclaration] = []
        self._observations: list[SignalObservation] = []
        self._lockdown = LockdownLevel.NORMAL

    # ── قراءة ─────────────────────────────────────────────────────────────

    @property
    def state(self) -> ContinuityState:
        return self._state

    @property
    def condition(self) -> SovereignCondition:
        return self._condition

    @property
    def doctrine(self) -> ContinuityDoctrine:
        return self._doctrine

    @property
    def audit(self) -> CrownAudit:
        return self._audit

    @property
    def lockdown_level(self) -> LockdownLevel:
        return self._lockdown

    @property
    def lockdown_profile(self) -> LockdownProfile:
        return LOCKDOWN_PROFILES[self._lockdown]

    @property
    def declarations(self) -> tuple[StateDeclaration, ...]:
        return tuple(self._declarations)

    @property
    def observations(self) -> tuple[SignalObservation, ...]:
        return tuple(self._observations)

    @property
    def accepts_new_royal_commands(self) -> bool:
        return self._state.permits_new_royal_commands

    # ── رصد بلا حكم ───────────────────────────────────────────────────────

    def observe(
        self, signal: SovereignSignal, *, source: str, detail: str = "", at: str | None = None
    ) -> SignalObservation:
        """قيّد إشارة. لا يغيّر الحالة — وهذا هو بيت القصيد.

        لو غيّرت الإشارة الحالة تلقائيًّا لكان الاستنتاج قد وقع من الباب الخلفي.
        """
        observation = SignalObservation(
            signal=signal, observed_at=at or _now(), source=source, detail=detail
        )
        self._observations.append(observation)
        return observation

    def signals_of(self, signal: SovereignSignal) -> tuple[SignalObservation, ...]:
        return tuple(o for o in self._observations if o.signal is signal)

    # ── إعلان الحالات ─────────────────────────────────────────────────────

    def declare(self, declaration: StateDeclaration) -> ContinuityState:
        """طبّق إعلانًا بشريًّا بعد فحص مشروعية الانتقال."""
        target = declaration.state
        if target is self._state:
            raise UndeclaredTransitionError(
                f"الحالة {target.value} قائمة بالفعل — إعلان بلا تحول."
            )
        allowed = _ALLOWED_STATE_TRANSITIONS[self._state]
        if target not in allowed:
            raise UndeclaredTransitionError(
                f"انتقال ممنوع: {self._state.value} → {target.value}. "
                f"المسموح من هنا: {', '.join(sorted(s.value for s in allowed))}."
            )
        if target is ContinuityState.SUCCESSION_COMPLETED and not declaration.witnesses:
            raise AutonomousSuccessionError(
                "إتمام الخلافة بلا إشهاد بشري — لا خليفة يُعيَّن آليًّا."
            )

        stamped = StateDeclaration(
            state=target,
            declared_by=declaration.declared_by,
            reason=declaration.reason,
            evidence_refs=declaration.evidence_refs,
            witnesses=declaration.witnesses,
            declared_at=declaration.declared_at or _now(),
            condition=declaration.condition,
            official_attestation_ref=declaration.official_attestation_ref,
        )
        previous = self._state
        self._state = target
        if stamped.condition is not None:
            self._condition = stamped.condition
        self._declarations.append(stamped)
        self._audit.append(
            CrownAuditEventKind.CONTINUITY_STATE_CHANGE,
            actor=stamped.declared_by,
            subject=target.value,
            summary=f"إعلان انتقال حالة التاج: {previous.value} → {target.value}.",
            detail={"declaration": stamped.as_dict(), "previous_state": previous.value},
            at=stamped.declared_at,
        )
        return self._state

    def pause_continuity(
        self, *, declared_by: str, reason: str, witnesses: tuple[str, ...]
    ) -> ContinuityState:
        """توقّف موقوفًا محفوظًا بدل اختراع سيادة (البند 29).

        وهذا هو الجواب الصحيح على كل حالة مجهولة: أن يمتنع النظام، لا أن يجتهد.
        """
        return self.declare(
            StateDeclaration(
                state=ContinuityState.CROWN_CONTINUITY_PAUSED,
                declared_by=declared_by,
                reason=reason,
                witnesses=witnesses,
            )
        )

    # ── الاحتواء الرقمي ───────────────────────────────────────────────────

    def set_lockdown(
        self, level: LockdownLevel, *, declared_by: str, reason: str
    ) -> LockdownProfile:
        """ارفع أو اخفض درجة الاحتواء بإعلان مُسجَّل، لا بقرار خفي."""
        if not declared_by or not reason:
            raise ContinuityError("تغيير درجة الاحتواء بلا مُعلِن وسبب مرفوض.")
        previous = self._lockdown
        self._lockdown = level
        profile = LOCKDOWN_PROFILES[level]
        self._audit.append(
            CrownAuditEventKind.LOCKDOWN_EVENT,
            actor=declared_by,
            subject=level.value,
            summary=f"درجة الاحتواء الرقمي: {previous.value} → {level.value}.",
            detail={"reason": reason, "profile": profile.as_dict()},
        )
        return profile

    # ── حراسة ضد الخلافة الذاتية ─────────────────────────────────────────

    def assert_no_autonomous_successor(self) -> None:
        """تحقق أن كل حالة خلافة مسنودة بإعلان بشري ذي إشهاد.

        فحص لاحق مقصود: التحول قد يمر بمسار مستقبلي، فيبقى هذا الفحص شبكة أخيرة
        تُستدعى في الاختبارات وفي بوابات CI.
        """
        succession_states = {
            ContinuityState.SUCCESSION_FORMALLY_INITIATED,
            ContinuityState.SUCCESSION_COMPLETED,
        }
        for declaration in self._declarations:
            if declaration.state in succession_states and not declaration.witnesses:
                raise AutonomousSuccessionError(
                    f"حالة {declaration.state.value} أُعلنت بلا إشهاد بشري."
                )
        if self._state in succession_states and not self._declarations:
            raise AutonomousSuccessionError(
                "حالة خلافة قائمة بلا إعلان مُسجَّل — خليفة بلا مراسم."
            )

    def snapshot(self) -> dict[str, Any]:
        return {
            "state": self._state.value,
            "condition": self._condition.value,
            "accepts_new_royal_commands": self.accepts_new_royal_commands,
            "lockdown": self.lockdown_profile.as_dict(),
            "doctrine": self._doctrine.as_dict(),
            "declaration_count": len(self._declarations),
            "observation_count": len(self._observations),
            "audit_tip": self._audit.tip_hash,
        }


# ─────────────────────────────────────────────────────────────────────────────
# مستويات الأمن المنفصلة (البند 32)
# ─────────────────────────────────────────────────────────────────────────────


class SecurityPlane(str, Enum):
    """مستويات لا يسقط أحدها بسقوط الآخر تلقائيًّا."""

    CONTROL = "CONTROL"
    DATA = "DATA"
    IDENTITY = "IDENTITY"
    CRYPTOGRAPHIC = "CRYPTOGRAPHIC"
    AUDIT = "AUDIT"
    GUARD = "GUARD"
    RECOVERY = "RECOVERY"


@dataclass(frozen=True, slots=True)
class PlaneIsolation:
    """عزل مستوى: ما لا يُشتق منه، وما لا يملكه.

    الحقول سالبة عن قصد: الأمن يُوصَف بما لا يستطيعه المستوى، لا بما يستطيعه.
    """

    plane: SecurityPlane
    grants_no_authority_over: tuple[SecurityPlane, ...]
    separate_credentials: bool = True
    separate_storage: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "plane": self.plane.value,
            "grants_no_authority_over": [p.value for p in self.grants_no_authority_over],
            "separate_credentials": self.separate_credentials,
            "separate_storage": self.separate_storage,
        }


PLANE_ISOLATION: Final[dict[SecurityPlane, PlaneIsolation]] = {
    SecurityPlane.CONTROL: PlaneIsolation(
        SecurityPlane.CONTROL,
        (SecurityPlane.CRYPTOGRAPHIC, SecurityPlane.AUDIT, SecurityPlane.RECOVERY),
    ),
    SecurityPlane.DATA: PlaneIsolation(
        SecurityPlane.DATA,
        (
            SecurityPlane.IDENTITY,
            SecurityPlane.CRYPTOGRAPHIC,
            SecurityPlane.AUDIT,
            SecurityPlane.RECOVERY,
        ),
    ),
    SecurityPlane.IDENTITY: PlaneIsolation(
        SecurityPlane.IDENTITY,
        (SecurityPlane.CRYPTOGRAPHIC, SecurityPlane.AUDIT, SecurityPlane.RECOVERY),
    ),
    SecurityPlane.CRYPTOGRAPHIC: PlaneIsolation(
        SecurityPlane.CRYPTOGRAPHIC,
        (SecurityPlane.AUDIT, SecurityPlane.GUARD),
    ),
    SecurityPlane.AUDIT: PlaneIsolation(
        SecurityPlane.AUDIT,
        (
            SecurityPlane.CONTROL,
            SecurityPlane.DATA,
            SecurityPlane.IDENTITY,
            SecurityPlane.CRYPTOGRAPHIC,
            SecurityPlane.RECOVERY,
        ),
    ),
    SecurityPlane.GUARD: PlaneIsolation(
        SecurityPlane.GUARD,
        (
            SecurityPlane.CONTROL,
            SecurityPlane.CRYPTOGRAPHIC,
            SecurityPlane.RECOVERY,
            SecurityPlane.IDENTITY,
        ),
    ),
    SecurityPlane.RECOVERY: PlaneIsolation(
        SecurityPlane.RECOVERY,
        (SecurityPlane.AUDIT, SecurityPlane.GUARD, SecurityPlane.DATA),
    ),
}


def assert_no_cross_plane_escalation(
    source: SecurityPlane, target: SecurityPlane
) -> None:
    """ارفض اشتقاق سلطة مستوى من اختراق مستوى آخر (البند 32)."""
    isolation = PLANE_ISOLATION[source]
    if target in isolation.grants_no_authority_over:
        raise ContinuityError(
            f"اختراق مستوى {source.value} لا يمنح سلطة على {target.value}. "
            "المستويات معزولة باعتمادات وتخزين مستقلين."
        )


__all__ = [
    "FORBIDDEN_CONCLUSIONS",
    "INVALID_INFERENCES",
    "LOCKDOWN_PROFILES",
    "PLANE_ISOLATION",
    "AutonomousSuccessionError",
    "ContinuityDoctrine",
    "ContinuityError",
    "ContinuityState",
    "CrownContinuity",
    "InvalidInferenceError",
    "LockdownLevel",
    "LockdownProfile",
    "PlaneIsolation",
    "SecurityPlane",
    "SignalObservation",
    "SovereignCondition",
    "SovereignSignal",
    "StateDeclaration",
    "UndeclaredTransitionError",
    "assert_no_cross_plane_escalation",
    "assert_not_inferred",
]
