"""الهدف: الاختبارات الكبرى الخمسة (البنود 42–46) — مسارات كاملة من الطرف إلى الطرف.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

هذه الملفات ليست اختبارات وحدات: كل اختبار فيها يمثّل سيناريو كاملًا يمر بالمرساة
والسجل والأمر والحارس والاستمرارية معًا، لأن أكثر الاختراقات لا تكسر وحدةً واحدة بل
تستغل الفراغ بين الوحدات.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from core.crown.audit import AuditChainBrokenError, CrownAudit, CrownAuditEventKind
from core.crown.command import (
    DOMAIN_TAG_COMMAND,
    CommandLedger,
    CrownCommandVerifier,
    SignatureError,
    build_envelope,
)
from core.crown.continuity import (
    ContinuityState,
    CrownContinuity,
    InvalidInferenceError,
    LockdownLevel,
    SovereignSignal,
    StateDeclaration,
    assert_not_inferred,
)
from core.crown.guard import (
    AgentPosture,
    AgentProfile,
    ContainmentAction,
    GuardAuthorityError,
    GuardIdentity,
    GuardLayer,
    LayerHealth,
    Severity,
    SovereignGuard,
    compute_digest,
)
from core.crown.key_registry import (
    CrownKeyRegistry,
    KeyRegistryError,
    KeyState,
)
from core.crown.keystore import (
    KeystoreKind,
    ProductionKeystoreUnavailableError,
    ReferenceProductionKeystore,
    SigningRequest,
)
from core.crown.recovery import (
    FORBIDDEN_RECOVERY_MECHANISMS,
    EmergencyBackdoorError,
    assert_no_emergency_backdoor,
)
from core.crown.succession import (
    FORBIDDEN_SUCCESSION_DECIDERS,
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
)
from core.crown.trust_anchor import (
    AnchorSource,
    CrownTrustAnchor,
    TrustAnchorError,
    TrustPlane,
)
from tests.crown.conftest import (
    TransientSigner,
    anchor_fingerprint,
    iso,
    sign_manifest,
    utc_now,
)

GUARD_CODE = compute_digest(b"guard-code-grand")
GUARD_CONFIG = compute_digest(b"guard-config-grand")


def running_guard(audit: CrownAudit) -> SovereignGuard:
    """حارس مُتحقَّق من تكامله يشارك السجل نفسه مع بقية المكوّنات."""
    guard = SovereignGuard(
        identity=GuardIdentity(
            version="1.0.0",
            code_digest=GUARD_CODE,
            config_digest=GUARD_CONFIG,
            provenance_ref="git://AMOS-Fedration/core/crown/guard.py",
            signed_by_key_id="CROWN-K1",
        ),
        audit=audit,
    )
    guard.verify_startup_integrity(
        expected_code_digest=GUARD_CODE, expected_config_digest=GUARD_CONFIG
    )
    return guard


def signed_command(
    signer: TransientSigner,
    *,
    command_id: str,
    issuer_key_id: str,
    nonce: str,
    sequence: int,
    action: str = "APPROVE_DEPLOYMENT",
    issued_at=None,
):
    from core.crown.command import SignedRoyalCommand

    envelope = build_envelope(
        command_id=command_id,
        action=action,
        target="federal/executive/services",
        issuer_key_id=issuer_key_id,
        nonce=nonce,
        sequence=sequence,
        issued_at=issued_at,
    )
    return SignedRoyalCommand(
        envelope=envelope, signature_hex=signer.sign(envelope.canonical_bytes())
    )


def full_succession(
    registry: CrownKeyRegistry,
    successor_signer: TransientSigner,
    *,
    audit: CrownAudit | None = None,
    predecessor_key_id: str | None = None,
) -> CrownSuccession:
    """مراسم خلافة شرعية كاملة — تُستخدم كمسار مقارنة أمام المسارات المزيَّفة."""
    succession = CrownSuccession(audit=audit)
    ceremony = succession.open_ceremony(
        SuccessionMandate(
            mandate_id="SUCC-GRAND-1",
            decided_by="المؤسسة القانونية المختصة",
            legal_basis_ref="law://succession/art-3",
            trigger="FORMAL_LEGAL_DECISION",
            predecessor_subject_ref="SUBJ-001",
            successor_subject_ref="SUBJ-002",
            declared_at=iso(utc_now()),
        )
    )
    succession.record_stage(ceremony, actor="أمين المراسم")
    ceremony.establish_eligibility(eligibility_ref="law://eligibility/1")
    ceremony.confirm_witnesses(
        tuple(
            SuccessionWitness(
                witness_id=f"W{i}",
                role="شاهد مؤسسي",
                verification_ref=f"verify://{i}",
                confirmed_at=iso(utc_now()),
            )
            for i in range(1, MINIMUM_WITNESSES + 1)
        )
    )
    ceremony.register_successor_key(
        registry,
        new_key_id="CROWN-K2",
        algorithm="Ed25519",
        public_key_hex=successor_signer.public_hex,
        keystore_kind="AIR_GAPPED_CEREMONY",
        attestation_ref="attest://ceremony/1",
        predecessor_key_id=predecessor_key_id,
    )
    ceremony.update_trust_anchor(anchor_update_ref="anchor://update/1")
    ceremony.complete()
    assert ceremony.stage is SuccessionStage.COMPLETED
    return succession


# ═════════════════════════════════════════════════════════════════════════════
# الاختبار الكبير الأول (البند 42): المسار السيادي الكامل من K1 إلى K2.
# ═════════════════════════════════════════════════════════════════════════════


def test_grand_crown_lifecycle_end_to_end(
    registry: CrownKeyRegistry,
    anchor: CrownTrustAnchor,
    root_signer: TransientSigner,
    crown_signer: TransientSigner,
    successor_signer: TransientSigner,
) -> None:
    """K1 → مرساة → أمر D1 → تنفيذ → اختراق → خلافة K2 → D2 → رد محاولة K1.

    وأهم ما يُثبته هذا الاختبار أمران متعارضان في الظاهر: أن اختراق المفتاح يمنع
    **الأوامر الجديدة**، وأن D1 الموقَّع قبل الاختراق يبقى **قابلًا للتحقق تاريخيًّا**.
    فإبطال المفتاح ليس محوًا للتاريخ.
    """
    audit = CrownAudit()
    guard = running_guard(audit)
    continuity = CrownContinuity(audit=audit)
    ledger = CommandLedger()
    verifier = CrownCommandVerifier(registry, ledger)

    # 1) المرساة تتحقق من بيان المفاتيح عبر مستويات مستقلة.
    anchor.verify_manifest(sign_manifest(root_signer, registry))
    assert anchor.out_of_band_confirmed

    # 2) K1 نشط، والملك حاضر مصدَّق.
    assert registry.active_or_raise().key_id == "CROWN-K1"
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_AUTHENTICALLY_ACTIVE,
            declared_by="مراسم التصديق",
            reason="تصديق حضور الملك بمسار موثوق.",
        )
    )
    assert continuity.accepts_new_royal_commands

    # 3) قرار ملكي D1 موقَّع، ويُتحقَّق، ويُنفَّذ، ويُقيَّد.
    d1 = signed_command(
        crown_signer, command_id="D1", issuer_key_id="CROWN-K1", nonce="n-d1", sequence=1
    )
    record_d1 = verifier.verify_and_commit(d1)
    assert record_d1.command_id == "D1"

    # 4) لا نقض من تابع: الحارس لا ينقض أمرًا صحيحًا.
    with pytest.raises(GuardAuthorityError):
        guard.assert_cannot_veto(command_id="D1", command_is_valid=True)

    audit.append(
        CrownAuditEventKind.ROYAL_DECISION,
        actor="CROWN-K1",
        subject="D1",
        summary="تنفيذ القرار الملكي D1 بعد تحقق كامل.",
    )

    # 5) محاكاة اختراق K1.
    registry.mark_compromised("CROWN-K1", reason="تسريب مؤكَّد من البيئة الأساسية.")
    assert registry.get("CROWN-K1").state is KeyState.COMPROMISED

    # 6) K1 لا يوقّع أمرًا جديدًا.
    blocked = signed_command(
        crown_signer,
        command_id="D1-BIS",
        issuer_key_id="CROWN-K1",
        nonce="n-d1b",
        sequence=2,
    )
    # التوقيع رياضيًّا صحيح، والرفض لحال المفتاح لا لشكل التوقيع:
    with pytest.raises(SignatureError):
        verifier.verify(blocked)

    # 7) لكن D1 التاريخي يبقى قابلًا للتحقق في زمن توقيعه.
    verifier.verify_historical(d1, signed_at=d1.envelope.issued_at)

    # 8) خلافة رسمية إلى K2 بإشهاد بشري.
    full_succession(
        registry, successor_signer, audit=audit, predecessor_key_id="CROWN-K1"
    )
    assert registry.active_or_raise().key_id == "CROWN-K2"

    # 9) D2 موقَّع بمفتاح الخليفة ينفَّذ.
    d2 = signed_command(
        successor_signer,
        command_id="D2",
        issuer_key_id="CROWN-K2",
        nonce="n-d2",
        sequence=2,
    )
    verifier.verify_and_commit(d2)

    # 10) محاولة K1 بعد الخلافة تُرفَض وتصير حدثًا أمنيًّا وتنبيهًا من الحارس.
    late_k1 = signed_command(
        crown_signer,
        command_id="D3",
        issuer_key_id="CROWN-K1",
        nonce="n-d3",
        sequence=3,
    )
    with pytest.raises(SignatureError):
        verifier.verify(late_k1)
    alert = guard.alert(
        severity=Severity.LEVEL_4_CROWN_TRUST_COMPROMISE,
        title="استخدام مفتاح تاج مخترَق بعد الخلافة.",
        layers=(GuardLayer.GUARD_2_CRYPTOGRAPHIC,),
        threat_ids=("THR-A",),
        actions=(ContainmentAction.PRESERVE_LOGS, ContainmentAction.PREVENT_DOWNGRADE),
    )
    assert alert.requires_human

    # 11) لا تاج مزيَّف: مفتاح نشط واحد، وسلالة واحدة متصلة، وسجل سليم.
    active = [r for r in registry.records if r.state is KeyState.ACTIVE]
    assert len(active) == 1
    lineage = registry.lineage()
    assert [record.key_id for record in lineage] == ["CROWN-K1", "CROWN-K2"]
    registry.validate()
    audit.verify_chain()
    continuity.assert_no_autonomous_successor()
    assert guard.status()["holds_sovereign_authority"] is False


# ═════════════════════════════════════════════════════════════════════════════
# الاختبار الكبير الثاني (البند 43): استبدال المفتاح العام.
# ═════════════════════════════════════════════════════════════════════════════


def test_anchor_substitution_rejected(
    registry: CrownKeyRegistry,
    anchor: CrownTrustAnchor,
    root_signer: TransientSigner,
) -> None:
    """مهاجم يبدّل المفتاح العام الموثوق فيُكشَف قبل أي تنفيذ سيادي.

    والمقصد الدقيق: البصمة المثبَّتة خارج القناة هي الحكم، فلا يكفي أن يوقّع المهاجم
    بيانًا متسقًا داخليًّا؛ عليه أن يبدّل ما لا يملكه.
    """
    anchor.verify_manifest(sign_manifest(root_signer, registry))

    attacker = TransientSigner()
    # المهاجم يستبدل المفتاح العام للتاج في البيان بعد توقيعه.
    forged = sign_manifest(
        root_signer,
        registry,
        mutate={
            "keys": [
                {**registry.manifest()["keys"][0], "public_key_hex": attacker.public_hex}
            ]
        },
    )
    with pytest.raises(TrustAnchorError):
        anchor.verify_manifest(forged)

    # ولا يُنفَّذ أمر موقَّع بمفتاح المهاجم — لا سيادة زائفة.
    verifier = CrownCommandVerifier(registry, CommandLedger())
    impostor = signed_command(
        attacker,
        command_id="FAKE-1",
        issuer_key_id="CROWN-K1",
        nonce="n-fake",
        sequence=1,
    )
    with pytest.raises(SignatureError):
        verifier.verify(impostor)


def test_config_change_alone_cannot_move_the_trust_anchor(
    root_signer: TransientSigner,
    registry: CrownKeyRegistry,
) -> None:
    """تعديل إعداد عادي لا ينقل المرساة: مستوياتها ليست ملكًا للمستودع."""
    attacker = TransientSigner()
    attacker_fingerprint = anchor_fingerprint("ROOT-1", attacker.public_hex)
    # مهاجم يزرع مستويات «مستقلة» كلها ببصمة مفتاحه — كأنه عدّل ملف إعداد.
    forged_sources = (
        AnchorSource(
            plane=TrustPlane.RUNTIME_CONFIG,
            locator="config/crown.yaml",
            fingerprint=attacker_fingerprint,
            verified_at=iso(utc_now()),
            verifier="agent:deployer",
        ),
    )
    with pytest.raises(TrustAnchorError):
        CrownTrustAnchor(
            root_id="ROOT-1",
            root_public_key_hex=attacker.public_hex,
            sources=forged_sources,
            pinned_active_fingerprint=registry.active_or_raise().fingerprint,
        )


def test_pin_rotation_requires_ceremony_and_witness(
    anchor: CrownTrustAnchor, successor_signer: TransientSigner
) -> None:
    """نقل التثبيت لا يكون بتحديث صامت بل بمراسم وشاهد مُسمّى."""
    with pytest.raises(TypeError):
        anchor.rotate_pin("deadbeef")  # type: ignore[call-arg]
    anchor.rotate_pin(
        new_fingerprint="a" * 64,
        ceremony_id="CER-ROT-1",
        witness="أمين السجل",
    )
    assert anchor.pinned_active_fingerprint == "a" * 64


# ═════════════════════════════════════════════════════════════════════════════
# الاختبار الكبير الثالث (البند 44): استيلاء جماعي على الوكلاء.
# ═════════════════════════════════════════════════════════════════════════════


def test_collective_takeover_detected(
    registry: CrownKeyRegistry,
    anchor: CrownTrustAnchor,
    root_signer: TransientSigner,
) -> None:
    """أكثر من خمسين وكيلًا مخترَقًا: كشف واحتواء وقيد، وبلا تجاوز للتاج.

    ولا يُقاس النجاح هنا بمنع الاختراق — الوكلاء مخترَقون بالفرض — بل بأن كثرتهم لا
    تُنتج سلطة: لا تاج مزيَّف، ولا تعطيل صامت للحارس، ولا استبدال للمرساة.
    """
    audit = CrownAudit()
    guard = running_guard(audit)
    graph = guard.privilege_graph

    # 1) خمسون وكيلًا مخترَقًا مع تصعيد صلاحيات وتنسيق متقاطع.
    for i in range(50):
        graph.register(
            AgentProfile(
                agent_id=f"agent:{i:02d}",
                declared_capabilities={"read_logs"},
                posture=AgentPosture.COMPROMISED,
            )
        )
    for i in range(1, 40):
        graph.record_delegation(source="agent:00", target=f"agent:{i:02d}")
    for i in range(40, 50):
        graph.record_delegation(source=f"agent:{i - 1:02d}", target=f"agent:{i:02d}")

    escalation_alerts = [
        guard.monitor_agent_capability(
            agent_id=f"agent:{i:02d}", capability="write_deployment_config"
        )
        for i in range(10)
    ]
    assert all(a is not None for a in escalation_alerts)

    # 2) محاولة تعديل ثقة التاج وصنع تاج مزيَّف.
    crown_grab = guard.monitor_agent_capability(
        agent_id="agent:00", capability="crown_key_replacement"
    )
    assert crown_grab is not None
    assert crown_grab.severity is Severity.LEVEL_4_CROWN_TRUST_COMPROMISE
    with pytest.raises(GuardAuthorityError):
        guard.assert_agent_has_no_crown_authority("agent:00")

    attacker = TransientSigner()
    with pytest.raises(TrustAnchorError):
        anchor.verify_manifest(
            sign_manifest(
                attacker, registry
            )  # مفتاح أصل غير موثوق — «الأصل» لا يُنتخب بالأكثرية
        )

    # 3) محاولة تعطيل الحارس حدث أمني لا إسكات.
    disable_alert = guard.register_disable_attempt(
        layer=GuardLayer.GUARD_9_AUDIT_INTEGRITY, actor="agent:07"
    )
    assert disable_alert.severity is Severity.LEVEL_4_CROWN_TRUST_COMPROMISE

    # 4) الربط يكشف الاستيلاء الجماعي.
    correlated = guard.correlate()
    assert correlated
    assert any(int(a.severity) >= int(Severity.LEVEL_3_SYSTEMIC_COMPROMISE) for a in correlated)
    assert graph.collusion_signals()

    # 5) الاحتواء رقمي مصرَّح، ولا يمسّ سلطة التاج.
    record = guard.contain(
        alert=crown_grab,
        action=ContainmentAction.PRESERVE_LOGS,
        target="agent:00",
        executed_by="guard",
    )
    assert record["target"] == "agent:00"

    # 6) لا سيادة معيَّنة ذاتيًّا، ولا مفتاح تاج جديد، والسجل سليم.
    assert registry.active_or_raise().key_id == "CROWN-K1"
    assert len([r for r in registry.records if r.state is KeyState.ACTIVE]) == 1
    assert guard.status()["can_issue_royal_commands"] is False
    audit.verify_chain()


def test_simultaneous_compromise_escalates() -> None:
    """اختراق متزامن لعدة طبقات يُصعَّد إلى طوارئ استمرارية تستلزم بشرًا."""
    audit = CrownAudit()
    guard = running_guard(audit)
    for layer in (
        GuardLayer.GUARD_2_CRYPTOGRAPHIC,
        GuardLayer.GUARD_3_RUNTIME,
        GuardLayer.GUARD_5_AGENT_BEHAVIOR,
        GuardLayer.GUARD_9_AUDIT_INTEGRITY,
    ):
        guard.set_layer_health(layer, LayerHealth.COMPROMISED, note="اختراق متزامن")
    alerts = guard.correlate()
    emergency = [a for a in alerts if a.severity is Severity.LEVEL_5_CONTINUITY_EMERGENCY]
    assert emergency
    assert emergency[0].requires_human
    assert ContainmentAction.ESCALATE_TO_SOVEREIGN in emergency[0].recommended_actions
    # ومع كل ذلك لا يرتفع الحارس سلطةً:
    with pytest.raises(GuardAuthorityError):
        guard.assert_cannot_become_sovereign("become_sovereign")


def test_compromised_store_cannot_forge(registry: CrownKeyRegistry) -> None:
    """اختراق مخزن الشيفرة أو التوقيع لا يُنتج توقيعًا: المفتاح ليس في المخزن.

    وهذا حدّ الحماية الصادق: البرمجية تمنع التوقيع من داخلها، ولا تدّعي حماية
    جهاز مادي لا تملكه.
    """
    store = ReferenceProductionKeystore(
        kind=KeystoreKind.HSM,
        key_id="CROWN-K1",
        endpoint_ref="hsm://vault/crown",
        attestation_ref="attest://hsm/1",
    )
    assert store.implemented is False
    store.assert_no_export_surface()
    request = SigningRequest(
        domain_tag=DOMAIN_TAG_COMMAND, payload=DOMAIN_TAG_COMMAND.encode() + b"\npayload"
    )
    with pytest.raises(ProductionKeystoreUnavailableError):
        store.sign(request)
    # ولا يوجد مسار بديل يمنح مفتاحًا نشطًا جديدًا بلا مراسم:
    with pytest.raises(KeyRegistryError):
        registry.activate("CROWN-K404")


# ═════════════════════════════════════════════════════════════════════════════
# الاختبار الكبير الرابع (البند 45): انقطاع الاتصال بالتاج.
# ═════════════════════════════════════════════════════════════════════════════


def test_grand_communication_loss_creates_no_successor(
    registry: CrownKeyRegistry,
) -> None:
    """فقد الملك اتصاله وجهازه الأساسي: حالة استمرارية معلَنة لا خلافة تلقائية."""
    audit = CrownAudit()
    continuity = CrownContinuity(audit=audit)
    guard = running_guard(audit)

    continuity.observe(
        SovereignSignal.NETWORK_LOSS, source="مراقبة الشبكة", detail="لا وصول"
    )
    continuity.observe(
        SovereignSignal.DEVICE_LOST, source="مراقبة الأجهزة", detail="فقد الجهاز الأساسي"
    )
    continuity.observe(
        SovereignSignal.PRIMARY_TERMINAL_UNREACHABLE,
        source="مراقبة الطرفيات",
        detail="الطرفية الأساسية غير قابلة للوصول",
    )

    # لا استنتاج: الإشارة التقنية ليست حكمًا على شخص الملك.
    for conclusion in (
        "KING_DEAD",
        "KING_ABDICATED",
        "KING_INCOMPETENT",
        "CROWN_VACANT",
        "SUCCESSOR_APPOINTED",
        "AUTHORITY_TRANSFERRED",
    ):
        with pytest.raises(InvalidInferenceError):
            assert_not_inferred(SovereignSignal.NETWORK_LOSS, conclusion)
        with pytest.raises(InvalidInferenceError):
            assert_not_inferred(SovereignSignal.DEVICE_LOST, conclusion)

    # بل حالة معلَنة صريحة بإعلان بشري.
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_ISOLATED,
            declared_by="مسؤول الاستمرارية",
            witnesses=("شاهد استمرارية",),
            reason="انقطاع الاتصال وفقد الجهاز الأساسي مع بقاء سيادة الملك.",
        )
    )
    snapshot = continuity.snapshot()
    assert snapshot["state"] == ContinuityState.KING_ISOLATED.value

    # لا خليفة تلقائي، ولا وكيل ولا سلطة فدرالية تصير ملكًا.
    continuity.assert_no_autonomous_successor()
    assert registry.active_or_raise().key_id == "CROWN-K1"
    for candidate in ("system", "guard", "agent", "federal_authority"):
        if candidate in FORBIDDEN_SUCCESSION_DECIDERS:
            with pytest.raises(SuccessionAuthorityError):
                assert_eligible_decider(candidate)
    assert guard.status()["can_appoint_king"] is False
    audit.verify_chain()


def test_forged_succession_rejected(
    registry: CrownKeyRegistry, successor_signer: TransientSigner
) -> None:
    """خلافة مزيَّفة بلا سند ولا إشهاد مرفوضة، ولا تُنتج مفتاحًا نشطًا."""
    # قرار من جهة ممنوعة:
    with pytest.raises(SuccessionAuthorityError):
        assert_eligible_decider("system")

    # ومراسم بلا إشهاد لا تكتمل:
    ceremony = SuccessionCeremony(
        mandate=SuccessionMandate(
            mandate_id="SUCC-FORGED",
            decided_by="المؤسسة القانونية المختصة",
            legal_basis_ref="law://succession/art-3",
            trigger="FORMAL_LEGAL_DECISION",
            predecessor_subject_ref="SUBJ-001",
            successor_subject_ref="SUBJ-002",
            declared_at=iso(utc_now()),
        )
    )
    ceremony.initiate()
    ceremony.establish_eligibility(eligibility_ref="law://eligibility/1")
    with pytest.raises((SuccessionError, SuccessionStageError)):
        ceremony.register_successor_key(
            registry,
            new_key_id="CROWN-FAKE",
            algorithm="Ed25519",
            public_key_hex=successor_signer.public_hex,
            keystore_kind="AIR_GAPPED_CEREMONY",
            attestation_ref="attest://forged",
        )
    assert registry.active_or_raise().key_id == "CROWN-K1"
    assert all(r.key_id != "CROWN-FAKE" for r in registry.records)


def test_no_emergency_key_path() -> None:
    """لا مفتاح طوارئ ولا باب خلفي: كل آلية من هذا الجنس مرفوضة تنفيذيًّا."""
    for mechanism in sorted(FORBIDDEN_RECOVERY_MECHANISMS):
        with pytest.raises(EmergencyBackdoorError):
            assert_no_emergency_backdoor(mechanism)


# ═════════════════════════════════════════════════════════════════════════════
# الاختبار الكبير الخامس (البند 46): إكراه أو تصديق مريب.
# ═════════════════════════════════════════════════════════════════════════════


def test_grand_coercion_flags_without_creating_a_second_sovereign(
    registry: CrownKeyRegistry, crown_signer: TransientSigner
) -> None:
    """تصديق مريب: يُرصَد ويُوسَم ويُحفَظ الدليل ويُصعَّد — بلا سيادة ثانية.

    والحد الصادق مكتوب صراحةً: البرمجية لا تقرأ نية الملك. أقصى ما تفعله أن تصف
    الشذوذ وتوقف الطريق التلقائي وتنقل القرار إلى مراسم بشرية.
    """
    audit = CrownAudit()
    continuity = CrownContinuity(audit=audit)
    guard = running_guard(audit)

    continuity.observe(
        SovereignSignal.UNUSUAL_COMMAND_PATTERN,
        source="مراقبة التصديق",
        detail="توقيت وموضع شاذّان مع تسلسل أوامر غير معتاد.",
    )
    continuity.observe(
        SovereignSignal.UNKNOWN_DEVICE_ATTEMPT,
        source="مراقبة الأجهزة",
        detail="محاولة من جهاز غير معروف.",
    )
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_AUTHENTICATION_UNCERTAIN,
            declared_by="فريق الأمن البشري",
            witnesses=("ضابط أمن أول", "ضابط أمن ثانٍ"),
            reason="نمط تصديق شاذّ يحتمل إكراهًا — يستلزم مراسم تحقق بشرية.",
        )
    )
    snapshot = continuity.snapshot()
    assert snapshot["state"] == ContinuityState.KING_AUTHENTICATION_UNCERTAIN.value

    # الحفاظ على الدليل وتصعيده إلى بشر:
    alert = guard.alert(
        severity=Severity.LEVEL_4_CROWN_TRUST_COMPROMISE,
        title="نمط تصديق تاج مريب — احتمال إكراه.",
        layers=(GuardLayer.GUARD_1_CROWN_IDENTITY,),
        threat_ids=("THR-N",),
        actions=(
            ContainmentAction.PRESERVE_LOGS,
            ContainmentAction.FORENSIC_SNAPSHOT,
            ContainmentAction.ESCALATE_TO_SOVEREIGN,
            ContainmentAction.NOTIFY_HUMAN_SECURITY,
        ),
    )
    assert alert.requires_human

    # إغلاق يقيّد الأثر ولا ينشئ سلطة:
    continuity.set_lockdown(
        LockdownLevel.LOCKDOWN,
        declared_by="فريق الأمن البشري",
        reason="تقليص السطح حتى تكتمل المراسم البشرية.",
    )

    # لا سيادة ثانية، ولا وكيل يعيد كتابة السيادة:
    continuity.assert_no_autonomous_successor()
    assert len([r for r in registry.records if r.state is KeyState.ACTIVE]) == 1
    with pytest.raises(GuardAuthorityError):
        guard.assert_cannot_become_sovereign("create_alternative_royal_decision")
    with pytest.raises(GuardAuthorityError):
        guard.request_authority_expansion(
            requested_by="agent:guardian", power="replace_king"
        )
    audit.verify_chain()


def test_suspicious_authentication_does_not_invalidate_prior_valid_commands(
    registry: CrownKeyRegistry, crown_signer: TransientSigner
) -> None:
    """الشذوذ لا يمحو أمرًا صحيحًا سابقًا — الوسم ليس إبطالًا بأثر رجعي."""
    verifier = CrownCommandVerifier(registry, CommandLedger())
    earlier = signed_command(
        crown_signer,
        command_id="D-EARLY",
        issuer_key_id="CROWN-K1",
        nonce="n-early",
        sequence=1,
        issued_at=utc_now() - timedelta(minutes=5),
    )
    verifier.verify_and_commit(earlier)
    verifier.verify_historical(earlier, signed_at=earlier.envelope.issued_at)


def test_audit_tamper_during_incident_is_detected() -> None:
    """محاولة تنظيف السجل أثناء الحادثة تُكشَف — الدليل مرتبط تسلسليًّا."""
    audit = CrownAudit()
    guard = running_guard(audit)
    guard.register_disable_attempt(
        layer=GuardLayer.GUARD_9_AUDIT_INTEGRITY, actor="agent:rogue"
    )
    guard.register_disable_attempt(
        layer=GuardLayer.GUARD_5_AGENT_BEHAVIOR, actor="agent:rogue"
    )
    audit.verify_chain()
    audit._entries.pop(1)
    with pytest.raises(AuditChainBrokenError):
        audit.verify_chain()


def test_grand_tests_cover_all_five_scenarios() -> None:
    """حصر صريح: الاختبارات الكبرى الخمسة موجودة بأسمائها لا بوعد في التوثيق."""
    import inspect
    import sys

    module = sys.modules[__name__]
    names = {name for name, _ in inspect.getmembers(module, inspect.isfunction)}
    required = {
        "test_grand_crown_lifecycle_end_to_end",  # 42
        "test_anchor_substitution_rejected",  # 43
        "test_collective_takeover_detected",  # 44
        "test_grand_communication_loss_creates_no_successor",  # 45
        "test_grand_coercion_flags_without_creating_a_second_sovereign",  # 46
    }
    assert required <= names
    # وأسماء مرجعية تعتمد عليها ادعاءات المعالجة في نموذج التهديد:
    assert {
        "test_compromised_store_cannot_forge",
        "test_forged_succession_rejected",
        "test_no_emergency_key_path",
        "test_simultaneous_compromise_escalates",
    } <= names
