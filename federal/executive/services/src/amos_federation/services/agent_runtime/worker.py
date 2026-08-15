"""
AMOS-Federation Worker Agent
الهدف: وكيل عامل ينفذ خطط المهام باستخدام الأدوات المسجلة
النطاق: agent-runtime
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from datetime import UTC, datetime
from typing import Any

from amos_federation.services.agent_runtime.base_agent import BaseAgent


class WorkerAgent(BaseAgent):
    """وكيل عامل ينفذ الخطوات بالترتيب ويسجل النتائج."""

    def __init__(
        self,
        agent_id: str = "worker-generic-001",
        domain: str = "federal",
        permissions: list[str] | None = None,
    ) -> None:
        super().__init__(agent_id, "worker", domain, permissions or ["*"])

    async def execute(
        self, task: dict[str, Any], plan: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """تنفيذ كل خطوة في الخطة بالترتيب وتجميع النتائج."""
        steps_results: list[dict[str, Any]] = []
        started_at = datetime.now(UTC)

        for step in plan:
            tool_id = step.get("tool", "")
            step_description = step.get("description", "")
            agent = step.get("agent", self.agent_id)
            step_number = step.get("number", len(steps_results) + 1)

            if not self.can_use_tool(tool_id):
                steps_results.append({
                    "number": step_number,
                    "description": step_description,
                    "tool": tool_id,
                    "agent": agent,
                    "status": "skipped",
                    "reason": f"الصلاحية غير كافية لاستخدام: {tool_id}",
                })
                continue

            tool_params = self._build_tool_params(tool_id, task, step_description)
            tool_result = self.sandbox.execute(tool_id, tool_params)

            steps_results.append({
                "number": step_number,
                "description": step_description,
                "tool": tool_id,
                "agent": agent,
                "status": "completed",
                "result": tool_result,
            })

        completed_at = datetime.now(UTC)
        return {
            "task_id": task.get("task_id"),
            "agent_id": self.agent_id,
            "status": "completed",
            "steps": steps_results,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "result_summary": self._summarize(steps_results),
        }

    def _build_tool_params(
        self, tool_id: str, task: dict[str, Any], description: str
    ) -> dict[str, Any]:
        """بناء معطيات الأداة بناءً على نوعها وسياق المهمة."""
        task_description = task.get("description", "")
        if tool_id == "sql_query":
            return {"database": "financial_db", "query": task_description}
        elif tool_id in ("generation",):
            return {"prompt": task_description}
        elif tool_id == "research_apis":
            return {"query": task_description, "sources": ["web", "internal"]}
        elif tool_id == "data_analysis":
            return {"data": [], "method": "descriptive"}
        elif tool_id == "chart_generate":
            return {"data": [], "chart_type": "bar", "title": description}
        elif tool_id == "critic_review":
            return {"target": task_description}
        return {"prompt": task_description}

    def _summarize(self, steps: list[dict[str, Any]]) -> str:
        """تلخيص نتائج الخطوات."""
        completed = sum(1 for s in steps if s.get("status") == "completed")
        skipped = sum(1 for s in steps if s.get("status") == "skipped")
        total = len(steps)
        return f"اكتملت {completed}/{total} خطوة، تخطيت {skipped}"
