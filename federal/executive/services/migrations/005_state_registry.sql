-- =============================================================================
-- AMOS-Federation Migration 005 — السجل الفدرالي للمؤسسات (R7-A)
-- الهدف: جداول المؤسسة والإدارة والمسؤول بروابط مرجعية مفروضة.
-- النطاق: federal/executive/services
-- المالك: federal/executive/services
-- تاريخ الإنشاء: 2026-08-17
-- =============================================================================
--
-- قابلة لإعادة التطبيق: كل جملة `IF NOT EXISTS`. لا `DROP` ولا تعديل عمود قائم،
-- فتطبيقها مرتين لا يفقد صفًّا ولا يفشل.
--
-- المستودع لا يستعمل Alembic (لا `alembic.ini` ولا مجلد `versions/`)، فالهجرة
-- هنا صريحة كما في 004. ولا تُضاف هجرة عشوائية: نموذج ORM في
-- `services/state_registry/models.py` هو نفسه هذا المخطَّط، وهذا الملف يخدم
-- النشرات التي تُدار بـ SQL لا بـ`create_all`.
--
-- تنبيه على SQLite: `PRAGMA foreign_keys=ON` لازم لكل اتصال وإلا لم تُفرض
-- المفاتيح. يفرضه `common/database.py::_enforce_sqlite_foreign_keys` على محرك
-- المستودع. PostgreSQL يفرضها دائمًا.
-- =============================================================================

BEGIN;

-- الخطوة 1: المؤسسات. `parent_institution_id` تبعية ذاتية حقيقية.
CREATE TABLE IF NOT EXISTS state_institutions (
    id                     VARCHAR PRIMARY KEY,
    code                   VARCHAR NOT NULL,
    name                   VARCHAR NOT NULL,
    kind                   VARCHAR NOT NULL,
    branch                 VARCHAR NOT NULL,
    status                 VARCHAR NOT NULL DEFAULT 'active',
    mandate                TEXT    DEFAULT '',
    parent_institution_id  VARCHAR REFERENCES state_institutions(id) ON DELETE RESTRICT,
    tenant_id              VARCHAR NOT NULL DEFAULT 'default',
    created_by             VARCHAR NOT NULL,
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_state_institutions_tenant_code UNIQUE (tenant_id, code),
    CONSTRAINT ck_state_institutions_kind CHECK (
        kind IN ('ministry','authority','court','bank','university','school','factory','registry','council')
    ),
    CONSTRAINT ck_state_institutions_branch CHECK (
        branch IN ('executive','legislative','judicial','treasury')
    ),
    CONSTRAINT ck_state_institutions_status CHECK (
        status IN ('active','suspended','dissolved')
    )
);

CREATE INDEX IF NOT EXISTS ix_state_institutions_tenant_status
    ON state_institutions (tenant_id, status);

-- الخطوة 2: الإدارات. لا إدارة بلا مؤسسة — القيد لا التعليق.
CREATE TABLE IF NOT EXISTS state_departments (
    id              VARCHAR PRIMARY KEY,
    institution_id  VARCHAR NOT NULL REFERENCES state_institutions(id) ON DELETE RESTRICT,
    code            VARCHAR NOT NULL,
    name            VARCHAR NOT NULL,
    mandate         TEXT    DEFAULT '',
    status          VARCHAR NOT NULL DEFAULT 'active',
    tenant_id       VARCHAR NOT NULL DEFAULT 'default',
    created_by      VARCHAR NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_state_departments_institution_code UNIQUE (institution_id, code),
    CONSTRAINT ck_state_departments_status CHECK (status IN ('active','suspended','closed'))
);

CREATE INDEX IF NOT EXISTS ix_state_departments_institution
    ON state_departments (institution_id, status);

-- الخطوة 3: المسؤولون. `agent_id` يشير إلى `agents.id` — الهوية واحدة ولا
-- جدول أشخاص موازٍ. ومن لا وجود له في `agents` لا يُقلَّد منصبًا.
CREATE TABLE IF NOT EXISTS state_officials (
    id                 VARCHAR PRIMARY KEY,
    agent_id           VARCHAR NOT NULL REFERENCES agents(id) ON DELETE RESTRICT,
    institution_id     VARCHAR NOT NULL REFERENCES state_institutions(id) ON DELETE RESTRICT,
    department_id      VARCHAR REFERENCES state_departments(id) ON DELETE RESTRICT,
    title              VARCHAR NOT NULL,
    status             VARCHAR NOT NULL DEFAULT 'appointed',
    is_head            BOOLEAN NOT NULL DEFAULT FALSE,
    appointed_by       VARCHAR NOT NULL,
    appointed_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at         TIMESTAMP,
    revocation_reason  TEXT DEFAULT '',
    tenant_id          VARCHAR NOT NULL DEFAULT 'default',
    CONSTRAINT ck_state_officials_status CHECK (status IN ('appointed','suspended','revoked'))
);

CREATE INDEX IF NOT EXISTS ix_state_officials_institution
    ON state_officials (institution_id, status);
CREATE INDEX IF NOT EXISTS ix_state_officials_agent
    ON state_officials (agent_id, status);

-- ملاحظة صادقة: «رئيس واحد لكل إدارة» ليس قيدًا هنا. الشرط يلزمه فهرس جزئي
-- (`WHERE is_head AND status='appointed'`) وصيغته تختلف بين اللهجتين، فهو
-- مفروض في `StateRegistry.appoint_official` ومُختبَر — لا في المخطَّط.

COMMIT;
