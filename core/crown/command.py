"""الهدف: تغليف الأمر الملكي وربط التوقيع بسياقه ومنع إعادة إرساله وتحريفه.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

خطران مختلفان يعالجهما هذا الملف، ولا يكفي علاج أحدهما:

1. **إعادة الإرسال** (البند 18): أمر ملكي صحيح يُنفَّذ مرتين. التوقيع سليم في
   المرتين — فالرياضيات لا تعرف «مرة أخرى». الذي يعرفها سجل نونسات وتسلسل
   رقابي ونافذة صلاحية.

2. **تحريف السياق** (البند 19): أخذ توقيع صحيح على الأمر «أ» وإلحاقه بالأمر
   «ب» بتغيير حقل لم يدخل في التوقيع. علاجه أن يُوقَّع **الغلاف كاملًا** بتمثيل
   قانوني وحيد ووسم مجال — فلا يوجد حقل حسّاس خارج التوقيع، ولا يُقرأ توقيع
   مجالٍ في مجال آخر.

والقاعدة الحاكمة للتحقق: كل حقل حسّاس أمنيًّا داخل التوقيع، وما خرج من التوقيع
لا يُعتَدّ به في القرار. ولذلك الغلاف هنا مُجمَّد، وأي بيانات مصاحبة غير موقَّعة
تُعامَل كتعليق لا كأمر.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Final

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from core.crown.key_registry import CrownKeyRegistry, CrownKeyRecord, KeyState

DOMAIN_TAG_COMMAND: Final[str] = "AMOS-CROWN-COMMAND-v1"

# حقول ممنوعة في البيانات غير الموقَّعة: من احتاجها فليضعها داخل الغلاف.
FORBIDDEN_UNSIGNED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "action",
        "target",
        "actor",
        "authority",
        "layer",
        "scope",
        "amount",
        "force",
        "bypass",
        "override",
        "skip_check",
        "no_verify",
        "unchecked",
        "emergency",
        "as_king",
        "on_behalf_of_crown",
    }
)


class CommandError(Exception):
    """خلل في أمر ملكي."""


class ReplayError(CommandError):
    """أمر ملكي مُعاد إرساله — نفس المعرّف أو النونس أو تسلسل راجع."""


class ContextTamperError(CommandError):
    """تغيير سياق أمر موقَّع — نقل توقيع من أمر إلى آخر."""


class ExpiredCommandError(CommandError):
    """أمر خارج نافذة صلاحيته."""


class SignatureError(CommandError):
    """توقيع غير صحيح أو بمفتاح لا صفة له."""


class UnsignedFieldError(CommandError):
    """حقل حسّاس خارج نطاق التوقيع."""


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _parse(moment: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(moment)
    except ValueError as exc:
        raise CommandError(f"وقت غير صالح «{moment}»: {exc}") from exc
    if parsed.tzinfo is None:
        raise CommandError(
            f"الوقت «{moment}» بلا منطقة زمنية. الأوقات الغامضة تفتح نوافذ تحريف."
        )
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class RoyalCommandEnvelope:
    """غلاف الأمر الملكي — كل حقل هنا داخل التوقيع، بلا استثناء.

    ``previous_command_hash`` يربط الأمر بسلسلة الأوامر حيث يلزم الترتيب، فلا
    يُنفَّذ أمر لاحق قبل سابقه ولا يُحذَف من بينهما أمر بصمت.
    """

    command_id: str
    action: str
    target: str
    issuer_key_id: str
    nonce: str
    sequence: int
    issued_at: str
    valid_until: str
    payload: dict[str, Any] = field(default_factory=dict)
    previous_command_hash: str = ""
    context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name, value in (
            ("command_id", self.command_id),
            ("action", self.action),
            ("issuer_key_id", self.issuer_key_id),
            ("nonce", self.nonce),
            ("issued_at", self.issued_at),
            ("valid_until", self.valid_until),
        ):
            if not value:
                raise CommandError(f"غلاف أمر ملكي بلا «{name}».")
        if self.sequence < 0:
            raise CommandError("تسلسل الأمر لا يكون سالبًا.")
        start = _parse(self.issued_at)
        end = _parse(self.valid_until)
        if end <= start:
            raise CommandError(
                f"نافذة صلاحية معكوسة: {self.issued_at} → {self.valid_until}."
            )

    # ── التمثيل القانوني ─────────────────────────────────────────────────

    def canonical_dict(self) -> dict[str, Any]:
        """كل حقل حسّاس، بترتيب لا يعتمد على المُصدِر."""
        return {
            "action": self.action,
            "command_id": self.command_id,
            "context": self.context,
            "issued_at": self.issued_at,
            "issuer_key_id": self.issuer_key_id,
            "nonce": self.nonce,
            "payload": self.payload,
            "previous_command_hash": self.previous_command_hash,
            "sequence": self.sequence,
            "target": self.target,
            "valid_until": self.valid_until,
        }

    def canonical_bytes(self) -> bytes:
        """بايتات التوقيع: وسم المجال ثم JSON مرتَّب مضغوط.

        ``sort_keys`` و``separators`` يُلغيان أثر ترتيب الحقول والمسافات، فلا
        يُنتج نفس الأمر بايتين مختلفين ولا يُنتج أمران نفس البايتات.
        """
        body = json.dumps(
            self.canonical_dict(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return DOMAIN_TAG_COMMAND.encode() + b"\n" + body.encode()

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def chain_hash(self) -> str:
        """تجزئة الحلقة — تُستعمل كـ previous_command_hash للأمر التالي."""
        return hashlib.sha256(
            f"{self.previous_command_hash}|{self.digest}".encode()
        ).hexdigest()

    def is_valid_at(self, moment: datetime | None = None) -> bool:
        now = moment or _now()
        return _parse(self.issued_at) <= now <= _parse(self.valid_until)

    def as_dict(self) -> dict[str, Any]:
        out = self.canonical_dict()
        out["digest"] = self.digest
        return out

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoyalCommandEnvelope:
        return cls(
            command_id=str(data["command_id"]),
            action=str(data["action"]),
            target=str(data.get("target", "")),
            issuer_key_id=str(data["issuer_key_id"]),
            nonce=str(data["nonce"]),
            sequence=int(data["sequence"]),
            issued_at=str(data["issued_at"]),
            valid_until=str(data["valid_until"]),
            payload=dict(data.get("payload") or {}),
            previous_command_hash=str(data.get("previous_command_hash", "")),
            context=dict(data.get("context") or {}),
        )


@dataclass(frozen=True, slots=True)
class SignedRoyalCommand:
    """أمر موقَّع + بيانات مصاحبة غير موقَّعة تُفحَص ولا يُعتَدّ بها.

    وجود ``unsigned_metadata`` مقصود: النقل يحتاج حقولًا (مسار، وسم شبكة). والخطر
    أن يتسلل حقل قرار فيها. لذلك تُفحَص عند البناء بقائمة حظر صريحة.
    """

    envelope: RoyalCommandEnvelope
    signature_hex: str
    unsigned_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.signature_hex:
            raise SignatureError("أمر ملكي بلا توقيع.")
        signed_keys = set(self.envelope.canonical_dict())
        for key in self.unsigned_metadata:
            lowered = str(key).lower()
            if lowered in FORBIDDEN_UNSIGNED_FIELDS or lowered in signed_keys:
                raise UnsignedFieldError(
                    f"الحقل «{key}» خارج نطاق التوقيع وهو حقل قرار. "
                    "كل حقل حسّاس يدخل الغلاف الموقَّع، وإلا أمكن تحويل الأمر "
                    "«أ» إلى «ب» بتغيير حقل غير موقَّع (البند 19)."
                )

    def verify_against(self, record: CrownKeyRecord) -> None:
        """تحقق تعميّ حقيقي من التوقيع مقابل مفتاح عام محدَّد."""
        if record.algorithm != "Ed25519":
            raise SignatureError(
                f"التحقق بمنظومة «{record.algorithm}» غير منفَّذ في هذا الإصدار."
            )
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(
            bytes.fromhex(record.public_key_hex)
        )
        try:
            public_key.verify(
                bytes.fromhex(self.signature_hex), self.envelope.canonical_bytes()
            )
        except (InvalidSignature, ValueError) as exc:
            raise SignatureError(
                f"توقيع الأمر «{self.envelope.command_id}» غير صحيح مقابل المفتاح "
                f"«{record.key_id}» ({exc.__class__.__name__}) — انتحال أو تحريف."
            ) from exc


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    """أثر تنفيذ أمر — أساس منع التنفيذ المزدوج."""

    command_id: str
    nonce: str
    sequence: int
    digest: str
    executed_at: str


class CommandLedger:
    """سجل الأوامر المنفَّذة: نونسات مستهلكة، وتسلسل رقابي، وسلسلة تجزئة.

    التسلسل **رقابي لا مجرد رقم**: لا يقبل رقمًا أقل من آخر منفَّذ ولا مساويًا،
    لأن الرجوع أو التكرار هو بعينه إعادة الإرسال.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, ExecutionRecord] = {}
        self._nonces: set[str] = set()
        self._digests: set[str] = set()
        self._highest_sequence: int = -1
        self._chain_tip: str = ""

    @property
    def executed_count(self) -> int:
        return len(self._by_id)

    @property
    def highest_sequence(self) -> int:
        return self._highest_sequence

    @property
    def chain_tip(self) -> str:
        return self._chain_tip

    def was_executed(self, command_id: str) -> bool:
        return command_id in self._by_id

    def assert_fresh(self, envelope: RoyalCommandEnvelope) -> None:
        """أربعة فحوص للطزاجة، وكل واحد يمسك حالة لا يمسكها غيره."""
        if envelope.command_id in self._by_id:
            raise ReplayError(
                f"الأمر «{envelope.command_id}» نُفِّذ من قبل في "
                f"{self._by_id[envelope.command_id].executed_at}."
            )
        if envelope.nonce in self._nonces:
            raise ReplayError(
                f"نونس «{envelope.nonce}» مستهلك — إعادة إرسال بمعرّف جديد."
            )
        if envelope.digest in self._digests:
            raise ReplayError(
                "بصمة الأمر مطابقة لأمر منفَّذ — نفس القرار مغلَّفًا من جديد."
            )
        if envelope.sequence <= self._highest_sequence:
            raise ReplayError(
                f"تسلسل الأمر {envelope.sequence} ليس أعلى من آخر منفَّذ "
                f"{self._highest_sequence} — تسلسل راجع."
            )
        if self._chain_tip and envelope.previous_command_hash:
            if not hmac.compare_digest(
                envelope.previous_command_hash, self._chain_tip
            ):
                raise ContextTamperError(
                    "مرجع سلسلة الأمر لا يطابق طرف السجل — أمر مُقتطع من سياقه "
                    "أو أمر وسيط محذوف."
                )

    def commit(self, envelope: RoyalCommandEnvelope, *, at: str | None = None) -> ExecutionRecord:
        """أثبت التنفيذ. لا يُدعى إلا بعد نجاح كل الفحوص."""
        self.assert_fresh(envelope)
        record = ExecutionRecord(
            command_id=envelope.command_id,
            nonce=envelope.nonce,
            sequence=envelope.sequence,
            digest=envelope.digest,
            executed_at=at or _now().isoformat(),
        )
        self._by_id[envelope.command_id] = record
        self._nonces.add(envelope.nonce)
        self._digests.add(envelope.digest)
        self._highest_sequence = envelope.sequence
        self._chain_tip = envelope.chain_hash()
        return record

    def records(self) -> tuple[ExecutionRecord, ...]:
        return tuple(
            sorted(self._by_id.values(), key=lambda r: (r.sequence, r.executed_at))
        )


