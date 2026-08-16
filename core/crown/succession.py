"""الهدف: مراسم خلافة رسمية بنسب محفوظ — لا خليفة بغياب، ولا وكيل يصير ملكًا.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

البند 27 يمنع ثلاث جمل بعينها:

    «لا رد من الملك ⇒ عيّن خليفة»
    «حساب الملك غير متاح ⇒ الوكيل يصير ملكًا»
    «نظام الأمن يقرر من هو الملك»

وكل واحدة منها مرفوضة هنا بفحص تنفيذي لا بتعليق. والبديل: مراسم تمر بمراحل
معلنة، لا تُطوى مرحلة منها، ويشترك فيها شهود بشريون، وتُقيَّد في سجل لا يُمحى،
ويبقى نسب المفاتيح متصلًا من التأسيس إلى الخلف.

وفرق جوهري بين التدوير والخلافة (البند 26 مقابل 27): التدوير يغيّر المفتاح
والحامل واحد؛ والخلافة تغيّر الحامل. فمن نفّذ الخلافة كأنها تدوير أخفى أخطر
حدث في حياة الدولة داخل عملية صيانة روتينية.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Final

from core.crown.audit import CrownAudit, CrownAuditEventKind
from core.crown.key_registry import (
    CrownKeyRegistry,
    KeyProvenance,
    LineageKind,
)


class SuccessionError(Exception):
    """خلل في مراسم الخلافة."""


class SuccessionAuthorityError(SuccessionError):
    """جهة غير مؤهلة تحاول تقرير الخلافة."""


class SuccessionStageError(SuccessionError):
    """طيّ مرحلة من مراسم الخلافة أو إعادتها."""


# جهات لا تملك تقرير الخلافة بحال — أسماء لا أوصاف، ليُكشَف من حاول.
FORBIDDEN_SUCCESSION_DECIDERS: Final[frozenset[str]] = frozenset(
    {
        "system",
        "guard",
        "sovereign_guard",
        "security_subsystem",
        "agent",
        "ai",
        "ai_king",
        "emergency_king",
        "guardian_king",
        "shadow_crown",
        "automation",
        "scheduler",
        "watchdog",
        "monitor",
        "gateway",
    }
)

# مبررات مرفوضة: كلها إشارات تقنية أُريد لها أن تصير قرارًا سياديًّا.
FORBIDDEN_SUCCESSION_TRIGGERS: Final[frozenset[str]] = frozenset(
    {
        "no_response",
        "timeout",
        "inactivity",
        "device_offline",
        "account_unavailable",
        "biometric_failure",
        "network_loss",
        "silence",
        "heartbeat_missing",
    }
)


class SuccessionStage(str, Enum):
    """مراحل المراسم — بالترتيب، ولا تُطوى واحدة."""

    NOT_STARTED = "NOT_STARTED"
    FORMALLY_INITIATED = "FORMALLY_INITIATED"
    ELIGIBILITY_ESTABLISHED = "ELIGIBILITY_ESTABLISHED"
    WITNESSES_CONFIRMED = "WITNESSES_CONFIRMED"
    SUCCESSOR_KEY_GENERATED = "SUCCESSOR_KEY_GENERATED"
    TRUST_ANCHOR_UPDATED = "TRUST_ANCHOR_UPDATED"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


_STAGE_ORDER: Final[tuple[SuccessionStage, ...]] = (
    SuccessionStage.NOT_STARTED,
    SuccessionStage.FORMALLY_INITIATED,
    SuccessionStage.ELIGIBILITY_ESTABLISHED,
    SuccessionStage.WITNESSES_CONFIRMED,
    SuccessionStage.SUCCESSOR_KEY_GENERATED,
    SuccessionStage.TRUST_ANCHOR_UPDATED,
    SuccessionStage.COMPLETED,
)

MINIMUM_WITNESSES: Final[int] = 3


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def assert_eligible_decider(decider: str) -> None:
    """ارفض أن يقرر الخلافة نظامٌ أو حارسٌ أو وكيل."""
    normalized = decider.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in FORBIDDEN_SUCCESSION_DECIDERS:
        raise SuccessionAuthorityError(
            f"«{decider}» لا يملك تقرير الخلافة بحال. "
            "نظام الأمن يحرس التاج ولا يقرر من هو الملك (البند 27)، "
            "والحارس يحمي ولا يصير محميًّا عليه سلطانه (البند 39)."
        )


def assert_valid_trigger(trigger: str) -> None:
    """ارفض مبررًا تقنيًّا لبدء الخلافة."""
    normalized = trigger.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in FORBIDDEN_SUCCESSION_TRIGGERS:
        raise SuccessionError(
            f"«{trigger}» إشارة تقنية لا تُبدئ خلافة. "
            "الخلافة تبدأ بإجراء بشري رسمي معلن بأدلة وإشهاد."
        )


@dataclass(frozen=True, slots=True)
class SuccessionWitness:
    """شاهد على المراسم: هويته، وصفته، ومرجع تحققه، ومتى شهد."""

    witness_id: str
    role: str
    verification_ref: str
    confirmed_at: str = ""

    def __post_init__(self) -> None:
        if not self.witness_id or not self.role:
            raise SuccessionError("شاهد بلا هوية أو بلا صفة.")
        if not self.verification_ref:
            raise SuccessionError(
                f"الشاهد «{self.witness_id}» بلا مرجع تحقق — شهادة غير قابلة للمراجعة."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "witness_id": self.witness_id,
            "role": self.role,
            "verification_ref": self.verification_ref,
            "confirmed_at": self.confirmed_at,
        }


@dataclass(frozen=True, slots=True)
class SuccessionMandate:
    """سند الخلافة: من قررها، وبأي مستند، وبأي حال معلن، ومن الخلف.

    ``legal_basis_ref`` مرجع مستند خارج النظام. وبغيره تصير الخلافة قرارًا
    برمجيًّا، وهو المحظور عينه.
    """

    mandate_id: str
    decided_by: str
    legal_basis_ref: str
    trigger: str
    predecessor_subject_ref: str
    successor_subject_ref: str
    declared_at: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.mandate_id:
            raise SuccessionError("سند خلافة بلا معرّف.")
        assert_eligible_decider(self.decided_by)
        assert_valid_trigger(self.trigger)
        if not self.legal_basis_ref:
            raise SuccessionError(
                "سند خلافة بلا مرجع نظامي خارج النظام — خلافة بقرار برمجي."
            )
        if not self.successor_subject_ref:
            raise SuccessionError("سند خلافة بلا خلف مُسمّى.")
        if self.successor_subject_ref == self.predecessor_subject_ref:
            raise SuccessionError("الخلف هو السابق نفسه — ليست خلافة.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "mandate_id": self.mandate_id,
            "decided_by": self.decided_by,
            "legal_basis_ref": self.legal_basis_ref,
            "trigger": self.trigger,
            "predecessor_subject_ref": self.predecessor_subject_ref,
            "successor_subject_ref": self.successor_subject_ref,
            "declared_at": self.declared_at,
            "notes": self.notes,
        }


@dataclass(slots=True)
class SuccessionCeremony:
    """مراسم واحدة بمراحلها وشهودها وأثرها في نسب المفاتيح."""

    mandate: SuccessionMandate
    stage: SuccessionStage = SuccessionStage.NOT_STARTED
    witnesses: list[SuccessionWitness] = field(default_factory=list)
    successor_key_id: str = ""
    anchor_update_ref: str = ""
    aborted_reason: str = ""
    stage_log: list[tuple[str, str]] = field(default_factory=list)

    def _assert_can_advance(self, target: SuccessionStage) -> None:
        """افحص شرعية الانتقال بلا تنفيذه — كي يُفحَص قبل أي أثر جانبي."""
        if self.stage is SuccessionStage.ABORTED:
            raise SuccessionStageError("مراسم مُلغاة لا تُستأنف — تُبدأ مراسم جديدة.")
        try:
            current_index = _STAGE_ORDER.index(self.stage)
            target_index = _STAGE_ORDER.index(target)
        except ValueError as exc:
            raise SuccessionStageError(f"مرحلة غير معروفة: {exc}") from exc
        if target_index != current_index + 1:
            raise SuccessionStageError(
                f"طيّ مرحلة: {self.stage.value} → {target.value}. "
                "المراسم تمر بمراحلها بالترتيب، وطيّ مرحلة إخفاء لخطوة رقابية."
            )

    def _advance(self, target: SuccessionStage) -> None:
        if self.stage is SuccessionStage.ABORTED:
            raise SuccessionStageError("مراسم مُلغاة لا تُستأنف — تُبدأ مراسم جديدة.")
        try:
            current_index = _STAGE_ORDER.index(self.stage)
            target_index = _STAGE_ORDER.index(target)
        except ValueError as exc:
            raise SuccessionStageError(f"مرحلة غير معروفة: {exc}") from exc
        if target_index != current_index + 1:
            raise SuccessionStageError(
                f"طيّ مرحلة: {self.stage.value} → {target.value}. "
                "المراسم تمر بمراحلها بالترتيب، وطيّ مرحلة إخفاء لخطوة رقابية."
            )
        self.stage = target
        self.stage_log.append((target.value, _now()))

    def initiate(self) -> None:
        self._advance(SuccessionStage.FORMALLY_INITIATED)

    def establish_eligibility(self, *, eligibility_ref: str) -> None:
        if not eligibility_ref:
            raise SuccessionError("إثبات أهلية الخلف بلا مرجع.")
        self._advance(SuccessionStage.ELIGIBILITY_ESTABLISHED)

    def confirm_witnesses(self, witnesses: tuple[SuccessionWitness, ...]) -> None:
        """اشترط عددًا أدنى من الشهود المستقلين.

        العدد الأدنى ليس رقمًا اعتباطيًّا: شاهد واحد يجعل الخلافة رهن شخص، وشاهدان
        يجعلانها رهن اتفاق ثنائي. والثلاثة أدنى ما يُصعِّب التواطؤ الصامت.
        """
        unique = {w.witness_id for w in witnesses}
        if len(unique) < MINIMUM_WITNESSES:
            raise SuccessionError(
                f"الشهود المستقلون {len(unique)} والحد الأدنى {MINIMUM_WITNESSES}."
            )
        if self.mandate.decided_by in unique:
            raise SuccessionError(
                "مقرِّر الخلافة لا يكون شاهدًا على قراره — الشهادة تستلزم استقلالًا."
            )
        self.witnesses = list(witnesses)
        self._advance(SuccessionStage.WITNESSES_CONFIRMED)

    def register_successor_key(
        self,
        registry: CrownKeyRegistry,
        *,
        new_key_id: str,
        algorithm: str,
        public_key_hex: str,
        keystore_kind: str,
        attestation_ref: str = "",
        predecessor_key_id: str | None = None,
    ) -> None:
        """سجّل مفتاح الخلف بنوع نسب SUCCESSION — لا ROTATION.

        التمييز مقصود: قارئ السجل بعد سنين يجب أن يعرف من النسب وحده أن الحامل
        قد تغيّر، لا أن يظن أنها صيانة مفاتيح.
        """
        # الترتيب مقصود: تُفحَص المرحلة والإشهاد **قبل** أي تعديل على السجل. ولو
        # فُحصت بعده لكانت مراسم ناقصة قد بدّلت المفتاح النشط فعلًا ثم اعترضت،
        # وهذا بابٌ لخلافة غير مصرَّح بها تُنفَّذ ثم تُشتكى.
        self._assert_can_advance(SuccessionStage.SUCCESSOR_KEY_GENERATED)
        if len({w.witness_id for w in self.witnesses}) < MINIMUM_WITNESSES:
            raise SuccessionError(
                "تسجيل مفتاح الخلف قبل استيفاء الإشهاد المستقل مرفوض."
            )
        provenance = KeyProvenance(
            ceremony_id=self.mandate.mandate_id,
            ceremony_kind="CROWN_SUCCESSION",
            keystore_kind=keystore_kind,
            attestation_ref=attestation_ref,
            witnesses=tuple(w.witness_id for w in self.witnesses),
            out_of_band_verified=True,
            notes=(
                f"خلافة رسمية من «{self.mandate.predecessor_subject_ref}» "
                f"إلى «{self.mandate.successor_subject_ref}»."
            ),
        )
        registry.rotate(
            new_key_id=new_key_id,
            algorithm=algorithm,
            public_key_hex=public_key_hex,
            provenance=provenance,
            lineage_kind=LineageKind.SUCCESSION,
            predecessor_key_id=predecessor_key_id,
        )
        self.successor_key_id = new_key_id
        self._advance(SuccessionStage.SUCCESSOR_KEY_GENERATED)

    def update_trust_anchor(self, *, anchor_update_ref: str) -> None:
        if not anchor_update_ref:
            raise SuccessionError("تحديث مرساة الثقة بلا مرجع مراسم.")
        self.anchor_update_ref = anchor_update_ref
        self._advance(SuccessionStage.TRUST_ANCHOR_UPDATED)

    def complete(self) -> None:
        if not self.successor_key_id:
            raise SuccessionStageError("إتمام خلافة بلا مفتاح خلف مسجَّل.")
        if len({w.witness_id for w in self.witnesses}) < MINIMUM_WITNESSES:
            raise SuccessionStageError("إتمام خلافة بشهود أقل من الحد الأدنى.")
        self._advance(SuccessionStage.COMPLETED)

    def abort(self, *, reason: str) -> None:
        if not reason:
            raise SuccessionError("إلغاء مراسم بلا سبب مكتوب.")
        self.aborted_reason = reason
        self.stage = SuccessionStage.ABORTED
        self.stage_log.append((SuccessionStage.ABORTED.value, _now()))

    def as_dict(self) -> dict[str, Any]:
        return {
            "mandate": self.mandate.as_dict(),
            "stage": self.stage.value,
            "witnesses": [w.as_dict() for w in self.witnesses],
            "successor_key_id": self.successor_key_id,
            "anchor_update_ref": self.anchor_update_ref,
            "aborted_reason": self.aborted_reason,
            "stage_log": [{"stage": s, "at": t} for s, t in self.stage_log],
        }


class CrownSuccession:
    """منسّق مراسم الخلافة: مراسم واحدة في الوقت، وكل خطوة مُقيَّدة في السجل.

    «واحدة في الوقت» شرط أمني: مراسم متزامنة تُنتج مفتاحين خلفين، وهو تاج موازٍ
    بصورة إجراء نظامي.
    """

    def __init__(self, *, audit: CrownAudit | None = None) -> None:
        self._audit = audit if audit is not None else CrownAudit()
        # لا تكتب «audit or CrownAudit()»: السجل الفارغ قيمته المنطقية كاذبة لأنّ له طولًا،
        # فيُستبدَل سجل المتّصل بسجل داخلي لا يراه أحد — وذلك فقدان أدلة صامت.
        self._active: SuccessionCeremony | None = None
        self._history: list[SuccessionCeremony] = []

    @property
    def audit(self) -> CrownAudit:
        return self._audit

    @property
    def active_ceremony(self) -> SuccessionCeremony | None:
        return self._active

    @property
    def history(self) -> tuple[SuccessionCeremony, ...]:
        return tuple(self._history)

    def open_ceremony(self, mandate: SuccessionMandate) -> SuccessionCeremony:
        if self._active is not None and self._active.stage not in {
            SuccessionStage.COMPLETED,
            SuccessionStage.ABORTED,
        }:
            raise SuccessionError(
                f"مراسم خلافة قائمة («{self._active.mandate.mandate_id}») في المرحلة "
                f"{self._active.stage.value}. مراسم متزامنة تُنتج تاجًا موازيًا."
            )
        ceremony = SuccessionCeremony(mandate=mandate)
        ceremony.initiate()
        self._active = ceremony
        self._history.append(ceremony)
        self._audit.append(
            CrownAuditEventKind.SUCCESSION_EVENT,
            actor=mandate.decided_by,
            subject=mandate.mandate_id,
            summary="بدء مراسم خلافة رسمية.",
            detail=mandate.as_dict(),
        )
        return ceremony

    def record_stage(self, ceremony: SuccessionCeremony, *, actor: str) -> None:
        """قيّد المرحلة الحالية في سجل التاج — فلا مرحلة تمر بلا أثر."""
        self._audit.append(
            CrownAuditEventKind.SUCCESSION_EVENT,
            actor=actor,
            subject=ceremony.mandate.mandate_id,
            summary=f"مراسم الخلافة بلغت المرحلة {ceremony.stage.value}.",
            detail=ceremony.as_dict(),
        )

    def lineage_report(self, registry: CrownKeyRegistry) -> dict[str, Any]:
        """تقرير النسب الكامل: كل مفتاح بسببه وسابقه — للمراجعة البشرية."""
        return {
            "keys": [
                {
                    "key_id": r.key_id,
                    "version": r.version,
                    "state": r.state.value,
                    "lineage_kind": r.lineage_kind.value,
                    "predecessor": r.predecessor_key_id,
                    "ceremony_id": r.provenance.ceremony_id,
                    "witnesses": list(r.provenance.witnesses),
                }
                for r in registry.lineage()
            ],
            "succession_count": sum(
                1
                for r in registry.lineage()
                if r.lineage_kind is LineageKind.SUCCESSION
            ),
            "rotation_count": sum(
                1 for r in registry.lineage() if r.lineage_kind is LineageKind.ROTATION
            ),
        }


__all__ = [
    "FORBIDDEN_SUCCESSION_DECIDERS",
    "FORBIDDEN_SUCCESSION_TRIGGERS",
    "MINIMUM_WITNESSES",
    "CrownSuccession",
    "SuccessionAuthorityError",
    "SuccessionCeremony",
    "SuccessionError",
    "SuccessionMandate",
    "SuccessionStage",
    "SuccessionStageError",
    "SuccessionWitness",
    "assert_eligible_decider",
    "assert_valid_trigger",
]
