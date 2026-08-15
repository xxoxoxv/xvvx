"""
AMOS-Federation Benchmark Suite + Gap Analyzer
الهدف: مجموعة مهام قياسية + اكتشاف فجوات معرفية
النطاق: evaluation
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Any

# مجموعة 20 مهمة قياسية موزعة على الأنواع والمجالات
BENCHMARK_TASKS: list[dict[str, Any]] = [
    {
        "id": "bench-001",
        "type": "analysis",
        "description": "حلل بيانات المبيعات الشهرية",
        "domain": "finance",
        "expected_tools": ["sql_query", "data_analysis", "chart_generate"],
    },
    {
        "id": "bench-002",
        "type": "analysis",
        "description": "حلل اتجاهات السوق العقاري",
        "domain": "finance",
        "expected_tools": ["research_apis", "data_analysis"],
    },
    {
        "id": "bench-003",
        "type": "analysis",
        "description": "حلل أداء المحفظة الاستثمارية",
        "domain": "finance",
        "expected_tools": ["sql_query", "data_analysis"],
    },
    {
        "id": "bench-004",
        "type": "analysis",
        "description": "حلل بيانات المرضى السريرية",
        "domain": "health",
        "expected_tools": ["medical_dbs", "data_analysis"],
    },
    {
        "id": "bench-005",
        "type": "analysis",
        "description": "حلل نتائج التجارب العلمية",
        "domain": "science",
        "expected_tools": ["data_analysis", "python_execute"],
    },
    {
        "id": "bench-006",
        "type": "report",
        "description": "تقرير سنوي عن الأداء المالي",
        "domain": "finance",
        "expected_tools": ["research_apis", "generation", "chart_generate"],
    },
    {
        "id": "bench-007",
        "type": "report",
        "description": "تقرير حالة بيئية",
        "domain": "science",
        "expected_tools": ["research_apis", "generation"],
    },
    {
        "id": "bench-008",
        "type": "report",
        "description": "تقرير قانوني للقضية",
        "domain": "law",
        "expected_tools": ["legal_search", "document_analysis", "generation"],
    },
    {
        "id": "bench-009",
        "type": "report",
        "description": "تقرير صحة عامة",
        "domain": "health",
        "expected_tools": ["medical_dbs", "generation"],
    },
    {
        "id": "bench-010",
        "type": "report",
        "description": "تقرير ثقافي فني",
        "domain": "culture",
        "expected_tools": ["research_apis", "generation"],
    },
    {
        "id": "bench-011",
        "type": "data",
        "description": "تحويل وتنظيف بيانات المبيعات",
        "domain": "finance",
        "expected_tools": ["sql_query", "python_execute"],
    },
    {
        "id": "bench-012",
        "type": "data",
        "description": "توليد رسوم بيانية للأرباح",
        "domain": "finance",
        "expected_tools": ["data_analysis", "chart_generate"],
    },
    {
        "id": "bench-013",
        "type": "data",
        "description": "تحليل إحصائي للتجربة",
        "domain": "science",
        "expected_tools": ["data_analysis", "python_execute"],
    },
    {
        "id": "bench-014",
        "type": "data",
        "description": "استخراج بيانات قانونية",
        "domain": "law",
        "expected_tools": ["legal_search", "document_analysis"],
    },
    {
        "id": "bench-015",
        "type": "data",
        "description": "تصميم مخططات بصرية",
        "domain": "culture",
        "expected_tools": ["design", "chart_generate"],
    },
    {
        "id": "bench-016",
        "type": "generic",
        "description": "تصنيف تذكرة دعم",
        "domain": "federal",
        "expected_tools": ["task_classifier"],
    },
    {
        "id": "bench-017",
        "type": "generic",
        "description": "ترجمة وثيقة",
        "domain": "law",
        "expected_tools": ["document_analysis", "generation"],
    },
    {
        "id": "bench-018",
        "type": "generic",
        "description": "توليد محتوى تسويقي",
        "domain": "culture",
        "expected_tools": ["generation", "design"],
    },
    {
        "id": "bench-019",
        "type": "generic",
        "description": "بحث طبي عام",
        "domain": "health",
        "expected_tools": ["medical_dbs", "research_apis"],
    },
    {
        "id": "bench-020",
        "type": "generic",
        "description": "مراجعة عقد",
        "domain": "law",
        "expected_tools": ["legal_search", "document_analysis"],
    },
]


def run_benchmark(
    execute_fn: Any | None = None,
) -> dict[str, Any]:
    """تشغيل مجموعة المهام القياسية وإرجاع تقرير."""
    results: list[dict[str, Any]] = []
    passed = 0
    failed = 0

    for task in BENCHMARK_TASKS:
        # إذا وُفرت دالة تنفيذ، استخدمها؛ خلافًا لذلك، تحقق هيكلي
        if execute_fn:
            try:
                result = execute_fn(task)
                success = result.get("status") == "completed"
            except Exception:
                success = False
                result = {"error": "execution_failed"}
        else:
            # تحقق هيكلي: هل الخطوات المتوقعة لها أدوات؟
            success = len(task["expected_tools"]) > 0
            result = {"structural_check": success, "expected_tools": task["expected_tools"]}

        if success:
            passed += 1
        else:
            failed += 1
        results.append(
            {
                "task_id": task["id"],
                "type": task["type"],
                "domain": task["domain"],
                "passed": success,
                "result": result,
            }
        )

    return {
        "total": len(BENCHMARK_TASKS),
        "passed": passed,
        "failed": failed,
        "pass_rate": round(passed / len(BENCHMARK_TASKS), 4),
        "results": results,
    }


def analyze_gaps(
    experiences: list[dict[str, Any]],
    benchmark_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """اكتشاف الفجوات المعرفية بمقارنة الخبرات مع المهام القياسية."""
    # تجميع الخبرات حسب المجال
    domain_stats: dict[str, dict[str, int]] = {}
    for exp in experiences:
        domain = "unknown"
        if exp.get("outcome") and isinstance(exp["outcome"], dict):
            domain = exp["outcome"].get("domain", "unknown")
        if domain not in domain_stats:
            domain_stats[domain] = {"success": 0, "failure": 0, "gap": 0}
        exp_type = exp.get("type", "success")
        if exp_type in domain_stats[domain]:
            domain_stats[domain][exp_type] += 1

    # اكتشاف المجالات ذات معدل الفشل العالي
    gaps: list[dict[str, Any]] = []
    for domain, stats in domain_stats.items():
        total = sum(stats.values())
        if total == 0:
            continue
        failure_rate = (stats["failure"] + stats["gap"]) / total
        if failure_rate > 0.3:
            gaps.append(
                {
                    "domain": domain,
                    "failure_rate": round(failure_rate, 4),
                    "total_experiences": total,
                    "recommendation": f"المجال '{domain}' يحتاج تحسين: معدل فشل {failure_rate:.0%}",
                }
            )

    # مقارنة مع نتائج المعيار
    uncovered_domains: list[str] = []
    if benchmark_results:
        covered_domains = {r["domain"] for r in benchmark_results if r.get("passed")}
        all_domains = {t["domain"] for t in BENCHMARK_TASKS}
        uncovered_domains = list(all_domains - covered_domains)

    return {
        "total_gaps": len(gaps),
        "gaps": gaps,
        "domain_coverage": domain_stats,
        "uncovered_domains": uncovered_domains,
    }
