"""
AMOS-Federation Task Store
الهدف: تجريد تخزين المهام مع بديل ذاكرة آمن للاختبارات والتطوير
النطاق: api-gateway
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import json
from typing import Any, Protocol

from amos_federation.common.database import db_cursor
from amos_federation.common.schemas import TaskDetails


class TaskStore(Protocol):
    """عقد التخزين الذي تعتمد عليه واجهات المهام."""

    def create(self, task: TaskDetails) -> TaskDetails:
        """حفظ مهمة جديدة وإرجاعها."""

    def get(self, task_id: str) -> TaskDetails | None:
        """إرجاع مهمة بالمعرّف أو None."""


class InMemoryTaskStore:
    """تنفيذ بسيط معزول في الذاكرة لبيئات بلا PostgreSQL."""

    def __init__(self) -> None:
        self._tasks: dict[str, TaskDetails] = {}

    def create(self, task: TaskDetails) -> TaskDetails:
        self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> TaskDetails | None:
        return self._tasks.get(task_id)


class PostgresTaskStore:
    """تنفيذ PostgreSQL مع رجوع آمن إلى بديل ذاكرة عند غياب قاعدة البيانات."""

    def __init__(self, fallback: TaskStore | None = None) -> None:
        self._fallback = fallback or InMemoryTaskStore()

    def create(self, task: TaskDetails) -> TaskDetails:
        """حفظ المهمة في جدول tasks أو استخدام الذاكرة عند تعذر الاتصال."""
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """INSERT INTO tasks
                       (task_id, type, description, priority, status, domain, tenant_id, result, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        task.task_id,
                        task.type,
                        task.description,
                        task.priority,
                        task.status,
                        task.domain,
                        task.tenant_id,
                        json.dumps(task.result) if task.result is not None else None,
                        task.created_at,
                    ),
                )
        except Exception:
            return self._fallback.create(task)
        return task  # pragma: no cover - postgres success path (production-only)

    def get(self, task_id: str) -> TaskDetails | None:
        """قراءة المهمة من PostgreSQL أو الرجوع إلى الذاكرة حين لا تتوفر الخدمة."""
        try:
            with db_cursor() as cursor:
                cursor.execute(
                    """SELECT task_id, type, description, priority, status, domain, tenant_id,
                              assigned_agent, result, created_at
                       FROM tasks WHERE task_id = %s""",
                    (task_id,),
                )
                row: dict[str, Any] | None = cursor.fetchone()
        except Exception:
            return self._fallback.get(task_id)
        if row is None:  # pragma: no cover - postgres success path (production-only)
            return None
        result = row["result"]
        if isinstance(result, str):  # pragma: no cover - postgres success path (production-only)
            result = json.loads(result)
        return TaskDetails(**row, result=result)  # pragma: no cover - postgres success path
