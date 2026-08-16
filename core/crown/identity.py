"""الهدف: فصل هويات التاج الخمس، وتمييز الهوية عن الحضور عن القصد عن السلطة.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

الخطأ المعماري الذي تمنعه هذه الوحدة هو **دمج الهويات في حقل واحد**: اسم الملك،
ومعرّف حسابه، ولقبه، ومعرّف مفتاح التاج، ومعرّف جهازه، وبصمته الحيوية — خمسة
أشياء مختلفة. من دمجها صار سرقة أحدها انتحالًا للبقية.

وتمييز ثانٍ لا يقلّ أهمية: **البصمة ليست مفتاحًا خاصًا.** البصمة والوجه والصوت
والحمض النووي عوامل إثبات هوية تفتح بيئة توقيع محمية، ولا تكون هي مادة التوقيع
التعمية. بصمة مسروقة لا تساوي ملكًا راضيًا، وصوتًا مُصطنعًا لا يساوي أمرًا ملكيًّا.

ولذلك تفصل هذه الوحدة أربعة أسئلة لا تُجاب بجواب واحد:

    IDENTITY   — من هذا؟
    PRESENCE   — هل هو حاضر الآن؟
    INTENT     — هل يقصد هذا الأمر بعينه؟
    AUTHORITY  — هل هذا الدور هو التاج؟

والسلطة (AUTHORITY) لا تُشتق من الثلاثة الأولى: التاج سلطة سيادية بموجب المادة
العاشرة، وهذه الوحدة تُثبت الهوية ولا تمنح سلطة ولا تُصادر سلطة.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Final


class IdentityError(Exception):
    """خلل في نموذج هويات التاج."""


class IdentityConflationError(IdentityError):
    """دمج هويتين مختلفتين في معرّف واحد — أصل انتحال."""


class BiometricAsKeyError(IdentityError):
    """استعمال عامل حيوي كمفتاح خاص — ممنوع بنيويًّا (التصحيح التقني · 2)."""


# ─────────────────────────────────────────────────────────────────────────────
# الهويات الخمس — كل واحدة نوع مستقل، ولا واحدة تُشتق من الأخرى
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class HumanSovereignIdentity:
    """الملك كإنسان. لا تُخزَّن هنا بيانات شخصية، بل مرجع مُعمّى إليها.

    السبب: سجل الدولة ليس محل حفظ بيانات الملك الشخصية، والمرجع المُعمّى يكفي
    للربط ولا يكفي لانتحال.
    """

    subject_ref: str
    display_title: str = "الملك"

    def __post_init__(self) -> None:
        if not self.subject_ref:
            raise IdentityError("الهوية البشرية بلا مرجع.")

    @property
    def kind(self) -> str:
        return "human_sovereign"


@dataclass(frozen=True, slots=True)
class CrownInstitutionalIdentity:
    """التاج كمؤسسة — الدور لا الشخص. يبقى عبر تعاقب المفاتيح والأشخاص."""

    crown_id: str
    established_at: str

    def __post_init__(self) -> None:
        if not self.crown_id:
            raise IdentityError("الهوية المؤسسية للتاج بلا معرّف.")

    @property
    def kind(self) -> str:
        return "crown_institutional"


@dataclass(frozen=True, slots=True)
class CrownCryptographicIdentity:
    """هوية التاج التعمية — مفتاح عام واحد بنسخته. تتغيّر بالتدوير ولا يتغيّر الدور."""

    key_id: str
    algorithm: str
    public_key_hex: str
    version: int

    def __post_init__(self) -> None:
        if not self.key_id or not self.public_key_hex:
            raise IdentityError("الهوية التعمية بلا معرّف مفتاح أو بلا مفتاح عام.")
        if self.version < 1:
            raise IdentityError("نسخة المفتاح تبدأ من 1.")

    @property
    def kind(self) -> str:
        return "crown_cryptographic"

    @property
    def fingerprint(self) -> str:
        """بصمة المفتاح العام — مُشتقّة لا مُدخَلة، فلا تُكتب خطأً ولا تُلفَّق."""
        return hashlib.sha256(
            f"AMOS-CROWN-KEY-v1:{self.algorithm}:{self.public_key_hex}".encode()
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class CrownDeviceIdentity:
    """جهاز التوقيع — معرّفه وإشهاد عتاده. الجهاز ليس الملك، وفقدانه ليس فقدانه."""

    device_id: str
    attestation_ref: str = ""
    hardware_backed: bool = False

    def __post_init__(self) -> None:
        if not self.device_id:
            raise IdentityError("هوية الجهاز بلا معرّف.")

    @property
    def kind(self) -> str:
        return "crown_device"


@dataclass(frozen=True, slots=True)
class CrownCommandIdentity:
    """هوية أمر واحد — معرّفه ونونسه وتسلسله. تُستهلك ولا تتكرر."""

    command_id: str
    nonce: str
    sequence: int

    def __post_init__(self) -> None:
        if not self.command_id or not self.nonce:
            raise IdentityError("هوية الأمر بلا معرّف أو بلا نونس.")
        if self.sequence < 0:
            raise IdentityError("تسلسل الأمر لا يكون سالبًا.")

    @property
    def kind(self) -> str:
        return "crown_command"


IDENTITY_KINDS: Final[tuple[str, ...]] = (
    "human_sovereign",
    "crown_institutional",
    "crown_cryptographic",
    "crown_device",
    "crown_command",
)


@dataclass(frozen=True, slots=True)
class IdentityBinding:
    """ربط صريح بين هويتين — الربط يُعلَن ولا يُفترض.

    `basis` يجيب سؤال «بأي شيء ثبت هذا الربط؟» — مرسوم، أو إشهاد بشري موثوق،
    أو مراسم تنصيب. ربطٌ بلا سند ليس ربطًا.
    """

    left_kind: str
    left_id: str
    right_kind: str
    right_id: str
    basis: str

    def __post_init__(self) -> None:
        for kind in (self.left_kind, self.right_kind):
            if kind not in IDENTITY_KINDS:
                raise IdentityError(f"نوع هوية مجهول: {kind}")
        if self.left_kind == self.right_kind:
            raise IdentityConflationError(
                f"ربط نوع هوية بنفسه ({self.left_kind}) ليس ربطًا بل دمج."
            )
        if not self.basis:
            raise IdentityError("ربط الهويات بلا سند مُعلَن.")


class IdentityGraph:
    """بيان الهويات وروابطها — يحرس أن تبقى الخمس خمسًا."""

    def __init__(self) -> None:
        self._identities: dict[str, Any] = {}
        self._bindings: list[IdentityBinding] = []

    def register(self, identity: Any) -> None:
        """سجّل هوية واحدة من نوعها.

        وإبدال هوية مسجَّلة بأخرى من نوعها ممنوع هنا: لو مرّ صامتًا لكان استبدال
        الهوية التعمية للتاج مجرّد نداء ``register`` ثانٍ، وهو عين ما تحرسه هذه
        الوحدة. فالإبدال يجري بمراسم تدوير مقيَّدة في السجل، لا بكتابة فوق قيد.
        """
        kind = getattr(identity, "kind", None)
        if kind not in IDENTITY_KINDS:
            raise IdentityError(f"كائن ليس هوية تاج معروفة: {identity!r}")
        existing = self._identities.get(kind)
        if existing is not None and existing != identity:
            raise IdentityConflationError(
                f"هوية من نوع «{kind}» مسجَّلة سابقًا؛ الإبدال الصامت ممنوع."
            )
        self._identities[kind] = identity

    def bind(self, binding: IdentityBinding) -> None:
        for kind in (binding.left_kind, binding.right_kind):
            if kind not in self._identities:
                raise IdentityError(f"لا هوية مسجَّلة من نوع «{kind}» لتُربَط.")
        self._bindings.append(binding)

    @property
    def bindings(self) -> tuple[IdentityBinding, ...]:
        return tuple(self._bindings)

    def get(self, kind: str) -> Any | None:
        return self._identities.get(kind)

    def identifiers(self) -> dict[str, str]:
        """المعرّف الفعلي لكل هوية مسجَّلة."""
        out: dict[str, str] = {}
        for kind, ident in self._identities.items():
            out[kind] = str(
                getattr(ident, "subject_ref", None)
                or getattr(ident, "crown_id", None)
                or getattr(ident, "key_id", None)
                or getattr(ident, "device_id", None)
                or getattr(ident, "command_id", None)
            )
        return out

    def assert_distinct(self) -> None:
        """لا معرّف واحد يخدم هويتين — وإلا فالفصل صوري.

        هذا الفحص هو الفرق بين «فصل معماري» و«خمسة أسماء لحقل واحد».
        """
        seen: dict[str, str] = {}
        for kind, ident_id in self.identifiers().items():
            if ident_id in seen:
                raise IdentityConflationError(
                    f"المعرّف «{ident_id}» يخدم «{seen[ident_id]}» و«{kind}» معًا. "
                    "الهويات الخمس لا تُدمَج في حقل واحد."
                )
            seen[ident_id] = kind

    def missing_kinds(self) -> tuple[str, ...]:
        return tuple(k for k in IDENTITY_KINDS if k not in self._identities)


# ─────────────────────────────────────────────────────────────────────────────
# عوامل الإثبات — ولا واحد منها مفتاح خاص
# ─────────────────────────────────────────────────────────────────────────────


class FactorKind(str, Enum):
    """أنواع عوامل إثبات هوية الملك أمام بيئة التوقيع."""

    POSSESSION = "POSSESSION"        # شيء يملكه الملك
    KNOWLEDGE = "KNOWLEDGE"          # شيء يعرفه
    BIOMETRIC = "BIOMETRIC"          # شيء مرتبط ببدنه
    DEVICE = "DEVICE"                # جهاز مُشهَد عليه
    HARDWARE_CONFIRMATION = "HARDWARE_CONFIRMATION"  # تأكيد على العتاد نفسه
    HUMAN_CONFIRMATION = "HUMAN_CONFIRMATION"        # تأكيد بشري صريح

    @property
    def proves_presence(self) -> bool:
        """أي العوامل تدل على حضور، لا على هوية فقط."""
        return self in {
            FactorKind.BIOMETRIC,
            FactorKind.HARDWARE_CONFIRMATION,
            FactorKind.HUMAN_CONFIRMATION,
        }

    @property
    def proves_intent(self) -> bool:
        """القصد لا يُثبته إلا تأكيد صريح — لا بصمة ولا صوت ولا صورة."""
        return self in {
            FactorKind.HUMAN_CONFIRMATION,
            FactorKind.HARDWARE_CONFIRMATION,
            FactorKind.KNOWLEDGE,
        }


# العوامل التي لا يجوز أن تكون مادة المفتاح الخاص بأي حال
FORBIDDEN_KEY_MATERIAL: Final[frozenset[str]] = frozenset(
    {
        "fingerprint",
        "face",
        "voice",
        "dna",
        "photograph",
        "iris",
        "retina",
        "behavioral_pattern",
        "gait",
        "brain_signal",
        "neural_implant",
    }
)


def _tokens(source: str) -> set[str]:
    """فكّ النص إلى كلماته — مطابقة الكلمة لا المقطع.

    والتمييز مقصود: المطابقة بالمقطع تُسقِط أسماء مشروعة («device_interface» فيها
    «face»)، والمطابقة بالنص كاملًا يتجاوزها من سمّى الحقل «fingerprint_template».
    فالكلمة هي الوحدة الصحيحة.
    """
    normalized = source.strip().lower()
    for separator in (" ", "-", ".", "/", ":", "|"):
        normalized = normalized.replace(separator, "_")
    return {token for token in normalized.split("_") if token}


def assert_not_key_material(source: str) -> None:
    """يرفع إن حاول أحد اتخاذ عامل حيوي مفتاحًا خاصًا.

    السبب ليس فقهيًّا بل تعميًّا: العامل الحيوي غير قابل للتدوير ولا للسحب،
    ويُنسَخ من غير علم صاحبه، فلو كان مفتاحًا لكان مفتاحًا أبديًّا مسروقًا.
    """
    tokens = _tokens(source)
    single_word_hit = bool(tokens & FORBIDDEN_KEY_MATERIAL)
    phrase_hit = any(
        set(entry.split("_")) <= tokens
        for entry in FORBIDDEN_KEY_MATERIAL
        if "_" in entry
    )
    if single_word_hit or phrase_hit:
        raise BiometricAsKeyError(
            f"«{source}» عامل إثبات هوية لا مفتاح خاص. المفتاح الخاص يبقى داخل "
            "عتاد أمني معزول، والعوامل الحيوية تفتحه ولا تكون هي إياه."
        )


@dataclass(frozen=True, slots=True)
class FactorEvidence:
    """دليل عامل واحد: نوعه، وهل نجح، ومصدره، ووقته."""

    kind: FactorKind
    satisfied: bool
    source: str
    observed_at: str
    anomaly: str = ""

    def __post_init__(self) -> None:
        assert_not_key_material(self.source)


@dataclass(frozen=True, slots=True)
class AuthenticationAssessment:
    """تقييم أربع مسائل منفصلة عن أمر ملكي واحد.

    ولا واحدة منها تُشتق من الأخرى: هوية ثابتة مع حضور مشكوك فيه ليست قصدًا،
    وقصد ثابت من غير التاج ليس سلطة.
    """

    identity_established: bool
    presence_established: bool
    intent_established: bool
    authority_is_crown: bool
    factors: tuple[FactorEvidence, ...] = ()
    anomalies: tuple[str, ...] = ()

    @property
    def factor_count(self) -> int:
        return sum(1 for f in self.factors if f.satisfied)

    @property
    def is_multi_factor(self) -> bool:
        """عاملان مستقلان على الأقل من نوعين مختلفين."""
        kinds = {f.kind for f in self.factors if f.satisfied}
        return len(kinds) >= 2

    @property
    def suspicious(self) -> bool:
        """أي شذوذ مُسجَّل، أو هوية بلا حضور، أو حضور بلا قصد."""
        if self.anomalies or any(f.anomaly for f in self.factors):
            return True
        if self.identity_established and not self.presence_established:
            return True
        return self.presence_established and not self.intent_established

    def as_dict(self) -> dict[str, Any]:
        return {
            "identity_established": self.identity_established,
            "presence_established": self.presence_established,
            "intent_established": self.intent_established,
            "authority_is_crown": self.authority_is_crown,
            "factor_count": self.factor_count,
            "multi_factor": self.is_multi_factor,
            "suspicious": self.suspicious,
            "anomalies": list(self.anomalies),
        }


def assess(
    factors: tuple[FactorEvidence, ...],
    *,
    authority_is_crown: bool,
    anomalies: tuple[str, ...] = (),
) -> AuthenticationAssessment:
    """اجمع أدلة العوامل في تقييم — بلا استنتاج زائد على الأدلة.

    القاعدة: الهوية تحتاج عاملين مستقلين، والحضور يحتاج عاملًا يدل على الحضور،
    والقصد يحتاج تأكيدًا صريحًا. وما لم يُثبَت لا يُفترَض.
    """
    satisfied = tuple(f for f in factors if f.satisfied)
    kinds = {f.kind for f in satisfied}
    return AuthenticationAssessment(
        identity_established=len(kinds) >= 2,
        presence_established=any(k.proves_presence for k in kinds),
        intent_established=any(k.proves_intent for k in kinds),
        authority_is_crown=authority_is_crown,
        factors=factors,
        anomalies=anomalies,
    )


@dataclass(frozen=True, slots=True)
class SigningCeremonyPolicy:
    """سياسة مراسم التوقيع: أدنى عدد عوامل، وأنواع لازمة، ومنع البصمة كمفتاح."""

    minimum_factors: int = 2
    required_kinds: tuple[FactorKind, ...] = (
        FactorKind.POSSESSION,
        FactorKind.HUMAN_CONFIRMATION,
    )
    biometric_may_be_sole_factor: bool = False
    notes: tuple[str, ...] = field(default_factory=tuple)

    def evaluate(self, assessment: AuthenticationAssessment) -> tuple[str, ...]:
        """ما نقص عن السياسة — قائمة أسباب، فارغة إذا استُوفيت."""
        gaps: list[str] = []
        if assessment.factor_count < self.minimum_factors:
            gaps.append(
                f"عوامل مستوفاة {assessment.factor_count} والحد الأدنى "
                f"{self.minimum_factors}."
            )
        satisfied_kinds = {f.kind for f in assessment.factors if f.satisfied}
        for required in self.required_kinds:
            if required not in satisfied_kinds:
                gaps.append(f"عامل لازم غائب: {required.value}.")
        if (
            not self.biometric_may_be_sole_factor
            and satisfied_kinds == {FactorKind.BIOMETRIC}
        ):
            gaps.append(
                "البصمة وحدها لا تُثبت قصدًا: بصمة مسروقة لا تساوي ملكًا راضيًا."
            )
        return tuple(gaps)


__all__ = [
    "FORBIDDEN_KEY_MATERIAL",
    "IDENTITY_KINDS",
    "AuthenticationAssessment",
    "BiometricAsKeyError",
    "CrownCommandIdentity",
    "CrownCryptographicIdentity",
    "CrownDeviceIdentity",
    "CrownInstitutionalIdentity",
    "FactorEvidence",
    "FactorKind",
    "HumanSovereignIdentity",
    "IdentityBinding",
    "IdentityConflationError",
    "IdentityError",
    "IdentityGraph",
    "SigningCeremonyPolicy",
    "assert_not_key_material",
    "assess",
]
