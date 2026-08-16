#!/usr/bin/env python3
"""الهدف: توليد مصفوفة حقيقة نطاق التاج من الدليل التنفيذي لا من الادّعاء.

هذه الأداة **لا تصدّق** حالة تُكتَب لها. لكل وحدة في `core/crown/` حالةٌ مُعلَنة على
سلّم النضج، والأداة تُسقِط الحالة إلى ما يُثبِته الدليل فعلًا:

* `IMPLEMENTED`  ← الملف موجود وفيه تعليمات تنفيذية.
* `TESTED`       ← تغطية فروع حقيقية ≥ الحدّ، مقيسة بتشغيل `pytest --cov` الآن.
* `INTEGRATED`   ← الوحدة مستوردة فعلًا من وحدة أخرى داخل النطاق أو من واجهة الأوامر.
* `SECURITY_TESTED` ← معرِّفات اختبارات خصومية مُعلَنة **وموجودة** في شجرة الاختبارات.
* `OBSERVED` / `DEPLOYED` / `PROVEN` ← ممنوعة هنا: لا نشر ولا رصد إنتاجيًّا بعد،
  فادّعاؤها كذب معماري تُسقِطه الأداة برمز خروج غير صفري.

فإن ادّعت الجدولة حالةً أعلى من الدليل، لم تُخفَض العتبة ولم يُحذف المدقّق: يسقط
التوليد ويُطبَع الفارق.

الاستخدام:
    python tools/crown/generate_crown_truth_matrix.py            # يكتب الوثيقة
    python tools/crown/generate_crown_truth_matrix.py --check     # يسقط عند الانحراف
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CROWN_DIR = REPO_ROOT / "core" / "crown"
TESTS_DIR = REPO_ROOT / "tests" / "crown"
OUTPUT = REPO_ROOT / "docs" / "audit" / "CROWN_TRUTH_MATRIX.md"

# سلّم النضج المسموح — لا كلمة COMPLETE فيه، لأنها كلمة بلا معيار.
LADDER = (
    "DESIGNED",
    "SPECIFIED",
    "IMPLEMENTED",
    "TESTED",
    "INTEGRATED",
    "SECURITY_TESTED",
    "DEPLOYED",
    "OBSERVED",
    "PROVEN",
)

# حالات لا يجوز ادّعاؤها في هذه المرحلة لانعدام دليلها أصلًا.
FORBIDDEN_NOW = ("DEPLOYED", "OBSERVED", "PROVEN")

BRANCH_COVERAGE_FLOOR = 90.0


class MatrixDriftError(RuntimeError):
    """الوثيقة لا تطابق الدليل التنفيذي."""


@dataclass(frozen=True)
class UnitClaim:
    """ادّعاء حالة لوحدة واحدة — يُمتحَن ولا يُقبَل كما هو."""

    module: str
    arabic: str
    claimed: str
    security_tests: tuple[str, ...] = ()
    note: str = ""


@dataclass
class UnitEvidence:
    """الدليل المقيس فعلًا لوحدة واحدة."""

    claim: UnitClaim
    statements: int = 0
    branch_coverage: float = 0.0
    importers: tuple[str, ...] = ()
    missing_security_tests: tuple[str, ...] = ()
    earned: str = "DESIGNED"
    demotions: list[str] = field(default_factory=list)


# الادّعاءات المُعلَنة. تعديلها لا يرفع الحالة؛ الدليل هو الذي يرفعها.
CLAIMS: tuple[UnitClaim, ...] = (
    UnitClaim(
        "trust_anchor.py",
        "مرساة الثقة — المفتاح العام مرجعًا لا سرًّا",
        "SECURITY_TESTED",
        (
            "tests/crown/test_crown_trust.py::test_public_key_substitution_rejected",
            "tests/crown/test_crown_trust.py::test_anchor_not_controlled_by_repository",
        ),
        "المرساة لا يملكها المستودع؛ الاستبدال يُرفَض والتراجع يُرفَض بالترقية.",
    ),
    UnitClaim(
        "key_registry.py",
        "سجل مفاتيح التاج — نسب وحالة ولا تاجان",
        "SECURITY_TESTED",
        (
            "tests/crown/test_crown_trust.py::test_retired_key_cannot_sign_new",
            "tests/crown/test_crown_grand_tests.py::test_forged_succession_rejected",
        ),
        "تنشيط مفتاح ثانٍ مع وجود نشط يُرفَض بـ KeyStateError.",
    ),
    UnitClaim(
        "command.py",
        "الأمر الملكي — توقيع Ed25519 ومنع إعادة اللعب",
        "SECURITY_TESTED",
        (
            "tests/crown/test_crown_command.py::test_forged_command_rejected",
            "tests/crown/test_crown_command.py::test_replay_rejected",
            "tests/crown/test_crown_command.py::test_signature_transplant_rejected",
        ),
    ),
    UnitClaim(
        "keystore.py",
        "حِفظ المفاتيح — الخاص خارج البرمجية",
        "SECURITY_TESTED",
        ("tests/crown/test_crown_grand_tests.py::test_compromised_store_cannot_forge",),
        "لا مادة مفتاح خاص في المستودع؛ الحفظ خارجي بإثبات جهاز.",
    ),
    UnitClaim(
        "identity.py",
        "هوية التاج — الحيوية دليل حضور لا مادة مفتاح",
        "SECURITY_TESTED",
        ("tests/crown/test_crown_trust.py::test_unattested_device_flagged",),
    ),
    UnitClaim(
        "succession.py",
        "الخلافة — لا خليفة يقرره نظام",
        "SECURITY_TESTED",
        (
            "tests/crown/test_crown_grand_tests.py::test_forged_succession_rejected",
            "tests/crown/test_crown_grand_tests.py::test_collective_takeover_detected",
        ),
    ),
    UnitClaim(
        "recovery.py",
        "الاسترداد — لا كلمة طوارئ ولا باب خلفي",
        "SECURITY_TESTED",
        ("tests/crown/test_crown_grand_tests.py::test_no_emergency_key_path",),
    ),
    UnitClaim(
        "continuity.py",
        "الاستمرارية — الاستمرار بلا تاج زائف",
        "SECURITY_TESTED",
        (
            "tests/crown/test_crown_continuity.py::test_compromise_response_flow",
            "tests/crown/test_crown_continuity.py::test_isolation_is_not_absence",
        ),
    ),
    UnitClaim(
        "guard.py",
        "الحارس السيادي — يحمي ولا يصير التاج",
        "SECURITY_TESTED",
        (
            "tests/crown/test_crown_guard.py::test_agent_escalation_detected",
            "tests/crown/test_crown_guard.py::test_disable_attempt_is_evidence",
            "tests/crown/test_crown_guard.py::test_malicious_update_blocked",
        ),
    ),
    UnitClaim(
        "audit.py",
        "سجل التاج — سلسلة تجزئة تكشف التحريف",
        "SECURITY_TESTED",
        ("tests/crown/test_crown_threat_model.py::test_audit_chain_detects_tampering",),
    ),
    UnitClaim(
        "threats.py",
        "نموذج التهديد — 38 تهديدًا بحدّ بشري مُعلَن",
        "SECURITY_TESTED",
        ("tests/crown/test_crown_threat_model.py::test_media_is_not_authority",),
        "ادّعاء الحماية بلا مرجع اختبار يُرفَض في وقت البناء.",
    ),
    UnitClaim(
        "sovereign_session.py",
        "المسار السيادي المنفَّذ — بوابات متسلسلة بلا سلطة",
        "SECURITY_TESTED",
        (
            "tests/crown/test_sovereign_continuity_e2e.py::test_command_before_anchor_verification_is_refused",
            "tests/crown/test_sovereign_continuity_e2e.py::test_hidden_veto_path_is_treated_as_false_crown",
            "tests/crown/test_sovereign_continuity_e2e.py::test_second_active_key_is_a_false_crown",
        ),
        "تقودها أداة إثبات تنفيذية (tools/crown/prove_sovereign_continuity.py) في CI.",
    ),
    UnitClaim(
        "cli.py",
        "واجهة الأوامر — بوابة الحدود المطلقة (9 فحوص)",
        "INTEGRATED",
        (),
        "مُدمَجة في CI ضمن وظيفة crown-root-of-trust؛ ليست هدفًا خصوميًّا بذاتها.",
    ),
)


# حارس التوالد: الأداة تُشغِّل pytest، وشجرة الاختبارات تحوي اختبارات تستورد الأداة.
# بلا هذا الحارس يستدعي كلٌّ منهما الآخر بلا نهاية. المتغيّر يُورَّث إلى العملية
# الفرعية، فأي محاولة قياس داخلها تسقط صراحةً بدل أن تتوالد صامتة.
RECURSION_ENV = "CROWN_TRUTH_MATRIX_MEASURING"


def measure_coverage() -> dict[str, dict]:
    """شغّل اختبارات التاج بتغطية فروع الآن، وأعد أرقامًا مقيسة لا محفوظة."""
    if os.environ.get(RECURSION_ENV) == "1":
        raise MatrixDriftError(
            "قياس التغطية استُدعي من داخل تشغيل قياس — توالد ممنوع. "
            "الاختبارات يجب أن تُبدِل القياس ببيانات ثابتة."
        )
    cov_json = REPO_ROOT / ".crown_truth_cov.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/crown/",
            "-q",
            "--cov=core.crown",
            "--cov-branch",
            f"--cov-report=json:{cov_json}",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, RECURSION_ENV: "1"},
        timeout=600,
    )
    if result.returncode != 0:
        raise MatrixDriftError(
            "اختبارات التاج ساقطة — لا تُولَّد مصفوفة حقيقة على اختبارات ساقطة:\n"
            + result.stdout[-2000:]
        )
    data = json.loads(cov_json.read_text(encoding="utf-8"))
    cov_json.unlink(missing_ok=True)
    return data["files"]


def collect_test_node_ids() -> set[str]:
    """اجمع معرِّفات دوال الاختبار الحقيقية من الشجرة النحوية لا من الأسماء المتوقَّعة."""
    node_ids: set[str] = set()
    for path in sorted(TESTS_DIR.glob("test_*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                node_ids.add(f"{rel}::{node.name}")
    return node_ids


def collect_importers() -> dict[str, tuple[str, ...]]:
    """من يستورد من؟ الدمج يُقاس باستيراد فعلي لا بجدول."""
    importers: dict[str, set[str]] = {p.name: set() for p in CROWN_DIR.glob("*.py")}
    for path in sorted(CROWN_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            module = ""
            if isinstance(node, ast.ImportFrom) and node.module:
                module = node.module
            elif isinstance(node, ast.Import):
                module = node.names[0].name
            if module.startswith("core.crown."):
                target = module.split(".")[-1] + ".py"
                if target in importers and target != path.name:
                    importers[target].add(path.name)
    return {k: tuple(sorted(v)) for k, v in importers.items()}


def evaluate() -> list[UnitEvidence]:
    """امتحن كل ادّعاء بالدليل، وأسقِطه إلى ما يستحقه."""
    files = measure_coverage()
    node_ids = collect_test_node_ids()
    importers = collect_importers()
    results: list[UnitEvidence] = []

    for claim in CLAIMS:
        if claim.claimed not in LADDER:
            raise MatrixDriftError(f"{claim.module}: حالة «{claim.claimed}» خارج سلّم النضج.")
        if claim.claimed in FORBIDDEN_NOW:
            raise MatrixDriftError(
                f"{claim.module}: حالة «{claim.claimed}» ممنوعة — لا نشر ولا رصد إنتاجي بعد."
            )

        ev = UnitEvidence(claim=claim)
        key = f"core/crown/{claim.module}"
        if key not in files:
            raise MatrixDriftError(f"{claim.module}: لا قياس تغطية — الملف غائب عن التنفيذ.")
        summary = files[key]["summary"]
        ev.statements = summary["num_statements"]
        ev.branch_coverage = summary["percent_covered"]
        ev.importers = importers.get(claim.module, ())
        ev.missing_security_tests = tuple(
            t for t in claim.security_tests if t not in node_ids
        )

        earned = "DESIGNED"
        if ev.statements > 0:
            earned = "IMPLEMENTED"
        if earned == "IMPLEMENTED" and ev.branch_coverage >= BRANCH_COVERAGE_FLOOR:
            earned = "TESTED"
        else:
            if ev.statements > 0 and ev.branch_coverage < BRANCH_COVERAGE_FLOOR:
                ev.demotions.append(
                    f"تغطية {ev.branch_coverage:.1f}% دون الحدّ {BRANCH_COVERAGE_FLOOR:.0f}%"
                )
        if earned == "TESTED" and (ev.importers or claim.module == "cli.py"):
            earned = "INTEGRATED"
        elif earned == "TESTED":
            ev.demotions.append("لا وحدة تستوردها — غير مدمجة")
        if earned == "INTEGRATED" and claim.security_tests and not ev.missing_security_tests:
            earned = "SECURITY_TESTED"
        elif earned == "INTEGRATED" and claim.security_tests:
            ev.demotions.append(
                "معرِّفات اختبار خصومي غائبة: " + ", ".join(ev.missing_security_tests)
            )

        ev.earned = earned
        results.append(ev)
    return results


def render(results: list[UnitEvidence]) -> str:
    """اكتب الوثيقة بأرقام مقيسة، وبفقرة صريحة لما لم يُثبَت بعد."""
    total_statements = sum(r.statements for r in results)
    security_tested = sum(1 for r in results if r.earned == "SECURITY_TESTED")
    lowest = min(results, key=lambda r: r.branch_coverage)

    lines: list[str] = []
    a = lines.append
    a("# مصفوفة حقيقة نطاق التاج — E2.2")
    a("")
    a("الهدف: بيان ما هو **مُثبَت** في نطاق التاج وما هو مُدَّعى، بحالات على سلّم نضج")
    a("لا تحتوي كلمة `COMPLETE`. هذه الوثيقة **مولَّدة** بـ")
    a("[`tools/crown/generate_crown_truth_matrix.py`](../../tools/crown/generate_crown_truth_matrix.py)")
    a("وتُقاس فيها التغطية بتشغيل الاختبارات لحظة التوليد، فلا تستطيع أن تكذب على القارئ")
    a("إلا بكذب المُنفَّذ نفسه. تحريرها يدويًّا يُسقِط بوابة `--check` في CI.")
    a("")
    a("## سلّم النضج")
    a("")
    a("| الحالة | معنى الدليل المطلوب |")
    a("|---|---|")
    a("| `DESIGNED` | فكرة موصوفة بلا تنفيذ |")
    a("| `SPECIFIED` | واجهة وسلوك محدَّدان كتابةً |")
    a("| `IMPLEMENTED` | تعليمات تنفيذية موجودة فعلًا |")
    a(f"| `TESTED` | تغطية فروع مقيسة ≥ {BRANCH_COVERAGE_FLOOR:.0f}% |")
    a("| `INTEGRATED` | وحدة أخرى تستوردها فعلًا |")
    a("| `SECURITY_TESTED` | اختبارات خصومية مُسمّاة وموجودة تُهاجم الضمان |")
    a("| `DEPLOYED` | منشور في بيئة حقيقية — **غير مُدَّعى** |")
    a("| `OBSERVED` | مرصود تحت حِمل حقيقي — **غير مُدَّعى** |")
    a("| `PROVEN` | مُثبَت بعد النشر والرصد — **غير مُدَّعى** |")
    a("")
    a("> الأداة **ترفض** توليد الوثيقة إذا ادّعى أحد الحالات الثلاث الأخيرة.")
    a("")
    a("## مصفوفة الوحدات")
    a("")
    a("| الوحدة | الدور | الحالة المُثبَتة | تعليمات | تغطية فروع | يستوردها | اختبارات خصومية |")
    a("|---|---|---|---:|---:|---|---:|")
    for r in results:
        importers = "، ".join(x.removesuffix(".py") for x in r.importers) or "—"
        sec = len(r.claim.security_tests) if not r.missing_security_tests else 0
        a(
            f"| `{r.claim.module}` | {r.claim.arabic} | `{r.earned}` | {r.statements} | "
            f"{r.branch_coverage:.1f}% | {importers} | {sec} |"
        )
    a("")
    a("| المقياس | القيمة |")
    a("|---|---:|")
    a(f"| وحدات النطاق | {len(results)} |")
    a(f"| منها `SECURITY_TESTED` | {security_tested} |")
    a(f"| إجمالي التعليمات التنفيذية | {total_statements} |")
    a(f"| أدنى تغطية وحدة | {lowest.claim.module} — {lowest.branch_coverage:.1f}% |")
    a("")
    demoted = [r for r in results if r.demotions]
    a("## إسقاطات الحالة (ادّعاء لم يصمد للدليل)")
    a("")
    if demoted:
        for r in demoted:
            a(f"- `{r.claim.module}`: " + " · ".join(r.demotions))
    else:
        a("لا إسقاط: كل حالة مُعلَنة صمدت لدليلها في هذا التوليد.")
    a("")
    a("## ما ليس مُثبَتًا في هذه المرحلة")
    a("")
    a("- **لا نشر ولا رصد.** لا وحدة في النطاق تحمل `DEPLOYED` أو `OBSERVED` أو `PROVEN`،")
    a("  فلم يعمل شيء منها في بيئة حقيقية تحت حِمل حقيقي.")
    a("- **الحدّ البشري ليس ثغرة تُسَد بالبرمجية.** 22 من 38 تهديدًا تحتاج فعلًا بشريًّا،")
    a("  و5 خارج نطاق البرمجية أصلًا — انظر")
    a("  [`CROWN_THREAT_MODEL.md`](../security/CROWN_THREAT_MODEL.md).")
    a("- **ثقة العتاد (`GUARD_0_PHYSICAL`) غير منفَّذة**، ومُعلَنة كذلك في تقرير الحارس.")
    a("- **التغطية ليست صحةً.** التغطية تقيس ما نُفِّذ من الشيفرة في الاختبار، لا صواب")
    a("  المعمار؛ الاختبارات الخصومية هي ما يُقرِّب من ذلك.")
    a("")
    a("## إعادة التوليد والتحقق")
    a("")
    a("```bash")
    a("python tools/crown/generate_crown_truth_matrix.py          # يكتب هذه الوثيقة")
    a("python tools/crown/generate_crown_truth_matrix.py --check  # يسقط عند الانحراف")
    a("```")
    a("")
    return "\n".join(lines) + "\n"


def main() -> int:
    check_only = "--check" in sys.argv
    results = evaluate()
    rendered = render(results)
    if check_only:
        if not OUTPUT.exists():
            print(f"✗ الوثيقة غائبة: {OUTPUT}")
            return 1
        current = OUTPUT.read_text(encoding="utf-8")
        if current != rendered:
            print("✗ مصفوفة حقيقة التاج لا تطابق الدليل التنفيذي. أعِد التوليد.")
            return 1
        print("✓ مصفوفة حقيقة التاج مطابقة للدليل.")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"✓ كُتبت: {OUTPUT.relative_to(REPO_ROOT)}")
    for r in results:
        print(f"  {r.claim.module}: {r.earned} (تغطية {r.branch_coverage:.1f}%)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MatrixDriftError as exc:
        print(f"✗ {exc}")
        sys.exit(1)