@dataclass(frozen=True, slots=True)
class VerificationOutcome:
    """نتيجة تحقق أمر: مقبول أو مرفوض بسبب مُسمّى، ومفتاح مُسمّى."""

    accepted: bool
    command_id: str
    key_id: str
    reason: str = ""
    historical: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "command_id": self.command_id,
            "key_id": self.key_id,
            "reason": self.reason,
            "historical_verification": self.historical,
        }


class CrownCommandVerifier:
    """مدقق الأوامر الملكية: توقيع، وصفة المفتاح، وطزاجة، ونافذة، وسياق.

    ترتيب الفحوص مقصود ولا يُقلَب: صفة المفتاح قبل الرياضيات، لأن توقيعًا صحيحًا
    بمفتاح مسحوب ليس أمرًا ملكيًّا، والاشتغال بالتحقق منه إضاعة لا فائدة فيها.
    """

    def __init__(
        self,
        registry: CrownKeyRegistry,
        ledger: CommandLedger | None = None,
        *,
        clock_skew_tolerance_seconds: int = 60,
    ) -> None:
        self._registry = registry
        self._ledger = ledger or CommandLedger()
        self._skew = timedelta(seconds=max(0, clock_skew_tolerance_seconds))

    @property
    def ledger(self) -> CommandLedger:
        return self._ledger

    @property
    def registry(self) -> CrownKeyRegistry:
        return self._registry

    def _resolve_key(self, key_id: str) -> CrownKeyRecord:
        record = self._registry.get(key_id)
        if record.is_revoked:
            raise SignatureError(
                f"المفتاح «{key_id}» حالته {record.state.value} "
                f"({record.revocation_reason or 'بلا سبب مُدوَّن'}). "
                "توقيع صحيح بمفتاح مسحوب ليس أمرًا ملكيًّا."
            )
        if record.state is KeyState.PENDING:
            raise SignatureError(
                f"المفتاح «{key_id}» معلَّق لم يُنشَّط — لا صفة له بعد."
            )
        return record

    def _assert_window(self, envelope: RoyalCommandEnvelope, at: datetime) -> None:
        start = _parse(envelope.issued_at) - self._skew
        end = _parse(envelope.valid_until) + self._skew
        if at < start:
            raise ExpiredCommandError(
                f"الأمر «{envelope.command_id}» لم تبدأ نافذته بعد "
                f"({envelope.issued_at})."
            )
        if at > end:
            raise ExpiredCommandError(
                f"الأمر «{envelope.command_id}» انتهت نافذته "
                f"({envelope.valid_until}) — أمر بائت لا يُنفَّذ."
            )

    def verify(
        self,
        command: SignedRoyalCommand,
        *,
        at: datetime | None = None,
        require_active_key: bool = True,
    ) -> VerificationOutcome:
        """تحقق كامل بلا إثبات تنفيذ — الفصل بين «صحيح» و«نُفِّذ» مقصود."""
        moment = at or _now()
        envelope = command.envelope
        record = self._resolve_key(envelope.issuer_key_id)

        if require_active_key and record.state is not KeyState.ACTIVE:
            raise SignatureError(
                f"المفتاح «{record.key_id}» حالته {record.state.value} "
                "ولا يُقبل لأمر جديد. الأوامر القديمة تُتحقَّق تاريخيًّا بمسار آخر."
            )

        self._assert_window(envelope, moment)
        command.verify_against(record)
        self._ledger.assert_fresh(envelope)
        return VerificationOutcome(
            accepted=True, command_id=envelope.command_id, key_id=record.key_id
        )

    def verify_and_commit(
        self, command: SignedRoyalCommand, *, at: datetime | None = None
    ) -> ExecutionRecord:
        """تحقق ثم أثبت التنفيذ — الاستدعاء الثاني لنفس الأمر يُرفَض."""
        self.verify(command, at=at)
        return self._ledger.commit(
            command.envelope, at=(at or _now()).isoformat()
        )

    def verify_historical(
        self, command: SignedRoyalCommand, *, signed_at: str | None = None
    ) -> VerificationOutcome:
        """تحقق من أمر قديم: هل كان مفتاحه ذا صفة لحظة إصداره؟

        هذا المسار لا يفحص النافذة ولا الطزاجة، لأن سؤاله مختلف: لا «هل يُنفَّذ
        الآن؟» بل «هل كان هذا قرارًا سياديًّا صحيحًا يومه؟».
        """
        envelope = command.envelope
        moment = signed_at or envelope.issued_at
        record = self._registry.get(envelope.issuer_key_id)
        if not record.was_valid_at(moment):
            return VerificationOutcome(
                accepted=False,
                command_id=envelope.command_id,
                key_id=record.key_id,
                reason=(
                    f"المفتاح «{record.key_id}» لم يكن ذا صفة في {moment} "
                    f"(الحالة {record.state.value})."
                ),
                historical=True,
            )
        try:
            command.verify_against(record)
        except SignatureError as exc:
            return VerificationOutcome(
                accepted=False,
                command_id=envelope.command_id,
                key_id=record.key_id,
                reason=str(exc),
                historical=True,
            )
        return VerificationOutcome(
            accepted=True,
            command_id=envelope.command_id,
            key_id=record.key_id,
            historical=True,
        )


