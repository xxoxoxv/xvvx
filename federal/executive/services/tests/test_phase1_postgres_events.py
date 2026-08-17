"""
AMOS-Federation Phase 1 Tests: Events + SQL layer on real PostgreSQL
الهدف: إثبات أن طبقة SQL الموحّدة (db_cursor + audit_log + events) تعمل على PostgreSQL فعلًا
النطاق: federal/executive/services/tests
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16

هذه الاختبارات هي الدليل الوحيد المقبول على عبارة «PostgreSQL مدعوم» في مسار
الأحداث. لا تُعلن العبارة إن سقط أي اختبار هنا. لا تُشغَّل إلا عند تفعيل
AMOS_RUN_POSTGRES_TESTS=1 مع AMOS_TEST_DATABASE_URL، وتستخدم التجهيزة
postgres_url فقط — فلا تؤثر على أي اختبار آخر في الحزمة.
"""

import json
import uuid

import pytest

from amos_federation.common import events
from amos_federation.common.database import (
    DIALECT_POSTGRES,
    db_cursor,
    db_dialect,
    drop_audit_log_table,
    ensure_audit_log_table,
)


@pytest.fixture
def pg_audit_log(postgres_url: str):
    """جدول audit_log نظيف على PostgreSQL الحقيقي، ويُزال بعد الاختبار."""
    drop_audit_log_table()
    ensure_audit_log_table()
    yield postgres_url
    drop_audit_log_table()


def _insert_row(event_id: str, chain_hash: str, prev_hash: str, metadata: dict) -> None:
    """إدراج صف بالمحاجيز القانونية «?» — نفس الشكل المستخدم في مسار الإنتاج."""
    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO audit_log (event_id, chain_hash, prev_hash, metadata) "
            "VALUES (?, ?, ?, ?)",
            (event_id, chain_hash, prev_hash, json.dumps(metadata, ensure_ascii=False)),
        )


class TestPortableCursorOnPostgres:
    """المؤشر المحايد يعمل على PostgreSQL بنفس الـ SQL المكتوب لـ SQLite."""

    def test_dialect_is_postgres(self, postgres_url: str) -> None:
        assert db_dialect() == DIALECT_POSTGRES
        with db_cursor() as cur:
            assert cur.dialect == DIALECT_POSTGRES

    def test_qmark_placeholders_round_trip(self, pg_audit_log: str) -> None:
        event_id = f"pg-{uuid.uuid4().hex[:12]}"
        _insert_row(event_id, "sha256:aaa", events.GENESIS_HASH, {"k": "v"})
        with db_cursor() as cur:
            cur.execute("SELECT chain_hash FROM audit_log WHERE event_id = ?", (event_id,))
            row = cur.fetchone()
        assert row is not None
        assert row["chain_hash"] == "sha256:aaa"

    def test_rows_are_mappings(self, pg_audit_log: str) -> None:
        event_id = f"pg-{uuid.uuid4().hex[:12]}"
        _insert_row(event_id, "sha256:bbb", events.GENESIS_HASH, {})
        with db_cursor() as cur:
            cur.execute("SELECT event_id, chain_hash FROM audit_log")
            rows = cur.fetchall()
        assert isinstance(rows[0], dict)
        assert rows[0]["event_id"] == event_id


class TestAuditLogSchemaOnPostgres:
    """تعريف audit_log الموحّد ينشئ الجدول وعمود الترتيب الرتيب على PostgreSQL."""

    def test_seq_column_exists_and_is_monotonic(self, pg_audit_log: str) -> None:
        ids = [f"pg-{uuid.uuid4().hex[:12]}" for _ in range(3)]
        for index, event_id in enumerate(ids):
            _insert_row(event_id, f"sha256:{index}", events.GENESIS_HASH, {})
        with db_cursor() as cur:
            cur.execute("SELECT event_id, seq FROM audit_log ORDER BY seq ASC")
            rows = cur.fetchall()
        assert [row["event_id"] for row in rows] == ids
        seqs = [row["seq"] for row in rows]
        assert seqs == sorted(seqs)


class TestChainHashOnPostgres:
    """سلسلة البصمات تقرأ الصف الأخير الصحيح — لا صفًّا عشوائيًا بترتيب UUID."""

    def test_genesis_when_table_empty(self, pg_audit_log: str) -> None:
        assert events.get_last_chain_hash() == events.GENESIS_HASH

    def test_last_hash_follows_insertion_order(self, pg_audit_log: str) -> None:
        # ثلاثة صفوف متتالية: يجب أن تعود بصمة الأخير إدراجًا، لا الأكبر UUID
        for index in range(3):
            _insert_row(f"pg-{uuid.uuid4().hex[:12]}", f"sha256:step{index}", "sha256:prev", {})
        assert events.get_last_chain_hash() == "sha256:step2"


