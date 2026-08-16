"""الهدف: بيئة توقيع التاج — المفتاح لا يخرج منها، ولا مادة إنتاجية في المستودع.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

البند الخامس من التوجيه يمنع وجود مادة توقيع إنتاجية في المستودع، أو في متغيرات
البيئة، أو في صور الحاويات، أو في صفوف قاعدة بيانات عادية، أو في نُسخ احتياطية
نصية، أو في السجلات، أو في آثار CI، أو في ذاكرة التطبيق أطول من اللازم، أو في
تجهيزات الاختبار.

فما الذي يبقى في المستودع؟ **البروتوكول** لا المادة: واجهة توقيع مجرَّدة، وبيانات
عامة، ومنطق تحقق، ومخططات، ومراجع، ومفاتيح اختبار عابرة تُولَّد في الذاكرة وتموت
مع العملية.

وأصدق ما في هذه الوحدة: بيئة الإنتاج (وحدة أمان عتادية أو جهاز توقيع مخصص)
**ليست منفَّذة هنا**، لأن تنفيذها يلزمه عتاد لا وجود له في هذا المستودع. فمرجعها
معلن، ونداء التوقيع عليه يرفع استثناءً صريحًا يقول ما ينقص. ولا يُدَّعى عمل ما
لا يعمل.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Final

from cryptography.hazmat.primitives.asymmetric import ed25519


class KeystoreError(Exception):
    """خلل في بيئة توقيع التاج."""


class KeyMaterialLeakError(KeystoreError):
    """محاولة إخراج مادة التوقيع من بيئتها — ممنوعة بنيويًّا."""


class ProductionKeystoreUnavailableError(KeystoreError):
    """بيئة توقيع إنتاجية مرجَعية بلا عتاد متصل — لا تُحاكى ولا تُدَّعى."""


class TestKeystoreInProductionError(KeystoreError):
    """بيئة اختبار استُدعيت في سياق إنتاجي."""


class KeystoreKind(str, Enum):
    """أنواع بيئات التوقيع المقبولة معماريًّا."""

    HSM = "HSM"
    HARDWARE_BACKED = "HARDWARE_BACKED"
    SECURE_ELEMENT = "SECURE_ELEMENT"
    SIGNING_APPLIANCE = "SIGNING_APPLIANCE"
    OFFLINE_ROOT = "OFFLINE_ROOT"
    AIR_GAPPED_CEREMONY = "AIR_GAPPED_CEREMONY"
    TEST_EPHEMERAL = "TEST_EPHEMERAL"

    @property
    def production_permitted(self) -> bool:
        return self is not KeystoreKind.TEST_EPHEMERAL

    @property
    def implemented_here(self) -> bool:
        """أي الأنواع لها تنفيذ فعلي في هذا المستودع؟ واحد فقط: الاختباري."""
        return self is KeystoreKind.TEST_EPHEMERAL


# المواضع التي لا تُحفَظ فيها مادة توقيع التاج بأي حال (البند 5).
FORBIDDEN_MATERIAL_LOCATIONS: Final[tuple[str, ...]] = (
    "source_files",
    "environment_variables",
    "container_images",
    "ordinary_filesystem_config",
    "sql_rows",
    "plaintext_backups",
    "logs",
    "ci_artifacts",
    "application_memory_beyond_need",
    "test_fixtures_with_production_material",
)

# ما يجوز وجوده في المستودع (البند 5).
PERMITTED_REPOSITORY_CONTENT: Final[tuple[str, ...]] = (
    "protocols",
    "public_metadata",
    "verification_logic",
    "schemas",
    "references",
    "test_only_ephemeral_keys",
)


@dataclass(frozen=True, slots=True)
class KeystoreCapabilities:
    """ما تضمنه بيئة التوقيع فعلًا — بلا مبالغة ولا نفي.

    كل حقل هنا سؤال يُسأل قبل الوثوق ببيئة: هل المادة غير قابلة للتصدير؟ وهل
    يلزم تأكيد مادي على العتاد؟ وهل يُصدَر إشهاد يمكن التحقق منه؟
    """

    key_non_exportable: bool
    hardware_attestation: bool
    requires_physical_confirmation: bool
    offline_capable: bool
    tamper_evident: bool
    rate_limited: bool
    production_permitted: bool
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "key_non_exportable": self.key_non_exportable,
            "hardware_attestation": self.hardware_attestation,
            "requires_physical_confirmation": self.requires_physical_confirmation,
            "offline_capable": self.offline_capable,
            "tamper_evident": self.tamper_evident,
            "rate_limited": self.rate_limited,
            "production_permitted": self.production_permitted,
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class SigningRequest:
    """طلب توقيع: البايتات القانونية ووسم مجالها ومعرّف الأمر.

    وسم المجال إلزامي: بلا فصل مجالات يصير توقيع بيان مفاتيح صالحًا كتوقيع أمر.
    """

    domain_tag: str
    payload: bytes
    command_id: str = ""

    def __post_init__(self) -> None:
        if not self.domain_tag:
            raise KeystoreError("طلب توقيع بلا وسم مجال.")
        if not self.payload:
            raise KeystoreError("طلب توقيع بلا حمولة.")
        if not self.payload.startswith(self.domain_tag.encode()):
            raise KeystoreError(
                f"حمولة الطلب لا تبدأ بوسم المجال «{self.domain_tag}» — "
                "خلط مجالات التوقيع."
            )

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.payload).hexdigest()


@dataclass(frozen=True, slots=True)
class SigningResult:
    """نتيجة توقيع: التوقيع ومعرّف المفتاح وبصمة الحمولة ومرجع الإشهاد.

    لا يوجد حقل يحمل مادة توقيع — وهذا مقصود ومُفحوص في الاختبارات.
    """

    signature_hex: str
    key_id: str
    payload_digest: str
    keystore_kind: KeystoreKind
    attestation_ref: str = ""


class CrownKeystore(ABC):
    """واجهة بيئة توقيع التاج. لا طريقة لتصدير المادة — الغياب هو الضمان.

    إضافة دالة تصدير إلى هذه الواجهة نقض للبند الخامس، ولذلك لا توجد، ولذلك
    يوجد ``assert_no_export_surface`` ليمنع إدخالها لاحقًا من باب خلفي.
    """

    kind: KeystoreKind
    key_id: str

    @property
    @abstractmethod
    def capabilities(self) -> KeystoreCapabilities:
        """ما تضمنه هذه البيئة فعلًا."""

    @abstractmethod
    def public_key_hex(self) -> str:
        """المفتاح العام — عام بطبعه ونشره لا يضر."""

    @abstractmethod
    def sign(self, request: SigningRequest) -> SigningResult:
        """وقّع داخل البيئة. المادة لا تخرج، والخارج توقيع فقط."""

    def assert_production_ready(self) -> None:
        """ارفض بيئة اختبار في سياق إنتاجي."""
        if not self.kind.production_permitted:
            raise TestKeystoreInProductionError(
                f"بيئة «{self.kind.value}» للاختبار فقط. "
                "مفاتيح الاختبار العابرة لا تُوقّع قرارًا سياديًّا."
            )

    def assert_no_export_surface(self) -> None:
        """تحقق ألّا سبيل معلن لإخراج المادة — لا الآن ولا بإضافة لاحقة.

        الفحص بالأسماء لأن الباب الخلفي يُفتَح عادةً بدالة «مفيدة»: تصدير للنسخ
        الاحتياطي، أو استخراج للترحيل، أو كشف للتشخيص.
        """
        forbidden = (
            "export_key",
            "export_material",
            "extract_key",
            "reveal_key",
            "dump_key",
            "get_signing_material",
            "raw_key",
            "key_bytes",
            "unwrap_key",
        )
        found = [name for name in forbidden if hasattr(self, name)]
        if found:
            raise KeyMaterialLeakError(
                f"بيئة التوقيع تعرض سبيل إخراج للمادة: {', '.join(found)}."
            )


class ReferenceProductionKeystore(CrownKeystore):
    """مرجع بيئة إنتاجية: يصف عتادًا ولا يحاكيه.

    لماذا لا يحاكي؟ لأن محاكاة وحدة أمان عتادية في برمجية تنتج شيئًا واحدًا:
    مادة توقيع داخل ذاكرة التطبيق. وهذا بعينه ما يمنعه البند الخامس. فالمرجع
    يحمل معرّفات ومواصفات، ونداء التوقيع عليه يرفع استثناءً يقول ما ينقص.
    """

    def __init__(
        self,
        *,
        kind: KeystoreKind,
        key_id: str,
        endpoint_ref: str,
        slot_ref: str = "",
        attestation_ref: str = "",
        published_public_key_hex: str = "",
        capabilities: KeystoreCapabilities | None = None,
    ) -> None:
        if kind is KeystoreKind.TEST_EPHEMERAL:
            raise KeystoreError("المرجع الإنتاجي لا يكون من نوع اختباري.")
        if not endpoint_ref:
            raise KeystoreError("مرجع بيئة إنتاجية بلا مرجع نقطة وصول.")
        self.kind = kind
        self.key_id = key_id
        self.endpoint_ref = endpoint_ref
        self.slot_ref = slot_ref
        self.attestation_ref = attestation_ref
        self._published_public_key_hex = published_public_key_hex.lower()
        self._capabilities = capabilities or KeystoreCapabilities(
            key_non_exportable=True,
            hardware_attestation=True,
            requires_physical_confirmation=True,
            offline_capable=kind
            in {KeystoreKind.OFFLINE_ROOT, KeystoreKind.AIR_GAPPED_CEREMONY},
            tamper_evident=True,
            rate_limited=True,
            production_permitted=True,
            notes="مواصفات معلنة لعتاد خارجي — غير محقَّقة برمجيًّا في هذا المستودع.",
        )

    @property
    def capabilities(self) -> KeystoreCapabilities:
        return self._capabilities

    @property
    def implemented(self) -> bool:
        """صريح: لا تنفيذ تشغيليًّا لهذه البيئة داخل المستودع."""
        return False

    def public_key_hex(self) -> str:
        if not self._published_public_key_hex:
            raise ProductionKeystoreUnavailableError(
                f"لا مفتاح عام منشور للمرجع «{self.key_id}». "
                "يُنشر بعد مراسم توليد على العتاد، ويُثبَّت خارج القناة."
            )
        return self._published_public_key_hex

    def sign(self, request: SigningRequest) -> SigningResult:
        raise ProductionKeystoreUnavailableError(
            f"التوقيع عبر «{self.kind.value}» يلزمه عتاد متصل عند "
            f"{self.endpoint_ref}"
            + (f" (الفتحة {self.slot_ref})" if self.slot_ref else "")
            + f". طلب المجال «{request.domain_tag}» ببصمة {request.digest[:12]}… "
            "غير موقَّع. هذه الوحدة تصف العتاد ولا تحاكيه: محاكاته تعني وضع "
            "مادة التوقيع في ذاكرة التطبيق، وهو الممنوع عينه."
        )

    def descriptor(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "key_id": self.key_id,
            "endpoint_ref": self.endpoint_ref,
            "slot_ref": self.slot_ref,
            "attestation_ref": self.attestation_ref,
            "implemented_in_repository": False,
            "capabilities": self.capabilities.as_dict(),
        }


class EphemeralTestKeystore(CrownKeystore):
    """بيئة اختبار عابرة: تولّد زوجًا في الذاكرة ولا تكتبه على قرص أبدًا.

    وجودها ضروري لاختبار منطق التحقق بتوقيعات حقيقية لا مزيَّفة. وحدّها معلن:
    ``production_permitted=False``، فأي مسار إنتاجي يستدعيها يُرفَض.
    """

    def __init__(self, *, key_id: str = "test-ephemeral") -> None:
        self.kind = KeystoreKind.TEST_EPHEMERAL
        self.key_id = key_id
        self._signer = ed25519.Ed25519PrivateKey.generate()
        self._signature_count = 0

    @property
    def capabilities(self) -> KeystoreCapabilities:
        return KeystoreCapabilities(
            key_non_exportable=True,
            hardware_attestation=False,
            requires_physical_confirmation=False,
            offline_capable=False,
            tamper_evident=False,
            rate_limited=False,
            production_permitted=False,
            notes="مادة عابرة في الذاكرة تموت مع العملية — للاختبار وحده.",
        )

    def public_key_hex(self) -> str:
        from cryptography.hazmat.primitives import serialization

        return (
            self._signer.public_key()
            .public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            .hex()
        )

    def sign(self, request: SigningRequest) -> SigningResult:
        signature = self._signer.sign(request.payload)
        self._signature_count += 1
        return SigningResult(
            signature_hex=signature.hex(),
            key_id=self.key_id,
            payload_digest=request.digest,
            keystore_kind=self.kind,
            attestation_ref="",
        )

    @property
    def signature_count(self) -> int:
        """عدد التوقيعات — يُستعمل في اختبارات مكافحة إعادة الإرسال."""
        return self._signature_count


@dataclass(frozen=True, slots=True)
class ContinuityEnvironment:
    """بيئة من بيئات الاستمرارية الأربع (البند 8) بحدودها المعلنة.

    والحد الأهم: ``may_become_replacement_authority=False`` في كل واحدة. البيئة
    الثانوية تُوقّع بأمر التاج، ولا تصير تاجًا لأن الأولى انقطعت.
    """

    environment_id: str
    role: str
    keystore_kind: KeystoreKind
    activation_requires_human_ceremony: bool = True
    may_become_replacement_authority: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if self.may_become_replacement_authority:
            raise KeystoreError(
                f"البيئة «{self.environment_id}» تدّعي أنها قد تصير سلطة بديلة. "
                "بيئة احتياطية لا تصير ملكًا بديلًا صامتًا (البند 8)."
            )
        if not self.activation_requires_human_ceremony:
            raise KeystoreError(
                f"البيئة «{self.environment_id}» تُنشَّط بلا مراسم بشرية — "
                "تفويض تلقائي غير مضبوط."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "environment_id": self.environment_id,
            "role": self.role,
            "keystore_kind": self.keystore_kind.value,
            "activation_requires_human_ceremony": True,
            "may_become_replacement_authority": False,
            "notes": self.notes,
        }


CONTINUITY_ENVIRONMENTS: Final[tuple[ContinuityEnvironment, ...]] = (
    ContinuityEnvironment(
        "ENV-PRIMARY",
        "بيئة توقيع التاج الأساسية",
        KeystoreKind.HSM,
        notes="المسار المعتاد للأوامر الملكية.",
    ),
    ContinuityEnvironment(
        "ENV-SECONDARY",
        "بيئة آمنة ثانوية",
        KeystoreKind.SECURE_ELEMENT,
        notes="تُستخدم عند تعذّر الأساسية، بمفتاح مسجَّل في نفس النسب.",
    ),
    ContinuityEnvironment(
        "ENV-EMERGENCY",
        "مراسم طوارئ خارج الشبكة",
        KeystoreKind.AIR_GAPPED_CEREMONY,
        notes="توقيع خارج الشبكة ونقل التوقيع فقط — لا اتصال ولا مادة.",
    ),
    ContinuityEnvironment(
        "ENV-RECOVERY",
        "بيئة استرداد",
        KeystoreKind.OFFLINE_ROOT,
        notes="لإعادة تأسيس النسب بعد فقد الوصول، بإشهاد متعدد.",
    ),
)


def assert_no_material_in(location: str) -> None:
    """ارفض أي موضع من مواضع الحظر العشرة."""
    normalized = location.strip().lower().replace(" ", "_").replace("-", "_")
    if normalized in FORBIDDEN_MATERIAL_LOCATIONS:
        raise KeyMaterialLeakError(
            f"مادة توقيع التاج لا تُحفَظ في «{location}» بأي حال (البند 5). "
            "تبقى داخل عتاد أمني، ويبقى في المستودع البروتوكول والتحقق فقط."
        )


__all__ = [
    "CONTINUITY_ENVIRONMENTS",
    "FORBIDDEN_MATERIAL_LOCATIONS",
    "PERMITTED_REPOSITORY_CONTENT",
    "ContinuityEnvironment",
    "CrownKeystore",
    "EphemeralTestKeystore",
    "KeyMaterialLeakError",
    "KeystoreCapabilities",
    "KeystoreError",
    "KeystoreKind",
    "ProductionKeystoreUnavailableError",
    "ReferenceProductionKeystore",
    "SigningRequest",
    "SigningResult",
    "TestKeystoreInProductionError",
    "assert_no_material_in",
]
