# =============================================================================
# File:        tests/smoke/run_smoke_tests.py
# Purpose:     مشغّل اختبارات الدخان لكل النطاقات الـ12 — يفحص كل stub ويطبع جدولًا
# Owner:       tests/
# Created:     2026-08-15
# Phase:       P3 (Working Nuclei)
# Article 009: هذا الملف يلتزم بالمادة 009 — الشفافية والمراجعة المستمرة.
#              يفحص جميع النطاقات ويتأكد من أن البيانات الحقيقية متاحة.
# =============================================================================
"""
مشغّل اختبارات الدخان (Smoke Test Runner) — Phase P3.

يقوم باستيراد كل domain stub، استدعاء دالة check() الخاصة به،
والإبلاغ عن نجاح/فشل كل نطاق. يخرج برمز 0 إذا نجح الجميع، أو 1 إذا فشل أي نطاق.
"""

import importlib
import sys
import os

# Ensure the project root is on sys.path so domain stub packages resolve
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# --- Registry of all 12 domain stubs ---
# Each tuple: (domain label, module path, function name)
DOMAIN_STUBS = [
    ("tools", "tools.stubs.registry_check", "check"),
    ("agents", "agents.stubs.registry_check", "check"),
    ("institutions", "institutions.stubs.registry_check", "check"),
    ("royal", "royal.stubs.guard_check", "check"),
    ("ops", "ops.stubs.audit_check", "check"),
    ("federal", "federal.stubs.treasury_check", "check"),
    ("core", "core.stubs.memory_check", "check"),
    ("runtime", "runtime.stubs.task_event_check", "check"),
    ("interfaces", "interfaces.stubs.registry_check", "check"),
    ("states", "states.stubs.policy_check", "check"),
    ("docs", "docs.stubs.docs_check", "check"),
]


def run_all():
    """Run smoke checks for all 12 domains.

    Returns:
        tuple: (results list, overall pass boolean)
    """
    results = []
    all_pass = True

    for domain, module_path, func_name in DOMAIN_STUBS:
        try:
            mod = importlib.import_module(module_path)
            check_fn = getattr(mod, func_name)
            result = check_fn()
            status = result.get("status", "fail")
            if status != "pass":
                all_pass = False
            results.append((domain, status, result))
        except Exception as exc:  # noqa: BLE001
            all_pass = False
            results.append((domain, "error", {"error": str(exc)}))

    return results, all_pass


def print_summary_table(results):
    """Print a formatted summary table of all domain checks."""
    header = f"{'Domain':<16} {'Status':<8} {'Detail'}"
    sep = "-" * len(header)
    print()
    print("=" * 64)
    print("  AMOS-Federation P3 Smoke Tests — Summary")
    print("=" * 64)
    print(header)
    print(sep)

    for domain, status, result in results:
        # Build a short detail string from the result dict
        detail_parts = []
        for key in ("count", "guards", "decrees", "memories", "experiences",
                    "tasks", "events", "transactions", "budgets",
                    "executive_roles", "nucleus_files", "schemas", "registries",
                    "legislations", "compliance_reports"):
            if key in result:
                detail_parts.append(f"{key}={result[key]}")
        if "note" in result:
            detail_parts.append(result["note"])
        if "error" in result:
            detail_parts.append(f"error={result['error']}")
        detail = ", ".join(detail_parts) if detail_parts else "-"
        marker = "PASS" if status == "pass" else "FAIL"
        print(f"{domain:<16} {marker:<8} {detail}")

    print(sep)
    passed = sum(1 for _, s, _ in results if s == "pass")
    total = len(results)
    print(f"  {passed}/{total} domains passed")
    print("=" * 64)


def main():
    """Entry point: run all smoke tests and exit with appropriate code."""
    results, all_pass = run_all()
    print_summary_table(results)
    if all_pass:
        print("\nAll smoke tests PASSED.")
        sys.exit(0)
    else:
        print("\nSome smoke tests FAILED.")
        sys.exit(1)


if __name__ == "__main__":
    main()
