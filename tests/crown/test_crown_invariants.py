"""الهدف: اختبار الثوابت الحدّية — أخطاء التحقق، والاستمرار على قرص، والصادرات.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

هذا الملف يقصد الفروع التي لا يمسّها المسار الشرعي: قيد بلا فاعل، ونسب متشعّب،
وبيان بلا مفاتيح، وسجل على قرص مُحرَّف. وهي المواضع التي تُثقب منها الأنظمة عادةً،
لأن أحدًا لا يجربها.
"""

from __future__ import annotations

import json
from datetime import timedelta

import pytest

from core.crown import audit as audit_module
from core.crown.audit import (
    AuditChainBrokenError,
    AuditError,
    CrownAudit,
    CrownAuditEntry,
    CrownAuditEventKind,
)
from core.crown.identity import (
    IDENTITY_KINDS,
    BiometricAsKeyError,
    assert_not_key_material,
)
from core.crown.key_registry import (
    SUPPORTED_ALGORITHMS,
    AlgorithmError,
    CrownKeyRecord,
    CrownKeyRegistry,
    KeyProvenance,
    KeyRegistryError,
    KeyState,
    KeyStateError,
    LineageError,
    LineageKind,
)
from core.crown.keystore import (
    EphemeralTestKeystore,
    KeystoreError,
    KeystoreKind,
    ReferenceProductionKeystore,
    SigningRequest,
)
from core.crown.keystore import (
    TestKeystoreInProductionError as ProductionUseRefusedError,  # اسم بديل يمنع جمع pytest
)
from tests.crown.conftest import (
    TransientSigner,
    iso,
    make_provenance,
    utc_now,
)


# ─────────────────────────────────────────────────────────────────────────────
# السجل: تحقق القيود، والاستمرار على قرص، والتحميل.
# ─────────────────────────────────────────────────────────────────────────────


def test_audit_entry_rejects_missing_actor_or_summary() -> None:
    """قيد بلا فاعل أو بلا خلاصة مرفوض — «حدث شيء» ليست مراقبة."""
    with pytest.raises(AuditError):
        CrownAuditEntry(
            sequence=0,
            kind=CrownAuditEventKind.GUARD_ALERT,
            actor="",
            subject="x",
            summary="خلاصة",
            recorded_at=iso(utc_now()),
            previous_hash="",
        )
    with pytest.raises(AuditError):
        CrownAuditEntry(
            sequence=0,
            kind=CrownAuditEventKind.GUARD_ALERT,
            actor="guard",
            subject="x",
            summary="",
            recorded_at=iso(utc_now()),
            previous_hash="",
        )
    with pytest.raises(AuditError):
        CrownAuditEntry(
            sequence=-1,
            kind=CrownAuditEventKind.GUARD_ALERT,
            actor="guard",
            subject="x",
            summary="خلاصة",
            recorded_at=iso(utc_now()),
            previous_hash="",
        )


def test_audit_entry_roundtrips_through_dict() -> None:
    """القيد يُسلسَل ويُستعاد بلا فقد — الاستعادة شرط قابلية التدقيق لاحقًا."""
    audit = CrownAudit()
    entry = audit.append(
        CrownAuditEventKind.ROYAL_DECISION,
        actor="CROWN-K1",
        subject="D1",
        summary="قرار.",
        detail={"k": "v"},
    )
    restored = CrownAuditEntry.from_dict(entry.as_dict())
    assert restored.entry_hash == entry.entry_hash


def test_audit_persists_and_reloads_from_disk(tmp_path) -> None:
    """السجل المكتوب على قرص يُعاد تحميله ويُتحقَّق من سلسلته عند التحميل."""
    path = tmp_path / "nested" / "crown-audit.jsonl"
    audit = CrownAudit(path=path)
    audit.append(
        CrownAuditEventKind.TRUST_ANCHOR_EVENT, actor="أمين السجل", summary="تحقق."
    )
    audit.append(CrownAuditEventKind.GUARD_ALERT, actor="guard", summary="تنبيه.")
    assert path.is_file()

    reloaded = CrownAudit(path=path)
    assert len(reloaded) == 2
    assert reloaded.tip_hash == audit.tip_hash
    reloaded.verify_chain()


def test_audit_load_rejects_corrupted_file(tmp_path) -> None:
    """ملف سجل محرَّف يرفع كسر سلسلة لا يُقرأ صامتًا."""
    path = tmp_path / "broken.jsonl"
    path.write_text("{ليس JSON صالحًا}\n", encoding="utf-8")
    with pytest.raises(AuditChainBrokenError):
        CrownAudit(path=path)


