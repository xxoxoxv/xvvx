"""الهدف: المرسوم الملكي — بنيته وتوقيعه Ed25519 والتحقق منه ومنع إعادة استخدامه.

المالك: core/sovereignty/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المرسوم هو الطريقة الوحيدة التي تُمارَس بها السلطة الملكية داخل النظام. لا يوجد
«وضع ملكي» يُفعَّل براية أو متغير بيئة، ولا انتحال لصفة الملك بلا مفتاحه.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from core.sovereignty.crown import Crown, CrownNotProvisionedError, load_crown
from core.sovereignty.prerogatives import immune_clauses_touched

_LOG = logging.getLogger("amos.sovereignty.decree")


class DecreeError(Exception):
    """خطأ في مرسوم ملكي."""


class DecreeSignatureError(DecreeError):
    """توقيع المرسوم غير صحيح — انتحال صفة ملكية."""


class DecreeImmuneClauseError(DecreeError):
    """المرسوم يمسّ نصًا محصَّنًا (المادة العاشرة · 3 · 3)."""


class DecreeReplayError(DecreeError):
    """المرسوم مُستخدَم من قبل — إعادة استخدام مرفوضة."""


@dataclass(frozen=True, slots=True)
class RoyalDecree:
    """مرسوم ملكي: أمر مُوقَّع من الملك بفعل واحد محدد.

    التوقيع يقع على التمثيل القانوني (canonical) للمرسوم، فأي تعديل في أي حقل
    — بما فيه decree_id — يُبطل التوقيع.
    """

    decree_id: str
    action: str
    target: str | None = None
    targets: tuple[str, ...] = ()
    issued_at: str = ""
    justification: str = ""
    key_id: str = ""
    signature_hex: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    # ── التمثيل القانوني ──────────────────────────────────────────────────
    def canonical_payload(self) -> bytes:
        """البايتات التي يقع عليها التوقيع. مستقرة وحتمية ولا تشمل التوقيع."""
        payload = {
            "decree_id": self.decree_id,
            "action": self.action,
            "target": self.target,
            "targets": list(self.targets),
            "issued_at": self.issued_at,
            "justification": self.justification,
            "key_id": self.key_id,
            "metadata": self.metadata,
        }
        return json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

    @property
    def fingerprint(self) -> str:
        """بصمة المرسوم — تُستخدم لمنع إعادة الاستخدام."""
        return hashlib.sha256(self.canonical_payload()).hexdigest()

    # ── التحقق ────────────────────────────────────────────────────────────
    def verify(self, crown: Crown | None = None) -> None:
        """تحقق كامل: التحصين أولًا، ثم صحة التوقيع. يرفع استثناءً عند الفشل.

        ترتيب الفحص مقصود: مرسوم يمسّ نصًا محصَّنًا يُرفض **قبل** النظر في
        توقيعه، حتى لا يُفهم أن توقيعًا صحيحًا يُجيز ما لا يجوز.
        """
        touched = immune_clauses_touched(self.all_targets())
        if touched:
            raise DecreeImmuneClauseError(
                "المرسوم يمسّ نصًا محصَّنًا لا يُعدَّل من أي طرف بما في ذلك الملك "
                f"(المادة العاشرة · 3 · 3): {', '.join(touched)}. "
                "التحصين حماية للملك من مرسوم مُنتحَل أو منتزَع إكراهًا."
            )
        if not self.signature_hex:
            raise DecreeSignatureError("المرسوم بلا توقيع.")
        try:
            signature = bytes.fromhex(self.signature_hex)
        except ValueError as exc:
            raise DecreeSignatureError(f"توقيع المرسوم ليس hex صالحًا: {exc}") from exc

        resolved = crown
        if resolved is None:
            resolved = load_crown()  # يرفع CrownNotProvisionedError إن لم يكن مُنصَّبًا
        if self.key_id and self.key_id != resolved.key_id:
            raise DecreeSignatureError(
                f"المرسوم موقَّع بمفتاح «{self.key_id}» والمفتاح النشط "
                f"«{resolved.key_id}»."
            )
        if not resolved.verify(self.canonical_payload(), signature):
            raise DecreeSignatureError(
                "توقيع المرسوم لا يطابق مفتاح التاج العام — انتحال صفة ملكية "
                "(المادة العاشرة · 3 · 2)."
            )

    def is_valid(self, crown: Crown | None = None) -> bool:
        """نسخة لا ترفع استثناءً — والسبب يُسجَّل لا يُبتلع.

        مرسوم مرفوض حدث دستوري يجب أن يبقى له أثر، لا `False` صامتة.
        """
        try:
            self.verify(crown)
        except (DecreeError, CrownNotProvisionedError) as exc:
            _LOG.warning("رُفض المرسوم «%s»: %s", self.decree_id, exc)
            return False
        return True

    def all_targets(self) -> tuple[str, ...]:
        """كل الأهداف: المفرد والجمع معًا."""
        combined = list(self.targets)
        if self.target:
            combined.append(self.target)
        return tuple(dict.fromkeys(combined))

    # ── التسلسل ───────────────────────────────────────────────────────────
    def to_dict(self) -> dict[str, Any]:
        return {
            "decree_id": self.decree_id,
            "action": self.action,
            "target": self.target,
            "targets": list(self.targets),
            "issued_at": self.issued_at,
            "justification": self.justification,
            "key_id": self.key_id,
            "signature_hex": self.signature_hex,
            "metadata": self.metadata,
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoyalDecree:
        return cls(
            decree_id=str(data.get("decree_id", "")),
            action=str(data.get("action", "")),
            target=data.get("target"),
            targets=tuple(data.get("targets") or ()),
            issued_at=str(data.get("issued_at", "")),
            justification=str(data.get("justification", "")),
            key_id=str(data.get("key_id", "")),
            signature_hex=str(data.get("signature_hex", "")),
            metadata=dict(data.get("metadata") or {}),
        )


class DecreeRegistry:
    """سجل المراسيم المُستهلَكة — يمنع إعادة استخدام مرسوم واحد مرتين."""

    def __init__(self) -> None:
        self._used: dict[str, str] = {}

    def consume(self, decree: RoyalDecree) -> None:
        fingerprint = decree.fingerprint
        if fingerprint in self._used:
            raise DecreeReplayError(
                f"المرسوم «{decree.decree_id}» استُهلك في "
                f"{self._used[fingerprint]} — إعادة الاستخدام مرفوضة."
            )
        self._used[fingerprint] = datetime.now(timezone.utc).isoformat()

    def was_used(self, decree: RoyalDecree) -> bool:
        return decree.fingerprint in self._used

    def __len__(self) -> int:
        return len(self._used)


def sign_decree(decree: RoyalDecree, private_key: Any) -> RoyalDecree:
    """أداة توقيع — للاختبارات ولأدوات الملك المحلية فقط.

    الدولة لا تملك مفتاحًا خاصًا، فهذه الدالة لا تُستخدَم في أي مسار تشغيلي.
    """
    signature = private_key.sign(decree.canonical_payload())
    return RoyalDecree(
        decree_id=decree.decree_id,
        action=decree.action,
        target=decree.target,
        targets=decree.targets,
        issued_at=decree.issued_at,
        justification=decree.justification,
        key_id=decree.key_id,
        signature_hex=signature.hex(),
        metadata=decree.metadata,
    )
