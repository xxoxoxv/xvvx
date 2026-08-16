"""الهدف: استرداد التاج بمراسم خارج الشبكة بإشهاد متعدد — بلا كلمة طوارئ سرية.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

البند 33 يطلب قدرة استرداد خارج الشبكة، وينهى في الوقت نفسه عن شيئين: تخزين
مادة إنتاجية في المستودع، وتنفيذ «كلمة مرور طوارئ سرية». والثاني أخطر من ظاهره:
كلمة سرية واحدة تُختصر بها كل الحمايات هي بعينها الباب الخلفي الذي بُنيت كل هذه
الطبقات لمنعه. من عرفها صار ملكًا.

فالبديل المنفَّذ هنا: **حصص مقسومة على حاملين مستقلين** (m من n)، بمواضع مادية
متعددة، ومواد تحقق مطبوعة أو في تخزين بارد، ومراسم لها مراحل وشهود وسجل. ولا
تكفي أغلبية واحدة في مكان واحد: يُشترط تعدد المواضع كي لا يكفي اقتحام غرفة واحدة.

وما في هذا الملف **أوصاف ومراجع وبروتوكول**، لا حصص ولا مواد. الحصة تبقى في
حرزها المادي، والمستودع يعرف أنها موجودة وأين توصيفها ولا يعرف قيمتها.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Final

from core.crown.audit import CrownAudit, CrownAuditEventKind


class RecoveryError(Exception):
    """خلل في مراسم استرداد التاج."""


class EmergencyBackdoorError(RecoveryError):
    """محاولة إنشاء كلمة طوارئ أو باب خلفي للاسترداد — ممنوع قطعًا."""


class QuorumError(RecoveryError):
    """نصاب الحاملين غير مستوفى أو غير مستقل."""


class RecoveryStageError(RecoveryError):
    """طيّ مرحلة من مراسم الاسترداد."""


# أسماء الأبواب الخلفية المعتادة — تُرفَض بالاسم كي يُكشَف من حاول إدخالها.
FORBIDDEN_RECOVERY_MECHANISMS: Final[frozenset[str]] = frozenset(
    {
        "emergency_password",
        "master_password",
        "break_glass_secret",
        "recovery_phrase_in_repository",
        "hardcoded_override",
        "vendor_backdoor",
        "support_bypass",
        "single_admin_reset",
        "sms_reset",
        "email_reset",
        "security_question",
    }
)

MINIMUM_QUORUM: Final[int] = 3
MINIMUM_SHARE_HOLDERS: Final[int] = 5
MINIMUM_DISTINCT_LOCATIONS: Final[int] = 3


def assert_no_emergency_backdoor(mechanism: str) -> None:
    """ارفض أي آلية استرداد تُختصر بها كل الحمايات."""
    normalized = mechanism.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in FORBIDDEN_RECOVERY_MECHANISMS:
        raise EmergencyBackdoorError(
            f"«{mechanism}» باب خلفي لا آلية استرداد. من عرفه صار ملكًا، "
            "فيُبطل كل ما بُني قبله. الاسترداد بحصص موزَّعة ومراسم بإشهاد."
        )


class RecoveryTrigger(str, Enum):
    """أسباب مشروعة لبدء الاسترداد — كلها فقدان وصول لا فقدان ملك."""

    PRIMARY_ENVIRONMENT_LOST = "PRIMARY_ENVIRONMENT_LOST"
    SIGNING_DEVICE_DESTROYED = "SIGNING_DEVICE_DESTROYED"
    KEY_COMPROMISE_CONFIRMED = "KEY_COMPROMISE_CONFIRMED"
    FACILITY_INACCESSIBLE = "FACILITY_INACCESSIBLE"
    PROLONGED_INFRASTRUCTURE_LOSS = "PROLONGED_INFRASTRUCTURE_LOSS"

    @property
    def implies_authority_change(self) -> bool:
        """لا واحد من هذه الأسباب يغيّر صاحب السلطة. الاسترداد ليس خلافة."""
        return False


class RecoveryStage(str, Enum):
    """مراحل مراسم الاسترداد بالترتيب."""

    NOT_STARTED = "NOT_STARTED"
    DECLARED = "DECLARED"
    HOLDERS_ASSEMBLED = "HOLDERS_ASSEMBLED"
    QUORUM_VERIFIED = "QUORUM_VERIFIED"
    OFFLINE_CEREMONY_PERFORMED = "OFFLINE_CEREMONY_PERFORMED"
    ANCHOR_REVERIFIED = "ANCHOR_REVERIFIED"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


_STAGE_ORDER: Final[tuple[RecoveryStage, ...]] = (
    RecoveryStage.NOT_STARTED,
    RecoveryStage.DECLARED,
    RecoveryStage.HOLDERS_ASSEMBLED,
    RecoveryStage.QUORUM_VERIFIED,
    RecoveryStage.OFFLINE_CEREMONY_PERFORMED,
    RecoveryStage.ANCHOR_REVERIFIED,
    RecoveryStage.COMPLETED,
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class ShareHolderDescriptor:
    """وصف حامل حصة — بلا حصة. معرّفه، وموضع حرزه، ومرجع تحققه.

    لا حقل هنا يحمل قيمة سرية، وهذا مفحوص في الاختبارات: وجود قيمة الحصة في
    المستودع يُبطل كل التقسيم، لأن قارئ المستودع يجمعها كلها.
    """

    holder_id: str
    role: str
    location_ref: str
    verification_ref: str
    cold_storage: bool = True

    def __post_init__(self) -> None:
        if not self.holder_id or not self.location_ref:
            raise RecoveryError("حامل حصة بلا معرّف أو بلا موضع حرز.")
        if not self.verification_ref:
            raise RecoveryError(
                f"الحامل «{self.holder_id}» بلا مرجع تحقق من هويته."
            )
        if not self.cold_storage:
            # حصة في حرز متصل بالشبكة ليست حصة موزَّعة، بل نسخة قابلة للسحب عن بعد.
            raise RecoveryError(
                f"حصة الحامل «{self.holder_id}» ليست في حرز بارد — "
                "الحرز المتصل يُبطل معنى التوزيع."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "holder_id": self.holder_id,
            "role": self.role,
            "location_ref": self.location_ref,
            "verification_ref": self.verification_ref,
            "cold_storage": self.cold_storage,
            "holds_material_in_repository": False,
        }


@dataclass(frozen=True, slots=True)
class RecoveryScheme:
    """مخطط الاسترداد: m من n، بمواضع متعددة، وبلا باب خلفي.

    شرط تعدد المواضع منفَّذ لا موصوف: بغيره يكفي اقتحام غرفة واحدة لجمع النصاب،
    فيصير التقسيم شكليًّا.
    """

    quorum: int
    holders: tuple[ShareHolderDescriptor, ...]
    printed_verification_ref: str
    offline_root_ref: str
    documentation_ref: str
    mechanism: str = "distributed_shares_offline_ceremony"

    def __post_init__(self) -> None:
        assert_no_emergency_backdoor(self.mechanism)
        if len(self.holders) < MINIMUM_SHARE_HOLDERS:
            raise QuorumError(
                f"حاملو الحصص {len(self.holders)} والحد الأدنى {MINIMUM_SHARE_HOLDERS}."
            )
        if self.quorum < MINIMUM_QUORUM:
            raise QuorumError(
                f"النصاب {self.quorum} والحد الأدنى {MINIMUM_QUORUM} — "
                "نصاب صغير يُقارب الحامل الواحد."
            )
        if self.quorum > len(self.holders):
            raise QuorumError("نصاب أكبر من عدد الحاملين — مخطط لا يُستَرد به أبدًا.")
        if self.quorum == len(self.holders):
            raise QuorumError(
                "نصاب مساوٍ لكل الحاملين يجعل فقد حامل واحد فقدًا للتاج. "
                "المخطط يحتاج احتمالًا للتخلّف."
            )
        locations = {h.location_ref for h in self.holders}
        if len(locations) < MINIMUM_DISTINCT_LOCATIONS:
            raise QuorumError(
                f"مواضع الحرز المتمايزة {len(locations)} والحد الأدنى "
                f"{MINIMUM_DISTINCT_LOCATIONS} — اقتحام موضع واحد يجمع النصاب."
            )
        if not self.printed_verification_ref:
            raise RecoveryError(
                "لا مرجع لمادة تحقق مطبوعة أو في تخزين بارد — "
                "الاسترداد يحتاج مرجعًا خارج الشبكة."
            )

    @property
    def holder_count(self) -> int:
        return len(self.holders)

    @property
    def distinct_locations(self) -> int:
        return len({h.location_ref for h in self.holders})

    def as_dict(self) -> dict[str, Any]:
        return {
            "mechanism": self.mechanism,
            "quorum": self.quorum,
            "holder_count": self.holder_count,
            "distinct_locations": self.distinct_locations,
            "printed_verification_ref": self.printed_verification_ref,
            "offline_root_ref": self.offline_root_ref,
            "documentation_ref": self.documentation_ref,
            "holders": [h.as_dict() for h in self.holders],
            "material_in_repository": False,
        }


@dataclass(slots=True)
class RecoveryCeremony:
    """مراسم استرداد بمراحلها وحضورها ومراجعها.

    ولا تُنتج سلطة جديدة: تُعيد الوصول إلى سلطة قائمة. ولذلك يوجد فحص صريح يمنع
    أن تنقلب المراسم إلى خلافة صامتة.
    """

    scheme: RecoveryScheme
    trigger: RecoveryTrigger
    declared_by: str
    stage: RecoveryStage = RecoveryStage.NOT_STARTED
    present_holders: list[str] = field(default_factory=list)
    offline_ceremony_ref: str = ""
    anchor_verification_ref: str = ""
    aborted_reason: str = ""
    stage_log: list[tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.declared_by:
            raise RecoveryError("مراسم استرداد بلا مُعلِن بشري.")

    def _advance(self, target: RecoveryStage) -> None:
        if self.stage is RecoveryStage.ABORTED:
            raise RecoveryStageError("مراسم مُلغاة لا تُستأنف.")
        current = _STAGE_ORDER.index(self.stage)
        nxt = _STAGE_ORDER.index(target)
        if nxt != current + 1:
            raise RecoveryStageError(
                f"طيّ مرحلة في الاسترداد: {self.stage.value} → {target.value}."
            )
        self.stage = target
        self.stage_log.append((target.value, _now()))

    def declare(self) -> None:
        self._advance(RecoveryStage.DECLARED)

    def assemble(self, holder_ids: tuple[str, ...]) -> None:
        known = {h.holder_id for h in self.scheme.holders}
        unknown = [h for h in holder_ids if h not in known]
        if unknown:
            raise QuorumError(
                f"حاملون غير مسجَّلين في المخطط: {', '.join(unknown)}."
            )
        self.present_holders = list(dict.fromkeys(holder_ids))
        self._advance(RecoveryStage.HOLDERS_ASSEMBLED)

    def verify_quorum(self) -> None:
        """تحقق النصاب وتعدد المواضع معًا — لا أحدهما دون الآخر."""
        if len(self.present_holders) < self.scheme.quorum:
            raise QuorumError(
                f"الحاضرون {len(self.present_holders)} والنصاب {self.scheme.quorum}."
            )
        locations = {
            h.location_ref
            for h in self.scheme.holders
            if h.holder_id in set(self.present_holders)
        }
        if len(locations) < 2:
            raise QuorumError(
                "كل الحاضرين من موضع حرز واحد — النصاب مستوفى شكلًا لا معنى، "
                "لأن اقتحام موضع واحد يكفي لجمعه."
            )
        self._advance(RecoveryStage.QUORUM_VERIFIED)

    def perform_offline_ceremony(self, *, ceremony_ref: str) -> None:
        """قيّد أن المراسم أُجريت خارج الشبكة. البرمجية تُقيّد ولا تُجري.

        وهذا حدّ صادق: التوقيع على عتاد معزول لا يمكن لهذه الوحدة تنفيذه، فتكتفي
        بحفظ مرجعه.
        """
        if not ceremony_ref:
            raise RecoveryError("مراسم خارج الشبكة بلا مرجع موثَّق.")
        self.offline_ceremony_ref = ceremony_ref
        self._advance(RecoveryStage.OFFLINE_CEREMONY_PERFORMED)

    def reverify_anchor(self, *, verification_ref: str) -> None:
        if not verification_ref:
            raise RecoveryError("إعادة تحقق مرساة الثقة بلا مرجع.")
        self.anchor_verification_ref = verification_ref
        self._advance(RecoveryStage.ANCHOR_REVERIFIED)

    def complete(self) -> None:
        if not (self.offline_ceremony_ref and self.anchor_verification_ref):
            raise RecoveryStageError(
                "إتمام استرداد بلا مرجع مراسم خارج الشبكة أو بلا إعادة تحقق للمرساة."
            )
        self._advance(RecoveryStage.COMPLETED)

    def abort(self, *, reason: str) -> None:
        if not reason:
            raise RecoveryError("إلغاء مراسم بلا سبب مكتوب.")
        self.aborted_reason = reason
        self.stage = RecoveryStage.ABORTED
        self.stage_log.append((RecoveryStage.ABORTED.value, _now()))

    def assert_not_succession(self) -> None:
        """الاسترداد يعيد الوصول ولا ينقل السلطة (فرق البند 33 عن البند 27)."""
        if self.trigger.implies_authority_change:
            raise RecoveryError(
                "سبب الاسترداد يدّعي تغيير صاحب السلطة. "
                "الاسترداد يستعيد الوصول، والخلافة مراسم أخرى لها شهودها."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "trigger": self.trigger.value,
            "declared_by": self.declared_by,
            "stage": self.stage.value,
            "present_holders": list(self.present_holders),
            "offline_ceremony_ref": self.offline_ceremony_ref,
            "anchor_verification_ref": self.anchor_verification_ref,
            "aborted_reason": self.aborted_reason,
            "scheme": self.scheme.as_dict(),
            "stage_log": [{"stage": s, "at": t} for s, t in self.stage_log],
        }


class CrownRecovery:
    """منسّق الاسترداد: مراسم واحدة في الوقت، وكل مرحلة في سجل التاج."""

    def __init__(self, *, audit: CrownAudit | None = None) -> None:
        self._audit = audit if audit is not None else CrownAudit()
        # لا تكتب «audit or CrownAudit()»: السجل الفارغ قيمته المنطقية كاذبة لأنّ له طولًا،
        # فيُستبدَل سجل المتّصل بسجل داخلي لا يراه أحد — وذلك فقدان أدلة صامت.
        self._active: RecoveryCeremony | None = None
        self._history: list[RecoveryCeremony] = []

    @property
    def audit(self) -> CrownAudit:
        return self._audit

    @property
    def active_ceremony(self) -> RecoveryCeremony | None:
        return self._active

    @property
    def history(self) -> tuple[RecoveryCeremony, ...]:
        return tuple(self._history)

    def open_ceremony(
        self,
        *,
        scheme: RecoveryScheme,
        trigger: RecoveryTrigger,
        declared_by: str,
    ) -> RecoveryCeremony:
        if self._active is not None and self._active.stage not in {
            RecoveryStage.COMPLETED,
            RecoveryStage.ABORTED,
        }:
            raise RecoveryError(
                f"مراسم استرداد قائمة في المرحلة {self._active.stage.value}."
            )
        ceremony = RecoveryCeremony(
            scheme=scheme, trigger=trigger, declared_by=declared_by
        )
        ceremony.assert_not_succession()
        ceremony.declare()
        self._active = ceremony
        self._history.append(ceremony)
        self._audit.append(
            CrownAuditEventKind.RECOVERY_EVENT,
            actor=declared_by,
            subject=trigger.value,
            summary="بدء مراسم استرداد التاج خارج الشبكة.",
            detail=ceremony.as_dict(),
        )
        return ceremony

    def record_stage(self, ceremony: RecoveryCeremony, *, actor: str) -> None:
        self._audit.append(
            CrownAuditEventKind.RECOVERY_EVENT,
            actor=actor,
            subject=ceremony.trigger.value,
            summary=f"مراسم الاسترداد بلغت المرحلة {ceremony.stage.value}.",
            detail=ceremony.as_dict(),
        )


__all__ = [
    "FORBIDDEN_RECOVERY_MECHANISMS",
    "MINIMUM_DISTINCT_LOCATIONS",
    "MINIMUM_QUORUM",
    "MINIMUM_SHARE_HOLDERS",
    "CrownRecovery",
    "EmergencyBackdoorError",
    "QuorumError",
    "RecoveryCeremony",
    "RecoveryError",
    "RecoveryScheme",
    "RecoveryStage",
    "RecoveryStageError",
    "RecoveryTrigger",
    "ShareHolderDescriptor",
    "assert_no_emergency_backdoor",
]
