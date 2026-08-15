#!/usr/bin/env python3
"""
ختّام حقول الهوية المشتقّة — Derived Identity Field Stamper

الهدف: إكمال حقلي المادة التاسعة **المشتقّين من واقع المستودع** في كل
       `README.md`: «تاريخ آخر تعديل» من سجل git، و«المحتويات» من الجرد الفعلي
       للمجلد مع هدف كل ملف مقروءًا من ترويسته.
النطاق: حقلان فقط في ملفات `README.md`. لا تكتب هذه الأداة تعريفًا ولا نطاقًا ولا
        مالكًا — تلك حقول يكتبها إنسان، ولا يجوز تلفيقها.
المالك: tools/governance — المجلس التأسيسي
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

## الحد الفاصل الذي تلتزمه هذه الأداة
«تاريخ آخر تعديل» و«المحتويات» **وقائع** تُقرأ من git ومن نظام الملفات، فتوليدها
دقة لا تلفيق، وكتابتها باليد تتعفّن في أول تعديل. أما «التعريف» و«النطاق»
و«المالك» فأحكام قصد بشري، لو ولّدتها الأداة لأنتجت التزامًا شكليًا كاذبًا —
فهي تتركها، ويظل الفحص يرفض المجلد حتى يكتبها إنسان.

الاستخدام:
    python tools/governance/stamp_readme_identity.py            # ختم
    python tools/governance/stamp_readme_identity.py --check    # فحص بلا كتابة
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    "node_modules", ".venv", "venv", "env", "htmlcov", ".tox", "dist", "build",
}

MTIME_HEADS = ("## تاريخ آخر تعديل", "## Last Modified", "## آخر تعديل")
CONTENTS_HEADS = ("## المحتويات", "## Contents", "## المكوّنات", "## البنية")

# الأنماط التي نستخرج منها هدف ملف مجاور لوصفه في قائمة المحتويات
PURPOSE_PATTERNS = (
    re.compile(r"^#\s*الهدف:\s*(.+)$", re.M),
    re.compile(r"^#\s*Purpose:\s*(.+)$", re.M),
    re.compile(r"^#\s+Purpose:\s+(.+)$", re.M),
    re.compile(r"^الهدف:\s*(.+)$", re.M),
    re.compile(r"^#\s+(.+)$", re.M),  # عنوان md
)

MAX_DESC = 95


def git_last_modified(path: Path) -> str:
    """تاريخ آخر تعديل من سجل git — واقع لا تقدير."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", str(path)],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        stamp = out.stdout.strip()
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", stamp):
            return stamp
    except (OSError, subprocess.SubprocessError) as exc:  # لا يُبتلع
        print(f"  [تنبيه] تعذّر قراءة سجل git لـ {path}: {exc}", file=sys.stderr)
    return date.today().isoformat()


def describe(path: Path) -> str:
    """وصف مختصر لملف، مأخوذ من ترويسة الملف نفسه."""
    if path.is_dir():
        n = sum(1 for _ in path.iterdir())
        return f"مجلد فرعي ({n} عنصرًا) — انظر بطاقته"
    if path.name == "README.md":
        return "بطاقة هوية هذا المجلد (المادة التاسعة)"
    try:
        head = path.read_text(encoding="utf-8", errors="ignore")[:1400]
    except OSError as exc:
        # السبب يُعلَن في الجرد وعلى الخطأ المعياري: ملف لا يُقرأ خبرٌ لا يُكتَم.
        print(f"  [تنبيه] تعذّر قراءة {path}: {exc}", file=sys.stderr)
        return f"ملف غير مقروء ({exc.strerror or exc.__class__.__name__})"
    if path.suffix == ".py":
        m = re.search(r'"""\s*\n?(.+?)\n', head)
        if m and m.group(1).strip():
            return _clip(m.group(1))
    for pat in PURPOSE_PATTERNS:
        m = pat.search(head)
        if m and m.group(1).strip():
            return _clip(m.group(1))
    return {"json": "بيانات مهيكلة", "yaml": "إعداد أو سجل مهيكل",
            "yml": "إعداد أو سجل مهيكل", "sql": "مخطّط أو استعلام قاعدة بيانات",
            "rego": "سياسة كسياسة-كشيفرة"}.get(path.suffix.lstrip("."), "ملف تابع")


def _clip(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip().strip("#*—-").strip())
    text = re.sub(r"^(الهدف|Purpose|التعريف)\s*[:：]\s*", "", text)
    return text[: MAX_DESC - 1] + "…" if len(text) > MAX_DESC else text


