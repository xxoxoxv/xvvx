-- AMOS-Federation Database Schema v1.0
-- الهدف: إنشاء كل جداول النظام الأساسية
-- النطاق: قاعدة بيانات amos_federation
-- المالك: federal/executive/services
-- تاريخ الإنشاء: 2026-08-15

-- Extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. agents — السكان (المواطنون الرقميون)
-- ============================================================
CREATE TABLE IF NOT EXISTS agents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        VARCHAR(255) UNIQUE NOT NULL,
    agent_type      VARCHAR(50) NOT NULL,
    domain          VARCHAR(100),
    version         VARCHAR(20) DEFAULT '1.0.0',
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'paused', 'retired', 'deceased')),
    manifest        JSONB NOT NULL DEFAULT '{}',
    permissions     JSONB DEFAULT '[]',
    budget          JSONB DEFAULT '{}',
    tenant_id       VARCHAR(100),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

CREATE INDEX idx_agents_agent_id ON agents (agent_id);
CREATE INDEX idx_agents_domain   ON agents (domain);
CREATE INDEX idx_agents_status   ON agents (status);

-- ============================================================
-- 2. tools — الموارد (الأدوات)
-- ============================================================
CREATE TABLE IF NOT EXISTS tools (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id         VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(255) NOT NULL,
    version         VARCHAR(20) NOT NULL,
    status          VARCHAR(20) DEFAULT 'active'
                    CHECK (status IN ('active', 'deprecated', 'disabled')),
    input_schema    JSONB NOT NULL DEFAULT '{}',
    output_schema   JSONB NOT NULL DEFAULT '{}',
    risk_level      VARCHAR(20) DEFAULT 'low'
                    CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    sandbox_required BOOLEAN DEFAULT TRUE,
    tool_bom        JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tools_tool_id   ON tools (tool_id);
CREATE INDEX idx_tools_risk_level ON tools (risk_level);

-- ============================================================
-- 3. tasks — المهام
-- ============================================================
-- ملاحظة مرجعية (E2.2-G · 2026-08-16): هذا التعريف **مُتجاوَز**.
-- المرجع الوحيد لجدول tasks هو نموذج ORM `TaskModel` في `common/database.py`،
-- حيث `id` هو معرّف المهمة ولا يوجد عمود `task_id`. لتصحيح نشرة طُبِّق عليها هذا
-- الملف، طبّق `004_unify_tasks_schema.sql`. لا تُعتمد الأعمدة أدناه كعقد.
CREATE TABLE IF NOT EXISTS tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id         VARCHAR(255) UNIQUE NOT NULL,
    type            VARCHAR(50) NOT NULL,
    description     TEXT NOT NULL,
    priority        VARCHAR(20) DEFAULT 'normal'
                    CHECK (priority IN ('low', 'normal', 'high', 'critical')),
    status          VARCHAR(30) DEFAULT 'pending'
                    CHECK (status IN ('pending', 'assigned', 'running', 'completed', 'failed', 'cancelled')),
    domain          VARCHAR(100),
    tenant_id       VARCHAR(100),
    assigned_agent  VARCHAR(255),
    result          JSONB,
    quality_score   DECIMAL(3,2),
    budget_used     JSONB DEFAULT '{}',
    parent_task_id  UUID REFERENCES tasks(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    assigned_at     TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_tasks_task_id   ON tasks (task_id);
CREATE INDEX idx_tasks_status    ON tasks (status);
CREATE INDEX idx_tasks_domain    ON tasks (domain);
CREATE INDEX idx_tasks_priority  ON tasks (priority);

-- ============================================================
-- 4. experiences — الخبرات (Experience Replay)
-- ============================================================
CREATE TABLE IF NOT EXISTS experiences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experience_id   VARCHAR(255) UNIQUE NOT NULL,
    task_id         UUID REFERENCES tasks(id),
    type            VARCHAR(20) NOT NULL
                    CHECK (type IN ('success', 'failure', 'gap', 'repair')),
    agent_id        VARCHAR(255),
    model_used      VARCHAR(100),
    outcome         JSONB NOT NULL DEFAULT '{}',
    quality_score   DECIMAL(3,2),
    provenance      JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_exp_type        ON experiences (type);
CREATE INDEX idx_exp_agent       ON experiences (agent_id);
CREATE INDEX idx_exp_quality     ON experiences (quality_score);

-- ============================================================
-- 5. model_versions — النماذج (النسخ المسجلة)
-- ============================================================
CREATE TABLE IF NOT EXISTS model_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id        VARCHAR(255) UNIQUE NOT NULL,
    parent_model    VARCHAR(255),
    base_model      VARCHAR(255) NOT NULL,
    status          VARCHAR(20) DEFAULT 'draft'
                    CHECK (status IN ('draft', 'training', 'evaluating', 'shadow', 'canary', 'active', 'archived', 'rejected')),
    training_data   JSONB,
    evaluation      JSONB,
    weights_location VARCHAR(500),
    model_bom       JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    activated_at    TIMESTAMPTZ
);

CREATE INDEX idx_models_status   ON model_versions (status);

-- ============================================================
-- 6. audit_log — سجل التدقيق (غير قابل للتعديل)
-- ============================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        VARCHAR(255) UNIQUE NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type      VARCHAR(50) NOT NULL,
    actor_type      VARCHAR(20) NOT NULL
                    CHECK (actor_type IN ('system', 'agent', 'human', 'governance')),
    actor_id        VARCHAR(255),
    action          VARCHAR(255) NOT NULL,
    chain_hash      VARCHAR(255) NOT NULL,
    prev_hash       VARCHAR(255),
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX idx_audit_timestamp ON audit_log (timestamp);
CREATE INDEX idx_audit_event_type ON audit_log (event_type);
CREATE INDEX idx_audit_actor     ON audit_log (actor_type, actor_id);

-- Append-only: prevent UPDATE and DELETE
CREATE RULE audit_no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE audit_no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;
-- Production: also REVOKE UPDATE, DELETE ON audit_log FROM amos_app;

-- ============================================================
-- 7. approvals — الموافقات الموقعة
-- ============================================================
CREATE TABLE IF NOT EXISTS approvals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id     VARCHAR(255) UNIQUE NOT NULL,
    type            VARCHAR(50) NOT NULL
                    CHECK (type IN ('model_promotion', 'agent_birth', 'agent_death',
                                    'kill_switch', 'constitutional_amendment', 'budget_override')),
    decision        VARCHAR(20) NOT NULL
                    CHECK (decision IN ('approved', 'rejected', 'pending')),
    reviewer_id     VARCHAR(255) NOT NULL,
    reason          TEXT,
    payload_hash    VARCHAR(255) NOT NULL,
    signature       VARCHAR(500) NOT NULL,
    algorithm       VARCHAR(20) DEFAULT 'Ed25519',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    decided_at      TIMESTAMPTZ
);

