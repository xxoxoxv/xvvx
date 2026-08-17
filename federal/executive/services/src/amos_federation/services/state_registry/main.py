"""
AMOS-Federation State Registry — HTTP Interface
الهدف: نقاط طرفية للسجل الفدرالي تأخذ سياق التخويل من الرمز لا من جسم الطلب
النطاق: services/state_registry
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R7-A)

## النمط المتَّبع

كل نقطة هنا تستعمل `Depends(require_context)` — أي أن الهوية والدور والمستأجر
تُشتقّ من الرمز المُتحقَّق من توقيعه. **ولا نموذج طلب واحد في هذا الملف يحمل
حقل `role` أو `permissions` أو `tenant_id`**، وذلك محروسٌ باختبار ساكن: تلك
الحقول لو قُبلت من العميل لعادت ثغرة R6 من باب النطاق بعد إغلاقها في النواة.

## الأخطاء

أخطاء النطاق تُترجَم إلى رموز HTTP صادقة: نقص الصلاحية 403، عبور المستأجر 403،
الجلسة المنتهية 401، الكيان المفقود 404، تعارض الرمز أو الرئاسة 409، ومخالفة
المفردة 400. ولا واحدة منها تُرجَع كـ200 مع جسم خطأ.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from amos_federation.common.auth_context import require_context
from amos_federation.common.principal import (
    AuthorizationContext,
    PrincipalUnverifiedError,
    SessionInvalidError,
    TenantIsolationError,
)
from amos_federation.common.registry import SERVICES
from amos_federation.common.service import create_service_app
from amos_federation.services.state_registry.authorization import RegistryAuthorizationError
from amos_federation.services.state_registry.service import (
    DepartmentHeadConflictError,
    DepartmentNotFoundError,
    DuplicateCodeError,
    InstitutionInactiveError,
    InstitutionNotEmptyError,
    InstitutionNotFoundError,
    OfficialNotFoundError,
    RegistryError,
    get_state_registry,
)

router = APIRouter(prefix="/registry", tags=["state-registry"])

Context = Annotated[AuthorizationContext, Depends(require_context)]


# === نماذج الطلب — بلا دور ولا صلاحيات ولا مستأجر ===


class InstitutionRequest(BaseModel):
    """تأسيس مؤسسة."""

    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=200)
    kind: str
    branch: str
    mandate: str = ""
    parent_code: str | None = None


class InstitutionStatusRequest(BaseModel):
    """تغيير حالة مؤسسة."""

    status: str
    reason: str = Field(min_length=3, max_length=500)


class DepartmentRequest(BaseModel):
    """إنشاء إدارة."""

    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=2, max_length=200)
    mandate: str = ""


class AppointmentRequest(BaseModel):
    """تقليد وكيل منصبًا."""

    agent_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=2, max_length=200)
    department_code: str | None = None
    is_head: bool = False


class RevocationRequest(BaseModel):
    """عزل مسؤول."""

    reason: str = Field(min_length=3, max_length=500)


def _http(exc: Exception) -> HTTPException:
    """ترجمة خطأ نطاق إلى رمز HTTP صادق."""
    if isinstance(exc, SessionInvalidError):
        return HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    if isinstance(
        exc, RegistryAuthorizationError | PrincipalUnverifiedError | TenantIsolationError
    ):
        return HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, InstitutionNotFoundError | DepartmentNotFoundError | OfficialNotFoundError):
        return HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(
        exc,
        DuplicateCodeError
        | DepartmentHeadConflictError
        | InstitutionNotEmptyError
        | InstitutionInactiveError,
    ):
        return HTTPException(status.HTTP_409_CONFLICT, detail=str(exc))
    return HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


_DOMAIN_ERRORS = (
    RegistryError,
    RegistryAuthorizationError,
    SessionInvalidError,
    PrincipalUnverifiedError,
    TenantIsolationError,
)


# === المؤسسات ===


@router.post("/institutions", status_code=status.HTTP_201_CREATED)
async def register_institution(payload: InstitutionRequest, context: Context) -> dict:
    """أسِّس مؤسسة."""
    try:
        return get_state_registry().register_institution(
            context=context,
            code=payload.code,
            name=payload.name,
            kind=payload.kind,
            branch=payload.branch,
            mandate=payload.mandate,
            parent_code=payload.parent_code,
        )
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc


@router.get("/institutions")
async def list_institutions(
    context: Context,
    kind: str | None = None,
    branch: str | None = None,
    institution_status: str | None = None,
    limit: int = 100,
) -> dict:
    """اسرد المؤسسات."""
    try:
        items = get_state_registry().list_institutions(
            context=context,
            kind=kind,
            branch=branch,
            status=institution_status,
            limit=limit,
        )
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc
    return {"count": len(items), "institutions": items}


@router.get("/institutions/{code}")
async def get_institution(code: str, context: Context) -> dict:
    """اقرأ مؤسسة."""
    try:
        return get_state_registry().get_institution(code, context=context)
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc


@router.get("/institutions/{code}/chart")
async def institution_chart(code: str, context: Context) -> dict:
    """مُخطَّط المؤسسة بإداراتها ومسؤوليها."""
    try:
        return get_state_registry().institution_chart(code, context=context)
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc


@router.patch("/institutions/{code}/status")
async def set_institution_status(
    code: str, payload: InstitutionStatusRequest, context: Context
) -> dict:
    """غيّر حالة مؤسسة."""
    try:
        return get_state_registry().set_institution_status(
            context=context, code=code, status=payload.status, reason=payload.reason
        )
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc


# === الإدارات ===


@router.post("/institutions/{code}/departments", status_code=status.HTTP_201_CREATED)
async def create_department(code: str, payload: DepartmentRequest, context: Context) -> dict:
    """أنشئ إدارة تحت مؤسسة."""
    try:
        return get_state_registry().create_department(
            context=context,
            institution_code=code,
            code=payload.code,
            name=payload.name,
            mandate=payload.mandate,
        )
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc


@router.get("/institutions/{code}/departments")
async def list_departments(code: str, context: Context) -> dict:
    """اسرد إدارات مؤسسة."""
    try:
        items = get_state_registry().list_departments(context=context, institution_code=code)
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc
    return {"count": len(items), "departments": items}


# === المسؤولون ===


@router.post("/institutions/{code}/officials", status_code=status.HTTP_201_CREATED)
async def appoint_official(code: str, payload: AppointmentRequest, context: Context) -> dict:
    """قلِّد وكيلًا منصبًا في مؤسسة."""
    try:
        return get_state_registry().appoint_official(
            context=context,
            agent_id=payload.agent_id,
            institution_code=code,
            title=payload.title,
            department_code=payload.department_code,
            is_head=payload.is_head,
        )
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc


@router.get("/officials")
async def list_officials(
    context: Context, institution_code: str | None = None, include_revoked: bool = False
) -> dict:
    """اسرد المسؤولين."""
    try:
        items = get_state_registry().list_officials(
            context=context,
            institution_code=institution_code,
            include_revoked=include_revoked,
        )
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc
    return {"count": len(items), "officials": items}


@router.delete("/officials/{official_id}")
async def revoke_official(official_id: str, payload: RevocationRequest, context: Context) -> dict:
    """اعزل مسؤولًا."""
    try:
        return get_state_registry().revoke_official(
            context=context, official_id=official_id, reason=payload.reason
        )
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc


# === الصحة ===


@router.get("/health/summary")
async def registry_health(context: Context) -> dict:
    """إحصاء السجل من القاعدة."""
    try:
        return get_state_registry().registry_health(context=context)
    except _DOMAIN_ERRORS as exc:
        raise _http(exc) from exc


_definition = SERVICES["state-registry"]

app = create_service_app(
    service_name=_definition["name"],
    port=_definition["port"],
    description=_definition["responsibility"],
    routers=[router],
)

__all__ = ["app", "router"]
