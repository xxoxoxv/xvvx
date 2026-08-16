"""الهدف: اختبار حدود الهوية والخلافة والاسترداد — رفض القيود الناقصة والمراحل الملغاة.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المسار الشرعي مُختبَر في الملفات الأخرى. وهنا نقصد الحواف: سند بلا مُسمّى، ومخطط
لا يُستَرد به أبدًا، ومراسم مُلغاة يُحاول أحدهم استئنافها. فحدود النظام هي حيث
يُختبر صدقُه.
"""

from __future__ import annotations

import pytest

from core.crown.identity import (
    AuthenticationAssessment,
    CrownCommandIdentity,
    CrownCryptographicIdentity,
    CrownDeviceIdentity,
    CrownInstitutionalIdentity,
    FactorEvidence,
    FactorKind,
    HumanSovereignIdentity,
    IdentityBinding,
    IdentityConflationError,
    IdentityError,
    IdentityGraph,
    SigningCeremonyPolicy,
    assess,
)
from core.crown.key_registry import CrownKeyRegistry
from core.crown.recovery import (
    CrownRecovery,
    QuorumError,
    RecoveryCeremony,
    RecoveryError,
    RecoveryScheme,
    RecoveryStage,
    RecoveryStageError,
    RecoveryTrigger,
    ShareHolderDescriptor,
)
from core.crown.succession import (
    CrownSuccession,
    SuccessionError,
    SuccessionMandate,
    SuccessionStage,
    SuccessionStageError,
    SuccessionWitness,
)
from tests.crown.conftest import TransientSigner, iso, utc_now


# ─────────────────────────────────────────────────────────────────────────────
# الهوية: قيود ناقصة، وخلط هويات، وتقييم مصادقة.
# ─────────────────────────────────────────────────────────────────────────────


def test_identity_objects_reject_empty_identifiers() -> None:
    """كل هوية تاج بلا معرّف مرفوضة — هوية بلا معرّف ليست هوية."""
    with pytest.raises(IdentityError):
        HumanSovereignIdentity(subject_ref="")
    with pytest.raises(IdentityError):
        CrownInstitutionalIdentity(crown_id="", established_at=iso(utc_now()))
    with pytest.raises(IdentityError):
        CrownCryptographicIdentity(
            key_id="", algorithm="Ed25519", public_key_hex="ab", version=1
        )
    with pytest.raises(IdentityError):
        CrownDeviceIdentity(device_id="")
    with pytest.raises(IdentityError):
        CrownCommandIdentity(command_id="", nonce="n", sequence=1)


def test_cryptographic_identity_rejects_zero_version_and_exposes_fingerprint() -> None:
    """نسخة المفتاح تبدأ من واحد، والبصمة مشتقّة لا مُعلَنة يدويًّا."""
    signer = TransientSigner()
    with pytest.raises(IdentityError):
        CrownCryptographicIdentity(
            key_id="CROWN-K1",
            algorithm="Ed25519",
            public_key_hex=signer.public_hex,
            version=0,
        )
    identity = CrownCryptographicIdentity(
        key_id="CROWN-K1",
        algorithm="Ed25519",
        public_key_hex=signer.public_hex,
        version=1,
    )
    assert len(identity.fingerprint) == 64
    assert identity.fingerprint != signer.public_hex


def test_command_identity_rejects_negative_sequence() -> None:
    """تسلسل الأمر لا يكون سالبًا — والنونس شرط لمنع الإعادة."""
    with pytest.raises(IdentityError):
        CrownCommandIdentity(command_id="C1", nonce="n", sequence=-1)
    with pytest.raises(IdentityError):
        CrownCommandIdentity(command_id="C1", nonce="", sequence=1)


def test_identity_graph_rejects_unknown_objects_and_conflation() -> None:
    """الرسم يرفض ما ليس هوية تاج، ويرفض تسجيل هويتين من نوع واحد."""
    graph = IdentityGraph()
    with pytest.raises(IdentityError):
        graph.register(object())
    graph.register(HumanSovereignIdentity(subject_ref="الملك"))
    with pytest.raises(IdentityConflationError):
        graph.register(HumanSovereignIdentity(subject_ref="شخص آخر"))


