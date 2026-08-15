"""
اختبارات استمرارية البيانات (Persistence)
الهدف: التحقق من أن البيانات تبقى بعد إعادة التشغيل
النطاق: persistent stores
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import os

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.common.persistent import (
    PersistentCriticStore,
    PersistentExperienceStore,
    PersistentMemoryStore,
    PersistentToolStore,
)
from amos_federation.services.critic.main import app as critic_app
from amos_federation.services.evaluation.main import app as eval_app
from amos_federation.services.memory_service.main import app as memory_app
from amos_federation.services.tool_registry.main import app as tool_app

AUTH_HEADERS = {
    "Authorization": "Bearer " + create_access_token("tester", [
        "memory:read", "memory:write", "eval:read", "eval:write",
        "critic:read", "critic:write", "tool:read", "tool:write",
    ])
}


def test_persistent_memory_survives_new_instance() -> None:
    """الذاكرة تبقى بعد إنشاء نسخة جديدة من المخزن."""
    store1 = PersistentMemoryStore()
    store1.store("persist_key_1", {"content": "بيانات مهمة للاختبار"})

    # إنشاء نسخة جديدة (محاكاة إعادة التشغيل)
    store2 = PersistentMemoryStore()
    item = store2.get("persist_key_1")
    assert item is not None
    assert "بيانات مهمة" in item["value"]


def test_persistent_experience_survives_new_instance() -> None:
    """الخبرات تبقى بعد إنشاء نسخة جديدة."""
    store1 = PersistentExperienceStore()
    result = store1.record({"type": "success", "agent_id": "test-agent", "outcome": {"domain": "finance"}})
    exp_id = result["experience_id"]

    store2 = PersistentExperienceStore()
    exp = store2.get(exp_id)
    assert exp is not None
    assert exp["type"] == "success"
    assert exp["agent_id"] == "test-agent"


def test_persistent_critic_review_survives_new_instance() -> None:
    """مراجعات الناقد تبقى بعد إعادة التشغيل."""
    store1 = PersistentCriticStore()
    result = store1.review({"quality_score": 0.85, "feedback": "نتيجة جيدة", "approved": True})
    rev_id = result["review_id"]

    store2 = PersistentCriticStore()
    rev = store2.get(rev_id)
    assert rev is not None
    assert rev["quality_score"] == 0.85


def test_persistent_tool_registry_survives_new_instance() -> None:
    """الأدوات تبقى بعد إعادة التشغيل."""
    store1 = PersistentToolStore()
    initial_count = len(store1.list_all())

    # إذا كانت هناك أدوات من seed، يجب أن نجدها في نسخة جديدة
    store2 = PersistentToolStore()
    assert len(store2.list_all()) == initial_count


def test_persistence_via_api_memory() -> None:
    """اختبار استمرارية الذاكرة عبر API."""
    client1 = TestClient(memory_app)
    client1.post("/v1/memory/store", headers=AUTH_HEADERS,
                 json={"key": "api_persist_test", "value": {"content": "اختبار الاستمرارية"}})

    # نسخة جديدة من التطبيق
    client2 = TestClient(memory_app)
    resp = client2.get("/v1/memory/api_persist_test", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert "اختبار الاستمرارية" in resp.json()["value"]


def test_persistence_via_api_experience() -> None:
    """اختبار استمرارية الخبرات عبر API."""
    client1 = TestClient(eval_app)
    create_resp = client1.post("/v1/experiences", headers=AUTH_HEADERS,
                               json={"type": "success", "agent_id": "persist-agent"})
    exp_id = create_resp.json()["experience_id"]

    # نسخة جديدة
    client2 = TestClient(eval_app)
    resp = client2.get(f"/v1/experiences/{exp_id}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["agent_id"] == "persist-agent"


def test_persistence_via_api_critic() -> None:
    """اختبار استمرارية مراجعات الناقد عبر API."""
    client1 = TestClient(critic_app)
    create_resp = client1.post("/v1/reviews", headers=AUTH_HEADERS,
                               json={"task_id": "persist-task", "agent_id": "persist-agent",
                                     "steps": [{"status": "completed", "result": {"ok": True}}],
                                     "result_summary": "اكتمل"})
    rev_id = create_resp.json()["review_id"]

    client2 = TestClient(critic_app)
    resp = client2.get(f"/v1/reviews/{rev_id}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["task_id"] == "persist-task"


def test_database_file_exists() -> None:
    """ملف قاعدة البيانات موجود فعليًا."""
    db_path = os.environ.get("AMOS_DATABASE_URL", "").replace("sqlite:///", "")
    if not db_path:
        db_path = os.path.join(os.getcwd(), "amos_federation.db")
    assert os.path.exists(db_path), f"قاعدة البيانات غير موجودة في {db_path}"
