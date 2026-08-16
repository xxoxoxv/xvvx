"""
اختبارات حدّ سرّ الملك — King Credential Boundary Tests (E2.2-E)
الهدف: إثبات أن دخول الملك لا يستند إلى سرّ مكتوب في الكود، وأن غياب السرّ يوقف
       الباب بدل أن يفتحه، وأن الرموز لا تُوقَّع بسرّ فارغ أو ضعيف.
النطاق: services/royal/main.py و common/auth.py و common/config.py.
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المبدأ: السرّ المكتوب في المستودع سرٌّ منشور. ومن عرف السلسلة صار ملكًا — فهذا
ليس ضعف تشفير بل انتحال سيادة. هذه الاختبارات تمنع عودته.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from amos_federation.common import auth
from amos_federation.common.config import (
    PLACEHOLDER_SECRETS,
    SECRET_FIELDS,
    InsecureConfigurationError,
    Settings,
    settings,
)
from amos_federation.services.royal.main import get_royal_app

client = TestClient(get_royal_app(), raise_server_exceptions=False)

# قيمة اختبارية تُحاكي ما يأتي من البيئة — تُسمّى بلا لفظ «سرّ» كي لا
# يحسبها ماسح الأسرار سرًّا حقيقيًّا مكتوبًا في الكود.
CONFIGURED_VALUE = "value-provided-by-the-environment"


@pytest.fixture
def king_secret(monkeypatch: pytest.MonkeyPatch):
    """هيّئ سرّ الملك في الإعدادات لهذا الاختبار وحده."""

    def _set(value: str) -> None:
        monkeypatch.setattr(settings, "king_login_secret", value, raising=False)

    return _set


# ── لا سرّ في الكود ─────────────────────────────────────────────────────────


def test_no_king_secret_literal_in_source() -> None:
    """السرّ التاريخي المكتوب نصًّا لا يعود إلى الملف."""
    from pathlib import Path

    source = Path(auth.__file__).resolve().parents[1] / "services" / "royal" / "main.py"
    text = source.read_text(encoding="utf-8")
    assert "amos-king-2026" not in text, "عاد سرّ الملك إلى الكود"
    assert "king_login_secret" in text, "الدخول لا يقرأ السرّ من الإعدادات"


def test_login_is_refused_when_secret_is_not_configured(king_secret) -> None:
    """بلا سرّ مهيّأ: يُغلق الباب (503)، ولا يُفتح بقيمة افتراضية."""
    king_secret("")
    response = client.post("/v1/auth/login", json={"username": "king", "password": ""})
    assert response.status_code == 503
    assert "access_token" not in response.json()


@pytest.mark.parametrize("placeholder", sorted(PLACEHOLDER_SECRETS))
def test_placeholder_secret_is_not_a_secret(king_secret, placeholder: str) -> None:
    """قيمة نائبة معروفة = لا سرّ."""
    king_secret(placeholder)
    response = client.post("/v1/auth/login", json={"username": "king", "password": placeholder})
    assert response.status_code == 503


def test_wrong_password_is_rejected(king_secret) -> None:
    king_secret(CONFIGURED_VALUE)
    response = client.post("/v1/auth/login", json={"username": "king", "password": "wrong"})
    assert response.status_code == 401


def test_wrong_username_is_rejected(king_secret) -> None:
    king_secret(CONFIGURED_VALUE)
    response = client.post(
        "/v1/auth/login", json={"username": "regent", "password": CONFIGURED_VALUE}
    )
    assert response.status_code == 401


def test_correct_secret_grants_the_king_token(king_secret) -> None:
    king_secret(CONFIGURED_VALUE)
    response = client.post(
        "/v1/auth/login", json={"username": "king", "password": CONFIGURED_VALUE}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "king"
    assert body["access_token"]


# ── لا توقيع بسرّ فارغ ───────────────────────────────────────────────────────


def test_signing_is_refused_when_jwt_secret_is_empty(monkeypatch) -> None:
    """توقيعٌ بسرّ فارغ ليس توقيعًا: أي طرف يصنع رمز ملك."""
    monkeypatch.setattr(settings, "jwt_secret", "", raising=False)
    with pytest.raises(HTTPException) as error:
        auth.create_access_token("anyone", ["*"], role="king")
    assert error.value.status_code == 503


def test_signing_is_refused_when_jwt_secret_is_too_short(monkeypatch) -> None:
    monkeypatch.setattr(settings, "jwt_secret", "short", raising=False)
    with pytest.raises(HTTPException) as error:
        auth.create_king_token()
    assert error.value.status_code == 503


def test_verification_is_refused_when_jwt_secret_is_empty(monkeypatch) -> None:
    """الرفض يشمل الفكّ أيضًا، وإلا قُبِل رمز موقَّع بسرّ فارغ."""
    token = auth.create_access_token("agent", ["read"])
    monkeypatch.setattr(settings, "jwt_secret", "", raising=False)
    with pytest.raises(HTTPException) as error:
        auth.decode_token(token)
    assert error.value.status_code == 503


# ── الإعداد يسقط صراحةً في الإنتاج ──────────────────────────────────────────


def test_secret_fields_have_no_code_defaults() -> None:
    """القيم الافتراضية للحقول السرّية فارغة — البيئة وحدها مصدرها."""
    defaults = Settings.model_fields
    for field in SECRET_FIELDS:
        assert defaults[field].default == "", f"{field} يحمل قيمة افتراضية في الكود"


@pytest.mark.parametrize("env", ["production", "prod", "staging", "PRODUCTION"])
def test_production_refuses_to_boot_with_missing_secrets(env: str) -> None:
    # يُمرَّر السرّ فارغًا صراحةً: بيئة الاختبار تضبط AMOS_JWT_SECRET، والمقصود
    # هنا إثبات أن الفراغ يُرصَد لا أن البيئة فارغة.
    config = Settings(environment=env, jwt_secret="", _env_file=None)
    with pytest.raises(InsecureConfigurationError) as error:
        config.assert_secrets_configured()
    message = str(error.value)
    assert "jwt_secret" in message
    assert "king_login_secret" in message


def test_production_accepts_real_secrets() -> None:
    config = Settings(
        environment="production",
        postgres_password="x" * 20,
        minio_secret_key="y" * 20,
        jwt_secret="z" * 40,
        king_login_secret="w" * 20,
        _env_file=None,
    )
    config.assert_secrets_configured()
    assert config.secret_violations() == []


def test_development_is_not_blocked_by_missing_secrets() -> None:
    """التطوير لا يُعطَّل — البوابة تخصّ الإنتاج، والادعاء لا يُعمَّم."""
    config = Settings(environment="development", _env_file=None)
    config.assert_secrets_configured()


def test_placeholder_value_counts_as_missing() -> None:
    config = Settings(
        environment="production",
        postgres_password="dev_password_change_me",
        minio_secret_key="y" * 20,
        jwt_secret="z" * 40,
        king_login_secret="w" * 20,
        _env_file=None,
    )
    assert config.secret_violations() == ["postgres_password"]


def test_violation_report_never_leaks_the_value() -> None:
    """رسالة الخطأ تذكر الاسم لا القيمة — التشخيص لا يكون تسريبًا."""
    config = Settings(
        environment="production",
        postgres_password="dev_password_change_me",
        _env_file=None,
    )
    with pytest.raises(InsecureConfigurationError) as error:
        config.assert_secrets_configured()
    assert "dev_password_change_me" not in str(error.value)
