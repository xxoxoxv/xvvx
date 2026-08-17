"""الهدف: اختبار الاستمرارية والخلافة والاسترداد — والفصل بين الغياب والانقطاع.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

جوهر ما يُختبر هنا حكم واحد: النظام لا يستنتج غياب الملك من إشارة تقنية، ولا يعيّن
خليفة من نفسه، ولا يمنح الاسترداد سلطة جديدة. وكل بند منها يُرفَض بكود لا بتعليق.
"""

from __future__ import annotations

import pytest

from core.crown.audit import AuditChainBrokenError, CrownAudit
from core.crown.continuity import (
    FORBIDDEN_CONCLUSIONS,
    INVALID_INFERENCES,
    LOCKDOWN_PROFILES,
    PLANE_ISOLATION,
    AutonomousSuccessionError,
    ContinuityDoctrine,
    ContinuityState,
    CrownContinuity,
    InvalidInferenceError,
    LockdownLevel,
    SecurityPlane,
    SovereignCondition,
    SovereignSignal,
    StateDeclaration,
    UndeclaredTransitionError,
    assert_no_cross_plane_escalation,
    assert_not_inferred,
)
from core.crown.key_registry import CrownKeyRegistry
from core.crown.recovery import (
    FORBIDDEN_RECOVERY_MECHANISMS,
    MINIMUM_DISTINCT_LOCATIONS,
    MINIMUM_QUORUM,
    MINIMUM_SHARE_HOLDERS,
    CrownRecovery,
    EmergencyBackdoorError,
    QuorumError,
    RecoveryScheme,
    RecoveryStage,
    RecoveryTrigger,
    ShareHolderDescriptor,
    assert_no_emergency_backdoor,
)
from core.crown.succession import (
    FORBIDDEN_SUCCESSION_DECIDERS,
    FORBIDDEN_SUCCESSION_TRIGGERS,
    MINIMUM_WITNESSES,
    CrownSuccession,
    SuccessionAuthorityError,
    SuccessionCeremony,
    SuccessionError,
    SuccessionMandate,
    SuccessionStage,
    SuccessionStageError,
    SuccessionWitness,
    assert_eligible_decider,
    assert_valid_trigger,
)

from tests.crown.conftest import TransientSigner, iso, utc_now

# ─────────────────────────────────────────────────────────────────────────────
# الإشارة ليست حكمًا (البندان 10 و11).
# ─────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("signal,conclusion,_reason", INVALID_INFERENCES)
def test_technical_signal_never_implies_sovereign_conclusion(
    signal: SovereignSignal, conclusion: str, _reason: str
) -> None:
    """كل استنتاج محظور مرفوض تنفيذيًّا: الجهاز المطفأ ليس ملكًا غائبًا."""
    with pytest.raises(InvalidInferenceError):
        assert_not_inferred(signal, conclusion)


def test_forbidden_conclusions_cover_authority_transfer() -> None:
    """قائمة الاستنتاجات المحظورة تشمل نقل السلطة وشغور التاج وتعيين خليفة."""
    for conclusion in ("KING_DEAD", "CROWN_VACANT", "AUTHORITY_TRANSFERRED", "SUCCESSOR_APPOINTED"):
        assert conclusion in FORBIDDEN_CONCLUSIONS


def test_observing_signals_changes_no_state() -> None:
    """رصد الإشارات يُقيَّد ولا يحوّل الحالة — الرصد ليس إعلانًا."""
    continuity = CrownContinuity()
    for signal in (
        SovereignSignal.DEVICE_OFFLINE,
        SovereignSignal.NO_RESPONSE,
        SovereignSignal.PROLONGED_SILENCE,
        SovereignSignal.BIOMETRIC_UNAVAILABLE,
    ):
        continuity.observe(signal, source="monitor", detail="رصد آلي")
    assert continuity.state is ContinuityState.KING_PRESENT
    assert len(continuity.observations) == 4
    assert continuity.signals_of(SovereignSignal.NO_RESPONSE)


