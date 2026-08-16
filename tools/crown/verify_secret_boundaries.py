"""الهدف: بوابة حدود الأسرار والثقة — تُثبِت تنفيذيًّا أن لا مفتاح خاص في الشجرة
ولا في التاريخ، ولا سرّ إنتاج مكتوب في الكود، ولا سلطة تعلو الملك، ولا تجاوز خفي.

كل فحص هنا يحاول أن **ينقض** حدًّا مُعلَنًا. والحدّ الذي لا يُنقَض في محاولة
جادّة هو وحده حدٌّ مُثبَت؛ وما عداه ادّعاء. ويسقط التشغيل عند أول مخالفة حقيقية
برمز خروج غير صفري — لأن سرًّا مكشوفًا لا يُؤجَّل.

النطاق: المستودع كله فيما يخصّ الأسرار، ونطاق التاج فيما يخصّ السيادة.
المالك: التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

SERVICES_SRC = REPO_ROOT / "federal" / "executive" / "services" / "src"

# النمط مُركَّب من أجزاء كي لا يحمل هذا الملف نفسه مادة مفتاح ولا يُسقِط بوابته.
_DASHES = "-" * 5
PEM_PRIVATE = re.compile(_DASHES + r"BEGIN [A-Z ]*PRIVATE KEY" + _DASHES)
_SEED_WORD = "seed"
PRIVATE_SEED = re.compile(
    r"(?:private|secret)_?(?:" + _SEED_WORD + r"|scalar)\s*=\s*[\"'][0-9a-fA-F]{32,}[\"']"
)

# امتدادات لا يُقبل وجودها أصلًا: مادة مفتاح أو مخزن مفاتيح.
KEY_FILE_SUFFIXES = (".pem", ".key", ".pfx", ".p12", ".jks", ".asc", ".ppk")

SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache", ".ruff_cache"}

# ملفات تُذكر فيها هذه الأنماط بوصفها **أنماط فحص** لا مادة سرّ.
SCANNER_FILES = {
    "tools/crown/verify_secret_boundaries.py",
    "tools/crown/verify_crown_root_of_trust.py",
    "tools/governance/truth_audit.py",
    ".github/workflows/ci.yml",
}

failures: list[str] = []
passed: list[str] = []


def check(name: str, ok: bool, detail: str = "", *, evidence: str = "") -> None:
    """سجّل نتيجة بوابة؛ ويُطبَع التعليل عند النجاح أيضًا.

    بوابة تقول «نجحت» بلا بيان لِما فحصته لا تُثبِت أنها فحصت شيئًا.
    """
    if ok:
        passed.append(name)
        print(f"✓ {name}" + (f" — {evidence}" if evidence else ""))
    else:
        failures.append(f"{name} — {detail}")
        print(f"✗ {name} — {detail}")


UNREADABLE: list[str] = []


def iter_text_files():
    """كل ملف في الشجرة مقروءًا نصًّا، عدا مجلدات العمل.

    تُقرأ البايتات وتُفكّ بتجاهل ما لا يُفكّ، فتُفحَص الملفات الثنائية أيضًا: ماسحُ
    أسرارٍ يتخطّى ما لا يستطيع قراءته يترك للسرّ بابًا. وما تعذّرت قراءته أصلًا
    يُسجَّل ويُعلَن، ولا يُبتلع صمتًا.
    """
    UNREADABLE.clear()
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        try:
            raw = path.read_bytes()
        except OSError as error:
            UNREADABLE.append(f"{rel}: {error}")
            continue
        yield rel, raw.decode("utf-8", errors="ignore")


# ── 1. لا مادة مفتاح خاص في الشجرة ──────────────────────────────────────────


def gate_no_private_key_in_tree() -> None:
    hits = [rel for rel, text in iter_text_files()
            if rel not in SCANNER_FILES and PEM_PRIVATE.search(text)]
    check(
        "لا مادة مفتاح خاص في شجرة العمل",
        not hits,
        f"ملفات تحمل كتلة مفتاح خاص: {hits[:5]}",
        evidence="فُحص كل ملف نصّي بنمط كتلة PEM الخاصة",
    )


def gate_no_key_files() -> None:
    hits = [p.relative_to(REPO_ROOT).as_posix()
            for p in REPO_ROOT.rglob("*")
            if p.is_file()
            and not any(part in SKIP_DIRS for part in p.parts)
            and p.suffix.lower() in KEY_FILE_SUFFIXES]
    check(
        "لا ملف مخزن مفاتيح في المستودع",
        not hits,
        f"ملفات بامتداد مفاتيح: {hits[:5]}",
        evidence=f"الامتدادات المرفوضة: {', '.join(KEY_FILE_SUFFIXES)}",
    )


def gate_no_private_seed_literal() -> None:
    hits = [rel for rel, text in iter_text_files()
            if rel not in SCANNER_FILES and PRIVATE_SEED.search(text)]
    check(
        "لا بذرة مفتاح خاص مكتوبة نصًّا",
        not hits,
        f"ملفات تحمل بذرة سرّية: {hits[:5]}",
        evidence="يُرفض إسناد بذرة/عدد سرّي بقيمة ست عشرية طويلة",
    )


# ── 2. لا مادة مفتاح في التاريخ المنشور ─────────────────────────────────────


def gate_no_private_key_in_history() -> None:
    """التاريخ ذاكرة لا تُمحى: سرٌّ التُزم مرة يبقى مكشوفًا وإن حُذف لاحقًا."""
    result = subprocess.run(
        ["git", "log", "--all", "-p", "--no-color"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        check("لا مادة مفتاح خاص في التاريخ", False,
              f"تعذّرت قراءة التاريخ: {result.stderr.strip()[:120]}")
        return
    added = [line for line in result.stdout.splitlines()
             if line.startswith("+") and PEM_PRIVATE.search(line)]
    check(
        "لا مادة مفتاح خاص في التاريخ المنشور",
        not added,
        f"{len(added)} سطرًا مُضافًا يحمل كتلة مفتاح خاص",
        evidence=f"فُحصت كل الأسطر المُضافة في {_commit_count()} التزامًا",
    )


def _commit_count() -> str:
    result = subprocess.run(
        ["git", "rev-list", "--all", "--count"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    return result.stdout.strip() or "?"


# ── 3. لا سرّ إنتاج مكتوب في الكود ──────────────────────────────────────────


def gate_secret_fields_have_no_defaults() -> None:
    """الحقول السرّية في إعدادات الخدمات لا تحمل قيمة افتراضية.

    القيمة الافتراضية المكتوبة في مستودع منشور سرٌّ منشور.
    """
    sys.path.insert(0, str(SERVICES_SRC))
    try:
        from amos_federation.common.config import (  # noqa: PLC0415
            SECRET_FIELDS,
            Settings,
        )
    except ImportError as exc:
        check("حقول الأسرار بلا قيم افتراضية", False, f"تعذّر استيراد الإعدادات: {exc}")
        return
    offenders = [f for f in SECRET_FIELDS if Settings.model_fields[f].default != ""]
    check(
        "حقول الأسرار في الإعدادات بلا قيمة افتراضية",
        not offenders,
        f"حقول تحمل افتراضيًّا: {offenders}",
        evidence=f"فُحص {len(SECRET_FIELDS)} حقلًا سرّيًّا",
    )


def gate_production_refuses_missing_secrets() -> None:
    """الإنتاج يسقط صراحةً بسرّ ناقص — لا يعمل بأمان موهوم."""
    sys.path.insert(0, str(SERVICES_SRC))
    try:
        from amos_federation.common.config import (  # noqa: PLC0415
            InsecureConfigurationError,
            Settings,
        )
    except ImportError as exc:
        check("الإنتاج يرفض الإقلاع بسرّ ناقص", False, f"تعذّر الاستيراد: {exc}")
        return
    config = Settings(environment="production", jwt_secret="",
                      king_login_secret="", _env_file=None)
    try:
        config.assert_secrets_configured()
    except InsecureConfigurationError as refusal:
        check("الإنتاج يرفض الإقلاع بسرّ ناقص", True,
              evidence=f"رفض فعلي: {refusal}")
        return
    check("الإنتاج يرفض الإقلاع بسرّ ناقص", False,
          "قُبل إعداد إنتاج بسرّ فارغ")


def gate_no_king_secret_literal() -> None:
    """سرّ دخول الملك لا يُكتب في الكود: من قرأه صار ملكًا."""
    login = SERVICES_SRC / "amos_federation" / "services" / "royal" / "main.py"
    if not login.exists():
        check("سرّ دخول الملك خارج الكود", False, f"الملف غير موجود: {login}")
        return
    text = login.read_text(encoding="utf-8")
    literal = "amos" + "-king-" + "2026"
    reads_env = "king_login_secret" in text
    constant_time = "compare_digest" in text
    check(
        "سرّ دخول الملك خارج الكود ويُقارَن بزمن ثابت",
        literal not in text and reads_env and constant_time,
        "السرّ ما زال في الكود أو لا يُقرأ من الإعدادات أو تُقارَن السلسلة مباشرة",
        evidence="يُقرأ من الإعدادات ويُقارَن بـ hmac.compare_digest",
    )


# ── 4. حدود الثقة السيادية ──────────────────────────────────────────────────


def gate_public_key_is_not_a_secret() -> None:
    """المفتاح العام يُنشَر ولا يُخفى؛ وحمايته من **التبديل** لا من الاطّلاع.

    والاختبار تنفيذي: يُبنى وصف عام حقيقي ويُفتَّش عن أي مادة سرّية فيه. فوصفٌ
    لا يُنشَر لا يُثبِت أنه قابل للنشر.
    """
    from core.crown.trust_anchor import (  # noqa: PLC0415
        AnchorSource,
        CrownTrustAnchor,
        DOMAIN_TAG_ANCHOR,
        TrustPlane,
    )

    public_hex = "ab" * 32
    # البصمة تُحسب كما تحسبها المرساة — وهي بصمة تُنشر، لا مفتاح يُخفى.
    fingerprint = hashlib.sha256(
        f"{DOMAIN_TAG_ANCHOR}:ROOT-VERIFY:{public_hex}".encode()
    ).hexdigest()
    anchor = CrownTrustAnchor(
        root_id="ROOT-VERIFY",
        root_public_key_hex=public_hex,
        sources=(
            AnchorSource(
                plane=TrustPlane.PRINTED_FINGERPRINT,
                locator="سجل ورقي — تحقق البوابة",
                fingerprint=fingerprint,
            ),
        ),
    )
    descriptor = anchor.public_descriptor()
    blob = repr(descriptor).lower()
    leaked = [word for word in ("private_key", "secret_key", "seed_hex", "privatekey")
              if word in blob]
    publishes_fingerprint = "root_fingerprint" in descriptor
    check(
        "المفتاح العام يُنشَر ولا يحمل الوصفُ العام سرًّا",
        publishes_fingerprint and not leaked,
        f"مادة سرّية في الوصف العام: {leaked}" if leaked
        else "الوصف العام لا يحمل بصمة الجذر",
        evidence=(
            f"وصف عام من {len(descriptor)} حقلًا، فيه بصمة الجذر ومصادره، "
            "وبلا أي مادة سرّية"
        ),
    )


def gate_biometric_is_never_key_material() -> None:
    """السمة الحيوية تعريف لا مفتاح: لا تُصنَع منها مادة توقيع."""
    from core.crown.identity import assert_not_key_material  # noqa: PLC0415

    refusals = []
    for attempt in ("بصمة الإصبع مفتاح خاص", "iris scan as private key",
                    "biometric private key", "بصمة العين تُشتقّ منها مادة مفتاح"):
        try:
            assert_not_key_material(attempt)
        except Exception as refusal:  # noqa: BLE001 — نوع الرفض يُثبَت بالرسالة
            refusals.append(type(refusal).__name__)
        else:
            refusals.append("")
    check(
        "السمة الحيوية لا تُقبل مادةَ مفتاح",
        all(refusals),
        f"مدخلات قُبلت بلا رفض: {refusals}",
        evidence=f"أربع محاولات، وكلها رُفضت: {sorted(set(refusals))}",
    )


def gate_no_authority_above_the_king() -> None:
    """الحارس لا يصير سيدًا: كل سلطة سيادية يطلبها تُرفض."""
    from core.crown.guard import (  # noqa: PLC0415
        FORBIDDEN_GUARD_POWERS,
        GuardAuthorityError,
        assert_not_sovereign_power,
    )

    reasons: list[str] = []
    accepted: list[str] = []
    for power in FORBIDDEN_GUARD_POWERS:
        try:
            assert_not_sovereign_power(power)
        except GuardAuthorityError as refusal:
            reasons.append(str(refusal))
        else:
            accepted.append(power)
    check(
        "لا سلطة تعلو الملك — الحارس يُرفَض عن كل سلطة سيادية",
        not accepted,
        f"سلطات قُبلت بلا رفض: {accepted}",
        evidence=(
            f"{len(reasons)} سلطة سيادية مرفوضة، بلا استثناء واحد · "
            f"مثال التعليل: {reasons[0][:90] if reasons else ''}"
        ),
    )


def gate_gitignore_covers_key_paths() -> None:
    """المخزن السرّي يُستبعَد صراحةً قبل أن يُلتزَم سهوًا."""
    ignore = (REPO_ROOT / ".gitignore")
    text = ignore.read_text(encoding="utf-8") if ignore.exists() else ""
    required = ("*.pem", "*.key", ".env")
    missing = [pattern for pattern in required if pattern not in text]
    check(
        ".gitignore يستبعد مسارات المفاتيح والبيئة",
        not missing,
        f"أنماط ناقصة: {missing}",
        evidence=f"موجودة: {', '.join(required)}",
    )


GATES = (
    gate_no_private_key_in_tree,
    gate_no_key_files,
    gate_no_private_seed_literal,
    gate_no_private_key_in_history,
    gate_secret_fields_have_no_defaults,
    gate_production_refuses_missing_secrets,
    gate_no_king_secret_literal,
    gate_public_key_is_not_a_secret,
    gate_biometric_is_never_key_material,
    gate_no_authority_above_the_king,
    gate_gitignore_covers_key_paths,
)


def main() -> int:
    print("بوابة حدود الأسرار والثقة (E2.2-E)")
    print("=" * 62)
    for gate in GATES:
        gate()
    print("=" * 62)
    if UNREADABLE:
        # ملف تعذّرت قراءته نقطةٌ عمياء، فيُعلَن ولا يُسكت عنه.
        print(f"تنبيه: {len(UNREADABLE)} ملفًا تعذّرت قراءته:")
        for entry in UNREADABLE[:10]:
            print(f"  - {entry}")
    if failures:
        print(f"BLOCKED: {len(failures)} مخالفة من {len(GATES)} بوابة")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"PASS: {len(passed)}/{len(GATES)} بوابة — لا سرّ مكشوف ولا سلطة فوق الملك")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
