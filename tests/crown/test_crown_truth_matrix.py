"""الهدف: حراسة صدق مولِّد مصفوفة حقيقة التاج نفسه.

المصفوفة تحكم على بقية النطاق، فلا بدّ أن تُحاكَم هي أيضًا: أن يخلو سلّمها من كلمة
`COMPLETE` بلا معيار، وأن ترفض ادّعاء النشر والرصد والإثبات، وأن تُسقِط الحالة إلى
دليلها لا أن تقبل الجدولة كما كُتِبت.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_PATH = REPO_ROOT / "tools" / "crown" / "generate_crown_truth_matrix.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("crown_truth_matrix_tool", TOOL_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # سجّل الوحدة قبل تنفيذها: `dataclass` يقرأ وحدة الصنف من `sys.modules`.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


tool = _load_tool()


def _fake_coverage_files() -> dict[str, dict]:
    """تغطية ثابتة للاختبار: لا تُشغَّل الحزمة داخل الحزمة.

    قياس التغطية الحقيقي يُشغِّل `pytest` في عملية فرعية، وهذا الملف جزء من الشجرة
    التي تُشغَّل — فالقياس داخل الاختبار توالدٌ لا فحص. لذلك يُبدَّل القياس هنا،
    ويبقى القياس الحقيقي في تشغيل الأداة وفي بوابة CI.
    """
    high = {
        "summary": {"num_statements": 120, "percent_covered": 96.0},
    }
    return {f"core/crown/{p.name}": dict(high) for p in tool.CROWN_DIR.glob("*.py")}


@pytest.fixture(autouse=True)
def _no_nested_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    """امنع أي اختبار في هذا الملف من تشغيل قياس تغطية متوالد."""
    monkeypatch.setattr(tool, "measure_coverage", _fake_coverage_files)


# مرجع الدالة الأصلية قبل أي إبدال، ليُختبَر حارس التوالد نفسه.
REAL_MEASURE_COVERAGE = tool.measure_coverage


def test_recursion_guard_blocks_nested_measurement(monkeypatch: pytest.MonkeyPatch) -> None:
    """القياس داخل قياس يسقط صراحةً بدل أن يتوالد صامتًا."""
    monkeypatch.setenv(tool.RECURSION_ENV, "1")
    with pytest.raises(tool.MatrixDriftError, match="توالد ممنوع"):
        REAL_MEASURE_COVERAGE()


def test_ladder_has_no_unmeasurable_completion_word() -> None:
    """«COMPLETE» ليست حالة: لا معيار لها فلا تُقاس."""
    assert "COMPLETE" not in tool.LADDER
    assert "DONE" not in tool.LADDER


def test_ladder_is_ordered_and_ends_at_proven() -> None:
    assert tool.LADDER[0] == "DESIGNED"
    assert tool.LADDER[-1] == "PROVEN"
    assert tool.LADDER.index("TESTED") < tool.LADDER.index("SECURITY_TESTED")


def test_deployment_grade_states_are_forbidden_now() -> None:
    """لا نشر ولا رصد إنتاجيًّا، فادّعاؤهما ممنوع لا مُتحفَّظ عليه."""
    assert set(tool.FORBIDDEN_NOW) == {"DEPLOYED", "OBSERVED", "PROVEN"}


def test_no_declared_claim_reaches_deployment_grade() -> None:
    for claim in tool.CLAIMS:
        assert claim.claimed not in tool.FORBIDDEN_NOW, claim.module
        assert claim.claimed in tool.LADDER, claim.module


def test_claiming_proven_is_rejected_not_downgraded_silently(monkeypatch) -> None:
    """ادّعاء `PROVEN` يُسقِط التوليد، ولا يُصحَّح في صمت."""
    forged = tool.UnitClaim("guard.py", "ادّعاء إثبات بلا نشر", "PROVEN")
    monkeypatch.setattr(tool, "CLAIMS", (forged,))
    with pytest.raises(tool.MatrixDriftError, match="ممنوعة"):
        tool.evaluate()


def test_claiming_state_outside_ladder_is_rejected(monkeypatch) -> None:
    forged = tool.UnitClaim("guard.py", "حالة مختلقة", "COMPLETE")
    monkeypatch.setattr(tool, "CLAIMS", (forged,))
    with pytest.raises(tool.MatrixDriftError, match="خارج سلّم النضج"):
        tool.evaluate()


def test_missing_module_is_rejected(monkeypatch) -> None:
    """وحدة لا وجود لها في التنفيذ لا تحصل على حالة."""
    forged = tool.UnitClaim("nonexistent_unit.py", "وحدة وهمية", "IMPLEMENTED")
    monkeypatch.setattr(tool, "CLAIMS", (forged,))
    with pytest.raises(tool.MatrixDriftError, match="لا قياس تغطية"):
        tool.evaluate()


def test_declared_security_test_ids_exist_in_the_tree() -> None:
    """كل معرِّف اختبار خصومي مُعلَن يجب أن يكون موجودًا فعلًا."""
    node_ids = tool.collect_test_node_ids()
    missing = [
        ref
        for claim in tool.CLAIMS
        for ref in claim.security_tests
        if ref not in node_ids
    ]
    assert missing == [], f"معرِّفات غائبة: {missing}"


def test_nonexistent_security_test_id_demotes_the_unit(monkeypatch) -> None:
    """ادّعاء اختبار خصومي غير موجود يُسقِط الوحدة عن SECURITY_TESTED."""
    forged = tool.UnitClaim(
        "guard.py",
        "حارس يدّعي اختبارًا خصوميًّا وهميًّا",
        "SECURITY_TESTED",
        ("tests/crown/test_crown_guard.py::test_this_test_does_not_exist",),
    )
    monkeypatch.setattr(tool, "CLAIMS", (forged,))
    results = tool.evaluate()
    assert results[0].earned == "INTEGRATED"
    assert results[0].missing_security_tests
    assert any("غائبة" in d for d in results[0].demotions)


def test_coverage_floor_is_not_below_ci_gate() -> None:
    """حدّ التغطية في المصفوفة لا يجوز أن يكون أضعف من بوابة CI."""
    assert tool.BRANCH_COVERAGE_FLOOR >= 90.0


def test_integration_is_measured_by_real_imports() -> None:
    """الدمج يُقاس باستيراد فعلي: `threats.py` مستوردة من غيرها فعلًا."""
    importers = tool.collect_importers()
    assert importers["threats.py"], "threats.py يجب أن تكون مستوردة من وحدة أخرى"
    assert "guard.py" not in importers["guard.py"]