def test_isolation_is_not_absence() -> None:
    """العزل حال مؤقت لا غياب: الحالة تُعلَن عزلًا ولا تُقبل أوامر جديدة فيها (البند 12)."""
    continuity = CrownContinuity()
    continuity.observe(SovereignSignal.NETWORK_LOSS, source="net-monitor")
    state = continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_ISOLATED,
            declared_by="مدير الأمن البشري",
            reason="انقطاع اتصال مطوّل مع تعذّر التحقق من القناة.",
            evidence_refs=("ticket://net-1",),
            witnesses=("W1",),
            condition=SovereignCondition.ISOLATION,
        )
    )
    assert state is ContinuityState.KING_ISOLATED
    assert not continuity.accepts_new_royal_commands
    # والعزل قابل للرجوع إلى الحضور — لأنه ليس غيابًا.
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_PRESENT,
            declared_by="مدير الأمن البشري",
            reason="عاد الاتصال وتحقّقت القناة بمراسم.",
            witnesses=("W1", "W2"),
            condition=SovereignCondition.NORMAL,
        )
    )
    assert continuity.accepts_new_royal_commands
    assert continuity.condition is SovereignCondition.NORMAL


def test_undeclared_transition_is_rejected() -> None:
    """انتقال غير مُدرَج مرفوض بالاسم: لا حالة تتغير بالسكوت."""
    continuity = CrownContinuity()
    with pytest.raises(UndeclaredTransitionError):
        continuity.declare(
            StateDeclaration(
                state=ContinuityState.SUCCESSION_COMPLETED,
                declared_by="أي أحد",
                reason="محاولة قفز إلى إتمام خلافة.",
                witnesses=("W1",),
            )
        )


def test_declaration_requires_human_declarer_and_reason() -> None:
    """إعلان بلا مُعلِن أو بلا سبب مرفوض — الإعلان مسؤولية شخص."""
    with pytest.raises(UndeclaredTransitionError):
        StateDeclaration(
            state=ContinuityState.KING_UNAVAILABLE, declared_by="", reason="س"
        )
    with pytest.raises(UndeclaredTransitionError):
        StateDeclaration(
            state=ContinuityState.KING_UNAVAILABLE, declared_by="مدير", reason=""
        )


def test_death_condition_requires_external_attestation() -> None:
    """الحال الذي يلزمه إشهاد رسمي لا يُقبَل بإقرار داخلي (البند 14)."""
    with pytest.raises(UndeclaredTransitionError):
        StateDeclaration(
            state=ContinuityState.SUCCESSION_FORMALLY_INITIATED,
            declared_by="مجلس",
            reason="وفاة مفترضة",
            witnesses=("W1", "W2", "W3"),
            condition=SovereignCondition.CONFIRMED_DEATH,
        )


def test_doctrine_death_does_not_end_the_state() -> None:
    """موت الملك لا ينهي الدولة — والعقيدة مكتوبة في كود لا في خطاب."""
    assert ContinuityDoctrine().death_ends_the_state is False


def test_no_autonomous_successor() -> None:
    """لا خليفة آلي: إتمام الخلافة بلا إشهاد بشري مرفوض."""
    continuity = CrownContinuity(initial_state=ContinuityState.KING_UNAVAILABLE)
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.SUCCESSION_FORMALLY_INITIATED,
            declared_by="مؤسسة قانونية",
            reason="مسار خلافة رسمي بسند قانوني.",
            witnesses=("W1", "W2", "W3"),
        )
    )
    with pytest.raises(AutonomousSuccessionError):
        continuity.declare(
            StateDeclaration(
                state=ContinuityState.SUCCESSION_COMPLETED,
                declared_by="النظام",
                reason="إتمام آلي.",
            )
        )
    continuity.assert_no_autonomous_successor()


# ─────────────────────────────────────────────────────────────────────────────
# التصعيد والانكفاء (البند 13).
# ─────────────────────────────────────────────────────────────────────────────


def test_lockdown_grants_no_new_authority() -> None:
    """كل مستويات الانكفاء تقيّد ولا تمنح — الطوارئ ليست بابًا لسلطة."""
    for level, profile in LOCKDOWN_PROFILES.items():
        assert profile.level is level
        assert profile.grants_new_authority is False


def test_lockdown_restricts_progressively() -> None:
    """الانكفاء تدريجي: يوقف التطور الذاتي وتوسيع الصلاحيات ويشدّد المرساة."""
    continuity = CrownContinuity()
    profile = continuity.set_lockdown(
        LockdownLevel.LOCKDOWN,
        declared_by="مدير الأمن البشري",
        reason="مؤشرات اختراق منظومي.",
    )
    assert profile.autonomous_evolution_halted
    assert profile.privilege_escalation_halted
    assert profile.trust_anchor_hardened
    assert continuity.lockdown_level is LockdownLevel.LOCKDOWN


