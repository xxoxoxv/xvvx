"""
AMOS-Federation State Registry — Domain Model
الهدف: تمثيل المؤسسة والإدارة والمسؤول كصفوف مترابطة بمفاتيح أجنبية مفروضة
النطاق: services/state_registry
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-17 (R7-A)

## لماذا `Base` المشترك ولا قاعدة تعريف ثانية

`governance/treasury.py` أنشأ `_TreasuryBase` خاصًّا به، فصارت جداول الخزانة في
خريطة تعريف منفصلة لا يراها `init_db()`. ولا نكرّر ذلك هنا: هذه النماذج على
`Base` نفسه في `common/database.py`، فالمؤسسة تستطيع أن تشير بمفتاح أجنبي حقيقي
إلى `agents.id` — وهو ما يستحيل عبر خريطتَي تعريف منفصلتين.

## المسؤول ليس هوية موازية

`state_officials.agent_id` مفتاح أجنبي إلى `agents.id`. لم يُنشأ جدول «أشخاص»
جديد: المسؤول **وكيلٌ مُقلَّد منصبًا**، فالهوية تبقى واحدة في `agents` وسجلّ
التقليد يضيف المنصب فوقها. ومن لا وجود له في `agents` لا يُقلَّد منصبًا — تمنعه
قاعدة البيانات لا التعليق.

## حدٌّ يُقال: رئاسة الإدارة مفروضة في طبقة الخدمة لا في القاعدة

«رئيس واحد لكل إدارة» شرطٌ على الصفوف النشطة فقط
(`UNIQUE (department_id) WHERE is_head AND status='appointed'`)، والفهرس الجزئي
غير محمول بين SQLite و PostgreSQL بصيغة واحدة في هذه الطبقة. فُرِض في
`StateRegistry.appoint_official`، ويُقال هنا صراحةً أنه ليس قيدًا في المخطَّط.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)

from amos_federation.common.database import Base

# === مفردات الحالات والأنواع — مصدر واحد للقيد وللتحقق ===

INSTITUTION_KINDS: tuple[str, ...] = (
    "ministry",
    "authority",
    "court",
    "bank",
    "university",
    "school",
    "factory",
    "registry",
    "council",
)

#: الفروع كما هي في شجرة المستودع فعلًا (`federal/`) — لا فرعًا مُختَرعًا.
INSTITUTION_BRANCHES: tuple[str, ...] = (
    "executive",
    "legislative",
    "judicial",
    "treasury",
)

INSTITUTION_STATUSES: tuple[str, ...] = ("active", "suspended", "dissolved")
DEPARTMENT_STATUSES: tuple[str, ...] = ("active", "suspended", "closed")
OFFICIAL_STATUSES: tuple[str, ...] = ("appointed", "suspended", "revoked")


def _now() -> datetime:
    return datetime.now(UTC)


class InstitutionModel(Base):
    """مؤسسة فدرالية — الوحدة الحاملة للاختصاص والميزانية والمسؤولين."""

    __tablename__ = "state_institutions"

    id = Column(String, primary_key=True)
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    mandate = Column(Text, default="")
    #: تبعية مؤسسية حقيقية — وزارة تحت مجلس، هيئة تحت وزارة.
    parent_institution_id = Column(
        String, ForeignKey("state_institutions.id", ondelete="RESTRICT"), nullable=True
    )
    tenant_id = Column(String, nullable=False, default="default")
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_state_institutions_tenant_code"),
        CheckConstraint(
            "kind IN ('" + "','".join(INSTITUTION_KINDS) + "')",
            name="ck_state_institutions_kind",
        ),
        CheckConstraint(
            "branch IN ('" + "','".join(INSTITUTION_BRANCHES) + "')",
            name="ck_state_institutions_branch",
        ),
        CheckConstraint(
            "status IN ('" + "','".join(INSTITUTION_STATUSES) + "')",
            name="ck_state_institutions_status",
        ),
        Index("ix_state_institutions_tenant_status", "tenant_id", "status"),
    )


class DepartmentModel(Base):
    """إدارة داخل مؤسسة — لا وجود لإدارة بلا مؤسسة، تمنعه القاعدة."""

    __tablename__ = "state_departments"

    id = Column(String, primary_key=True)
    institution_id = Column(
        String, ForeignKey("state_institutions.id", ondelete="RESTRICT"), nullable=False
    )
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    mandate = Column(Text, default="")
    status = Column(String, nullable=False, default="active")
    tenant_id = Column(String, nullable=False, default="default")
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_state_departments_institution_code"),
        CheckConstraint(
            "status IN ('" + "','".join(DEPARTMENT_STATUSES) + "')",
            name="ck_state_departments_status",
        ),
        Index("ix_state_departments_institution", "institution_id", "status"),
    )


class OfficialModel(Base):
    """تقليد وكيل منصبًا رسميًّا — الهوية في `agents`، والمنصب هنا."""

    __tablename__ = "state_officials"

    id = Column(String, primary_key=True)
    #: الهوية الواحدة. لا جدول أشخاص موازٍ.
    agent_id = Column(String, ForeignKey("agents.id", ondelete="RESTRICT"), nullable=False)
    institution_id = Column(
        String, ForeignKey("state_institutions.id", ondelete="RESTRICT"), nullable=False
    )
    department_id = Column(
        String, ForeignKey("state_departments.id", ondelete="RESTRICT"), nullable=True
    )
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default="appointed")
    is_head = Column(Boolean, nullable=False, default=False)
    appointed_by = Column(String, nullable=False)
    appointed_at = Column(DateTime, default=_now)
    revoked_at = Column(DateTime, nullable=True)
    revocation_reason = Column(Text, default="")
    tenant_id = Column(String, nullable=False, default="default")

    __table_args__ = (
        CheckConstraint(
            "status IN ('" + "','".join(OFFICIAL_STATUSES) + "')",
            name="ck_state_officials_status",
        ),
        Index("ix_state_officials_institution", "institution_id", "status"),
        Index("ix_state_officials_agent", "agent_id", "status"),
    )


#: الجداول التي تملكها هذه الوحدة — تُستعمل في الهجرة وفي فحوص المخطَّط.
REGISTRY_TABLES: tuple[str, ...] = (
    "state_institutions",
    "state_departments",
    "state_officials",
)

__all__ = [
    "DEPARTMENT_STATUSES",
    "INSTITUTION_BRANCHES",
    "INSTITUTION_KINDS",
    "INSTITUTION_STATUSES",
    "OFFICIAL_STATUSES",
    "REGISTRY_TABLES",
    "DepartmentModel",
    "InstitutionModel",
    "OfficialModel",
]
