"""
AMOS-Federation Phase 1 Tests: PostgreSQL Persistence
الهدف: اختبار استمرارية البيانات في PostgreSQL عبر جلسات منفصلة
النطاق: federal/executive/services/tests
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

from amos_federation.common.database import (
    AgentModel,
    AuditEntryModel,
    ExperienceModel,
    MemoryModel,
    ReviewModel,
    TaskModel,
    ToolModel,
    get_session_factory,
    init_db,
    reset_engine,
)


def _is_pg():
    """تحقق من أن اختبارات PostgreSQL مفعّلة صراحة."""
    return os.environ.get("AMOS_RUN_POSTGRES_TESTS") == "1" and os.environ.get(
        "AMOS_TEST_DATABASE_URL", ""
    ).startswith("postgresql")


pytestmark = pytest.mark.skipif(
    not _is_pg(),
    reason="Set AMOS_RUN_POSTGRES_TESTS=1 and AMOS_TEST_DATABASE_URL=postgresql://... to run",
)


@pytest.fixture(autouse=True)
def _set_pg_url(monkeypatch: pytest.MonkeyPatch):
    """استخدام AMOS_TEST_DATABASE_URL لهذا الملف وحده، ثم إعادة البيئة كما كانت.

    النسخة السابقة كانت تكتب os.environ مباشرة ولا تردّ القيمة، فتتسرّب لهجة
    PostgreSQL إلى الملفات التالية في نفس الجلسة. monkeypatch يضمن العزل.
    """
    monkeypatch.setenv("AMOS_DATABASE_URL", os.environ["AMOS_TEST_DATABASE_URL"])
    reset_engine()
    yield
    reset_engine()


@pytest.fixture
def pg_session():
    """جلسة PostgreSQL نظيفة لكل اختبار."""
    reset_engine()
    init_db()
    session_factory = get_session_factory()
    session = session_factory()
    yield session
    session.rollback()
    session.close()
    reset_engine()


class TestPostgresPersistence:
    """اختبارات استمرارية البيانات في PostgreSQL."""

    def test_agent_persistence_across_sessions(self, pg_session):
        """الوكيل يبقى بعد إغلاق الجلسة."""
        agent_id = str(uuid.uuid4())
        agent = AgentModel(
            id=agent_id,
            name="Persist Agent",
            role="executor",
            permissions=["read"],
            token_budget=5000,
        )
        pg_session.add(agent)
        pg_session.commit()

        # محاكاة إعادة تشغيل
        pg_session.close()
        reset_engine()
        init_db()
        session_factory = get_session_factory()
        new_session = session_factory()
        found = new_session.query(AgentModel).filter_by(id=agent_id).first()
        assert found is not None
        assert found.name == "Persist Agent"
        assert found.role == "executor"
        new_session.delete(found)
        new_session.commit()
        new_session.close()

    def test_all_models_crud(self, pg_session):
        """كل النماذج السبعة تدعم CRUD."""
        test_id = str(uuid.uuid4())

        # Create
        agent = AgentModel(id=test_id, name="CRUD Agent", role="guardian")
        tool = ToolModel(id=f"t-{test_id[:8]}", name=f"crud_tool_{test_id[:8]}")
        task = TaskModel(id=test_id, type="test", description="CRUD test")
        mem = MemoryModel(key=f"m-{test_id[:8]}", value="crud memory")
        exp = ExperienceModel(id=test_id, type="success")
        review = ReviewModel(id=test_id, quality_score=0.9)
        import hashlib

        audit = AuditEntryModel(
            id=test_id,
            action="crud_test",
            actor="test",
            hash=hashlib.sha256(b"crud").hexdigest(),
        )

        pg_session.add_all([agent, tool, task, mem, exp, review, audit])
        pg_session.commit()

        # Read
        assert pg_session.query(AgentModel).filter_by(id=test_id).first() is not None
        assert pg_session.query(ToolModel).filter_by(id=f"t-{test_id[:8]}").first() is not None
        assert pg_session.query(TaskModel).filter_by(id=test_id).first() is not None
        assert pg_session.query(MemoryModel).filter_by(key=f"m-{test_id[:8]}").first() is not None
        assert pg_session.query(ExperienceModel).filter_by(id=test_id).first() is not None
        assert pg_session.query(ReviewModel).filter_by(id=test_id).first() is not None
        assert pg_session.query(AuditEntryModel).filter_by(id=test_id).first() is not None

        # Update
        agent_row = pg_session.query(AgentModel).filter_by(id=test_id).first()
        agent_row.status = "active"
        pg_session.commit()
        assert pg_session.query(AgentModel).filter_by(id=test_id).first().status == "active"

        # Delete
        pg_session.query(AgentModel).filter_by(id=test_id).delete()
        pg_session.query(ToolModel).filter_by(id=f"t-{test_id[:8]}").delete()
        pg_session.query(TaskModel).filter_by(id=test_id).delete()
        pg_session.query(MemoryModel).filter_by(key=f"m-{test_id[:8]}").delete()
        pg_session.query(ExperienceModel).filter_by(id=test_id).delete()
        pg_session.query(ReviewModel).filter_by(id=test_id).delete()
        pg_session.query(AuditEntryModel).filter_by(id=test_id).delete()
        pg_session.commit()

        assert pg_session.query(AgentModel).filter_by(id=test_id).first() is None

    def test_engine_restart_preserves_data(self, pg_session):
        """إعادة تعيين المحرك لا تضيع البيانات."""
        agent_id = str(uuid.uuid4())
        agent = AgentModel(id=agent_id, name="Restart Test", role="clerk")
        pg_session.add(agent)
        pg_session.commit()
        pg_session.close()

        # إعادة تعيين كاملة
        reset_engine()
        init_db()
        session_factory = get_session_factory()
        s2 = session_factory()
        found = s2.query(AgentModel).filter_by(id=agent_id).first()
        assert found is not None
        assert found.name == "Restart Test"
        s2.delete(found)
        s2.commit()
        s2.close()

    def test_json_columns_persist(self, pg_session):
        """أعمدة JSON تُحفظ وتُقرأ بشكل صحيح."""
        agent_id = str(uuid.uuid4())
        agent = AgentModel(
            id=agent_id,
            name="JSON Agent",
            role="executor",
            permissions=["read", "write", "admin"],
            allowed_tools=["python_execute", "file_read"],
        )
        pg_session.add(agent)
        pg_session.commit()

        pg_session.close()
        reset_engine()
        init_db()
        session_factory = get_session_factory()
        s2 = session_factory()
        found = s2.query(AgentModel).filter_by(id=agent_id).first()
        assert found is not None
        assert "read" in found.permissions
        assert "write" in found.permissions
        assert "admin" in found.permissions
        assert "python_execute" in found.allowed_tools
        s2.delete(found)
        s2.commit()
        s2.close()


class TestServiceLevelPersistence:
    """اختبارات استمرارية على مستوى الخدمة (عبر stores فعلية)."""

    def test_tool_registry_persists_tool_across_restart(self, pg_session):
        """PersistentToolStore يكتب ويقرأ من PostgreSQL عبر إعادة تشغيل."""
        from amos_federation.common.persistent import PersistentToolStore

        PersistentToolStore()  # verify store initializes
        tool_id = f"svc-test-{uuid.uuid4().hex[:8]}"
        tool_name = f"svc_tool_{tool_id}"

        # Create tool via store's session (not direct ORM)
        session = get_session_factory()()
        from amos_federation.common.database import ToolModel

        tool = ToolModel(id=tool_id, name=tool_name, description="service test", category="test")
        session.add(tool)
        session.commit()
        session.close()

        # Restart engine and read back via PersistentToolStore
        reset_engine()
        init_db()
        session2 = get_session_factory()()
        found = session2.query(ToolModel).filter_by(id=tool_id).first()
        assert found is not None
        assert found.name == tool_name
        session2.query(ToolModel).filter_by(id=tool_id).delete()
        session2.commit()
        session2.close()

    def test_task_store_persists_across_restart(self, pg_session):
        """PersistentTaskStore يكتب ويقرأ من PostgreSQL عبر إعادة تشغيل."""
        from amos_federation.common.persistent import PersistentTaskStore

        store = PersistentTaskStore()
        task_id = f"svc-task-{uuid.uuid4().hex[:8]}"
        store.create(task_id, "test", "Service-level persistence test")

        # Restart
        reset_engine()
        init_db()
        result = store.get(task_id)
        assert result is not None
        assert result["id"] == task_id
        assert result["description"] == "Service-level persistence test"

        # Cleanup
        from amos_federation.common.database import TaskModel

        session = get_session_factory()()
        session.query(TaskModel).filter_by(id=task_id).delete()
        session.commit()
        session.close()

    def test_api_gateway_task_create_and_read(self, pg_session):
        """API Gateway DatabaseTaskStore يكتب ويقرأ من PostgreSQL عبر TaskModel."""
        from amos_federation.common.schemas import TaskDetails
        from amos_federation.services.api_gateway.store import DatabaseTaskStore

        adapter = DatabaseTaskStore()
        task = TaskDetails(
            task_id=f"api-test-{uuid.uuid4().hex[:8]}",
            type="analysis",
            description="API Gateway persistence test",
            priority="normal",
            status="pending",
            domain="general",
            tenant_id="default",
            result={},
            created_at=datetime.now(UTC),
        )

        adapter.create(task)

        # Restart
        reset_engine()
        init_db()
        found = adapter.get(task.task_id)
        assert found is not None
        assert found.task_id == task.task_id
        assert found.description == "API Gateway persistence test"

        # Cleanup
        from amos_federation.common.database import TaskModel

        session = get_session_factory()()
        session.query(TaskModel).filter_by(id=task.task_id).delete()
        session.commit()
        session.close()

    def test_api_gateway_preserves_non_default_fields(self, pg_session):
        """API Gateway يحفظ ويقرأ الحقول غير الافتراضية (priority, domain, tenant_id, status)."""
        from amos_federation.common.schemas import TaskDetails
        from amos_federation.services.api_gateway.store import DatabaseTaskStore

        adapter = DatabaseTaskStore()
        task = TaskDetails(
            task_id=f"api-fields-{uuid.uuid4().hex[:8]}",
            type="report",
            description="Non-default fields persistence test",
            priority="high",
            status="pending",
            domain="finance",
            tenant_id="finance",
            result={},
            created_at=datetime.now(UTC),
        )

        adapter.create(task)

        # Restart
        reset_engine()
        init_db()
        found = adapter.get(task.task_id)
        assert found is not None
        assert found.task_id == task.task_id
        assert found.priority == "high"
        assert found.status == "pending"
        assert found.domain == "finance"
        assert found.tenant_id == "finance"
        assert found.description == "Non-default fields persistence test"

        # Cleanup
        from amos_federation.common.database import TaskModel

        session = get_session_factory()()
        session.query(TaskModel).filter_by(id=task.task_id).delete()
        session.commit()
        session.close()
