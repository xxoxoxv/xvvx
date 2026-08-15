"""
اختبارات الأدوات الحقيقية (Phase 4)
الهدف: التحقق من أن الأدوات تعمل فعليًا مع Sandbox و Policy Check
النطاق: services/tool_registry/sandbox
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import os
import tempfile

import pytest

from amos_federation.services.governance.canary import reset_kill_switch
from amos_federation.services.tool_registry.sandbox import (
    ToolSandbox,
    execute_tool_with_governance,
)


@pytest.fixture(autouse=True)
def cleanup_kill_switch():
    """إعادة ضبط Kill Switch قبل وبعد كل اختبار."""
    reset_kill_switch()
    yield
    reset_kill_switch()


# === 4.2: python_execute ===

def test_python_execute_simple() -> None:
    """تنفيذ كود Python بسيط وإرجاع ناتج حقيقي."""
    sandbox = ToolSandbox("python_execute")
    result = sandbox.execute_python("x = 2 + 3\nprint(f'result: {x}')")
    assert result.get("returncode") == 0
    assert "result: 5" in result.get("stdout", "")


def test_python_execute_math() -> None:
    """حساب رياضي حقيقي."""
    sandbox = ToolSandbox("python_execute")
    result = sandbox.execute_python("import math; print(math.sqrt(16))")
    assert "4.0" in result.get("stdout", "")


def test_python_execute_timeout() -> None:
    """انتهاء المهلة يعمل."""
    sandbox = ToolSandbox("python_execute", timeout_seconds=1)
    result = sandbox.execute_python("import time; time.sleep(10)")
    assert result.get("error") == "timeout"


def test_python_execute_error_handling() -> None:
    """التقاط الأخطاء."""
    sandbox = ToolSandbox("python_execute")
    result = sandbox.execute_python("1/0")
    assert result.get("error") is not None or "ZeroDivisionError" in result.get("stderr", "")


# === 4.3: sql_query ===

def test_sql_query_real_results() -> None:
    """استعلام SQL يعيد نتائج حقيقية."""
    # إنشاء قاعدة بيانات اختبار
    import sqlite3
    db_path = tempfile.mktemp(suffix=".db")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE test_data (id INTEGER, name TEXT)")
    conn.execute("INSERT INTO test_data VALUES (1, 'أحمد'), (2, 'سارة')")
    conn.commit()
    conn.close()

    sandbox = ToolSandbox("sql_query")
    result = sandbox.execute_sql("SELECT * FROM test_data", db_path=db_path)
    assert result.get("row_count") == 2
    assert result["rows"][0]["name"] == "أحمد"
    os.unlink(db_path)


def test_sql_query_blocks_writes() -> None:
    """استعلامات الكتابة ممنوعة."""
    sandbox = ToolSandbox("sql_query")
    result = sandbox.execute_sql("INSERT INTO test VALUES (1)")
    assert result.get("error") == "write_blocked"


def test_sql_query_blocks_drop() -> None:
    """DROP ممنوع."""
    sandbox = ToolSandbox("sql_query")
    result = sandbox.execute_sql("DROP TABLE test")
    assert result.get("error") == "write_blocked"


# === 4.4: http_request ===

def test_http_request_blocked_without_permission() -> None:
    """طلب HTTP محجوب بدون إذن شبكة."""
    sandbox = ToolSandbox("http_request")
    result = sandbox.execute_http("https://example.com")
    assert result.get("error") == "network_blocked"


# === 4.5: document_analysis ===

def test_document_analysis_real_file() -> None:
    """تحليل ملف حقيقي."""
    # إنشاء ملف اختبار
    test_file = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8")
    test_file.write("هذا ملف اختبار للتحليل.\nيحتوي على عدة أسطر.\nللتأكد من عمل الأداة.")
    test_file.close()

    sandbox = ToolSandbox("document_analysis")
    result = sandbox.analyze_document(test_file.name)
    assert result.get("word_count", 0) > 0
    assert result.get("line_count", 0) >= 3
    assert "ملف اختبار" in result.get("preview", "")
    os.unlink(test_file.name)


def test_document_analysis_nonexistent_file() -> None:
    """ملف غير موجود يعيد خطأ."""
    sandbox = ToolSandbox("document_analysis")
    result = sandbox.analyze_document("/nonexistent/file.txt")
    assert result.get("error") == "file_not_found"


# === 4.6: chart_generate ===

def test_chart_generate_real_png() -> None:
    """إنشاء رسم بياني حقيقي (PNG)."""
    sandbox = ToolSandbox("chart_generate")
    result = sandbox.generate_chart({"أ": 10, "ب": 20, "ج": 15}, "bar")
    assert result.get("chart_path") is not None
    assert os.path.exists(result["chart_path"])
    assert result["size_bytes"] > 0
    assert result["chart_type"] == "bar"


def test_chart_generate_pie() -> None:
    """رسم دائري."""
    sandbox = ToolSandbox("chart_generate")
    result = sandbox.generate_chart({"X": 30, "Y": 70}, "pie")
    assert os.path.exists(result["chart_path"])


# === text_summary ===

def test_text_summary_real() -> None:
    """تلخيص نص حقيقي."""
    text = "هذا الجملة الأولى وهي مهمة جدا. الجملة الثانية أقل أهمية. الجملة الثالثة مهمة أيضا وتتحدث عن البيانات."
    sandbox = ToolSandbox("text_summary")
    result = sandbox.summarize_text(text, max_sentences=2)
    assert len(result["summary"]) > 0
    assert result["original_sentences"] == 3
    assert result["sentence_count"] == 2
    assert result["summary_length"] < result["original_length"]


# === 4.9: Policy Check قبل التنفيذ ===

def test_execute_with_governance_allows_safe_tool() -> None:
    """أداة آمنة تنفذ بنجاح."""
    result = execute_tool_with_governance("chart_generate", {"data": {"a": 1, "b": 2}}, role="admin")
    assert "error" not in result or result.get("error") != "policy_denied"


def test_execute_with_governance_denies_dangerous_for_user() -> None:
    """أداة خطيرة مرفوضة للمستخدم العادي."""
    result = execute_tool_with_governance("python_execute", {"code": "print(1)"}, role="user")
    assert result.get("error") == "policy_denied"


def test_execute_with_governance_allows_dangerous_for_admin() -> None:
    """أداة خطيرة مسموحة للمشرف."""
    result = execute_tool_with_governance("python_execute", {"code": "print('hello')"}, role="admin")
    assert result.get("returncode") == 0
    assert "hello" in result.get("stdout", "")


def test_execute_with_governance_kill_switch_halt() -> None:
    """Kill Switch halt يمنع التنفيذ."""
    from amos_federation.services.governance.canary import activate_kill_switch
    activate_kill_switch("halt", "اختبار", "tester")
    with pytest.raises(Exception):  # HTTPException
        execute_tool_with_governance("chart_generate", {"data": {"a": 1}}, role="admin")


def test_execute_with_governance_publishes_event() -> None:
    """تنفيذ أداة ينشر حدث."""
    from amos_federation.common.event_bus import get_event_bus
    bus = get_event_bus()
    initial = bus.count("amos_federation.tool.executed")
    execute_tool_with_governance("chart_generate", {"data": {"a": 1, "b": 2}}, role="admin")
    assert bus.count("amos_federation.tool.executed") > initial


# === 4.7: قيود الموارد ===

def test_sandbox_workspace_isolation() -> None:
    """مساحة العمل معزولة."""
    sandbox1 = ToolSandbox("tool1")
    sandbox2 = ToolSandbox("tool2")
    assert sandbox1.workspace != sandbox2.workspace
    sandbox1.cleanup()
    sandbox2.cleanup()


def test_sandbox_cleanup_removes_files() -> None:
    """التنظيف يحذف الملفات."""
    sandbox = ToolSandbox("cleanup_test")
    workspace = sandbox.workspace
    assert os.path.exists(workspace)
    sandbox.cleanup()
    assert not os.path.exists(workspace)
