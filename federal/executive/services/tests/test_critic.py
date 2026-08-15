"""
اختبارات خدمة الناقد
الهدف: التحقق من مراجعة النتائج وتقييم الجودة
النطاق: services/critic
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.critic.main import app

client = TestClient(app)
AUTH_HEADERS = {
    "Authorization": "Bearer " + create_access_token("tester", ["critic:read", "critic:write"])
}


def _good_review_request() -> dict:
    """طلب مراجعة بنتيجة جيدة."""
    return {
        "task_id": "task-critic-001",
        "agent_id": "worker-analyst",
        "steps": [
            {"number": 1, "status": "completed", "result": {"data": "ok"}, "tool": "sql_query"},
            {"number": 2, "status": "completed", "result": {"stats": {}}, "tool": "data_analysis"},
            {"number": 3, "status": "completed", "result": {"path": "/tmp/chart.png"}, "tool": "chart_generate"},
        ],
        "result_summary": "اكتملت 3/3 خطوة",
    }


def _poor_review_request() -> dict:
    """طلب مراجعة بنتيجة ضعيفة."""
    return {
        "task_id": "task-critic-002",
        "agent_id": "worker-researcher",
        "steps": [
            {"number": 1, "status": "skipped", "result": None, "tool": "unknown"},
            {"number": 2, "status": "completed", "result": {"error": "timeout"}, "tool": "research_apis"},
        ],
        "result_summary": "",
    }


def test_review_good_result_gets_high_score() -> None:
    """النتيجة الجيدة تحصل على درجة عالية وموافقة."""
    resp = client.post("/v1/reviews", headers=AUTH_HEADERS, json=_good_review_request())
    assert resp.status_code == 201
    data = resp.json()
    assert data["quality_score"] >= 0.7
    assert data["approved"] is True
    assert "review_id" in data
    assert data["task_id"] == "task-critic-001"


def test_review_poor_result_gets_low_score() -> None:
    """النتيجة الضعيفة تحصل على درجة منخفضة ورفض."""
    resp = client.post("/v1/reviews", headers=AUTH_HEADERS, json=_poor_review_request())
    assert resp.status_code == 201
    data = resp.json()
    assert data["quality_score"] < 0.7
    assert data["approved"] is False


def test_review_consistency() -> None:
    """نفس المدخلات تنتج نفس الدرجة."""
    resp1 = client.post("/v1/reviews", headers=AUTH_HEADERS, json=_good_review_request())
    resp2 = client.post("/v1/reviews", headers=AUTH_HEADERS, json=_good_review_request())
    assert resp1.json()["quality_score"] == resp2.json()["quality_score"]


def test_get_review_by_id() -> None:
    """استرجاع مراجعة بالمعرّف."""
    create_resp = client.post("/v1/reviews", headers=AUTH_HEADERS, json=_good_review_request())
    review_id = create_resp.json()["review_id"]
    get_resp = client.get(f"/v1/reviews/{review_id}", headers=AUTH_HEADERS)
    assert get_resp.status_code == 200
    assert get_resp.json()["review_id"] == review_id


def test_list_reviews_with_filter() -> None:
    """فلترة المراجعات بمعرّف المهمة."""
    client.post("/v1/reviews", headers=AUTH_HEADERS, json=_good_review_request())
    resp = client.get("/v1/reviews?task_id=task-critic-001", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    for rev in resp.json():
        assert rev["task_id"] == "task-critic-001"


def test_list_reviews_min_score() -> None:
    """فلترة المراجعات بحد أدنى للدرجة."""
    client.post("/v1/reviews", headers=AUTH_HEADERS, json=_good_review_request())
    client.post("/v1/reviews", headers=AUTH_HEADERS, json=_poor_review_request())
    resp = client.get("/v1/reviews?min_score=0.7", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    for rev in resp.json():
        assert rev["quality_score"] >= 0.7


def test_get_nonexistent_review_404() -> None:
    """مراجعة غير موجودة تعيد 404."""
    resp = client.get("/v1/reviews/nonexistent", headers=AUTH_HEADERS)
    assert resp.status_code == 404


def test_review_stats() -> None:
    """إحصائيات المراجعات تعمل."""
    client.post("/v1/reviews", headers=AUTH_HEADERS, json=_good_review_request())
    resp = client.get("/v1/reviews/stats/summary", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert "total_reviews" in resp.json()
    assert "average_score" in resp.json()


def test_review_rejects_missing_auth() -> None:
    """المراجعة تتطلب مصادقة."""
    resp = client.post("/v1/reviews", json=_good_review_request())
    assert resp.status_code == 401


def test_scoring_criteria_present() -> None:
    """معايير التقييم موجودة في النتيجة."""
    resp = client.post("/v1/reviews", headers=AUTH_HEADERS, json=_good_review_request())
    criteria = resp.json()["criteria"]
    assert "completion_ratio" in criteria
    assert "has_result" in criteria
    assert "result_quality" in criteria
