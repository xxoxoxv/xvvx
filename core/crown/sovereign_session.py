"""الهدف: مسار تنفيذ سيادي واحد يربط المرساة والسجل والأمر والاستمرارية والحارس.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

سبب وجود هذه الوحدة أن الوحدات كانت مُختبَرة كلٌّ على حدة، فكانت السلسلة السيادية
تُروى في الاختبار ولا تُنفَّذ في مسار واحد. والسلسلة التي لا تُنفَّذ في مسار واحد
تنكسر في أول موضع لم يصله أحد: من تحقّق من التوقيع ونسي حالة الاستمرارية، أو نفّذ
ونسي القيد في السجل.

وهذه الوحدة **لا تملك سلطة**: لا تُنشئ مفتاحًا، ولا تُعلن حالة نيابةً عن أحد، ولا
تُتمّ خلافة. هي بوّابة رفض متسلسلة: كل خطوة إما تمرّ بدليل أو تمنع التنفيذ. وأشدّ ما
تحرسه ``assert_no_false_crown`` — تُشغَّل قبل كل تنفيذ وبعده، لأن التاج الزائف لا
يُعلن عن نفسه، بل يظهر مفتاحًا نشطًا ثانيًا أو سلالةً منقطعة أو سجلًّا مكسورًا.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.crown.audit import CrownAudit, CrownAuditEventKind
from core.crown.command import (
    CommandLedger,
    CrownCommandVerifier,
    ExecutionRecord,
    SignedRoyalCommand,
    VerificationOutcome,
)
from core.crown.continuity import ContinuityState, CrownContinuity, StateDeclaration
from core.crown.guard import (
    ContainmentAction,
    GuardAuthorityError,
    GuardLayer,
    Severity,
    SovereignGuard,
)
from core.crown.key_registry import CrownKeyRegistry, KeyState
from core.crown.trust_anchor import CrownTrustAnchor, SignedKeyManifest


class SovereignSessionError(Exception):
    """خطأ في المسار السيادي — كل اشتقاق منه يمنع التنفيذ ولا يُسجَّل تحذيرًا."""


class AnchorNotVerifiedError(SovereignSessionError):
    """أمر قبل التحقق من المرساة — تنفيذٌ يثق بمفتاح لم يُثبَت أصله."""


class ContinuityRefusalError(SovereignSessionError):
    """حال الاستمرارية لا يقبل أوامر ملكية جديدة الآن."""


class FalseCrownError(SovereignSessionError):
    """تاج زائف: مفتاحان نشطان، أو سلالة منقطعة، أو حارس ادّعى سيادة."""


@dataclass
class SessionEvidence:
    """أثر خطوة واحدة — يُطبع ويُراجَع، ولا يُستنتج من نجاح صامت."""

    step: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"step": self.step, "passed": self.passed, "detail": self.detail}


@dataclass
class SovereignSession:
    """المسار السيادي الواحد: من المرساة إلى القيد في السجل.

    ولا تُنشأ هذه الجلسة بمفتاح خاص ولا تحمله: التوقيع يقع خارجها، وهي تتحقق فقط.
    """

    registry: CrownKeyRegistry
    anchor: CrownTrustAnchor
    guard: SovereignGuard
    audit: CrownAudit | None = None
    continuity: CrownContinuity | None = None
    ledger: CommandLedger = field(default_factory=CommandLedger)
    _anchor_verified: bool = field(default=False, init=False)
    _evidence: list[SessionEvidence] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.audit = self.audit if self.audit is not None else CrownAudit()
        self.continuity = (
            self.continuity
            if self.continuity is not None
            else CrownContinuity(audit=self.audit)
        )
        self.verifier = CrownCommandVerifier(self.registry, self.ledger)

    # ── الدليل ────────────────────────────────────────────────────────────────

    @property
    def evidence(self) -> tuple[SessionEvidence, ...]:
        return tuple(self._evidence)

    def _record(self, step: str, *, detail: str = "") -> None:
        self._evidence.append(SessionEvidence(step=step, passed=True, detail=detail))

    # ── 1. المرساة ────────────────────────────────────────────────────────────

    def verify_anchor(self, signed: SignedKeyManifest) -> CrownKeyRegistry:
        """تحقّق من بيان المفاتيح عبر المرساة قبل قبول أي أمر.

        والمرساة هي التي تتحقق، لا الجلسة: من جعل الجلسة تُصدِّق نفسها أعاد الثقة
        الدائرية من الباب الذي أُغلق.
        """
        verified = self.anchor.verify_manifest(signed)
        self._anchor_verified = True
        assert self.audit is not None
        self.audit.append(
            CrownAuditEventKind.TRUST_ANCHOR_EVENT,
            actor="anchor",
            subject=signed.root_key_id,
            summary="تحقّقت المرساة من بيان المفاتيح عبر مستويات مستقلة.",
            detail={"independent_sources": len(self.anchor.independent_sources)},
        )
        self._record(
            "المرساة محقَّقة",
            detail=(
                f"مصادر مستقلة: {len(self.anchor.independent_sources)} · "
                f"تثبيت خارج القناة: {self.anchor.out_of_band_confirmed}"
            ),
        )
        return verified

    # ── 2. لا تاج زائف ────────────────────────────────────────────────────────

    def assert_no_false_crown(self) -> None:
        """امنع التاج الزائف بفحص أربعة أدلة، لا برايةٍ ثابتة.

        ولا يكفي أحدها: مفتاح نشط واحد مع سجل مكسور تزويرٌ أيضًا.
        """
        active = [r for r in self.registry.records if r.state is KeyState.ACTIVE]
        if len(active) > 1:
            raise FalseCrownError(
                f"مفتاحان نشطان أو أكثر: {[r.key_id for r in active]} — تاجان لا تاج."
            )
        self.registry.validate()
        assert self.audit is not None
        self.audit.verify_chain()
        assert self.continuity is not None
        self.continuity.assert_no_autonomous_successor()
        # الاستدعاء يجب أن **يُرفَض**، ونصّ الرفض يُقيَّد دليلًا: استثناءٌ يُبتلع
        # بلا قيد يجعل البوابة غير قابلة للتمييز عن بوابة محذوفة.
        try:
            self.guard.assert_cannot_become_sovereign()
        except GuardAuthorityError as refusal:
            self._record("الحارس رُفض عن ادّعاء السيادة", detail=str(refusal)[:120])
        else:
            raise FalseCrownError(
                "الحارس قَبِل ادّعاء السيادة بلا رفض — انقلاب حارس صامت."
            )
        if self.guard.status()["holds_sovereign_authority"] is not False:
            raise FalseCrownError("الحارس يُعلن سلطة سيادية — انقلاب حارس.")

    def assert_guard_has_no_veto(self, command_id: str) -> str:
        """أثبت أن الحارس **يُرفَض** عن نقض أمر صحيح — بمحاولة فعلية لا بادّعاء.

        وإن مرّت المحاولة بلا رفض فذلك نقضٌ خفيّ، وهو أخطر من نقض معلن.
        """
        try:
            self.guard.assert_cannot_veto(command_id=command_id, command_is_valid=True)
        except GuardAuthorityError as refusal:
            self._record("لا نقض من تابع", detail=str(refusal)[:120])
            return str(refusal)
        raise FalseCrownError(
            f"الحارس نقض الأمر {command_id} بلا رفض — مسار نقض خفيّ."
        )

    # ── 3. التنفيذ ────────────────────────────────────────────────────────────

    def execute(
        self, command: SignedRoyalCommand, *, at: datetime | None = None
    ) -> ExecutionRecord:
        """نفّذ أمرًا ملكيًّا بعد اجتياز البوابات كلها بالترتيب.

        الترتيب مقصود: المرساة قبل التوقيع، والتوقيع قبل الاستمرارية، والاستمرارية
        قبل القيد. ومن نفّذ ثم تحقّق فقد نفّذ.
        """
        if not self._anchor_verified:
            raise AnchorNotVerifiedError(
                "لم تُتحقَّق المرساة بعد — لا يُقبل أمر بمفتاح لم يُثبَت أصله."
            )
        self.assert_no_false_crown()

        assert self.continuity is not None
        if not self.continuity.accepts_new_royal_commands:
            raise ContinuityRefusalError(
                f"حال الاستمرارية «{self.continuity.state.value}» لا يقبل أوامر جديدة. "
                "والتوقف الآمن أصدق من تنفيذٍ بسيادة غير مؤكَّدة."
            )

        outcome = self.verifier.verify(command, at=at)
        self._record(
            f"توقيع {command.envelope.command_id} صحيح",
            detail=f"المفتاح {outcome.key_id}",
        )
        self.assert_guard_has_no_veto(command.envelope.command_id)

        record = self.verifier.verify_and_commit(command, at=at)
        assert self.audit is not None
        self.audit.append(
            CrownAuditEventKind.ROYAL_DECISION,
            actor=command.envelope.issuer_key_id,
            subject=command.envelope.command_id,
            summary=f"تنفيذ القرار الملكي {command.envelope.command_id} بعد تحقق كامل.",
            detail={"action": command.envelope.action, "digest": record.digest},
        )
        self.assert_no_false_crown()
        self._record(
            f"نُفّذ {record.command_id} وقُيّد",
            detail=f"البصمة {record.digest[:16]}…",
        )
        return record

    # ── 4. الاختراق والاستمرارية ──────────────────────────────────────────────

    def declare_key_compromised(
        self, key_id: str, *, reason: str, witnesses: tuple[str, ...]
    ) -> None:
        """أعلن اختراق مفتاح: يُبطَل، وتُعلَن الحالة، ويُنبَّه الحارس بشريًّا.

        ولا يخلف النظام مفتاحًا من تلقائه هنا: الخلافة مراسم بشرية، والإعلان وحده
        لا يُنشئ خليفة.
        """
        if not witnesses:
            raise ContinuityRefusalError(
                "إعلان اختراق التاج بلا شاهد — والحالة تلزمها مراسم بإشهاد بشري."
            )
        self.registry.mark_compromised(key_id, reason=reason)
        assert self.continuity is not None
        self.continuity.declare(
            self._compromise_declaration(
                key_id=key_id, reason=reason, witnesses=witnesses
            )
        )
        alert = self.guard.alert(
            severity=Severity.LEVEL_4_CROWN_TRUST_COMPROMISE,
            title=f"اختراق مفتاح التاج {key_id}.",
            layers=(GuardLayer.GUARD_2_CRYPTOGRAPHIC,),
            actions=(ContainmentAction.PRESERVE_LOGS, ContainmentAction.PREVENT_DOWNGRADE),
        )
        if not alert.requires_human:
            raise FalseCrownError(
                "إنذار اختراق التاج لا يستدعي بشرًا — احتواء ذاتي لحدث سيادي."
            )
        self.continuity.assert_no_autonomous_successor()
        self._record(
            f"أُعلن اختراق {key_id}",
            detail="إنذار من الدرجة الرابعة يستدعي بشرًا، وبلا خليفة تلقائي",
        )

    @staticmethod
    def _compromise_declaration(
        *, key_id: str, reason: str, witnesses: tuple[str, ...]
    ) -> StateDeclaration:
        return StateDeclaration(
            state=ContinuityState.CROWN_KEY_COMPROMISED,
            declared_by="ديوان الأمن",
            reason=f"إبطال {key_id}: {reason}",
            evidence_refs=(f"registry:{key_id}",),
            witnesses=witnesses,
        )

    def verify_historical(self, command: SignedRoyalCommand) -> VerificationOutcome:
        """هل كان هذا القرار سياديًّا صحيحًا **يومه**؟ لا: هل يُنفَّذ الآن؟

        والجواب يتبع حال المفتاح لا رغبة المتحقق، والقاعدة المنفَّذة في
        ``CrownKeyRecord.was_valid_at`` صريحة: الإحالة بعد التدوير **لا** تُبطل
        الماضي، والاختراق أو السحب **يُبطله** — لأن معناهما أن الصفة لم تكن حقيقية.
        ولذلك تُعاد النتيجة كاملةً بسببها، ولا تُختزل إلى «نعم/لا» بلا تعليل.
        """
        outcome = self.verifier.verify_historical(
            command, signed_at=command.envelope.issued_at
        )
        self._record(
            f"التحقق التاريخي من {command.envelope.command_id}",
            detail=f"مقبول تاريخيًّا: {outcome.accepted} · {outcome.reason}"[:160],
        )
        return outcome

    # ── 5. الحال ──────────────────────────────────────────────────────────────

    def snapshot(self) -> dict[str, Any]:
        """حال الجلسة كاملًا — بما لا تملكه كما بما تملكه."""
        assert self.continuity is not None and self.audit is not None
        active = [r for r in self.registry.records if r.state is KeyState.ACTIVE]
        return {
            "anchor_verified": self._anchor_verified,
            "anchor_out_of_band_confirmed": self.anchor.out_of_band_confirmed,
            "independent_sources": len(self.anchor.independent_sources),
            "active_key_ids": [r.key_id for r in active],
            "lineage": [r.key_id for r in self.registry.lineage()],
            "continuity_state": self.continuity.state.value,
            "accepts_new_royal_commands": self.continuity.accepts_new_royal_commands,
            "executed_commands": [r.command_id for r in self.ledger.records()],
            "audit_entries": len(self.audit.snapshot()["entries"]),
            "guard_holds_sovereign_authority": self.guard.status()[
                "holds_sovereign_authority"
            ],
            "session_grants_authority": False,
            "evidence": [e.as_dict() for e in self._evidence],
        }