def test_audit_load_skips_blank_lines(tmp_path) -> None:
    """الأسطر الفارغة لا تُفسِد التحميل — التحريف يُكشَف، والفراغ يُتجاوز."""
    source = CrownAudit()
    source.append(CrownAuditEventKind.GUARD_ALERT, actor="guard", summary="تنبيه.")
    path = tmp_path / "with-blanks.jsonl"
    path.write_text(
        "\n".join(
            ["", json.dumps(source.entries[0].as_dict(), ensure_ascii=False), "", ""]
        ),
        encoding="utf-8",
    )
    loaded = CrownAudit(path=path)
    assert len(loaded) == 1


def test_audit_grouping_and_snapshot() -> None:
    """التصنيف بالنوع، وانتقاء الحرِج، ولقطة السجل — أدوات مراجعة لا زينة."""
    audit = CrownAudit()
    audit.append(CrownAuditEventKind.GUARD_ALERT, actor="guard", summary="تنبيه.")
    audit.append(
        CrownAuditEventKind.CROWN_KEY_COMPROMISED,
        actor="أمين السجل",
        summary="اختراق مفتاح.",
    )
    assert len(audit.by_kind(CrownAuditEventKind.GUARD_ALERT)) == 1
    critical = audit.critical_entries()
    assert critical
    assert all(entry.kind.is_critical for entry in critical)
    snapshot = audit.snapshot()
    assert snapshot["count"] == 2
    assert snapshot["critical_count"] == 1
    assert snapshot["tip_hash"] == audit.tip_hash
    assert snapshot["integrity_digest"] == audit.integrity_digest()


def test_critical_event_kinds_are_declared() -> None:
    """أنواع الأحداث الحرِجة معلَنة بالاسم لا بالتقدير."""
    critical = [k for k in CrownAuditEventKind if k.is_critical]
    assert CrownAuditEventKind.CROWN_KEY_COMPROMISED in critical
    assert CrownAuditEventKind.SUCCESSION_EVENT in critical
    assert CrownAuditEventKind.GUARD_ALERT not in critical


def test_audit_module_now_returns_iso_utc() -> None:
    """أوقات السجل بتوقيت عالمي صريح — سجل بلا منطقة زمنية سجل مُلتبِس."""
    stamp = audit_module._now()
    assert stamp.endswith("+00:00") or stamp.endswith("Z")


# ─────────────────────────────────────────────────────────────────────────────
# سجل المفاتيح: تحقق القيد والنسب والبيان.
# ─────────────────────────────────────────────────────────────────────────────


def _record(**overrides) -> CrownKeyRecord:
    data = {
        "key_id": "CROWN-K1",
        "version": 1,
        "algorithm": "Ed25519",
        "public_key_hex": TransientSigner().public_hex,
        "state": KeyState.PENDING,
        "lineage_kind": LineageKind.GENESIS,
        "predecessor_key_id": None,
        "registered_at": iso(utc_now()),
        "provenance": make_provenance(),
    }
    data.update(overrides)
    return CrownKeyRecord(**data)


def test_provenance_requires_ceremony_and_keystore() -> None:
    """مصدر المفتاح بلا مراسم أو بلا بيئة توقيع معلَنة مرفوض."""
    with pytest.raises(KeyRegistryError):
        KeyProvenance(
            ceremony_id="",
            ceremony_kind="CROWN_GENESIS",
            keystore_kind="TEST_EPHEMERAL",
        )
    with pytest.raises(KeyRegistryError):
        KeyProvenance(
            ceremony_id="CER-1", ceremony_kind="CROWN_GENESIS", keystore_kind=""
        )


def test_key_record_validation_rejects_malformed_fields() -> None:
    """قيد بلا معرّف أو بنسخة صفرية أو بلا مفتاح عام أو بمفتاح غير سِتّي — مرفوض."""
    with pytest.raises(KeyRegistryError):
        _record(key_id="")
    with pytest.raises(KeyRegistryError):
        _record(version=0)
    with pytest.raises(KeyRegistryError):
        _record(public_key_hex="")
    with pytest.raises(KeyRegistryError):
        _record(public_key_hex="ليس سِتّيًّا")
    with pytest.raises(KeyRegistryError):
        _record(public_key_hex="aabb")  # طول غير مطابق لـ Ed25519


