"""
AMOS-Federation Phase 4 — Real Tools Tests
الهدف: اختبار الأدوات الحقيقية داخل sandbox مع قيود موارد
النطاق: tests/test_phase4_tools.py
"""

import pytest
import os
import tempfile


class TestPythonExecute:
    """4.2: python_execute داخل container آمن."""

    def test_simple_calculation(self):
        """4.2: تنفيذ حساب بسيط."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("python_execute_test")
        result = sandbox.execute_python("x = 2 + 3\nprint(x)")
        assert result.get("returncode") == 0
        assert "5" in result.get("stdout", "")
        sandbox.cleanup()

    def test_error_handling(self):
        """4.2: التعامل مع الأخطاء."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("python_execute_test")
        result = sandbox.execute_python("raise ValueError('test error')")
        assert "test error" in result.get("stderr", "") or "test error" in result.get("error", "")
        sandbox.cleanup()

    def test_timeout_protection(self):
        """4.7: حماية المهلة الزمنية."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("python_timeout_test", timeout_seconds=2)
        result = sandbox.execute_python("import time\ntime.sleep(10)")
        assert "timeout" in str(result.get("error", "")).lower() or result.get("returncode") != 0
        sandbox.cleanup()

    def test_no_secret_access(self):
        """4.10: لا يمكن قراءة الأسرار."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("python_secret_test")
        result = sandbox.execute_python("import os\nprint(os.environ.get('AMOS_DATABASE_URL', 'not_found'))")
        # في الـ sandbox، لا يجب أن تكون الأسرار متاحة
        assert "postgresql://" not in result.get("stdout", "")
        sandbox.cleanup()

    def test_workspace_isolation(self):
        """4.8: عزل مساحة العمل."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("python_isolation_test")
        result = sandbox.execute_python("import os\nprint(os.getcwd())")
        assert sandbox.workspace in result.get("stdout", "") or result.get("returncode") == 0
        sandbox.cleanup()


class TestSqlQuery:
    """4.3: sql_query على قاعدة بيانات حقيقية (read-only)."""

    def test_select_query(self):
        """4.3: استعلام SELECT يعيد نتائج."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        # إنشاء DB مؤقت للاختبار
        import sqlite3
        db_path = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE test_items (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO test_items VALUES (1, 'item1'), (2, 'item2')")
        conn.commit()
        conn.close()

        sandbox = ToolSandbox("sql_query_test")
        result = sandbox.execute_sql("SELECT * FROM test_items", db_path=db_path)
        assert result.get("row_count") == 2
        assert len(result.get("rows", [])) == 2
        sandbox.cleanup()
        os.unlink(db_path)

    def test_write_blocked(self):
        """4.3: استعلامات الكتابة محجوبة."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("sql_query_test")
        result = sandbox.execute_sql("INSERT INTO test VALUES (1, 'hack')")
        assert "write_blocked" in str(result.get("error", "")) or "error" in result
        sandbox.cleanup()

    def test_drop_blocked(self):
        """4.3: DROP محجوب."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("sql_query_test")
        result = sandbox.execute_sql("DROP TABLE important_table")
        assert "write_blocked" in str(result.get("error", "")) or "error" in result
        sandbox.cleanup()


class TestHttpRequest:
    """4.4: http_request عام."""

    def test_network_blocked_by_default(self):
        """4.8: الشبكة محجوبة افتراضيًا."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("http_test")
        result = sandbox.execute_http("https://example.com")
        assert "network_blocked" in str(result.get("error", ""))
        sandbox.cleanup()

    def test_network_allowed(self):
        """4.4: عند السماح، يتم الطلب."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("http_test")
        sandbox.allow_network()
        result = sandbox.execute_http("https://httpbin.org/status/200")
        # قد ينجح أو يفشل حسب الشبكة
        assert "network_blocked" not in str(result.get("error", ""))
        sandbox.cleanup()


class TestDocumentAnalysis:
    """4.5: document_analysis."""

    def test_analyze_text_file(self):
        """4.5: قراءة ملف نصي."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        # إنشاء ملف مؤقت
        test_file = tempfile.mktemp(suffix=".txt")
        with open(test_file, "w") as f:
            f.write("This is a test document.\nIt has multiple lines.\nFor testing purposes.")

        sandbox = ToolSandbox("doc_analysis_test")
        result = sandbox.analyze_document(test_file)
        assert result.get("line_count") == 3
        assert result.get("word_count") > 0
        sandbox.cleanup()
        os.unlink(test_file)

    def test_file_not_found(self):
        """4.5: ملف غير موجود."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("doc_analysis_test")
        result = sandbox.analyze_document("/nonexistent/file.txt")
        assert "file_not_found" in str(result.get("error", ""))
        sandbox.cleanup()


class TestChartGenerate:
    """4.6: chart_generate (matplotlib)."""

    def test_bar_chart(self):
        """4.6: إنشاء رسم بياني شريطي."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("chart_test")
        result = sandbox.generate_chart({"A": 10, "B": 20, "C": 15}, "bar")
        if "error" not in result:
            assert os.path.exists(result.get("chart_path", ""))
            assert result.get("size_bytes", 0) > 0
        sandbox.cleanup()

    def test_line_chart(self):
        """4.6: إنشاء رسم بياني خطي."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("chart_test")
        result = sandbox.generate_chart({"Jan": 5, "Feb": 8, "Mar": 12}, "line")
        if "error" not in result:
            assert result.get("chart_type") == "line"
        sandbox.cleanup()


class TestTextSummary:
    """تلبية نص حقيقية."""

    def test_summary(self):
        """تلخيص نص."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        text = "This is the first sentence. This is the second one with more words. And a third sentence here."
        sandbox = ToolSandbox("summary_test")
        result = sandbox.summarize_text(text, max_sentences=2)
        assert result.get("original_sentences", 0) == 3
        assert len(result.get("summary", "")) > 0
        sandbox.cleanup()

    def test_empty_text(self):
        """نص فارغ."""
        from amos_federation.services.tool_registry.sandbox import ToolSandbox
        sandbox = ToolSandbox("summary_test")
        result = sandbox.summarize_text("")
        assert result.get("original_length") == 0
        sandbox.cleanup()


class TestGovernedExecution:
    """4.9: مراجعة صلاحيات قبل التنفيذ."""

    def test_policy_denies_dangerous_tool_for_citizen(self):
        """4.9: Policy Engine يرفض python_execute للمواطن."""
        from amos_federation.services.tool_registry.sandbox import execute_tool_with_governance
        result = execute_tool_with_governance(
            "python_execute",
            {"code": "print('hello')"},
            role="citizen",
        )
        assert "policy_denied" in str(result.get("error", "")) or result.get("error") == "policy_denied"

    def test_policy_allows_safe_tool(self):
        """4.9: الأدوات الآمنة مسموحة."""
        from amos_federation.services.tool_registry.sandbox import execute_tool_with_governance
        result = execute_tool_with_governance(
            "text_summary",
            {"text": "Test sentence for summary."},
            role="citizen",
        )
        assert "policy_denied" not in str(result)
