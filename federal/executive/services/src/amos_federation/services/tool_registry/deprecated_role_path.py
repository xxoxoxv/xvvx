"""
AMOS-Federation DEPRECATED Declared-Role Compatibility Adapter
الهدف: إبقاء نداءات ما قبل R6 عاملة في التطوير وحده، بعزلها في وحدة واحدة موسومة
النطاق: services/tool_registry
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R6.1)

## لماذا وحدة منفصلة

بعد R6 كان لطبقة التخويل **مسارا ثقة**: مدخل كانوني يلزمه مبدأ مُتحقَّق منه،
ومعامل `role=` يقول به المُستدعي عن نفسه فيُلَفّ في سياق `UNVERIFIED`. والثاني
كان يفشل مغلقًا في الإنتاج ويُوسَم في كل نتيجة — لكنه **بقي معاملًا في دالّة
الإنتاج نفسها**، فكان قارئ التوقيع يرى بابين ولا يعرف أيّهما المقصود.

R6.1 أزالت المعامل من دالّة الإنتاج، ونقلت ما تبقّى إلى هنا. والفرق ليس شكليًّا:

- `sandbox.execute_tool_with_governance` صار **يلزمه `principal`**، فلا يوجد فيه
  معامل دور يُمرَّر ادّعاءً. ويحرس ذلك اختبار على التوقيع.
- والادّعاء لم يبقَ له إلا هذه الوحدة، واسمها ووسمها يقولان ما هي.

## ما يفعله هذا المُهاجر

يبني سياق `UNVERIFIED` صريحًا من دور مُدّعىً، ثم يُسلِّمه للمسار الكانوني. فهو
**لا يمنح ثقة**: طبقة التخويل ترى `UNVERIFIED` وتتصرّف على ذلك — لا ترجمة دور
(فلا يصير `king` مديرًا)، ولا فحص مستأجر يُحسَب مُجتازًا، والنتيجة تُعلِن عدم
التحقّق.

## وحدّه الصارم

يرفع `DeprecatedRolePathUnavailableError` في أي بيئة إنتاجية **قبل** أن يلمس
أي شيء. وهذا فحصٌ ثانٍ لا وحيد: `unverified_context` ترفع هناك أيضًا. والتكرار
مقصود — طبقتان تفشلان مغلقتين أحسن من واحدة.

## ولمن يقرأ هذا بحثًا عن الطريق الصحيح

    from amos_federation.services.governance.session_identity import resolve_context
    from amos_federation.services.tool_registry.sandbox import execute_tool_for_principal

    context = resolve_context(session_token)
    execute_tool_for_principal("python_execute", params, context)
"""

from __future__ import annotations

import os
import warnings
from typing import Any

from amos_federation.common.config import PRODUCTION_ENVIRONMENTS
from amos_federation.common.principal import unverified_context

#: وسم يُقرأ ساكنًا — الاختبارات تؤكّد وجوده في هذا الملف وغيابه من مسار الإنتاج.
DEPRECATED_MARKER = "DEPRECATED"

#: أسماء المُهاجرين المُهملين — قائمة واحدة معلومة، لا مسارات متفرّقة.
DEPRECATED_ENTRYPOINTS: tuple[str, ...] = ("execute_tool_with_declared_role",)


class DeprecatedRolePathUnavailableError(RuntimeError):
    """مسار الدور المُدّعى مُستدعىً في بيئة إنتاجية.

    ليست `PermissionError`: هذه ليست «رُفض طلبك» بل «هذا الباب غير موجود هنا».
    والتفريق يجعل السجلّ يقول أيّ الأمرين وقع.
    """


def _is_production() -> bool:
    """بيئة إنتاجية؟ تُقرأ من البيئة عند كل نداء لا وقت الاستيراد.

    القراءة وقت الاستيراد تجعل عمليةً بدأت في التطوير تظلّ تقبل الادّعاء بعد
    ترقية البيئة، وذلك أسوأ ما يمكن أن يفعله فحصٌ كهذا.
    """
    return (os.environ.get("AMOS_ENVIRONMENT", "development")).strip().lower() in (
        PRODUCTION_ENVIRONMENTS
    )


def execute_tool_with_declared_role(
    tool_id: str,
    params: dict[str, Any],
    declared_role: str,
    *,
    reason: str = "نداء ما قبل R6 لم يُهاجَر بعد",
) -> dict[str, Any]:
    """**مُهمَل.** نفِّذ أداة بدور يقوله المُستدعي — في التطوير والاختبار وحدهما.

    Args:
        declared_role: دور **مُدّعىً**، بلا جلسة ولا رمز ولا أي إثبات. يُوسَم
            `UNVERIFIED` في كل نتيجة وحدث، ولا يُترجَم إلى مفردة محرِّك السياسة،
            فادّعاء `king` لا يصير `admin`.
        reason: لماذا لم يُهاجَر هذا النداء بعد. يظهر في السياق وفي التحذير،
            فيُعرَف الدَين بمكانه لا بعدده.

    Raises:
        DeprecatedRolePathUnavailableError: البيئة إنتاجية — fail closed.
    """
    if _is_production():
        raise DeprecatedRolePathUnavailableError(
            f"مسار الدور المُدّعى ({DEPRECATED_MARKER}) غير متاح في بيئة "
            f"'{os.environ.get('AMOS_ENVIRONMENT')}'. "
            "استعمل resolve_context ثم execute_tool_for_principal."
        )

    warnings.warn(
        f"{DEPRECATED_MARKER}: execute_tool_with_declared_role"
        f"(role='{declared_role}') — دور مُدّعىً بلا إثبات. السبب المُسجَّل: {reason}. "
        "المسار الكانوني: resolve_context ثم execute_tool_for_principal.",
        DeprecationWarning,
        stacklevel=2,
    )

    from amos_federation.services.tool_registry.sandbox import execute_tool_with_governance

    context = unverified_context(
        f"دور مُدّعىً عبر المُهاجر المُهمَل: '{declared_role}' — {reason}",
        claimed_role=declared_role,
    )
    return execute_tool_with_governance(tool_id, params, principal=context)
