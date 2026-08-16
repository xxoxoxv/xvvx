"""
اختبارات السجل القانوني الواحد لسلسلة التدقيق
الهدف: إثبات أن publish وverify_chain يبنيان **نفس** التمثيل القانوني حرفيًا،
       وأن تغيير أي حقل جوهري أو ترتيب السلسلة يكسر التحقق.
النطاق: common/events
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16

هذه الاختبارات تعمل على SQLite (الافتراضي الخفيف). النظائر على PostgreSQL
الحقيقي في tests/test_phase1_postgres_events.py.
"""

import json

import pytest

from amos_federation.common import events
from amos_federation.common.database import (
    db_cursor,
    drop_audit_log_table,
    ensure_audit_log_table,
)


@pytest.fixture
def audit_log(sqlite_url: str):
    """جدول audit_log نظيف لكل اختبار، بنفس تعريف مسار الإنتاج."""
    drop_audit_log_table()
    ensure_audit_log_table()
    yield
    drop_audit_log_table()


def _rows() -> list[dict]:
    columns = ", ".join((*events.CANONICAL_AUDIT_FIELDS, "chain_hash", "prev_hash", "seq"))
    with db_cursor() as cur:
        cur.execute(f"SELECT {columns} FROM audit_log ORDER BY seq ASC")
        return list(cur.fetchall())


async def _publish(publisher: events.EventPublisher, n: int = 3) -> None:
    for index in range(n):
        await publisher.publish(
            f"task.step{index}",
            "test-suite",
            {"index": index, "note": "قيمة عربية"},
            actor_type="system",
            actor_id=f"actor-{index}",
        )