class TestPublisherPersistenceOnPostgres:
    """publish() يكتب فعليًا في audit_log على PostgreSQL بلا رجوع صامت."""

    @pytest.mark.asyncio
    async def test_publish_persists_audit_row(self, pg_audit_log: str) -> None:
        publisher = events.EventPublisher()
        event_id = await publisher.publish(
            event_type="task.created",
            source="api-gateway",
            data={"task_id": "pg-task-1"},
            actor_type="system",
            actor_id="sys",
        )
        with db_cursor() as cur:
            cur.execute(
                "SELECT event_type, actor_type, actor_id, metadata, chain_hash, prev_hash "
                "FROM audit_log WHERE event_id = ?",
                (event_id,),
            )
            row = cur.fetchone()
        assert row is not None, "publish() لم يُثبت الصف على PostgreSQL"
        assert row["event_type"] == "task.created"
        assert row["actor_type"] == "system"
        assert row["actor_id"] == "sys"
        assert row["prev_hash"] == events.GENESIS_HASH
        assert row["chain_hash"].startswith("sha256:")
        # عمود JSONB يعود قاموسًا من psycopg2
        metadata = row["metadata"]
        if isinstance(metadata, str):
            metadata = json.loads(metadata)
        assert metadata == {"task_id": "pg-task-1"}

    @pytest.mark.asyncio
    async def test_publish_chains_prev_hash_across_events(self, pg_audit_log: str) -> None:
        publisher = events.EventPublisher()
        first = await publisher.publish("task.created", "api-gateway", {"n": 1})
        second = await publisher.publish("task.created", "api-gateway", {"n": 2})
        with db_cursor() as cur:
            cur.execute("SELECT event_id, chain_hash, prev_hash FROM audit_log ORDER BY seq ASC")
            rows = cur.fetchall()
        assert [row["event_id"] for row in rows] == [first, second]
        assert rows[0]["prev_hash"] == events.GENESIS_HASH
        # الحدث الثاني يربط ببصمة الأول — يثبت أن قراءة آخر بصمة تعمل على PostgreSQL
        assert rows[1]["prev_hash"] == rows[0]["chain_hash"]


class TestVerifyChainOnPostgres:
    """verify_chain() يميّز السلسلة السليمة من المتلاعب بها على PostgreSQL."""

    @pytest.mark.asyncio
    async def test_verify_chain_true_for_valid_chain(self, pg_audit_log: str) -> None:
        metadata = {"task_id": "pg-t-1"}
        # نفس التمثيل القانوني الذي يبنيه publish ويعيد verify_chain بناءه.
        chain_hash = events.compute_chain_hash(
            events.GENESIS_HASH,
            events.canonical_audit_record(
                event_id="pg-e1",
                timestamp=None,
                event_type=None,
                actor_type=None,
                actor_id=None,
                action=None,
                metadata=metadata,
            ),
        )
        _insert_row("pg-e1", chain_hash, events.GENESIS_HASH, metadata)
        publisher = events.EventPublisher()
        assert await publisher.verify_chain() is True

    @pytest.mark.asyncio
    async def test_verify_chain_false_for_tampered_chain(self, pg_audit_log: str) -> None:
        _insert_row("pg-e1", "sha256:tampered", events.GENESIS_HASH, {})
        publisher = events.EventPublisher()
        assert await publisher.verify_chain() is False

    @pytest.mark.asyncio
    async def test_verify_chain_false_without_table(self, postgres_url: str) -> None:
        drop_audit_log_table()
        publisher = events.EventPublisher()
        assert await publisher.verify_chain() is False


