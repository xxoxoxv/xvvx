#!/usr/bin/env python3
"""الهدف: إثبات تنفيذي للاستمرارية السيادية — يُشغَّل ويُرجع صفرًا أو يُوقف البناء.

المالك: tools/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

سبب وجود هذه الأداة بجوار الاختبارات أن الاختبار يُثبت للمطوِّر، وهذه تُثبت
للمراجع: تُشغَّل خارج pytest، وتطبع سلسلة الأدلة سطرًا سطرًا، وتُرجع رمزًا غير صفري
عند أول ادّعاء لم يتحقق. فلا يبقى الإثبات حكاية في تقرير.

وهي **لا تصنع سلطة**: تقود ``core.crown.sovereign_session.SovereignSession`` نفسها
التي يقودها الإنتاج، بمفاتيح عابرة في الذاكرة لا تُكتب ولا تُصدَّر. ولو حُذفت بوابة
من الوحدة لسقطت هذه الأداة كما يسقط الاختبار.

الاستعمال:
    python tools/crown/prove_sovereign_continuity.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.crown.audit import CrownAudit, CrownAuditEventKind  # noqa: E402
from core.crown.continuity import (  # noqa: E402
    ContinuityState,
    CrownContinuity,
    StateDeclaration,
)
from core.crown.key_registry import KeyState  # noqa: E402
from core.crown.sovereign_session import (  # noqa: E402
    ContinuityRefusalError,
    SovereignSession,
)

# مساعدات الاختبار تُعاد استخدامها عن قصد: من كتب موقِّعًا ثانيًا للأداة خاطر بأن
# يُثبت شيئًا عن موقِّعه لا عن التاج.
from tests.crown.conftest import (  # noqa: E402
    TransientSigner,
    anchor_fingerprint,
    iso,
    make_provenance,
    sign_manifest,
    utc_now,
)
from tests.crown.test_crown_grand_tests import (  # noqa: E402
    full_succession,
    running_guard,
    signed_command,
)

WITNESSES = ("W1", "W2", "W3")


class ProofFailure(Exception):
    """ادّعاء في السلسلة لم يتحقق — والأداة تتوقف عنده ولا تكمل التقرير."""


def check(claim: str, condition: bool) -> None:
    if not condition:
        raise ProofFailure(claim)
    print(f"  [PASS] {claim}")


def build_session() -> tuple[SovereignSession, dict[str, object]]:
    """ابنِ جلسة سيادية حقيقية: سجل، ومرساة مثبَّتة، وحارس مُتحقَّق، وسجل تدقيق واحد."""
    from core.crown.key_registry import (
        CrownKeyRecord,
        CrownKeyRegistry,
        LineageKind,
    )
    from core.crown.trust_anchor import AnchorSource, CrownTrustAnchor, TrustPlane

    crown_signer = TransientSigner()
    root_signer = TransientSigner()
    successor_signer = TransientSigner()

    registry = CrownKeyRegistry()
    registry.register(
        CrownKeyRecord(
            key_id="CROWN-K1",
            version=1,
            algorithm="Ed25519",
            public_key_hex=crown_signer.public_hex,
            state=KeyState.PENDING,
            lineage_kind=LineageKind.GENESIS,
            predecessor_key_id=None,
            registered_at=iso(utc_now()),
            provenance=make_provenance(),
        )
    )
    registry.activate("CROWN-K1")

    fingerprint = anchor_fingerprint("ROOT-1", root_signer.public_hex)
    sources = tuple(
        AnchorSource(
            plane=plane,
            locator=locator,
            fingerprint=fingerprint,
            verified_at=iso(utc_now()),
            verifier=verifier,
        )
        for plane, locator, verifier in (
            (TrustPlane.PRINTED_FINGERPRINT, "سجل ورقي في خزانة محرزة", "أمين السجل"),
            (TrustPlane.OFFLINE_ROOT, "أصل معزول خارج الشبكة", "حافظ الأصل"),
            (TrustPlane.HUMAN_OUT_OF_BAND, "مطابقة شفوية بإشهاد", "شاهد ثالث"),
        )
    )
    anchor = CrownTrustAnchor(
        root_id="ROOT-1",
        root_public_key_hex=root_signer.public_hex,
        sources=sources,
        pinned_active_fingerprint=registry.active_or_raise().fingerprint,
    )

    audit = CrownAudit()
    continuity = CrownContinuity(audit=audit)
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_AUTHENTICALLY_ACTIVE,
            declared_by="مراسم التصديق",
            reason="تصديق حضور الملك بمسار موثوق.",
        )
    )
    session = SovereignSession(
        registry=registry,
        anchor=anchor,
        guard=running_guard(audit),
        audit=audit,
        continuity=continuity,
    )
    context = {
        "registry": registry,
        "audit": audit,
        "continuity": continuity,
        "crown_signer": crown_signer,
        "root_signer": root_signer,
        "successor_signer": successor_signer,
    }
    return session, context


def prove() -> None:
    session, ctx = build_session()
    registry = ctx["registry"]
    audit = ctx["audit"]
    continuity = ctx["continuity"]

    print("1) المرساة قبل كل شيء — الأمر قبلها مرفوض.")
    unanchored = signed_command(
        ctx["crown_signer"],
        command_id="D0",
        issuer_key_id="CROWN-K1",
        nonce="proof-0",
        sequence=1,
    )
    try:
        session.execute(unanchored)
    except Exception as exc:  # noqa: BLE001 — النوع نفسه يُفحَص أدناه
        check(
            "أمرٌ قبل التحقق من المرساة يُرفض بخطأ صريح",
            type(exc).__name__ == "AnchorNotVerifiedError",
        )
    else:
        raise ProofFailure("نُفِّذ أمر قبل التحقق من المرساة — ثقة بمفتاح لم يُثبت أصله")

    print("2) التحقق من المرساة بثلاثة مستويات مستقلة.")
    session.verify_anchor(sign_manifest(ctx["root_signer"], registry))
    check("المرساة مُتحقَّقة وخارج القناة", session.snapshot()["anchor_verified"] is True)

    print("3) لا تاج زائف قبل التنفيذ.")
    session.assert_no_false_crown()
    check("مفتاح نشط واحد فقط", session.snapshot()["active_key_ids"] == ["CROWN-K1"])

    print("4) D1 يُنفَّذ، والحارس لا يملك نقضًا.")
    d1 = signed_command(
        ctx["crown_signer"],
        command_id="D1",
        issuer_key_id="CROWN-K1",
        nonce="proof-1",
        sequence=1,
    )
    record = session.execute(d1)
    check("D1 نُفِّذ وقُيِّد في سجل الأوامر", record.command_id == "D1")
    check("الحارس رُفض عن نقض أمر صحيح", bool(session.assert_guard_has_no_veto("D1")))

    print("5) إعادة اللعب مرفوضة.")
    try:
        session.execute(d1)
    except Exception as exc:  # noqa: BLE001
        check("إعادة D1 تُرفض", type(exc).__name__ == "ReplayError")
    else:
        raise ProofFailure("نُفِّذ الأمر نفسه مرتين — إعادة لعب مقبولة")

    print("6) اختراق K1 — إعلان بشري بإشهاد، وبلا خليفة تلقائي.")
    session.declare_key_compromised(
        "CROWN-K1", reason="تسريب مؤكَّد.", witnesses=WITNESSES
    )
    check(
        "K1 صار مختَرقًا في السجل",
        registry.get("CROWN-K1").state is KeyState.COMPROMISED,
    )
    check(
        "الاستمرارية لا تقبل أوامر جديدة الآن",
        session.snapshot()["accepts_new_royal_commands"] is False,
    )
    historical = session.verify_historical(d1)
    check(
        "الاختراق يُبطل الماضي ويُعلن سببه (لا محو صامت)",
        historical.accepted is False and "COMPROMISED" in historical.reason,
    )

    print("7) خلافة شرعية كاملة إلى K2، ثم إعلان حضور الملك الجديد.")
    full_succession(
        registry,
        ctx["successor_signer"],
        audit=audit,
        predecessor_key_id="CROWN-K1",
    )
    for state, reason in (
        (ContinuityState.SUCCESSION_FORMALLY_INITIATED, "بدء المراسم بقرار قانوني."),
        (ContinuityState.SUCCESSION_COMPLETED, "اكتملت المراسم بإشهاد."),
    ):
        continuity.declare(
            StateDeclaration(
                state=state,
                declared_by="المؤسسة القانونية المختصة",
                reason=reason,
                witnesses=WITNESSES,
            )
        )
    d2 = signed_command(
        ctx["successor_signer"],
        command_id="D2",
        issuer_key_id="CROWN-K2",
        nonce="proof-2",
        sequence=2,
    )
    try:
        session.execute(d2)
    except ContinuityRefusalError as refusal:
        check(
            f"مفتاح جديد لا يستأنف الأوامر قبل إعلان حضور الملك ({refusal})",
            "SUCCESSION_COMPLETED" in str(refusal),
        )
    else:
        raise ProofFailure("استُؤنفت الأوامر بمجرد وجود مفتاح — استمرارية تُستنتج تلقائيًّا")
    continuity.declare(
        StateDeclaration(
            state=ContinuityState.KING_PRESENT,
            declared_by="ديوان المراسم",
            reason="حضور الملك الجديد بعد اكتمال المراسم.",
        )
    )
    check("D2 نُفِّذ بمفتاح الخليفة", session.execute(d2).command_id == "D2")

    print("8) أمر جديد بمفتاح K1 المختَرق مرفوض.")
    revived = signed_command(
        ctx["crown_signer"],
        command_id="D3",
        issuer_key_id="CROWN-K1",
        nonce="proof-3",
        sequence=3,
    )
    try:
        session.execute(revived)
    except Exception as exc:  # noqa: BLE001 — النوع يُفحَص باسمه أدناه
        # الرفض وحده لا يكفي دليلًا: لو رُفض لسبب عارض (نافذة، تسلسل) لبقي السؤال
        # قائمًا. فيُشترط أن يكون السبب هو حال المفتاح أو توقيعه.
        check(
            f"أمر K1 بعد الاختراق يُرفض بسبب حال المفتاح ({type(exc).__name__})",
            type(exc).__name__ in {"KeyStateError", "SignatureError", "CommandError"},
        )
    else:
        raise ProofFailure("مفتاح مختَرق أصدر أمرًا نافذًا — تاج زائف")

    print("9) لا تاج زائف بعد كل ذلك، ولا سلطة للجلسة نفسها.")
    session.assert_no_false_crown()
    snapshot = session.snapshot()
    check("الجلسة لا تمنح سلطة", snapshot["session_grants_authority"] is False)
    check(
        "الحارس لا يحمل سلطة سيادية",
        snapshot["guard_holds_sovereign_authority"] is False,
    )
    audit.verify_chain()  # يرفع استثناءً عند أي تحريف — والاستثناء يُفشل الأداة
    check("سلسلة التدقيق أُعيد بناؤها بلا تحريف", True)
    check(
        "قرارات ملكية مُقيَّدة في التدقيق",
        bool(audit.by_kind(CrownAuditEventKind.ROYAL_DECISION)),
    )
    check("سلالة المفاتيح متصلة", snapshot["lineage"] == ["CROWN-K1", "CROWN-K2"])
    check("المنفَّذ هو D1 و D2 فقط", snapshot["executed_commands"] == ["D1", "D2"])


def main() -> int:
    print("إثبات الاستمرارية السيادية عبر المسار المنفَّذ (SovereignSession)")
    print("=" * 72)
    try:
        prove()
    except ProofFailure as exc:
        print("=" * 72)
        print(f"BLOCKED — ادّعاء لم يتحقق: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001 — خطأ غير متوقع يبقى فشلًا لا يُبتلع
        print("=" * 72)
        print(f"BLOCKED — خطأ غير متوقع: {type(exc).__name__}: {exc}")
        return 1
    print("=" * 72)
    print("PASS — السلسلة السيادية أُثبتت تنفيذيًّا من الطرف إلى الطرف.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
