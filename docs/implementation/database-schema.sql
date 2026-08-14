-- AMOS-Federation Core Database Schema v1.0
-- الهدف: تعريف جداول قاعدة البيانات الرئيسية للنظام
-- النطاق: كل الخدمات التي تستخدم PostgreSQL
-- المالك: docs/implementation
-- تاريخ الإنشاء: 2026-08-15
-- See: docs/implementation/database-schema-full.sql for complete version

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- agents (السكان)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    agent_type VARCHAR(50) NOT NULL,
    domain VARCHAR(100),
    version VARCHAR(20) DEFAULT '1.0.0',
    status VARCHAR(20) DEFAULT 'active',
    manifest JSONB NOT NULL,
    permissions JSONB DEFAULT '[]',
    budget JSONB DEFAULT '{}',
    tenant_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- tools (الموارد)
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    risk_level VARCHAR(20) DEFAULT 'low',
    sandbox_required BOOLEAN DEFAULT TRUE,
    tool_bom JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- tasks (المهام)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(30) DEFAULT 'pending',
    result JSONB,
    quality_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- experiences (الخبرات)
CREATE TABLE experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experience_id VARCHAR(255) UNIQUE NOT NULL,
    task_id UUID REFERENCES tasks(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('success', 'failure', 'gap', 'repair')),
    agent_id VARCHAR(255),
    model_used VARCHAR(100),
    outcome JSONB NOT NULL,
    quality_score DECIMAL(3,2),
    provenance JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- model_versions (النماذج)
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id VARCHAR(255) UNIQUE NOT NULL,
    parent_model VARCHAR(255),
    base_model VARCHAR(255) NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',
    training_data JSONB,
    evaluation JSONB,
    weights_location VARCHAR(500),
    model_bom JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- audit_log (سجل التدقيق — غير قابل للتعديل)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    actor_type VARCHAR(20) NOT NULL,
    actor_id VARCHAR(255),
    action VARCHAR(255) NOT NULL,
    chain_hash VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}'
);

-- Append-only
CREATE RULE no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;
-- Production: REVOKE UPDATE, DELETE ON audit_log FROM amos_app;
