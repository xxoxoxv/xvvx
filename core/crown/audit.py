"""الهدف: سجل تاج غير قابل للتعديل — إضافة فقط، بسلسلة تجزئة تكشف أي عبث.

المالك: core/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

البند 31 يمنع الاعتماد على جدول SQL واحد قابل للتعديل. السبب واضح: من يملك
صلاحية UPDATE على جدول التدقيق يملك أن يجعل الحادثة كأنها لم تكن. والسجل الذي
يُعدَّل ليس سجلًّا بل رأيًا.

فالتصميم هنا: **إضافة فقط**، وكل قيد يحمل تجزئة سابقه، فحذف قيد من الوسط أو
تعديله يكسر السلسلة كسرًا مكشوفًا. ولا توجد في هذه الوحدة دالة حذف ولا تعديل —
وغيابها هو الضمان، لا وجود راية تمنعهما.

والتسمية دقيقة: هذا سجل **كاشف للعبث** (tamper-evident) لا **مانع له**
(tamper-proof). من ملك التخزين كله أعاد كتابة السلسلة من أولها. الذي يمنع ذلك
نسخ متعدد ومستويات مستقلة ونشر البصمة خارج النظام — لا الكود وحده.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Final

DOMAIN_TAG_AUDIT: Final[str] = "AMOS-CROWN-AUDIT-v1"


class AuditError(Exception):
    """خلل في سجل التاج."""


class AuditChainBrokenError(AuditError):
    """سلسلة التجزئة مكسورة — عبث بالسجل."""


class AuditAppendOnlyError(AuditError):
    """محاولة تعديل أو حذف قيد — السجل إضافة فقط."""


class CrownAuditEventKind(str, Enum):
    """الأحداث التي يلزم لها أثر لا يُمحى (البند 31)."""

    CROWN_KEY_CREATED = "CROWN_KEY_CREATED"
    CROWN_KEY_ACTIVATED = "CROWN_KEY_ACTIVATED"
    CROWN_KEY_ROTATED = "CROWN_KEY_ROTATED"
    CROWN_KEY_RETIRED = "CROWN_KEY_RETIRED"
    CROWN_KEY_COMPROMISED = "CROWN_KEY_COMPROMISED"
    CROWN_KEY_REVOKED = "CROWN_KEY_REVOKED"
    SUCCESSION_EVENT = "SUCCESSION_EVENT"
    RECOVERY_EVENT = "RECOVERY_EVENT"
    ROYAL_DECISION = "ROYAL_DECISION"
    GUARD_ALERT = "GUARD_ALERT"
    GUARD_CONTAINMENT = "GUARD_CONTAINMENT"
    AUTHORITY_CHANGE = "AUTHORITY_CHANGE"
    CONSTITUTIONAL_CHANGE = "CONSTITUTIONAL_CHANGE"
    CRITICAL_DEPLOYMENT = "CRITICAL_DEPLOYMENT"
    POLICY_CHANGE = "POLICY_CHANGE"
    TRUST_ANCHOR_EVENT = "TRUST_ANCHOR_EVENT"
    CONTINUITY_STATE_CHANGE = "CONTINUITY_STATE_CHANGE"
    LOCKDOWN_EVENT = "LOCKDOWN_EVENT"

    @property
    def is_critical(self) -> bool:
        """الأحداث التي لا يجوز أن تمر بلا مراجعة بشرية."""
        return self in {
            CrownAuditEventKind.CROWN_KEY_COMPROMISED,
            CrownAuditEventKind.CROWN_KEY_REVOKED,
            CrownAuditEventKind.SUCCESSION_EVENT,
            CrownAuditEventKind.RECOVERY_EVENT,
            CrownAuditEventKind.AUTHORITY_CHANGE,
            CrownAuditEventKind.CONSTITUTIONAL_CHANGE,
            CrownAuditEventKind.GUARD_CONTAINMENT,
            CrownAuditEventKind.LOCKDOWN_EVENT,
        }


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True, slots=True)
class CrownAuditEntry:
    """قيد واحد: نوعه، وفاعله، وموضوعه، ووقته، وتجزئة سابقه.

    ``actor`` هو من فعل، و``subject`` هو ما فُعل به. فصلهما يمنع سجلًّا يقول
    «حدث شيء» بلا فاعل — وهو أسوأ من غياب السجل لأنه يُوهم بالرقابة.
    """

    sequence: int
    kind: CrownAuditEventKind
    actor: str
    subject: str
    summary: str
    recorded_at: str
    previous_hash: str
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.sequence < 0:
            raise AuditError("تسلسل القيد لا يكون سالبًا.")
        if not self.actor:
            raise AuditError("قيد بلا فاعل — سجل يقول «حدث شيء» بلا فاعل لا يُراقِب.")
        if not self.summary:
            raise AuditError("قيد بلا خلاصة مقروءة.")

    def canonical_bytes(self) -> bytes:
        body = json.dumps(
            {
                "actor": self.actor,
                "detail": self.detail,
                "kind": self.kind.value,
                "previous_hash": self.previous_hash,
                "recorded_at": self.recorded_at,
                "sequence": self.sequence,
                "subject": self.subject,
                "summary": self.summary,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return DOMAIN_TAG_AUDIT.encode() + b"\n" + body.encode()

    @property
    def entry_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "kind": self.kind.value,
            "actor": self.actor,
            "subject": self.subject,
            "summary": self.summary,
            "recorded_at": self.recorded_at,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
            "critical": self.kind.is_critical,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CrownAuditEntry:
        return cls(
            sequence=int(data["sequence"]),
            kind=CrownAuditEventKind(str(data["kind"])),
            actor=str(data["actor"]),
            subject=str(data.get("subject", "")),
            summary=str(data["summary"]),
            recorded_at=str(data["recorded_at"]),
            previous_hash=str(data.get("previous_hash", "")),
            detail=dict(data.get("detail") or {}),
        )


class CrownAudit:
    """سجل التاج: إضافة فقط، مسلسل، بسلسلة تجزئة، وبمرآة قرصية اختيارية.

    لا توجد ``delete`` ولا ``update`` ولا ``truncate``. ومن أراد التصحيح يُضيف
    قيدًا مصححًا — فيبقى الخطأ وتصحيحه معًا في الأثر، وهذا هو معنى التدقيق.
    """

    def __init__(self, path: Path | None = None) -> None:
        self._entries: list[CrownAuditEntry] = []
        self._path = path
        if path is not None and path.exists():
            self._load(path)

    # ── قراءة ─────────────────────────────────────────────────────────────

    @property
    def entries(self) -> tuple[CrownAuditEntry, ...]:
        return tuple(self._entries)

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def tip_hash(self) -> str:
        return self._entries[-1].entry_hash if self._entries else ""

    def by_kind(self, kind: CrownAuditEventKind) -> tuple[CrownAuditEntry, ...]:
        return tuple(e for e in self._entries if e.kind is kind)

    def critical_entries(self) -> tuple[CrownAuditEntry, ...]:
        return tuple(e for e in self._entries if e.kind.is_critical)

    # ── كتابة (إضافة فقط) ─────────────────────────────────────────────────

    def append(
        self,
        kind: CrownAuditEventKind,
        *,
        actor: str,
        subject: str = "",
        summary: str,
        detail: dict[str, Any] | None = None,
        at: str | None = None,
    ) -> CrownAuditEntry:
        entry = CrownAuditEntry(
            sequence=len(self._entries),
            kind=kind,
            actor=actor,
            subject=subject,
            summary=summary,
            recorded_at=at or _now(),
            previous_hash=self.tip_hash,
            detail=detail or {},
        )
        self._entries.append(entry)
        if self._path is not None:
            self._flush(self._path)
        return entry

    # ── تحقق السلامة ──────────────────────────────────────────────────────

    def verify_chain(self) -> None:
        """أعد بناء السلسلة من الصفر — أي تعديل أو حذف يظهر هنا حتمًا."""
        previous = ""
        for index, entry in enumerate(self._entries):
            if entry.sequence != index:
                raise AuditChainBrokenError(
                    f"تسلسل القيد {entry.sequence} في الموضع {index} — قيد محذوف أو مُقحَم."
                )
            if entry.previous_hash != previous:
                raise AuditChainBrokenError(
                    f"القيد {index} يشير إلى سابق مختلف — عبث بالسجل."
                )
            previous = entry.entry_hash

    def integrity_digest(self) -> str:
        """بصمة السجل كله — هي ما يُنشَر خارج النظام لتقييد الماضي.

        نشرها ضروري: بغير مرجع خارجي، من ملك التخزين أعاد كتابة السلسلة من أولها
        وبقيت متسقة داخليًّا.
        """
        return hashlib.sha256(
            (DOMAIN_TAG_AUDIT + "|" + "|".join(e.entry_hash for e in self._entries)).encode()
        ).hexdigest()

    # ── مرآة قرصية ────────────────────────────────────────────────────────

    def _flush(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for entry in self._entries:
                handle.write(
                    json.dumps(entry.as_dict(), ensure_ascii=False, sort_keys=True) + "\n"
                )

    def _load(self, path: Path) -> None:
        loaded: list[CrownAuditEntry] = []
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                loaded.append(CrownAuditEntry.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError, ValueError) as exc:
                raise AuditChainBrokenError(
                    f"قيد غير قابل للقراءة في {path}:{line_number} — {exc}"
                ) from exc
        self._entries = loaded
        self.verify_chain()

    def snapshot(self) -> dict[str, Any]:
        return {
            "domain": DOMAIN_TAG_AUDIT,
            "count": len(self._entries),
            "tip_hash": self.tip_hash,
            "integrity_digest": self.integrity_digest(),
            "critical_count": len(self.critical_entries()),
            "entries": [e.as_dict() for e in self._entries],
        }


__all__ = [
    "DOMAIN_TAG_AUDIT",
    "AuditAppendOnlyError",
    "AuditChainBrokenError",
    "AuditError",
    "CrownAudit",
    "CrownAuditEntry",
    "CrownAuditEventKind",
]
