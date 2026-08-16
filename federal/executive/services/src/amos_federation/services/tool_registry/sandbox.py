"""
AMOS-Federation Real Tool Sandbox
الهدف: تنفيذ أدوات حقيقية مع عزل وقيود موارد
النطاق: services/tool_registry/sandbox
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any


class ToolSandbox:
    """صندوق رملي حقيقي لتنفيذ الأدوات مع قيود موارد."""

    def __init__(self, tool_id: str, timeout_seconds: int = 10, memory_limit_mb: int = 128):
        self.tool_id = tool_id
        self.timeout = timeout_seconds
        self.memory_limit = memory_limit_mb * 1024 * 1024  # bytes
        self.workspace = tempfile.mkdtemp(prefix=f"amos_sandbox_{tool_id}_")
        self._network_allowed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self):
        """تنظيف مساحة العمل."""
        shutil.rmtree(self.workspace, ignore_errors=True)

    def allow_network(self):
        """السماح بالوصول للشبكة."""
        self._network_allowed = True

    def execute_python(self, code: str) -> dict[str, Any]:
        """تنفيذ كود Python حقيقي مع قيود."""
        script_path = os.path.join(self.workspace, "script.py")
        result_path = os.path.join(self.workspace, "result.json")

        wrapper = f"""
import json
import sys
import resource
import os

# قيود الموارد
try:
    resource.setrlimit(resource.RLIMIT_AS, ({self.memory_limit}, {self.memory_limit}))
except Exception:
    pass

result = {{"stdout": "", "stderr": "", "output": None, "error": None}}

try:
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    from io import StringIO
    stdout_buf = StringIO()
    stderr_buf = StringIO()
    sys.stdout = stdout_buf
    sys.stderr = stderr_buf

    exec_result = None
    exec({repr(code)}, {{"__name__": "__main__"}}, locals())

    result["stdout"] = stdout_buf.getvalue()
    result["stderr"] = stderr_buf.getvalue()
    result["output"] = exec_result
except Exception as e:
    result["error"] = str(e)
    result["stderr"] = str(e)
finally:
    sys.stdout = old_stdout
    sys.stderr = old_stderr

with open({repr(result_path)}, "w") as f:
    json.dump(result, f, ensure_ascii=False, default=str)
