"""الهدف: إثبات الاستمرارية السيادية من الطرف إلى الطرف عبر مسار تنفيذ واحد.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

ملاحظة صدق تسبق كل ادّعاء هنا: السلسلة نفسها كانت مُختبَرة قبل هذا الملف في
``test_crown_grand_tests.py::test_grand_crown_lifecycle_end_to_end``، لكنها كانت
مُركَّبة **داخل الاختبار**: الاختبار هو من رتّب البوابات، فلو نسي مسارُ إنتاجٍ بوابةً
لما سقط اختبار. وهذا الملف يقود ``SovereignSession`` — المسار المنفَّذ نفسه — فيصير
النسيان مُكتشَفًا: من حذف بوابة من الوحدة سقط هنا.

ويضيف ما لم يكن مغطّى: الأمر قبل التحقق من المرساة، والتنفيذ أثناء توقف الاستمرارية،
وإعادة اللعب بعد الخلافة، والنقض الخفيّ، والمفتاح النشط الثاني.
"""

from __future__ import annotations

import pytest

from core.crown.audit import CrownAuditEventKind
from core.crown.command import ReplayError, SignatureError
from core.crown.continuity import ContinuityState, CrownContinuity, StateDeclaration
from core.crown.guard import GuardAuthorityError
from core.crown.key_registry import KeyState, KeyStateError
from core.crown.sovereign_session import (
    AnchorNotVerifiedError,
    ContinuityRefusalError,
    FalseCrownError,
    SovereignSession,
)
from tests.crown.test_crown_grand_tests import (
    full_succession,
    running_guard,
    signed_command,
)


@pytest.fixture
def session(registry, anchor, audit) -> SovereignSession:
    """جلسة سيادية بمكوّنات حقيقية تتشارك السجل نفسه."""
    continuity = CrownContinuity(audit=audit)
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_AUTHENTICALLY_ACTIVE,
            declared_by="مراسم التصديق",
            reason="تصديق حضور الملك بمسار موثوق.",
        )
    )
    return SovereignSession(
        registry=registry,
        anchor=anchor,
        guard=running_guard(audit),
        audit=audit,
        continuity=continuity,
    )


# ═════════════════════════════════════════════════════════════════════════════
# السلسلة الكاملة عبر المسار المنفَّذ.
# ═════════════════════════════════════════════════════════════════════════════


def test_sovereign_continuity_through_the_executed_path(
    session: SovereignSession, registry, root_signer, crown_signer, successor_signer
) -> None:
    """K1 ← مرساة ← D1 ← لا نقض ← تنفيذ ← سجل ← إبطال ← K2 ← D2 ← رفض K1.

    وكل خطوة هنا يُنفّذها ``SovereignSession`` لا الاختبار، فالمقيس هو المسار.
    """
    from tests.crown.conftest import sign_manifest

    session.verify_anchor(sign_manifest(root_signer, registry))
    assert registry.active_or_raise().key_id == "CROWN-K1"

    d1 = signed_command(
        crown_signer, command_id="D1", issuer_key_id="CROWN-K1", nonce="e2e-1", sequence=1
    )
    record = session.execute(d1)
    assert record.command_id == "D1"

    session.declare_key_compromised(
        "CROWN-K1",
        reason="تسريب مؤكَّد من البيئة الأساسية.",
        witnesses=("W1", "W2", "W3"),
    )
    assert registry.get("CROWN-K1").state is KeyState.COMPROMISED

    # والاختراق يُبطل الماضي بحكم القاعدة المنفَّذة، ويُعلَن سببه صراحةً.
    historical = session.verify_historical(d1)
    assert historical.accepted is False
    assert "COMPROMISED" in historical.reason

    full_succession(
        registry, successor_signer, audit=session.audit, predecessor_key_id="CROWN-K1"
    )
    assert registry.active_or_raise().key_id == "CROWN-K2"
    # ولا قفز في الحالات: الاكتمال لا يُعلَن قبل إعلان بدء المراسم رسميًّا.
    session.continuity.declare(
        StateDeclaration(
            state=ContinuityState.SUCCESSION_FORMALLY_INITIATED,
            declared_by="المؤسسة القانونية المختصة",
            reason="بدء مراسم الخلافة بقرار قانوني.",
            witnesses=("W1", "W2", "W3"),
        )
    )
    session.continuity.declare(
        StateDeclaration(
            state=ContinuityState.SUCCESSION_COMPLETED,
            declared_by="المؤسسة القانونية المختصة",
            reason="اكتملت المراسم بإشهاد.",
            witnesses=("W1", "W2", "W3"),
        )
    )

    d2 = signed_command(
        successor_signer,
        command_id="D2",
        issuer_key_id="CROWN-K2",
        nonce="e2e-2",
        sequence=2,
    )
    # ومفتاحٌ جديد لا يكفي: الأوامر لا تُستأنف قبل إعلان حضور الملك الجديد.
    with pytest.raises(ContinuityRefusalError):
        session.execute(d2)
    session.continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_PRESENT,
            declared_by="ديوان المراسم",
            reason="حضور الملك الجديد بعد اكتمال المراسم.",
        )
    )
    assert session.execute(d2).command_id == "D2"

    late = signed_command(
        crown_signer, command_id="D3", issuer_key_id="CROWN-K1", nonce="e2e-3", sequence=3
    )
    with pytest.raises(SignatureError):
        session.execute(late)

    snapshot = session.snapshot()
    assert snapshot["active_key_ids"] == ["CROWN-K2"]
    assert snapshot["lineage"] == ["CROWN-K1", "CROWN-K2"]
    assert snapshot["executed_commands"] == ["D1", "D2"]
    assert snapshot["guard_holds_sovereign_authority"] is False
    assert snapshot["session_grants_authority"] is False
    session.assert_no_false_crown()


