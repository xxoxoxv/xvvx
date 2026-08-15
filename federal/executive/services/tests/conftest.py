# AMOS-Federation test configuration
# الهدف: ضمان بيئة اختبار نظيفة ومنع Flaky Tests
# النطاق: federal/executive/services/tests
# المالك: federal/executive/services
# تاريخ الإنشاء: 2026-08-15

"""Pytest configuration for AMOS-Federation tests.

Forces a clean test database state before each session to prevent
flaky tests caused by stale SQLite files. Never touches production DB.
"""

import contextlib
import os
import shutil
from pathlib import Path

# Force test environment — override any production env vars
os.environ["AMOS_ENVIRONMENT"] = "test"
os.environ["AMOS_DATABASE_URL"] = "sqlite:///amos_federation_test.db"
os.environ["AMOS_JWT_SECRET"] = "test_secret_at_least_32_characters_long"
os.environ["AMOS_CLAUDE_API_KEY"] = "test_key_not_real"

# Test-only database file (never touch production files)
TEST_DB_FILE = "amos_federation_test.db"


def _cleanup_test_db(workspace: Path) -> None:
    """Remove only the test database file, never production files."""
    for db_file in workspace.glob(TEST_DB_FILE):
        with contextlib.suppress(OSError):
            db_file.unlink()
    # Also clean test-related journal files
    for pattern in (TEST_DB_FILE + "-*", TEST_DB_FILE + "-wal", TEST_DB_FILE + "-shm"):
        for f in workspace.glob(pattern):
            with contextlib.suppress(OSError):
                f.unlink()
    # Clean egg-info cache if present
    for egg_dir in workspace.glob("*.egg-info"):
        with contextlib.suppress(OSError):
            shutil.rmtree(egg_dir, ignore_errors=True)


def pytest_sessionstart(session):
    """Clean up test database before test session starts."""
    workspace = Path(__file__).resolve().parent.parent
    _cleanup_test_db(workspace)


def pytest_sessionfinish(session, exitstatus):
    """Clean up test database after test session ends."""
    workspace = Path(__file__).resolve().parent.parent
    _cleanup_test_db(workspace)