"""
        with open(script_path, "w") as f:
            f.write(wrapper)

        try:
            proc = subprocess.run(
                ["python3", script_path],
                timeout=self.timeout,
                capture_output=True,
                text=True,
                cwd=self.workspace,
                env={
                    "PATH": os.environ.get("PATH", "/usr/bin:/usr/local/bin"),
                    "HOME": self.workspace,
                    "PYTHONPATH": "",
                    "AMOS_SANDBOX": "1",
                },
            )
            if os.path.exists(result_path):
                with open(result_path) as f:
                    result = json.load(f)
            else:
                result = {
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "error": "no result file",
                    "output": None,
                }
            result["returncode"] = proc.returncode
            result["tool"] = self.tool_id
            return result
        except subprocess.TimeoutExpired:
            return {"error": "timeout", "tool": self.tool_id, "timeout_seconds": self.timeout}
        except Exception as e:
            return {"error": str(e), "tool": self.tool_id}

    def execute_sql(self, query: str, db_path: str | None = None) -> dict[str, Any]:
        """تنفيذ استعلام SQL حقيقي (read-only)."""
        import sqlite3

        if db_path is None:
            db_path = os.environ.get("AMOS_DATABASE_URL", "sqlite:///amos_federation.db").replace(
                "sqlite:///", ""
            )
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.getcwd(), db_path)

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # منع استعلامات الكتابة
            query_upper = query.strip().upper()
            if any(
                query_upper.startswith(kw)
                for kw in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE"]
            ):
                return {"error": "write_blocked", "message": "SQL sandbox: read-only queries only"}

            cur.execute(query)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            data = [dict(row) for row in rows]
            conn.close()
            return {
                "columns": columns,
                "rows": data,
                "row_count": len(data),
                "tool": self.tool_id,
            }
        except Exception as e:
            return {"error": str(e), "tool": self.tool_id}

    def execute_http(
        self, url: str, method: str = "GET", headers: dict | None = None
    ) -> dict[str, Any]:
        """تنفيذ طلب HTTP حقيقي."""
        if not self._network_allowed:
            return {
                "error": "network_blocked",
                "message": "Sandbox: network not allowed for this tool",
            }

        try:
            import urllib.request

            req = urllib.request.Request(url, method=method)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return {
                    "status_code": resp.status,
                    "headers": dict(resp.headers),
                    "body": body[:10000],  # حد 10KB
                    "tool": self.tool_id,
                }
        except Exception as e:
            return {"error": str(e), "tool": self.tool_id}

    def analyze_document(self, file_path: str) -> dict[str, Any]:
        """تحليل مستند نصي حقيقي."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"error": "file_not_found", "path": file_path, "tool": self.tool_id}

            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            words = content.split()

            return {
                "file": str(path.name),
                "size_bytes": path.stat().st_size,
                "line_count": len(lines),
                "word_count": len(words),
                "char_count": len(content),
                "preview": content[:500],
                "tool": self.tool_id,
            }
        except Exception as e:
            return {"error": str(e), "tool": self.tool_id}

    def generate_chart(self, data: dict[str, Any], chart_type: str = "bar") -> dict[str, Any]:
        """إنشاء رسم بياني حقيقي."""
        try:
            import matplotlib

            matplotlib.use("Agg")  # لا واجهة رسومية
            import matplotlib.pyplot as plt

            chart_path = os.path.join(self.workspace, f"chart_{uuid.uuid4().hex[:8]}.png")
            labels = list(data.keys())
            values = list(data.values())

            fig, ax = plt.subplots(figsize=(8, 4))
            if chart_type == "bar":
                ax.bar(labels, values)
            elif chart_type == "line":
                ax.plot(labels, values, marker="o")
            elif chart_type == "pie":
                ax.pie(values, labels=labels, autopct="%1.1f%%")
            else:
                ax.bar(labels, values)

            ax.set_title("AMOS Federation Chart")
            plt.tight_layout()
            plt.savefig(chart_path, dpi=100)
            plt.close()

            size = os.path.getsize(chart_path)
            return {
                "chart_path": chart_path,
                "chart_type": chart_type,
                "size_bytes": size,
                "data_points": len(labels),
                "tool": self.tool_id,
            }
        except ImportError:
            return {"error": "matplotlib_not_available", "tool": self.tool_id}
        except Exception as e:
            return {"error": str(e), "tool": self.tool_id}

    def summarize_text(self, text: str, max_sentences: int = 3) -> dict[str, Any]:
        """تلخيص نص حقيقي باستخدام تردد الكلمات."""
        import re

        # تنظيف النص
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return {"summary": "", "original_length": 0, "summary_length": 0, "tool": self.tool_id}

        # حساب تردد الكلمات
        words = re.findall(r"\w+", text.lower())
        word_freq = {}
        for w in words:
            if len(w) > 2:
                word_freq[w] = word_freq.get(w, 0) + 1

        # ترتيب الجمل حسب مجموع تردد كلماتها
        sentence_scores = []
        for i, sent in enumerate(sentences):
            sent_words = re.findall(r"\w+", sent.lower())
            score = sum(word_freq.get(w, 0) for w in sent_words) / max(len(sent_words), 1)
            sentence_scores.append((i, score, sent))

        sentence_scores.sort(key=lambda x: -x[1])
        top = sorted(sentence_scores[:max_sentences], key=lambda x: x[0])

        summary = ". ".join(s[2] for s in top)
        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "sentence_count": len(top),
            "original_sentences": len(sentences),
            "tool": self.tool_id,
        }


