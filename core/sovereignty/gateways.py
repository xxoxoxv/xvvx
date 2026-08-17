"""الهدف: بوابات الطبقات التابعة — كل طبقة لها بوابتها المُثبَّتة على طبقتها.

المالك: core/sovereignty/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

قبل E2.1 كانت التبعية ضمنية: بوابة واحدة، والفاعل حقلٌ في الطلب. والضمني لا
يُختبَر. هذه الوحدة تجعل التبعية **صريحة ومُثبَّتة**: بوابة الولاية ولاية، ولا
تصير تاجًا بأي معامل ولا بأي حقل ولا بأي وراثة.

وثلاثة قيود تحرسها اختبارات مباشرة:

1. **لا ترقّي**: بوابة تابعة ترفض أي طلب يُقدَّم بطبقة أعلى من طبقتها.
2. **لا نقض**: لا تملك بوابة تابعة منع قرار سيادي — ليس فيها مسار إلى ذلك أصلًا.
3. **لا تخفيف**: القيود الدستورية على الطبقة التابعة كما هي قبل E2.1 تمامًا.

والفدرالية بهذا تبقى حقيقية لا شكلية: الطبقات التابعة مقيَّدة فعلًا، وكل فعل
يمرّ من البوابة، وكل فعل يُسجَّل. وهي مع ذلك ليست سلطة فوق التاج.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from core.constitutional_engine.model import ActionRequest, Verdict
from core.sovereignty.authority import (
    AuthorityLayer,
    SovereigntyModelError,
    layer_of_actor,
)
from core.sovereignty.gateway import SovereignGateway

T = TypeVar("T")


class LayerEscalationError(SovereigntyModelError):
    """طرف تابع حاول التقدّم بطلب من طبقة أعلى من طبقته."""


class SubordinateGateway:
    """أساس البوابات التابعة. لا تُستعمل مباشرة — تُستعمل إحدى بناتها.

    وهي **غلاف** على البوابة السيادية لا بديل عنها: كل تنفيذ يمرّ من
    `SovereignGateway.execute` نفسها، فلا يوجد مسار تنفيذ ثانٍ في الدولة
    (المادة العاشرة · 4). ودورها الوحيد أن تمنع الترقّي قبل التسليم.
    """

    layer: AuthorityLayer  # تُثبَّت في كل بنت، ولا تُمرَّر معامَلًا

    def __init__(self, gateway: SovereignGateway | None = None) -> None:
        if not hasattr(type(self), "layer"):
            raise SovereigntyModelError(
                f"«{type(self).__name__}» بلا طبقة مُثبَّتة. لا بوابة بلا طبقة."
            )
        if self.layer.is_sovereign:
            raise SovereigntyModelError(
                "لا تُبنى بوابة تابعة على الطبقة السيادية. السيادة ليست طبقة "
                "تُورَّث، بل تُثبَت بمرسوم موقَّع."
            )
        self._gateway = gateway or SovereignGateway()

    # ── الحراسة ───────────────────────────────────────────────────────────
    def _assert_no_escalation(self, request: ActionRequest) -> None:
        """طبقة الفاعل يجب أن تكون طبقة هذه البوابة أو أدنى منها.

        الأدنى مقبول: الفدرالي يُقدّم طلبًا باسم وكيل. والأعلى مرفوض دائمًا،
        وأعلى الجميع التاج — فلا تُقدَّم قرارات التاج من بوابة تابعة.
        """
        actor_layer = layer_of_actor(request.actor)
        if actor_layer < self.layer:
            raise LayerEscalationError(
                f"بوابة «{self.layer.arabic}» تلقّت طلبًا من طبقة "
                f"«{actor_layer.arabic}» وهي أعلى منها. الترقّي عبر البوابات ممنوع: "
                "الطبقة تُنسَب للفاعل ولا تُنتزَع من البوابة."
            )
        if request.royal_decree is not None:
            raise LayerEscalationError(
                f"بوابة «{self.layer.arabic}» لا تحمل مرسومًا ملكيًّا. القرار "
                "السيادي مساره البوابة السيادية وحدها، ولا يُوسَّط بطرف تابع."
            )

    # ── الاستعمال ─────────────────────────────────────────────────────────
    def review(self, request: ActionRequest) -> Verdict:
        """حكم دستوري مُلزِم بلا تنفيذ."""
        self._assert_no_escalation(request)
        return self._gateway.review(request)

    def execute(self, request: ActionRequest, executor: Callable[[], T]) -> T:
        """تنفيذ تابع: الدستور مُلزِم، والمخالفة تمنع. لا استثناء لطرف تابع."""
        self._assert_no_escalation(request)
        return self._gateway.execute(request, executor)

    @property
    def sovereign_gateway(self) -> SovereignGateway:
        return self._gateway

    def __repr__(self) -> str:
        return f"<{type(self).__name__} layer={self.layer.name}>"


class FederalGateway(SubordinateGateway):
    """بوابة السلطة الفدرالية — الفروع الأربعة (المادة الثالثة)."""

    layer = AuthorityLayer.FEDERAL


class StateGateway(SubordinateGateway):
    """بوابة الولاية — تابعة للفدرالية وللتاج (المادة الرابعة)."""

    layer = AuthorityLayer.STATE


class InstitutionGateway(SubordinateGateway):
    """بوابة المؤسسة — تابعة لولايتها وللفدرالية وللتاج."""

    layer = AuthorityLayer.INSTITUTION


class AgentGateway(SubordinateGateway):
    """بوابة الوكيل — أضيق الطبقات صلاحية (المادة الثانية)."""

    layer = AuthorityLayer.AGENT


SUBORDINATE_GATEWAYS: tuple[type[SubordinateGateway], ...] = (
    FederalGateway,
    StateGateway,
    InstitutionGateway,
    AgentGateway,
)


__all__ = [
    "AgentGateway",
    "FederalGateway",
    "InstitutionGateway",
    "LayerEscalationError",
    "SUBORDINATE_GATEWAYS",
    "StateGateway",
    "SubordinateGateway",
]
