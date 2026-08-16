"""
AMOS-Federation Principal & Authorization Context
الهدف: هوية المُستدعي المُتحقَّق منها، ومنها يُشتقّ الدور — لا من الطلب
النطاق: كل مسار تخويل تنفيذي
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R6)

## المشكلة التي تُصلحها هذه الوحدة

قبل R6 كان `actor_role` معاملًا عاديًّا يُمرَّر إلى طبقة التخويل:

    execute_tool_with_governance(tool_id, params, role="admin")

فمن يستدعي يقول «أنا admin» وتُصدَّق كلمته. لا نظام مصادقة كان يشهد لها.

R6 تنقل الدور إلى **مصدر موثوق**: سجلّ الجلسات المُخزَّن (`security_sessions`)
وجدول الأدوار (`security_roles`)، أو مطالبات رمز JWT مُوقَّع. وما لم يثبت مصدر،
فالمبدأ غير مُتحقَّق منه — ويُقال ذلك ولا يُموَّه.

## لم يُبنَ نظام مصادقة جديد

الموجود قابل للاستخدام، فاستُخدم:

- `common/auth.py` — إصدار JWT وفكّه بـHS256، وسرّ التوقيع مرفوض إن قصر عن 32
  محرفًا. توقيعٌ حقيقي، فمطالبات الرمز لا تُفبرَك بلا السرّ.
- `services/governance/security.py` — `security_sessions` (جلسات مُخزَّنة برمز
  وانتهاء) و`security_roles` (أدوار وصلاحيات على الخادم).

ما أضافته R6 هو **الوصلة** بينهما وبين طبقة التخويل، وحدٌّ صريح لما لا يثبت.

## درجات التحقّق — أربع، مُرتَّبة، ولا يُرفَع منها شيء بلا دليل

| الدرجة | المصدر | القوّة |
| --- | --- | --- |
| `SESSION_VERIFIED` | سجلّ `security_sessions` + `security_roles` | الأقوى: هوية دائمة، انتهاء مفحوص، صلاحيات من الخادم |
| `TOKEN_VERIFIED` | مطالبات JWT بعد التحقّق من التوقيع | قوّي التوقيع، لكن لا إلغاء من جانب الخادم |
| `SYSTEM_INTERNAL` | نداء داخلي في العملية نفسها | ليس مستخدمًا نهائيًّا؛ يلزمه سبب مُسمّى، ولا يُبنى من طلب شبكي |
| `UNVERIFIED` | لا شيء — أو دور مُدّعىً من المُستدعي | **لا يُخوَّل في الإنتاج** |

`UNVERIFIED` ليست درجة أدنى يُتسامح معها بصمت: هي إعلان أن الهوية لم تثبت.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from amos_federation.common.config import PRODUCTION_ENVIRONMENTS


class PrincipalVerification(StrEnum):
    """درجة إثبات هوية المُستدعي. تُقرأ ولا تُستنتج."""

    SESSION_VERIFIED = "SESSION_VERIFIED"
    TOKEN_VERIFIED = "TOKEN_VERIFIED"
    SYSTEM_INTERNAL = "SYSTEM_INTERNAL"
    UNVERIFIED = "UNVERIFIED"


class PrincipalKind(StrEnum):
    """نوع المُستدعي — يفصل المستخدم النهائي عن النداء الداخلي."""

    USER = "USER"
    SERVICE = "SERVICE"
    SYSTEM = "SYSTEM"
    ANONYMOUS = "ANONYMOUS"


#: الدرجات التي يجوز التخويل عليها. `UNVERIFIED` ليست منها بحال.
TRUSTED_VERIFICATIONS: frozenset[str] = frozenset(
    {
        PrincipalVerification.SESSION_VERIFIED.value,
        PrincipalVerification.TOKEN_VERIFIED.value,
        PrincipalVerification.SYSTEM_INTERNAL.value,
    }
)

#: أسماء حقول ممنوعة داخل سياق التخويل — السياق يُنقل ويُسجَّل، فلا سرّ فيه.
FORBIDDEN_CONTEXT_KEYS: tuple[str, ...] = (
    "PASSWORD",
    "SECRET",
    "TOKEN",
    "API_KEY",
    "APIKEY",
    "PRIVATE_KEY",
    "CREDENTIAL",
    "DATABASE_URL",
    "AUTHORIZATION",
    "SESSION_TOKEN",
    "JWT",
    "BEARER",
)

#: مفردتا الأدوار القائمتان في المستودع — R6 لا تُنشئ ثالثة، بل تُظهر التباعُد.
#:
#: `common/auth.py`            : king · royal_guard · admin · agent · citizen
#: `governance/security.py`    : public · citizen · agent · official · royal · king
#: `governance/policy_engine.py`: يفحص `role != "admin"` حرفيًّا للأدوات الخطيرة
#:
#: وهنا ظهر خللٌ حقيقي كشفته R6: قبلها كان المُستدعي يقول `role="admin"` فيمرّ.
#: وحين صار الدور يُشتقّ من سجلّ الجلسة صار `king` هو ما يصل إلى محرِّك السياسة —
#: و`king` ليس `admin` حرفيًّا، فيُرفَض. أي أن أعلى سلطة كانت ستُحجَب عن الأدوات
#: الخطيرة.
#:
#: الحلّ **لا** يُوحِّد الدور فيُفقِد الهوية اسمها، ولا يُعدِّل قواعد محرِّك
#: السياسة (ذلك توسيع صلاحية خارج نطاق R6). بل يُفصَل حقلان:
#:
#: - `Principal.role` / `AuthorizationContext.role` — الدور **الحقيقي** كما في
#:   سجلّ الجلسة. `king` يبقى `king`.
#: - `policy_role(role)` — ترجمة ذلك الدور إلى مفردة محرِّك السياسة، عند نقطة
#:   نداء المحرِّك وحدها.
#:
#: والترجمة تتبع مستويات `DEFAULT_ROLES` القائمة (public 0 · citizen 1 · agent 2
#: · official 3 · royal 4 · king 5) ولا تخترع ترتيبًا: ما كان في طبقة `official`
#: أو أعلى يُترجَم `admin`. وهو **دَين مُسجَّل** في وثيقة R6: المفردتان يجب أن
#: تُوحَّدا في جولة لاحقة، والترجمة جسر مؤقّت مُعلَن لا حلّ نهائي.
POLICY_ROLE_MAP: dict[str, str] = {
    "king": "admin",
    "royal": "admin",
    "royal_guard": "admin",
    "official": "admin",
    "admin": "admin",
    "agent": "agent",
    "citizen": "citizen",
    "public": "citizen",
}


def canonical_role(role: str) -> str:
    """طبِّع اسم الدور بلا تغيير هويته — تنظيف نصّي فقط.

    `king` يبقى `king` و`citizen` يبقى `citizen`. لا ترقية ولا خفض هنا.
    """
    return (role or "").strip().lower()


def policy_role(role: str) -> str:
    """ترجِم الدور إلى مفردة محرِّك السياسة — عند نداء المحرِّك وحده.

    الدور المجهول يُردّ كما هو لا يُترجَم إلى `admin`: المجهول يُرفَض ولا يُرقّى.
    """
    normalized = canonical_role(role)
    return POLICY_ROLE_MAP.get(normalized, normalized)


class PrincipalUnverifiedError(PermissionError):  # noqa: N818 — رفض هوية، لا عطل
    """المبدأ لم تثبت هويته، والفعل يلزمه إثبات.

    ترفع هذه عند محاولة التخويل على `UNVERIFIED`. وهي رفض متعمَّد: البديل هو
    قبول ادّعاء المُستدعي، وذلك هو ما جاءت R6 لإزالته.
    """


class SessionInvalidError(PermissionError):  # noqa: N818 — جلسة باطلة، لا عطل
    """رمز الجلسة غير موجود أو منتهي أو دوره غير معروف."""


def _is_production() -> bool:
    """بيئة إنتاجية؟ يُقرأ من البيئة عند كل نداء لا وقت الاستيراد."""
    return (os.environ.get("AMOS_ENVIRONMENT", "development")).strip().lower() in (
        PRODUCTION_ENVIRONMENTS
    )


@dataclass(frozen=True)
class Principal:
    """هوية المُستدعي ودرجة إثباتها.

    الحقول `role` و`permissions` **لا تُملأ من الطلب** في أي من دوالّ البناء
    الموثوقة أدناه. `unverified()` وحدها تقبل دورًا مُدّعىً، وهي تُعلِن ذلك في
    `verification` وتُوجِب سببًا.
    """

    principal_id: str
    verification: PrincipalVerification
    kind: PrincipalKind
    role: str = ""
    permissions: tuple[str, ...] = ()
    session_id: str | None = None
    tenant_id: str | None = None
    expires_at: datetime | None = None
    #: سبب عدم التحقّق أو سبب النداء الداخلي — نصٌّ مُلزَم في هاتين الحالتين.
    reason: str = ""

    def __post_init__(self) -> None:
        if self.verification is PrincipalVerification.UNVERIFIED and not self.reason:
            raise ValueError("المبدأ غير المُتحقَّق منه يلزمه سبب مُسمّى")
        if self.verification is PrincipalVerification.SYSTEM_INTERNAL and not self.reason:
            raise ValueError("النداء الداخلي يلزمه سبب مُسمّى")

    @property
    def is_trusted(self) -> bool:
        """هل يجوز التخويل على هذا المبدأ؟"""
        return self.verification.value in TRUSTED_VERIFICATIONS

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        expiry = self.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        return expiry <= datetime.now(UTC)

    def assert_trusted(self) -> None:
        """ارفع `PrincipalUnverifiedError` إن لم تثبت الهوية — fail closed."""
        if self.is_expired:
            raise SessionInvalidError(
                f"هوية المبدأ '{self.principal_id}' منتهية — لا تخويل على جلسة ميّتة"
            )
        if not self.is_trusted:
            raise PrincipalUnverifiedError(
                f"مبدأ غير مُتحقَّق منه ({self.verification.value}): {self.reason}"
            )

    # ── دوالّ البناء ─────────────────────────────────────────────────────

    @classmethod
    def from_token_claims(cls, claims: dict[str, Any]) -> Principal:
        """ابنِ مبدأً من مطالبات JWT **بعد** التحقّق من توقيعها.

        المُستدعي مسؤول عن أن تكون `claims` ناتج `auth.decode_token` — أي أن
        التوقيع فُحص. والدور يُقرأ من المطالبة `role` لا من جسم الطلب.

        الدرجة `TOKEN_VERIFIED` لا `SESSION_VERIFIED`: الرمز موقَّع لكن لا سجلّ
        على الخادم يُمكِّن من إلغائه قبل انتهائه. حدٌّ يُقال.
        """
        subject = str(claims.get("sub") or "").strip()
        if not subject:
            raise SessionInvalidError("رمز بلا `sub` — لا هوية فيه")
        expires_at = claims.get("exp")
        parsed_expiry: datetime | None = None
        if isinstance(expires_at, int | float):
            parsed_expiry = datetime.fromtimestamp(float(expires_at), tz=UTC)
        elif isinstance(expires_at, datetime):
            parsed_expiry = expires_at
        scopes = claims.get("scopes")
        return cls(
            principal_id=subject,
            verification=PrincipalVerification.TOKEN_VERIFIED,
            kind=PrincipalKind.USER,
            role=canonical_role(str(claims.get("role") or "")),
            permissions=tuple(str(s) for s in scopes) if isinstance(scopes, list | tuple) else (),
            session_id=str(claims["sid"]) if claims.get("sid") else None,
            tenant_id=str(claims["tenant_id"]) if claims.get("tenant_id") else None,
            expires_at=parsed_expiry,
        )

    @classmethod
    def from_session_record(
        cls,
        *,
        session_id: str,
        username: str,
        role_id: str,
        permissions: tuple[str, ...],
        expires_at: datetime | None,
        tenant_id: str | None = None,
    ) -> Principal:
        """ابنِ مبدأً من سجلّ جلسة مُخزَّن — أقوى الدرجات.

        الدور والصلاحيات من الخادم: `security_sessions` يربط الجلسة بـ`role_id`،
        و`security_roles` يُملي صلاحياته. فلا يُملي المُستدعي شيئًا منهما.
        """
        return cls(
            principal_id=username,
            verification=PrincipalVerification.SESSION_VERIFIED,
            kind=PrincipalKind.USER,
            role=canonical_role(role_id),
            permissions=permissions,
            session_id=session_id,
            tenant_id=tenant_id,
            expires_at=expires_at,
        )

    @classmethod
    def system(cls, component: str, reason: str) -> Principal:
        """مبدأ داخلي لنداء في العملية نفسها — لا يُبنى من طلب شبكي.

        هذا ليس بابًا خلفيًّا للمستخدمين: `kind=SYSTEM` مُعلَن في كل نتيجة،
        و`reason` مُلزَم، ويحرس اختبار ساكن ألّا يُبنى من بيانات طلب.
        """
        if not component.strip():
            raise ValueError("النداء الداخلي يلزمه اسم مُكوِّن")
        return cls(
            principal_id=f"system:{component.strip()}",
            verification=PrincipalVerification.SYSTEM_INTERNAL,
            kind=PrincipalKind.SYSTEM,
            role="",
            permissions=(),
            reason=reason,
        )

    @classmethod
    def unverified(cls, reason: str, *, claimed_role: str = "") -> Principal:
        """مبدأ لم تثبت هويته — والدور المُدّعى يُحمَل موسومًا لا مُصدَّقًا.

        `claimed_role` يُحفظ لأن مسارات ما قبل R6 ما زالت تُمرِّره، لكن
        `verification` تقول `UNVERIFIED`، و`assert_trusted()` ترفضه. فالدور
        هنا **بيانات**، لا سلطة.
        """
        return cls(
            principal_id="anonymous",
            verification=PrincipalVerification.UNVERIFIED,
            kind=PrincipalKind.ANONYMOUS,
            role=canonical_role(claimed_role),
            permissions=(),
            reason=reason or "لا مصدر هوية في الطلب",
        )


@dataclass(frozen=True)
class AuthorizationContext:
    """سياق التخويل الكانوني — يُنقل بين الطبقات ويُسجَّل، وبلا أي سرّ.

    وهو **ليس** بديلًا عن الهوية الدائمة: `security_sessions` و`agents` هما
    السجلّان الدائمان، وهذا السياق أثرٌ لطلب واحد مُشتقٌّ منهما.
    """

    principal_id: str
    verification: PrincipalVerification
    principal_kind: PrincipalKind
    role: str = ""
    permissions: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    session_id: str | None = None
    tenant_id: str | None = None
    correlation_id: str = field(default="")
    reason: str = ""

    def __post_init__(self) -> None:
        if not self.correlation_id:
            object.__setattr__(self, "correlation_id", f"corr-{uuid.uuid4().hex[:12]}")
        self.assert_no_secrets()

    @property
    def is_trusted(self) -> bool:
        return self.verification.value in TRUSTED_VERIFICATIONS

    def assert_no_secrets(self) -> None:
        """ارفض قيمة تحمل اسم سرّ — السياق يُسجَّل في التدقيق."""
        offenders = [
            name
            for name in (*self.permissions, *self.capabilities)
            if any(pattern in name.upper() for pattern in FORBIDDEN_CONTEXT_KEYS)
        ]
        if offenders:
            raise ValueError("أسماء تشبه الأسرار في سياق التخويل: " + ", ".join(sorted(offenders)))

    def assert_authorizable(self) -> None:
        """ارفع خطأً إن لم يجز التخويل على هذا السياق — fail closed."""
        if not self.is_trusted:
            raise PrincipalUnverifiedError(
                f"سياق تخويل غير مُتحقَّق منه ({self.verification.value}): {self.reason}"
            )

    def has_permission(self, permission: str) -> bool:
        """صلاحية مُخوَّلة؟ `*` تعني الكل، وغياب الصلاحيات يعني لا."""
        if not self.is_trusted:
            return False
        return "*" in self.permissions or permission in self.permissions

    @classmethod
    def from_principal(
        cls,
        principal: Principal,
        *,
        capabilities: tuple[str, ...] = (),
        correlation_id: str = "",
    ) -> AuthorizationContext:
        """اشتقّ السياق من مبدأ — الدور من المبدأ لا من الطلب."""
        return cls(
            principal_id=principal.principal_id,
            verification=principal.verification,
            principal_kind=principal.kind,
            role=principal.role,
            permissions=principal.permissions,
            capabilities=capabilities,
            session_id=principal.session_id,
            tenant_id=principal.tenant_id,
            correlation_id=correlation_id,
            reason=principal.reason,
        )

    def as_dict(self) -> dict[str, Any]:
        """تمثيل للتدقيق والنشر — بلا أسرار."""
        return {
            "principal_id": self.principal_id,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "role": self.role,
            "permissions": list(self.permissions),
            "capabilities": list(self.capabilities),
            "correlation_id": self.correlation_id,
            "principal_verification": self.verification.value,
            "principal_kind": self.principal_kind.value,
        }


def unverified_context(reason: str, *, claimed_role: str = "") -> AuthorizationContext:
    """سياق لمُستدعٍ لم تثبت هويته — يُرفَض في الإنتاج.

    الدور المُدّعى يُنقل موسومًا `UNVERIFIED`. وفي بيئة إنتاجية يُرفَض البناء
    أصلًا: البديل أن يمرّ ادّعاء الدور إلى طبقة التخويل، وذلك هو الخلل نفسه.
    """
    if _is_production():
        raise PrincipalUnverifiedError(
            "مبدأ غير مُتحقَّق منه مرفوض في بيئة إنتاجية — "
            f"يلزمه جلسة أو رمز موقَّع (السبب المُعلَن: {reason})"
        )
    return AuthorizationContext.from_principal(
        Principal.unverified(reason, claimed_role=claimed_role)
    )


#: المستأجر الضمني حين لا يُسمّى — قيمة واحدة معلومة، لا «كل المستأجرين».
DEFAULT_TENANT = "default"

#: مستأجر التاج: يعبر حدود المستأجرين. ويلزمه سياق موثوق دائمًا.
FEDERAL_TENANT = "federal"


def tenant_matches(context: AuthorizationContext, resource_tenant: str | None) -> bool:
    """هل يملك السياق حق الوصول إلى مستأجر المورد؟

    القاعدة: المستأجر غير المُسمّى **لا** يعني «كل المستأجرين»، بل يعني
    `default` تحديدًا — مستأجرًا واحدًا معلومًا. فسياق بلا مستأجر يصل إلى موارد
    `default` وحدها، ويُرفَض على مورد مستأجر آخر.

    حدٌّ يُقال ولا يُخفى: جدول `security_sessions` لا يحمل عمود مستأجر (فيه
    `username` و`role_id` و`expires_at` ولا شيء عن المستأجر). فالمبدأ المُتحقَّق
    من جلسة يخرج بمستأجر `None`، أي `default`. والعزل الحقيقي بين مستأجرين
    متعدِّدين على مستوى الجلسة يحتاج تعديل مخطَّط — دَينٌ مُسجَّل في وثيقة R6، ولم
    يُنفَّذ هنا ولم يُزعم تنفيذه. والعزل يعمل فعلًا اليوم للسياقات التي **تُسمّي**
    مستأجرها (رمز JWT فيه مطالبة `tenant_id`، أو نداء داخلي مُسمّى).
    """
    if not context.is_trusted:
        return False
    holder = context.tenant_id or DEFAULT_TENANT
    if holder == FEDERAL_TENANT:
        return True
    return holder == (resource_tenant or DEFAULT_TENANT)