def test_identity_graph_binding_requires_both_kinds_registered() -> None:
    """الربط لا يُنشئ هويات — يربط مسجَّلتين أو يُرفَض."""
    graph = IdentityGraph()
    human = HumanSovereignIdentity(subject_ref="الملك")
    graph.register(human)
    binding = IdentityBinding(
        left_kind=human.kind,
        left_id="الملك",
        right_kind="crown_cryptographic",
        right_id="CROWN-K1",
        basis="مراسم موثَّقة",
    )
    with pytest.raises(IdentityError):
        graph.bind(binding)

    signer = TransientSigner()
    crypto = CrownCryptographicIdentity(
        key_id="CROWN-K1",
        algorithm="Ed25519",
        public_key_hex=signer.public_hex,
        version=1,
    )
    graph.register(crypto)
    graph.bind(
        IdentityBinding(
            left_kind=human.kind,
            left_id="الملك",
            right_kind=crypto.kind,
            right_id="CROWN-K1",
            basis="مراسم موثَّقة",
        )
    )
    assert len(graph.bindings) == 1
    assert graph.get(human.kind) is human
    assert graph.get("نوع غير مسجَّل") is None
    assert graph.identifiers()[crypto.kind] == "CROWN-K1"
    assert graph.missing_kinds()


def test_identity_graph_assert_distinct_detects_shared_identifier() -> None:
    """معرّف واحد لهويتين خلطٌ — الهوية البشرية ليست الهوية التعمية."""
    graph = IdentityGraph()
    graph.register(HumanSovereignIdentity(subject_ref="CROWN-1"))
    graph.register(
        CrownInstitutionalIdentity(crown_id="CROWN-1", established_at=iso(utc_now()))
    )
    with pytest.raises(IdentityConflationError):
        graph.assert_distinct()


def test_assessment_flags_suspicion_on_partial_establishment() -> None:
    """هوية بلا حضور، أو حضور بلا نية، أو شذوذ — كلها حالات ريبة معلَنة."""
    now = iso(utc_now())
    identity_only = AuthenticationAssessment(
        identity_established=True,
        presence_established=False,
        intent_established=False,
        authority_is_crown=True,
    )
    assert identity_only.suspicious is True

    presence_without_intent = AuthenticationAssessment(
        identity_established=True,
        presence_established=True,
        intent_established=False,
        authority_is_crown=True,
    )
    assert presence_without_intent.suspicious is True

    clean = AuthenticationAssessment(
        identity_established=True,
        presence_established=True,
        intent_established=True,
        authority_is_crown=True,
        factors=(
            FactorEvidence(
                kind=FactorKind.POSSESSION,
                satisfied=True,
                source="hardware_security_module_slot",
                observed_at=now,
            ),
        ),
    )
    assert clean.suspicious is False
    assert clean.as_dict()["identity_established"] is True

    with_anomaly = assess(
        (
            FactorEvidence(
                kind=FactorKind.BIOMETRIC,
                satisfied=True,
                source="attested_capture_session",
                observed_at=now,
                anomaly="جهاز غير مُشهَد",
            ),
        ),
        authority_is_crown=True,
    )
    assert with_anomaly.suspicious is True


def test_signing_policy_refuses_biometric_as_sole_factor() -> None:
    """القياس الحيوي وحده لا يكفي لمراسم توقيع — سياسة مُنفَّذة لا نصيحة."""
    now = iso(utc_now())
    assessment = assess(
        (
            FactorEvidence(
                kind=FactorKind.BIOMETRIC,
                satisfied=True,
                source="attested_capture_session",
                observed_at=now,
            ),
        ),
        authority_is_crown=True,
    )
    violations = SigningCeremonyPolicy().evaluate(assessment)
    assert violations
    assert assessment.is_multi_factor is False
    assert assessment.factor_count == 1


# ─────────────────────────────────────────────────────────────────────────────
# الخلافة.
# ─────────────────────────────────────────────────────────────────────────────


def _mandate(**overrides) -> SuccessionMandate:
    data = {
        "mandate_id": "MAN-1",
        "decided_by": "HUMAN_KING",
        "legal_basis_ref": "docs/constitution/succession.md",
        "trigger": "CONFIRMED_DEATH",
        "predecessor_subject_ref": "الملك الأول",
        "successor_subject_ref": "الملك الثاني",
    }
    data.update(overrides)
    return SuccessionMandate(**data)


def _witnesses() -> tuple[SuccessionWitness, ...]:
    return tuple(
        SuccessionWitness(
            witness_id=f"W{i}", role="شاهد دستوري", verification_ref=f"ref-{i}"
        )
        for i in range(1, 4)
    )


def test_witness_requires_identity_and_role() -> None:
    """شاهد بلا هوية أو بلا صفة أو بلا مرجع تحقق لا يُعتدّ به."""
    with pytest.raises(SuccessionError):
        SuccessionWitness(witness_id="", role="شاهد", verification_ref="r")
    with pytest.raises(SuccessionError):
        SuccessionWitness(witness_id="W1", role="شاهد", verification_ref="")