# =============================================================================
# السجل القانوني الواحد على PostgreSQL — قرار E2.2-G
# =============================================================================
class TestCanonicalAuditRecordOnPostgres:
    """publish وverify_chain يبنيان نفس التمثيل القانوني على PostgreSQL أيضًا.

    هذا مهم على PostgreSQL تحديدًا لأن `metadata` عمود JSONB يعود قاموسًا،
    لا نصًّا كما في SQLite — فلو لم يكن التوحيد حقيقيًّا لانكسر التحقق هنا وحده.
    """

    @pytest.mark.asyncio
    async def test_published_chain_verifies_on_postgres(self, pg_audit_log: str) -> None:
        publisher = events.EventPublisher()
        for index in range(3):
            await publisher.publish(
                f"pg.step{index}",
                "test-suite",
                {"index": index, "note": "قيمة عربية"},
                actor_type="system",
                actor_id=f"actor-{index}",
            )
        with db_cursor() as cur:
            cur.execute("SELECT event_id, chain_hash, prev_hash FROM audit_log ORDER BY seq ASC")
            rows = cur.fetchall()
        assert len(rows) == 3
        assert rows[0]["prev_hash"] == events.GENESIS_HASH
        assert rows[1]["prev_hash"] == rows[0]["chain_hash"]
        assert await publisher.verify_chain() is True

    @pytest.mark.asyncio
    async def test_jsonb_metadata_canonicalizes_like_text(self, pg_audit_log: str) -> None:
        publisher = events.EventPublisher()
        await publisher.publish("pg.one", "test-suite", {"b": 2, "a": 1})
        with db_cursor() as cur:
            columns = ", ".join(events.CANONICAL_AUDIT_FIELDS)
            cur.execute(f"SELECT {columns} FROM audit_log ORDER BY seq ASC")
            row = cur.fetchone()
        # العمود JSONB يعود قاموسًا فعلًا، والتمثيل القانوني يوحّده مع مسار النص.
        assert isinstance(row["metadata"], dict)
        rebuilt = events.canonical_audit_record_from_row(row)
        assert rebuilt["metadata"] == {"a": 1, "b": 2}
        assert await publisher.verify_chain() is True

    @pytest.mark.asyncio
    async def test_tampering_metadata_breaks_verification_on_postgres(
        self, pg_audit_log: str
    ) -> None:
        publisher = events.EventPublisher()
        await publisher.publish("pg.one", "test-suite", {"index": 1})
        assert await publisher.verify_chain() is True
        with db_cursor() as cur:
            cur.execute("UPDATE audit_log SET metadata = ?", (json.dumps({"index": 999}),))
        assert await publisher.verify_chain() is False

    @pytest.mark.asyncio
    async def test_swapping_seq_breaks_verification_on_postgres(self, pg_audit_log: str) -> None:
        publisher = events.EventPublisher()
        for index in range(3):
            await publisher.publish(f"pg.step{index}", "test-suite", {"index": index})
        assert await publisher.verify_chain() is True
        with db_cursor() as cur:
            cur.execute("SELECT seq FROM audit_log ORDER BY seq ASC")
            seqs = [row["seq"] for row in cur.fetchall()]
            spare = max(seqs) + 1000
            cur.execute("UPDATE audit_log SET seq = ? WHERE seq = ?", (spare, seqs[0]))
            cur.execute("UPDATE audit_log SET seq = ? WHERE seq = ?", (seqs[0], seqs[1]))
            cur.execute("UPDATE audit_log SET seq = ? WHERE seq = ?", (seqs[1], spare))
        # الترتيب الأساسي للسلسلة هو seq — تبديله وحده يكسر التحقق.
        assert await publisher.verify_chain() is False


class TestTaskModelIsSourceOfTruthOnPostgres:
    """جدول tasks على PostgreSQL يُكتب ويُقرأ عبر TaskModel وحده."""

    def test_tasks_table_has_no_competing_task_id_column(self, postgres_url: str) -> None:
        from amos_federation.common.database import TaskModel, init_db

        init_db()
        columns = {column.name for column in TaskModel.__table__.columns}
        assert "task_id" not in columns
        assert "id" in columns

    def test_create_then_get_persists_on_postgres(self, postgres_url: str) -> None:
        from datetime import UTC, datetime

        from amos_federation.common.schemas import TaskDetails
        from amos_federation.services.api_gateway.store import DatabaseTaskStore

        task_id = f"pg-task-{uuid.uuid4().hex[:12]}"
        task = TaskDetails(
            task_id=task_id,
            type="analysis",
            description="مهمة إثبات على PostgreSQL",
            priority="normal",
            status="pending",
            domain="federal",
            tenant_id="default",
            created_at=datetime.now(UTC),
            result=None,
        )
        DatabaseTaskStore().create(task)
        # مثيل جديد تمامًا: القراءة من القاعدة لا من ذاكرة الكائن.
        fetched = DatabaseTaskStore().get(task_id)
        assert fetched is not None
        assert fetched.task_id == task_id
        assert fetched.description == "مهمة إثبات على PostgreSQL"
