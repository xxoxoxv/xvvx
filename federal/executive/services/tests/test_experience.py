"""
اختبارات خدمة التقييم والخبرات
الهدف: التحقق من تسجيل واسترجاع وفلترة الخبرات
النطاق: services/evaluation
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.evaluation.main import app

client = TestClient(app)
AUTH_HEADERS = {
    "Authorization": "Bearer "
    + create_access_token("tester", ["experience:read", "experience:write"])
}


def test_record_and_get_experience() -> None:
    """تسجيل خبرة ثم استرجاعها."""
    record_resp = client.post(
        "/v1/experiences",
        headers=AUTH_HEADERS,
        json={
            "task_id": "task-exp-001",
            "type": "success",
            "agent_id": "worker-analyst",
            "outcome": {"result": "تحليل ناجح", "steps_completed": 3},
            "quality_score": 0.92,
        },
    )
    assert record_resp.status_code == 201
    exp_id = record_resp.json()["experience_id"]
    assert exp_id.startswith("exp-")

    get_resp = client.get(f"/v1/experiences/{exp_id}", headers=AUTH_HEADERS)
    assert get_resp.status_code == 200
    assert get_resp.json()["type"] == "success"
    assert get_resp.json()["quality_score"] == 0.92


def test_record_failure_experience() -> None:
    """تسجيل خبرة فشل."""
    resp = client.post(
        "/v1/experiences",
        headers=AUTH_HEADERS,
        json={
            "task_id": "task-exp-002",
            "type": "failure",
            "agent_id": "worker-researcher",
            "outcome": {"error": "انتهت مهلة الاتصال"},
            "quality_score": 0.1,
        },
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "failure"


def test_record_gap_experience() -> None:
    """تسجيل خبرة فجوة معرفية."""
    resp = client.post(
        "/v1/experiences",
        headers=AUTH_HEADERS,
        json={
            "task_id": "task-exp-003",
            "type": "gap",
            "outcome": {"missing": "بيانات السوق غير متاحة"},
        },
    )
    assert resp.status_code == 201
    assert resp.json()["type"] == "gap"


def test_filter_by_type() -> None:
    """فلترة الخبرات بال نوع."""
    # تسجيل خبرات متنوعة
    for t in ["success", "failure", "success"]:
        client.post(
            "/v1/experiences",
            headers=AUTH_HEADERS,
            json={"type": t, "outcome": {"test": True}},
        )
    resp = client.get("/v1/experiences?type=success", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    for exp in resp.json():
        assert exp["type"] == "success"


def test_filter_by_min_score() -> None:
    """فلترة الخبرات بحد أدنى للجودة."""
    client.post(
        "/v1/experiences",
        headers=AUTH_HEADERS,
        json={"type": "success", "quality_score": 0.95, "outcome": {}},
    )
    client.post(
        "/v1/experiences",
        headers=AUTH_HEADERS,
        json={"type": "success", "quality_score": 0.3, "outcome": {}},
    )
    resp = client.get("/v1/experiences?min_score=0.8", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    for exp in resp.json():
        assert exp["quality_score"] >= 0.8


def test_filter_by_agent() -> None:
    """فلترة الخبرات بالوكيل."""
    client.post(
        "/v1/experiences",
        headers=AUTH_HEADERS,
        json={"type": "success", "agent_id": "agent-xyz", "outcome": {}},
    )
    resp = client.get("/v1/experiences?agent_id=agent-xyz", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    for exp in resp.json():
        assert exp["agent_id"] == "agent-xyz"


def test_get_nonexistent_returns_404() -> None:
    """خبرة غير موجودة تعيد 404."""
    resp = client.get("/v1/experiences/nonexistent", headers=AUTH_HEADERS)
    assert resp.status_code == 404


def test_provenance_tracking() -> None:
    """تتبع المصدر يُسجل تلقائيًا."""
    resp = client.post(
        "/v1/experiences",
        headers=AUTH_HEADERS,
        json={"type": "success", "outcome": {"data": "test"}},
    )
    assert resp.status_code == 201
    provenance = resp.json()["provenance"]
    assert "source" in provenance
    assert "recorded_at" in provenance


def test_run_evaluation() -> None:
    """تشغيل التقييم يعيد إحصائيات."""
    resp = client.post("/v1/evaluations/run", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert "total_experiences" in resp.json()
    assert "by_type" in resp.json()


def test_record_rejects_invalid_type() -> None:
    """نوع غير صالح يُرفض."""
    resp = client.post(
        "/v1/experiences",
        headers=AUTH_HEADERS,
        json={"type": "invalid_type", "outcome": {}},
    )
    assert resp.status_code == 422


def test_record_rejects_missing_auth() -> None:
    """التسجيل يتطلب مصادقة."""
    resp = client.post("/v1/experiences", json={"type": "success", "outcome": {}})
    assert resp.status_code == 401
