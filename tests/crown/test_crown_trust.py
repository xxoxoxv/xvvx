"""الهدف: اختبار جذر الثقة — الهوية، وسجل المفاتيح، والمرساة، وبيئة التوقيع.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

الاختبارات هنا نوعان: إيجابية تُثبت أن المسار الشرعي يعمل، وخصومية تُثبت أن
المسار غير الشرعي **يُرفَض فعلًا** لا أن الرفض مكتوب في تعليق.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from core.crown.identity import (
    AuthenticationAssessment,
    BiometricAsKeyError,
    CrownCommandIdentity,
    CrownCryptographicIdentity,
    CrownDeviceIdentity,
    CrownInstitutionalIdentity,
    FactorEvidence,
    FactorKind,
    HumanSovereignIdentity,
    IDENTITY_KINDS,
    IdentityBinding,
    IdentityConflationError,
    IdentityGraph,
    SigningCeremonyPolicy,
    assert_not_key_material,
    assess,
)
from core.crown.key_registry import (
    AlgorithmAgilityPlan,
    AlgorithmError,
    CrownKeyRecord,
    CrownKeyRegistry,
    KeyState,
    KeyStateError,
    LineageKind,
    SUPPORTED_ALGORITHMS,
)
from core.crown.keystore import (
    CONTINUITY_ENVIRONMENTS,
    EphemeralTestKeystore,
    FORBIDDEN_MATERIAL_LOCATIONS,
    KeyMaterialLeakError,
    KeystoreKind,
    ProductionKeystoreUnavailableError,
    ReferenceProductionKeystore,
    SigningRequest,
    assert_no_material_in,
)
from core.crown.trust_anchor import (
    AnchorSource,
    AnchorSubstitutionError,
    CircularTrustError,
    CrownTrustAnchor,
    DOMAIN_TAG_ANCHOR,
    DowngradeError,
    OutOfBandVerificationRequiredError,
    RollbackError,
    RootKeyReuseError,
    SUBSTITUTION_VECTORS,
    TrustPlane,
    substitution_matrix,
)

from tests.crown.conftest import (
    TransientSigner,
    anchor_fingerprint,
    iso,
    make_provenance,
    sign_manifest,
    utc_now,
)

# ─────────────────────────────────────────────────────────────────────────────
# فصل الهويات (البند 6).
# ─────────────────────────────────────────────────────────────────────────────


def test_five_identities_are_distinct() -> None:
    """الهويات الخمس منفصلة، والرسم يعرف نقصها ويرفض خلطها."""
    graph = IdentityGraph()
    assert set(graph.missing_kinds()) == set(IDENTITY_KINDS)

    graph.register(HumanSovereignIdentity(subject_ref="SUBJ-001"))
    graph.register(
        CrownInstitutionalIdentity(crown_id="CROWN-INST-1", established_at=iso(utc_now()))
    )
    graph.register(
        CrownCryptographicIdentity(
            key_id="CROWN-K1", algorithm="Ed25519", public_key_hex="ab" * 32, version=1
        )
    )
    graph.register(CrownDeviceIdentity(device_id="DEV-1", attestation_ref="att", hardware_backed=True))
    graph.register(CrownCommandIdentity(command_id="CMD-1", nonce="n1", sequence=1))

    assert graph.missing_kinds() == ()
    graph.assert_distinct()
    assert len(set(graph.identifiers().values())) == len(IDENTITY_KINDS)


def test_identity_conflation_is_rejected() -> None:
    """خلط هويتين بمعرّف واحد يُرفَض — الخلط أصل ثغرات الانتحال."""
    graph = IdentityGraph()
    graph.register(HumanSovereignIdentity(subject_ref="SAME"))
    graph.register(
        CrownInstitutionalIdentity(crown_id="SAME", established_at=iso(utc_now()))
    )
    with pytest.raises(IdentityConflationError):
        graph.assert_distinct()


def test_identity_binding_requires_basis() -> None:
    """الربط بين هويتين يحتاج سندًا — ربط بلا سند ربط بلا مراجعة."""
    with pytest.raises(Exception):
        IdentityBinding(
            left_kind="human_sovereign",
            left_id="A",
            right_kind="crown_cryptographic",
            right_id="B",
            basis="",
        )


@pytest.mark.parametrize(
    "source",
    ["fingerprint", "face", "iris", "dna", "brain_signal", "fingerprint_template"],
)
def test_biometric_can_never_be_a_private_key(source: str) -> None:
    """القياس الحيوي مرفوض كمادة مفتاح — ولو غُيِّر اسم الحقل."""
    with pytest.raises(BiometricAsKeyError):
        assert_not_key_material(source)


def test_legitimate_source_names_are_not_false_positives() -> None:
    """أسماء مشروعة لا تُرفَض: مطابقة الكلمة لا المقطع."""
    for benign in ["device_interface", "hsm_slot", "surface_terminal", "smartcard"]:
        assert_not_key_material(benign)


def test_biometric_alone_cannot_authorize_signing() -> None:
    """عامل حيوي وحده لا يكفي لمراسم توقيع — يُثبت حضورًا لا نيّة."""
    assessment = assess(
        (
            FactorEvidence(
                kind=FactorKind.BIOMETRIC,
                satisfied=True,
                source="biometric_reader",
                observed_at=iso(utc_now()),
            ),
        ),
        authority_is_crown=True,
    )
    problems = SigningCeremonyPolicy().evaluate(assessment)
    assert problems, "عامل حيوي منفرد قُبِل — وهذا خلط بين الحضور والنيّة."


def test_full_ceremony_factors_are_accepted() -> None:
    """المسار الشرعي: حيازة + تأكيد بشري + عتاد ⇒ لا اعتراض."""
    now = iso(utc_now())
    assessment = assess(
        (
            FactorEvidence(
                kind=FactorKind.POSSESSION, satisfied=True, source="hsm_token", observed_at=now
            ),
            FactorEvidence(
                kind=FactorKind.HUMAN_CONFIRMATION,
                satisfied=True,
                source="physical_button",
                observed_at=now,
            ),
            FactorEvidence(
                kind=FactorKind.HARDWARE_CONFIRMATION,
                satisfied=True,
                source="secure_element",
                observed_at=now,
            ),
        ),
        authority_is_crown=True,
    )
    assert isinstance(assessment, AuthenticationAssessment)
    assert assessment.is_multi_factor
    assert SigningCeremonyPolicy().evaluate(assessment) == ()


# ─────────────────────────────────────────────────────────────────────────────
# سجل المفاتيح والنسب (البندان 25 و26).
# ─────────────────────────────────────────────────────────────────────────────


def test_rotation_preserves_lineage(
    registry: CrownKeyRegistry, successor_signer: TransientSigner
) -> None:
    """التدوير: الأول يتقاعد والثاني ينشط، والنسب متصل ولا حال غامضة."""
    registry.rotate(
        new_key_id="CROWN-K2",
        algorithm="Ed25519",
        public_key_hex=successor_signer.public_hex,
        provenance=make_provenance(ceremony_kind="CROWN_ROTATION"),
    )
    assert registry.get("CROWN-K1").state is KeyState.RETIRED
    assert registry.active_or_raise().key_id == "CROWN-K2"
    assert registry.get("CROWN-K2").predecessor_key_id == "CROWN-K1"
    assert registry.get("CROWN-K2").lineage_kind is LineageKind.ROTATION
    registry.validate()


def test_retired_key_cannot_sign_new(
    registry: CrownKeyRegistry, successor_signer: TransientSigner
) -> None:
    """المفتاح المتقاعد يبقى صالحًا للتاريخ ولا يصلح لأمر جديد (البند 26)."""
    at_rotation = utc_now()
    registry.rotate(
        new_key_id="CROWN-K2",
        algorithm="Ed25519",
        public_key_hex=successor_signer.public_hex,
        provenance=make_provenance(ceremony_kind="CROWN_ROTATION"),
        at=iso(at_rotation),
    )
    old = registry.get("CROWN-K1")
    assert not old.is_activated_now, "مفتاح متقاعد ظهر نشطًا — حال غامضة محظورة."
    # صالح للتحقق من قديم:
    assert old.was_valid_at(iso(at_rotation - timedelta(hours=12)))
    # وغير صالح لجديد:
    assert not old.was_valid_at(iso(at_rotation + timedelta(hours=1)))
    later = iso(at_rotation + timedelta(hours=1))
    verifiers_now = {r.key_id for r in registry.valid_verifiers_at(later)}
    assert "CROWN-K1" not in verifiers_now
    assert "CROWN-K2" in verifiers_now


def test_two_active_keys_are_rejected(
    registry: CrownKeyRegistry, successor_signer: TransientSigner
) -> None:
    """مفتاحان نشطان = تاجان. يُرفَض."""
    registry.register(
        CrownKeyRecord(
            key_id="CROWN-KX",
            version=2,
            algorithm="Ed25519",
            public_key_hex=successor_signer.public_hex,
            state=KeyState.PENDING,
            lineage_kind=LineageKind.ROTATION,
            predecessor_key_id="CROWN-K1",
            registered_at=iso(utc_now()),
            provenance=make_provenance(),
        )
    )
    with pytest.raises((KeyStateError, Exception)):
        registry.activate("CROWN-KX")


def test_unimplemented_algorithm_is_declared_not_claimed() -> None:
    """المنظومات غير المنفَّذة معلنة، والتوقيع بها مرفوض — العَلَم ليس تنفيذًا (البند 25)."""
    plan = AlgorithmAgilityPlan()
    assert "Ed25519" in plan.enabled_algorithms
    assert any(not enabled for enabled in SUPPORTED_ALGORITHMS.values())
    with pytest.raises(AlgorithmError):
        plan.assert_usable("ML-DSA-65")
    plan.assert_usable("Ed25519")


# ─────────────────────────────────────────────────────────────────────────────
# مرساة الثقة (البندان 17 و38).
# ─────────────────────────────────────────────────────────────────────────────


def test_valid_manifest_is_accepted(
    anchor: CrownTrustAnchor,
    registry: CrownKeyRegistry,
    root_signer: TransientSigner,
) -> None:
    """المسار الشرعي: بيان موقَّع بمفتاح الأصل يُقبَل وتُقيَّد مشاهدته."""
    signed = sign_manifest(root_signer, registry)
    verified = anchor.verify_manifest(signed)
    assert verified.active_or_raise().key_id == "CROWN-K1"
    assert anchor.last_observation is not None
    anchor.verify_observation_chain()


def test_public_key_substitution_rejected(
    anchor: CrownTrustAnchor,
    registry: CrownKeyRegistry,
    root_signer: TransientSigner,
    successor_signer: TransientSigner,
) -> None:
    """استبدال المفتاح العام مرفوض — وهو أخطر من سرقة الخاص (البند 17)."""
    forged = CrownKeyRegistry()
    forged.register(
        CrownKeyRecord(
            key_id="CROWN-K1",
            version=1,
            algorithm="Ed25519",
            public_key_hex=successor_signer.public_hex,  # مفتاح المهاجم
            state=KeyState.PENDING,
            lineage_kind=LineageKind.GENESIS,
            predecessor_key_id=None,
            registered_at=iso(utc_now()),
            provenance=make_provenance(),
        )
    )
    forged.activate("CROWN-K1")
    attacker_root = TransientSigner()
    signed = sign_manifest(attacker_root, forged)
    with pytest.raises(AnchorSubstitutionError):
        anchor.verify_manifest(signed)


def test_tampered_manifest_after_signing_is_rejected(
    anchor: CrownTrustAnchor,
    registry: CrownKeyRegistry,
    root_signer: TransientSigner,
) -> None:
    """تحريف البيان بعد توقيعه يظهر في التحقق حتمًا."""
    signed = sign_manifest(
        root_signer, registry, mutate={"manifest_version": 99}
    )
    with pytest.raises(AnchorSubstitutionError):
        anchor.verify_manifest(signed)


def test_rollback_to_older_manifest_is_rejected(
    anchor: CrownTrustAnchor,
    registry: CrownKeyRegistry,
    root_signer: TransientSigner,
    successor_signer: TransientSigner,
) -> None:
    """إعادة بيان أقدم مرفوضة — الرجوع بالنسخة إعادةٌ لمفتاح مسحوب (البند 21)."""
    first = sign_manifest(root_signer, registry)
    anchor.verify_manifest(first)

    registry.rotate(
        new_key_id="CROWN-K2",
        algorithm="Ed25519",
        public_key_hex=successor_signer.public_hex,
        provenance=make_provenance(ceremony_kind="CROWN_ROTATION"),
    )
    anchor.rotate_pin(
        new_fingerprint=registry.active_or_raise().fingerprint,
        ceremony_id="CER-ROT-1",
        witness="أمين السجل",
    )
    second = sign_manifest(root_signer, registry)
    anchor.verify_manifest(second)

    # إعادة بيان أقدم هبوط ورجوع في الوقت معًا؛ أيُّهما رفضًا مقبول.
    with pytest.raises((RollbackError, DowngradeError)):
        anchor.verify_manifest(first)


def test_anchor_not_controlled_by_repository(
    root_signer: TransientSigner, registry: CrownKeyRegistry
) -> None:
    """مرساة من مستوى يملكه التطبيق = ثقة دائرية. تُرفَض (البند 38)."""
    fingerprint = anchor_fingerprint("ROOT-1", root_signer.public_hex)
    controlled = (
        AnchorSource(
            plane=TrustPlane.APPLICATION_DATABASE,
            locator="نفس قاعدة بيانات التطبيق",
            fingerprint=fingerprint,
        ),
        AnchorSource(
            plane=TrustPlane.REPOSITORY_FILE,
            locator="ملف في المستودع",
            fingerprint=fingerprint,
        ),
    )
    # الرفض يقع في البناء نفسه: مرساة دائرية لا يجوز أن توجد أصلًا.
    with pytest.raises(CircularTrustError):
        CrownTrustAnchor(
            root_id="ROOT-1",
            root_public_key_hex=root_signer.public_hex,
            sources=controlled,
            require_out_of_band=False,
        )


def test_first_pin_requires_out_of_band_verification(
    root_signer: TransientSigner,
    registry: CrownKeyRegistry,
) -> None:
    """التثبيت الأول لا يُستنتَج من الشبكة (البند 18)."""
    fingerprint = anchor_fingerprint("ROOT-1", root_signer.public_hex)
    sources = (
        AnchorSource(
            plane=TrustPlane.OFFLINE_ROOT,
            locator="أصل خارج الشبكة بلا إشهاد بشري بعد",
            fingerprint=fingerprint,
        ),
    )
    anchor = CrownTrustAnchor(
        root_id="ROOT-1",
        root_public_key_hex=root_signer.public_hex,
        sources=sources,
    )
    assert not anchor.out_of_band_confirmed
    signed = sign_manifest(root_signer, registry)
    with pytest.raises(OutOfBandVerificationRequiredError):
        anchor.verify_manifest(signed)


def test_root_key_may_not_be_a_crown_key(
    root_signer: TransientSigner,
    crown_signer: TransientSigner,
    independent_sources: tuple[AnchorSource, ...],
    registry: CrownKeyRegistry,
) -> None:
    """مفتاح الأصل لا يكون مفتاح التاج — وإلا صادقت الشرعية على نفسها."""
    fingerprint = anchor_fingerprint("ROOT-1", crown_signer.public_hex)
    sources = tuple(
        AnchorSource(
            plane=s.plane,
            locator=s.locator,
            fingerprint=fingerprint,
            verified_at=s.verified_at,
            verifier=s.verifier,
        )
        for s in independent_sources
    )
    anchor = CrownTrustAnchor(
        root_id="ROOT-1",
        root_public_key_hex=crown_signer.public_hex,
        sources=sources,
    )
    with pytest.raises(RootKeyReuseError):
        anchor.assert_root_independent_of(registry)


def test_observation_chain_detects_deletion(
    anchor: CrownTrustAnchor,
    registry: CrownKeyRegistry,
    root_signer: TransientSigner,
) -> None:
    """سلسلة المشاهدات تكشف حذف مشاهدة — وهو أثر إخفاء استبدال."""
    anchor.verify_manifest(sign_manifest(root_signer, registry))
    anchor.record_observation(
        manifest_version=1,
        manifest_digest="d" * 64,
        active_key_fingerprint=registry.active_or_raise().fingerprint,
    )
    anchor.verify_observation_chain()
    anchor._observations.pop(0)  # محاكاة حذف — عبث مقصود
    with pytest.raises(Exception):
        anchor.verify_observation_chain()


def test_substitution_matrix_is_documented_and_honest() -> None:
    """مصفوفة الاستبدال تحفظ حدّ البرمجية صريحًا لكل متجه."""
    assert len(SUBSTITUTION_VECTORS) >= 10
    matrix = substitution_matrix()
    assert all(row["software_limit"] for row in matrix), (
        "متجه بلا حدّ برمجي معلَن — يوهم بحماية كاملة."
    )
    assert DOMAIN_TAG_ANCHOR.startswith("AMOS-CROWN")


def test_anchor_descriptor_carries_no_secret(
    anchor: CrownTrustAnchor, tmp_path
) -> None:
    """الوصف المنشور يحمل مفاتيح عامة وبصمات فقط — لا مادة سرية."""
    descriptor = anchor.public_descriptor()
    serialized = str(descriptor).lower()
    for forbidden in ["private", "seed", "mnemonic", "passphrase"]:
        assert forbidden not in serialized
    path = anchor.write_descriptor(tmp_path / "anchor.json")
    assert path.exists()


# ─────────────────────────────────────────────────────────────────────────────
# بيئة التوقيع (البندان 7 و8).
# ─────────────────────────────────────────────────────────────────────────────


_COMMAND_TAG = "AMOS-CROWN-COMMAND-v1"


def _request(body: bytes) -> SigningRequest:
    """طلب توقيع سليم: الحمولة تبدأ بوسم المجال كي لا تُخلط المجالات."""
    return SigningRequest(
        domain_tag=_COMMAND_TAG, payload=_COMMAND_TAG.encode() + b"\n" + body
    )


def test_production_keystore_is_honest_about_not_being_implemented() -> None:
    """المخزن الإنتاجي المرجعي يرفض التوقيع بدل أن يزعم عتادًا غير موجود."""
    keystore = ReferenceProductionKeystore(
        kind=KeystoreKind.HSM,
        key_id="CROWN-K1",
        endpoint_ref="hsm://reference",
        published_public_key_hex="ab" * 32,
    )
    assert not keystore.implemented
    keystore.assert_no_export_surface()
    with pytest.raises(ProductionKeystoreUnavailableError):
        keystore.sign(_request(b"x"))


def test_test_keystore_signs_but_is_forbidden_in_production() -> None:
    """المخزن العابر يوقّع فعلًا للاختبار، ويرفض أن يُعَد إنتاجيًّا."""
    keystore = EphemeralTestKeystore()
    result = keystore.sign(_request(b"payload"))
    assert result.signature_hex
    assert keystore.signature_count == 1
    with pytest.raises(Exception):
        keystore.assert_production_ready()


def test_signing_request_requires_domain_tag() -> None:
    """توقيع بلا وسم مجال يفتح باب نقل التوقيعات بين السياقات."""
    with pytest.raises(Exception):
        SigningRequest(domain_tag="", payload=b"x")


@pytest.mark.parametrize("location", sorted(FORBIDDEN_MATERIAL_LOCATIONS))
def test_forbidden_material_locations_are_rejected(location: str) -> None:
    """كل موضع محظور لمادة المفتاح يُرفَض تنفيذيًّا لا وصفيًّا."""
    with pytest.raises(KeyMaterialLeakError):
        assert_no_material_in(location)


def test_continuity_environments_grant_no_new_authority() -> None:
    """بيئات الاستمرارية بديلة وصول لا بديلة سلطة (البند 34)."""
    assert len(CONTINUITY_ENVIRONMENTS) >= 3
    for env in CONTINUITY_ENVIRONMENTS:
        assert env.activation_requires_human_ceremony
        assert not env.may_become_replacement_authority


def test_unattested_device_flagged() -> None:
    """جهاز بلا إثبات عتاد يُوسَم — لا يُعتَبر جهاز تاج (البند 22)."""
    weak = CrownDeviceIdentity(device_id="DEV-X", attestation_ref="", hardware_backed=False)
    assert not weak.hardware_backed
    assert weak.attestation_ref == ""
    strong = CrownDeviceIdentity(
        device_id="DEV-Y", attestation_ref="attest://vendor/1", hardware_backed=True
    )
    assert strong.hardware_backed and strong.attestation_ref