def test_planned_rotation_preserves_the_past(
    session: SovereignSession, registry, root_signer, crown_signer, successor_signer
) -> None:
    """التدوير المخطَّط يُحيل المفتاح ولا يمحو قراراته — خلاف الاختراق.

    والفرق ليس تفصيلًا: لو أبطل التدويرُ الماضيَ لبطل كل قرار سيادي سابق كلما
    دُوِّر مفتاح، ولو لم يُبطله الاختراقُ لبقي قرارُ مزوِّرٍ نافذًا.
    """
    from tests.crown.conftest import make_provenance, sign_manifest

    session.verify_anchor(sign_manifest(root_signer, registry))
    d1 = signed_command(
        crown_signer, command_id="D-ROT", issuer_key_id="CROWN-K1", nonce="rot-1", sequence=1
    )
    session.execute(d1)
    registry.rotate(
        new_key_id="CROWN-K2",
        algorithm="Ed25519",
        public_key_hex=successor_signer.public_hex,
        provenance=make_provenance(ceremony_kind="CROWN_ROTATION"),
    )
    outcome = session.verify_historical(d1)
    assert outcome.accepted is True
    assert registry.get("CROWN-K1").state is KeyState.RETIRED


def test_audit_records_the_whole_chain(
    session: SovereignSession, registry, root_signer, crown_signer
) -> None:
    """السلسلة تترك أثرًا في السجل، والسجل يكشف تحريفه."""
    from tests.crown.conftest import sign_manifest

    session.verify_anchor(sign_manifest(root_signer, registry))
    session.execute(
        signed_command(
            crown_signer,
            command_id="D-AUD",
            issuer_key_id="CROWN-K1",
            nonce="aud-1",
            sequence=1,
        )
    )
    assert session.audit.by_kind(CrownAuditEventKind.ROYAL_DECISION)
    assert session.audit.by_kind(CrownAuditEventKind.TRUST_ANCHOR_EVENT)
    session.audit.verify_chain()


# ═════════════════════════════════════════════════════════════════════════════
# قائمة الخصومة: كل بند محاولةٌ فعلية تُرفَض، لا وصفٌ لرفضٍ مزعوم.
# ═════════════════════════════════════════════════════════════════════════════


def test_compromise_declaration_without_witnesses_is_refused(
    session: SovereignSession,
) -> None:
    """إبطال مفتاح التاج حدثٌ سيادي، فلا يُعلَن بلا شاهد بشري."""
    with pytest.raises(ContinuityRefusalError):
        session.declare_key_compromised("CROWN-K1", reason="اشتباه.", witnesses=())


def test_command_before_anchor_verification_is_refused(
    session: SovereignSession, crown_signer
) -> None:
    """أمرٌ قبل تثبيت المرساة تنفيذٌ بثقة لم تُثبَت — يُرفَض."""
    with pytest.raises(AnchorNotVerifiedError):
        session.execute(
            signed_command(
                crown_signer,
                command_id="D-EARLY",
                issuer_key_id="CROWN-K1",
                nonce="early",
                sequence=1,
            )
        )


