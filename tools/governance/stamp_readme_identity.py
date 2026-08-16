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


def _is_dirty(path: Path) -> bool:
    """هل للملف تعديل غير مُلتزَم؟ فحينئذ تاريخ git أقدم من الواقع."""
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--", str(path)],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=20, check=False,
        )
        return bool(out.stdout.strip())
    except (OSError, subprocess.SubprocessError) as exc:  # لا يُبتلع
        print(f"  [تنبيه] تعذّر قراءة حالة git لـ {path}: {exc}", file=sys.stderr)
        return False


def expected_last_modified(readme: Path) -> str:
    """التاريخ الذي **يجب** أن تحمله البطاقة: اليوم إن كانت مُعدَّلة، وإلا سجل git."""
    if _is_dirty(readme):
        return date.today().isoformat()
    return git_last_modified(readme)


DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def declared_last_modified(text: str) -> str | None:
    """التاريخ المُعلَن في البطاقة، أو None إن لم يُعلَن."""
    body = _section_body(text, MTIME_HEADS)
    if body is None:
        return None
    m = DATE_RE.search(strip_boilerplate(body))
    return m.group(0) if m else None


def date_drift(readme: Path, text: str | None = None) -> tuple[str, str] | None:
    """(المُعلَن، الواقع) إذا كذب التاريخ المُعلَن، وإلا None.

    وجود الحقل لا يكفي: تاريخٌ يناقض سجل git **كذبٌ موثَّق**، وكان الفحص يقبله
    لأنه كان يسأل «أموجود؟» لا «أصادق؟».

    والكذب هنا نوعان لا ثالث لهما:

    * **متقادم:** المُعلَن أقدم من آخر تعديل فعلي — البطاقة تدّعي جمودًا كاذبًا.
    * **مستقبلي:** المُعلَن بعد اليوم — تاريخ لم يأتِ بعد.

    أما بطاقة تُعلن اليوم وسجلّها أمس فليست كذبًا: الملف عُدِّل في شجرة العمل أو
    خُتِم اليوم ثم لم يُلتزَم بعد. اشتراط المطابقة الحرفية هناك يُنتج تذبذبًا لا
    ينتهي: كل تصحيح يجعل الملف مُعدَّلًا فيغيّر ما يُتوقَّع منه.
    """
    text = readme.read_text(encoding="utf-8") if text is None else text
    declared = declared_last_modified(text)
    if declared is None:
        return None
    actual = expected_last_modified(readme)
    today = date.today().isoformat()
    if declared < actual:
        return (declared, actual)
    if declared > today:
        return (declared, today)
    return None


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


_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_HORIZONTAL_RULE = re.compile(r"^\s*-{3,}\s*$", re.M)
# حاشية البطاقة المائلة في الذيل — ليست مضمونًا لأي حقل.
_CARD_FOOTER = re.compile(r"^\s*\*[^*][\s\S]*?\*\s*$", re.M)


def strip_boilerplate(body: str) -> str:
    """جرّد النائب والفاصل وحاشية البطاقة قبل الحكم على الامتلاء.

    مطابقة لِما في `check_repository_identity.py`: القسم الأخير في البطاقة كانت
    تقع تحته الحاشية فتُحتسب مضمونًا له، فيمرّ حقلٌ فارغ.
    """
    cleaned = _HTML_COMMENT.sub("", body)
    cleaned = _CARD_FOOTER.sub("", cleaned)
    cleaned = _HORIZONTAL_RULE.sub("", cleaned)
    return cleaned.strip()


def _has(text: str, heads: tuple[str, ...]) -> bool:
    """الحقل موجود **ومملوء**. ترويسة فوق فراغ أو فوق نائب أو فوق حاشية ليست حقلًا."""
    body = _section_body(text, heads)
    if body is None:
        return False
    return bool(strip_boilerplate(body))


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
        stamp_date = expected_last_modified(readme)
        filled = _fill(text, MTIME_HEADS, stamp_date)
        text = (filled if filled != text
                else text.rstrip("\n") + f"\n\n## تاريخ آخر تعديل\n{stamp_date}\n")
    else:
        drift = date_drift(readme, text)
        if drift is not None:
            # التصحيح يكتب تاريخ اليوم: الملف يُعدَّل الآن بهذا التصحيح نفسه.
            text = _fill(text, MTIME_HEADS, date.today().isoformat())

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
    stale = []
    for readme in iter_readmes(Path(args.root)):
        text = readme.read_text(encoding="utf-8")
        if not (_has(text, MTIME_HEADS) and _has(text, CONTENTS_HEADS)):
            pending.append(readme)
            continue
        drift = date_drift(readme, text)
        if drift is not None:
            stale.append((readme, *drift))

    if args.check:
        if pending or stale:
            if pending:
                print(f"[README STAMP] ✗ {len(pending)} بطاقة ينقصها حقل مشتقّ.")
                for p in pending[:20]:
                    print(f"  - {p}")
            if stale:
                print(f"[README STAMP] ✗ {len(stale)} بطاقة تُعلن تاريخًا يناقض سجل git.")
                for readme, declared, expected in stale[:20]:
                    print(f"  - {readme}: مُعلَن {declared} · الواقع {expected}")
            return 1
        print("[README STAMP] ✓ كل البطاقات تحمل حقليها المشتقّين مطابقين للواقع.")
        return 0

    changed = sum(1 for readme in [*pending, *(r for r, _, _ in stale)] if stamp(readme))
    print(f"[README STAMP] ✓ خُتمت {changed} بطاقة بحقليها المشتقّين من git والجرد.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