def build_envelope(
    *,
    command_id: str,
    action: str,
    target: str,
    issuer_key_id: str,
    nonce: str,
    sequence: int,
    validity_seconds: int = 900,
    payload: dict[str, Any] | None = None,
    previous_command_hash: str = "",
    context: dict[str, Any] | None = None,
    issued_at: datetime | None = None,
) -> RoyalCommandEnvelope:
    """مُيسِّر بناء غلاف بنافذة صلاحية افتراضية محدودة.

    النافذة الافتراضية قصيرة عن قصد: أمر بلا انتهاء أمر أبدي، وسرقته سرقة دائمة.
    """
    start = issued_at or _now()
    return RoyalCommandEnvelope(
        command_id=command_id,
        action=action,
        target=target,
        issuer_key_id=issuer_key_id,
        nonce=nonce,
        sequence=sequence,
        issued_at=start.isoformat(),
        valid_until=(start + timedelta(seconds=validity_seconds)).isoformat(),
        payload=payload or {},
        previous_command_hash=previous_command_hash,
        context=context or {},
    )


__all__ = [
    "DOMAIN_TAG_COMMAND",
    "FORBIDDEN_UNSIGNED_FIELDS",
    "CommandError",
    "CommandLedger",
    "ContextTamperError",
    "CrownCommandVerifier",
    "ExecutionRecord",
    "ExpiredCommandError",
    "ReplayError",
    "RoyalCommandEnvelope",
    "SignatureError",
    "SignedRoyalCommand",
    "UnsignedFieldError",
    "VerificationOutcome",
    "build_envelope",
]
