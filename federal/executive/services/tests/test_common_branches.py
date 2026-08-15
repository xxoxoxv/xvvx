"""
اختبارات الأفرع للوحدات المشتركة
الهدف: رفع تغطية الأفرع لـ events / database / api_gateway store
النطاق: common + api_gateway
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import os

import pytest

from amos_federation.common import events
from amos_federation.common.database import (
    db_cursor,
    get_database_url,
    get_engine,
    _is_postgres,
    _pg_connect_args,
    reset_engine,
)
from amos_federation.common.schemas import TaskDetails
from amos_federation.services.api_gateway.store import (
    InMemoryTaskStore,
    PostgresTaskStore,
)
import json as _json

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from amos_federation.common import auth
from amos_federation.common.event_schemas import (
    _has_required_fields,
    load_event_schema,
    validate_event,
)


def _ensure_audit_log_table() -> None:
    """إنشاء جدول audit_log في قاعدة بيانات الاختبار لتغطية مسار النجاح."""
    with db_cursor() as cur:
        cur.execute(
            """CREATE TABLE IF NOT EXISTS audit_log (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   event_id TEXT,
                   timestamp TEXT,
                   event_type TEXT,
                   actor_type TEXT,
                   actor_id TEXT,
                   action TEXT,
                   chain_hash TEXT,
                   prev_hash TEXT,
                   metadata TEXT
               )"""
        )


def _drop_audit_log_table() -> None:
    """إزالة جدول audit_log لإعادة الحالة الافتراضية للاختبارات الأخرى."""
    with db_cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS audit_log")


# =============================================================================
# events.py
# =============================================================================
class TestEventChainHash:
    def test_compute_chain_hash_is_deterministic(self) -> None:
        data = {"event_id": "e1", "type": "task.created"}
        h1 = events.compute_chain_hash("sha256:prev", data)
        h2 = events.compute_chain_hash("sha256:prev", data)
        assert h1 == h2
        assert h1.startswith("sha256:")

    def test_compute_chain_hash_changes_with_input(self) -> None:
        base = {"event_id": "e1"}
        assert events.compute_chain_hash("a", base) != events.compute_chain_hash("b", base)


class TestEventPublisher:
    def test_get_last_chain_hash_falls_back_to_genesis(self) -> None:
        # No audit_log table in test DB -> except branch -> GENESIS_HASH
        assert events.get_last_chain_hash() == events.GENESIS_HASH

    @pytest.mark.asyncio
    async def test_publish_uses_fallback_bus_and_skips_audit(self) -> None:
        publisher = events.EventPublisher()
        event_id = await publisher.publish(
            event_type="task.created",
            source="api-gateway",
            data={"task_id": "t-1"},
            actor_type="system",
            actor_id="sys",
        )
        assert event_id  # uuid string returned
        # publisher never connected -> _nc None, _local_bus None -> fallback path

    @pytest.mark.asyncio
    async def test_verify_chain_returns_false_without_audit_table(self) -> None:
        publisher = events.EventPublisher()
        # No audit_log table -> except -> False
        assert await publisher.verify_chain() is False

    @pytest.mark.asyncio
    async def test_verify_chain_success_with_valid_chain(self) -> None:
        _ensure_audit_log_table()
        try:
            publisher = events.EventPublisher()
            metadata = {"task_id": "t-1"}
            chain_hash = events.compute_chain_hash(
                events.GENESIS_HASH, {"event_id": "e1", "metadata": metadata}
            )
            with db_cursor() as cur:
                cur.execute(
                    "INSERT INTO audit_log (event_id, chain_hash, prev_hash, metadata) "
                    "VALUES (?, ?, ?, ?)",
                    ("e1", chain_hash, events.GENESIS_HASH, _json.dumps(metadata)),
                )
            # valid chain -> returns True (covers loop + chain.verified)
            assert await publisher.verify_chain() is True
        finally:
            _drop_audit_log_table()

    @pytest.mark.asyncio
    async def test_verify_chain_detects_broken_chain(self) -> None:
        _ensure_audit_log_table()
        try:
            publisher = events.EventPublisher()
            with db_cursor() as cur:
                cur.execute(
                    "INSERT INTO audit_log (event_id, chain_hash, prev_hash, metadata) "
                    "VALUES (?, ?, ?, ?)",
                    ("e1", "sha256:tampered", events.GENESIS_HASH, "{}"),
                )
            # tampered hash -> returns False (covers chain.broken branch)
            assert await publisher.verify_chain() is False
        finally:
            _drop_audit_log_table()

    def test_get_last_chain_hash_returns_existing_row(self) -> None:
        _ensure_audit_log_table()
        try:
            with db_cursor() as cur:
                cur.execute(
                    "INSERT INTO audit_log (event_id, chain_hash, prev_hash, metadata) "
                    "VALUES (?, ?, ?, ?)",
                    ("e1", "sha256:existinghash", events.GENESIS_HASH, "{}"),
                )
            # existing row -> returns its chain_hash (covers `if row` True branch)
            assert events.get_last_chain_hash() == "sha256:existinghash"
        finally:
            _drop_audit_log_table()


# =============================================================================
# database.py
# =============================================================================
class TestDatabaseHelpers:
    def test_get_database_url_uses_env(self) -> None:
        assert get_database_url().startswith("sqlite")

    def test_get_database_url_default_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("AMOS_DATABASE_URL", raising=False)
        url = get_database_url()
        assert url.startswith("sqlite:///")

    def test_is_postgres_false_for_sqlite(self) -> None:
        assert _is_postgres() is False

    def test_pg_connect_args_sqlite_branch(self) -> None:
        # sqlite branch returns check_same_thread=False
        args = _pg_connect_args()
        assert args == {"check_same_thread": False}

    def test_get_engine_returns_sqlite_engine(self) -> None:
        try:
            engine = get_engine()
            assert engine is not None
            assert "sqlite" in str(engine.url)
        finally:
            reset_engine()

    def test_db_cursor_sqlite_path(self) -> None:
        with db_cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS _t (id INTEGER)")
            cur.execute("INSERT INTO _t VALUES (1)")
        # context manager commits and closes without error


# =============================================================================
# api_gateway/store.py
# =============================================================================
def _make_task() -> TaskDetails:
    return TaskDetails(
        task_id="task-test-1",
        type="analysis",
        description="تحليل تجريبي",
        priority="high",
        status="created",
        domain="finance",
        tenant_id="default",
        created_at="2026-08-15T00:00:00Z",
        result=None,
    )


class TestInMemoryTaskStore:
    def test_create_and_get(self) -> None:
        store = InMemoryTaskStore()
        task = _make_task()
        store.create(task)
        assert store.get("task-test-1") is not None
        assert store.get("missing") is None


class TestPostgresTaskStoreFallback:
    def test_create_falls_back_to_memory(self) -> None:
        store = PostgresTaskStore(fallback=InMemoryTaskStore())
        task = _make_task()
        result = store.create(task)
        # No tasks table in sqlite -> except -> fallback.create
        assert result.task_id == "task-test-1"

    def test_get_falls_back_to_memory(self) -> None:
        fallback = InMemoryTaskStore()
        fallback.create(_make_task())
        store = PostgresTaskStore(fallback=fallback)
        # SELECT raises -> except -> fallback.get
        assert store.get("task-test-1") is not None
        assert store.get("missing") is None


# =============================================================================
# auth.py
# =============================================================================
def _creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


class TestAuthTokens:
    def test_create_and_decode_king_token(self) -> None:
        token = auth.create_king_token()
        data = auth.decode_token(token)
        assert data["role"] == auth.ROLE_KING
        assert data["sub"] == "king"

    def test_decode_invalid_token_raises_401(self) -> None:
        with pytest.raises(HTTPException) as exc:
            auth.decode_token("not-a-valid-token")
        assert exc.value.status_code == 401

    def test_require_king_allows_king(self) -> None:
        token = auth.create_king_token()
        data = auth.require_king(credentials=_creds(token))
        assert data["role"] == auth.ROLE_KING

    def test_require_king_rejects_citizen(self) -> None:
        token = auth.create_access_token(subject="u1", scopes=[], role=auth.ROLE_CITIZEN)
        with pytest.raises(HTTPException) as exc:
            auth.require_king(credentials=_creds(token))
        assert exc.value.status_code == 403

    def test_require_king_rejects_missing_credentials(self) -> None:
        with pytest.raises(HTTPException) as exc:
            auth.require_king(credentials=None)
        assert exc.value.status_code == 401

    def test_require_role_checker_king_bypass(self) -> None:
        checker = auth.require_role("admin")
        token = auth.create_king_token()
        data = checker(credentials=_creds(token))
        assert data["role"] == auth.ROLE_KING

    def test_require_role_checker_rejects_unauthorized_role(self) -> None:
        checker = auth.require_role("admin")
        token = auth.create_access_token(subject="u1", scopes=[], role=auth.ROLE_CITIZEN)
        with pytest.raises(HTTPException) as exc:
            checker(credentials=_creds(token))
        assert exc.value.status_code == 403


# =============================================================================
# event_schemas.py
# =============================================================================
class TestEventSchemas:
    def test_load_event_schema_returns_dict(self) -> None:
        schema = load_event_schema("task.created")
        assert schema["type"] == "object"

    def test_validate_event_rejects_non_dict(self) -> None:
        assert validate_event("task.created", "not-a-dict") is False

    def test_validate_event_rejects_wrong_const(self) -> None:
        payload = {
            "event_id": "e1",
            "timestamp": "2026-08-15T00:00:00Z",
            "event_type": "wrong.type",
            "source": "api-gateway",
            "data": {"task_id": "t1", "type": "analysis", "description": "x"},
            "chain_hash": "sha256:" + "a" * 64,
        }
        assert validate_event("task.created", payload) is False

    def test_validate_event_unknown_type_returns_false(self) -> None:
        assert validate_event("unknown.event.type", {"a": 1}) is False

    def test_has_required_fields_non_dict(self) -> None:
        assert _has_required_fields({"required": ["a"]}, 42) is False
