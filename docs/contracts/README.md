# docs/contracts — العقود والمخططات

## التعريف
مجلد عقود البيانات (Contracts) للدولة الفدرالية الرقمية AMOS-Federation.

## النطاق
مخططات JSON Schema لكل مجال، تعرّف بنية البيانات والعقود بين الأجزاء.

## المالك
core/meta/

## تاريخ الإنشاء
2026-08-15 (المرحلة P2)

## بصمة الهوية
يخضع هذا المجلد لقانون هوية الملفات (المادة الدستورية 009).

## الملفات

| الملف | المجال | الجداول المرتبطة |
|------|--------|-------------------|
| `schemas/tools.schema.json` | tools | `tools`, `tool_generation_queue` |
| `schemas/agent.schema.json` | agents | `agents`, `agent_population` |
| `schemas/institution.schema.json` | institutions | `institutions` |
| `schemas/task.schema.json` | runtime | `tasks` |
| `schemas/event.schema.json` | runtime | `event_store`, `durable_events` |
| `schemas/interface.schema.json` | interfaces | `interface_registry` |
| `schemas/approval.schema.json` | royal | `approvals`, `audit_entries`, `reviews` |
| `schemas/treasury.schema.json` | federal | `treasury_transactions`, `treasury_budgets`, `treasury_reports` |
| `schemas/memory.schema.json` | core | `memories`, `experiences` |
| `schemas/state_policy.schema.json` | states | `legislations`, `compliance_reports` |
| `schemas/observability.schema.json` | ops | `agent_health_checks`, `agent_isolations`, `agent_treatments` |
| `schemas/smoke_test.schema.json` | tests | — (مخصص لاختبارات الدخان) |

## قاعدة المخطط
كل مخطط:
- يستخدم JSON Schema Draft-07
- يحتوي على `$schema`, `$id`, `title`, `type`, `properties`, `required`
- يحتوي على `x-amos` metadata: `{domain, created, phase, status}`
- `additionalProperties: false` للعقود الصارمة
- مواءم مع جداول قاعدة بيانات Supabase الفعلية
