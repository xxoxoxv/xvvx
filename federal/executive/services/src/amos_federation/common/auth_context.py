"""
AMOS-Federation FastAPI Authorization Context Dependency
الهدف: تسليم النقاط الطرفية سياق تخويل مُتحقَّقًا منه بدل إسقاط حمولة الرمز
النطاق: common
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R6)

## المشكلة

المستودع يستعمل `Depends(require_auth)` في 127 موضعًا، لكنه يُسقِط الحمولة:

    _: Annotated[dict, Depends(require_auth)]

فالمصادقة تحدث — الرمز يُفكّ ويُتحقَّق من توقيعه — ثم **يُرمى ناتجها**. أي أن
النقطة الطرفية تعرف أن أحدًا مُصادَقًا عليه اتّصل، ولا تعرف من هو ولا دوره. ومن
احتاج الدور بعدها اضطُرّ إلى أخذه من جسم الطلب، وهذا هو أصل خلل R6.

## الاستعمال

    @app.post("/tasks")
    async def create_task(
        context: Annotated[AuthorizationContext, Depends(require_context)],
    ) -> dict:
        ...  # context.principal_id و context.role موثوقان هنا

ولمن يلزمه دور بعينه:

    Depends(require_permission("execute:tools"))

## حدٌّ يُقال

هذه الوحدة تُتيح النمط ولا تفرضه بأثر رجعي. المواضع الـ127 القائمة ما زالت
تُسقِط الحمولة، وتحويلها عملُ جولة لاحقة — دَينٌ مُسجَّل في وثيقة R6، ولا يُزعم
أنه أُنجِز. والذي يُمنَع اليوم فعلًا هو ما هو أخطر: لا مسار تنفيذ أداة يقبل دورًا
من المُستدعي، وهذا مفروضٌ ومحروسٌ ساكنًا لا موصوفٌ فقط.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastapi import Depends, HTTPException, status

# noqa مع سبب: `require_auth` تُستعمل وقت التشغيل داخل `Depends()`، فنقلها إلى
# كتلة الفحص النوعي يكسر حلّ التبعيات عند FastAPI.
from amos_federation.common.auth import require_auth  # noqa: TCH001
from amos_federation.common.principal import (
    AuthorizationContext,
    Principal,
    PrincipalUnverifiedError,
    SessionInvalidError,
)

if TYPE_CHECKING:
    from collections.abc import Callable


def require_context(
    payload: Annotated[dict[str, Any], Depends(require_auth)],
) -> AuthorizationContext:
    """اشتقّ سياق تخويل من رمز مُتحقَّق من توقيعه.

    `require_auth` تكفّلت بالتوقيع والانتهاء ورفعت 401 عند فشلهما. وهذه تُحوِّل
    حمولتها إلى سياق كانوني بدل إسقاطها.

    Raises:
        HTTPException: 401 إن كانت الحمولة بلا هوية صالحة.
    """
    try:
        principal = Principal.from_token_claims(payload)
        principal.assert_trusted()
    except (SessionInvalidError, PrincipalUnverifiedError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"هوية غير صالحة في الرمز: {exc}",
        ) from exc
    return AuthorizationContext.from_principal(principal)


def require_permission(permission: str) -> Callable[..., AuthorizationContext]:
    """تبعية تلزم صلاحية بعينها — والرفض 403 لا 200 مع جسم خطأ."""

    def _dependency(
        context: Annotated[AuthorizationContext, Depends(require_context)],
    ) -> AuthorizationContext:
        if not context.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"الصلاحية '{permission}' غير ممنوحة لهذا المبدأ",
            )
        return context

    return _dependency
