# Agent Manifest: worker-analyst
# الهدف: توصيف وكيل التحليل في ولاية العلم
# النطاق: states/science/agents
# المالك: agents/registry
# تاريخ الإنشاء: 2026-08-15

agent_id: "worker-analyst"
agent_type: "worker"
domain: "science"
version: "1.0.0"
status: "active"

description: "وكيل محلل يحلل البيانات ويستخرج الاستنتاجات"

permissions:
  - "data_analysis"
  - "sql_query"
  - "python_execute"
  - "chart_generate"

tools:
  - "data_analysis"
  - "sql_query"
  - "python_execute"
  - "chart_generate"

budget:
  daily_token_limit: 120000
  daily_cost_limit: 12.00
  max_concurrent_tasks: 5

capabilities:
  - "statistical_analysis"
  - "data_visualization"
  - "trend_detection"

successor: "critic-001"
