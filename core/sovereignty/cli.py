"""الهدف: واجهة سطر أوامر لنواة السيادة — تنصيب التاج وفحص السيادة وبوابات CI.

المالك: core/sovereignty/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

رموز الخروج: 0 = سليم/مسموح · 2 = مرفوض دستوريًا · 1 = فشل بوابة أو خطأ تشغيلي.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

from core.constitutional_engine.model import ActionRequest, Branch
from core.sovereignty.crown import CrownError, crown_is_provisioned, load_crown, provision_crown
from core.sovereignty.gateway import (
    FORBIDDEN_BYPASS_PARAMS,
    SovereignGateway,
    SovereigntyViolation,
)
from core.sovereignty.prerogatives import (
    FEDERALISM_BYPASS_ACTIONS,
    IMMUNE_CLAUSES,
    ROYAL_AUTHORITY_EROSION_ACTIONS,
    ROYAL_EXCLUSIVE_ACTIONS,
)

_ARTICLE_010 = (
    Path(__file__).resolve().parents[2]
    / "core"
    / "constitution"
    / "articles"
    / "010-royal-sovereignty.md"
)


def _cmd_provision_crown(args: argparse.Namespace) -> int:
    try:
        crown = provision_crown(Path(args.out), holder=args.holder)
    except CrownError as exc:
        print(f"[PROVISION] ✗ {exc}", file=sys.stderr)
        return 1
    print(f"[PROVISION] ✓ نُصِّب التاج — المفتاح «{crown.key_id}» لحامله «{crown.holder}».")
    print("[PROVISION]   المفتاح العام نُشر في royal/crown/CROWN_KEYS.json")
    print(f"[PROVISION]   المفتاح الخاص كُتب في {args.out} بصلاحية 600.")
    print("[PROVISION] ⚠ انقل المفتاح الخاص إلى حرز الملك واحذفه من هذا الجهاز.")
    print("[PROVISION] ⚠ لا نسخة منه في المستودع ولا في أي نظام تشغيلي للدولة.")
    return 0


def _cmd_crown_status(_args: argparse.Namespace) -> int:
    if not crown_is_provisioned():
        print("[CROWN] التاج غير مُنصَّب — الاختصاص الملكي الحصري مُجمَّد لا منقول.")
        print("[CROWN] التنصيب: python -m core.sovereignty.cli provision-crown --out <مسار خارج المستودع>")
        return 0
    crown = load_crown()
    print(f"[CROWN] ✓ مُنصَّب — المفتاح «{crown.key_id}» · الحامل «{crown.holder}»")
    print(f"[CROWN]   الخوارزمية Ed25519 · التنصيب {crown.provisioned_at}")
    return 0


def _cmd_sovereignty_check(_args: argparse.Namespace) -> int:
    """بوابة CI: هل السيادة الملكية ما زالت محروسة بنيويًا؟"""
    failures: list[str] = []

    if not _ARTICLE_010.exists():
        failures.append("المادة العاشرة مفقودة من الدستور.")

    gateway = SovereignGateway()
    if gateway.engine.unguarded_articles():
        failures.append(
            f"مواد بلا حراسة: {', '.join(gateway.engine.unguarded_articles())}"
        )

    coverage = gateway.engine.coverage()
    royal_rules = coverage.get("A010", 0)
    if royal_rules < 7:
        failures.append(f"قواعد المادة العاشرة {royal_rules} والحد الأدنى 7.")

    # لا راية تجاوز في البوابة — تُفحَص من توقيع الدوال نفسها
    for name in ("execute", "review", "__init__"):
        params = set(inspect.signature(getattr(SovereignGateway, name)).parameters)
        leaked = params & FORBIDDEN_BYPASS_PARAMS
        if leaked:
            failures.append(f"SovereignGateway.{name} يقبل راية تجاوز: {sorted(leaked)}")

    for expected in ("royal_sovereignty", "royal_exclusive_authority", "royal_authority_immunity"):
        if expected not in IMMUNE_CLAUSES:
            failures.append(f"النص «{expected}» فُقد من قائمة النصوص المحصَّنة.")

    if failures:
        for f in failures:
            print(f"[SOVEREIGNTY] ✗ {f}", file=sys.stderr)
        return 1

    print(f"[SOVEREIGNTY] ✓ المادة العاشرة سارية ومحروسة بـ{royal_rules} قاعدة تنفيذية.")
    print(f"[SOVEREIGNTY] ✓ {len(ROYAL_EXCLUSIVE_ACTIONS)} اختصاصًا ملكيًا حصريًا محميًا.")
    print(f"[SOVEREIGNTY] ✓ {len(ROYAL_AUTHORITY_EROSION_ACTIONS)} فعل تآكل للسلطة مرفوض من كل طرف.")
    print(f"[SOVEREIGNTY] ✓ {len(FEDERALISM_BYPASS_ACTIONS)} فعل تجاوز للفدرالية مرفوض.")
    print(f"[SOVEREIGNTY] ✓ {len(IMMUNE_CLAUSES)} نصًا محصَّنًا لا يُعدَّل من أي طرف.")
    print("[SOVEREIGNTY] ✓ البوابة السيادية بلا راية تجاوز واحدة.")
    print(f"[SOVEREIGNTY]   حالة التاج: {gateway.crown_status()}")
    return 0


def _cmd_gate(args: argparse.Namespace) -> int:
    """تشغيل فعل عبر البوابة السيادية — بلا مرسوم، لعرض المنع."""
    gateway = SovereignGateway()
    request = ActionRequest(
        actor=Branch(args.actor),
        action=args.action,
        target=args.target or "",
    )
    try:
        gateway.execute(request, lambda: "EXECUTED")
    except SovereigntyViolation as exc:
        print(exc.verdict.explain())
        print("\n[GATEWAY] لم يُستدعَ المُنفِّذ. الفعل لم يقع.")
        return 2
    print("[GATEWAY] ALLOW — نُفِّذ الفعل.")
    return 0


def _cmd_prerogatives(_args: argparse.Namespace) -> int:
    print(
        json.dumps(
            {
                "royal_exclusive_actions": sorted(ROYAL_EXCLUSIVE_ACTIONS),
                "royal_authority_erosion_actions": sorted(ROYAL_AUTHORITY_EROSION_ACTIONS),
                "federalism_bypass_actions": sorted(FEDERALISM_BYPASS_ACTIONS),
                "immune_clauses": sorted(IMMUNE_CLAUSES),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m core.sovereignty.cli",
        description="نواة السيادة — السيادة الملكية كقوة نافذة (E2)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("provision-crown", help="مراسم تنصيب التاج (توليد مفتاح الملك)")
    p.add_argument("--out", required=True, help="مسار المفتاح الخاص — خارج المستودع إلزامًا")
    p.add_argument("--holder", default="الملك", help="حامل التاج")
    p.set_defaults(func=_cmd_provision_crown)

    p = sub.add_parser("crown-status", help="حالة التاج")
    p.set_defaults(func=_cmd_crown_status)

    p = sub.add_parser("sovereignty-check", help="بوابة CI: حراسة السيادة الملكية")
    p.set_defaults(func=_cmd_sovereignty_check)

    p = sub.add_parser("gate", help="تشغيل فعل عبر البوابة السيادية")
    p.add_argument("--actor", required=True, choices=[b.value for b in Branch])
    p.add_argument("--action", required=True)
    p.add_argument("--target", default="")
    p.set_defaults(func=_cmd_gate)

    p = sub.add_parser("prerogatives", help="طبع مفردات الاختصاص والحصانة")
    p.set_defaults(func=_cmd_prerogatives)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