def test_key_record_rejects_unknown_algorithm() -> None:
    """منظومة تعمية مجهولة مرفوضة، والمعروف غير المسموح يُرفَض عند الاستعمال."""
    with pytest.raises(AlgorithmError):
        _record(algorithm="RSA-9999")
    assert SUPPORTED_ALGORITHMS["Ed25519"] is True
    assert any(value is False for value in SUPPORTED_ALGORITHMS.values())


def test_key_record_lineage_rules() -> None:
    """التأسيس لا سابق له، وغير التأسيس لا يكون بلا سابق."""
    with pytest.raises(LineageError):
        _record(lineage_kind=LineageKind.GENESIS, predecessor_key_id="CROWN-K0")
    with pytest.raises(LineageError):
        _record(lineage_kind=LineageKind.ROTATION, predecessor_key_id=None)


def test_key_record_state_time_rules() -> None:
    """مفتاح نشط بلا وقت تنشيط، ومسحوب بلا وقت سحب — قيود ناقصة مرفوضة."""
    with pytest.raises(KeyStateError):
        _record(state=KeyState.ACTIVE, activated_at="")
    with pytest.raises(KeyStateError):
        _record(state=KeyState.REVOKED, revoked_at="", revocation_reason="سبب")


def test_registry_rejects_duplicate_ids_and_versions(
    registry: CrownKeyRegistry,
) -> None:
    """معرّف مكرَّر أو نسخة مكرَّرة نسبٌ متشعّب — والتاج لا يتشعّب."""
    with pytest.raises(KeyRegistryError):
        registry.register(_record(key_id="CROWN-K1", version=9))
    with pytest.raises(KeyRegistryError):
        registry.register(
            _record(
                key_id="CROWN-KX",
                version=1,
                lineage_kind=LineageKind.ROTATION,
                predecessor_key_id="CROWN-K1",
            )
        )


def test_registry_rejects_second_active_key(registry: CrownKeyRegistry) -> None:
    """مفتاحان نشطان معًا تاجان — مرفوض بالبنية."""
    registry.register(
        _record(
            key_id="CROWN-K2",
            version=2,
            lineage_kind=LineageKind.ROTATION,
            predecessor_key_id="CROWN-K1",
        )
    )
    with pytest.raises(KeyStateError):
        registry.activate("CROWN-K2")


def test_revocation_requires_a_declared_reason(registry: CrownKeyRegistry) -> None:
    """سحب المفتاح أو إعلان اختراقه بلا سبب معلَن مرفوض."""
    with pytest.raises(KeyRegistryError):
        registry.revoke("CROWN-K1", reason="")
    with pytest.raises(KeyRegistryError):
        registry.mark_compromised("CROWN-K1", reason="")


def test_rotation_rejects_a_predecessor_that_is_not_active(
    registry: CrownKeyRegistry, successor_signer: TransientSigner
) -> None:
    """تسمية سلف غير النشط تدويرٌ من غير موضعه."""
    with pytest.raises(KeyRegistryError):
        registry.rotate(
            new_key_id="CROWN-K2",
            algorithm="Ed25519",
            public_key_hex=successor_signer.public_hex,
            provenance=make_provenance(ceremony_kind="CROWN_ROTATION"),
            predecessor_key_id="CROWN-K404",
        )


def test_rotation_after_compromise_requires_a_named_predecessor(
    registry: CrownKeyRegistry, successor_signer: TransientSigner
) -> None:
    """بعد الاختراق لا سلف مستنتَج: يُسمّى في المراسم أو يُرفَض التدوير.

    ولا يجوز أن يكون إعلان الاختراق قفلًا أبديًّا يمنع التدوير، وإلا صار الصدق
    بابًا لتجميد التاج.
    """
    registry.mark_compromised("CROWN-K1", reason="تسريب مؤكَّد.")
    with pytest.raises(KeyRegistryError):
        registry.rotate(
            new_key_id="CROWN-K2",
            algorithm="Ed25519",
            public_key_hex=successor_signer.public_hex,
            provenance=make_provenance(ceremony_kind="CROWN_ROTATION"),
        )
    record = registry.rotate(
        new_key_id="CROWN-K2",
        algorithm="Ed25519",
        public_key_hex=successor_signer.public_hex,
        provenance=make_provenance(ceremony_kind="CROWN_ROTATION"),
        predecessor_key_id="CROWN-K1",
    )
    assert record.state is KeyState.ACTIVE
    assert record.predecessor_key_id == "CROWN-K1"
    registry.validate()


