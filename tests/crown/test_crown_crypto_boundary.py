"""الهدف: اختبار حدود التعمية — مصادر المرساة، وبيئات التوقيع، وأغلفة الأوامر.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المسارات الشرعية والخصومية للمرساة والأوامر مُختبَرة في ملفّيها. وهذا الملف يقصد
الحواف التعمية: بصمة ليست SHA-256، ووصف عتاد بلا مفتاح منشور، وغلاف أمر بحقول
ناقصة. فالحدّ الذي لا يُختبَر حدٌّ مزعوم.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from core.crown.command import (
    CommandError,
    CommandLedger,
    ContextTamperError,
    CrownCommandVerifier,
    ReplayError,
    RoyalCommandEnvelope,
    SignatureError,
    SignedRoyalCommand,
    build_envelope,
)
from core.crown.key_registry import CrownKeyRegistry
from core.crown.keystore import (
    FORBIDDEN_MATERIAL_LOCATIONS,
    ContinuityEnvironment,
    KeyMaterialLeakError,
    KeystoreCapabilities,
    KeystoreError,
    KeystoreKind,
    ProductionKeystoreUnavailableError,
    ReferenceProductionKeystore,
    SigningRequest,
    assert_no_material_in,
)
from core.crown.threats import (
    ALL_THREATS,
    ThreatModelError,
    boundary_report,
    threat,
    unresolved_threats,
)
from core.crown.trust_anchor import (
    AnchorSource,
    AnchorSubstitutionError,
    CrownTrustAnchor,
    DowngradeError,
    RollbackError,
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

DIGEST = "a" * 64


# ─────────────────────────────────────────────────────────────────────────────
# مرساة الثقة.
# ─────────────────────────────────────────────────────────────────────────────


def test_anchor_source_requires_locator_and_valid_fingerprint() -> None:
    """مصدر مرساة بلا موضع أو ببصمة ليست SHA-256 ست عشرية مرفوض."""
    with pytest.raises(TrustAnchorError):
        AnchorSource(
            plane=TrustPlane.PRINTED_FINGERPRINT, locator="", fingerprint=DIGEST
        )
    with pytest.raises(TrustAnchorError):
        AnchorSource(
            plane=TrustPlane.PRINTED_FINGERPRINT,
            locator="خزنة",
            fingerprint="ليست بصمة",
        )
    source = AnchorSource(
        plane=TrustPlane.PRINTED_FINGERPRINT, locator="خزنة", fingerprint=DIGEST
    )
    assert source.as_dict()["plane"] == TrustPlane.PRINTED_FINGERPRINT.value


def test_anchor_construction_validates_root_identity(
    root_signer: TransientSigner,
) -> None:
    """مرساة بلا معرّف أصل، أو بمفتاح أصل غير صالح، أو بلا مصادر — ليست مرساة."""
    fingerprint = anchor_fingerprint("ROOT-1", root_signer.public_hex)
    sources = (
        AnchorSource(
            plane=TrustPlane.PRINTED_FINGERPRINT,
            locator="خزنة",
            fingerprint=fingerprint,
        ),
        AnchorSource(
            plane=TrustPlane.OFFLINE_ROOT, locator="عتاد معزول", fingerprint=fingerprint
        ),
        AnchorSource(
            plane=TrustPlane.HUMAN_OUT_OF_BAND,
            locator="تحقق شفهي",
            fingerprint=fingerprint,
        ),
    )
    with pytest.raises(TrustAnchorError):
        CrownTrustAnchor(
            root_id="", root_public_key_hex=root_signer.public_hex, sources=sources
        )
    with pytest.raises(TrustAnchorError):
        CrownTrustAnchor(
            root_id="ROOT-1", root_public_key_hex="ليس سِتّيًّا", sources=sources
        )
    with pytest.raises(TrustAnchorError):
        CrownTrustAnchor(
            root_id="ROOT-1", root_public_key_hex="ab" * 10, sources=sources
        )
    with pytest.raises(TrustAnchorError):
        CrownTrustAnchor(
            root_id="ROOT-1", root_public_key_hex=root_signer.public_hex, sources=()
        )


def test_anchor_descriptor_is_public_and_writable(
    anchor: CrownTrustAnchor, tmp_path
) -> None:
    """الوصف العام يُنشر بلا سرّ: يحوي المفتاح العام ولا يحوي مادة خاصة."""
    descriptor = anchor.public_descriptor()
    assert descriptor["root_id"]
    assert "private" not in json.dumps(descriptor).lower()
    path = anchor.write_descriptor(tmp_path / "anchor.json")
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["root_id"] == descriptor["root_id"]
    assert anchor.sources


def test_manifest_verification_rejects_unsigned_and_malformed(
    anchor: CrownTrustAnchor,
    registry: CrownKeyRegistry,
    root_signer: TransientSigner,
) -> None:
    """بيان بلا توقيع مرفوض، وبيان مشوَّه البنية يُعَدّ محاولة استبدال."""
    signed = sign_manifest(root_signer, registry)
    with pytest.raises(TrustAnchorError):
        type(signed)(
            manifest=signed.manifest,
            signature_hex="",
            root_key_id=signed.root_key_id,
        )
    broken = sign_manifest(
        root_signer, registry, mutate={"keys": "ليست قائمة"}
    )
    with pytest.raises(AnchorSubstitutionError):
        anchor.verify_manifest(broken)


def test_observation_chain_detects_rollback_and_records_history(
    anchor: CrownTrustAnchor,
    registry: CrownKeyRegistry,
    root_signer: TransientSigner,
) -> None:
    """سلسلة الرصد تكشف الرجوع إلى نسخة أقدم، وتحفظ تاريخ ما رُصد."""
    anchor.record_observation(
        manifest_version=3, manifest_digest=DIGEST, active_key_fingerprint=DIGEST
    )
    anchor.verify_observation_chain()
    assert len(anchor.observations) == 1
    assert anchor.last_observation is not None
    # ثم يُعرَض بيان نسخته أدنى مما رُصد: إرجاع إلى ماضٍ يُرفَض بالمقارنة لا بالثقة.
    older = sign_manifest(root_signer, registry)
    assert older.manifest_version < 3
    # المرساة تُصعِّد حدَّها الأدنى بما رصدته، فالبيان الأقدم يُرفَض هبوطًا أو إرجاعًا.
    with pytest.raises((RollbackError, DowngradeError)):
        anchor.verify_manifest(older)
    anchor.verify_observation_chain()
    assert len(anchor.observations) == 1


def test_pin_rotation_validates_the_new_fingerprint(anchor: CrownTrustAnchor) -> None:
    """تدوير التثبيت يطلب مراسم وشاهدًا وبصمة سليمة — لا كتابة حرّة."""
    with pytest.raises(TrustAnchorError):
        anchor.rotate_pin(new_fingerprint=DIGEST, ceremony_id="", witness="شاهد")
    with pytest.raises(TrustAnchorError):
        anchor.rotate_pin(
            new_fingerprint="ليست بصمة", ceremony_id="CER-9", witness="شاهد"
        )
    anchor.rotate_pin(new_fingerprint="b" * 64, ceremony_id="CER-9", witness="شاهد")


# ─────────────────────────────────────────────────────────────────────────────
# بيئات التوقيع.
# ─────────────────────────────────────────────────────────────────────────────


def test_keystore_kind_flags_test_environments() -> None:
    """النوع الاختباري يُعرَف بذاته — كي لا يمرّ إنتاجًا بالسهو."""
    assert KeystoreKind.TEST_EPHEMERAL.implemented_here is True
    assert KeystoreKind.TEST_EPHEMERAL.production_permitted is False
    assert KeystoreKind.HSM.implemented_here is False
    assert KeystoreKind.HSM.production_permitted is True


def test_capabilities_are_declared_explicitly() -> None:
    """قدرات بيئة التوقيع معلَنة حقلًا حقلًا لا مضمَرة في الاسم."""
    caps = KeystoreCapabilities(
        key_non_exportable=True,
        hardware_attestation=True,
        requires_physical_confirmation=True,
        offline_capable=True,
        tamper_evident=True,
        rate_limited=True,
        production_permitted=True,
    )
    assert caps.as_dict()["key_non_exportable"] is True


def test_reference_production_keystore_validates_its_descriptor() -> None:
    """المرجع الإنتاجي لا يكون اختباريًّا ولا بلا نقطة وصول."""
    with pytest.raises(KeystoreError):
        ReferenceProductionKeystore(
            kind=KeystoreKind.TEST_EPHEMERAL, key_id="K", endpoint_ref="e"
        )
    with pytest.raises(KeystoreError):
        ReferenceProductionKeystore(kind=KeystoreKind.HSM, key_id="K", endpoint_ref="")


def test_reference_production_keystore_does_not_pretend_to_sign() -> None:
    """المرجع يصف العتاد ولا يحاكيه: التوقيع يرفع «غير متاح» لا توقيعًا مزيَّفًا."""
    store = ReferenceProductionKeystore(
        kind=KeystoreKind.HSM, key_id="CROWN-K1", endpoint_ref="pkcs11://slot/1"
    )
    with pytest.raises(ProductionKeystoreUnavailableError):
        store.public_key_hex()
    with pytest.raises(ProductionKeystoreUnavailableError):
        store.sign(SigningRequest(domain_tag="TAG", payload=b"TAG\nx"))
    assert store.capabilities.production_permitted is True
    assert store.descriptor()["implemented_in_repository"] is False


def test_published_public_key_is_returned_when_ceremony_provided_it() -> None:
    """المفتاح العام يُنشر بعد مراسم التوليد — والعام ليس سرًّا."""
    signer = TransientSigner()
    store = ReferenceProductionKeystore(
        kind=KeystoreKind.HSM,
        key_id="CROWN-K1",
        endpoint_ref="pkcs11://slot/1",
        published_public_key_hex=signer.public_hex,
    )
    assert store.public_key_hex() == signer.public_hex


def test_forbidden_material_locations_are_enforced() -> None:
    """كل موضع محظور لمادة المفتاح يُرفَض بالكود لا بالتوصية."""
    for location in FORBIDDEN_MATERIAL_LOCATIONS:
        with pytest.raises(KeyMaterialLeakError):
            assert_no_material_in(location)
    assert_no_material_in("hardware_security_module")


def test_continuity_environment_cannot_declare_itself_replacement_authority() -> None:
    """بيئة احتياطية تُوقِّع بأمر بشري، ولا تُعلن نفسها سلطة بديلة."""
    env = ContinuityEnvironment(
        environment_id="ENV-2",
        role="بيئة توقيع احتياطية",
        keystore_kind=KeystoreKind.AIR_GAPPED_CEREMONY,
    )
    assert env.activation_requires_human_ceremony is True
    assert env.may_become_replacement_authority is False
    assert env.as_dict()["may_become_replacement_authority"] is False
    with pytest.raises(KeystoreError):
        ContinuityEnvironment(
            environment_id="ENV-3",
            role="بيئة",
            keystore_kind=KeystoreKind.HSM,
            activation_requires_human_ceremony=False,
        )


# ─────────────────────────────────────────────────────────────────────────────
# أغلفة الأوامر.
# ─────────────────────────────────────────────────────────────────────────────


def _envelope(**overrides) -> RoyalCommandEnvelope:
    data = {
        "command_id": "CMD-1",
        "action": "APPROVE",
        "target": "budget",
        "issuer_key_id": "CROWN-K1",
        "nonce": "n-1",
        "sequence": 1,
    }
    data.update(overrides)
    return build_envelope(**data)


def test_envelope_rejects_missing_fields_and_negative_sequence() -> None:
    """غلاف بحقل ناقص أو بتسلسل سالب مرفوض قبل أي توقيع."""
    with pytest.raises(CommandError):
        _envelope(command_id="")
    with pytest.raises(CommandError):
        _envelope(action="")
    with pytest.raises(CommandError):
        _envelope(sequence=-1)


def test_envelope_rejects_invalid_or_inverted_times() -> None:
    """وقت غير صالح، أو صلاحية تنتهي قبل الإصدار — مرفوضان."""
    with pytest.raises(CommandError):
        _envelope(validity_seconds=0)
    envelope = _envelope()
    with pytest.raises(CommandError):
        RoyalCommandEnvelope.from_dict({**envelope.as_dict(), "issued_at": "ليس وقتًا"})


def test_envelope_roundtrip_and_validity_window() -> None:
    """الغلاف يُسلسَل ويُستعاد ببصمة واحدة، ونافذته الزمنية محسوبة لا مزعومة."""
    issued = utc_now()
    envelope = _envelope(issued_at=issued, validity_seconds=60)
    restored = RoyalCommandEnvelope.from_dict(envelope.as_dict())
    assert restored.canonical_bytes() == envelope.canonical_bytes()
    assert envelope.is_valid_at(issued + timedelta(seconds=30)) is True
    assert envelope.is_valid_at(issued + timedelta(seconds=120)) is False
    assert len(envelope.chain_hash()) == 64


def test_unsigned_command_is_rejected(
    crown_signer: TransientSigner, registry: CrownKeyRegistry
) -> None:
    """أمر بلا توقيع مرفوض — والغياب ليس ثقة."""
    envelope = _envelope()
    with pytest.raises(SignatureError):
        SignedRoyalCommand(envelope=envelope, signature_hex="")
    # وتوقيع سِتّي سليم الشكل لكنه ليس توقيع التاج يُرفَض أيضًا:
    verifier = CrownCommandVerifier(registry)
    with pytest.raises(SignatureError):
        verifier.verify(SignedRoyalCommand(envelope=envelope, signature_hex="ab" * 32))


def test_ledger_rejects_replay_and_broken_chain(
    crown_signer: TransientSigner, registry: CrownKeyRegistry
) -> None:
    """السجل يرفض إعادة المعرّف أو النونس، ويكشف كسر ربط الأمر بسابقه."""
    ledger = CommandLedger()
    first = _envelope()
    ledger.commit(first)
    assert ledger.was_executed("CMD-1") is True
    assert ledger.records

    with pytest.raises(ReplayError):
        ledger.assert_fresh(first)
    with pytest.raises(ReplayError):
        ledger.assert_fresh(_envelope(command_id="CMD-2", sequence=2))

    with pytest.raises(ContextTamperError):
        ledger.assert_fresh(
            _envelope(
                command_id="CMD-3",
                nonce="n-3",
                sequence=2,
                previous_command_hash="c" * 64,
            )
        )


# ─────────────────────────────────────────────────────────────────────────────
# مكتبة التهديدات.
# ─────────────────────────────────────────────────────────────────────────────


def test_threat_lookup_and_unresolved_listing() -> None:
    """كل تهديد يُطلَب بمعرّفه، والمجهول يرفع خطأً لا يعود فراغًا."""
    known = ALL_THREATS[0]
    assert threat(known.threat_id) is known
    with pytest.raises(ThreatModelError):
        threat("THR-غير-موجود")
    unresolved = unresolved_threats()
    assert unresolved
    assert len(unresolved) < len(ALL_THREATS)


def test_threat_dict_and_boundary_report_are_serialisable() -> None:
    """المصفوفة والحدّ قابلان للتسلسل JSONًا — كي يُنشرا للمراجعة."""
    payload = json.dumps(
        {"threat": ALL_THREATS[0].as_dict(), "boundary": boundary_report()},
        ensure_ascii=False,
    )
    assert "threat_id" in payload


def test_registering_a_duplicate_threat_id_is_rejected() -> None:
    """معرّف تهديد مكرَّر مرفوض — وإلا استُبدل تهديد بآخر صامتًا."""
    from core.crown.threats import register_threat

    with pytest.raises(ThreatModelError):
        register_threat(ALL_THREATS[0])


def test_threat_horizon_and_status_helpers_are_consistent() -> None:
    """حال المعالجة تُعلن ادّعاء الحماية صراحةً، ولا ادّعاء بلا اختبار."""
    for item in ALL_THREATS:
        if item.mitigation_status.claims_protection:
            assert item.test_refs
    assert iso(utc_now())