def test_compromise_response_flow() -> None:
    """مسار الاستجابة لاختراق مفتاح: تعليق الأوامر، ثم إحالة، ثم إعادة تأسيس."""
    audit = CrownAudit()
    continuity = CrownContinuity(audit=audit)
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.CROWN_KEY_COMPROMISED,
            declared_by="مدير الأمن البشري",
            reason="أثر استخدام مادة مفتاح خارج العتاد.",
            evidence_refs=("forensics://1",),
            witnesses=("W1", "W2"),
        )
    )
    assert not continuity.accepts_new_royal_commands
    continuity.set_lockdown(
        LockdownLevel.LOCKDOWN, declared_by="مدير الأمن البشري", reason="احتواء"
    )
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.CROWN_KEY_RETIRED,
            declared_by="مدير الأمن البشري",
            reason="إحالة المفتاح المخترق ونقل النسب.",
            witnesses=("W1", "W2", "W3"),
        )
    )
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_PRESENT,
            declared_by="مدير الأمن البشري",
            reason="مفتاح جديد بمراسم وإشهاد ومرساة محدَّثة.",
            witnesses=("W1", "W2", "W3"),
        )
    )
    assert continuity.accepts_new_royal_commands
    audit.verify_chain()
    snapshot = continuity.snapshot()
    assert snapshot["state"] == ContinuityState.KING_PRESENT.value


def test_audit_records_every_state_change_and_detects_tampering() -> None:
    """كل تحول حالة يُقيَّد، والعبث بالقيد يُكشَف."""
    audit = CrownAudit()
    continuity = CrownContinuity(audit=audit)
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_UNAVAILABLE,
            declared_by="مدير الأمن البشري",
            reason="تعذّر الوصول مؤقتًا.",
            witnesses=("W1",),
        )
    )
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_ISOLATED,
            declared_by="مدير الأمن البشري",
            reason="تأكد العزل.",
            witnesses=("W1", "W2"),
        )
    )
    audit.verify_chain()
    assert len(audit.entries) >= 2
    audit._entries.pop(0)  # عبث مقصود: حذف قيد من الوسط
    with pytest.raises(AuditChainBrokenError):
        audit.verify_chain()


def test_tail_truncation_requires_external_tip_pin() -> None:
    """قطع ذيل السجل لا تكشفه السلسلة وحدها — وهذا حدٌّ مُعلَن لا مستور.

    السلسلة تربط كل قيد بسابقه، فحذف الأخير يُبقي الباقي متسقًا، والكشف يحتاج
    تثبيت رأس السلسلة خارج النطاق المخترَق — وهو ما يُثبته هذا الاختبار.
    """
    audit = CrownAudit()
    continuity = CrownContinuity(audit=audit)
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_UNAVAILABLE,
            declared_by="مدير الأمن البشري",
            reason="تعذّر مؤقت.",
            witnesses=("W1",),
        )
    )
    pinned_tip = audit.tip_hash
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_ISOLATED,
            declared_by="مدير الأمن البشري",
            reason="تأكد العزل.",
            witnesses=("W1", "W2"),
        )
    )
    new_tip = audit.tip_hash
    assert new_tip != pinned_tip
    audit._entries.pop()  # قطع الذيل
    audit.verify_chain()  # السلسلة وحدها لا تكشفه
    assert audit.tip_hash == pinned_tip
    assert audit.tip_hash != new_tip, (
        "مقارنة رأس السلسلة بمرجع خارجي هي وجه الكشف الوحيد لقطع الذيل."
    )


# ─────────────────────────────────────────────────────────────────────────────
# عزل المستويات (البند 15).
# ─────────────────────────────────────────────────────────────────────────────


def test_planes_are_isolated_and_grant_no_authority_over_each_other() -> None:
    """السيطرة على مستوى لا تعني السيطرة على غيره."""
    assert set(PLANE_ISOLATION) == set(SecurityPlane)
    for plane, isolation in PLANE_ISOLATION.items():
        assert isolation.plane is plane
        assert isolation.separate_credentials


def test_cross_plane_escalation_is_rejected() -> None:
    """التصعيد من مستوى إلى مستوى ممنوع صراحة — لا تسلسل صامت."""
    with pytest.raises(Exception):
        assert_no_cross_plane_escalation(SecurityPlane.DATA, SecurityPlane.CRYPTOGRAPHIC)


# ─────────────────────────────────────────────────────────────────────────────
# الخلافة (البند 27).
# ─────────────────────────────────────────────────────────────────────────────


