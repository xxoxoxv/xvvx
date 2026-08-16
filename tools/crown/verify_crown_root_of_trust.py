"""الهدف: بوابة سلامة جذر ثقة التاج — فحوص تنفيذية لا شكلية، تُشغَّل في CI ومحليًّا،
وترجع رمز خروج غير صفري عند أول مخالفة حقيقية.

كل فحص هنا يحاول أن **ينقض** ضمانًا مُعلَنًا: إن نُقِض سقطت البوابة. ولا يُقاس شيء
هنا بوجود ملف، بل بسلوك يُشغَّل.

المالك: التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

CROWN_DIR = REPO_ROOT / "core" / "crown"
CROWN_TESTS = REPO_ROOT / "tests" / "crown"
SECURITY_DOCS = REPO_ROOT / "docs" / "security"

# ترويسات مادة المفتاح — مُركَّبة بأقواس كي لا يطابق النمط نفسه هذا الملف.
KEY_MATERIAL_PATTERNS = (
    r"BEGIN (OPENSSH |EC |RSA |DSA |PGP |ENCRYPTED |)PRIVATE KEY",
    r"BEGIN (X509 |)CRL",
)

BYPASS_FLAGS = (
    "force",
    "bypass",
    "skip_check",
    "skip_verification",
    "unchecked",
    "override",
    "no_verify",
    "unsafe",
    "trust_me",
)

# ادّعاءات ممنوعة نصًّا — البند 52 يمنع ادّعاء الأمن المطلق أو حماية وهمية.
FORBIDDEN_CLAIMS = (
    "أمن مطلق",
    "أمان مطلق",
    "حماية مطلقة",
    "absolute security",
    "unbreakable",
    "100% secure",
    "لا يمكن اختراقه",
)

failures: list[str] = []
passed: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        passed.append(name)
        print(f"✓ {name}")
    else:
        failures.append(f"{name} — {detail}")
        print(f"✗ {name} — {detail}")


def gate_cli_check() -> None:
    """بوابة الحدود المطلقة في `crown-check` ترجع صفرًا فعلًا."""
    result = subprocess.run(
        [sys.executable, "-m", "core.crown.cli", "crown-check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    check(
        "بوابة 1 — crown-check يخرج بصفر",
        result.returncode == 0,
        f"رمز الخروج {result.returncode}: {result.stdout[-400:]}{result.stderr[-400:]}",
    )


def gate_no_key_material() -> None:
    """لا ترويسة مفتاح خاص في نطاق التاج ولا في اختباراته ولا في وثائقه."""
    offenders: list[str] = []
    for directory in (CROWN_DIR, CROWN_TESTS, SECURITY_DOCS):
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix == ".pyc":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in KEY_MATERIAL_PATTERNS:
                if re.search(pattern, text):
                    offenders.append(str(path.relative_to(REPO_ROOT)))
    check(
        "بوابة 2 — لا مادة مفتاح خاص في نطاق التاج",
        not offenders,
        f"ملفات مخالفة: {offenders}",
    )


def gate_no_bypass_flags() -> None:
    """لا راية تجاوز في توقيع أي دالة من دوال التاج."""
    offenders: list[str] = []
    signature = re.compile(
        r"def [A-Za-z_]+\([^)]*(" + "|".join(BYPASS_FLAGS) + r")", re.DOTALL
    )
    for path in sorted(CROWN_DIR.glob("*.py")):
        for match in signature.finditer(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.name}: {match.group(0)[:80]}")
    check(
        "بوابة 3 — لا راية تجاوز في تواقيع التاج",
        not offenders,
        f"تواقيع مخالفة: {offenders}",
    )


def gate_no_absolute_claims() -> None:
    """لا ادّعاء أمن مطلق في وثائق التاج ولا في شيفرته."""
    offenders: list[str] = []
    for directory in (CROWN_DIR, CROWN_TESTS, SECURITY_DOCS):
        for path in directory.rglob("*"):
            if not path.is_file() or path.suffix == ".pyc":
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for claim in FORBIDDEN_CLAIMS:
                for line in text.splitlines():
                    if claim in line and "لا " not in line and "ولا" not in line:
                        offenders.append(f"{path.relative_to(REPO_ROOT)}: {claim}")
    check(
        "بوابة 4 — لا ادّعاء أمن مطلق",
        not offenders,
        f"ادّعاءات: {offenders[:5]}",
    )


def gate_false_mitigation_claim_is_blocked() -> None:
    """رفع حال تهديد إلى «منفَّذ» بلا مرجع اختبار يجب أن يرفع استثناءً فعلًا.

    هذا فحص أسنان البوابة نفسها: لو صار الادّعاء بلا دليل ممكنًا سقط كل نموذج
    التهديد، فنُجرّب النقض بدل أن نثق بالوصف.
    """
    from core.crown.threats import (
        DetectionCapability,
        FalseMitigationClaimError,
        MitigationStatus,
        ResponsibleParty,
        Threat,
        ThreatDomain,
        ThreatHorizon,
    )

    def build(**overrides: object) -> None:
        base = {
            "threat_id": "THR-CI-PROBE",
            "title": "فحص بوابة",
            "domain": ThreatDomain.CRYPTOGRAPHIC,
            "horizon": ThreatHorizon.PRESENT,
            "detection": DetectionCapability.DETECTABLE_BY_SOFTWARE,
            "mitigation_status": MitigationStatus.IMPLEMENTED_AND_TESTED,
            "responsible": ResponsibleParty.SOFTWARE,
            "description": "تهديد اصطناعي لفحص البوابة.",
        }
        base.update(overrides)
        Threat(**base)  # type: ignore[arg-type]

    unclaimed_passed = False
    try:
        build()  # ادّعاء تنفيذ بلا test_refs
    except FalseMitigationClaimError:
        unclaimed_passed = True
    check(
        "بوابة 5 — ادّعاء حماية بلا مرجع اختبار مرفوض",
        unclaimed_passed,
        "أمكن ادّعاء تنفيذ بلا اختبار — نموذج التهديد بلا أسنان.",
    )

    speculative_blocked = False
    try:
        build(
            horizon=ThreatHorizon.SPECULATIVE,
            test_refs=("tests/crown/test_crown_threat_model.py::test_media_is_not_authority",),
        )
    except FalseMitigationClaimError:
        speculative_blocked = True
    check(
        "بوابة 6 — ادّعاء حماية ضد أفق تخميني مرفوض",
        speculative_blocked,
        "أمكن ادّعاء حماية من تقنية غير متحققة.",
    )


def gate_boundary_is_declared() -> None:
    """حدّ البرمجية معلَن بالأرقام، ومجموع الفئات مطابق للمجموع الكلي."""
    from core.crown.threats import boundary_report

    report = boundary_report()
    total = report["total_threats"]
    by_status = (
        report["implemented_and_tested"]
        + report["partially_implemented"]
        + report["modelled_not_implemented"]
        + report["out_of_software_scope"]
    )
    check(
        "بوابة 7 — تصنيف التهديدات مُستوفى وغير متناقض",
        total == by_status and total > 0,
        f"المجموع {total} وتصنيفه {by_status}",
    )
    check(
        "بوابة 8 — حدّ البرمجية معلَن لا مُخفى",
        report["out_of_software_scope"] > 0 and report["requires_human"] > 0,
        "لا تهديد خارج مقدرة البرمجية — إخفاء للحدّ يوهم بحماية شاملة.",
    )


def gate_guard_cannot_become_sovereign() -> None:
    """كل سلطة سيادية محظورة على الحارس ترفع `GuardAuthorityError` عند محاولتها.

    ولا يُقبَل هنا استثناء عامّ: خطأ استيراد أو اسم دالة مُغيَّر يُسقط البوابة، لأن
    بوابةً تُمرِّر ما لا تفهمه ليست بوابة.
    """
    from core.crown.guard import (
        FORBIDDEN_GUARD_POWERS,
        GuardAuthorityError,
        assert_not_sovereign_power,
    )

    leaked: list[str] = []
    for power in sorted(FORBIDDEN_GUARD_POWERS):
        try:
            assert_not_sovereign_power(power)
        except GuardAuthorityError:
            continue
        leaked.append(power)
    check(
        f"بوابة 9 — الحارس لا يصير سلطةً سيادية ({len(FORBIDDEN_GUARD_POWERS)} سلطة محظورة)",
        not leaked and len(FORBIDDEN_GUARD_POWERS) >= 15,
        f"سلطات مرّت بلا رفض: {leaked}",
    )


def gate_single_active_crown() -> None:
    """لا تاجان: تنشيط مفتاح ثانٍ مع وجود مفتاح نشط يُرفَض فعلًا، لا وصفًا."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    from core.crown.key_registry import (
        CrownKeyRecord,
        CrownKeyRegistry,
        KeyProvenance,
        KeyState,
        KeyStateError,
        LineageKind,
    )

    def public_hex() -> str:
        return (
            Ed25519PrivateKey.generate()
            .public_key()
            .public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            .hex()
        )

    provenance = KeyProvenance(
        ceremony_id="CI-PROBE",
        ceremony_kind="ci_probe",
        keystore_kind="TEST_EPHEMERAL",
        attestation_ref="tools/crown/verify_crown_root_of_trust.py",
        witnesses=("ci-a", "ci-b", "ci-c"),
        out_of_band_verified=True,
    )
    registry = CrownKeyRegistry()
    registry.register(
        CrownKeyRecord(
            key_id="CI-K1",
            version=1,
            algorithm="Ed25519",
            public_key_hex=public_hex(),
            state=KeyState.PENDING,
            lineage_kind=LineageKind.GENESIS,
            predecessor_key_id=None,
            registered_at="2026-08-16T00:00:00+00:00",
            provenance=provenance,
        )
    )
    registry.register(
        CrownKeyRecord(
            key_id="CI-K2",
            version=2,
            algorithm="Ed25519",
            public_key_hex=public_hex(),
            state=KeyState.PENDING,
            lineage_kind=LineageKind.ROTATION,
            predecessor_key_id="CI-K1",
            registered_at="2026-08-16T00:00:01+00:00",
            provenance=provenance,
        )
    )
    registry.activate("CI-K1", at="2026-08-16T00:00:02+00:00")
    doubled = False
    try:
        registry.activate("CI-K2", at="2026-08-16T00:00:03+00:00")
        doubled = True
    except KeyStateError:
        doubled = False
    check(
        "بوابة 10 — لا تاجان: تنشيط مفتاح ثانٍ مرفوض",
        not doubled,
        "أمكن وجود مفتاحَي تاج نشطين معًا — تاجان.",
    )


def gate_threat_doc_matches_code() -> None:
    """وثيقة نموذج التهديد مطابقة لمكتبة التهديدات — لا توثيق يسبق التنفيذ."""
    result = subprocess.run(
        [sys.executable, "tools/governance/generate_crown_threat_doc.py", "--check"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    check(
        "بوابة 11 — وثيقة التهديد مطابقة للتنفيذ",
        result.returncode == 0,
        result.stdout.strip() + result.stderr.strip(),
    )


def main() -> int:
    print("═══ بوابة جذر ثقة التاج ═══")
    gate_cli_check()
    gate_no_key_material()
    gate_no_bypass_flags()
    gate_no_absolute_claims()
    gate_false_mitigation_claim_is_blocked()
    gate_boundary_is_declared()
    gate_guard_cannot_become_sovereign()
    gate_single_active_crown()
    gate_threat_doc_matches_code()
    print("───────────────────────────")
    print(f"ناجح: {len(passed)} · مخالف: {len(failures)}")
    if failures:
        for item in failures:
            print(f"::error::{item}")
        return 1
    print("✓ جذر ثقة التاج سليم.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
