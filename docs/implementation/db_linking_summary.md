<!--
File:        docs/implementation/db_linking_summary.md
Purpose:     ملخص ربط جميع مجالات المستودع بقاعدة بيانات Supabase — وثيقة تجميعية P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking (Summary)
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# P4 — ملخص ربط قاعدة البيانات (Database Linking Summary)

> **وثيقة تجميعية للمرحلة P4.** تلخّص ربط كل مجال في مستودع AMOS-Federation بقاعدة بيانات
> Supabase. كل مجال يملك ملف `db_link.md` خاصًا به يوثّق جداوله وأعمدتها واستعلاماتها.

## مرجع مشروع Supabase

| الخاصية | القيمة |
|---|---|
| Project Ref | `mqcfmwtdaymrmwvthqyw` |
| Project URL | https://mqcfmwtdaymrmwvthqyw.supabase.co |
| PostgreSQL Host | `db.mqcfmwtdaymrmwvthqyw.supabase.co:5432` |
| Database | `postgres` |
| المستخدم | `postgres` |
| ملف البيئة | `.env.example` |

## تفاصيل الاتصال (من `.env.example`)

```dotenv
DATABASE_URL=postgresql://postgres:****@db.mqcfmwtdaymrmwvthqyw.supabase.co:5432/postgres
SUPABASE_URL=https://mqcfmwtdaymrmwvthqyw.supabase.co
SUPABASE_PROJECT_REF=mqcfmwtdaymrmwvthqyw
SUPABASE_PUBLISHABLE_KEY=sb_publishable_****
SUPABASE_DB_HOST=db.mqcfmwtdaymrmwvthqyw.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
```

> ملاحظة تشغيلية من `.env.example`: بيئة الـ sandbox الحالية لا تستطيع الوصول المباشر لمضيف
> Supabase (TCP 5432 محظور). الـ AMOS runtime يتصل بها في بيئته الخاصة.

## المؤشرات الإجمالية

| المؤشر | القيمة |
|---|---|
| إجمالي الجداول المربوطة | 23 |
| المجالات المغطاة | 11 |
| الهجرات المدمّرة | **0** |
| نهج الربط | للقراءة فقط عبر Supabase REST API / PostgreSQL |
| تاريخ الإنشاء | 2026-08-15 |
| المرحلة | P4 — Database Linking |

## مصفوفة المجال × الجداول × الصفوف

| # | المجال | ملف الربط | الجدول | الصفوف |
|---|---|---|---|---:|
| 1 | agents | `agents/db_link.md` | `agents` | 0 |
| 2 | agents | `agents/db_link.md` | `agent_population` | 342 |
| 3 | agents | `agents/db_link.md` | `school_results` | 6 |
| 4 | tools | `tools/db_link.md` | `tools` | 10 |
| 5 | tools | `tools/db_link.md` | `tool_generation_queue` | 0 |
| 6 | runtime | `runtime/db_link.md` | `tasks` | 1 |
| 7 | runtime | `runtime/db_link.md` | `event_store` | 157 |
| 8 | royal | `royal/db_link.md` | `royal_guards` | 7 |
| 9 | royal | `royal/db_link.md` | `king_decrees` | 1 |
| 10 | royal | `royal/db_link.md` | `audit_entries` | 10 |
| 11 | royal | `royal/db_link.md` | `reviews` | 0 |
| 12 | institutions | `institutions/db_link.md` | `institutions` | 8 |
| 13 | federal | `federal/db_link.md` | `treasury_transactions` | 0 |
| 14 | federal | `federal/db_link.md` | `treasury_budgets` | 0 |
| 15 | federal | `federal/db_link.md` | `treasury_reports` | 0 |
| 16 | interfaces | `interfaces/db_link.md` | `interface_registry` | 0 |
| 17 | core | `core/db_link.md` | `memories` | 2 |
| 18 | core | `core/db_link.md` | `experiences` | 1 |
| 19 | tools/models | `tools/models/db_link.md` | `model_cache` | 2 |
| 20 | tools/models | `tools/models/db_link.md` | `model_cost_log` | 2 |
| 21 | states/health | `states/health/db_link.md` | `agent_health_checks` | 0 |
| 22 | states/health | `states/health/db_link.md` | `agent_treatments` | 0 |
| 23 | royal/security | `royal/security/db_link.md` | `agent_isolations` | 0 |

**ملاحظة:** تذكر `ARCHITECTURE.md` أيضًا الجدول `agent_training_queue` (0 صفوف) المرتبط بمجال
`agents/` — وهو مدرج ضمن جداول Supabase (23 جدولًا أساسيًا موثّقًا هنا + جدول الطابور).

## المجالات المغطاة (11)

| # | المجال | ملف الربط | عدد الجداول |
|---:|---|---|---:|
| 1 | core | `core/db_link.md` | 2 |
| 2 | royal | `royal/db_link.md` | 4 |
| 3 | royal/security | `royal/security/db_link.md` | 1 |
| 4 | federal | `federal/db_link.md` | 3 |
| 5 | states/health | `states/health/db_link.md` | 2 |
| 6 | institutions | `institutions/db_link.md` | 1 |
| 7 | agents | `agents/db_link.md` | 3 |
| 8 | tools | `tools/db_link.md` | 2 |
| 9 | tools/models | `tools/models/db_link.md` | 2 |
| 10 | interfaces | `interfaces/db_link.md` | 1 |
| 11 | runtime | `runtime/db_link.md` | 2 |
| | **الإجمالي** | **11 وثيقة** | **23 جدولًا** |

## نهج الربط

1. **للقراءة فقط** — كل وثائق `db_link.md` تتبنّى نهج الربط للقراءة فقط عبر Supabase REST
   API أو PostgreSQL مباشرة.
2. **لا هجرات مدمّرة** (No destructive migrations) — لا تُنشئ، تُعدّل، أو تُحذف جداول/أعمدة
   من هذه الوثائق. صفر هجرات مدمّرة.
3. **استعلامات حقيقية** — كل استعلام نموذجي يعمل فعليًا على الجداول الموجودة في قاعدة البيانات.
4. **هوية الملفات** — كل وثيقة تحمل ترويسة تعريفية وفق المادة الدستورية 009 (قانون هوية الملفات):
   المسار، الغرض، المالك، تاريخ الإنشاء، المرحلة P4.
5. **مرجع Supabase** — كل وثيقة تتضمن تفاصيل مشروع Supabase في أعلاها.

## سلسلة الحقيقة (Hash Chain)

الجداول التالية تستخدم سلسلة هاش للتحقق من السلامة (وفق ADR-010: Hash Chain لـ Audit Log):

- `audit_entries` (royal)
- `treasury_transactions` (federal)
- `agent_health_checks` (states/health)

كل وثيقة `db_link.md` ذات صلة تتضمن استعلام تحقق من السلسلة.

## المالك والتاريخ

- **المالك:** المجلس التأسيسي — Driving H
- **تاريخ الإنشاء:** 2026-08-15
- **المرحلة:** P4 — Database Linking
- **المادة الدستورية:** 009 (قانون هوية الملفات)