def _mandate(**overrides) -> SuccessionMandate:
    data = {
        "mandate_id": "SUCC-1",
        "decided_by": "المؤسسة القانونية المختصة",
        "legal_basis_ref": "law://succession/art-3",
        "trigger": "FORMAL_LEGAL_DECISION",
        "predecessor_subject_ref": "SUBJ-001",
        "successor_subject_ref": "SUBJ-002",
        "declared_at": iso(utc_now()),
    }
    data.update(overrides)
    return SuccessionMandate(**data)


@pytest.mark.parametrize("decider", sorted(FORBIDDEN_SUCCESSION_DECIDERS))
def test_forbidden_decider_cannot_decide_succession(decider: str) -> None:
    """لا النظام ولا الحارس ولا وكيل يقرر خلافة — القرار بشري مؤسسي."""
    with pytest.raises(SuccessionAuthorityError):
        assert_eligible_decider(decider)


@pytest.mark.parametrize("trigger", sorted(FORBIDDEN_SUCCESSION_TRIGGERS))
def test_forged_succession_trigger_rejected(trigger: str) -> None:
    """مُحرِّك تقني للخلافة مرفوض: الصمت والانقطاع ليسا سببًا لخلافة."""
    with pytest.raises((SuccessionError, SuccessionAuthorityError)):
        assert_valid_trigger(trigger)


def test_succession_requires_minimum_witnesses(
    successor_signer: TransientSigner, registry: CrownKeyRegistry
) -> None:
    """إشهاد أقل من الحد الأدنى مرفوض — الخلافة ليست فعل شخص."""
    ceremony = SuccessionCeremony(mandate=_mandate())
    ceremony.initiate()
    ceremony.establish_eligibility(eligibility_ref="law://eligibility/1")
    too_few = tuple(
        SuccessionWitness(
            witness_id=f"W{i}",
            role="شاهد مؤسسي",
            verification_ref=f"verify://{i}",
            confirmed_at=iso(utc_now()),
        )
        for i in range(1, MINIMUM_WITNESSES)
    )
    with pytest.raises(SuccessionError):
        ceremony.confirm_witnesses(too_few)


def test_succession_stages_cannot_be_skipped() -> None:
    """لا قفز في المراحل: تسجيل مفتاح الخليفة قبل الإشهاد مرفوض."""
    ceremony = SuccessionCeremony(mandate=_mandate())
    ceremony.initiate()
    with pytest.raises(SuccessionStageError):
        ceremony.complete()


def test_full_succession_ceremony_transfers_lineage_with_witnesses(
    registry: CrownKeyRegistry, successor_signer: TransientSigner
) -> None:
    """المسار الشرعي الكامل: سند قانوني، وأهلية، وإشهاد، ومفتاح جديد، ومرساة محدَّثة."""
    succession = CrownSuccession()
    ceremony = succession.open_ceremony(_mandate())  # يبدأ المراسم بنفسه
    assert ceremony.stage is SuccessionStage.FORMALLY_INITIATED
    succession.record_stage(ceremony, actor="أمين المراسم")
    ceremony.establish_eligibility(eligibility_ref="law://eligibility/1")
    witnesses = tuple(
        SuccessionWitness(
            witness_id=f"W{i}",
            role="شاهد مؤسسي",
            verification_ref=f"verify://{i}",
            confirmed_at=iso(utc_now()),
        )
        for i in range(1, MINIMUM_WITNESSES + 1)
    )
    ceremony.confirm_witnesses(witnesses)
    ceremony.register_successor_key(
        registry,
        new_key_id="CROWN-K2",
        algorithm="Ed25519",
        public_key_hex=successor_signer.public_hex,
        keystore_kind="AIR_GAPPED_CEREMONY",
        attestation_ref="attest://ceremony/1",
    )
    ceremony.update_trust_anchor(anchor_update_ref="anchor://update/1")
    ceremony.complete()

    assert ceremony.stage is SuccessionStage.COMPLETED
    assert registry.active_or_raise().key_id == "CROWN-K2"
    report = succession.lineage_report(registry)
    assert report["succession_count"] == 1
    assert [k["key_id"] for k in report["keys"]] == ["CROWN-K1", "CROWN-K2"]
    assert report["keys"][-1]["predecessor"] == "CROWN-K1"
    assert report["keys"][-1]["witnesses"]
    succession.audit.verify_chain()


