"""الهدف: سجل مفاتيح التاج بنسخه ونسبه وحالات تنشيطه وسحبه ومصدره.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

هذه الوحدة تُحقّق الطبقة الثانية من سلسلة الثقة (البند الثالث من التوجيه):

    مرساة الثقة → سجل مفاتيح التاج → مفتاح التوقيع النشط → التوقيع الملكي → القرار السيادي

والفرق بينها وبين ``core.sovereignty.crown``: تلك تعرف «المفتاح النشط الآن»،
وهذه تعرف **تاريخ المفاتيح كله** — من أين جاء كل مفتاح، وبأي مراسم، ومن سبقه،
ومتى كان صحيحًا، ومتى بطل، وهل بطلانه سحب أمني أم إحالة عادية بعد تدوير.

سبب الحاجة إلى التاريخ: توقيع صحيح على أمر قديم يجب أن يبقى قابلًا للتحقق بعد
تدوير المفتاح، وتوقيع بمفتاح مسحوب يجب أن يُرفَض حتى لو كان التوقيع رياضيًّا
سليمًا. الرياضيات تقول «التوقيع صحيح»، والسجل هو ما يقول «وهل كان صاحبه ذا صفة؟».

المفاتيح الخاصة لا تدخل هذه الوحدة ولا تُخزَّن فيها بأي حال.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Final

# المنظومات التعمية المقبولة الآن، ومساحة اتساع للمستقبل بعد الكم (البند 25).
# القبول هنا لا يعني وجود تنفيذ: ما ليس مدعومًا بمكتبة تحقق حقيقية يبقى معلنًا
# غير مفعَّل، ولا يُدَّعى أنه يعمل.
SUPPORTED_ALGORITHMS: Final[dict[str, bool]] = {
    "Ed25519": True,
    "Ed448": False,
    "ECDSA-P384": False,
    "ML-DSA-65": False,      # Dilithium — بعد الكم، غير مفعَّل بعد
    "ML-DSA-87": False,
    "SLH-DSA-SHA2-128s": False,  # SPHINCS+ — بعد الكم، غير مفعَّل بعد
}

# منظومات هجينة (كلاسيكي + بعد كمي) — الترقية المخططة، غير مفعَّلة بعد.
HYBRID_ALGORITHMS: Final[frozenset[str]] = frozenset(
    {"Ed25519+ML-DSA-65", "ECDSA-P384+ML-DSA-87"}
)

DOMAIN_TAG_MANIFEST: Final[str] = "AMOS-CROWN-KEY-MANIFEST-v1"


class KeyRegistryError(Exception):
    """خلل في سجل مفاتيح التاج."""


class LineageError(KeyRegistryError):
    """نسب المفاتيح غير متصل أو متشعّب — أصل تاج مزيّف موازٍ."""


class KeyStateError(KeyRegistryError):
    """انتقال حالة غير مشروع لمفتاح التاج."""


class AlgorithmError(KeyRegistryError):
    """منظومة تعمية غير مقبولة أو معلنة غير مفعَّلة."""


class KeyState(str, Enum):
    """حالات مفتاح التاج — معلنة صراحةً لا مستنبطة من غياب حقل."""

    PENDING = "PENDING"          # مُسجَّل ولم يُنشَّط بعد
    ACTIVE = "ACTIVE"            # مفتاح التوقيع النافذ
    RETIRED = "RETIRED"          # أُحيل بعد تدوير سليم — تحققه التاريخي باقٍ
    REVOKED = "REVOKED"          # سُحب بقرار — لا صحة له ولا تاريخية
    COMPROMISED = "COMPROMISED"  # ثبت اختراقه — يبطل حتى ما وقّعه سابقًا


# الانتقالات المشروعة فقط. وما ليس في الجدول ممنوع، لا «مسكوت عنه».
_ALLOWED_TRANSITIONS: Final[dict[KeyState, frozenset[KeyState]]] = {
    KeyState.PENDING: frozenset({KeyState.ACTIVE, KeyState.REVOKED}),
    KeyState.ACTIVE: frozenset(
        {KeyState.RETIRED, KeyState.REVOKED, KeyState.COMPROMISED}
    ),
    KeyState.RETIRED: frozenset({KeyState.COMPROMISED, KeyState.REVOKED}),
    KeyState.REVOKED: frozenset(),      # نهائي
    KeyState.COMPROMISED: frozenset(),  # نهائي
}


class LineageKind(str, Enum):
    """سبب وجود المفتاح — ولا مفتاح بلا سبب معلن."""

    GENESIS = "GENESIS"        # أول مفتاح — مراسم التنصيب
    ROTATION = "ROTATION"      # تدوير دوري، التاج والملك كما هما (البند 26)
    SUCCESSION = "SUCCESSION"  # خلافة رسمية — شخص جديد يحمل الدور (البند 27)
    RECOVERY = "RECOVERY"      # استرداد بعد فقد الوصول (البند 8)
    COMPROMISE_RESPONSE = "COMPROMISE_RESPONSE"  # استجابة لاختراق مؤكَّد


@dataclass(frozen=True, slots=True)
class KeyProvenance:
    """من أين جاء هذا المفتاح — بأي مراسم، وبأي بيئة، وبأي إشهاد، وبشهادة من.

    لا يوجد حقل «سري» هنا: كل ما في المصدر مرجع أو بصمة أو اسم بيئة.
    """

    ceremony_id: str
    ceremony_kind: str
    keystore_kind: str
    attestation_ref: str = ""
    witnesses: tuple[str, ...] = ()
    out_of_band_verified: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.ceremony_id:
            raise KeyRegistryError("مصدر المفتاح بلا معرّف مراسم.")
        if not self.keystore_kind:
            raise KeyRegistryError("مصدر المفتاح بلا بيئة توقيع معلنة.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "ceremony_id": self.ceremony_id,
            "ceremony_kind": self.ceremony_kind,
            "keystore_kind": self.keystore_kind,
            "attestation_ref": self.attestation_ref,
            "witnesses": list(self.witnesses),
            "out_of_band_verified": self.out_of_band_verified,
            "notes": self.notes,
        }


@dataclass(frozen=True, slots=True)
class CrownKeyRecord:
    """قيد مفتاح تاج واحد — عام فقط، بنسخته ونسبه وحالته وصلاحيته الزمنية."""

    key_id: str
    version: int
    algorithm: str
    public_key_hex: str
    state: KeyState
    lineage_kind: LineageKind
    predecessor_key_id: str | None
    registered_at: str
    provenance: KeyProvenance
    activated_at: str = ""
    retired_at: str = ""
    revoked_at: str = ""
    revocation_reason: str = ""

    def __post_init__(self) -> None:
        if not self.key_id:
            raise KeyRegistryError("قيد مفتاح بلا معرّف.")
        if self.version < 1:
            raise KeyRegistryError("نسخة المفتاح تبدأ من 1.")
        if not self.public_key_hex:
            raise KeyRegistryError(f"المفتاح «{self.key_id}» بلا مفتاح عام.")
        try:
            raw = bytes.fromhex(self.public_key_hex)
        except ValueError as exc:
            raise KeyRegistryError(
                f"المفتاح العام لـ«{self.key_id}» ليس ست عشريًّا صالحًا: {exc}"
            ) from exc
        if self.algorithm == "Ed25519" and len(raw) != 32:
            raise KeyRegistryError(
                f"مفتاح Ed25519 «{self.key_id}» طوله {len(raw)} بايت والمطلوب 32."
            )
        if self.algorithm not in SUPPORTED_ALGORITHMS and self.algorithm not in HYBRID_ALGORITHMS:
            raise AlgorithmError(f"منظومة تعمية مجهولة: {self.algorithm}")
        if self.lineage_kind is LineageKind.GENESIS and self.predecessor_key_id:
            raise LineageError("مفتاح التأسيس لا سابق له.")
        if self.lineage_kind is not LineageKind.GENESIS and not self.predecessor_key_id:
            raise LineageError(
                f"المفتاح «{self.key_id}» من نوع {self.lineage_kind.value} بلا سابق. "
                "مفتاح بلا نسب هو تاج موازٍ."
            )
        if self.state is KeyState.ACTIVE and not self.activated_at:
            raise KeyStateError(f"المفتاح النشط «{self.key_id}» بلا وقت تنشيط.")
        if self.state in {KeyState.REVOKED, KeyState.COMPROMISED} and not self.revoked_at:
            raise KeyStateError(f"سحب المفتاح «{self.key_id}» بلا وقت سحب.")

    @property
    def is_activated_now(self) -> bool:
        return self.state is KeyState.ACTIVE

    @property
    def is_revoked(self) -> bool:
        return self.state in {KeyState.REVOKED, KeyState.COMPROMISED}

    @property
    def algorithm_is_enabled(self) -> bool:
        """هل التحقق بهذه المنظومة منفَّذ فعلًا؟ الإعلان ليس تنفيذًا."""
        return SUPPORTED_ALGORITHMS.get(self.algorithm, False)

    @property
    def fingerprint(self) -> str:
        """بصمة المفتاح — مُشتقّة من المنظومة والمفتاح العام مع وسم مجال."""
        return hashlib.sha256(
            f"AMOS-CROWN-KEY-v1:{self.algorithm}:{self.public_key_hex}".encode()
        ).hexdigest()

    def was_valid_at(self, moment: str) -> bool:
        """الصلاحية التاريخية: هل كان هذا المفتاح ذا صفة في لحظة بعينها؟

        السحب والاختراق يُبطلان الماضي — لأن السحب معناه أن الصفة لم تكن حقيقية.
        والإحالة بعد التدوير لا تُبطل الماضي — لأن التوقيع وقتها كان صحيحًا بصفة
        صحيحة، وإبطاله يُبطل كل قرار سيادي سابق بلا سبب.
        """
        if self.is_revoked:
            return False
        if not self.activated_at:
            return False
        if moment < self.activated_at:
            return False
        return not (self.retired_at and moment > self.retired_at)

    def as_dict(self) -> dict[str, Any]:
        return {
            "key_id": self.key_id,
            "version": self.version,
            "algorithm": self.algorithm,
            "public_key_hex": self.public_key_hex,
            "fingerprint": self.fingerprint,
            "state": self.state.value,
            "lineage_kind": self.lineage_kind.value,
            "predecessor_key_id": self.predecessor_key_id,
            "registered_at": self.registered_at,
            "activated_at": self.activated_at,
            "retired_at": self.retired_at,
            "revoked_at": self.revoked_at,
            "revocation_reason": self.revocation_reason,
            "provenance": self.provenance.as_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CrownKeyRecord:
        prov = data.get("provenance") or {}
        return cls(
            key_id=str(data["key_id"]),
            version=int(data["version"]),
            algorithm=str(data["algorithm"]),
            public_key_hex=str(data["public_key_hex"]),
            state=KeyState(str(data["state"])),
            lineage_kind=LineageKind(str(data["lineage_kind"])),
            predecessor_key_id=data.get("predecessor_key_id") or None,
            registered_at=str(data.get("registered_at", "")),
            activated_at=str(data.get("activated_at", "")),
            retired_at=str(data.get("retired_at", "")),
            revoked_at=str(data.get("revoked_at", "")),
            revocation_reason=str(data.get("revocation_reason", "")),
            provenance=KeyProvenance(
                ceremony_id=str(prov.get("ceremony_id", "")),
                ceremony_kind=str(prov.get("ceremony_kind", "")),
                keystore_kind=str(prov.get("keystore_kind", "")),
                attestation_ref=str(prov.get("attestation_ref", "")),
                witnesses=tuple(prov.get("witnesses", ())),
                out_of_band_verified=bool(prov.get("out_of_band_verified", False)),
                notes=str(prov.get("notes", "")),
            ),
        )


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class CrownKeyRegistry:
    """سجل مفاتيح التاج: قيود مرتّبة بالنسخة، بمفتاح نشط واحد على الأكثر.

    «على الأكثر» لا «بالضبط»: التاج قد يكون غير مُنصَّب، وقد يكون مفتاحه مسحوبًا
    بعد اختراق، وفي الحالتين لا مفتاح نشط — والاختصاص الملكي يُجمَّد ولا يُنقَل.
    """

    def __init__(self, records: list[CrownKeyRecord] | None = None) -> None:
        self._records: list[CrownKeyRecord] = list(records or [])
        self.validate()

    # ── قراءة ──────────────────────────────────────────────────────────────

    @property
    def records(self) -> tuple[CrownKeyRecord, ...]:
        return tuple(sorted(self._records, key=lambda r: r.version))

    @property
    def manifest_version(self) -> int:
        """أعلى نسخة مفتاح — تُستخدم في منع التراجع بمرساة الثقة."""
        return max((r.version for r in self._records), default=0)

    def get(self, key_id: str) -> CrownKeyRecord:
        for record in self._records:
            if record.key_id == key_id:
                return record
        raise KeyRegistryError(f"لا مفتاح بالمعرّف «{key_id}» في السجل.")

    def active(self) -> CrownKeyRecord | None:
        for record in self._records:
            if record.state is KeyState.ACTIVE:
                return record
        return None

    def active_or_raise(self) -> CrownKeyRecord:
        record = self.active()
        if record is None:
            raise KeyRegistryError(
                "لا مفتاح تاج نشط. الاختصاص الملكي مُجمَّد ولا يُنقَل إلى أي طرف."
            )
        return record

    def lineage(self) -> tuple[CrownKeyRecord, ...]:
        """النسب من التأسيس إلى الأحدث، متصلًا بلا تشعّب."""
        return self.records

    def valid_verifiers_at(self, moment: str) -> tuple[CrownKeyRecord, ...]:
        """المفاتيح التي كانت ذات صفة في لحظة — للتحقق من أوامر قديمة."""
        return tuple(r for r in self.records if r.was_valid_at(moment))

    # ── تحقق البنية ───────────────────────────────────────────────────────

    def validate(self) -> None:
        """تحقق شامل: نسخ فريدة، معرّفات فريدة، نسب متصل، نشط واحد."""
        ids = [r.key_id for r in self._records]
        if len(set(ids)) != len(ids):
            raise KeyRegistryError("معرّفات مفاتيح مكرّرة في السجل.")
        versions = [r.version for r in self._records]
        if len(set(versions)) != len(versions):
            raise LineageError("نسخ مفاتيح مكرّرة — نسب متشعّب.")

        actives = [r for r in self._records if r.state is KeyState.ACTIVE]
        if len(actives) > 1:
            raise KeyStateError(
                f"مفاتيح تاج نشطة {len(actives)} في وقت واحد. "
                "تاجان نشطان معناهما تاج مزيّف موازٍ."
            )

        genesis = [r for r in self._records if r.lineage_kind is LineageKind.GENESIS]
        if self._records and len(genesis) != 1:
            raise LineageError(
                f"عدد مفاتيح التأسيس {len(genesis)} والمطلوب واحد بالضبط."
            )

        by_id = {r.key_id: r for r in self._records}
        ordered = self.records
        for index, record in enumerate(ordered):
            if index == 0:
                if record.lineage_kind is not LineageKind.GENESIS:
                    raise LineageError("أول مفتاح في النسب يجب أن يكون التأسيس.")
                continue
            if record.predecessor_key_id not in by_id:
                raise LineageError(
                    f"سابق المفتاح «{record.key_id}» "
                    f"(«{record.predecessor_key_id}») غير موجود في السجل."
                )
            predecessor = by_id[record.predecessor_key_id]
            if predecessor.version >= record.version:
                raise LineageError(
                    f"المفتاح «{record.key_id}» نسخته {record.version} "
                    f"وسابقه نسخته {predecessor.version} — النسب لا يرجع للخلف."
                )

        # لا مفتاحان بنفس المفتاح العام: إعادة استخدام المادة تُخفي انقطاع نسب.
        fingerprints = [r.fingerprint for r in self._records]
        if len(set(fingerprints)) != len(fingerprints):
            raise LineageError(
                "مفتاحان عامّان متطابقان بمعرّفين مختلفين — إعادة استخدام مادة مفتاح."
            )

    # ── تعديل ─────────────────────────────────────────────────────────────

    def register(self, record: CrownKeyRecord) -> None:
        """أضف قيدًا جديدًا ثم تحقق — والتحقق قبل الإقرار لا بعده."""
        candidate = [*self._records, record]
        probe = CrownKeyRegistry.__new__(CrownKeyRegistry)
        probe._records = candidate
        probe.validate()
        self._records = candidate

    def _transition(self, key_id: str, new_state: KeyState, **updates: str) -> CrownKeyRecord:
        current = self.get(key_id)
        allowed = _ALLOWED_TRANSITIONS[current.state]
        if new_state not in allowed:
            raise KeyStateError(
                f"انتقال ممنوع للمفتاح «{key_id}»: "
                f"{current.state.value} → {new_state.value}."
            )
        data = current.as_dict()
        data.pop("fingerprint", None)
        data["state"] = new_state.value
        data.update(updates)
        updated = CrownKeyRecord.from_dict(data)
        self._records = [updated if r.key_id == key_id else r for r in self._records]
        self.validate()
        return updated

    def activate(self, key_id: str, *, at: str | None = None) -> CrownKeyRecord:
        """نشّط مفتاحًا معلَّقًا — ولا يُنشَّط اثنان."""
        existing = self.active()
        if existing is not None and existing.key_id != key_id:
            raise KeyStateError(
                f"المفتاح «{existing.key_id}» نشط. أحِله أو اسحبه قبل تنشيط غيره."
            )
        return self._transition(key_id, KeyState.ACTIVE, activated_at=at or _now())

    def retire(self, key_id: str, *, at: str | None = None) -> CrownKeyRecord:
        """أحِل مفتاحًا بعد تدوير سليم — تحققه التاريخي باقٍ (البند 26)."""
        return self._transition(key_id, KeyState.RETIRED, retired_at=at or _now())

    def revoke(
        self, key_id: str, *, reason: str, at: str | None = None
    ) -> CrownKeyRecord:
        """اسحب مفتاحًا بقرار — يبطل حاضره وماضيه."""
        if not reason:
            raise KeyRegistryError("سحب مفتاح التاج بلا سبب معلن مرفوض.")
        return self._transition(
            key_id, KeyState.REVOKED, revoked_at=at or _now(), revocation_reason=reason
        )

    def mark_compromised(
        self, key_id: str, *, reason: str, at: str | None = None
    ) -> CrownKeyRecord:
        """أعلن اختراق مفتاح — أشد من السحب، ويستوجب مراسم استرداد."""
        if not reason:
            raise KeyRegistryError("إعلان اختراق بلا سبب معلن مرفوض.")
        return self._transition(
            key_id,
            KeyState.COMPROMISED,
            revoked_at=at or _now(),
            revocation_reason=reason,
        )

    def rotate(
        self,
        *,
        new_key_id: str,
        algorithm: str,
        public_key_hex: str,
        provenance: KeyProvenance,
        lineage_kind: LineageKind = LineageKind.ROTATION,
        predecessor_key_id: str | None = None,
        at: str | None = None,
    ) -> CrownKeyRecord:
        """تدوير: أحِل النشط، وسجّل الخلف، ونشّطه — بلا فجوة ولا تاجين.

        الدور واحد قبل التدوير وبعده. ما يتغيّر هو مادة المفتاح لا صاحب التاج،
        إلا في الخلافة الرسمية (البند 27) وهي نوع نسب آخر يُعلَن.

        وثمة حال لا يجوز إغفالها: إعلان اختراق المفتاح النشط يُخرجه من النشاط، فلا
        يبقى مفتاح نشط يُدوَّر منه. ولو اشترطنا مفتاحًا نشطًا دائمًا لصار إعلان
        الاختراق قفلًا أبديًّا يمنع الخلافة والاسترداد — أي عقوبةً على الصدق. فيُسمح
        بسلف **مُسمّى صراحةً** شرط أن يكون مخترَقًا أو مسحوبًا، ويبقى تسلسل النسب
        متصلًا ومقروءًا.
        """
        moment = at or _now()
        current = self.active()
        if current is None:
            if not predecessor_key_id:
                raise KeyRegistryError(
                    "لا مفتاح تاج نشط، ولم يُسمَّ سلف صراحةً. التدوير بعد اختراق "
                    "يلزمه تعيين السلف في المراسم لا استنتاجه."
                )
            current = self.get(predecessor_key_id)
            if current.state not in (KeyState.COMPROMISED, KeyState.REVOKED, KeyState.RETIRED):
                raise KeyRegistryError(
                    f"السلف المُسمّى «{predecessor_key_id}» حالته {current.state.value} "
                    "وليست حالة سلف مُنهى دوره."
                )
        elif predecessor_key_id and predecessor_key_id != current.key_id:
            raise KeyRegistryError(
                f"السلف المُسمّى «{predecessor_key_id}» ليس المفتاح النشط "
                f"«{current.key_id}» — تدويرٌ من غير موضعه."
            )
        record = CrownKeyRecord(
            key_id=new_key_id,
            version=self.manifest_version + 1,
            algorithm=algorithm,
            public_key_hex=public_key_hex,
            state=KeyState.PENDING,
            lineage_kind=lineage_kind,
            predecessor_key_id=current.key_id,
            registered_at=moment,
            provenance=provenance,
        )
        self.register(record)
        if current.state is KeyState.ACTIVE:
            self.retire(current.key_id, at=moment)
        return self.activate(new_key_id, at=moment)

    # ── تسلسل ─────────────────────────────────────────────────────────────

    def manifest(self) -> dict[str, Any]:
        """بيان المفاتيح — الشكل القانوني الذي يُوقَّع ويُقارن بمرساة الثقة."""
        return {
            "domain": DOMAIN_TAG_MANIFEST,
            "manifest_version": self.manifest_version,
            "active_key_id": (self.active().key_id if self.active() else None),
            "keys": [r.as_dict() for r in self.records],
        }

    def canonical_manifest_bytes(self) -> bytes:
        """تمثيل قانوني وحيد للبيان — لا يعتمد على ترتيب مفاتيح JSON ولا مسافاته.

        وسم المجال في المقدمة يمنع أن يُقرأ توقيع بيان مفاتيح كأنه توقيع أمر ملكي.
        """
        body = json.dumps(
            self.manifest(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        return DOMAIN_TAG_MANIFEST.encode() + b"\n" + body.encode()

    def manifest_digest(self) -> str:
        return hashlib.sha256(self.canonical_manifest_bytes()).hexdigest()

    @classmethod
    def from_manifest(cls, data: dict[str, Any]) -> CrownKeyRegistry:
        if data.get("domain") != DOMAIN_TAG_MANIFEST:
            raise KeyRegistryError(
                f"بيان بوسم مجال مختلف: {data.get('domain')!r}. "
                "قراءة بيان من مجال آخر أصل خلط توقيعات."
            )
        keys = data.get("keys")
        if not isinstance(keys, list):
            raise KeyRegistryError("بيان المفاتيح بلا قائمة keys.")
        return cls([CrownKeyRecord.from_dict(k) for k in keys])


@dataclass(frozen=True, slots=True)
class AlgorithmAgilityPlan:
    """خطة مرونة المنظومات: ما هو نافذ الآن، وما هو مخطط، وما ليس منفَّذًا (البند 25).

    هذا الكائن يمنع الادعاء: كل منظومة تظهر بحالتها الحقيقية — مفعَّلة أو معلنة
    غير مفعَّلة — ومقاومة الكم هنا **خطة ترقية**، لا خصيصة قائمة اليوم.
    """

    current: str = "Ed25519"
    planned_hybrid: str = "Ed25519+ML-DSA-65"
    rationale: str = (
        "التوقيع الكلاسيكي نافذ اليوم، والترقية المخططة هجينة كي لا يسقط التحقق "
        "بسقوط إحدى المنظومتين. ومقاومة الكم لا تُدَّعى قبل تنفيذ تحقق حقيقي."
    )
    enabled_algorithms: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            name for name, enabled in SUPPORTED_ALGORITHMS.items() if enabled
        )
    )
    declared_not_implemented: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            name for name, enabled in SUPPORTED_ALGORITHMS.items() if not enabled
        )
        + tuple(sorted(HYBRID_ALGORITHMS))
    )

    def assert_usable(self, algorithm: str) -> None:
        """ارفض التوقيع بمنظومة معلنة غير منفَّذة — العَلَم ليس تنفيذًا."""
        if algorithm not in self.enabled_algorithms:
            raise AlgorithmError(
                f"المنظومة «{algorithm}» معلنة في خطة الترقية وغير منفَّذة بعد. "
                f"المنفَّذ فعلًا: {', '.join(self.enabled_algorithms)}."
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "current": self.current,
            "planned_hybrid": self.planned_hybrid,
            "enabled": list(self.enabled_algorithms),
            "declared_not_implemented": list(self.declared_not_implemented),
            "rationale": self.rationale,
        }


__all__ = [
    "DOMAIN_TAG_MANIFEST",
    "HYBRID_ALGORITHMS",
    "SUPPORTED_ALGORITHMS",
    "AlgorithmAgilityPlan",
    "AlgorithmError",
    "CrownKeyRecord",
    "CrownKeyRegistry",
    "KeyProvenance",
    "KeyRegistryError",
    "KeyState",
    "KeyStateError",
    "LineageError",
    "LineageKind",
]
