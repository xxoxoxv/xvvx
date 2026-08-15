"""
واجهة سطر الأوامر للنواة الدستورية — Constitutional Kernel CLI (E1)
الهدف: إتاحة استخدام المحرك من CI ومن يد المشغّل البشري: ختم الدستور، التحقق من الأختام، تقييم فعل، فحص سلامة السجل.
النطاق: تحويل الأوامر إلى استدعاءات للمحرك وطباعة النتيجة. لا منطق دستوري هنا.
المالك: core/constitutional_engine/
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

Usage:
    python -m core.constitutional_engine.cli seal
    python -m core.constitutional_engine.cli verify        # بوابة CI
    python -m core.constitutional_engine.cli coverage
    python -m core.constitutional_engine.cli ledger-verify
    python -m core.constitutional_engine.cli evaluate --actor executive --action legislate
"""

from __future__ import annotations

import argparse
import json
import sys

from .articles import load_articles, verify_seals, write_seals
from .engine import ConstitutionalEngine
from .ledger import ConstitutionalLedger
from .model import ActionRequest, Branch


def _cmd_seal(_: argparse.Namespace) -> int:
    payload = write_seals()
    print(f"[SEAL] خُتمت {len(payload['seals'])} مادة دستورية.")
    for aid, e in payload["seals"].items():
        print(f"  {aid}  {e['sha256'][:16]}…  {e['title']}")
    return 0


def _cmd_verify(_: argparse.Namespace) -> int:
    problems = verify_seals()
    if problems:
        print("[VERIFY] ✗ الدستور مُعدَّل خارج إجراء التعديل (المادة الخامسة):")
        for p in problems:
            print(f"  - {p}")
        return 1
    arts = load_articles()
    print(f"[VERIFY] ✓ {len(arts)} مادة مطابقة لختمها المسجل.")
    return 0


def _cmd_coverage(_: argparse.Namespace) -> int:
    eng = ConstitutionalEngine()
    cov = eng.coverage()
    print(f"[COVERAGE] {len(eng.rules)} قاعدة تنفيذية تحرس {len(eng.articles)} مادة\n")
    print("| المادة | العنوان | قواعد |")
    print("|---|---|---:|")
    for a in eng.articles:
        print(f"| {a.article_id} | {a.title} | {cov[a.article_id]} |")
    unguarded = eng.unguarded_articles()
    if unguarded:
        print(f"\n[COVERAGE] ✗ مواد بلا حراسة تنفيذية: {', '.join(unguarded)}")
        return 1
    print("\n[COVERAGE] ✓ كل مادة سارية تحرسها قاعدة تنفيذية واحدة على الأقل.")
    return 0


def _cmd_ledger_verify(args: argparse.Namespace) -> int:
    led = ConstitutionalLedger(args.ledger)
    problems = led.verify_chain()
    if problems:
        print("[LEDGER] ✗ السجل الدستوري مكسور:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"[LEDGER] ✓ سلسلة سليمة — {len(led)} قيد · الرأس {led.head_hash()[:16]}…")
    return 0


def _cmd_evaluate(args: argparse.Namespace) -> int:
    eng = ConstitutionalEngine(ledger_path=args.ledger)
    req = ActionRequest(
        actor=Branch(args.actor),
        action=args.action,
        target=args.target,
        human_approved=args.human_approved,
        human_signature=args.human_signature,
        approving_branches=tuple(Branch(b) for b in (args.approvals or [])),
        channel=args.channel,
        criticality=args.criticality,
        kill_switch_level=args.kill_switch_level,
        review_days=args.review_days,
        council_approval_pct=args.council_pct,
        has_identity_header=not args.no_identity_header,
    )
    verdict = eng.evaluate(req)
    if args.json:
        print(json.dumps(verdict.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(verdict.explain())
        print(f"\nقيد السجل: {verdict.ledger_entry_hash[:16]}…")
    return 0 if verdict.allowed else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="constitutional_engine", description="النواة الدستورية — AMOS-Federation")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("seal", help="اختم المواد الدستورية (بعد تعديل مصرح به فقط)").set_defaults(fn=_cmd_seal)
    sub.add_parser("verify", help="تحقق من عدم تعديل الدستور — بوابة CI").set_defaults(fn=_cmd_verify)
    sub.add_parser("coverage", help="تغطية القواعد التنفيذية لكل مادة").set_defaults(fn=_cmd_coverage)

    lv = sub.add_parser("ledger-verify", help="تحقق من سلامة سلسلة السجل الدستوري")
    lv.add_argument("--ledger", default=None)
    lv.set_defaults(fn=_cmd_ledger_verify)

    ev = sub.add_parser("evaluate", help="اعرض فعلًا على الدستور")
    ev.add_argument("--actor", required=True, choices=[b.value for b in Branch])
    ev.add_argument("--action", required=True)
    ev.add_argument("--target", default="")
    ev.add_argument("--human-approved", action="store_true")
    ev.add_argument("--human-signature", default=None)
    ev.add_argument("--approvals", nargs="*", choices=[b.value for b in Branch])
    ev.add_argument("--channel", default="direct")
    ev.add_argument("--criticality", default="normal", choices=["normal", "critical", "fateful"])
    ev.add_argument("--kill-switch-level", type=int, default=0)
    ev.add_argument("--review-days", type=int, default=0)
    ev.add_argument("--council-pct", type=float, default=0.0)
    ev.add_argument("--no-identity-header", action="store_true")
    ev.add_argument("--ledger", default=None)
    ev.add_argument("--json", action="store_true")
    ev.set_defaults(fn=_cmd_evaluate)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    sys.exit(main())
