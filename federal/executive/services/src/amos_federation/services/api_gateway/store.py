"""
AMOS-Federation Task Store
الهدف: مرجعية واحدة لتخزين المهام — طبقة قاعدة البيانات (TaskModel) هي مصدر
الحقيقة الدائم، مع تحويل صريح بين DTO الطبقة التشغيلية والنموذج الدائم.
النطاق: api-gateway
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
تاريخ آخر تعديل: 2026-08-16

قرار المرجعية (E2.2-G):
- `TaskModel` في `common/database.py` هو **النموذج الدائم الوحيد** للمهام.
- `TaskDetails` في `common/schemas.py` هو DTO الطبقة التشغيلية فقط، وله تحويل
  صريح ومسمّى إلى `TaskModel` (انظر `TASK_DTO_TO_MODEL_FIELDS`).
- `InMemoryTaskStore` بديل اختباري صريح **وليس مصدر حقيقة**، ولا يُستخدم كرجوع
  تلقائي صامت عند تعذر قاعدة البيانات.
- أُزيل مسار SQL الخام الذي كان يخاطب عمودًا `tasks.task_id` غير موجود في
  `TaskModel`؛ ذلك المسار كان نموذجًا ثانيًا متنافسًا ويفشل صامتًا إلى الذاكرة.
"""

from datetime import UTC, datetime
from typing import Any, Protocol

from amos_federation.common.database import TaskModel, get_session_factory, init_db
from amos_federation.common.schemas import TaskDetails

# التحويل الصريح بين حقول DTO وحقول النموذج الدائم.
# المفتاح: حقل `TaskDetails` — القيمة: عمود `TaskModel`.
# هذا الجدول هو التوثيق التنفيذي لقرار «مرجعية واحدة»: `task_id` في الـDTO هو
# `id` في النموذج الدائم، ولا يوجد عمود `task_id` في `TaskModel`.
TASK_DTO_TO_MODEL_FIELDS: dict[str, str] = {
    "task_id": "id",
    "type": "type",
    "description": "description",
    "status": "status",
    "priority": "priority",
    "domain": "domain",
    "tenant_id": "tenant_id",
    "assigned_agent": "assigned_agent",
    "result": "result",
    "created_at": "created_at",
}

# قيم افتراضية للحقول التي يسمح DTO بغيابها ولا يسمح النموذج الدائم بأن تكون بلا معنى.
_DOMAIN_DEFAULT = "general"
_TENANT_DEFAULT = "default"


class TaskStoreUnavailableError(RuntimeError):
    """تعذّر الوصول إلى مصدر الحقيقة الدائم للمهام.

    يُرفع صراحةً بدلًا من الرجوع الصامت إلى الذاكرة: بديل الذاكرة ليس مصدر حقيقة،
    وإخفاء تعذّر القاعدة يجعل النظام يبدو ناجحًا وهو لا يحفظ شيئًا.
    """


class TaskStore(Protocol):
    """عقد التخزين الذي تعتمد عليه واجهات المهام."""

    def create(self, task: TaskDetails) -> TaskDetails:
        """حفظ مهمة جديدة وإرجاعها."""

    def get(self, task_id: str) -> TaskDetails | None:
        """إرجاع مهمة بالمعرّف أو None."""


def task_details_to_model_kwargs(task: TaskDetails) -> dict[str, Any]:
    """تحويل DTO إلى معاملات `TaskModel` عبر `TASK_DTO_TO_MODEL_FIELDS` حصرًا."""
    values: dict[str, Any] = {}
    for dto_field, column in TASK_DTO_TO_MODEL_FIELDS.items():
        values[column] = getattr(task, dto_field)
    values["domain"] = values["domain"] or _DOMAIN_DEFAULT
    values["tenant_id"] = values["tenant_id"] or _TENANT_DEFAULT
    values["created_at"] = _as_naive_utc(values["created_at"])
    return values


def task_details_to_model(task: TaskDetails) -> TaskModel:
    """بناء صف `TaskModel` من DTO."""
    return TaskModel(**task_details_to_model_kwargs(task))


def task_model_to_details(row: TaskModel) -> TaskDetails:
    """التحويل العكسي: صف `TaskModel` → DTO، بنفس جدول الحقول."""
    values: dict[str, Any] = {}
    for dto_field, column in TASK_DTO_TO_MODEL_FIELDS.items():
        values[dto_field] = getattr(row, column)
    values["domain"] = values["domain"] or _DOMAIN_DEFAULT
    values["tenant_id"] = values["tenant_id"] or _TENANT_DEFAULT
    values["created_at"] = values["created_at"] or datetime.now(UTC)
    return TaskDetails(**values)


def _as_naive_utc(value: datetime | None) -> datetime:
    """توحيد الوقت إلى UTC بلا منطقة زمنية — عمود `DateTime` بلا timezone."""
    if value is None:
        return datetime.now(UTC).replace(tzinfo=None)
    if value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)
    return value


class InMemoryTaskStore:
    """بديل معزول في الذاكرة — **للاختبارات فقط، وليس مصدر حقيقة**.

    لا يُستخدم كرجوع تلقائي عند تعذّر قاعدة البيانات؛ من يريده يبنيه صراحةً.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, TaskDetails] = {}

    def create(self, task: TaskDetails) -> TaskDetails:
        self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> TaskDetails | None:
        return self._tasks.get(task_id)


class DatabaseTaskStore:
    """مصدر الحقيقة الدائم للمهام: `TaskModel` عبر طبقة قاعدة البيانات.

    يعمل على PostgreSQL في الإنتاج وعلى SQLite في الاختبارات الخفيفة بنفس
    النموذج ونفس التحويل — لا SQL خاص بلهجة، ولا عمود خارج `TaskModel`.
    عند تعذّر القاعدة يُرفع `TaskStoreUnavailableError` ولا يُخفى الفشل.
    """

    def __init__(self) -> None:
        # نفس سلوك التهيئة القائم في `common/persistent.py`: إنشاء الجداول إن غابت.
        init_db()

    def create(self, task: TaskDetails) -> TaskDetails:
        """حفظ المهمة في جدول `tasks` عبر `TaskModel`."""
        session = None
        try:
            session = get_session_factory()()
            session.merge(task_details_to_model(task))
            session.commit()
        except Exception as error:
            if session is not None:
                session.rollback()
            raise TaskStoreUnavailableError(
                f"تعذّر حفظ المهمة {task.task_id} في مصدر الحقيقة الدائم"
            ) from error
        finally:
            if session is not None:
                session.close()
        return task

    def get(self, task_id: str) -> TaskDetails | None:
        """قراءة المهمة من `TaskModel` بمفتاحها الدائم `id`."""
        session = None
        try:
            session = get_session_factory()()
            row = session.query(TaskModel).filter(TaskModel.id == task_id).first()
        except Exception as error:
            raise TaskStoreUnavailableError(
                f"تعذّرت قراءة المهمة {task_id} من مصدر الحقيقة الدائم"
            ) from error
        else:
            return None if row is None else task_model_to_details(row)
        finally:
            if session is not None:
                session.close()
