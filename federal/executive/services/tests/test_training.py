"""
اختبارات Training Service: Data Pipeline + Model Registry
الهدف: التحقق من خط معالجة البيانات وتسجيل النماذج
النطاق: services/training
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from fastapi.testclient import TestClient

from amos_federation.common.auth import create_access_token
from amos_federation.services.training.data_pipeline import InMemoryDataPipeline
from amos_federation.services.training.main import app

client = TestClient(app)
AUTH_HEADERS = {
    "Authorization": "Bearer " + create_access_token("tester", ["training:read", "training:write"])
}


def _sample_experiences() -> list[dict]:
    """خبرات تجريبية متنوعة."""
    return [
        {
            "experience_id": "exp-1",
            "type": "success",
            "agent_id": "worker-1",
            "model_used": "alpha",
            "quality_score": 0.9,
            "created_at": "2026-08-15T10:00:00Z",
            "outcome": {"input": "حلل البيانات", "output": "تم التحليل", "domain": "finance"},
        },
        {
            "experience_id": "exp-2",
            "type": "failure",
            "agent_id": "worker-2",
            "model_used": "alpha",
            "quality_score": 0.3,
            "created_at": "2026-08-15T11:00:00Z",
            "outcome": {"input": "تقرير قانوني", "output": "", "domain": "law"},
        },
        {
            "experience_id": "exp-3",
            "type": "gap",
            "agent_id": "worker-1",
            "model_used": "alpha",
            "quality_score": 0.5,
            "created_at": "2026-08-15T12:00:00Z",
            "outcome": {"input": "تحليل طبي", "output": "ناقص", "domain": "health"},
        },
        {
            "experience_id": "exp-4",
            "type": "success",
            "agent_id": "worker-3",
            "model_used": "beta",
            "quality_score": 0.85,
            "created_at": "2026-08-15T13:00:00Z",
            "outcome": {"input": "حلل البيانات", "output": "تم التحليل", "domain": "finance"},
        },
    ]


# === Data Pipeline Tests ===


def test_collect_extracts_samples() -> None:
    """استخراج عينات من الخبرات."""
    pipeline = InMemoryDataPipeline()
    samples = pipeline.collect(_sample_experiences())
    assert len(samples) == 4
    assert all("sample_id" in s for s in samples)
    assert all("input" in s and "output" in s for s in samples)


def test_deduplicate_removes_duplicates() -> None:
    """إزالة العينات المكررة."""
    pipeline = InMemoryDataPipeline()
    samples = pipeline.collect(_sample_experiences())
    deduped = pipeline.deduplicate(samples)
    # exp-1 و exp-4 لهما نفس input/output
    assert len(deduped) == 3


def test_balance_limits_per_type() -> None:
    """موازنة العينات حسب النوع."""
    pipeline = InMemoryDataPipeline()
    samples = pipeline.collect(_sample_experiences())
    balanced = pipeline.balance(samples, target_per_type=1)
    # 3 أنواع: success, failure, gap
    by_type = {}
    for s in balanced:
        by_type[s["type"]] = by_type.get(s["type"], 0) + 1
    assert all(v <= 1 for v in by_type.values())


def test_create_bom() -> None:
    """إنشاء Data BOM."""
    pipeline = InMemoryDataPipeline()
    samples = pipeline.collect(_sample_experiences())
    bom = pipeline.create_bom(samples)
    assert "bom_id" in bom
    assert bom["total_samples"] == 4
    assert "by_type" in bom
    assert "by_domain" in bom
    assert "hash" in bom


def test_create_dataset_full_pipeline() -> None:
    """خط كامل: استخراج → تنظيف → موازنة → BOM."""
    pipeline = InMemoryDataPipeline()
    dataset = pipeline.create_dataset(_sample_experiences(), target_per_type=50)
    assert "dataset_id" in dataset
    assert "bom" in dataset
    assert dataset["status"] == "ready"
    assert "samples" in dataset


# === API Tests ===


def test_api_create_dataset() -> None:
    """واجهة إنشاء مجموعة بيانات."""
    resp = client.post(
        "/v1/datasets",
        headers=AUTH_HEADERS,
        json={"experiences": _sample_experiences(), "target_per_type": 10},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "dataset_id" in data
    assert "bom" in data
    assert "sample_count" in data


def test_api_list_datasets() -> None:
    """واجهة عرض البيانات."""
    client.post("/v1/datasets", headers=AUTH_HEADERS, json={"experiences": _sample_experiences()})
    resp = client.get("/v1/datasets", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_api_get_dataset() -> None:
    """واجهة استرجاع مجموعة بيانات."""
    create = client.post(
        "/v1/datasets", headers=AUTH_HEADERS, json={"experiences": _sample_experiences()}
    )
    dataset_id = create.json()["dataset_id"]
    resp = client.get(f"/v1/datasets/{dataset_id}", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["dataset_id"] == dataset_id


def test_api_train_model() -> None:
    """واجهة تدريب LoRA."""
    create_ds = client.post(
        "/v1/datasets", headers=AUTH_HEADERS, json={"experiences": _sample_experiences()}
    )
    dataset_id = create_ds.json()["dataset_id"]
    resp = client.post(
        "/v1/models/train",
        headers=AUTH_HEADERS,
        json={"dataset_id": dataset_id, "base_model": "llama-3-8b", "training_method": "LoRA"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "model_id" in data
    assert "model_card" in data
    assert data["status"] == "trained"
    assert "accuracy" in data["model_card"]["metrics"]


def test_api_train_nonexistent_dataset() -> None:
    """تدريب بمجموعة بيانات غير موجودة يعيد 404."""
    resp = client.post("/v1/models/train", headers=AUTH_HEADERS, json={"dataset_id": "nonexistent"})
    assert resp.status_code == 404


def test_api_list_models() -> None:
    """واجهة عرض النماذج."""
    create_ds = client.post(
        "/v1/datasets", headers=AUTH_HEADERS, json={"experiences": _sample_experiences()}
    )
    client.post(
        "/v1/models/train",
        headers=AUTH_HEADERS,
        json={"dataset_id": create_ds.json()["dataset_id"]},
    )
    resp = client.get("/v1/models", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_api_get_model() -> None:
    """واجهة استرجاع نموذج."""
    create_ds = client.post(
        "/v1/datasets", headers=AUTH_HEADERS, json={"experiences": _sample_experiences()}
    )
    train = client.post(
        "/v1/models/train",
        headers=AUTH_HEADERS,
        json={"dataset_id": create_ds.json()["dataset_id"]},
    )
    model_id = train.json()["model_id"]
    resp = client.get(f"/v1/models/{model_id}", headers=AUTH_HEADERS)
    assert resp.status_code == 200


def test_api_update_model_status() -> None:
    """تحديث حالة نموذج."""
    create_ds = client.post(
        "/v1/datasets", headers=AUTH_HEADERS, json={"experiences": _sample_experiences()}
    )
    train = client.post(
        "/v1/models/train",
        headers=AUTH_HEADERS,
        json={"dataset_id": create_ds.json()["dataset_id"]},
    )
    model_id = train.json()["model_id"]
    resp = client.patch(
        f"/v1/models/{model_id}/status", headers=AUTH_HEADERS, json={"status": "evaluated"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "evaluated"


def test_api_get_model_card() -> None:
    """استرجاع Model Card."""
    create_ds = client.post(
        "/v1/datasets", headers=AUTH_HEADERS, json={"experiences": _sample_experiences()}
    )
    train = client.post(
        "/v1/models/train",
        headers=AUTH_HEADERS,
        json={"dataset_id": create_ds.json()["dataset_id"]},
    )
    model_id = train.json()["model_id"]
    resp = client.get(f"/v1/models/{model_id}/card", headers=AUTH_HEADERS)
    assert resp.status_code == 200
    card = resp.json()
    assert "model_id" in card
    assert "base_model" in card
    assert "metrics" in card
    assert card["knowledge_injection"] is True


def test_api_train_rejects_missing_auth() -> None:
    """التدريب يتطلب مصادقة."""
    resp = client.post("/v1/models/train", json={"dataset_id": "x"})
    assert resp.status_code == 401
