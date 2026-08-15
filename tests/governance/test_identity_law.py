"""
اختبارات قانون هوية الملفات — Article 009 Identity Law Tests (E3)
الهدف: إثبات أن مدقّق الهوية يقيس ما تقوله المادة التاسعة فعلًا: يرفض النقص،
       ولا يُعفي إلا ما أعفاه تفسير دستوري، ولا يقبل امتثالًا شكليًّا.
النطاق: tools/governance/check_repository_identity.py و stamp_readme_identity.py
        و write_domain_readmes.py. لا يفحص مضمون الوثائق نفسها.
المالك: tests/governance/
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المبدأ: المدقّق نفسه سلطة، والسلطة تُراقَب. هذه الاختبارات تحرس الحارس — فلو
وُسِّع المدقّق يومًا ليُمرِّر مخالفة، فشل هنا قبل أن يمرّ إلى `main`.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = REPO_ROOT / "tools" / "governance"


def _load(name: str):
    """حمّل أداة حوكمة كوحدة — أسماء ملفاتها ليست حزمة مستوردة."""
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


checker = _load("check_repository_identity")
stamper = _load("stamp_readme_identity")
writer = _load("write_domain_readmes")


COMPLETE_README = """# إقليم تجريبي

## التعريف
إقليم لاختبار المدقّق.

## النطاق
الاختبار وحده.

## المالك
tests/

## تاريخ الإنشاء
2026-08-16

## تاريخ آخر تعديل
2026-08-16

