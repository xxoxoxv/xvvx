"""الهدف: سياسة شبكة صريحة للصندوق الرملي — لا وصول ضمني.

النطاق: services/tool_registry/providers
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17

`DENY` هو الافتراضي. أداة تحتاج الشبكة تُعلن ذلك في مواصفتها، وتُسمّي مضيفيها
إن كانت `ALLOWLIST`. و`ALLOW_ALL` موجودة لأن إخفاءها لا يمنعها: من أرادها
سيمرّر `ALLOWLIST` بمضيف `*` أو يعطّل الفحص. وجودها مُسمّاةً يعني أنها تظهر في
كل نتيجة تنفيذ وفي كل حدث، فتصبح قابلة للمراجعة.

قيد صريح على المدى: هذه الوحدة تحكم ما **يُطلب ويُعلَن ويُفحَص** في طبقة
المزوِّدات. أما الحبس الشبكي الفعلي فمن يملكه هو المزوِّد نفسه (قواعد الشبكة
عند Modal أو E2B) أو المضيف. المزوِّد المحلّي **لا** يملك عزلًا شبكيًّا حقيقيًّا،
وهذا يُعلَن في `enforcement` بقيمة `DECLARED_ONLY` ولا يُزعم غير ذلك.
"""

from __future__ import annotations

from dataclasses import dataclass

#: القيم المسموحة لـ`SandboxSpec.network_policy`.
NETWORK_POLICIES: tuple[str, ...] = ("DENY", "ALLOWLIST", "ALLOW_ALL")

#: كيف تُفرَض السياسة عند كل مزوِّد — لا يُزعم فرضٌ غير موجود.
ENFORCEMENT_BY_PROVIDER: dict[str, str] = {
    "local": "DECLARED_ONLY",
    "modal": "PROVIDER_ENFORCED",
    "e2b": "PROVIDER_ENFORCED",
    "simulation": "NOT_APPLICABLE",
}


class NetworkPolicyViolation(RuntimeError):  # noqa: N818 — خرق سياسة، لا عطل
    """طلب شبكي يخالف سياسة الصندوق المُعلَنة."""


@dataclass(frozen=True)
class NetworkDecision:
    """قرار على مضيف بعينه، بسببه — صالح للسجل."""

    allowed: bool
    policy: str
    enforcement: str
    host: str | None = None
    reason: str | None = None


def normalize_policy(policy: str) -> str:
    """طبّع اسم السياسة وارفض المجهول — لا افتراض صامت إلى `DENY` ولا إلى السماح."""
    value = (policy or "").strip().upper()
    if value not in NETWORK_POLICIES:
        raise NetworkPolicyViolation(
            f"سياسة شبكة غير معروفة: '{policy}' — المسموح: {', '.join(NETWORK_POLICIES)}"
        )
    return value


def enforcement_for(provider: str) -> str:
    """كيف تُفرَض السياسة عند هذا المزوِّد — المجهول يُعلَن مجهولًا."""
    return ENFORCEMENT_BY_PROVIDER.get(provider, "UNKNOWN")


def evaluate(
    policy: str,
    *,
    provider: str,
    host: str | None = None,
    allowed_hosts: tuple[str, ...] = (),
) -> NetworkDecision:
    """قرِّر السماح بمضيف وفق السياسة، وسمِّ السبب دائمًا."""
    normalized = normalize_policy(policy)
    enforcement = enforcement_for(provider)

    if normalized == "DENY":
        return NetworkDecision(
            allowed=False,
            policy=normalized,
            enforcement=enforcement,
            host=host,
            reason="سياسة الصندوق DENY — لا وصول شبكي",
        )
    if normalized == "ALLOW_ALL":
        return NetworkDecision(
            allowed=True,
            policy=normalized,
            enforcement=enforcement,
            host=host,
            reason="سياسة الصندوق ALLOW_ALL — مُعلَنة صراحةً",
        )

    if not allowed_hosts:
        return NetworkDecision(
            allowed=False,
            policy=normalized,
            enforcement=enforcement,
            host=host,
            reason="ALLOWLIST بلا مضيف واحد — تُعامَل معاملة DENY",
        )
    if host is None:
        return NetworkDecision(
            allowed=False,
            policy=normalized,
            enforcement=enforcement,
            host=None,
            reason="ALLOWLIST تحتاج مضيفًا مُسمّى للفحص",
        )
    if host in allowed_hosts:
        return NetworkDecision(
            allowed=True,
            policy=normalized,
            enforcement=enforcement,
            host=host,
            reason="المضيف في قائمة السماح",
        )
    return NetworkDecision(
        allowed=False,
        policy=normalized,
        enforcement=enforcement,
        host=host,
        reason="المضيف خارج قائمة السماح",
    )