def test_aborted_succession_leaves_no_partial_authority(
    registry: CrownKeyRegistry,
) -> None:
    """إجهاض المراسم لا يترك سلطة نصف منقولة."""
    ceremony = SuccessionCeremony(mandate=_mandate())
    ceremony.initiate()
    ceremony.abort(reason="ظهر شكّ في سند القرار.")
    assert ceremony.stage is SuccessionStage.ABORTED
    assert registry.active_or_raise().key_id == "CROWN-K1"
    with pytest.raises(SuccessionStageError):
        ceremony.complete()


def test_mandate_requires_legal_basis() -> None:
    """تكليف خلافة بلا سند قانوني مرفوض."""
    with pytest.raises(SuccessionError):
        _mandate(legal_basis_ref="")


# ─────────────────────────────────────────────────────────────────────────────
# الاسترداد (البند 28).
# ─────────────────────────────────────────────────────────────────────────────


def _holders(count: int = MINIMUM_SHARE_HOLDERS) -> tuple[ShareHolderDescriptor, ...]:
    return tuple(
        ShareHolderDescriptor(
            holder_id=f"H{i}",
            role="حافظ نصيب",
            location_ref=f"vault://loc-{i % MINIMUM_DISTINCT_LOCATIONS}",
            verification_ref=f"verify://h{i}",
            cold_storage=True,
        )
        for i in range(1, count + 1)
    )


def _scheme(**overrides) -> RecoveryScheme:
    data = {
        "quorum": MINIMUM_QUORUM,
        "holders": _holders(),
        "printed_verification_ref": "print://fingerprint/1",
        "offline_root_ref": "offline://root/1",
        "documentation_ref": "docs/security/CROWN_SOVEREIGNTY_PROTECTION.md",
        "mechanism": "SHAMIR_M_OF_N_OFFLINE",
    }
    data.update(overrides)
    return RecoveryScheme(**data)


@pytest.mark.parametrize("mechanism", sorted(FORBIDDEN_RECOVERY_MECHANISMS))
def test_no_emergency_backdoor(mechanism: str) -> None:
    """لا مفتاح طوارئ، ولا وصول مطوّر، ولا استرداد عبر بريد — كلها مرفوضة."""
    with pytest.raises(EmergencyBackdoorError):
        assert_no_emergency_backdoor(mechanism)


def test_recovery_scheme_requires_real_distribution() -> None:
    """نصاب يساوي عدد الحافظين ليس توزيعًا — وحافظون أقل من الحد مرفوضون."""
    with pytest.raises(QuorumError):
        _scheme(quorum=MINIMUM_SHARE_HOLDERS)
    with pytest.raises(QuorumError):
        _scheme(quorum=1, holders=_holders(2))


def test_recovery_requires_quorum_presence() -> None:
    """اجتماع أقل من النصاب لا يفتح استردادًا."""
    ceremony = CrownRecovery().open_ceremony(
        scheme=_scheme(),
        trigger=RecoveryTrigger.PRIMARY_ENVIRONMENT_LOST,
        declared_by="مدير الأمن البشري",
    )
    assert ceremony.stage is RecoveryStage.DECLARED
    ceremony.assemble(("H1", "H2"))
    with pytest.raises(QuorumError):
        ceremony.verify_quorum()


def test_full_recovery_grants_no_new_authority() -> None:
    """الاسترداد يعيد الوصول ولا ينقل السلطة، وليس خلافة."""
    recovery = CrownRecovery()
    ceremony = recovery.open_ceremony(
        scheme=_scheme(),
        trigger=RecoveryTrigger.SIGNING_DEVICE_DESTROYED,
        declared_by="مدير الأمن البشري",
    )
    ceremony.assemble(("H1", "H2", "H3"))
    ceremony.verify_quorum()
    ceremony.perform_offline_ceremony(ceremony_ref="offline://cer/1")
    ceremony.reverify_anchor(verification_ref="anchor://reverify/1")
    ceremony.complete()
    assert ceremony.stage is RecoveryStage.COMPLETED
    ceremony.assert_not_succession()
    assert ceremony.trigger.implies_authority_change is False
    recovery.audit.verify_chain()


def test_recovery_is_not_a_succession_path() -> None:
    """الاسترداد ليس بابًا خلفيًّا للخلافة — والتمييز منفَّذ لا موصوف."""
    for trigger in RecoveryTrigger:
        assert trigger.implies_authority_change is False
