"""
AMOS-Federation Authentication
الهدف: إصدار والتحقق من رموز JWT لحماية واجهات الخدمات
النطاق: كل واجهات FastAPI المحمية
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from amos_federation.common.config import settings

_security = HTTPBearer(auto_error=False)


def create_access_token(subject: str, scopes: list[str], tenant_id: str | None = None) -> str:
    """إنشاء رمز وصول موقع بخوارزمية HS256."""
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "scopes": scopes, "exp": expires_at}
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """فك رمز وصول والتحقق من توقيعه وصلاحيته."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز الوصول غير صالح أو منتهٍ",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)] = None,
) -> dict[str, Any]:
    """اعتماد FastAPI يرفض الطلبات التي لا تحمل رمز Bearer صالحًا.

    يبقى التحقق مفعّلًا افتراضيًا حتى في التطوير. يمكن للخدمة المحلية اختيار اعتماد
    بديل صراحةً عند ``environment == development`` و``debug == true``، ولا يحدث
    هذا التعطيل ضمنيًا في أي بيئة أخرى.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز Bearer مطلوب",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)
