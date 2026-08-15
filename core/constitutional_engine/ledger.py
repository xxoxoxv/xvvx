"""
السجل الدستوري غير القابل للعبث — Tamper-Evident Constitutional Ledger (E1)
الهدف: تسجيل كل حكم دستوري في سلسلة تجزئة متصلة، بحيث لا يمكن حذف قيد ولا تعديله ولا إعادة ترتيبه دون كشف فوري.
النطاق: الكتابة الملحقة فقط (append-only) والتحقق من السلسلة. لا حذف، ولا تعديل، ولا اقتطاع — بأي صلاحية.
المالك: core/constitutional_engine/
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المبدأ (المادة الأولى · 3 و 4، والمادة السابعة): الذاكرة مقدسة، والشفافية مطلقة.
كل قيد يحمل بصمة القيد السابق. كسر السلسلة يُكتشف بـ verify_chain() ولا يمكن إخفاؤه.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LEDGER = REPO_ROOT / "core" / "constitution" / "ledger" / "constitutional_ledger.jsonl"

GENESIS_HASH = "0" * 64


def _canonical(payload: dict[str, Any]) -> str:
    """تمثيل نصي حتمي — نفس المحتوى ينتج نفس البصمة دائمًا."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash_entry(prev_hash: str, body: dict[str, Any]) -> str:
    return hashlib.sha256((prev_hash + _canonical(body)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LedgerEntry:
    index: int
    timestamp: str
    prev_hash: str
    entry_hash: str
    body: dict[str, Any]


class LedgerTamperError(RuntimeError):
    """يُرفع عند اكتشاف كسر في سلسلة السجل. لا يُبتلع أبدًا."""


class ConstitutionalLedger:
    """سجل ملحق فقط بسلسلة تجزئة. لا يوفر — عمدًا — أي دالة حذف أو تعديل."""

    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_LEDGER
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # -- قراءة ------------------------------------------------------------
    def entries(self) -> list[LedgerEntry]:
        if not self.path.exists():
            return []
        out: list[LedgerEntry] = []
        for line_no, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise LedgerTamperError(
                    f"قيد تالف في {self.path}:{line_no} — السجل غير قابل للقراءة: {exc}"
                ) from exc
            out.append(
                LedgerEntry(
                    index=rec["index"],
                    timestamp=rec["timestamp"],
                    prev_hash=rec["prev_hash"],
                    entry_hash=rec["entry_hash"],
                    body=rec["body"],
                )
            )
        return out

    def head_hash(self) -> str:
        entries = self.entries()
        return entries[-1].entry_hash if entries else GENESIS_HASH

    def __len__(self) -> int:
        return len(self.entries())

    # -- كتابة ------------------------------------------------------------
    def append(self, body: dict[str, Any], *, timestamp: str | None = None) -> LedgerEntry:
        """ألحق قيدًا جديدًا. الكتابة ذرّية (ملف مؤقت ثم استبدال سطر ملحق)."""
        existing = self.entries()
        self._verify(existing)  # لا نضيف فوق سلسلة مكسورة

        index = len(existing)
        prev_hash = existing[-1].entry_hash if existing else GENESIS_HASH
        ts = timestamp or datetime.now(timezone.utc).isoformat(timespec="microseconds")

        sealed_body = {"index": index, "timestamp": ts, **body}
        entry_hash = _hash_entry(prev_hash, sealed_body)

        record = {
            "index": index,
            "timestamp": ts,
            "prev_hash": prev_hash,
            "entry_hash": entry_hash,
            "body": sealed_body,
        }
        line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"

        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line)
            fh.flush()
            os.fsync(fh.fileno())

        return LedgerEntry(index, ts, prev_hash, entry_hash, sealed_body)

    # -- تحقق -------------------------------------------------------------
    @staticmethod
    def _verify(entries: list[LedgerEntry]) -> None:
        prev = GENESIS_HASH
        for i, e in enumerate(entries):
            if e.index != i:
                raise LedgerTamperError(
                    f"ترتيب مكسور عند الموضع {i}: القيد يحمل index={e.index}. "
                    "حذف أو إعادة ترتيب قيود مخالفة دستورية (المادة الأولى · 3)."
                )
            if e.prev_hash != prev:
                raise LedgerTamperError(
                    f"سلسلة مكسورة عند القيد {i}: prev_hash={e.prev_hash[:12]}… "
                    f"والمتوقع {prev[:12]}…"
                )
            recomputed = _hash_entry(e.prev_hash, e.body)
            if recomputed != e.entry_hash:
                raise LedgerTamperError(
                    f"محتوى معدَّل في القيد {i}: البصمة المسجلة {e.entry_hash[:12]}… "
                    f"والمحسوبة {recomputed[:12]}…"
                )
            prev = e.entry_hash

    def verify_chain(self) -> list[str]:
        """يرجع قائمة المشاكل (فارغة = سلسلة سليمة). لا يرفع استثناءً."""
        try:
            self._verify(self.entries())
        except LedgerTamperError as exc:
            return [str(exc)]
        return []
