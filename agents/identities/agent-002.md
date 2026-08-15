# Agent Manifest: worker-researcher
# الهدف: توصيف وكيل البحث في ولاية العلم
# النطاق: states/science/agents
# المالك: agents/registry
# تاريخ الإنشاء: 2026-08-15

agent_id: "worker-researcher"
agent_type: "worker"
domain: "science"
version: "1.0.0"
status: "active"

description: "وكيل باحث يجمع المصادر والبيانات من واجهات خارجية"

permissions:
  - "research_apis"
  - "data_analysis"
  - "document_analysis"

tools:
  - "research_apis"
  - "data_analysis"
  - "document_analysis"

budget:
  daily_token_limit: 150000
  daily_cost_limit: 15.00
  max_concurrent_tasks: 3

capabilities:
  - "web_research"
  - "data_collection"
  - "source_verification"

successor: "worker-analyst"
