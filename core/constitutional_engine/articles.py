"""
محمّل المواد الدستورية وبصماتها — Constitutional Article Loader & Sealing (E1)
الهدف: قراءة نصوص المواد من القرص، وحساب بصمة SHA-256 لكل مادة، وكشف أي تعديل غير مصرح به على الدستور.
النطاق: core/constitution/articles/*.md و core/constitution/preamble.md. لا يعدّل نص أي مادة إطلاقًا.
تاريخ آخر تعديل: 2026-08-16 (E3) — الديباجة صارت مختومة فعلًا بعد أن كان ثابتها معلَّقًا بلا استخدام.
المالك: core/constitutional_engine/
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المبدأ (المادة الخامسة): النظام لا يملك تعديل ميثاق حوكمة نفسه. هذه الوحدة تقرأ وتختم فقط.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

# جذر المستودع = ثلاث مستويات فوق هذا الملف
REPO_ROOT = Path(__file__).resolve().parents[2]
ARTICLES_DIR = REPO_ROOT / "core" / "constitution" / "articles"
PREAMBLE = REPO_ROOT / "core" / "constitution" / "preamble.md"
SEALS_PATH = REPO_ROOT / "core" / "constitution" / "ARTICLE_SEALS.json"

_ARTICLE_FILE = re.compile(r"^(\d{3})-(.+)\.md$")


@dataclass(frozen=True)
class Article:
    """مادة دستورية واحدة كما هي على القرص."""

    article_id: str      # "A001"
    number: int          # 1
    slug: str            # "identity"
    title: str           # "المادة الأولى — الهوية"
    path: Path
    text: str
    sha256: str

    @property
    def in_force(self) -> bool:
        return "سارية المفعول" in self.text


def _sha256(text: str) -> str:
    # التطبيع: أسطر LF فقط، وبلا مسافات ذيلية — حتى لا تتغير البصمة بتغيير المحرر
    normalized = "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").split("\n")).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _title_of(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def load_preamble(path: Path | None = None) -> Article | None:
    """حمّل الديباجة كنص دستوري مختوم برقم `PRE`.

    الديباجة ليست مادة — لا رقم لها ولا قواعد تنفيذية — لكنها **نص دستوري** من
    رتبة المواد، فيها تُعلَن غايات الدولة. كانت في E1 معلَّقة: الثابت `PREAMBLE`
    مُعلَنًا وغير مُستخدَم، فكان نصها **قابلًا للتعديل بصمت** بلا ختم يكشفه —
    وهو ما رصده فحص هوية المستودع في E3. تُختَم الآن كما تُختَم المواد.

    ترجع `None` إذا لم يوجد ملف الديباجة، فلا يتوقف المحرك على وجودها.
    """
    src = Path(path) if path else PREAMBLE
    if not src.exists():
        return None
    text = src.read_text(encoding="utf-8")
    return Article(
        article_id="PRE",
        number=0,
        slug="preamble",
        title=_title_of(text, "الديباجة"),
        path=src,
        text=text,
        sha256=_sha256(text),
    )


def load_articles(articles_dir: Path | None = None) -> list[Article]:
    """حمّل كل المواد مرتبة برقمها. يرفع خطأً إذا لم يوجد أي مادة —
    دولة بلا دستور مقروء لا يجوز أن تُقلع صامتة."""
    d = Path(articles_dir) if articles_dir else ARTICLES_DIR
    articles: list[Article] = []
    for p in sorted(d.glob("*.md")):
        m = _ARTICLE_FILE.match(p.name)
        if not m:
            continue  # README.md و NUCLEUS.md ليست مواد
        number, slug = int(m.group(1)), m.group(2)
        text = p.read_text(encoding="utf-8")
        articles.append(
            Article(
                article_id=f"A{number:03d}",
                number=number,
                slug=slug,
                title=_title_of(text, f"المادة {number}"),
                path=p,
                text=text,
                sha256=_sha256(text),
            )
        )
    if not articles:
        raise ConstitutionNotFoundError(
            f"لا توجد مواد دستورية قابلة للقراءة في {d}. "
            "المحرك يرفض العمل بلا دستور — لا سقوط صامت."
        )
    return sorted(articles, key=lambda a: a.number)


class ConstitutionNotFoundError(RuntimeError):
    """يُرفع عندما يتعذر تحميل الدستور. لا يُبتلع أبدًا."""


class SealMismatchError(RuntimeError):
    """يُرفع عند اكتشاف تعديل غير مصرح به على نص مادة."""


def load_constitutional_text(articles_dir: Path | None = None) -> list[Article]:
    """كل نص دستوري خاضع للختم: الديباجة ثم المواد مرتبة.

    هذه هي الدالة التي يعتمدها الختم والتحقق — لا `load_articles` — حتى لا يبقى
    نص دستوري خارج الحراسة.
    """
    pre = load_preamble()
    arts = load_articles(articles_dir)
    return ([pre] if pre else []) + arts


def current_seals(articles: list[Article] | None = None) -> dict[str, str]:
    arts = articles if articles is not None else load_constitutional_text()
    return {a.article_id: a.sha256 for a in arts}


def write_seals(path: Path | None = None, articles: list[Article] | None = None) -> dict:
    """اختم الدستور. يُستدعى يدويًا فقط بعد تعديل مصرح به وفق المادة الخامسة."""
    arts = articles if articles is not None else load_constitutional_text()
    target = Path(path) if path else SEALS_PATH
    payload = {
        "$comment": (
            "بصمات SHA-256 للمواد الدستورية (المادة الخامسة). "
            "أي اختلاف = تعديل غير مصرح به. لا يُحدَّث هذا الملف إلا بمرسوم تعديل موثق في amendments/."
        ),
        "schema_version": 1,
        "algorithm": "sha256",
        "normalization": "LF endings, trailing whitespace stripped, document stripped",
        # المسار نسبةً لجذر المستودع لا الاسم المجرّد: الديباجة خارج مجلد المواد،
        # ومن قرأ الاسم وحده افترض موضعًا فأخطأ (التفسير INT-002).
        "seals": {
            a.article_id: {
                # نسبةً لجذر المستودع متى أمكن؛ وإلا فالاسم (مواد من مسار مؤقت
                # في الاختبارات). لا try/except صامت — الشرط مُعلَن.
                "file": (
                    a.path.relative_to(REPO_ROOT).as_posix()
                    if a.path.is_relative_to(REPO_ROOT) else a.path.name
                ),
                "title": a.title,
                "sha256": a.sha256,
            }
            for a in arts
        },
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def verify_seals(path: Path | None = None, articles: list[Article] | None = None) -> list[str]:
    """قارن الدستور الحالي بختمه المسجل. يرجع قائمة المخالفات (فارغة = سليم)."""
    target = Path(path) if path else SEALS_PATH
    arts = articles if articles is not None else load_constitutional_text()
    if not target.exists():
        return [f"SEALS_MISSING: لا يوجد ختم دستوري في {target}. شغّل `seal` أولًا."]

    recorded = json.loads(target.read_text(encoding="utf-8")).get("seals", {})
    problems: list[str] = []
    live = {a.article_id: a for a in arts}

    for aid, entry in sorted(recorded.items()):
        if aid not in live:
            problems.append(f"TEXT_REMOVED: {aid} مختوم لكنه غير موجود — حذف نص دستوري يتطلب تعديلًا دستوريًا.")
            continue
        if live[aid].sha256 != entry.get("sha256"):
            problems.append(
                f"SEAL_MISMATCH: {aid} ({live[aid].title}) — "
                f"مختومة {str(entry.get('sha256'))[:12]}… والحالية {live[aid].sha256[:12]}…"
            )
    for aid in sorted(set(live) - set(recorded)):
        # نص جديد بلا ختم = تسريب إلى الدستور، ويلزمه مرسوم. أما نص قائم منذ
        # التأسيس يُدخَل في الحراسة فليس تسريبًا (التفسير INT-002).
        problems.append(
            f"TEXT_UNSEALED: {aid} ({live[aid].title}) نص دستوري بلا ختم. "
            "إن كان نصًّا جديدًا فلا يدخل الدستور إلا بمرسوم تعديل (المادة الخامسة "
            "والعاشرة · 2 · 1). وإن كان قائمًا منذ التأسيس بحرفه فختمه توسيع حراسة "
            "لا تعديل (التفسير INT-002) — اختمه بـ `seal`."
        )
    return problems
