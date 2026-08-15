"""
اختبارات المصادقة
الهدف: التحقق من إصدار وفك ورفض رموز JWT
النطاق: common/auth.py
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException

from amos_federation.common.auth import create_access_token, decode_token
from amos_federation.common.config import settings


def test_issue_and_decode_access_token() -> None:
    """الرمز الصحيح يحفظ هوية المستخدم والصلاحيات والمستأجر."""
    token = create_access_token("agent-001", ["tasks:write"], "finance")
    payload = decode_token(token)
    assert payload["sub"] == "agent-001"
    assert payload["scopes"] == ["tasks:write"]
    assert payload["tenant_id"] == "finance"


def test_invalid_token_is_rejected() -> None:
    """الرمز التالف يعيد رفض 401."""
    with pytest.raises(HTTPException, match="غير صالح") as error:
        decode_token("not-a-jwt")
    assert error.value.status_code == 401


def test_expired_token_is_rejected() -> None:
    """الرمز المنتهي يعيد رفض 401."""
    token = jwt.encode(
        {"sub": "agent-001", "exp": datetime.now(UTC) - timedelta(seconds=1)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(HTTPException, match="منته") as error:
        decode_token(token)
    assert error.value.status_code == 401