def test_mandate_validation_rejects_incoherent_succession() -> None:
    """سند بلا معرّف، أو بلا خلف، أو بخلف هو السابق نفسه — مرفوض."""
    with pytest.raises(SuccessionError):
        _mandate(mandate_id="")
    with pytest.raises(SuccessionError):
        _mandate(successor_subject_ref="")
    with pytest.raises(SuccessionError):
        _mandate(successor_subject_ref="الملك الأول")
    assert _mandate().as_dict()["mandate_id"] == "MAN-1"


def test_aborted_succession_cannot_be_resumed() -> None:
    """مراسم مُلغاة لا تُستأنف — تُبدأ مراسم جديدة بسند جديد."""
    ceremony = CrownSuccession().open_ceremony(_mandate())
    with pytest.raises(SuccessionError):
        ceremony.abort(reason="")
    ceremony.abort(reason="ظهر السابق حيًّا.")
    assert ceremony.stage is SuccessionStage.ABORTED
    with pytest.raises(SuccessionStageError):
        ceremony.establish_eligibility(eligibility_ref="ref")
    with pytest.raises(SuccessionStageError):
        ceremony.confirm_witnesses(_witnesses())


def test_succession_stage_references_require_evidence() -> None:
    """كل مرحلة تطلب مرجعًا موثَّقًا: أهلية، وتحديث مرساة، وشهودًا كفاية."""
    ceremony = CrownSuccession().open_ceremony(_mandate())
    with pytest.raises(SuccessionError):
        ceremony.establish_eligibility(eligibility_ref="")
    ceremony.establish_eligibility(eligibility_ref="docs/constitution/eligibility.md")
    with pytest.raises(SuccessionError):
        ceremony.confirm_witnesses(_witnesses()[:2])
    ceremony.confirm_witnesses(_witnesses())
    with pytest.raises(SuccessionStageError):
        ceremony.update_trust_anchor(anchor_update_ref="ref")


def test_completion_requires_the_full_sequence(
    registry: CrownKeyRegistry, successor_signer: TransientSigner
) -> None:
    """الإتمام آخر المراحل لا أولها، ولا يُقبل تحديث مرساة بلا مرجع."""
    succession = CrownSuccession()
    ceremony = succession.open_ceremony(_mandate())
    with pytest.raises(SuccessionStageError):
        ceremony.complete()
    ceremony.establish_eligibility(eligibility_ref="docs/constitution/eligibility.md")
    ceremony.confirm_witnesses(_witnesses())
    ceremony.register_successor_key(
        registry,
        new_key_id="CROWN-K2",
        algorithm="Ed25519",
        public_key_hex=successor_signer.public_hex,
        keystore_kind="AIR_GAPPED_CEREMONY",
        attestation_ref="attest-2",
    )
    with pytest.raises(SuccessionError):
        ceremony.update_trust_anchor(anchor_update_ref="")
    ceremony.update_trust_anchor(anchor_update_ref="ceremony-anchor-2")
    ceremony.complete()
    assert ceremony.stage is SuccessionStage.COMPLETED
    succession.record_stage(ceremony, actor="أمين السجل")
    assert succession.active_ceremony is None or succession.history
    report = succession.lineage_report(registry)
    assert report["succession_count"] >= 1


def test_unknown_stage_transition_is_rejected() -> None:
    """قفزة إلى مرحلة غير معروفة مرفوضة — التسلسل معلَن لا مفتوح."""
    ceremony = CrownSuccession().open_ceremony(_mandate())
    ceremony.stage = "MARHALA_MAJHULA"  # type: ignore[assignment]
    with pytest.raises(SuccessionStageError):
        ceremony.establish_eligibility(eligibility_ref="ref")


# ─────────────────────────────────────────────────────────────────────────────
# الاسترداد.
# ─────────────────────────────────────────────────────────────────────────────


def _holders(count: int = 5, locations: int = 3) -> tuple[ShareHolderDescriptor, ...]:
    return tuple(
        ShareHolderDescriptor(
            holder_id=f"H{i}",
            role="حامل حصة",
            location_ref=f"موضع-{i % locations}",
            verification_ref=f"ref-{i}",
        )
        for i in range(count)
    )


def _scheme(**overrides) -> RecoveryScheme:
    data = {
        "quorum": 3,
        "holders": _holders(),
        "printed_verification_ref": "طبعة ورقية موثَّقة",
        "offline_root_ref": "جذر خارج الشبكة",
        "documentation_ref": "docs/security/CROWN_SOVEREIGNTY_PROTECTION.md",
    }
    data.update(overrides)
    return RecoveryScheme(**data)


