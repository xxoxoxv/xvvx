"""الهدف: ترجمة أخطاء النواة التنفيذية إلى رموز HTTP — تعريف واحد لا أربعة.

النطاق: federal/executive/services — النواة التنفيذية (طبقة الواجهات)
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

لماذا وحدة مستقلّة: بعد R1 صارت أربع خدمات تدخل النواة (`executive-core`,
`api-gateway`, `orchestrator`, `agent-runtime`). لو نسخت كل واحدة ترجمة الأخطاء،
لصار للدولة أربع سياسات HTTP لنفس الخطأ، وانحرفت واحدة منها بلا أن يلاحظ أحد.
هنا سياسة واحدة، ومن يخالفها يخالف استيرادًا ظاهرًا في الشِفرة.

هذه الوحدة لا تحتوي منطق سيادة ولا حالات ولا تدقيق — ترجمة فقط.
"""

from __future__ import annotations

from fastapi import HTTPException

from amos_federation.services.executive_core.engine import ExecutionRefusedError
from amos_federation.services.executive_core.repository import TaskNotFoundError
from amos_federation.services.executive_core.sovereignty_bridge import SovereigntyUnavailableError
from amos_federation.services.executive_core.states import IllegalTransitionError, UnknownStateError

#: سبب رفض التنفيذ المباشر: طلب حمل مهمّة وخطة خامّتين بلا مهمّة قانونية في القاعدة.
#: نصّ واحد يُستورَد في الخدمة والاختبار، فلا يتفرّق المعنى بين الاثنين.
EXECUTION_BYPASS_FORBIDDEN = (
    "execution_bypass_forbidden: التنفيذ المباشر بمهمّة وخطة خامّتين ممنوع. "
    "المهمّة تُقبَل أولًا في النواة التنفيذية (POST /v1/tasks) ثم تُنفَّذ بمعرّفها، "
    "لأن التنفيذ بلا إذن سيادي وانتقال حالة ذرّي وقيد تدقيق ليس تنفيذًا في الدولة."
)

#: سبب رفض التخطيط الدائم لمهمّة غير مقبولة في القاعدة.
PLAN_REQUIRES_CANONICAL_TASK = (
    "canonical_task_required: التخطيط الدائم يحتاج مهمّة مقبولة في النواة التنفيذية. "
    "أرسل `task_id` لمهمّة قائمة، أو استخدم `preview=true` لخطة استطلاعية لا تُحفَظ."
)


def to_http_exception(exc: Exception) -> HTTPException:
    """رمز HTTP للخطأ، أو إعادة رفعه إن لم يكن من أخطاء النواة المعروفة.

    الأخطاء غير المعروفة **لا** تُترجَم إلى 500 مجمَّل: تُرفَع كما هي ليظهر سببها
    في السجل بدل أن يُطمَس تحت رسالة عامّة.
    """
    if isinstance(exc, TaskNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, IllegalTransitionError | UnknownStateError | ExecutionRefusedError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, SovereigntyUnavailableError):
        return HTTPException(status_code=503, detail=str(exc))
    raise exc
