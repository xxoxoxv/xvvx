# P2 Schemas Creation — Findings Summary

## الهدف
تسجيل نتائج إنشاء مخططات JSON للمرحلة الثانية (العقود والمخططات) وما تبيّن خلالها.

**Task:** Create JSON Schema files for Phase 2 (P2) "Contracts and Schemas" of the AMOS-Federation execution plan.
**Date:** 2026-08-15
**Status:** COMPLETE

## Verification Source

All schema column definitions were verified against the live Supabase database (project `mqcfmwtdaymrmwvthqyw`, "zoorooz's Project", region ap-northeast-1, PostgreSQL 17) via the `list_tables` connector tool with `verbose=true`. The actual table columns matched the task description exactly. Blueprint sections 8.3 (Tool Registration Protocol) and 12.1 (Event Schema) were read from `docs/blueprints/AMOS-SE_Final_Blueprint.pplx.md`.

## Files Created

### JSON Schemas (12) — `/home/user/workspace/AMOS-Fedration/docs/contracts/schemas/`

| # | File | Domain | Based on (tables) | Blueprint ref |
|---|------|--------|--------------------|---------------|
| 1 | tools.schema.json | tools | `tools` | §8.3 (input_schema/output_schema) |
| 2 | agent.schema.json | agents | `agents` + `agent_population` | — |
| 3 | institution.schema.json | institutions | `institutions` | — |
| 4 | task.schema.json | runtime | `tasks` | — |
| 5 | event.schema.json | runtime | `event_store` + `durable_events` | §12.1 (full event schema) |
| 6 | interface.schema.json | interfaces | `interface_registry` | — |
| 7 | approval.schema.json | royal | `approvals` + `audit_entries` + `reviews` | — |
| 8 | treasury.schema.json | federal | `treasury_transactions` + `treasury_budgets` + `treasury_reports` | — |
| 9 | memory.schema.json | core | `memories` + `experiences` | — |
| 10 | state_policy.schema.json | states | `legislations` + `compliance_reports` | — |
| 11 | observability.schema.json | ops | `agent_health_checks` + `agent_isolations` + `agent_treatments` | — |
| 12 | smoke_test.schema.json | tests | (custom test result structure) | — |

### ADR Template — `/home/user/workspace/AMOS-Fedration/docs/adr/template.md`

Bilingual (English + Arabic) ADR template with sections: Title, Status (proposed/accepted/deprecated/superseded), Context, Decision, Consequences, Alternatives, Date, Authors, plus a Related section. Matches the existing Arabic ADR README style.

## Schema Conventions Applied

- `$schema`: `http://json-schema.org/draft-07/schema#` (all 12 files)
- `$id`: canonical URL `https://amos-federation/docs/contracts/schemas/<name>.schema.json`
- `x-amos` metadata in every file: `{ "domain": "<domain>", "created": "2026-08-15", "phase": "P2", "status": "stub" }`
- `additionalProperties: false` at top level and on nested sub-objects (strict contracts)
- Enums applied where the blueprint or domain semantics define a closed set (e.g. event_type, tx_type, status fields, experience type, actor type)
- Numeric ranges (minimum/maximum) applied to scores (0-1) and budget/amount fields (≥0)
- `format: "date-time"` applied to all timestamp columns
- Defaults from the DB schema preserved (e.g. priority='normal', domain='general', status='active', created_by='system', interface_type='custom', budget=0)

## Validation Results

- **`python3 -c "import json; json.load(open('file'))"`**: all 12 files pass (valid JSON)
- **`jsonschema.Draft7Validator.check_schema`**: all 12 files pass (valid JSON Schema Draft-07 documents conforming to the official meta-schema)
- **`x-amos` metadata check**: all 12 files have correct created=2026-08-15, phase=P2, status=stub, and domain set
- **`$schema` check**: all 12 files use `http://json-schema.org/draft-07/schema#`

## Notes

- The `event.schema.json` event_type enum combines the blueprint §12.1 enum (17 values) with the domain event contracts from `docs/implementation/event-contracts.md` (task.created, experience.recorded, approval.signed) for a total of 20 enum values.
- The `durable_events` table stores `data` as text (JSON-encoded); the schema reflects this as `type: string` with a description noting the semantic JSON payload.
- The `agent_population.permissions` and `allowed_tools` columns are stored as text in the DB but semantically lists; the `agent.schema.json` models the canonical `agents` table (json columns) as arrays and the population sub-object reflects the population table's text columns as described.
- The validation helper script `_validate.py` was created during validation and then removed; only the 12 schema files remain in the schemas directory.
