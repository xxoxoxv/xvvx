"""
AMOS-Federation Shared Schemas
الهدف: نماذج Pydantic المشتركة لعقود واجهات الخدمات
النطاق: كل خدمات AMOS-Federation
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskRequest(BaseModel):
    """طلب إنشاء مهمة جديدة."""

    type: Literal["analysis", "report", "data", "generic"] = "generic"
    description: str = Field(min_length=1, max_length=10000)
    priority: Literal["low", "normal", "high", "critical"] = "normal"
    domain: str | None = Field(default=None, max_length=100)
    tenant_id: str | None = Field(default=None, max_length=100)


class TaskAccepted(BaseModel):
    """استجابة قبول مهمة بشكل غير متزامن."""

    task_id: str
    status: str
    accepted_at: datetime


class TaskDetails(TaskRequest):
    """تفاصيل مهمة محفوظة في المستودع."""

    task_id: str
    status: str
    created_at: datetime
    assigned_agent: str | None = None
    result: dict[str, Any] | None = None


class AgentManifestModel(BaseModel):
    """بيان وكيل مسجل في البوابة."""

    agent_id: str = Field(min_length=1)
    agent_type: str = "worker"
    domain: str | None = None
    name: str
    description: str | None = None
    permissions: list[str] = Field(default_factory=list)


class ToolManifestModel(BaseModel):
    """بيان أداة مسجلة في البوابة."""

    tool_id: str = Field(min_length=1)
    name: str
    version: str = "1.0.0"
    risk_level: Literal["low", "medium", "high", "critical"] = "low"
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class MemoryStore(BaseModel):
    """طلب حفظ عنصر ذاكرة."""

    key: str
    value: dict[str, Any]
    tenant_id: str | None = None


class MemoryQuery(BaseModel):
    """طلب بحث ضمن الذاكرة."""

    query: str
    tenant_id: str | None = None
    limit: int = Field(default=10, ge=1, le=100)


class HealthResponse(BaseModel):
    """استجابة فحص صحة الخدمة."""

    status: Literal["healthy"] = "healthy"
    service: str


class ReadyResponse(BaseModel):
    """استجابة جاهزية الخدمة لاستقبال الطلبات."""

    status: Literal["ready"] = "ready"
    service: str
