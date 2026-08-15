# عقود الأحداث (Event Contracts)

كل حدث يُنشر على NATS JetStream بالـ subject: `amos_federation.{domain}.{event_type}`

## الأحداث الأساسية

### task.created
```json
{
  "event_id": "uuid",
  "timestamp": "2026-08-15T22:07:23Z",
  "event_type": "task.created",
  "source": "api-gateway",
  "data": {
    "task_id": "task-001",
    "type": "analysis",
    "description": "Analyze Q3 sales",
    "priority": "high",
    "domain": "finance"
  },
  "chain_hash": "sha256:..."
}
```

### agent.assigned
```json
{
  "event_id": "uuid",
  "event_type": "agent.assigned",
  "data": {
    "task_id": "task-001",
    "agent_id": "worker-financial-analyzer-001",
    "tools_allowed": ["sql_query"],
    "budget": {"max_tokens": 5000}
  },
  "chain_hash": "sha256:..."
}
```

### experience.recorded
```json
{
  "event_id": "uuid",
  "event_type": "experience.recorded",
  "data": {
    "experience_id": "exp-001",
    "task_id": "task-001",
    "type": "success",
    "quality_score": 0.92,
    "provenance": {"source": "live_operation", "verified": true}
  },
  "chain_hash": "sha256:..."
}
```

### approval.signed
```json
{
  "event_id": "uuid",
  "event_type": "approval.signed",
  "data": {
    "approval_id": "appr-001",
    "type": "model_promotion",
    "decision": "approved",
    "reviewer_id": "human-001",
    "signed_artifact": {
      "signature": "ed25519:...",
      "payload_hash": "sha256:..."
    }
  },
  "chain_hash": "sha256:..."
}
```
