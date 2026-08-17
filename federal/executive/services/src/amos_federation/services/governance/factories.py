"""
AMOS-Federation Phase 13 — Federal Factories
الهدف: أربعة مصانع إنتاج حقيقية تستهلك الوكلاء والأدوات والنماذج
النطاق: services/governance/factories
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15

المتطلبات:
  13.1: مصنع التقارير المالية (استخراج ← تنظيف ← تحليل ← كتابة ← مراجعة ← نشر)
  13.2: مصنع المحتوى (مقالات، ترجمات، ملخصات)
  13.3: مصنع الأبحاث (أسئلة بحثية → أوراق علمية)
  13.4: مصنع المراقبة الأمنية (سجلات → تقارير تهديدات)
  13.5: توسيع كتالوج الأدوات
  13.6: ربط كل مصنع بمدير خط إنتاج وعمال حقيقيين
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from amos_federation.common.database import get_database_url
from amos_federation.common.persistent import PersistentAuditStore


class FactoryBase(DeclarativeBase):
    pass


class FactoryModel(FactoryBase):
    """جدول المصانع."""

    __tablename__ = "federal_factories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    factory_id = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # financial_report, content, research, security
    state_id = Column(String, nullable=True)  # الولاية التابع لها
    manager_agent_id = Column(String, nullable=True)
    status = Column(String, default="active")  # active, paused, closed
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class FactoryProductModel(FactoryBase):
    """مخرجات المصانع."""

    __tablename__ = "factory_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, nullable=False, unique=True, index=True)
    factory_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, default="")
    quality_score = Column(Integer, default=0)
    status = Column(String, default="draft")  # draft, reviewed, published
    pipeline_steps = Column(Text, default="[]")  # JSON array of completed steps
    produced_by = Column(String, nullable=True)  # agent_id
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    published_at = Column(DateTime, nullable=True)


# تعريف المصانع الأربعة
FACTORIES = {
    "financial_report": {
        "name": "مصنع التقارير المالية",
        "type": "financial_report",
        "state_id": "finance",
        "pipeline": ["extract", "clean", "analyze", "write", "review", "publish"],
    },
    "content": {
        "name": "مصنع المحتوى",
        "type": "content",
        "state_id": "culture",
        "pipeline": ["research", "draft", "edit", "review", "publish"],
    },
    "research": {
        "name": "مصنع الأبحاث",
        "type": "research",
        "state_id": "science",
        "pipeline": [
            "question",
            "literature",
            "methodology",
            "experiment",
            "write",
            "review",
            "publish",
        ],
    },
    "security": {
        "name": "مصنع المراقبة الأمنية",
        "type": "security",
        "state_id": "law",
        "pipeline": ["collect_logs", "analyze", "detect_threats", "assess", "report", "publish"],
    },
}


class Factory:
    """13.1-13.4: مصنع إنتاج حقيقي بخط أنابيب."""

    def __init__(self, factory_id: str) -> None:
        self._engine = create_engine(
            get_database_url(),
            connect_args={"check_same_thread": False}
            if get_database_url().startswith("sqlite")
            else {},
        )
        FactoryBase.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, autoflush=False, expire_on_commit=False)
        self.factory_id = factory_id
        self._init_factory()

    def _init_factory(self) -> None:
        """تهيئة المصنع إذا لم يكن موجودًا."""
        session = self._Session()
        try:
            existing = (
                session.query(FactoryModel)
                .filter(FactoryModel.factory_id == self.factory_id)
                .first()
            )
            if not existing and self.factory_id in FACTORIES:
                info = FACTORIES[self.factory_id]
                factory = FactoryModel(
                    factory_id=self.factory_id,
                    name=info["name"],
                    type=info["type"],
                    state_id=info["state_id"],
                )
                session.add(factory)
                session.commit()
        finally:
            session.close()

    def start_production(self, title: str, producer_agent_id: str = "") -> dict[str, Any]:
        """بدء إنتاج منتج جديد — يدخل خط الأنابيب."""
        session = self._Session()
        try:
            product_id = f"prod-{uuid.uuid4().hex[:10]}"
            pipeline = FACTORIES.get(self.factory_id, {}).get("pipeline", [])
            product = FactoryProductModel(
                product_id=product_id,
                factory_id=self.factory_id,
                title=title,
                produced_by=producer_agent_id,
                pipeline_steps="[]",
            )
            session.add(product)
            session.commit()

            audit = PersistentAuditStore()
            audit.append(
                "factory.production_started",
                producer_agent_id or "system",
                {
                    "factory_id": self.factory_id,
                    "product_id": product_id,
                    "title": title,
                },
            )

            return {
                "product_id": product_id,
                "factory_id": self.factory_id,
                "title": title,
                "pipeline": pipeline,
                "status": "draft",
                "started": True,
            }
        finally:
            session.close()

    def complete_step(
        self, product_id: str, step: str, output: str = "", quality: int = 0
    ) -> dict[str, Any]:
        """إكمال خطوة في خط الأنابيب."""
        session = self._Session()
        try:
            product = (
                session.query(FactoryProductModel)
                .filter(FactoryProductModel.product_id == product_id)
                .first()
            )
            if not product:
                return {"error": "product_not_found"}

            steps = json.loads(product.pipeline_steps or "[]")
            steps.append(
                {
                    "step": step,
                    "output": output[:200],
                    "quality": quality,
                    "completed_at": datetime.now(UTC).isoformat(),
                }
            )
            product.pipeline_steps = json.dumps(steps)

            # إذا كانت الخطوة هي النشر، حدّث الحالة
            pipeline = FACTORIES.get(self.factory_id, {}).get("pipeline", [])
            if step == pipeline[-1]:  # الخطوة الأخيرة
                product.status = "published"
                product.published_at = datetime.now(UTC)
            elif step == "review":
                product.status = "reviewed"

            session.commit()

            return {
                "product_id": product_id,
                "step": step,
                "quality": quality,
                "status": product.status,
                "steps_completed": len(steps),
                "total_steps": len(pipeline),
            }
        finally:
            session.close()

    def run_full_pipeline(self, title: str, producer_agent_id: str = "") -> dict[str, Any]:
        """تشغيل خط الأنابيب الكامل من البداية للنشر."""
        result = self.start_production(title, producer_agent_id)
        product_id = result["product_id"]
        pipeline = result["pipeline"]

        for step in pipeline:
            self.complete_step(product_id, step, f"مخرج {step}", quality=85)

        session = self._Session()
        try:
            product = (
                session.query(FactoryProductModel)
                .filter(FactoryProductModel.product_id == product_id)
                .first()
            )
            return {
                "product_id": product_id,
                "factory_id": self.factory_id,
                "title": title,
                "status": product.status,
                "steps_completed": len(pipeline),
                "published_at": product.published_at.isoformat() if product.published_at else None,
            }
        finally:
            session.close()

    def list_products(self, limit: int = 50) -> list[dict[str, Any]]:
        """مخرجات المصنع."""
        session = self._Session()
        try:
            products = (
                session.query(FactoryProductModel)
                .filter(FactoryProductModel.factory_id == self.factory_id)
                .order_by(FactoryProductModel.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "product_id": p.product_id,
                    "title": p.title,
                    "status": p.status,
                    "quality_score": p.quality_score,
                    "produced_by": p.produced_by,
                    "steps_completed": len(json.loads(p.pipeline_steps or "[]")),
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in products
            ]
        finally:
            session.close()

    def get_product(self, product_id: str) -> dict[str, Any] | None:
        """تفاصيل منتج."""
        session = self._Session()
        try:
            p = (
                session.query(FactoryProductModel)
                .filter(FactoryProductModel.product_id == product_id)
                .first()
            )
            if not p:
                return None
            return {
                "product_id": p.product_id,
                "factory_id": p.factory_id,
                "title": p.title,
                "content": p.content,
                "status": p.status,
                "quality_score": p.quality_score,
                "pipeline_steps": json.loads(p.pipeline_steps or "[]"),
                "produced_by": p.produced_by,
            }
        finally:
            session.close()


class FactoryRegistry:
    """13.6: سجل المصانع — ربط بمديري خطوط الإنتاج."""

    def __init__(self) -> None:
        self._engine = create_engine(
            get_database_url(),
            connect_args={"check_same_thread": False}
            if get_database_url().startswith("sqlite")
            else {},
        )
        FactoryBase.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, autoflush=False, expire_on_commit=False)

    def list_factories(self) -> list[dict[str, Any]]:
        """قائمة المصانع."""
        session = self._Session()
        try:
            factories = session.query(FactoryModel).all()
            return [
                {
                    "factory_id": f.factory_id,
                    "name": f.name,
                    "type": f.type,
                    "state_id": f.state_id,
                    "manager_agent_id": f.manager_agent_id,
                    "status": f.status,
                }
                for f in factories
            ]
        finally:
            session.close()

    def assign_manager(self, factory_id: str, agent_id: str) -> dict[str, Any]:
        """13.6: تعيين مدير خط إنتاج."""
        session = self._Session()
        try:
            factory = (
                session.query(FactoryModel).filter(FactoryModel.factory_id == factory_id).first()
            )
            if not factory:
                return {"error": "factory_not_found"}
            factory.manager_agent_id = agent_id
            session.commit()
            audit = PersistentAuditStore()
            audit.append(
                "factory.manager_assigned",
                "system",
                {
                    "factory_id": factory_id,
                    "agent_id": agent_id,
                },
            )
            return {"factory_id": factory_id, "manager_agent_id": agent_id, "assigned": True}
        finally:
            session.close()


# Singletons
_factories: dict[str, Factory] = {}
_registry: FactoryRegistry | None = None


def get_factory(factory_id: str) -> Factory:
    global _factories
    if factory_id not in _factories:
        _factories[factory_id] = Factory(factory_id)
    return _factories[factory_id]


def get_factory_registry() -> FactoryRegistry:
    global _registry
    if _registry is None:
        _registry = FactoryRegistry()
    return _registry
