"""الهدف: آلة حالات المهمة الفدرالية — الانتقالات المشروعة وحدها، لا غيرها.

النطاق: federal/executive/services — النواة التنفيذية
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المشكلة التي تحلّها هذه الوحدة: كان عمود `tasks.status` نصًّا حرًّا يكتب فيه من
شاء ما شاء — `created` من مخزن المهام، و`planned` من المنسّق، ولا شيء يمنع مهمّة
من أن تُعلَن `completed` وهي لم تُخطَّط، ولا يمنع مهمّة مرفوضة سياديًّا من أن
تعود للتنفيذ. الحالة بلا آلة حالات ليست حالة، بل وصف متأخّر لما حدث.

القرار: الانتقالات مُعلَنة صراحةً في `TRANSITIONS`، وكل انتقال غير مُعلَن يرفع
`IllegalTransitionError`. لا معامل `force`، ولا وضع تشخيصي، ولا تجاوز — لأن الانتقال
غير المشروع يعني ضياع الأثر التدقيقي، والأثر ليس تفصيلًا في هذه الدولة.
"""

from __future__ import annotations

from enum import Enum


class TaskState(str, Enum):
    """حالات المهمة الفدرالية.

    القيم نصّية بقصد: عمود `tasks.status` قائم في القاعدة ومكتوب فيه بالفعل
    `created`، فالتوافق مع ما هو مخزَّن شرطٌ لا خيار.
    """

    CREATED = "created"
    AUTHORIZED = "authorized"
    PLANNED = "planned"
    DISPATCHED = "dispatched"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


#: الحالات النهائية — لا انتقال بعدها إطلاقًا.
TERMINAL_STATES: frozenset[TaskState] = frozenset(
    {
        TaskState.COMPLETED,
        TaskState.FAILED,
        TaskState.REJECTED,
        TaskState.CANCELLED,
    }
)

#: الانتقالات المشروعة. ما ليس هنا ممنوع — لا استثناء ولا تجاوز.
TRANSITIONS: dict[TaskState, frozenset[TaskState]] = {
    # مهمة مُسجَّلة: إمّا تجتاز التقييم الدستوري، أو تُرفَض، أو تُلغى قبل بدئها.
    TaskState.CREATED: frozenset({TaskState.AUTHORIZED, TaskState.REJECTED, TaskState.CANCELLED}),
    # مأذونة: تُخطَّط، أو تُلغى. لا تنفيذ بلا خطة.
    TaskState.AUTHORIZED: frozenset({TaskState.PLANNED, TaskState.CANCELLED, TaskState.FAILED}),
    # مخطَّطة: تُوزَّع على وكيل، أو تسقط إن لم يوجد وكيل مؤهَّل.
    TaskState.PLANNED: frozenset({TaskState.DISPATCHED, TaskState.CANCELLED, TaskState.FAILED}),
    # موزَّعة: تبدأ التنفيذ، أو تُلغى قبل البدء.
    TaskState.DISPATCHED: frozenset({TaskState.EXECUTING, TaskState.CANCELLED, TaskState.FAILED}),
    # تنفيذ جارٍ: تنتهي بنجاح أو بفشل. الإلغاء أثناء التنفيذ ليس مدعومًا بعد،
    # لأن إلغاء عملٍ جارٍ يحتاج مقاطعة حقيقية للوكيل لا تغييرَ صفٍّ في جدول.
    TaskState.EXECUTING: frozenset({TaskState.COMPLETED, TaskState.FAILED}),
    TaskState.COMPLETED: frozenset(),
    TaskState.FAILED: frozenset(),
    TaskState.REJECTED: frozenset(),
    TaskState.CANCELLED: frozenset(),
}


class IllegalTransitionError(RuntimeError):
    """انتقال حالة غير مُعلَن في `TRANSITIONS`.

    يُرفَع ولا يُبتلع: انتقال غير مشروع يعني أن مُنادِيًا فقد تسلسل الحالة، وإخفاء
    ذلك يُنتج مهامّ «مكتملة» لم تُنفَّذ.
    """


class UnknownStateError(ValueError):
    """قيمة حالة غير معروفة في عمود `tasks.status`."""


def parse_state(value: str | TaskState) -> TaskState:
    """تحويل نصّ مخزَّن إلى حالة معروفة، أو رفعُ خطأ صريح.

    القاعدة قد تحمل نصًّا كتبه كود أقدم من آلة الحالات. الرفض الصريح أصدق من
    افتراض `created`، لأن الافتراض يُخفي انحرافًا حقيقيًّا في البيانات.
    """
    if isinstance(value, TaskState):
        return value
    try:
        return TaskState(value)
    except ValueError as exc:
        raise UnknownStateError(f"حالة مهمّة غير معروفة في القاعدة: {value!r}") from exc


def is_terminal(state: str | TaskState) -> bool:
    """هل الحالة نهائية؟"""
    return parse_state(state) in TERMINAL_STATES


def next_states(state: str | TaskState) -> frozenset[TaskState]:
    """الحالات المشروعة التالية لحالة معطاة."""
    return TRANSITIONS[parse_state(state)]


def is_legal(current: str | TaskState, target: str | TaskState) -> bool:
    """هل الانتقال مُعلَن مشروعًا؟"""
    return parse_state(target) in TRANSITIONS[parse_state(current)]


def assert_transition(current: str | TaskState, target: str | TaskState) -> TaskState:
    """التحقّق من مشروعية الانتقال وإرجاع الحالة الهدف، أو رفع `IllegalTransitionError`."""
    current_state = parse_state(current)
    target_state = parse_state(target)
    if target_state not in TRANSITIONS[current_state]:
        allowed = ", ".join(sorted(s.value for s in TRANSITIONS[current_state])) or "لا شيء"
        raise IllegalTransitionError(
            f"انتقال غير مشروع: {current_state.value} → {target_state.value}. "
            f"المسموح من {current_state.value}: {allowed}"
        )
    return target_state