def test_share_holder_requires_identity_and_cold_storage() -> None:
    """حامل حصة بلا معرّف أو بلا حرز بارد لا يُعتدّ به."""
    with pytest.raises(RecoveryError):
        ShareHolderDescriptor(
            holder_id="", role="حامل", location_ref="م", verification_ref="r"
        )
    with pytest.raises(RecoveryError):
        ShareHolderDescriptor(
            holder_id="H1",
            role="حامل",
            location_ref="م",
            verification_ref="r",
            cold_storage=False,
        )


def test_scheme_rejects_impossible_or_single_point_quorums() -> None:
    """نصاب أكبر من الحاملين لا يُستَرد به أبدًا، ونصاب يساويهم يفقد الاحتمال."""
    with pytest.raises(QuorumError):
        _scheme(quorum=1)
    with pytest.raises(QuorumError):
        _scheme(quorum=9)
    with pytest.raises(QuorumError):
        _scheme(quorum=5, holders=_holders(count=5))
    with pytest.raises(QuorumError):
        _scheme(holders=_holders(count=3))
    with pytest.raises(RecoveryError):
        _scheme(holders=_holders(count=5, locations=1))
    assert _scheme().as_dict()["quorum"] == 3
    assert _scheme().distinct_locations >= 3


def test_recovery_requires_a_human_declarer_and_documented_refs() -> None:
    """الاسترداد يُعلنه بشر، وكل مرحلة تطلب مرجعًا موثَّقًا."""
    with pytest.raises(RecoveryError):
        RecoveryCeremony(
            scheme=_scheme(),
            trigger=RecoveryTrigger.SIGNING_DEVICE_DESTROYED,
            declared_by="",
        )
    ceremony = CrownRecovery().open_ceremony(
        scheme=_scheme(),
        trigger=RecoveryTrigger.SIGNING_DEVICE_DESTROYED,
        declared_by="الملك",
    )
    with pytest.raises(QuorumError):
        ceremony.assemble(("H0", "H1", "H404"))
    ceremony.assemble(("H0", "H1"))
    with pytest.raises(QuorumError):
        # الحاضرون أقل من النصاب: التجميع لا يُغني عن التحقق.
        ceremony.verify_quorum()
    ceremony.present_holders = ["H0", "H1", "H2"]
    ceremony.verify_quorum()
    with pytest.raises(RecoveryError):
        ceremony.perform_offline_ceremony(ceremony_ref="")
    ceremony.perform_offline_ceremony(ceremony_ref="مراسم خارج الشبكة #1")
    with pytest.raises(RecoveryError):
        ceremony.reverify_anchor(verification_ref="")
    ceremony.reverify_anchor(verification_ref="بصمة مطبوعة مطابقة")
    ceremony.complete()
    assert ceremony.stage is RecoveryStage.COMPLETED
    ceremony.assert_not_succession()
    assert ceremony.as_dict()["stage"] == RecoveryStage.COMPLETED.value


def test_aborted_recovery_cannot_be_resumed() -> None:
    """مراسم استرداد مُلغاة لا تُستأنف، وإلغاؤها بلا سبب مكتوب مرفوض."""
    recovery = CrownRecovery()
    ceremony = recovery.open_ceremony(
        scheme=_scheme(),
        trigger=RecoveryTrigger.FACILITY_INACCESSIBLE,
        declared_by="الملك",
    )
    with pytest.raises(RecoveryError):
        ceremony.abort(reason="")
    ceremony.abort(reason="عاد الموضع متاحًا.")
    assert ceremony.stage is RecoveryStage.ABORTED
    with pytest.raises(RecoveryStageError):
        ceremony.assemble(("H0", "H1", "H2"))
    recovery.record_stage(ceremony, actor="أمين السجل")
    assert recovery.history


def test_recovery_out_of_order_completion_is_rejected() -> None:
    """الإتمام قبل مراسم خارج الشبكة وإعادة تحقق المرساة مرفوض."""
    ceremony = CrownRecovery().open_ceremony(
        scheme=_scheme(),
        trigger=RecoveryTrigger.PRIMARY_ENVIRONMENT_LOST,
        declared_by="الملك",
    )
    with pytest.raises(RecoveryStageError):
        ceremony.complete()
    with pytest.raises(RecoveryStageError):
        ceremony.reverify_anchor(verification_ref="ref")


def test_declaring_twice_is_rejected() -> None:
    """إعلان مراسم مُعلَنة مرتين تكرارٌ يُخفي حالًا — مرفوض."""
    ceremony = CrownRecovery().open_ceremony(
        scheme=_scheme(),
        trigger=RecoveryTrigger.KEY_COMPROMISE_CONFIRMED,
        declared_by="الملك",
    )
    with pytest.raises(RecoveryStageError):
        ceremony.declare()