def test_paused_continuity_refuses_new_commands(
    session: SovereignSession, registry, root_signer, crown_signer
) -> None:
    """التوقف الآمن يمنع الأوامر الجديدة — ولا يخترع سيادة بديلة."""
    from tests.crown.conftest import sign_manifest

    session.verify_anchor(sign_manifest(root_signer, registry))
    session.continuity.pause_continuity(
        declared_by="ديوان الأمن",
        reason="انقطاع مسار التصديق.",
        witnesses=("W1", "W2", "W3"),
    )
    with pytest.raises(ContinuityRefusalError):
        session.execute(
            signed_command(
                crown_signer,
                command_id="D-PAUSED",
                issuer_key_id="CROWN-K1",
                nonce="paused",
                sequence=1,
            )
        )
    session.continuity.assert_no_autonomous_successor()


def test_replay_after_execution_is_refused(
    session: SovereignSession, registry, root_signer, crown_signer
) -> None:
    """إعادة الأمر نفسه بعد تنفيذه تُرفَض — التنفيذ مرة واحدة."""
    from tests.crown.conftest import sign_manifest

    session.verify_anchor(sign_manifest(root_signer, registry))
    command = signed_command(
        crown_signer,
        command_id="D-REPLAY",
        issuer_key_id="CROWN-K1",
        nonce="replay-1",
        sequence=1,
    )
    session.execute(command)
    with pytest.raises(ReplayError):
        session.execute(command)


def test_guard_veto_attempt_is_refused_not_silently_allowed(
    session: SovereignSession,
) -> None:
    """محاولة نقض من الحارس تُرفَض بالاسم، والرفض يُسجَّل دليلًا."""
    reason = session.assert_guard_has_no_veto("D-ANY")
    assert reason
    with pytest.raises(GuardAuthorityError):
        session.guard.assert_cannot_veto(command_id="D-ANY", command_is_valid=True)


def test_hidden_veto_path_is_treated_as_false_crown(
    session: SovereignSession, monkeypatch
) -> None:
    """لو صار النقض ممكنًا بلا رفض، وجب أن ينكسر المسار لا أن يمضي.

    وهذا اختبار للبوابة نفسها: بوابةٌ لا تسقط حين يُنزَع شرطها ليست بوابة.
    """
    monkeypatch.setattr(
        session.guard, "assert_cannot_veto", lambda **_: None, raising=True
    )
    with pytest.raises(FalseCrownError):
        session.assert_guard_has_no_veto("D-ANY")


def test_second_active_key_is_a_false_crown(session: SovereignSession, registry) -> None:
    """تاجان لا تاج: السجل يرفض تنشيط ثانٍ، والجلسة ترفض حالًا فيه نشطان."""
    from tests.crown.conftest import make_provenance, utc_now, iso
    from core.crown.key_registry import CrownKeyRecord, LineageKind

    registry.register(
        CrownKeyRecord(
            key_id="CROWN-FAKE",
            version=2,
            algorithm="Ed25519",
            public_key_hex="cd" * 32,
            state=KeyState.PENDING,
            lineage_kind=LineageKind.ROTATION,
            predecessor_key_id="CROWN-K1",
            registered_at=iso(utc_now()),
            provenance=make_provenance(ceremony_kind="CROWN_ROTATION"),
        )
    )
    with pytest.raises(KeyStateError):
        registry.activate("CROWN-FAKE")

    # وحتى لو زُرِعت الحالة قسرًا في السجل، الجلسة تكشفها قبل أي تنفيذ.
    object.__setattr__(registry.get("CROWN-FAKE"), "state", KeyState.ACTIVE)
    with pytest.raises(FalseCrownError):
        session.assert_no_false_crown()


def test_session_holds_no_authority_of_its_own(session: SovereignSession) -> None:
    """الجلسة ممرّ لا سلطة: لا تُنشئ مفتاحًا ولا تُتمّ خلافة ولا تمنح صلاحية."""
    assert not hasattr(session, "issue_command")
    assert not hasattr(session, "create_key")
    assert not hasattr(session, "appoint_successor")
    assert session.snapshot()["session_grants_authority"] is False
