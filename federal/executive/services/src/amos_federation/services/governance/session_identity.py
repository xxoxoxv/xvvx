"""
AMOS-Federation Session Identity Resolution
الهدف: تحويل رمز جلسة مُخزَّن إلى مبدأ مُتحقَّق منه — الدور من الخادم لا من الطلب
النطاق: services/governance
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R6)

هذه الوحدة هي الوصلة بين سجلّ الجلسات القائم (`security_sessions`) وطبقة
التخويل. لم يُبنَ مخزن جلسات جديد: الموجود يحمل الرمز والمستخدم و`role_id`
و`expires_at`، وجدول `security_roles` يحمل الصلاحيات. المفقود كان القراءة منهما
عند التخويل، وهذا ما تُضيفه R6.

**الانتهاء مفحوص هنا.** `RBACSystem.check_permission` كانت تقبل جلسة منتهية لأنها
لا تنظر إلى `expires_at` إطلاقًا — وهو خلل حقيقي أُصلح في R6 هناك، ويُفحَص هنا
أيضًا قبل بناء أي مبدأ.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from amos_federation.common.principal import (
    AuthorizationContext,
    Principal,
    SessionInvalidError,
)

if TYPE_CHECKING:
    from amos_federation.services.governance.security import RBACSystem


def _normalize_expiry(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def resolve_principal(session_token: str, *, rbac: RBACSystem | None = None) -> Principal:
    """حوِّل رمز جلسة إلى مبدأ `SESSION_VERIFIED`، أو ارفع `SessionInvalidError`.

    كل حالة فشل ترفع، ولا واحدة منها تُرجع مبدأً بدرجة أدنى: انحدار الدرجة عند
    الفشل هو بابٌ خلفي، فالفشل يُرفَع.

    Raises:
        SessionInvalidError: رمز فارغ، أو جلسة غير موجودة، أو منتهية، أو دور غير
            معروف في `security_roles`.
    """
    from amos_federation.services.governance.security import (
        RoleModel,
        UserSessionModel,
        get_rbac,
    )

    token = (session_token or "").strip()
    if not token:
        raise SessionInvalidError("رمز جلسة فارغ — لا هوية فيه")

    system = rbac if rbac is not None else get_rbac()
    session = system._Session()  # noqa: SLF001 — نفس الحزمة، ولا واجهة قراءة عامّة بعد
    try:
        record = (
            session.query(UserSessionModel).filter(UserSessionModel.session_token == token).first()
        )
        if record is None:
            raise SessionInvalidError("لا جلسة بهذا الرمز")

        expires_at = _normalize_expiry(record.expires_at)
        if expires_at is not None and expires_at <= datetime.now(UTC):
            raise SessionInvalidError(f"جلسة منتهية منذ {expires_at.isoformat()}")

        role = session.query(RoleModel).filter(RoleModel.role_id == record.role_id).first()
        if role is None:
            # جلسة تحمل دورًا لا وجود له: لا يُفترَض دور أدنى، بل تُرفَض.
            raise SessionInvalidError(f"دور الجلسة '{record.role_id}' غير معروف في سجلّ الأدوار")

        try:
            permissions = tuple(str(p) for p in json.loads(role.permissions or "[]"))
        except (TypeError, ValueError) as exc:
            raise SessionInvalidError(
                f"صلاحيات الدور '{record.role_id}' غير قابلة للقراءة"
            ) from exc

        return Principal.from_session_record(
            session_id=token[:16],
            username=str(record.username),
            role_id=str(record.role_id),
            permissions=permissions,
            expires_at=expires_at,
            # R6.1: المستأجر من عمود الجلسة لا من المُستدعي. وقبل إضافة العمود
            # كان هذا الموضع يُمرّر `None` دائمًا، فتساوت كل الجلسات على `default`.
            tenant_id=(str(record.tenant_id) if record.tenant_id else None),
        )
    finally:
        session.close()


def resolve_context(
    session_token: str,
    *,
    capabilities: tuple[str, ...] = (),
    correlation_id: str = "",
    rbac: RBACSystem | None = None,
) -> AuthorizationContext:
    """سياق تخويل كانوني من رمز جلسة مُخزَّن."""
    principal = resolve_principal(session_token, rbac=rbac)
    return AuthorizationContext.from_principal(
        principal,
        capabilities=capabilities,
        correlation_id=correlation_id,
    )


def context_from_bearer_token(
    bearer_token: str,
    *,
    capabilities: tuple[str, ...] = (),
    correlation_id: str = "",
) -> AuthorizationContext:
    """سياق من رمز JWT موقَّع — يُفكّ ويُتحقَّق من توقيعه أولًا.

    الدرجة `TOKEN_VERIFIED`: التوقيع حقيقي، لكن لا سجلّ خادم يُلغي الرمز قبل
    انتهائه. ومن أراد الأقوى فليستعمل `resolve_context` على جلسة مُخزَّنة.
    """
    from amos_federation.common.auth import decode_token

    claims = decode_token(bearer_token)
    principal = Principal.from_token_claims(claims)
    principal.assert_trusted()
    return AuthorizationContext.from_principal(
        principal,
        capabilities=capabilities,
        correlation_id=correlation_id,
    )