def test_manifest_roundtrip_and_rejection_of_malformed_manifest(
    registry: CrownKeyRegistry,
) -> None:
    """البيان يُستعاد كما هو، وبيان بلا قائمة مفاتيح أو بمجال آخر يُرفَض."""
    manifest = registry.manifest()
    restored = CrownKeyRegistry.from_manifest(manifest)
    assert restored.manifest_digest() == registry.manifest_digest()

    with pytest.raises(KeyRegistryError):
        CrownKeyRegistry.from_manifest({**manifest, "keys": None})
    with pytest.raises(KeyRegistryError):
        CrownKeyRegistry.from_manifest({**manifest, "domain": "مجال آخر"})


def test_valid_verifiers_and_retirement_instant(registry: CrownKeyRegistry) -> None:
    """المفتاح صالح للتحقق حتى لحظة سحبه، ولا يصلح بعدها."""
    moment = utc_now()
    assert registry.valid_verifiers_at(iso(moment))
    registry.retire("CROWN-K1", at=iso(moment))
    assert not registry.valid_verifiers_at(iso(moment + timedelta(seconds=1)))


def test_registry_get_unknown_key_raises(registry: CrownKeyRegistry) -> None:
    """طلب مفتاح غير مسجَّل يرفع خطأً — لا قيمة فارغة تمرّ صامتة."""
    with pytest.raises(KeyRegistryError):
        registry.get("CROWN-K404")


# ─────────────────────────────────────────────────────────────────────────────
# بيئة التوقيع والهوية.
# ─────────────────────────────────────────────────────────────────────────────


def test_signing_request_enforces_domain_separation() -> None:
    """طلب توقيع بلا وسم مجال أو بحمولة لا تبدأ به مرفوض — خلط المجالات ثغرة."""
    with pytest.raises(KeystoreError):
        SigningRequest(domain_tag="", payload=b"x")
    with pytest.raises(KeystoreError):
        SigningRequest(domain_tag="TAG", payload=b"")
    with pytest.raises(KeystoreError):
        SigningRequest(domain_tag="TAG", payload=b"OTHER\npayload")


def test_ephemeral_keystore_is_refused_in_production() -> None:
    """بيئة توقيع اختبارية ترفض أن تُستعمل إنتاجًا — بالكود لا بالتوصية."""
    store = EphemeralTestKeystore()
    request = SigningRequest(domain_tag="TAG", payload=b"TAG\npayload")
    result = store.sign(request)
    assert result.signature_hex
    assert store.signature_count == 1
    with pytest.raises(ProductionUseRefusedError):
        store.assert_production_ready()


def test_reference_production_keystore_declares_no_export_surface() -> None:
    """بيئة الإنتاج المرجعية تصف العتاد ولا تحاكيه، وتنكر سطح تصدير."""
    store = ReferenceProductionKeystore(
        kind=KeystoreKind.SECURE_ELEMENT,
        key_id="CROWN-K1",
        endpoint_ref="se://device/1",
        slot_ref="slot-2",
    )
    store.assert_no_export_surface()
    assert store.implemented is False


def test_identity_kinds_are_separate_and_biometrics_are_not_keys() -> None:
    """هويات التاج منفصلة، والقياس الحيوي دليل حضور لا مادة مفتاح."""
    assert len(IDENTITY_KINDS) >= 5
    for source in ("fingerprint_template", "face_embedding", "neural_implant_signal"):
        with pytest.raises(BiometricAsKeyError):
            assert_not_key_material(source)
    assert_not_key_material("hardware_security_module_slot")


# ─────────────────────────────────────────────────────────────────────────────
# صادرات الحزمة.
# ─────────────────────────────────────────────────────────────────────────────


def test_package_exports_are_lazy_and_complete() -> None:
    """كل اسم معلَن في ``__all__`` قابل للاستيراد فعلًا — لا صادرات وهمية."""
    import core.crown as crown

    assert crown.__all__
    for name in crown.__all__:
        assert getattr(crown, name) is not None
    with pytest.raises(AttributeError):
        crown.اسم_غير_موجود  # noqa: B018


def test_package_dir_lists_exports() -> None:
    """``dir()`` على الحزمة يعرض صادراتها — كي تُستكشف بلا قراءة الشيفرة."""
    import core.crown as crown

    listed = dir(crown)
    assert set(crown.__all__) <= set(listed)
