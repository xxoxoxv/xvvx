-- Core Database Schema for AMOS Federation
-- Purpose: Defines the persistent storage structure for all federation data
-- Owner: database_persistence
-- Created: 2026-08-17

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    tenant_id UUID NOT NULL,
    owner_id UUID NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    capabilities JSONB DEFAULT '[]',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    version VARCHAR(50) DEFAULT '1.0.0',
    metadata JSONB DEFAULT '{}'
);

-- Agent profiles table
CREATE TABLE IF NOT EXISTS agent_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    tags TEXT[] DEFAULT '{}',
    avatar_url TEXT,
    public BOOLEAN DEFAULT FALSE,
    trust_score DECIMAL(3,2) DEFAULT 0.00,
    reputation JSONB DEFAULT '{}',
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    tenant_id UUID NOT NULL,
    assigned_agent_id UUID REFERENCES agents(id),
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Events table (immutable audit trail)
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    aggregate_type VARCHAR(100) NOT NULL,
    tenant_id UUID NOT NULL,
    data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}',
    sequence_number BIGINT NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(type);
CREATE INDEX IF NOT EXISTS idx_agent_profiles_agent ON agent_profiles(agent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_events_aggregate ON events(aggregate_id, aggregate_type);
CREATE INDEX IF NOT EXISTS idx_events_tenant ON events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_events_sequence ON events(sequence_number);
