-- Database schema definition for PostgreSQL

-- AMOS Federal State - Complete Database Schema
-- Owner: zoorooz (Sovereign)
-- Project: https://zwuhhjjoyvhqndiruodh.supabase.co

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- === CORE SOVEREIGNTY TABLES ===

-- Citizens table
CREATE TABLE IF NOT EXISTS citizens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    national_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    date_of_birth DATE,
    place_of_birth VARCHAR(255),
    nationality VARCHAR(100) DEFAULT 'Federal',
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Roles and permissions
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    level VARCHAR(50) DEFAULT 'citizen',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS citizen_roles (
    citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    granted_by UUID REFERENCES citizens(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (citizen_id, role_id)
);

-- === FEDERAL INSTITUTIONS ===

CREATE TABLE IF NOT EXISTS institutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL,
    parent_institution_id UUID REFERENCES institutions(id),
    constitution_article INTEGER,
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS institution_members (
    institution_id UUID REFERENCES institutions(id) ON DELETE CASCADE,
    citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
    role VARCHAR(100) NOT NULL,
    appointed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    appointed_by UUID REFERENCES citizens(id),
    PRIMARY KEY (institution_id, citizen_id)
);

-- === LEGISLATIVE BRANCH ===

CREATE TABLE IF NOT EXISTS laws (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    article_number VARCHAR(50),
    chapter VARCHAR(100),
    category VARCHAR(100),
    status VARCHAR(50) DEFAULT 'draft',
    proposed_by UUID REFERENCES citizens(id),
    approved_by UUID REFERENCES citizens(id),
    enacted_at TIMESTAMP WITH TIME ZONE,
    repealed_at TIMESTAMP WITH TIME ZONE,
    content JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS legislative_votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    law_id UUID REFERENCES laws(id) ON DELETE CASCADE,
    voter_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
    vote VARCHAR(20) NOT NULL,
    voted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(law_id, voter_id)
);

-- === EXECUTIVE BRANCH ===

CREATE TABLE IF NOT EXISTS executive_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    order_number VARCHAR(50),
    issued_by UUID REFERENCES citizens(id),
    status VARCHAR(50) DEFAULT 'pending',
    effective_date TIMESTAMP WITH TIME ZONE,
    expiry_date TIMESTAMP WITH TIME ZONE,
    content JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS government_agencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    parent_agency_id UUID REFERENCES government_agencies(id),
    director_id UUID REFERENCES citizens(id),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- === JUDICIAL BRANCH ===

CREATE TABLE IF NOT EXISTS courts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    level VARCHAR(50) NOT NULL,
    jurisdiction VARCHAR(255),
    location VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_number VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    court_id UUID REFERENCES courts(id),
    plaintiff_id UUID REFERENCES citizens(id),
    defendant_id UUID REFERENCES citizens(id),
    judge_id UUID REFERENCES citizens(id),
    case_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'open',
    filed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    judgment TEXT,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS case_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    document_type VARCHAR(100),
    content TEXT,
    filed_by UUID REFERENCES citizens(id),
    filed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- === TREASURY AND FINANCE ===

CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number VARCHAR(50) UNIQUE NOT NULL,
    owner_id UUID REFERENCES citizens(id),
    account_type VARCHAR(50) DEFAULT 'personal',
    currency VARCHAR(10) DEFAULT 'FED',
    balance DECIMAL(20, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_account UUID REFERENCES accounts(id),
    to_account UUID REFERENCES accounts(id),
    amount DECIMAL(20, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'FED',
    transaction_type VARCHAR(50),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fiscal_year INTEGER NOT NULL,
    institution_id UUID REFERENCES institutions(id),
    allocated_amount DECIMAL(20, 2) NOT NULL,
    spent_amount DECIMAL(20, 2) DEFAULT 0,
    status VARCHAR(50) DEFAULT 'approved',
    approved_by UUID REFERENCES citizens(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- === TASKS AND AGENTS ===

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'normal',
    status VARCHAR(50) DEFAULT 'pending',
    assigned_to UUID REFERENCES citizens(id),
    assigned_agent_id UUID,
    created_by UUID REFERENCES citizens(id),
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    result JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(100) NOT NULL,
    capabilities JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'inactive',
    owner_id UUID REFERENCES citizens(id),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_tasks (
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'assigned',
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (agent_id, task_id)
);

-- === EVENTS AND AUDIT LOG ===

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    source VARCHAR(255),
    actor_id UUID REFERENCES citizens(id),
    target_id UUID,
    data JSONB DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'info',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_id UUID REFERENCES events(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    actor_id UUID REFERENCES citizens(id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- === CONSTITUTION ===

CREATE TABLE IF NOT EXISTS constitution_articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    article_number INTEGER UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    chapter VARCHAR(100),
    section VARCHAR(100),
    amended_at TIMESTAMP WITH TIME ZONE,
    amended_by UUID REFERENCES citizens(id),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- === SKILLS AND CAPABILITIES ===

CREATE TABLE IF NOT EXISTS skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS citizen_skills (
    citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
    skill_id UUID REFERENCES skills(id) ON DELETE CASCADE,
    proficiency_level INTEGER DEFAULT 1 CHECK (proficiency_level BETWEEN 1 AND 5),
    certified_at TIMESTAMP WITH TIME ZONE,
    certified_by UUID REFERENCES citizens(id),
    PRIMARY KEY (citizen_id, skill_id)
);

-- === MEMORY AND EXPERIENCE ===

CREATE TABLE IF NOT EXISTS experiences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    citizen_id UUID REFERENCES citizens(id) ON DELETE CASCADE,
    experience_type VARCHAR(100),
    title VARCHAR(500),
    description TEXT,
    outcome JSONB,
    lessons_learned TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- === SEED DATA ===

-- Insert default roles
INSERT INTO roles (name, description, level) VALUES 
('sovereign', 'Absolute ruler of the state', 'sovereign'),
('royal', 'Member of royal family', 'royal'),
('minister', 'Government minister', 'executive'),
('judge', 'Judicial officer', 'judicial'),
('legislator', 'Member of legislature', 'legislative'),
('official', 'Government official', 'executive'),
('citizen', 'Regular citizen', 'citizen')
ON CONFLICT (name) DO NOTHING;

-- Insert sovereign citizen
INSERT INTO citizens (national_id, full_name, email, status) 
VALUES ('KING-001', 'zoorooz', 'sovereign@federal.state', 'active')
ON CONFLICT (national_id) DO NOTHING;

-- Grant sovereign role to king
INSERT INTO citizen_roles (citizen_id, role_id)
SELECT c.id, r.id FROM citizens c, roles r 
WHERE c.national_id = 'KING-001' AND r.name = 'sovereign'
ON CONFLICT (citizen_id, role_id) DO NOTHING;
