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

# الأدوار في النظام الملكي الفدرالي
ROLE_KING = "king"               # المالك المطلق — صلاحيات غير محدودة
ROLE_ROYAL_GUARD = "royal_guard"  # حرس ملكي — مراقبة وتدقيق
ROLE_ADMIN = "admin"             # مدير — صلاحيات تنفيذية واسعة
ROLE_AGENT = "agent"             # وكيل — صلاحيات محدودة
ROLE_CITIZEN = "citizen"         # مواطن — وصول للقراءة فقط

ALL_ROLES = [ROLE_KING, ROLE_ROYAL_GUARD, ROLE_ADMIN, ROLE_AGENT, ROLE_CITIZEN]


def create_access_token(subject: str, scopes: list[str], tenant_id: str | None = None,
                        role: str = ROLE_CITIZEN) -> str:
    """إنشاء رمز وصول موقع بخوارزمية HS256."""
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "scopes": scopes,
        "exp": expires_at,
        "role": role,
    }
    if tenant_id is not None:
        payload["tenant_id"] = tenant_id
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_king_token() -> str:
    """إنشاء رمز وصول للمالك/الملك بصلاحيات مطلقة."""
    return create_access_token(
        subject="king",
        scopes=["*"],
        tenant_id="federal",
        role=ROLE_KING,
    )


def decode_token(token: str) -> dict[str, Any]:
    """فك رمز وصول والتحقق من توقيعه وصلاحيته."""
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز الوصول غير صالح أو منتهي",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def require_auth(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)] = None,
) -> dict[str, Any]:
    """اعتماد FastAPI يرفض الطلبات التي لا تحمل رمز Bearer صالحاً."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="رمز Bearer مطلوب",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_token(credentials.credentials)


def require_role(*roles: str):
    """اعتماد يتطلب دوراً محدداً أو أكثر. الملك له صلاحيات مطلقة."""
    def checker(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)] = None,
    ) -> dict[str, Any]:
        token_data = require_auth(credentials)
        user_role = token_data.get("role", ROLE_CITIZEN)
        if user_role == ROLE_KING:
            return token_data
        if user_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"الدور المطلوب: {roles} — دورك الحالي: {user_role}",
            )
        return token_data
    return checker


def require_king(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)] = None,
) -> dict[str, Any]:
    """اعتماد يتطلب دور المالك/الملك فقط."""
    token_data = require_auth(credentials)
    if token_data.get("role") != ROLE_KING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذا الإجراء يتطلب صلاحيات المالك/الملك",
        )
    return token_data