def build_contents(directory: Path) -> str:
    entries = sorted(
        (p for p in directory.iterdir() if p.name not in SKIP_DIRS
         and not p.name.endswith((".pyc", ".egg-info"))),
        key=lambda p: (p.is_dir(), p.name),
    )
    lines = [f"- `{p.name}{'/' if p.is_dir() else ''}` — {describe(p)}" for p in entries]
    return "\n".join(lines) if lines else "- (فارغ)"


# نائبٌ يضعه `write_domain_readmes.py` مكان الحقل المشتقّ ليملأه هذا الخاتم.
PLACEHOLDER = "<!-- يُملأ آليًا بـ stamp_readme_identity.py -->"


def _section_body(text: str, heads: tuple[str, ...]) -> str | None:
    """نص القسم تحت أول ترويسة مطابقة — أو None إذا لا ترويسة."""
    for h in heads:
        # العناوين مُخزَّنة بعلامات «##»، فتُجرَّد قبل بناء النمط وإلا تضاعفت.
        m = re.search(
            rf"^#+\s*{re.escape(h.lstrip('#').strip())}\s*$\n(.*?)(?=^#+\s|\Z)",
            text, re.M | re.S,
        )
        if m:
            return m.group(1)
    return None


def _has(text: str, heads: tuple[str, ...]) -> bool:
    """الحقل موجود **ومملوء**. ترويسة فوق فراغ أو فوق نائب ليست حقلًا.

    كان الفحص وجودَ العنوان فحسب، فكان `## المحتويات` فوق تعليق نائب يُحتسب
    حقلًا مكتملًا — امتثالٌ شكلي. صار الفحص على المضمون.
    """
    body = _section_body(text, heads)
    if body is None:
        return False
    stripped = body.replace(PLACEHOLDER, "").strip()
    return bool(stripped)


def _fill(text: str, heads: tuple[str, ...], value: str) -> str:
    """املأ قسمًا قائمًا لكنه فارغ/نائب، بدل إلحاق قسم مكرّر في الذيل."""
    for h in heads:
        pat = re.compile(
            rf"(^#+\s*{re.escape(h.lstrip('#').strip())}\s*$\n)(.*?)(?=^#+\s|\Z)",
            re.M | re.S,
        )
        if pat.search(text):
            return pat.sub(lambda m: f"{m.group(1)}{value}\n\n", text, count=1)
    return text


def stamp(readme: Path) -> bool:
    """أكمل الحقلين المشتقّين إن نقصا. يرجع True إن تغيّر الملف."""
    text = readme.read_text(encoding="utf-8")
    original = text
    directory = readme.parent

    if not _has(text, MTIME_HEADS):
        stamp_date = git_last_modified(readme)
        filled = _fill(text, MTIME_HEADS, stamp_date)
        text = (filled if filled != text
                else text.rstrip("\n") + f"\n\n## تاريخ آخر تعديل\n{stamp_date}\n")

    if not _has(text, CONTENTS_HEADS):
        contents = build_contents(directory)
        filled = _fill(text, CONTENTS_HEADS, contents)
        text = (filled if filled != text
                else text.rstrip("\n") + "\n\n## المحتويات\n" + contents + "\n")

    if text != original:
        readme.write_text(text, encoding="utf-8")
        return True
    return False


def iter_readmes(root: Path):
    for readme in sorted(root.rglob("README.md")):
        if any(p in SKIP_DIRS for p in readme.parts):
            continue
        if any(p.endswith(".egg-info") for p in readme.parts):
            continue
        # بطاقات المواطنين المستوردين تُولَّد بأداتها الخاصة
        if "identities/imported" in readme.as_posix() and readme.parent.name != "imported":
            continue
        yield readme


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ختّام حقول الهوية المشتقّة")
    parser.add_argument("root", nargs="?", default=str(REPO_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    pending = []
    for readme in iter_readmes(Path(args.root)):
        text = readme.read_text(encoding="utf-8")
        if not (_has(text, MTIME_HEADS) and _has(text, CONTENTS_HEADS)):
            pending.append(readme)

    if args.check:
        if pending:
            print(f"[README STAMP] ✗ {len(pending)} بطاقة ينقصها حقل مشتقّ.")
            for p in pending[:20]:
                print(f"  - {p}")
            return 1
        print("[README STAMP] ✓ كل البطاقات تحمل حقليها المشتقّين.")
        return 0

    changed = sum(1 for readme in pending if stamp(readme))
    print(f"[README STAMP] ✓ خُتمت {changed} بطاقة بحقليها المشتقّين من git والجرد.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