# === تنفيذ الأدوات: تخويل ثم صندوق ===
#
# `python_execute` صار يمرّ عبر طبقة المزوِّدات (R5): يُختار المزوِّد من
# `AMOS_SANDBOX_PROVIDER`، والافتراضي `local` وهو نفس العملية الفرعية المقيَّدة
# التي كانت هنا — فلا تغيير سلوك لمن لم يُعِدّ شيئًا. وبقية الأدوات المتخصّصة
# (SQL، الرسم، المستندات، التلخيص) تبقى على `ToolSandbox` أعلاه لأنها ليست تنفيذ
# كود عامًّا ولا معنى لتوزيعها على مزوِّد بعد.
#
# نطاق التخويل مُعلَن في كل نتيجة بحقل `authorization_scope`:
#
# - `AGENT_CHAIN` — مُرِّر `agent_id`، فاجتيزت السلسلة كاملة:
#   Agent → Role → Capability → Permission → Tool → Sandbox.
# - `ROLE_ONLY` — لم يُمرَّر `agent_id`، فالمفحوص هو الدور وحده (kill switch +
#   محرِّك السياسة). وهذا **أضعف**، ويُقال في النتيجة ولا يُقدَّم كتخويل كامل.


#: نطاقات التخويل الممكنة — تُفحَص في الاختبارات.
AUTHORIZATION_SCOPES: tuple[str, ...] = ("AGENT_CHAIN", "ROLE_ONLY")

#: أدوات تمرّ عبر طبقة المزوِّدات لا عبر مُعالِج محلّي.
PROVIDER_BACKED_TOOLS: frozenset[str] = frozenset({"python_execute"})


def execute_tool_with_governance(
    tool_id: str,
    params: dict[str, Any],
    role: str = "user",
) -> dict[str, Any]:
    """نفِّذ أداة بعد التخويل — ولا يُنشأ صندوق قبله بحال."""
    from amos_federation.common.event_bus import get_event_bus
    from amos_federation.services.governance.canary import enforce_kill_switch, get_system_status
    from amos_federation.services.governance.policy_engine import get_policy_engine

    agent_id = params.get("agent_id")
    scope = "AGENT_CHAIN" if agent_id else "ROLE_ONLY"

    if agent_id:
        # السلسلة الكاملة. الرفض يُرجَع قاموسًا للتوافُق مع النداءات القائمة،
        # لكنه رفض حقيقي: لا صندوق يُنشأ بعده.
        from amos_federation.services.tool_registry.authorized_execution import (
            AuthorizationDenied,
            authorize,
        )

        try:
            decision = authorize(
                agent_id=str(agent_id),
                tool_id=tool_id,
                actor_role=role,
            )
        except AuthorizationDenied as denial:
            return {
                "error": "policy_denied" if denial.stage == "tool" else "authorization_denied",
                "denied_at": denial.stage,
                "reason": denial.reason,
                "tool": tool_id,
                "agent_id": agent_id,
                "authorization_scope": scope,
            }
        stages = list(decision.stages_passed)
    else:
        # 1. Kill Switch — يرفع استثناءً كما كان.
        enforce_kill_switch(tool_id, role)

        # 2. محرِّك السياسة على الدور.
        engine = get_policy_engine()
        state = get_system_status()["level"]
        policy_result = engine.evaluate_tool_access(tool_id, role, state)
        if not policy_result["allowed"]:
            return {
                "error": "policy_denied",
                "denied_by": policy_result["denied_by"],
                "tool": tool_id,
                "authorization_scope": scope,
            }
        stages = ["role", "tool"]

    # 3. التنفيذ — الآن فقط يُنشأ صندوق.
    if tool_id in PROVIDER_BACKED_TOOLS:
        result = _execute_via_provider(tool_id, params, agent_id=agent_id)
    else:
        result = _execute_locally(tool_id, params)
        if "error" in result and result["error"] == "unknown_tool":
            return {**result, "authorization_scope": scope}

    result["authorization_scope"] = scope
    result["authorization_stages"] = stages

    # 4. نشر حدث بنَسَب التنفيذ وصدقه.
    get_event_bus().publish(
        "amos_federation.tool.executed",
        {
            "tool_id": tool_id,
            "agent_id": params.get("agent_id", "unknown"),
            "result": "error" if "error" in result else "success",
            "task_id": params.get("task_id"),
            "provider": result.get("provider"),
            "execution_fidelity": result.get("execution_fidelity"),
            "execution_id": result.get("execution_id"),
            "correlation_id": result.get("correlation_id"),
            "authorization_scope": scope,
        },
    )
    return result


