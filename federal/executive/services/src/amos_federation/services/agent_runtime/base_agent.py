"""
AMOS-Federation Base Agent
الهدف: تعريف الواجهة الأساسية لكل الوكلاء في النظام
النطاق: agent-runtime
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from amos_federation.services.agent_runtime.sandbox import ToolSandbox


class BaseAgent(ABC):
    """القاعدة التي يرث منها كل وكيل."""

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        domain: str,
        permissions: list[str] | None = None,
    ) -> None:
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.domain = domain
        self.permissions = permissions or []
        self.sandbox = ToolSandbox()
        self.created_at = datetime.now(UTC)

    @abstractmethod
    async def execute(self, task: dict[str, Any], plan: list[dict[str, Any]]) -> dict[str, Any]:
        """تنفيذ مهمة وفق خطة معينة وإرجاع النتيجة."""

    def can_use_tool(self, tool_id: str) -> bool:
        """التحقق من صلاحية الوكيل لاستخدام أداة موجودة في الصندوق الرمل."""
        if tool_id not in self.sandbox.available_tools():
            return False
        if "*" in self.permissions:
            return True
        return tool_id in self.permissions

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.agent_id} domain={self.domain}>"
