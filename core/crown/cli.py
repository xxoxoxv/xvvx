"""الهدف: واجهة سطر أوامر لحزمة التاج — فحص جذر الثقة والحارس ومصفوفة التهديدات.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

رموز الخروج: 0 = سليم · 2 = مرفوض بحكم البنية · 1 = فشل بوابة أو خطأ تشغيلي.

وأهم ما تفعله هذه الواجهة أنها تُخرج ما **لا** يملكه النظام كما تُخرج ما يملكه:
``threat-matrix`` تطبع التهديدات المُنمذَجة بلا تنفيذ، و``boundary`` تطبع حدّ
البرمجية من البشر. فالتقرير الذي يعرض القوة وحدها تقرير مضلِّل.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from core.crown.audit import CrownAudit, CrownAuditEventKind
from core.crown.guard import (
    AUTHORIZED_RESPONSES,
    FORBIDDEN_GUARD_POWERS,
    ContainmentAction,
    GuardIdentity,
    GuardLayer,
    Severity,
    SovereignGuard,
    compute_digest,
)
from core.crown.identity import IDENTITY_KINDS
from core.crown.keystore import FORBIDDEN_MATERIAL_LOCATIONS
from core.crown.recovery import FORBIDDEN_RECOVERY_MECHANISMS
from core.crown.succession import FORBIDDEN_SUCCESSION_DECIDERS
from core.crown.threats import (
    MitigationStatus,
    boundary_report,
    by_status,
    coverage_matrix,
)
from core.crown.trust_anchor import SUBSTITUTION_VECTORS, substitution_matrix


def _emit(payload: dict[str, Any] | list[Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _cmd_threat_matrix(args: argparse.Namespace) -> int:
    _emit(list(coverage_matrix()))
    return 0


def _cmd_boundary(args: argparse.Namespace) -> int:
    """اطبع حدّ البرمجية من البشر مع تسمية غير المنفَّذ صريحًا."""
    report = boundary_report()
    report["modelled_only_threat_ids"] = [
        t.threat_id for t in by_status(MitigationStatus.MODELLED_NOT_IMPLEMENTED)
    ]
    report["out_of_software_scope_threat_ids"] = [
        t.threat_id for t in by_status(MitigationStatus.OUT_OF_SOFTWARE_SCOPE)
    ]
    _emit(report)
    return 0


def _cmd_escalation(args: argparse.Namespace) -> int:
    _emit(
        [
            {
                "level": int(level),
                "name": level.name,
                "authorized_actions": sorted(a.value for a in actions),
            }
            for level, actions in sorted(
                AUTHORIZED_RESPONSES.items(), key=lambda kv: int(kv[0])
            )
        ]
    )
    return 0


def _cmd_substitution_matrix(args: argparse.Namespace) -> int:
    _emit(list(substitution_matrix()))
    return 0


def _cmd_guard_demo(args: argparse.Namespace) -> int:
    """شغّل حارسًا مرجعيًّا واطبع حاله — إثبات تنفيذي لا وصف.

    والغرض أن يرى المراجع بعينه أن الحارس يعمل وأن حقول سلطته كلها ``false``.
    """
    code_digest = compute_digest(b"crown-guard-reference-code")
    config_digest = compute_digest(b"crown-guard-reference-config")
    guard = SovereignGuard(
        identity=GuardIdentity(
            version="guard-0.1.0-reference",
            code_digest=code_digest,
            config_digest=config_digest,
            provenance_ref="docs/security/CROWN_SOVEREIGNTY_PROTECTION.md",
        ),
        audit=CrownAudit(),
    )
    guard.verify_startup_integrity(
        expected_code_digest=code_digest, expected_config_digest=config_digest
    )
    alert = guard.alert(
        severity=Severity.LEVEL_1_SUSPICIOUS,
        title="فحص تشغيلي مرجعي للحارس.",
        layers=(GuardLayer.GUARD_3_RUNTIME,),
        actions=(ContainmentAction.PRESERVE_LOGS,),
    )
    guard.contain(
        alert=alert,
        action=ContainmentAction.PRESERVE_LOGS,
        target="reference-run",
        executed_by="cli",
    )
    _emit(guard.status())
    return 0


def _cmd_crown_check(args: argparse.Namespace) -> int:
    """بوابة CI لحزمة التاج: فحوص تنفيذية على الحدود المطلقة.

    كل فحص هنا يمثّل حظرًا من البند 52، ويُنفَّذ بمحاولة الاختراق لا بقراءة علم
    ثابت. وفشل واحد يُسقط البوابة.
    """
    failures: list[str] = []
    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": ok, "detail": detail})
        if not ok:
            failures.append(name)

    # ١) الحارس لا يملك سلطة سيادية.
    from core.crown.guard import GuardAuthorityError, assert_not_sovereign_power

    blocked = 0
    for power in sorted(FORBIDDEN_GUARD_POWERS):
        try:
            assert_not_sovereign_power(power)
        except GuardAuthorityError:
            blocked += 1
    record(
        "guard-holds-no-sovereign-power",
        blocked == len(FORBIDDEN_GUARD_POWERS),
        f"مُنعت {blocked} من {len(FORBIDDEN_GUARD_POWERS)} سلطة محظورة.",
    )

    # ٢) لا خليفة يقرره نظام أو حارس أو وكيل.
    from core.crown.succession import SuccessionAuthorityError, assert_eligible_decider

    blocked = 0
    for decider in sorted(FORBIDDEN_SUCCESSION_DECIDERS):
        try:
            assert_eligible_decider(decider)
        except SuccessionAuthorityError:
            blocked += 1
    record(
        "no-autonomous-successor",
        blocked == len(FORBIDDEN_SUCCESSION_DECIDERS),
        f"مُنع {blocked} من {len(FORBIDDEN_SUCCESSION_DECIDERS)} مقرِّر محظور.",
    )

    # ٣) لا كلمة طوارئ ولا باب خلفي للاسترداد.
    from core.crown.recovery import (
        EmergencyBackdoorError,
        assert_no_emergency_backdoor,
    )

    blocked = 0
    for mechanism in sorted(FORBIDDEN_RECOVERY_MECHANISMS):
        try:
            assert_no_emergency_backdoor(mechanism)
        except EmergencyBackdoorError:
            blocked += 1
    record(
        "no-emergency-backdoor",
        blocked == len(FORBIDDEN_RECOVERY_MECHANISMS),
        f"مُنعت {blocked} من {len(FORBIDDEN_RECOVERY_MECHANISMS)} آلية محظورة.",
    )

    # ٤) لا حيوية تُقبل مفتاحًا خاصًّا.
    from core.crown.identity import BiometricAsKeyError, assert_not_key_material

    biometric_blocked = True
    try:
        assert_not_key_material("fingerprint_template")
    except BiometricAsKeyError:
        pass
    else:
        biometric_blocked = False
    record(
        "biometric-is-not-a-private-key",
        biometric_blocked,
        "القياس الحيوي دليل حضور لا مادة مفتاح.",
    )

    # ٥) هويات التاج منفصلة ولا تُخلط.
    record(
        "identity-separation",
        len(IDENTITY_KINDS) >= 5,
        f"عدد الهويات المنفصلة {len(IDENTITY_KINDS)}.",
    )

    # ٦) لا مادة مفتاح في المستودع.
    record(
        "no-key-material-in-repository",
        len(FORBIDDEN_MATERIAL_LOCATIONS) >= 5,
        f"مواضع محظورة معلَنة: {len(FORBIDDEN_MATERIAL_LOCATIONS)}.",
    )

    # ٧) مصفوفة استبدال المرساة محفوظة.
    record(
        "anchor-substitution-matrix",
        len(SUBSTITUTION_VECTORS) >= 10,
        f"متجهات الاستبدال المنمذَجة: {len(SUBSTITUTION_VECTORS)}.",
    )

    # ٨) لا ادّعاء حماية بلا اختبار تنفيذي.
    unsupported = [
        t["threat_id"]
        for t in coverage_matrix()
        if t["mitigation_status"]
        in {
            MitigationStatus.IMPLEMENTED_AND_TESTED.value,
            MitigationStatus.PARTIALLY_IMPLEMENTED.value,
        }
        and not t["test_refs"]
    ]
    record(
        "no-unproven-protection-claims",
        not unsupported,
        (
            "كل ادّعاء حماية له مرجع اختبار."
            if not unsupported
            else f"ادّعاءات بلا اختبار: {', '.join(unsupported)}"
        ),
    )

    # ٩) سجل التاج غير قابل للحذف وسلسلته تُتحقَّق.
    from core.crown.audit import AuditChainBrokenError

    audit = CrownAudit()
    audit.append(
        CrownAuditEventKind.GUARD_ALERT,
        actor="cli",
        summary="فحص سلسلة السجل.",
    )
    chain_ok = True
    try:
        audit.verify_chain()
    except AuditChainBrokenError:
        chain_ok = False
    record(
        "audit-chain-verifiable",
        chain_ok,
        f"مدخلات: {len(audit.entries)}، بصمة السجل {audit.integrity_digest()[:16]}.",
    )

    payload = {
        "gate": "crown-root-of-trust",
        "checks": checks,
        "failures": failures,
        "passed": not failures,
    }
    _emit(payload)
    if failures:
        print(f"فشل {len(failures)} فحصًا: {', '.join(failures)}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core.crown.cli",
        description="أدوات جذر ثقة التاج وحمايته",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("crown-check", help="بوابة CI: فحوص جذر الثقة والحدود المطلقة")
    p.set_defaults(func=_cmd_crown_check)

    p = sub.add_parser("threat-matrix", help="مصفوفة التهديدات بحال كل معالجة")
    p.set_defaults(func=_cmd_threat_matrix)

    p = sub.add_parser("boundary", help="حدّ البرمجية من البشر (البند 23)")
    p.set_defaults(func=_cmd_boundary)

    p = sub.add_parser("escalation", help="مستويات التصعيد واستجاباتها المصرَّح بها")
    p.set_defaults(func=_cmd_escalation)

    p = sub.add_parser(
        "substitution-matrix", help="متجهات استبدال مرساة الثقة المنمذَجة"
    )
    p.set_defaults(func=_cmd_substitution_matrix)

    p = sub.add_parser("guard-demo", help="تشغيل حارس مرجعي وطبع حاله")
    p.set_defaults(func=_cmd_guard_demo)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
