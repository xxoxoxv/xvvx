#!/usr/bin/env python3
"""
فحص هوية المستودع — Repository Identity Checker
الهدف: التحقق من أن كل مجلد يحتوي على README.md وكل ملف يحتوي على ترويسة تعريفية
النطاق: المستودع كامل
المالك: governance/
تاريخ الإنشاء: 2026-08-15

CI يفشل إذا وُجد مجلد بلا README أو ملف بلا ترويسة تعريفية.
Usage: python check_repository_identity.py /path/to/amos-federation
"""

import sys
import re
from pathlib import Path


def check_readme(directory: Path) -> list[str]:
    """تحقق من وجود README.md في كل مجلد يحتوي على ملفات."""
    errors = []
    skip_dirs = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "node_modules", ".venv", "venv", "env", ".egg-info", "egg-info"}
    for item in sorted(directory.rglob("*")):
        if item.is_dir():
            # Skip if any parent is in skip_dirs or ends with .egg-info
            if any(part in skip_dirs for part in item.parts) or item.name.endswith(".egg-info"):
                continue
            readme = item / "README.md"
            if not readme.exists():
                # Check if directory has any files directly (not just subdirs)
                has_files = any(f.is_file() for f in item.iterdir())
                if has_files:
                    errors.append(f"MISSING_README: {item}/README.md")
    return errors


def check_file_header(directory: Path) -> list[str]:
    """تحقق من وجود ترويسة تعريفية في كل ملف .md و .py و .yaml و .rego و .sql."""
    errors = []
    exempt_patterns = [".gitignore", ".gitattributes", ".example", "LICENSE"]

    # Identity markers that count as a valid header
    md_identity_markers = [
        "## الهدف", "## التعريف", "## النطاق", "## المالك",
        "## الهوية", "# ", "## الهدف:",
    ]
    code_identity_markers = [
        '"""',  # Python docstring
        "# الهدف:", "# التعريف:", "# النطاق:", "# المالك:",
        "# tool_id:", "# Tool Manifest", "# Model BOM",
        "# AMOS-Federation", "# Policy-as-Code",
        "# AMOS-Federation Core Database",
        "# كل حدث", "# Event Contracts",
        "# سجل", "# بوابات", "# مستويات",
        "# خطوط", "# أهداف", "# الذاكرة",
        "# النموذج", "# هوية",
        "# الديباجة", "# المادة", "# الكبسولة",
        "# ولاية", "# مصفوفة", "# مقدمو",
        "# ميثاق", "# خارطة", "# المساهمون",
        "# نظام", "# معجم", "# خريطة",
        "# خطة", "# قالب", "# سجل الإصدارات",
        "-- AMOS-Federation", "-- كل حدث",
        '"$comment"', '"$id"', '"$schema"',
    ]

    extensions = ["*.md", "*.py", "*.yaml", "*.yml", "*.rego", "*.sql", "*.json"]

    skip_dirs = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".mypy_cache", "node_modules", ".venv", "venv", "env", ".egg-info", "egg-info"}
    for pattern in extensions:
        for filepath in sorted(directory.rglob(pattern)):
            if filepath.name == "README.md":
                continue  # READMEs are checked separately
            if any(exempt in filepath.name for exempt in exempt_patterns):
                continue
            # Skip files inside skipped directories or .egg-info
            if any(part in skip_dirs for part in filepath.parts) or any(
                part.endswith(".egg-info") for part in filepath.parts
            ):
                continue

            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            first_500 = content[:500]

            # For .md files: check for identity markers (## الهدف or ## التعريف etc.)
            if filepath.suffix == ".md":
                has_header = any(marker in first_500 for marker in md_identity_markers)
            else:
                has_header = any(marker in first_500 for marker in code_identity_markers)

            if not has_header:
                errors.append(f"MISSING_HEADER: {filepath}")

    return errors


if __name__ == "__main__":
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    print(f"فحص هوية المستودع: {directory}")
    print("=" * 60)

    errors = []
    errors.extend(check_readme(directory))
    errors.extend(check_file_header(directory))

    if errors:
        print(f"\nفشل: {len(errors)} انتهاك هوية:")
        for error in errors:
            print(f"  {error}")
        sys.exit(1)
    else:
        print("\nنجح: كل المجلدات تحتوي على README.md وكل الملفات تحتوي على ترويسة.")
        sys.exit(0)
