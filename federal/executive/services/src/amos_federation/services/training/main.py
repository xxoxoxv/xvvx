"""
AMOS-Federation Training Service
الهدف: خط معالجة البيانات + Model Registry + محاكاة تدريب LoRA
النطاق: خدمة training على المنفذ 8010
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from amos_federation.common.auth import require_auth
from amos_federation.services.training.data_pipeline import InMemoryDataPipeline
from amos_federation.services.training.model_registry import InMemoryModelRegistry

router = APIRouter(prefix="/v1", tags=["training"])


def _make_service(port: int, description: str) -> Any:
    """إنشاء تطبيق خدمة training بدون registry."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="AMOS-Federation Training Service",
        description=description,
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy"}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    return app


# تهيئة المخازن
_pipeline = InMemoryDataPipeline()
_registry = InMemoryModelRegistry()


class CreateDatasetRequest(BaseModel):
    """طلب إنشاء مجموعة بيانات."""

    experiences: list[dict[str, Any]] = Field(default_factory=list)
    target_per_type: int = Field(default=50, ge=1, le=500)


class TrainRequest(BaseModel):
    """طلب تدريب LoRA."""

    dataset_id: str
    base_model: str = "llama-3-8b"
    training_method: str = "LoRA"
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    intended_use: str = ""


class UpdateModelStatusRequest(BaseModel):
    """طلب تحديث حالة نموذج."""

    status: str = Field(pattern="^(registered|training|trained|evaluated|promoted|archived)$")


@router.post("/datasets", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    request: CreateDatasetRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إنشاء مجموعة بيانات من الخبرات: استخراج → تنظيف → موازنة → BOM."""
    dataset = _pipeline.create_dataset(request.experiences, request.target_per_type)
    # إخفاء العينات من الاستجابة
    return {k: v for k, v in dataset.items() if k != "samples"}


@router.get("/datasets", response_model=list[dict])
async def list_datasets(
    _: Annotated[dict[str, object], Depends(require_auth)],
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """عرض مجموعات البيانات."""
    return _pipeline.list_datasets(limit=limit)


@router.get("/datasets/{dataset_id}", response_model=dict)
async def get_dataset(
    dataset_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إرجاع مجموعة بيانات بالمعرّف."""
    ds = _pipeline.get_dataset(dataset_id)
    if ds is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="مجموعة البيانات غير موجودة"
        )
    return ds


@router.post("/models/train", response_model=dict, status_code=status.HTTP_201_CREATED)
async def train_model(
    request: TrainRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تدريب LoRA (محاكاة حتمية) وإنشاء Model Card."""

    # التحقق من وجود البيانات
    dataset = _pipeline.get_dataset(request.dataset_id)
    if dataset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="مجموعة البيانات غير موجودة",
        )

    # محاكاة حتمية للتدريب
    import hashlib

    train_hash = hashlib.sha256(
        f"{request.dataset_id}:{request.base_model}:{request.training_method}".encode()
    ).hexdigest()

    # مقاييس حتمية بناءً على hash
    seed = int(train_hash[:8], 16)
    accuracy = round(0.75 + (seed % 20) / 100, 4)  # 0.75-0.95
    loss = round(0.05 + (seed % 10) / 100, 4)  # 0.05-0.15

    # تسجيل النموذج
    model = _registry.register(
        {
            "name": f"lora-{request.base_model}-{train_hash[:8]}",
            "base_model": request.base_model,
            "training_method": request.training_method,
            "dataset_id": request.dataset_id,
            "hyperparameters": request.hyperparameters,
            "description": request.description,
            "intended_use": request.intended_use,
            "metrics": {
                "accuracy": accuracy,
                "loss": loss,
                "train_hash": train_hash[:16],
            },
            "knowledge_injection": True,  # anti-forgetting enabled
            "status": "trained",
        }
    )

    return model


@router.get("/models", response_model=list[dict])
async def list_models(
    _: Annotated[dict[str, object], Depends(require_auth)],
    model_status: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[dict[str, Any]]:
    """عرض النماذج مع فلترة اختيارية."""
    return _registry.list_all(status=model_status, limit=limit)


@router.get("/models/{model_id}", response_model=dict)
async def get_model(
    model_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إرجاع نموذج بالمعرّف."""
    model = _registry.get(model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="النموذج غير موجود")
    return model


@router.patch("/models/{model_id}/status", response_model=dict)
async def update_model_status(
    model_id: str,
    request: UpdateModelStatusRequest,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """تحديث حالة نموذج."""
    updated = _registry.update_status(model_id, request.status)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="النموذج غير موجود")
    return updated


@router.get("/models/{model_id}/card", response_model=dict)
async def get_model_card(
    model_id: str,
    _: Annotated[dict[str, object], Depends(require_auth)],
) -> dict[str, Any]:
    """إرجاع Model Card لنموذج."""
    model = _registry.get(model_id)
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="النموذج غير موجود")
    return model["model_card"]


app = _make_service(8010, "تدريب LoRA + Model Registry + Data Pipeline")
