-- AMOS-Federation Seed Data
-- الهدف: بيانات أولية للنظام (وكلاء، أدوات، دستور)
-- النطاق: قاعدة بيانات amos_federation
-- المالك: federal/executive/services
-- تاريخ الإنشاء: 2026-08-15

-- Agent: Orchestrator
INSERT INTO agents (agent_id, agent_type, domain, manifest, permissions, budget)
VALUES (
    'orchestrator-001',
    'orchestrator',
    'federal',
    '{"name": "Orchestrator", "description": "رئيس الوزراء — ينسق كل الولايات"}'::jsonb,
    '["read_all", "delegate", "coordinate"]'::jsonb,
    '{"daily_token_limit": 5000000, "daily_cost_limit": 500.00}'::jsonb
) ON CONFLICT (agent_id) DO NOTHING;

-- Agent: Financial Worker
INSERT INTO agents (agent_id, agent_type, domain, manifest, permissions, budget)
VALUES (
    'worker-financial-analyzer-001',
    'worker',
    'finance',
    '{"name": "Financial Analyzer", "description": "محلل مالي في ولاية المال"}'::jsonb,
    '["sql_query", "python_execute", "chart_generate"]'::jsonb,
    '{"daily_token_limit": 100000, "daily_cost_limit": 10.00, "max_concurrent": 5}'::jsonb
) ON CONFLICT (agent_id) DO NOTHING;

-- Agent: Critic
INSERT INTO agents (agent_id, agent_type, domain, manifest, permissions, budget)
VALUES (
    'critic-001',
    'critic',
    'federal',
    '{"name": "Critic", "description": "المراجع — يقيم جودة النتائج"}'::jsonb,
    '["read_all", "score", "review"]'::jsonb,
    '{"daily_token_limit": 200000, "daily_cost_limit": 20.00}'::jsonb
) ON CONFLICT (agent_id) DO NOTHING;

-- Tools
INSERT INTO tools (tool_id, name, version, input_schema, output_schema, risk_level, sandbox_required) VALUES
    ('sql_query', 'SQL Query Executor', '2.1.0',
     '{"database": "string", "query": "string", "timeout": "integer"}'::jsonb,
     '{"rows": "array", "columns": "array", "row_count": "integer"}'::jsonb,
     'low', true),
    ('python_execute', 'Python Code Executor', '1.5.0',
     '{"code": "string", "timeout": "integer"}'::jsonb,
     '{"stdout": "string", "stderr": "string", "result": "any"}'::jsonb,
     'medium', true),
    ('chart_generate', 'Chart Generator', '1.2.0',
     '{"data": "array", "chart_type": "string", "title": "string"}'::jsonb,
     '{"image_path": "string", "format": "string"}'::jsonb,
     'low', true),
    ('document_analysis', 'Document Analyzer', '1.0.0',
     '{"document": "string", "analysis_type": "string"}'::jsonb,
     '{"summary": "string", "entities": "array", "sentiment": "string"}'::jsonb,
     'medium', true),
    ('legal_search', 'Legal Search Engine', '1.1.0',
     '{"query": "string", "jurisdiction": "string"}'::jsonb,
     '{"results": "array", "count": "integer"}'::jsonb,
     'low', false),
    ('research_apis', 'External Research APIs', '2.0.0',
     '{"query": "string", "sources": "array"}'::jsonb,
     '{"results": "array", "sources_used": "array"}'::jsonb,
     'medium', true),
    ('data_analysis', 'Statistical Data Analysis', '1.3.0',
     '{"data": "array", "method": "string", "params": "object"}'::jsonb,
     '{"statistics": "object", "visualizations": "array"}'::jsonb,
     'medium', true),
    ('medical_dbs', 'Medical Database Query', '1.0.0',
     '{"database": "string", "query": "string"}'::jsonb,
     '{"results": "array", "count": "integer"}'::jsonb,
     'high', true),
    ('generation', 'Content Generation', '2.5.0',
     '{"prompt": "string", "max_tokens": "integer"}'::jsonb,
     '{"text": "string", "tokens_used": "integer"}'::jsonb,
     'medium', true),
    ('design', 'Design Tool', '1.0.0',
     '{"spec": "string", "format": "string"}'::jsonb,
     '{"image_path": "string", "format": "string"}'::jsonb,
     'low', true)
ON CONFLICT (tool_id) DO NOTHING;

-- Constitution v1.0
INSERT INTO constitution_versions (version, content_hash, articles, signed_by, signature, is_active)
VALUES (
    '1.0.0',
    'sha256:pending_initial_hash',
    '[1,2,3,4,5,6,7,8,9]'::jsonb,
    'driving-h',
    'ed25519:pending_initial_signature',
    true
) ON CONFLICT DO NOTHING;

-- Budget: Orchestrator (daily)
INSERT INTO budgets (entity_type, entity_id, period, token_limit, token_used, cost_limit_usd, cost_used_usd)
VALUES ('agent', 'orchestrator-001', to_char(NOW(), 'YYYY-MM-DD'), 5000000, 0, 500.00, 0)
ON CONFLICT (entity_type, entity_id, period) DO NOTHING;

-- Budget: Financial Worker (daily)
INSERT INTO budgets (entity_type, entity_id, period, token_limit, token_used, cost_limit_usd, cost_used_usd)
VALUES ('agent', 'worker-financial-analyzer-001', to_char(NOW(), 'YYYY-MM-DD'), 100000, 0, 10.00, 0)
ON CONFLICT (entity_type, entity_id, period) DO NOTHING;

-- Budget: Critic (daily)
INSERT INTO budgets (entity_type, entity_id, period, token_limit, token_used, cost_limit_usd, cost_used_usd)
VALUES ('agent', 'critic-001', to_char(NOW(), 'YYYY-MM-DD'), 200000, 0, 20.00, 0)
ON CONFLICT (entity_type, entity_id, period) DO NOTHING;
