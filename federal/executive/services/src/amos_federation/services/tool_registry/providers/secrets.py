"""الهدف: حدّ أسرار الصندوق الرملي — قائمة سماح صريحة لا وراثة بيئة.

النطاق: services/tool_registry/providers
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17

الحدّ الذي تفرضه هذه الوحدة، بالسلب أولًا: بيئة الصندوق **لا** تُبنى من
`os.environ` ثم يُحذَف منها الخطر. تُبنى من الفراغ ويُضاف إليها ما سُمّي.
الفرق ليس تجميليًّا: قائمة الحجب تفشل صامتةً عند كل سرّ جديد يُضاف إلى النظام
لاحقًا، وقائمة السماح لا تفشل بهذه الطريقة أبدًا.

ما لا يجوز أن يرى الصندوق بحال:

- `AMOS_DATABASE_URL` / `DATABASE_URL` وكل بيانات PostgreSQL
- اعتمادات Supabase
- أسرار التاج (`KING_LOGIN_SECRET`، `JWT_SECRET`)
- رِموز GitHub
- اعتمادات Modal (`MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET`)
- مفتاح E2B (`E2B_API_KEY`)
- مفاتيح النماذج ومفاتيح المضيف عمومًا

اعتماد المزوِّد نفسه استثناء مقصود ومحدود: هو يُستعمل في **عملية المضيف** عند
مخاطبة Modal أو E2B، ولا يُمرَّر داخل الصندوق إطلاقًا. تنفيذ التمييز في
`build_sandbox_env`: لا شيء يدخل ما لم يُسمَّ في `spec.secret_allowlist`، والأسماء
المحجوبة تُرفَض حتى إن سُمّيت.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

#: بادئات وأسماء لا يجوز تمريرها إلى الصندوق ولو وُضعت في قائمة السماح.
#: قائمة السماح تحكم «ما يدخل»؛ هذه تحكم «ما لا يدخل بحال» — وهي تسبقها.
FORBIDDEN_SECRET_PATTERNS: tuple[str, ...] = (
    "DATABASE_URL",
    "POSTGRES",
    "PGPASSWORD",
    "SUPABASE",
    "JWT_SECRET",
    "KING_LOGIN_SECRET",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_PAT",
    "MODAL_TOKEN",
    "E2B_API_KEY",
    "CLAUDE_API_KEY",
    "ANTHROPIC",
    "OPENAI",
    "MINIO_SECRET",
    "AWS_SECRET",
    "AWS_SESSION_TOKEN",
    "REDIS_PASSWORD",
    "NATS_PASSWORD",
    "HTTPS_PROXY",
    "HTTP_PROXY",
    "ALL_PROXY",
)

#: بيئة الصندوق الأساسية — لا سرّ فيها بحال. `PYTHONPATH` فارغ بقصد: تركه
#: موروثًا يجعل الصندوق يرى شجرة `amos_federation` نفسها وفيها كل الإعدادات.
BASE_SANDBOX_ENV: dict[str, str] = {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "HOME": "/tmp/amos_sandbox",
    "PYTHONPATH": "",
    "PYTHONDONTWRITEBYTECODE": "1",
    "LANG": "C.UTF-8",
    "AMOS_SANDBOX": "1",
}


class SecretBoundaryViolation(RuntimeError):  # noqa: N818 — خرق حدّ الأسرار
    """محاولة تمرير سرّ محجوب إلى الصندوق — تُرفَض ولا تُصفَّى بصمت.

    الرفض الصريح مقصود: تصفية الاسم بصمت تجعل الأداة تعمل بلا السرّ الذي طلبته
    فتفشل بسبب غامض، والمُشغِّل لا يعرف أن الحدّ الأمني هو ما منعها.
    """


@dataclass(frozen=True)
class SecretInjectionPlan:
    """ما سيُمرَّر فعلًا — بالأسماء لا بالقيم. صالح للسجل والتقارير."""

    injected: tuple[str, ...]
    requested: tuple[str, ...]
    unavailable: tuple[str, ...]


def is_forbidden_secret(name: str) -> bool:
    """هل هذا الاسم محجوب عن الصندوق مهما كانت قائمة السماح."""
    upper = name.upper()
    return any(pattern in upper for pattern in FORBIDDEN_SECRET_PATTERNS)


def assert_allowlist_is_safe(allowlist: tuple[str, ...]) -> None:
    """ارفض قائمة سماح تحتوي اسمًا محجوبًا — قبل إنشاء الصندوق لا بعده."""
    offenders = sorted({name for name in allowlist if is_forbidden_secret(name)})
    if offenders:
        raise SecretBoundaryViolation("أسماء محجوبة عن الصندوق الرملي: " + ", ".join(offenders))


def build_sandbox_env(
    allowlist: tuple[str, ...] = (),
    *,
    source: dict[str, str] | None = None,
    extra: dict[str, str] | None = None,
) -> tuple[dict[str, str], SecretInjectionPlan]:
    """ابنِ بيئة الصندوق من الفراغ ثم أضف المسموح فقط.

    Args:
        allowlist: أسماء متغيّرات البيئة المسموح تمريرها لهذه الأداة.
        source: مصدر القيم (افتراضيًّا بيئة المضيف). يُمرَّر في الاختبارات.
        extra: قيم لا تأتي من البيئة (مثل `AMOS_EXECUTION_ID`). تُفحَص كذلك.

    Returns:
        البيئة النهائية، وخطّة تُسمّي ما مُرِّر وما طُلب وما لم يوجد.

    Raises:
        SecretBoundaryViolation: إن طُلب اسم محجوب.
    """
    assert_allowlist_is_safe(allowlist)
    env = dict(BASE_SANDBOX_ENV)
    values = os.environ if source is None else source

    injected: list[str] = []
    unavailable: list[str] = []
    for name in allowlist:
        value = values.get(name)
        if value is None:
            unavailable.append(name)
            continue
        env[name] = value
        injected.append(name)

    for name, value in (extra or {}).items():
        if is_forbidden_secret(name):
            raise SecretBoundaryViolation(f"اسم محجوب عن الصندوق الرملي: {name}")
        env[name] = value

    return env, SecretInjectionPlan(
        injected=tuple(injected),
        requested=tuple(allowlist),
        unavailable=tuple(unavailable),
    )


def leaked_secret_names(env: dict[str, str]) -> tuple[str, ...]:
    """أسماء محجوبة وُجدت في بيئة جاهزة — أداة تحقُّق للاختبارات والتشخيص."""
    return tuple(sorted(name for name in env if is_forbidden_secret(name)))
