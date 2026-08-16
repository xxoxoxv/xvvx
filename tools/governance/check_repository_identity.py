#!/usr/bin/env python3
"""
فحص هوية المستودع — Repository Identity Checker (v2)

الهدف: قياس الالتزام الفعلي بالمادة التاسعة (قانون هوية الملفات) لا مجرد وجود
       سطرٍ ما في أول الملف.
النطاق: كل ملف `.md` `.py` `.yaml` `.yml` `.rego` `.sql` `.json` في المستودع.
المالك: tools/governance — المجلس التأسيسي
تاريخ الإنشاء: 2026-08-15
تاريخ آخر تعديل: 2026-08-16

المادة التاسعة تفرض شيئين:

1. **كل مجلد يحمل `README.md`** يُعلن اسمه وتعريفه ونطاقه ومالكه وتاريخي إنشائه
   وآخر تعديله ومحتوياته. الوجود وحده لا يكفي — الحقول مطلوبة.
2. **كل ملف يُعلن هدفه** في ترويسته، بالعربية أو الإنجليزية.

النسخة الأولى من هذه الأداة كانت تقبل قائمة عبارات عشوائية (`# سجل`، `# مقدمو`،
`# `…)، فكان أي ملف `.md` فيه عنوان واحد يمر، وكان ملف يحمل ترويسة كاملة بصيغة
`# Purpose:` يُرفض. الأداة الآن تفحص **حقولًا** لا عبارات، وتقبل الصيغتين
العربية والإنجليزية — فصارت أدق وأصعب في الوقت نفسه.

أنواع المخالفات:
  MISSING_README        مجلد فيه ملفات ولا `README.md`
  README_MISSING_FIELD  `README.md` ينقصه حقل من حقول المادة التاسعة
  MISSING_PURPOSE       ملف لا يُعلن هدفه في ترويسته

الاستخدام:
    python tools/governance/check_repository_identity.py .
    python tools/governance/check_repository_identity.py . --json out.json
    python tools/governance/check_repository_identity.py . --kind MISSING_PURPOSE
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ── نطاق الفحص ───────────────────────────────────────────────────────────────

SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    "node_modules", ".venv", "venv", "env", ".egg-info", "egg-info",
    "htmlcov", ".tox", "dist", "build",
}

EXTENSIONS = ("*.md", "*.py", "*.yaml", "*.yml", "*.rego", "*.sql", "*.json")

# ملفات معفاة: ملفات نظام، وأمثلة صريحة، ومخرجات مولَّدة آليًا لا تحمل ترويسة
# يدوية — هويتها موثّقة في README مجلدها، وتوليدها موثّق في أداة التوليد.
EXEMPT_NAMES = {
    ".gitignore", ".gitattributes", "LICENSE",
    "truth_matrix.json", "truth_baseline.json", "CROWN_KEYS.json",
    "ARTICLE_SEALS.json", "package-lock.json", "poetry.lock",
}
EXEMPT_SUBSTRINGS = (".example", ".lock")

# ── حقول المادة التاسعة ──────────────────────────────────────────────────────

# كل حقل: (المعرّف، مرادفاته المقبولة). يكفي مرادف واحد.
_PLACEHOLDER = re.compile(r"<!--.*?-->", re.S)
_HORIZONTAL_RULE = re.compile(r"^\s*-{3,}\s*$", re.M)
# حاشية البطاقة: فقرة مائلة في ذيل الملف («*بطاقة هوية إقليم — المادة التاسعة…*»).
_CARD_FOOTER = re.compile(r"^\s*\*[^*][\s\S]*?\*\s*$", re.M)


def strip_boilerplate(body: str) -> str:
    """جرّد ما ليس مضمونًا: النائب، والفاصل الأفقي، وحاشية البطاقة.

    كان الفحص يقبل قسمًا فارغًا إذا وقع **آخر** أقسام البطاقة، لأن حاشية الذيل
    تقع تحته فتُحتسب مضمونًا له. فكانت `## المحتويات` فوق تعليق نائب تمرّ.
    الحاشية ليست جوابًا عن سؤال الحقل، فتُجرَّد قبل الحكم.
    """
    cleaned = _PLACEHOLDER.sub("", body)
    cleaned = _CARD_FOOTER.sub("", cleaned)
    cleaned = _HORIZONTAL_RULE.sub("", cleaned)
    return cleaned.strip()


def _field_filled(text: str, aliases: tuple[str, ...]) -> bool:
    """هل يوجد قسم بأحد هذه العناوين وتحته مضمون فعلي؟"""
    for alias in aliases:
        head = alias.lstrip("#").strip()
        m = re.search(
            rf"^#+\s*{re.escape(head)}\s*$\n(.*?)(?=^#+\s|\Z)",
            text, re.M | re.S,
        )
        if m and strip_boilerplate(m.group(1)):
            return True
    return False


README_FIELDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("التعريف", ("## التعريف", "## Definition", "## الهدف", "## Purpose")),
    ("النطاق", ("## النطاق", "## Scope")),
    ("المالك", ("## المالك", "## Owner")),
    ("تاريخ الإنشاء", ("## تاريخ الإنشاء", "## Created", "## تاريخ السحب")),
    ("تاريخ آخر تعديل", ("## تاريخ آخر تعديل", "## Last Modified", "## آخر تعديل")),
    ("المحتويات", ("## المحتويات", "## Contents", "## المكوّنات", "## البنية")),
)

# إعلان الهدف — يُقبل بالعربية أو الإنجليزية، وبأي صيغة تعليق.
PURPOSE_MARKERS = (
    "الهدف", "التعريف", "الغرض",
    "Purpose", "purpose:", "Objective", "Description",
    "$comment", "$schema", "$id",
)

HEADER_WINDOW = 1400  # عدد المحارف التي تُقرأ من أول الملف

# ── إعفاء النص الدستوري المختوم (التفسير INT-001) ────────────────────────────
#
# التفسير الدستوري INT-001 يقرر أن شرط الترويسة في المادة التاسعة · 2 لا ينطبق
# على ملفات النص الدستوري **المختومة**، لأن هويتها ثابتة بعنوانها وبختمها في
# ARTICLE_SEALS.json، ولأن إلزامها بترويسة يوجب تعديل نص لا يُعدَّل (المادة
# الخامسة). والإعفاء **مشروط بالختم**: ملف مادة غير مختوم لا يُعفى — فلا يصير
# هذا بابًا خلفيًا لإخراج نص من الحراسة.
#
# core/constitution/interpretations/INT-001-article-009-scope.md

SEALS_PATH = Path("core/constitution/ARTICLE_SEALS.json")
ARTICLES_DIR = Path("core/constitution/articles")


def sealed_text_files(root: Path) -> frozenset[Path]:
    """مسارات النص الدستوري المختوم فعلًا — لا كل ما في مجلد الدستور."""
    seals = root / SEALS_PATH
    if not seals.exists():
        return frozenset()
    try:
        data = json.loads(seals.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:  # يُبلَّغ ولا يُبتلع
        print(f"  [تنبيه] سجل الأختام غير مقروء ({exc}) — لا إعفاء لأي نص.",
              file=sys.stderr)
        return frozenset()

    paths: set[Path] = set()
    for entry in (data.get("seals") or {}).values():
        if not isinstance(entry, dict):
            continue
        rel = entry.get("file")
        # الإعفاء مشروط بوجود بصمة فعلية: مدخل بلا sha256 ليس ختمًا فليس إعفاءً.
        if rel and entry.get("sha256"):
            # `file` مسار نسبةً لجذر المستودع. تُقبل الصيغة القديمة (الاسم
            # المجرّد داخل مجلد المواد) للتوافق مع أختام سابقة.
            cand = root / rel
            paths.add((cand if cand.exists() else root / ARTICLES_DIR / rel).resolve())
    return frozenset(paths)


def _iter_files(root: Path):
    for pattern in EXTENSIONS:
        for path in sorted(root.rglob(pattern)):
            if any(p in SKIP_DIRS for p in path.parts):
                continue
            if any(p.endswith(".egg-info") for p in path.parts):
                continue
            if path.name in EXEMPT_NAMES:
                continue
            if any(s in path.name for s in EXEMPT_SUBSTRINGS):
                continue
            yield path


def check_readmes(root: Path) -> list[dict]:
    """كل مجلد فيه ملفات يحمل README.md، وكل README يحمل حقول المادة التاسعة."""
    violations: list[dict] = []
    for item in sorted(root.rglob("*")):
        if not item.is_dir():
            continue
        if any(p in SKIP_DIRS for p in item.parts) or item.name.endswith(".egg-info"):
            continue
        try:
            has_files = any(f.is_file() for f in item.iterdir())
        except OSError as exc:  # مجلد لا يُقرأ — سببه يُنقَل ولا يُبتلع
            violations.append({
                "kind": "MISSING_README", "path": str(item / "README.md"),
                "detail": f"المجلد غير قابل للقراءة ({exc}) — تعذّر التحقق",
            })
            continue
        if not has_files:
            continue

        readme = item / "README.md"
        if not readme.exists():
            violations.append({
                "kind": "MISSING_README", "path": str(readme),
                "detail": "مجلد فيه ملفات بلا بطاقة هوية (المادة التاسعة · 1)",
            })
            continue

        text = readme.read_text(encoding="utf-8", errors="ignore")
        # الحقل يُحتسب موجودًا إذا كان **مملوءًا**. ترويسة فوق فراغ، أو فوق تعليق
        # نائب ينتظر أداة تملؤه، ليست حقل هوية — وقبولها امتثال شكلي يفرّغ المادة
        # التاسعة من معناها.
        missing = [
            name for name, aliases in README_FIELDS
            if not _field_filled(text, aliases)
        ]
        if missing:
            violations.append({
                "kind": "README_MISSING_FIELD", "path": str(readme),
                "detail": "حقول ناقصة: " + " · ".join(missing),
            })
    return violations


def check_purposes(root: Path) -> list[dict]:
    """كل ملف يُعلن هدفه في ترويسته — عدا النص الدستوري المختوم (INT-001)."""
    violations: list[dict] = []
    sealed = sealed_text_files(root)
    for path in _iter_files(root):
        if path.name == "README.md":
            continue  # يُفحص بحقوله في check_readmes
        if path.resolve() in sealed:
            continue  # نص دستوري مختوم — هويته ختمه (التفسير INT-001)
        head = path.read_text(encoding="utf-8", errors="ignore")[:HEADER_WINDOW]
        if not any(m in head for m in PURPOSE_MARKERS):
            violations.append({
                "kind": "MISSING_PURPOSE", "path": str(path),
                "detail": "الملف لا يُعلن هدفه في ترويسته (المادة التاسعة · 2)",
            })
    return violations


def audit(root: Path) -> list[dict]:
    return check_readmes(root) + check_purposes(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="فحص هوية المستودع — المادة التاسعة")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--json", dest="json_out", help="اكتب التقرير الكامل بصيغة JSON")
    parser.add_argument("--kind", help="اعرض نوعًا واحدًا من المخالفات فقط")
    parser.add_argument("--quiet", action="store_true", help="اعرض العدد فقط")
    args = parser.parse_args(argv)

    root = Path(args.root)
    print(f"فحص هوية المستودع (المادة التاسعة): {root}")
    print("=" * 62)

    violations = audit(root)
    if args.kind:
        violations = [v for v in violations if v["kind"] == args.kind]

    counts: dict[str, int] = {}
    for v in violations:
        counts[v["kind"]] = counts.get(v["kind"], 0) + 1

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"total": len(violations), "counts": counts,
                        "violations": violations}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if not violations:
        print("\nنجح: كل مجلد يحمل بطاقة هوية كاملة، وكل ملف يُعلن هدفه.")
        return 0

    print(f"\nفشل: {len(violations)} مخالفة هوية")
    for kind, n in sorted(counts.items()):
        print(f"  - {kind}: {n}")
    if not args.quiet:
        print()
        for v in violations:
            print(f"  {v['kind']}: {v['path']}")
            print(f"      {v['detail']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
