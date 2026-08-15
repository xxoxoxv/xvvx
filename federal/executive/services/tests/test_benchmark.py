"""
اختبارات المعيار القياسي ومحلل الفجوات
الهدف: التحقق من تشغيل المعيار واكتشاف الفجوات
النطاق: services/evaluation (benchmark + gap analyzer)
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.evaluation.benchmark import (
    BENCHMARK_TASKS,
    analyze_gaps,
    run_benchmark,
)

client = TestClient(__import__("amos_federation.services.evaluation.main", fromlist=["app"]).app)
AUTH_HEADERS = {
    "Authorization": "Bearer " + create_access_token("tester", ["eval:read", "eval:write"])
}


def test_benchmark_suite_has_20_tasks() -> None:
    """مجموعة المعيار تحتوي على 20 مهمة قياسية."""
    assert len(BENCHMARK_TASKS) == 20


def test_benchmark_covers_all_types() -> None:
    """المعيار يغطي كل أنواع المهام."""
    types = {t["type"] for t in BENCHMARK_TASKS}
    assert types == {"analysis", "report", "data", "generic"}


def test_benchmark_covers_multiple_domains() -> None:
    """المعيار يغطي مجالات متعددة."""
    domains = {t["domain"] for t in BENCHMARK_TASKS}
    assert len(domains) >= 4
    assert "finance" in domains
    assert "health" in domains


def test_run_benchmark_returns_report() -> None:
    """تشغيل المعيار يعيد تقريرًا بالإحصائيات."""
    result = run_benchmark()
    assert result["total"] == 20
    assert result["passed"] + result["failed"] == 20
    assert 0.0 <= result["pass_rate"] <= 1.0
    assert len(result["results"]) == 20


def test_benchmark_is_deterministic() -> None:
    """تشغيل المعيار مرتين ينتج نفس النتائج."""
    r1 = run_benchmark()
    r2 = run_benchmark()
    assert r1["pass_rate"] == r2["pass_rate"]


def test_benchmark_endpoint() -> None:
    """واجهة تشغيل المعيار تعمل."""
    resp = client.post("/v1/evaluations/benchmark", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 20
    assert "pass_rate" in data


def test_gap_analyzer_with_no_experiences() -> None:
    """محلل الفجوات بدون خبرات يعيد نتائج فارغة."""
    result = analyze_gaps([])
    assert result["total_gaps"] == 0
    assert result["gaps"] == []


def test_gap_analyzer_detects_weak_domain() -> None:
    """محلل الفجوات يكتشف المجالات الضعيفة."""
    experiences = [
        {"type": "failure", "outcome": {"domain": "health"}},
        {"type": "failure", "outcome": {"domain": "health"}},
        {"type": "success", "outcome": {"domain": "health"}},
        {"type": "success", "outcome": {"domain": "finance"}},
    ]
    result = analyze_gaps(experiences)
    assert result["total_gaps"] >= 1
    health_gap = [g for g in result["gaps"] if g["domain"] == "health"]
    assert len(health_gap) == 1
    assert health_gap[0]["failure_rate"] > 0.3


def test_gap_endpoint() -> None:
    """واجهة اكتشاف الفجوات تعمل."""
    resp = client.get("/v1/evaluations/gaps", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert "total_gaps" in resp.json()
    assert "gaps" in resp.json()


def test_evaluation_run_includes_benchmark() -> None:
    """واجهة التقييم تشمل نتائج المعيار."""
    resp = client.post("/v1/evaluations/run", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "benchmark" in data
    assert data["benchmark"]["total"] == 20
    assert "pass_rate" in data["benchmark"]