## المحتويات
- `a.md` — ملف تجريبي
"""


def _mk(tmp_path: Path, readme: str | None = COMPLETE_README) -> Path:
    d = tmp_path / "domain"
    d.mkdir()
    (d / "a.md").write_text("# ملف\nالهدف: اختبار.\n", encoding="utf-8")
    if readme is not None:
        (d / "README.md").write_text(readme, encoding="utf-8")
    return tmp_path


# ── الحدّ الأدنى: يمرّ الكامل ويفشل الناقص ──────────────────────────────────


def test_complete_domain_passes(tmp_path: Path) -> None:
    root = _mk(tmp_path)
    assert checker.check_readmes(root) == []
    assert checker.check_purposes(root) == []


def test_directory_without_readme_is_flagged(tmp_path: Path) -> None:
    root = _mk(tmp_path, readme=None)
    kinds = {v["kind"] for v in checker.check_readmes(root)}
    assert "MISSING_README" in kinds


def test_file_without_declared_purpose_is_flagged(tmp_path: Path) -> None:
    root = _mk(tmp_path)
    (root / "domain" / "silent.md").write_text("# بلا هدف\nنص.\n", encoding="utf-8")
    paths = [v["path"] for v in checker.check_purposes(root)]
    assert any("silent.md" in p for p in paths)


@pytest.mark.parametrize(
    "field",
    ["## التعريف", "## النطاق", "## المالك", "## تاريخ الإنشاء",
     "## تاريخ آخر تعديل", "## المحتويات"],
)
def test_each_required_field_is_actually_required(tmp_path: Path, field: str) -> None:
    """حذف أي حقل من حقول المادة التاسعة يجب أن يُرصَد — لا حقل تجميلي."""
    body = COMPLETE_README.replace(field, "## حقل_مبهم")
    root = _mk(tmp_path, readme=body)
    v = checker.check_readmes(root)
    assert v, f"حذف «{field}» مرّ بلا رصد"
    assert field.lstrip("# ") in v[0]["detail"]


# ── الامتثال الشكلي مرفوض ────────────────────────────────────────────────────


def test_empty_field_is_not_a_field(tmp_path: Path) -> None:
    """ترويسة فوق فراغ ليست هوية."""
    body = COMPLETE_README.replace("## النطاق\nالاختبار وحده.", "## النطاق\n")
    root = _mk(tmp_path, readme=body)
    v = checker.check_readmes(root)
    assert v and "النطاق" in v[0]["detail"]


def test_placeholder_comment_is_not_a_field(tmp_path: Path) -> None:
    """تعليق نائب ينتظر أداة تملؤه ليس هوية — وهي الثغرة التي كُشفت في E3."""
    body = COMPLETE_README.replace(
        "## المحتويات\n- `a.md` — ملف تجريبي",
        "## المحتويات\n<!-- يُملأ آليًا بـ stamp_readme_identity.py -->",
    )
    root = _mk(tmp_path, readme=body)
    v = checker.check_readmes(root)
    assert v and "المحتويات" in v[0]["detail"]


# ── الإعفاء الدستوري: مشروط بالختم (INT-001) ────────────────────────────────


def _mk_constitution(tmp_path: Path, *, seal: bool, sha: str | None = "abc123") -> Path:
    arts = tmp_path / "core" / "constitution" / "articles"
    arts.mkdir(parents=True)
    (arts / "001-identity.md").write_text(
        "# المادة الأولى — الهوية\n\nنص دستوري بلا ترويسة هدف.\n", encoding="utf-8"
    )
    seals = tmp_path / "core" / "constitution" / "ARTICLE_SEALS.json"
    entry: dict = {"file": "core/constitution/articles/001-identity.md",
                   "title": "المادة الأولى — الهوية"}
    if sha is not None:
        entry["sha256"] = sha
    seals.write_text(
        json.dumps({"seals": {"A001": entry} if seal else {}}, ensure_ascii=False),
        encoding="utf-8",
    )
    return tmp_path


def test_sealed_article_is_exempt_but_unsealed_is_not(tmp_path: Path) -> None:
    """جوهر INT-001: الختم هو سبب الإعفاء، فلا إعفاء بلا ختم.

    هذا هو الاختبار الذي يمنع تحوّل التفسير إلى باب خلفي: لو أُعفي نص غير مختوم،
    صار كل من أراد إخراج ملف من الحراسة يسمّيه «مادة».
    """
    sealed = _mk_constitution(tmp_path / "s", seal=True)
    unsealed = _mk_constitution(tmp_path / "u", seal=False)

    assert checker.check_purposes(sealed) == [], "نص مختوم يجب أن يُعفى (INT-001)"

    flagged = [v["path"] for v in checker.check_purposes(unsealed)]
    assert any("001-identity.md" in p for p in flagged), \
        "نص غير مختوم لا يُعفى — الإعفاء معلَّق بالختم"


def test_seal_entry_without_hash_grants_no_exemption(tmp_path: Path) -> None:
    """مدخل بلا بصمة ليس ختمًا، فليس إعفاءً."""
    root = _mk_constitution(tmp_path, seal=True, sha=None)
    flagged = [v["path"] for v in checker.check_purposes(root)]
    assert any("001-identity.md" in p for p in flagged)


def test_unreadable_seal_registry_exempts_nothing(tmp_path: Path) -> None:
    """سجل أختام معطوب لا يُبتلع خطؤه ولا يُعفي شيئًا."""
    root = _mk_constitution(tmp_path, seal=True)
    (root / "core" / "constitution" / "ARTICLE_SEALS.json").write_text(
        "{ليس JSON", encoding="utf-8"
    )
    assert checker.sealed_text_files(root) == frozenset()


# ── الخاتم: يشتقّ ولا يخترع ─────────────────────────────────────────────────


def test_stamper_fills_placeholder_in_place_without_duplicating(tmp_path: Path) -> None:
    """يملأ القسم القائم، ولا يُلحق قسمًا ثانيًا بالاسم نفسه."""
    body = COMPLETE_README.replace(
        "## المحتويات\n- `a.md` — ملف تجريبي",
        "## المحتويات\n<!-- يُملأ آليًا بـ stamp_readme_identity.py -->",
    )
    root = _mk(tmp_path, readme=body)
    readme = root / "domain" / "README.md"

    assert stamper.stamp(readme) is True
    out = readme.read_text(encoding="utf-8")
    assert out.count("## المحتويات") == 1, "تضاعف القسم بدل ملئه"
    assert "a.md" in out
    assert "يُملأ آليًا" not in out


def test_stamper_is_idempotent(tmp_path: Path) -> None:
    root = _mk(tmp_path)
    readme = root / "domain" / "README.md"
    stamper.stamp(readme)
    before = readme.read_text(encoding="utf-8")
    assert stamper.stamp(readme) is False
    assert readme.read_text(encoding="utf-8") == before


def test_stamper_never_writes_judgement_fields(tmp_path: Path) -> None:
    """التعريف والنطاق والمالك أحكام بشرية — لا تُولَّد ولو نقصت."""
    body = "# إقليم\n\n## تاريخ الإنشاء\n2026-08-16\n"
    root = _mk(tmp_path, readme=body)
    readme = root / "domain" / "README.md"
    stamper.stamp(readme)
    out = readme.read_text(encoding="utf-8")
    for judgement in ("## التعريف", "## النطاق", "## المالك"):
        assert judgement not in out, f"الخاتم اختلق «{judgement}» — امتثال زائف"


# ── كاتب بطاقات الأقاليم: لا يخترع تعريفًا ولا يزعم قدرة ─────────────────────


def test_writer_refuses_domain_with_no_declared_goal(tmp_path: Path, monkeypatch) -> None:
    """إقليم بلا هدف مُعلَن ولا تعريف يدوي: يتوقف ولا يخترع."""
    d = tmp_path / "ghost"
    d.mkdir()
    (d / "NUCLEUS.md").write_text("# إقليم\n\n## الحالة\nstub\n", encoding="utf-8")
    monkeypatch.setitem(writer.SCOPES, "ghost", ("نطاق", "مالك"))
    with pytest.raises(SystemExit):
        writer.build_readme(tmp_path, "ghost")


def test_writer_transcribes_goal_and_cites_its_source(tmp_path: Path, monkeypatch) -> None:
    d = tmp_path / "real"
    d.mkdir()
    (d / "NUCLEUS.md").write_text(
        "# إقليم حقيقي\n\n## الهدف\nهدف مُعلَن سابقًا.\n\n## الحالة\nنشط\n",
        encoding="utf-8",
    )
    (d / "code.py") .write_text("# الهدف: كود.\n", encoding="utf-8")
    monkeypatch.setitem(writer.SCOPES, "real", ("نطاق مكتوب يدويًا.", "tests/"))
    out = writer.build_readme(tmp_path, "real")
    assert "هدف مُعلَن سابقًا." in out
    assert "NUCLEUS.md" in out, "لم يُنسب التعريف إلى مصدره"


def test_writer_declares_empty_domain_as_unproven(tmp_path: Path, monkeypatch) -> None:
    """إقليم لا يحوي إلا نواته: تُعلَن حالته «بلا محتوى تنفيذي» لا «قائم»."""
    d = tmp_path / "hollow"
    d.mkdir()
    (d / "NUCLEUS.md").write_text(
        "# إقليم فارغ\n\n## الهدف\nهدف.\n\n## الحالة\nstub\n", encoding="utf-8"
    )
    monkeypatch.setitem(writer.SCOPES, "hollow", ("نطاق.", "tests/"))
    out = writer.build_readme(tmp_path, "hollow")
    assert "بلا محتوى تنفيذي" in out


# ── البوابة على المستودع الحقيقي ────────────────────────────────────────────


def test_the_repository_itself_conforms() -> None:
    """المستودع الحقيقي — لا نسخة تجريبية — يمتثل للمادة التاسعة."""
    r = subprocess.run(
        [sys.executable, str(TOOLS / "check_repository_identity.py"),
         str(REPO_ROOT), "--quiet"],
        capture_output=True, text=True, timeout=180, check=False,
    )
    assert r.returncode == 0, f"المستودع مخالف:\n{r.stdout}\n{r.stderr}"


@pytest.mark.parametrize("tool", ["write_domain_readmes", "stamp_readme_identity",
                                  "generate_identity_cards"])
def test_generators_are_settled_on_the_repository(tool: str) -> None:
    """`--check` يجب أن يمرّ: لا بطاقة ناقصة ولا حقل مشتقّ غير مختوم."""
    r = subprocess.run(
        [sys.executable, str(TOOLS / f"{tool}.py"), "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=180, check=False,
    )
    assert r.returncode == 0, f"{tool} --check فشل:\n{r.stdout}\n{r.stderr}"
