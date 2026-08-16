"""الهدف: حماية علاقة الثقة بمفتاح التاج العام — مرساة ثقة لا دائرية، مضادة للتراجع.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المفتاح العام ليس سرًّا (البند الرابع من التوجيه). المحمي هو **الجواب على سؤال:
أي مفتاح عام هو مفتاح التاج الصحيح؟** لأن الخصم لا يحتاج سرقة مفتاح خاص إذا أمكنه
إقناع النظام بمفتاح عام آخر: يستبدل صفًّا في قاعدة بيانات، أو ملفًّا في المستودع،
أو حزمة في سلسلة التوريد، أو أثرًا من آثار CI، أو ردًّا من واجهة، فيصير توقيعه هو
«التوقيع الملكي».

ولذلك مبدأان بنيويان:

1. **لا ثقة دائرية.** لا تُخزَّن مرساة الثقة في نفس المكان الذي تحرسه. قاعدة بيانات
   التطبيق لا تكون هي مصدر الحقيقة عن مفتاح التاج، وإلا فمن اخترق القاعدة صار
   ملكًا. فالمرساة تحتاج مستويات مستقلة عن سيطرة التطبيق: عتاد، أو أصل خارج
   الشبكة، أو إشهاد بشري خارج القناة.

2. **استقلال أصل الثقة عن مفتاح التوقيع** (البند 38). المفتاح الذي يوقّع *بيان
   المفاتيح* ليس هو مفتاح التاج الذي يوقّع *الأوامر*. لو كانا واحدًا لكان بيان
   المفاتيح يُصدّق نفسه: من ملك مفتاح التوقيع أعاد تعريف من يملك مفتاح التوقيع.

وهذه الوحدة لا تدّعي منع كل استبدال. تدّعي أن الاستبدال **يُكتَشف** بمقارنة بصمة
ثابتة، وبمنع الرجوع إلى نسخة بيان أقدم، وباشتراط تثبيت بشري خارج القناة عند أول
ربط وعند كل تغيير في الأصل.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Final

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from core.crown.key_registry import (
    DOMAIN_TAG_MANIFEST,
    CrownKeyRegistry,
    KeyRegistryError,
)

DOMAIN_TAG_ANCHOR: Final[str] = "AMOS-CROWN-TRUST-ANCHOR-v1"


class TrustAnchorError(Exception):
    """خلل في مرساة ثقة التاج."""


class CircularTrustError(TrustAnchorError):
    """المرساة تستند إلى ما تحرسه — ثقة دائرية."""


class AnchorSubstitutionError(TrustAnchorError):
    """بيان المفاتيح لا يطابق المرساة — استبدال أو تسميم إعدادات."""


class RollbackError(TrustAnchorError):
    """محاولة إرجاع بيان المفاتيح إلى نسخة أقدم."""


class DowngradeError(TrustAnchorError):
    """محاولة الهبوط إلى منظومة تعمية أضعف أو إلى بيان بضمانات أقل."""


class OutOfBandVerificationRequiredError(TrustAnchorError):
    """أصل الثقة لم يُثبَّت بشريًّا خارج القناة — لا يُقبل ضمنًا."""


class RootKeyReuseError(TrustAnchorError):
    """مفتاح الأصل هو نفسه مفتاح التوقيع — البيان يُصدّق نفسه."""


class TrustPlane(str, Enum):
    """المستويات التي قد يأتي منها أصل الثقة — ولكل مستوى قدر مخاطرة مختلف."""

    APPLICATION_DATABASE = "APPLICATION_DATABASE"
    REPOSITORY_FILE = "REPOSITORY_FILE"
    RUNTIME_CONFIG = "RUNTIME_CONFIG"
    ENVIRONMENT_VARIABLE = "ENVIRONMENT_VARIABLE"
    PACKAGE_ARTIFACT = "PACKAGE_ARTIFACT"
    CI_ARTIFACT = "CI_ARTIFACT"
    REMOTE_API = "REMOTE_API"
    OFFLINE_ROOT = "OFFLINE_ROOT"
    HARDWARE_ROOT = "HARDWARE_ROOT"
    PRINTED_FINGERPRINT = "PRINTED_FINGERPRINT"
    HUMAN_OUT_OF_BAND = "HUMAN_OUT_OF_BAND"

    @property
    def under_application_control(self) -> bool:
        """هل يستطيع من اخترق التطبيق أن يغيّر هذا المستوى؟

        إن كان الجواب نعم فهذا المستوى لا يصلح أصلًا وحيدًا للثقة، لأنه يسقط
        مع أول اختراق للنظام الذي يُفترض أن المرساة تحرسه.
        """
        return self in {
            TrustPlane.APPLICATION_DATABASE,
            TrustPlane.REPOSITORY_FILE,
            TrustPlane.RUNTIME_CONFIG,
            TrustPlane.ENVIRONMENT_VARIABLE,
            TrustPlane.PACKAGE_ARTIFACT,
            TrustPlane.CI_ARTIFACT,
            TrustPlane.REMOTE_API,
        }

    @property
    def requires_human_step(self) -> bool:
        return self in {
            TrustPlane.PRINTED_FINGERPRINT,
            TrustPlane.HUMAN_OUT_OF_BAND,
            TrustPlane.OFFLINE_ROOT,
        }


# المستويات المستقلة التي يجوز أن تُبنى عليها الثقة الأساسية.
INDEPENDENT_PLANES: Final[frozenset[TrustPlane]] = frozenset(
    p for p in TrustPlane if not p.under_application_control
)


@dataclass(frozen=True, slots=True)
class AnchorSource:
    """موضع واحد أُخذت منه بصمة الأصل — بمستواه وموضعه وما قُرئ منه.

    لا سر هنا: كل ما يُنقَل بصمة عامة وموضع.
    """

    plane: TrustPlane
    locator: str
    fingerprint: str
    verified_at: str = ""
    verifier: str = ""

    def __post_init__(self) -> None:
        if not self.locator:
            raise TrustAnchorError("مصدر مرساة بلا موضع.")
        if len(self.fingerprint) != 64 or not all(
            c in "0123456789abcdef" for c in self.fingerprint.lower()
        ):
            raise TrustAnchorError(
                f"بصمة المصدر «{self.locator}» ليست SHA-256 ست عشرية (64 محرفًا)."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "plane": self.plane.value,
            "locator": self.locator,
            "fingerprint": self.fingerprint.lower(),
            "verified_at": self.verified_at,
            "verifier": self.verifier,
        }


@dataclass(frozen=True, slots=True)
class SignedKeyManifest:
    """بيان مفاتيح موقَّع بمفتاح الأصل — لا بمفتاح التاج نفسه."""

    manifest: dict[str, Any]
    signature_hex: str
    root_key_id: str

    def __post_init__(self) -> None:
        if self.manifest.get("domain") != DOMAIN_TAG_MANIFEST:
            raise TrustAnchorError(
                f"بيان بوسم مجال غير متوقع: {self.manifest.get('domain')!r}"
            )
        if not self.signature_hex:
            raise TrustAnchorError("بيان مفاتيح بلا توقيع.")

    @property
    def manifest_version(self) -> int:
        return int(self.manifest.get("manifest_version", 0))

    def canonical_bytes(self) -> bytes:
        """نفس التمثيل القانوني الذي يُنتجه السجل — وإلا فشل التحقق بلا سبب أمني."""
        body = json.dumps(
            self.manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return DOMAIN_TAG_MANIFEST.encode() + b"\n" + body.encode()

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def registry(self) -> CrownKeyRegistry:
        try:
            return CrownKeyRegistry.from_manifest(self.manifest)
        except KeyRegistryError as exc:
            raise AnchorSubstitutionError(f"بيان مفاتيح غير سليم: {exc}") from exc


@dataclass(frozen=True, slots=True)
class AnchorObservation:
    """ما رآه النظام آخر مرة — أساس كشف التراجع والاستبدال الصامت."""

    manifest_version: int
    manifest_digest: str
    active_key_fingerprint: str
    observed_at: str
    previous_observation_hash: str = ""

    def entry_hash(self) -> str:
        """سلسلة تجزئة: كل مشاهدة تشدّ ما قبلها، فلا تُحذَف مشاهدة بصمت."""
        payload = (
            f"{self.previous_observation_hash}|{self.manifest_version}|"
            f"{self.manifest_digest}|{self.active_key_fingerprint}|{self.observed_at}"
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "manifest_digest": self.manifest_digest,
            "active_key_fingerprint": self.active_key_fingerprint,
            "observed_at": self.observed_at,
            "previous_observation_hash": self.previous_observation_hash,
            "entry_hash": self.entry_hash(),
        }


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class CrownTrustAnchor:
    """مرساة ثقة التاج: بصمة أصل ثابتة + مصادر مستقلة + منع تراجع + سلسلة مشاهدات.

    عقد هذه المرساة صريح:

    - تقبل بيان مفاتيح إن وإن فقط: توقيعه صحيح بمفتاح الأصل، ونسخته ليست أقدم
      من آخر مشاهدة، وبصمة مفتاحه النشط مثبَّتة أو التغيير مُصرَّح به بمراسم،
      وأصلها مُثبَّت خارج القناة.
    - لا تقبل أن يكون مفتاح الأصل هو مفتاح التاج (البند 38).
    - لا تقبل أن تكون كل مصادرها تحت سيطرة التطبيق (البند 4).
    """

    def __init__(
        self,
        *,
        root_id: str,
        root_public_key_hex: str,
        sources: tuple[AnchorSource, ...],
        established_at: str | None = None,
        pinned_active_fingerprint: str = "",
        minimum_manifest_version: int = 1,
        require_out_of_band: bool = True,
    ) -> None:
        if not root_id:
            raise TrustAnchorError("مرساة بلا معرّف أصل.")
        try:
            raw = bytes.fromhex(root_public_key_hex)
        except ValueError as exc:
            raise TrustAnchorError(f"مفتاح الأصل العام غير صالح: {exc}") from exc
        if len(raw) != 32:
            raise TrustAnchorError(
                f"مفتاح أصل Ed25519 طوله {len(raw)} بايت والمطلوب 32."
            )
        if not sources:
            raise TrustAnchorError("مرساة بلا مصادر ليست مرساة.")

        self.root_id = root_id
        self.root_public_key_hex = root_public_key_hex.lower()
        self._sources = tuple(sources)
        self.established_at = established_at or _now()
        self.pinned_active_fingerprint = pinned_active_fingerprint.lower()
        self.minimum_manifest_version = minimum_manifest_version
        self.require_out_of_band = require_out_of_band
        self._observations: list[AnchorObservation] = []

        self.assert_not_circular()

    # ── هوية الأصل ────────────────────────────────────────────────────────

    @property
    def root_fingerprint(self) -> str:
        """بصمة الأصل الثابتة — هي ما يُطبَع ويُقرأ صوتيًّا ويُثبَّت خارج القناة."""
        return hashlib.sha256(
            f"{DOMAIN_TAG_ANCHOR}:{self.root_id}:{self.root_public_key_hex}".encode()
        ).hexdigest()

    @property
    def sources(self) -> tuple[AnchorSource, ...]:
        return self._sources

    @property
    def independent_sources(self) -> tuple[AnchorSource, ...]:
        return tuple(s for s in self._sources if s.plane in INDEPENDENT_PLANES)

    @property
    def out_of_band_confirmed(self) -> bool:
        return any(
            s.plane.requires_human_step and s.verified_at and s.verifier
            for s in self._sources
        )

    def assert_not_circular(self) -> None:
        """ارفض مرساة كل مصادرها تحت سيطرة التطبيق، ومرساة مصادرها متناقضة."""
        if not self.independent_sources:
            planes = ", ".join(sorted({s.plane.value for s in self._sources}))
            raise CircularTrustError(
                "كل مصادر المرساة تحت سيطرة التطبيق "
                f"({planes}). من اخترق التطبيق يعيد تعريف مفتاح التاج، "
                "فالثقة دائرية. يلزم مصدر مستقل: عتاد، أو أصل خارج الشبكة، "
                "أو تثبيت بشري خارج القناة."
            )
        digests = {s.fingerprint.lower() for s in self._sources}
        if len(digests) > 1:
            detail = "; ".join(
                f"{s.plane.value}@{s.locator}={s.fingerprint[:12]}…" for s in self._sources
            )
            raise AnchorSubstitutionError(
                f"مصادر المرساة غير متسقة — {detail}. "
                "اختلاف البصمات بين المستويات دليل تسميم أحدها."
            )
        recorded = next(iter(digests))
        if not hmac.compare_digest(recorded, self.root_fingerprint):
            raise AnchorSubstitutionError(
                "بصمة المصادر لا تطابق بصمة مفتاح الأصل المحسوبة — استبدال أصل ثقة."
            )

    def assert_root_independent_of(self, registry: CrownKeyRegistry) -> None:
        """مفتاح الأصل لا يكون أحد مفاتيح التاج (البند 38)."""
        for record in registry.records:
            if record.public_key_hex.lower() == self.root_public_key_hex:
                raise RootKeyReuseError(
                    f"مفتاح الأصل هو نفسه مفتاح التاج «{record.key_id}». "
                    "حينها يُصدّق بيان المفاتيح نفسه: من ملك مفتاح التوقيع "
                    "أعاد تعريف من يملك مفتاح التوقيع."
                )

    # ── التحقق ────────────────────────────────────────────────────────────

    def _verify_signature(self, signed: SignedKeyManifest) -> None:
        if signed.root_key_id != self.root_id:
            raise AnchorSubstitutionError(
                f"البيان موقَّع بأصل «{signed.root_key_id}» والمرساة أصلها "
                f"«{self.root_id}»."
            )
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(self.root_public_key_hex)
        )
        try:
            public_key.verify(
                bytes.fromhex(signed.signature_hex), signed.canonical_bytes()
            )
        except (InvalidSignature, ValueError) as exc:
            raise AnchorSubstitutionError(
                "توقيع بيان المفاتيح غير صحيح مقابل مفتاح الأصل — "
                f"بيان مُلفَّق أو معبوث به ({exc.__class__.__name__})."
            ) from exc

    def _assert_no_rollback(self, signed: SignedKeyManifest) -> None:
        if signed.manifest_version < self.minimum_manifest_version:
            raise DowngradeError(
                f"نسخة البيان {signed.manifest_version} أدنى من الحد الأدنى "
                f"{self.minimum_manifest_version} — هبوط إلى ضمانات أقل."
            )
        last = self.last_observation
        if last is None:
            return
        if signed.manifest_version < last.manifest_version:
            raise RollbackError(
                f"البيان المعروض نسخته {signed.manifest_version} وآخر مشاهدة "
                f"{last.manifest_version} — إرجاع إلى ماضٍ (rollback)."
            )
        if (
            signed.manifest_version == last.manifest_version
            and signed.digest != last.manifest_digest
        ):
            raise AnchorSubstitutionError(
                f"نسخة البيان {signed.manifest_version} كما هي وبصمته تغيّرت — "
                "تعديل صامت على نفس النسخة."
            )

    def _assert_pin(self, registry: CrownKeyRegistry) -> None:
        active = registry.active()
        if active is None:
            raise AnchorSubstitutionError(
                "بيان بلا مفتاح نشط لا يُقبل كأساس للتحقق. "
                "غياب النشط يُجمِّد الاختصاص ولا يُنشئ مفتاحًا بديلًا."
            )
        if self.pinned_active_fingerprint and not hmac.compare_digest(
            self.pinned_active_fingerprint, active.fingerprint
        ):
            raise AnchorSubstitutionError(
                f"بصمة المفتاح النشط «{active.key_id}» لا تطابق البصمة المثبَّتة "
                "في المرساة. تغيير المفتاح النشط لا يمر إلا بمراسم تدوير معلنة "
                "تُحدِّث التثبيت."
            )

    def verify_manifest(self, signed: SignedKeyManifest) -> CrownKeyRegistry:
        """البوابة الكاملة: توقيع، ثم عدم تراجع، ثم استقلال أصل، ثم تثبيت، ثم مشاهدة.

        ترتيب الفحوص مقصود: لا نستخرج سجلًّا من بيان قبل التحقق من توقيعه، ولا
        نُثبت مشاهدة قبل نجاح كل الفحوص — فلا يُلوَّث السجل ببيان مرفوض.
        """
        if self.require_out_of_band and not self.out_of_band_confirmed:
            raise OutOfBandVerificationRequiredError(
                f"بصمة الأصل {self.root_fingerprint[:16]}… لم تُثبَّت خارج القناة "
                "بإشهاد بشري. تثبيت أول مرة لا يُستنتَج من الشبكة، وإلا فمن يسيطر "
                "على الشبكة يسيطر على مَن هو الملك."
            )
        self._verify_signature(signed)
        self._assert_no_rollback(signed)
        registry = signed.registry()
        registry.validate()
        self.assert_root_independent_of(registry)
        self._assert_pin(registry)

        active = registry.active_or_raise()
        if signed.digest != CrownKeyRegistry.from_manifest(
            signed.manifest
        ).manifest_digest():
            raise AnchorSubstitutionError(
                "بصمة البيان المعروض لا تطابق بصمة السجل المُعاد بناؤه منه."
            )
        self.record_observation(
            manifest_version=signed.manifest_version,
            manifest_digest=signed.digest,
            active_key_fingerprint=active.fingerprint,
        )
        return registry

    # ── سلسلة المشاهدات ───────────────────────────────────────────────────

    @property
    def observations(self) -> tuple[AnchorObservation, ...]:
        return tuple(self._observations)

    @property
    def last_observation(self) -> AnchorObservation | None:
        return self._observations[-1] if self._observations else None

    def record_observation(
        self,
        *,
        manifest_version: int,
        manifest_digest: str,
        active_key_fingerprint: str,
        at: str | None = None,
    ) -> AnchorObservation:
        last = self.last_observation
        observation = AnchorObservation(
            manifest_version=manifest_version,
            manifest_digest=manifest_digest,
            active_key_fingerprint=active_key_fingerprint,
            observed_at=at or _now(),
            previous_observation_hash=(last.entry_hash() if last else ""),
        )
        self._observations.append(observation)
        if manifest_version > self.minimum_manifest_version:
            self.minimum_manifest_version = manifest_version
        return observation

    def verify_observation_chain(self) -> None:
        """تحقق سلسلة المشاهدات — حذف مشاهدة أو تعديلها يكسر التجزئة."""
        previous = ""
        for index, obs in enumerate(self._observations):
            if obs.previous_observation_hash != previous:
                raise AnchorSubstitutionError(
                    f"سلسلة مشاهدات المرساة مكسورة عند المشاهدة {index}."
                )
            previous = obs.entry_hash()

    # ── مراسم تحديث التثبيت ───────────────────────────────────────────────

    def rotate_pin(
        self, *, new_fingerprint: str, ceremony_id: str, witness: str
    ) -> None:
        """حدّث البصمة المثبَّتة بمراسم معلنة — لا تلقائيًّا ولا صامتًا.

        بغير مراسم يصير التثبيت بلا معنى: كل استبدال «يُحدِّث التثبيت» فيُقبَل.
        """
        if not ceremony_id or not witness:
            raise TrustAnchorError(
                "تحديث التثبيت يلزمه معرّف مراسم وإشهاد بشري. "
                "تحديث تلقائي للتثبيت يُفرغه من معناه."
            )
        if len(new_fingerprint) != 64:
            raise TrustAnchorError("البصمة الجديدة ليست SHA-256 ست عشرية.")
        self.pinned_active_fingerprint = new_fingerprint.lower()

    # ── تسلسل عام ─────────────────────────────────────────────────────────

    def public_descriptor(self) -> dict[str, Any]:
        """وصف عام قابل للنشر — بصمات ومواضع، بلا مواد سرية."""
        return {
            "domain": DOMAIN_TAG_ANCHOR,
            "root_id": self.root_id,
            "root_fingerprint": self.root_fingerprint,
            "established_at": self.established_at,
            "minimum_manifest_version": self.minimum_manifest_version,
            "pinned_active_fingerprint": self.pinned_active_fingerprint,
            "require_out_of_band": self.require_out_of_band,
            "out_of_band_confirmed": self.out_of_band_confirmed,
            "sources": [s.as_dict() for s in self._sources],
            "independent_source_count": len(self.independent_sources),
            "observations": [o.as_dict() for o in self._observations],
        }

    def write_descriptor(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.public_descriptor(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path


@dataclass(frozen=True, slots=True)
class SubstitutionVector:
    """طريق استبدال معروف، وكيف تُكتشف، وما لا تكفيه البرمجيات وحدها.

    وجود عمود «الحد» مقصود: البرمجيات تكشف التناقض، ولا تمنع من يملك المستوى
    كله من تغييره. والاعتراف بالحد أصدق من دعوى منعٍ لا يوجد.
    """

    vector_id: str
    name: str
    plane: TrustPlane
    detection: str
    software_limit: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "vector_id": self.vector_id,
            "name": self.name,
            "plane": self.plane.value,
            "detection": self.detection,
            "software_limit": self.software_limit,
        }


SUBSTITUTION_VECTORS: Final[tuple[SubstitutionVector, ...]] = (
    SubstitutionVector(
        "SUB-01",
        "استبدال غير مصرَّح به لمفتاح عام",
        TrustPlane.APPLICATION_DATABASE,
        "مقارنة بصمة المفتاح النشط بالبصمة المثبَّتة في المرساة.",
        "من يملك المرساة والقاعدة معًا يغيّر الاثنين؛ لذا يلزم مصدر مستقل.",
    ),
    SubstitutionVector(
        "SUB-02",
        "تعديل صامت على نفس نسخة البيان",
        TrustPlane.REPOSITORY_FILE,
        "نفس manifest_version ببصمة مختلفة ⇒ رفض.",
        "لا يُكشف إلا إذا كانت هناك مشاهدة سابقة محفوظة.",
    ),
    SubstitutionVector(
        "SUB-03",
        "تسميم الإعدادات",
        TrustPlane.RUNTIME_CONFIG,
        "الإعداد ليس مصدر ثقة مستقلًّا؛ يُقارَن بالمصدر المستقل.",
        "لا يمنع تعطيل الخدمة، بل يمنع قبول مفتاح مُسمَّم.",
    ),
    SubstitutionVector(
        "SUB-04",
        "إبدال قاعدة البيانات كاملة",
        TrustPlane.APPLICATION_DATABASE,
        "التراجع في نسخة البيان وكسر سلسلة المشاهدات.",
        "قاعدة جديدة بلا مشاهدات تبدو «أول تشغيل» — لذا التثبيت البشري لازم.",
    ),
    SubstitutionVector(
        "SUB-05",
        "إبدال عبر DNS أو واجهة بعيدة",
        TrustPlane.REMOTE_API,
        "الواجهة البعيدة مستوى غير مستقل ولا يُقبل أصلًا وحيدًا.",
        "لا حماية إن كان التثبيت نفسه يُجلَب من الشبكة.",
    ),
    SubstitutionVector(
        "SUB-06",
        "إبدال في المستودع",
        TrustPlane.REPOSITORY_FILE,
        "توقيع الأصل على البيان + بصمة مطبوعة خارج المستودع.",
        "من يملك المستودع ومفتاح الأصل يوقّع بيانًا صحيحًا.",
    ),
    SubstitutionVector(
        "SUB-07",
        "إبدال أثر CI",
        TrustPlane.CI_ARTIFACT,
        "التحقق من التوقيع عند التشغيل لا عند البناء.",
        "من يملك مفتاح الأصل داخل CI يوقّع؛ لذا الأصل يبقى خارج CI.",
    ),
    SubstitutionVector(
        "SUB-08",
        "إبدال حزمة (سلسلة توريد)",
        TrustPlane.PACKAGE_ARTIFACT,
        "المرساة لا تُقرأ من حزمة قابلة للتحديث تلقائيًّا.",
        "حزمة مخترقة تعطّل الفحص؛ الحماية بالمستوى المستقل لا بالكود.",
    ),
    SubstitutionVector(
        "SUB-09",
        "حقن في زمن التشغيل",
        TrustPlane.RUNTIME_CONFIG,
        "إعادة التحقق عند كل أمر لا مرة واحدة عند الإقلاع.",
        "من نفّذ كودًا داخل العملية يعبث بالذاكرة؛ الحد معلن لا مُنكَر.",
    ),
    SubstitutionVector(
        "SUB-10",
        "ترحيل خبيث لقاعدة البيانات",
        TrustPlane.APPLICATION_DATABASE,
        "الترحيل لا يملك تغيير التثبيت؛ التغيير بمراسم ذات إشهاد.",
        "ترحيل بصلاحية كاملة على كل المستويات يتجاوز؛ لذا تُفصل الصلاحيات.",
    ),
    SubstitutionVector(
        "SUB-11",
        "تغيير إعدادات غير مصرَّح به",
        TrustPlane.ENVIRONMENT_VARIABLE,
        "متغيرات البيئة ليست مصدر ثقة، ورفضها معماري لا اختياري.",
        "لا يمنع تعطيلًا، بل يمنع ترقية إعداد إلى أصل ثقة.",
    ),
)


def substitution_matrix() -> tuple[dict[str, Any], ...]:
    """مصفوفة طرق الاستبدال — للتوثيق وبوابات CI."""
    return tuple(v.as_dict() for v in SUBSTITUTION_VECTORS)


__all__ = [
    "DOMAIN_TAG_ANCHOR",
    "INDEPENDENT_PLANES",
    "SUBSTITUTION_VECTORS",
    "AnchorObservation",
    "AnchorSource",
    "AnchorSubstitutionError",
    "CircularTrustError",
    "CrownTrustAnchor",
    "DowngradeError",
    "OutOfBandVerificationRequiredError",
    "RollbackError",
    "RootKeyReuseError",
    "SignedKeyManifest",
    "SubstitutionVector",
    "TrustAnchorError",
    "TrustPlane",
    "substitution_matrix",
]
