"""
AMOS-Federation State Registry — Domain Authorization Boundary
الهدف: ربط عمليات السجل بمفردة الصلاحيات القائمة، لا اختراع مفردة ثالثة
النطاق: services/state_registry
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R7-A)

## الدرس المحمول من R6

كان في المستودع مفردتا أدوار متباعدتان (`auth.py` و`security.py`)، فظهر خلل
حقيقي: `king` لا يساوي `admin` حرفيًّا فكانت أعلى سلطة تُحجَب عن الأدوات
الخطيرة. والدَّين لم يُسدَّد بعد. فلا نضيف اليوم مفردة صلاحيات ثالثة
(`registry:write` وأمثالها) تحتاج تسويةً غدًا مع اثنتين.

الصلاحيات المستعملة هنا **هي نفسها المزروعة في `security_roles`** عبر
`DEFAULT_ROLES`، ولا صلاحية واحدة مُختَرعة:

| العملية               | المطلوب (أيٌّ منها)             | من يملكه فعلًا        |
|-----------------------|---------------------------------|------------------------|
| قراءة السجل           | `read:all`                      | official · royal · king |
| تأسيس/حلّ مؤسسة        | `manage:all`                    | royal · king            |
| إنشاء إدارة            | `manage:all`                    | royal · king            |
| تقليد/عزل مسؤول        | `manage:agents` · `manage:all`  | official · royal · king |

و`king` يملك `*` فيمرّ في كل واحدة عبر `has_permission` نفسها — لا استثناء
مكتوبًا باسمه في هذه الوحدة. **التاج أعلى سلطة بصلاحياته لا بتفريعٍ عليه**، وهذا
مقصود: أيُّ `if role == "king"` هنا كان سيصير مسارًا ثانيًا للثقة، وهو ما أُزيل
في R6.1.

## المستأجر

كل عملية تمرّ على `assert_tenant` قبل الكتابة وبعد القراءة. والمستأجر يُؤخذ من
السياق لا من جسم الطلب، والنظام ما زال مُصنَّفًا `SINGLE_TENANT`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from amos_federation.common.principal import assert_tenant

if TYPE_CHECKING:
    from amos_federation.common.principal import AuthorizationContext

# === الصلاحيات المطلوبة — من `DEFAULT_ROLES` القائمة حصرًا ===

PERMISSIONS_REGISTRY_READ: tuple[str, ...] = ("read:all",)
PERMISSIONS_INSTITUTION_WRITE: tuple[str, ...] = ("manage:all",)
PERMISSIONS_DEPARTMENT_WRITE: tuple[str, ...] = ("manage:all",)
PERMISSIONS_OFFICIAL_WRITE: tuple[str, ...] = ("manage:agents", "manage:all")

#: كل ما تفحصه هذه الوحدة — يُستعمل في اختبار ساكن يمنع تسرّب مفردة جديدة.
DOMAIN_PERMISSIONS: tuple[str, ...] = tuple(
    sorted(
        {
            *PERMISSIONS_REGISTRY_READ,
            *PERMISSIONS_INSTITUTION_WRITE,
            *PERMISSIONS_DEPARTMENT_WRITE,
            *PERMISSIONS_OFFICIAL_WRITE,
        }
    )
)


class RegistryAuthorizationError(PermissionError):  # noqa: N818 — رفض تخويل، لا عطل
    """رُفضت عملية سجل لنقص صلاحية — رفضٌ صريح لا قيمة فارغة."""

    def __init__(self, action: str, required: tuple[str, ...], context: AuthorizationContext):
        self.action = action
        self.required = required
        self.principal_id = context.principal_id
        self.role = context.role
        super().__init__(
            f"العملية '{action}' تلزمها إحدى الصلاحيات {list(required)} — "
            f"والمبدأ '{context.principal_id}' بدور '{context.role}' لا يملك واحدة منها"
        )


def require_domain_permission(
    context: AuthorizationContext,
    action: str,
    required: tuple[str, ...],
) -> None:
    """افرض حدّ التخويل على عملية سجل واحدة — fail closed.

    الترتيب مقصود: `assert_authorizable` أولًا فتُرفَض الجلسة المنتهية وغير
    المُتحقَّق منها قبل أن يُسأل عن صلاحية إطلاقًا. وسؤال الصلاحية على سياق ميّت
    يُجيب «لا» أصلًا (`has_permission` تسأل `is_trusted`)، لكن الرسالة تفرق:
    «جلستك انتهت» ليست «لا تملك الصلاحية».

    Raises:
        SessionInvalidError: جلسة السياق منتهية.
        PrincipalUnverifiedError: سياق غير مُتحقَّق منه.
        RegistryAuthorizationError: مُتحقَّق منه ولا يملك الصلاحية.
    """
    context.assert_authorizable()
    if not any(context.has_permission(permission) for permission in required):
        raise RegistryAuthorizationError(action, required, context)


def require_tenant(context: AuthorizationContext, resource_tenant: str | None) -> None:
    """افرض حدّ المستأجر على مورد سجل — نفس دالّة R6.1، لا فحص موازٍ."""
    assert_tenant(context, resource_tenant)


__all__ = [
    "DOMAIN_PERMISSIONS",
    "PERMISSIONS_DEPARTMENT_WRITE",
    "PERMISSIONS_INSTITUTION_WRITE",
    "PERMISSIONS_OFFICIAL_WRITE",
    "PERMISSIONS_REGISTRY_READ",
    "RegistryAuthorizationError",
    "require_domain_permission",
    "require_tenant",
]