# =============================================================================
# 1. التمثيل القانوني واحد في الإنشاء والتحقق
# =============================================================================
class TestCanonicalRecordIsSingleShape:
    def test_from_row_equals_direct_construction(self, audit_log: None) -> None:
        record = events.canonical_audit_record(
            event_id="e1",
            timestamp="2026-08-16T10:00:00+00:00",
            event_type="task.created",
            actor_type="system",
            actor_id="a1",
            action="task.created",
            metadata={"k": "v"},
        )
        with db_cursor() as cur:
            cur.execute(
                """INSERT INTO audit_log
                   (event_id, timestamp, event_type, actor_type, actor_id,
                    action, chain_hash, prev_hash, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "e1",
                    "2026-08-16T10:00:00+00:00",
                    "task.created",
                    "system",
                    "a1",
                    "task.created",
                    "sha256:unused",
                    events.GENESIS_HASH,
                    json.dumps({"k": "v"}, ensure_ascii=False),
                ),
            )
        from_row = events.canonical_audit_record_from_row(_rows()[0])
        assert from_row == record

    def test_canonical_fields_are_exactly_the_hashed_material(self) -> None:
        assert set(events.CANONICAL_AUDIT_FIELDS) == {
            "event_id",
            "timestamp",
            "event_type",
            "actor_type",
            "actor_id",
            "action",
            "metadata",
        }

    def test_metadata_string_and_dict_canonicalize_identically(self) -> None:
        payload = {"b": 2, "a": 1}
        as_dict = events.canonical_audit_record(
            event_id="e",
            timestamp=None,
            event_type=None,
            actor_type=None,
            actor_id=None,
            action=None,
            metadata=payload,
        )
        as_text = events.canonical_audit_record(
            event_id="e",
            timestamp=None,
            event_type=None,
            actor_type=None,
            actor_id=None,
            action=None,
            metadata=json.dumps(payload),
        )
        assert as_dict == as_text

    def test_timestamp_string_and_datetime_canonicalize_identically(self) -> None:
        from datetime import UTC, datetime

        moment = datetime(2026, 8, 16, 10, 0, tzinfo=UTC)
        kwargs = dict(
            event_id="e",
            event_type=None,
            actor_type=None,
            actor_id=None,
            action=None,
            metadata=None,
        )
        as_dt = events.canonical_audit_record(timestamp=moment, **kwargs)
        as_text = events.canonical_audit_record(timestamp=moment.isoformat(), **kwargs)
        assert as_dt == as_text


# =============================================================================
# 2. الدورة الكاملة: publish ثم verify_chain
# =============================================================================
class TestPublishVerifyRoundTrip:
    @pytest.mark.asyncio
    async def test_published_chain_verifies(self, audit_log: None) -> None:
        publisher = events.EventPublisher()
        await _publish(publisher)
        rows = _rows()
        assert len(rows) == 3
        # الربط الحقيقي: prev_hash لكل صف هو chain_hash الذي قبله.
        assert rows[0]["prev_hash"] == events.GENESIS_HASH
        assert rows[1]["prev_hash"] == rows[0]["chain_hash"]
        assert rows[2]["prev_hash"] == rows[1]["chain_hash"]
        assert await publisher.verify_chain() is True

    @pytest.mark.asyncio
    async def test_empty_chain_verifies(self, audit_log: None) -> None:
        assert await events.EventPublisher().verify_chain() is True


# =============================================================================
# 3. تغيير أي حقل جوهري يكسر التحقق
# =============================================================================
@pytest.mark.parametrize("field", list(events.CANONICAL_AUDIT_FIELDS))
@pytest.mark.asyncio
async def test_tampering_any_canonical_field_breaks_verification(
    audit_log: None, field: str
) -> None:
    publisher = events.EventPublisher()
    await _publish(publisher, n=2)
    assert await publisher.verify_chain() is True

    target = _rows()[0]
    tampered = "tampered" if field != "metadata" else json.dumps({"index": 999})
    with db_cursor() as cur:
        cur.execute(
            f"UPDATE audit_log SET {field} = ? WHERE seq = ?",  # noqa: S608 - اسم العمود من ثابت داخلي
            (tampered, target["seq"]),
        )

    assert await publisher.verify_chain() is False


@pytest.mark.asyncio
async def test_tampering_prev_hash_breaks_verification(audit_log: None) -> None:
    publisher = events.EventPublisher()
    await _publish(publisher, n=2)
    rows = _rows()
    with db_cursor() as cur:
        cur.execute(
            "UPDATE audit_log SET prev_hash = ? WHERE seq = ?",
            ("sha256:not-the-previous-hash", rows[1]["seq"]),
        )
    assert await publisher.verify_chain() is False


@pytest.mark.asyncio
async def test_tampering_chain_hash_breaks_verification(audit_log: None) -> None:
    publisher = events.EventPublisher()
    await _publish(publisher, n=2)
    rows = _rows()
    with db_cursor() as cur:
        cur.execute(
            "UPDATE audit_log SET chain_hash = ? WHERE seq = ?",
            ("sha256:forged", rows[0]["seq"]),
        )
    assert await publisher.verify_chain() is False


# =============================================================================
# 4. تغيير ترتيب السلسلة يكسر التحقق — الترتيب الأساسي هو seq
# =============================================================================
class TestChainOrderIsMaterial:
    @pytest.mark.asyncio
    async def test_swapping_seq_of_two_rows_breaks_verification(self, audit_log: None) -> None:
        publisher = events.EventPublisher()
        await _publish(publisher, n=3)
        assert await publisher.verify_chain() is True

        rows = _rows()
        first, second = rows[0]["seq"], rows[1]["seq"]
        spare = max(r["seq"] for r in rows) + 1000
        # تبديل ترتيب صفين دون تغيير أي حقل آخر: كل بصمة سليمة في ذاتها،
        # لكن الربط عبر prev_hash لم يعد يطابق الترتيب.
        with db_cursor() as cur:
            cur.execute("UPDATE audit_log SET seq = ? WHERE seq = ?", (spare, first))
            cur.execute("UPDATE audit_log SET seq = ? WHERE seq = ?", (first, second))
            cur.execute("UPDATE audit_log SET seq = ? WHERE seq = ?", (second, spare))

        reordered = [r["event_id"] for r in _rows()]
        original = [r["event_id"] for r in rows]
        assert reordered[:2] == [original[1], original[0]]
        assert await publisher.verify_chain() is False

    @pytest.mark.asyncio
    async def test_deleting_a_middle_row_breaks_verification(self, audit_log: None) -> None:
        publisher = events.EventPublisher()
        await _publish(publisher, n=3)
        rows = _rows()
        with db_cursor() as cur:
            cur.execute("DELETE FROM audit_log WHERE seq = ?", (rows[1]["seq"],))
        assert await publisher.verify_chain() is False

    @pytest.mark.asyncio
    async def test_appending_a_forged_row_breaks_verification(self, audit_log: None) -> None:
        publisher = events.EventPublisher()
        await _publish(publisher, n=2)
        with db_cursor() as cur:
            cur.execute(
                """INSERT INTO audit_log
                   (event_id, timestamp, event_type, actor_type, actor_id,
                    action, chain_hash, prev_hash, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "forged",
                    "2026-08-16T10:00:00+00:00",
                    "task.forged",
                    "system",
                    None,
                    "task.forged",
                    "sha256:forged",
                    events.GENESIS_HASH,
                    "{}",
                ),
            )
        assert await publisher.verify_chain() is False