CREATE INDEX idx_approvals_type    ON approvals (type);
CREATE INDEX idx_approvals_decision ON approvals (decision);

-- ============================================================
-- 8. tool_executions — سجل تنفيذ الأدوات
-- ============================================================
CREATE TABLE IF NOT EXISTS tool_executions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id    VARCHAR(255) UNIQUE NOT NULL,
    tool_id         VARCHAR(255) NOT NULL,
    agent_id        VARCHAR(255) NOT NULL,
    task_id         UUID REFERENCES tasks(id),
    inputs          JSONB NOT NULL DEFAULT '{}',
    outputs         JSONB,
    status          VARCHAR(20) DEFAULT 'running'
                    CHECK (status IN ('running', 'success', 'failed', 'timeout')),
    error           TEXT,
    duration_ms     INTEGER,
    tokens_used     INTEGER DEFAULT 0,
    cost_usd        DECIMAL(10,4) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_tool_exec_agent   ON tool_executions (agent_id);
CREATE INDEX idx_tool_exec_tool    ON tool_executions (tool_id);
CREATE INDEX idx_tool_exec_status  ON tool_executions (status);

-- ============================================================
-- 9. budgets — الميزانيات والاستهلاك
-- ============================================================
CREATE TABLE IF NOT EXISTS budgets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     VARCHAR(20) NOT NULL
                    CHECK (entity_type IN ('agent', 'state', 'federal')),
    entity_id       VARCHAR(255) NOT NULL,
    period          VARCHAR(10) NOT NULL,
    token_limit     BIGINT NOT NULL,
    token_used      BIGINT DEFAULT 0,
    cost_limit_usd  DECIMAL(10,2) NOT NULL,
    cost_used_usd   DECIMAL(10,4) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (entity_type, entity_id, period)
);

CREATE INDEX idx_budgets_entity ON budgets (entity_type, entity_id);

-- ============================================================
-- 10. constitution_versions — نسخ الدستور
-- ============================================================
CREATE TABLE IF NOT EXISTS constitution_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version         VARCHAR(20) NOT NULL,
    content_hash    VARCHAR(255) NOT NULL,
    articles        JSONB NOT NULL DEFAULT '[]',
    signed_by       VARCHAR(255) NOT NULL,
    signature       VARCHAR(500) NOT NULL,
    activated_at    TIMESTAMPTZ DEFAULT NOW(),
    is_active       BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_constitution_active ON constitution_versions (is_active);

-- ============================================================
-- Updated trigger for updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
