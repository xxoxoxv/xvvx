"""الهدف: اختبار مسار الأمر الملكي — التوقيع، والنطاق الزمني، وعدم الإعادة، والسجل.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

الأمر الملكي هو الموضع الذي تتحول فيه إرادة سيادية إلى أثر تنفيذي، فكل اختبار هنا
يقابل طريقة انتحال بعينها: تلفيق، وتحريف، وإعادة، ونقل توقيع، وحقل غير موقَّع.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from core.crown.command import (
    DOMAIN_TAG_COMMAND,
    FORBIDDEN_UNSIGNED_FIELDS,
    CommandLedger,
    ContextTamperError,
    CrownCommandVerifier,
    ExpiredCommandError,
    ReplayError,
    RoyalCommandEnvelope,
    SignatureError,
    SignedRoyalCommand,
    UnsignedFieldError,
    build_envelope,
)
from core.crown.key_registry import (
    CrownKeyRecord,
    CrownKeyRegistry,
    KeyState,
    LineageKind,
)

from tests.crown.conftest import TransientSigner, iso, make_provenance, utc_now


def make_command(
    signer: TransientSigner,
    *,
    command_id: str = "CMD-0001",
    action: str = "APPROVE_DEPLOYMENT",
    target: str = "federal/executive/services",
    issuer_key_id: str = "CROWN-K1",
    nonce: str = "nonce-0001",
    sequence: int = 1,
    validity_seconds: int = 900,
    issued_at=None,
    context: dict | None = None,
    unsigned_metadata: dict | None = None,
) -> SignedRoyalCommand:
    """يبني أمرًا موقَّعًا توقيعًا حقيقيًّا — لا محاكاة للتوقيع."""
    envelope = build_envelope(
        command_id=command_id,
        action=action,
        target=target,
        issuer_key_id=issuer_key_id,
        nonce=nonce,
        sequence=sequence,
        validity_seconds=validity_seconds,
        issued_at=issued_at,
        context=context,
    )
    return SignedRoyalCommand(
        envelope=envelope,
        signature_hex=signer.sign(envelope.canonical_bytes()),
        unsigned_metadata=unsigned_metadata or {},
    )


@pytest.fixture
def verifier(registry: CrownKeyRegistry) -> CrownCommandVerifier:
    return CrownCommandVerifier(registry, CommandLedger())


# ── المسار الشرعي ────────────────────────────────────────────────────────────


def test_valid_command_is_accepted(
    verifier: CrownCommandVerifier, crown_signer: TransientSigner
) -> None:
    """أمر موقَّع بالمفتاح النشط داخل نطاقه الزمني يُقبَل ويُقيَّد تنفيذه."""
    command = make_command(crown_signer)
    outcome = verifier.verify(command)
    assert outcome.accepted
    assert outcome.key_id == "CROWN-K1"

    record = verifier.verify_and_commit(command)
    assert record.command_id == "CMD-0001"
    assert verifier.ledger.was_executed("CMD-0001")
    assert verifier.ledger.executed_count == 1


def test_command_domain_tag_is_bound_to_signature(
    crown_signer: TransientSigner,
) -> None:
    """بايتات التوقيع تبدأ بوسم مجال الأمر — فلا يُقرأ توقيع أمر كتوقيع بيان."""
    command = make_command(crown_signer)
    assert command.envelope.canonical_bytes().startswith(DOMAIN_TAG_COMMAND.encode())


def test_chain_hash_links_commands(crown_signer: TransientSigner) -> None:
    """ربط الأوامر بسلسلة يجعل حذف أمر من التاريخ مكشوفًا."""
    first = make_command(crown_signer)
    ledger = CommandLedger()
    ledger.commit(first.envelope)
    tip = ledger.chain_tip
    assert tip
    assert first.envelope.chain_hash() != first.envelope.digest


# ── الخصومة: تلفيق وتحريف ────────────────────────────────────────────────────


def test_forged_command_rejected(
    verifier: CrownCommandVerifier,
) -> None:
    """أمر موقَّع بمفتاح ليس مفتاح التاج يُرفَض — التوقيع مصدر الشرعية لا الشكل."""
    attacker = TransientSigner()
    command = make_command(attacker)
    with pytest.raises(SignatureError):
        verifier.verify(command)


def test_mutated_command_rejected(
    verifier: CrownCommandVerifier, crown_signer: TransientSigner
) -> None:
    """تحريف حرف واحد في الهدف بعد التوقيع يُبطل التوقيع."""
    original = make_command(crown_signer)
    mutated_envelope = RoyalCommandEnvelope(
        command_id=original.envelope.command_id,
        action=original.envelope.action,
        target="states/rogue-target",  # تحريف
        issuer_key_id=original.envelope.issuer_key_id,
        nonce=original.envelope.nonce,
        sequence=original.envelope.sequence,
        issued_at=original.envelope.issued_at,
        valid_until=original.envelope.valid_until,
        payload=original.envelope.payload,
        previous_command_hash=original.envelope.previous_command_hash,
        context=original.envelope.context,
    )
    mutated = SignedRoyalCommand(
        envelope=mutated_envelope, signature_hex=original.signature_hex
    )
    with pytest.raises(SignatureError):
        verifier.verify(mutated)


def test_replay_rejected(
    verifier: CrownCommandVerifier, crown_signer: TransientSigner
) -> None:
    """أمر صحيح نُفِّذ مرة لا يُنفَّذ ثانية — وإلا صار كل أمر قابلًا للتكرار."""
    command = make_command(crown_signer)
    verifier.verify_and_commit(command)
    with pytest.raises(ReplayError):
        verifier.verify(command)


def test_replay_with_new_id_but_same_nonce_rejected(
    verifier: CrownCommandVerifier, crown_signer: TransientSigner
) -> None:
    """إعادة استخدام nonce بمعرّف جديد إعادةٌ متخفية — تُرفَض."""
    verifier.verify_and_commit(make_command(crown_signer))
    disguised = make_command(
        crown_signer, command_id="CMD-0002", nonce="nonce-0001", sequence=2
    )
    with pytest.raises(ReplayError):
        verifier.verify(disguised)


def test_signature_transplant_rejected(
    verifier: CrownCommandVerifier, crown_signer: TransientSigner
) -> None:
    """نقل توقيع أمر صحيح إلى أمر آخر يُرفَض — التوقيع مرتبط بمحتواه كاملًا."""
    donor = make_command(crown_signer, command_id="CMD-A", nonce="n-a", sequence=1)
    recipient_envelope = build_envelope(
        command_id="CMD-B",
        action="TRANSFER_AUTHORITY",
        target="agents/rogue",
        issuer_key_id="CROWN-K1",
        nonce="n-b",
        sequence=2,
    )
    transplanted = SignedRoyalCommand(
        envelope=recipient_envelope, signature_hex=donor.signature_hex
    )
    with pytest.raises(SignatureError):
        verifier.verify(transplanted)


def test_expired_command_rejected(
    verifier: CrownCommandVerifier, crown_signer: TransientSigner
) -> None:
    """النطاق الزمني حدّ حقيقي: أمر منتهٍ يُرفَض ولو كان توقيعه صحيحًا (البند 20)."""
    stale = make_command(
        crown_signer,
        validity_seconds=60,
        issued_at=utc_now() - timedelta(hours=6),
    )
    with pytest.raises(ExpiredCommandError):
        verifier.verify(stale)


def test_future_dated_command_rejected(
    verifier: CrownCommandVerifier, crown_signer: TransientSigner
) -> None:
    """أمر من المستقبل خارج هامش انزياح الساعة يُرفَض — إزاحة ساعة أداة هجوم."""
    ahead = make_command(crown_signer, issued_at=utc_now() + timedelta(hours=2))
    with pytest.raises(ExpiredCommandError):
        verifier.verify(ahead)


def test_clock_skew_tolerance_is_bounded(
    registry: CrownKeyRegistry, crown_signer: TransientSigner
) -> None:
    """هامش الانزياح محدود لا مفتوح: ثانية داخل الهامش تُقبَل وساعة تُرفَض."""
    verifier = CrownCommandVerifier(
        registry, CommandLedger(), clock_skew_tolerance_seconds=60
    )
    slightly_ahead = make_command(
        crown_signer, issued_at=utc_now() + timedelta(seconds=30)
    )
    assert verifier.verify(slightly_ahead).accepted


@pytest.mark.parametrize("field_name", sorted(FORBIDDEN_UNSIGNED_FIELDS))
def test_authority_bearing_field_may_not_be_unsigned(
    field_name: str, crown_signer: TransientSigner
) -> None:
    """كل حقل حامل سلطة يجب أن يكون داخل التوقيع — الميتاداتا لا تحمل سلطة."""
    with pytest.raises(UnsignedFieldError):
        make_command(crown_signer, unsigned_metadata={field_name: "x"})


def test_benign_unsigned_metadata_is_allowed(crown_signer: TransientSigner) -> None:
    """ميتاداتا وصفية لا تحمل سلطة مسموحة — وإلا صار كل وسم ممنوعًا بلا سبب."""
    command = make_command(
        crown_signer, unsigned_metadata={"ui_locale": "ar", "trace_id": "t-1"}
    )
    assert command.unsigned_metadata["ui_locale"] == "ar"


def test_context_tamper_is_detected(
    verifier: CrownCommandVerifier, crown_signer: TransientSigner
) -> None:
    """السياق داخل التوقيع: تغييره بعد التوقيع يُكشَف (البند 19)."""
    command = make_command(crown_signer, context={"channel": "royal-terminal"})
    tampered_envelope = RoyalCommandEnvelope(
        command_id=command.envelope.command_id,
        action=command.envelope.action,
        target=command.envelope.target,
        issuer_key_id=command.envelope.issuer_key_id,
        nonce=command.envelope.nonce,
        sequence=command.envelope.sequence,
        issued_at=command.envelope.issued_at,
        valid_until=command.envelope.valid_until,
        payload=command.envelope.payload,
        previous_command_hash=command.envelope.previous_command_hash,
        context={"channel": "unknown-channel"},
    )
    tampered = SignedRoyalCommand(
        envelope=tampered_envelope, signature_hex=command.signature_hex
    )
    with pytest.raises((SignatureError, ContextTamperError)):
        verifier.verify(tampered)


def test_command_from_retired_key_is_rejected_for_new_but_verifiable_historically(
    registry: CrownKeyRegistry,
    crown_signer: TransientSigner,
    successor_signer: TransientSigner,
) -> None:
    """أمر بمفتاح متقاعد: مرفوض كأمر جديد، وصحيح كوثيقة تاريخية (البند 26)."""
    signed_at = utc_now() - timedelta(minutes=1)
    command = make_command(crown_signer, issued_at=signed_at)
    registry.rotate(
        new_key_id="CROWN-K2",
        algorithm="Ed25519",
        public_key_hex=successor_signer.public_hex,
        provenance=make_provenance(ceremony_kind="CROWN_ROTATION"),
    )
    verifier = CrownCommandVerifier(registry, CommandLedger())
    with pytest.raises(SignatureError):
        verifier.verify(command)
    historical = verifier.verify_historical(command, signed_at=iso(signed_at))
    assert historical.accepted and historical.historical


def test_command_from_revoked_key_is_invalid_even_historically(
    registry: CrownKeyRegistry, crown_signer: TransientSigner
) -> None:
    """المفتاح المسحوب يُبطل الماضي — لأن السحب معناه أن الصفة لم تكن حقيقية."""
    signed_at = utc_now() - timedelta(minutes=5)
    command = make_command(crown_signer, issued_at=signed_at)
    registry.mark_compromised("CROWN-K1", reason="مادة المفتاح خرجت من العتاد")
    verifier = CrownCommandVerifier(registry, CommandLedger())
    outcome = verifier.verify_historical(command, signed_at=iso(signed_at))
    assert not outcome.accepted
    assert outcome.reason


def test_unknown_issuer_key_is_rejected(
    verifier: CrownCommandVerifier, crown_signer: TransientSigner
) -> None:
    """مفتاح مُصدِر غير مسجَّل يُرفَض — لا يُقبَل مفتاح يعرّف نفسه."""
    command = make_command(crown_signer, issuer_key_id="CROWN-GHOST")
    with pytest.raises(Exception):
        verifier.verify(command)


def test_pending_key_cannot_issue_commands(
    registry: CrownKeyRegistry, successor_signer: TransientSigner
) -> None:
    """مفتاح مسجَّل غير مُنشَّط لا يوقّع أوامر — التسجيل ليس تنشيطًا."""
    registry.register(
        CrownKeyRecord(
            key_id="CROWN-PENDING",
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
    verifier = CrownCommandVerifier(registry, CommandLedger())
    command = make_command(successor_signer, issuer_key_id="CROWN-PENDING")
    with pytest.raises(SignatureError):
        verifier.verify(command)
