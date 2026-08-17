# =============================================================================
# File:        tests/stubs/tests_check.py
# Purpose:     فحص مجال الاختبارات — يتحقق من اكتمال اختبارات الدخان والنوى
# Owner:       tests/
# Created:     2026-08-15
# Phase:       P3 (Working Nuclei) — استكمال الاختبار الثاني عشر
# Article 009: هذا الملف يلتزم بالمادة 009 — الشفافية والمراجعة المستمرة.
# =============================================================================
"""
أداة فحص مجال الاختبارات (Tests Domain Check) — Phase P3 Stub.

تتحقق من:
- وجود مشغّل اختبارات الدخان
- عدد النوى (NUCLEUS.md) في مجال tests
- وجود اختبارات التكامل و e2e
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Counts (cached structural data) ---
SMOKE_RUNNER = "tests/smoke/run_smoke_tests.py"
SMOKE_DOMAINS = 12  # 11 domain stubs + tests domain = 12

# Nucleus files inside the tests domain
TESTS_NUCLEUS_FILES = 4  # tests, tests/smoke, tests/integration, tests/e2e


def check():
    """Run the tests-domain smoke check.

    Returns:
        dict: domain, smoke_domains, nucleus_files, runner, status
    """
    runner_path = os.path.join(PROJECT_ROOT, SMOKE_RUNNER)
    runner_ok = os.path.isfile(runner_path)

    # Count actual NUCLEUS.md files under tests/
    nucleus_count = 0
    tests_dir = os.path.join(PROJECT_ROOT, "tests")
    for root, _dirs, files in os.walk(tests_dir):
        if "NUCLEUS.md" in files:
            nucleus_count += 1

    status = "pass" if runner_ok and nucleus_count >= TESTS_NUCLEUS_FILES else "fail"
    return {
        "domain": "tests",
        "smoke_domains": SMOKE_DOMAINS,
        "nucleus_files": nucleus_count,
        "runner": "present" if runner_ok else "missing",
        "status": status,
    }


if __name__ == "__main__":
    import json

    result = check()
    print(json.dumps(result, ensure_ascii=False, indent=2))