def _execute_via_provider(
    tool_id: str,
    params: dict[str, Any],
    *,
    agent_id: Any = None,
) -> dict[str, Any]:
    """نفِّذ عبر طبقة المزوِّدات، وأعلِن الغياب غيابًا لا محاكاةً.

    `ProviderUnavailableError` تُترجَم إلى `execution_fidelity = "UNAVAILABLE"`
    مع سببها. ولا مسار هنا يُنتج `SIMULATION` عند الفشل.
    """
    from amos_federation.services.tool_registry.providers.contract import (
        ExecutionContext,
        ExecutionRequest,
        ProviderUnavailableError,
        SandboxSpec,
    )
    from amos_federation.services.tool_registry.providers.selection import execute_in_sandbox

    spec = SandboxSpec(
        tool_id=tool_id,
        timeout_seconds=int(params.get("timeout_seconds", 10)),
        memory_limit_mb=int(params.get("memory_limit_mb", 256)),
        network_policy=str(params.get("network_policy", "DENY")),
        secret_allowlist=tuple(params.get("secret_allowlist", ()) or ()),
    )
    context = ExecutionContext(
        tool_id=tool_id,
        agent_id=str(agent_id) if agent_id else None,
        task_id=params.get("task_id"),
    )
    request = ExecutionRequest(code=params.get("code", ""), context=context)

    try:
        result = execute_in_sandbox(spec, request)
    except ProviderUnavailableError as exc:
        return {
            "error": "provider_unavailable",
            "message": str(exc),
            "tool": tool_id,
            "execution_fidelity": "UNAVAILABLE",
            "fidelity_reason": str(exc),
            "exit_code": None,
            "returncode": None,
            "stdout": "",
            "stderr": "",
        }

    payload = result.as_dict()
    payload["tool"] = tool_id
    # اسم قديم محفوظ للنداءات القائمة — القيمة نفسها لا قيمة موازية.
    payload["returncode"] = result.exit_code
    if result.error:
        payload["error"] = result.error
    return payload


def _execute_locally(tool_id: str, params: dict[str, Any]) -> dict[str, Any]:
    """الأدوات المتخصّصة على `ToolSandbox` المحلّي — REAL على المضيف."""
    from amos_federation.services.executive_core.fidelity import ExecutionFidelity

    sandbox = ToolSandbox(tool_id)
    try:
        if tool_id == "sql_query":
            result = sandbox.execute_sql(params.get("query", ""))
        elif tool_id == "http_request":
            if params.get("allow_network"):
                sandbox.allow_network()
            result = sandbox.execute_http(params.get("url", ""), params.get("method", "GET"))
        elif tool_id == "document_analysis":
            result = sandbox.analyze_document(params.get("file_path", ""))
        elif tool_id == "chart_generate":
            result = sandbox.generate_chart(params.get("data", {}), params.get("chart_type", "bar"))
        elif tool_id == "text_summary":
            result = sandbox.summarize_text(params.get("text", ""), params.get("max_sentences", 3))
        else:
            return {"error": "unknown_tool", "tool": tool_id}
    finally:
        sandbox.cleanup()

    result.setdefault("provider", "local")
    result.setdefault("execution_fidelity", ExecutionFidelity.REAL.value)
    return result
