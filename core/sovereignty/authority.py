"""الهدف: تعريف طبقات السلطة وتمييز القرار السيادي عن القرار التابع تمييزًا صريحًا.

المالك: core/sovereignty/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

هذه الوحدة هي جواب E2.1 على سؤال معماري واحد: **من يحكم على من؟**

في E2 لم يكن للنظام مفهوم «طبقة سلطة» أصلًا. كان لديه فاعلون (`Branch`) وقواعد،
وكل قاعدة تُقيَّم على كل فاعل بالتساوي. فكانت نتيجته أن أغلبية فرعين (المادة
الثالثة · 3) ونسبة مجلس (المادة الرابعة · 1) **تنقض الملك** — وهو عكس المادة
العاشرة · 5 · 3 و 4 · 4 نصًّا.

فالعلاج ليس استثناءً للملك داخل القواعد (`if king: return True`)، بل **تمثيل
التسلسل نفسه في المعمار**: طبقةٌ عليا سيادية، وطبقاتٌ تابعة، وقاعدةٌ تعرف على
أيّها تُلزِم وعلى أيّها تُخبِر فقط.

قاعدة معمارية: `AuthorityLayer.CROWN` هي القيمة الصغرى، ولا يمكن إنشاء طبقة
أعلى منها — تحرس ذلك `assert_no_layer_above_crown()` واختبارٌ يفحص التعداد نفسه.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, Any

from core.sovereignty.crown import CrownError, crown_is_provisioned
from core.sovereignty.decree import DecreeError, RoyalDecree
from core.sovereignty.security_events import SecurityEventKind

if TYPE_CHECKING:  # pragma: no cover
    from core.constitutional_engine.model import ActionRequest, Branch


class AuthorityLayer(IntEnum):
    """طبقات السلطة مرتَّبة: الأصغر أعلى.

    الترتيب العددي ليس تزيينًا — هو التسلسل الدستوري نفسه، ويُقارَن به:
    `AuthorityLayer.CROWN < AuthorityLayer.FEDERAL` أي أن التاج أعلى.
    """

    CROWN = 0        # التاج — السيادة النهائية، لا طبقة فوقها
    FEDERAL = 1      # الحكومة الفدرالية وفروعها الأربعة
    STATE = 2        # الولايات
    INSTITUTION = 3  # المؤسسات
    AGENT = 4        # الوكلاء والأدوات والنماذج والمهام

    @property
    def is_sovereign(self) -> bool:
        return self is AuthorityLayer.CROWN

    @property
    def is_subordinate(self) -> bool:
        return not self.is_sovereign

    @property
    def arabic(self) -> str:
        return _LAYER_ARABIC[self]


_LAYER_ARABIC: dict[AuthorityLayer, str] = {
    AuthorityLayer.CROWN: "التاج",
    AuthorityLayer.FEDERAL: "الفدرالية",
    AuthorityLayer.STATE: "الولاية",
    AuthorityLayer.INSTITUTION: "المؤسسة",
    AuthorityLayer.AGENT: "الوكيل",
}

SUBORDINATE_LAYERS: frozenset[AuthorityLayer] = frozenset(
    layer for layer in AuthorityLayer if layer.is_subordinate
)


def supreme_layer() -> AuthorityLayer:
    """الطبقة العليا — تُحسَب من التعداد ولا تُكتَب بالاسم.

    لو أُضيفت يومًا طبقة أعلى من التاج لتغيّرت هذه القيمة، ولفشل الاختبار الحارس.
    """
    return min(AuthorityLayer)


def assert_no_layer_above_crown() -> None:
    """حراسة معمارية: لا طبقة تعلو التاج (المادة العاشرة · 1 · 3)."""
    if supreme_layer() is not AuthorityLayer.CROWN:
        raise SovereigntyModelError(
            f"طبقة «{supreme_layer().name}» تعلو التاج. "
            "لا سلطة في الدولة تعلو على سلطة الملك (المادة العاشرة · 1 · 3)."
        )


class DecisionKind(str, Enum):
    """نوع القرار — الأساس الذي يُبنى عليه أي مسار تقييم.

    المادة العاشرة تفرّق بين «فعل فدرالي» و«فعل سيادي ملكي»، وهذا التعداد هو
    ذلك الفرق في الكود.
    """

    SOVEREIGN_ROYAL = "SOVEREIGN_ROYAL"
    FEDERAL = "FEDERAL"
    STATE = "STATE"
    INSTITUTIONAL = "INSTITUTIONAL"
    AGENT = "AGENT"

    @property
    def is_sovereign(self) -> bool:
        return self is DecisionKind.SOVEREIGN_ROYAL


class SovereigntyModelError(Exception):
    """خلل في نموذج السيادة نفسه — لا في طلب بعينه."""


class RoyalAuthenticityError(Exception):
    """ادّعاء صفة ملكية لم تثبت أصالته تشفيريًّا.

    هذا ليس نقضًا لقرار سيادي، بل نفيٌ لكونه قرارًا سياديًّا أصلًا (من غير الملك):
    «لا سلطة فوق الملك» لا تعني «لا حاجة إلى إثبات أن الملك هو المتكلم».
    """

    def __init__(self, reason: str, *, event_kind: str | SecurityEventKind) -> None:
        self.reason = reason
        # يُحوّل دائمًا للنوع المعدود: نوع حدث مجهول يرفع هنا ولا يمرّ نصًا حرًّا.
        self.event_kind: SecurityEventKind = SecurityEventKind(event_kind)
        super().__init__(reason)


# ─────────────────────────────────────────────────────────────────────────────
# نسبة الفاعل إلى طبقته
# ─────────────────────────────────────────────────────────────────────────────

def layer_of_actor(actor: "Branch") -> AuthorityLayer:
    """طبقة الفاعل.

    ملاحظة أمنية مقصودة: `Branch.HUMAN` و`Branch.ROYAL` **لا** تمنحان الطبقة
    السيادية بمجردهما. الطبقة السيادية تُنال بمرسوم موقَّع لا بقيمة تعداد يكتبها
    الطالب في طلبه — وإلا صار انتحال صفة الملك حرفًا في حقل.
    """
    from core.constitutional_engine.model import Branch  # استيراد متأخر: منع دور

    return {
        Branch.ROYAL: AuthorityLayer.FEDERAL,
        Branch.HUMAN: AuthorityLayer.FEDERAL,
        Branch.EXECUTIVE: AuthorityLayer.FEDERAL,
        Branch.LEGISLATIVE: AuthorityLayer.FEDERAL,
        Branch.JUDICIAL: AuthorityLayer.FEDERAL,
        Branch.TREASURY: AuthorityLayer.FEDERAL,
        Branch.STATE: AuthorityLayer.STATE,
        Branch.INSTITUTION: AuthorityLayer.INSTITUTION,
        Branch.AGENT: AuthorityLayer.AGENT,
        Branch.SYSTEM: AuthorityLayer.AGENT,
    }[actor]


def _kind_of_layer(layer: AuthorityLayer) -> DecisionKind:
    return {
        AuthorityLayer.CROWN: DecisionKind.SOVEREIGN_ROYAL,
        AuthorityLayer.FEDERAL: DecisionKind.FEDERAL,
        AuthorityLayer.STATE: DecisionKind.STATE,
        AuthorityLayer.INSTITUTION: DecisionKind.INSTITUTIONAL,
        AuthorityLayer.AGENT: DecisionKind.AGENT,
    }[layer]


@dataclass(frozen=True, slots=True)
class AuthorityClassification:
    """تصنيف طلب واحد: أي طبقة يتكلم، وهل قراره سيادي.

    الطبقة السيادية لا تُدَّعى — تُثبَت. ولذلك يحمل هذا التصنيف نتيجة تحقّق
    تعميّ لا رايةً كتبها الطالب.
    """

    kind: DecisionKind
    layer: AuthorityLayer
    claimed_royal: bool
    authenticity_verified: bool
    decree_id: str | None
    reason: str

    @property
    def is_sovereign(self) -> bool:
        return self.kind.is_sovereign

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "layer": self.layer.name,
            "layer_rank": int(self.layer),
            "claimed_royal": self.claimed_royal,
            "authenticity_verified": self.authenticity_verified,
            "decree_id": self.decree_id,
            "reason": self.reason,
        }


def classify(request: "ActionRequest") -> AuthorityClassification:
    """صنّف الطلب: قرار سيادي ملكي أم قرار تابع؟

    شروط المسار السيادي — كلها لازمة، ولا واحد منها موافقةُ سلطة أعلى:

    1. **الأصالة** (authenticity): الفاعل `royal` ومعه مرسوم موقَّع Ed25519 صحيح.
    2. **الاختصاص** (authority): المرسوم صادر عن مفتاح التاج المُسجَّل.
    3. **السلامة** (integrity): المرسوم غير معبوث به — التوقيع على تمثيله القانوني.

    والتحقق من هذه الثلاثة **ليس إذنًا من سلطة أعلى**: هو الجواب على سؤال «هل
    هذا هو الملك؟» لا على سؤال «هل يُسمح للملك؟». الأول سؤال هوية، والثاني لا
    يُطرَح في ملكية سيادية.

    ويرفع `RoyalAuthenticityError` عند ادّعاء ملكي لم يثبت — فادّعاء الصفة
    الملكية بلا مفتاح ليس قرارًا سياديًّا ولا قرارًا تابعًا، بل حدث أمني.
    """
    from core.constitutional_engine.model import Branch  # استيراد متأخر: منع دور

    assert_no_layer_above_crown()

    claimed_royal = request.actor is Branch.ROYAL
    decree = request.royal_decree

    if not claimed_royal:
        if isinstance(decree, RoyalDecree):
            # مرسوم ملكي في يد فاعل غير الملك: لا يرفع طبقته.
            raise RoyalAuthenticityError(
                f"الفاعل «{request.actor.value}» يقدّم مرسومًا ملكيًّا "
                f"«{decree.decree_id}» وهو ليس الملك. المرسوم لا يُحمَل بالوكالة "
                "ولا يرفع طبقة حامله.",
                event_kind="DECREE_PRESENTED_BY_NON_ROYAL",
            )
        layer = layer_of_actor(request.actor)
        return AuthorityClassification(
            kind=_kind_of_layer(layer),
            layer=layer,
            claimed_royal=False,
            authenticity_verified=False,
            decree_id=None,
            reason=(
                f"قرار تابع من طبقة «{layer.arabic}» — يُقيَّم دستوريًّا تقييمًا "
                "مُلزِمًا كالمعتاد."
            ),
        )

    # ── ادّعاء ملكي: يُثبَت أو يُرفَض، ولا يمرّ كقرار تابع ──────────────────
    if decree is None:
        raise RoyalAuthenticityError(
            f"أمر ملكي «{request.action}» بلا مرسوم موقَّع. لا سلطة فوق الملك، "
            "ولكن لا سيادة بلا إثبات: الأمر غير الموقَّع ليس أمرًا ملكيًّا.",
            event_kind="ROYAL_COMMAND_UNSIGNED",
        )
    if not isinstance(decree, RoyalDecree):
        raise RoyalAuthenticityError(
            f"حقل المرسوم من نوع «{type(decree).__name__}» لا `RoyalDecree`. "
            "لا يُقبل كائن يشبه المرسوم مكان المرسوم.",
            event_kind="DECREE_TYPE_INVALID",
        )
    if decree.action != request.action:
        raise RoyalAuthenticityError(
            f"المرسوم «{decree.decree_id}» صادر للفعل «{decree.action}» "
            f"والمطلوب «{request.action}». المرسوم لا يُعاد توجيهه إلى فعل آخر.",
            event_kind="DECREE_ACTION_MISMATCH",
        )
    if not crown_is_provisioned():
        raise RoyalAuthenticityError(
            "التاج غير مُنصَّب فلا يُتحقق من المرسوم. غياب التاج يُجمّد الاختصاص "
            "الملكي ولا ينقله لأي طرف (المادة العاشرة · 6 · 2).",
            event_kind="CROWN_UNPROVISIONED",
        )
    try:
        decree.verify()
    except (DecreeError, CrownError) as exc:
        raise RoyalAuthenticityError(
            f"مرسوم «{decree.decree_id}» لم تثبت أصالته تشفيريًّا: "
            f"{type(exc).__name__}: {exc}",
            event_kind="ROYAL_SIGNATURE_INVALID",
        ) from exc

    return AuthorityClassification(
        kind=DecisionKind.SOVEREIGN_ROYAL,
        layer=AuthorityLayer.CROWN,
        claimed_royal=True,
        authenticity_verified=True,
        decree_id=decree.decree_id,
        reason=(
            f"قرار سيادي ملكي بالمرسوم «{decree.decree_id}» — أصالته واختصاصه "
            "وسلامته ثابتة تعميًّا. يُقيَّم دستوريًّا تقييمًا **مُخبِرًا** لا مانعًا."
        ),
    )


__all__ = [
    "AuthorityClassification",
    "AuthorityLayer",
    "DecisionKind",
    "RoyalAuthenticityError",
    "SovereigntyModelError",
    "SUBORDINATE_LAYERS",
    "assert_no_layer_above_crown",
    "classify",
    "layer_of_actor",
    "supreme_layer",
]
