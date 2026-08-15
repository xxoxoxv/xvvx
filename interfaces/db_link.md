<!--
File:        interfaces/db_link.md
Purpose:     ربط مجال الواجهات بقاعدة بيانات Supabase — وثيقة الربط P4
Owner:       المجلس التأسيسي — Driving H
Created:     2026-08-15
Phase:       P4 — Database Linking
Article 009: يخضع هذا الملف لقانون هوية الملفات (المادة الدستورية 009). هذه ترويسة تعريفية إلزامية.
-->

# Interfaces — ربط قاعدة البيانات (db_link)

> **المرحلة P4 — ربط مجال الواجهات (API/CLI/Web) بقاعدة بيانات Supabase.**
> يوثّق جدول سجل الواجهات، أعمدته، أنواعها، واستعلامات نموذجية. لا تُنفّذ أي هجرات
> مدمّرة — الربط للقراءة فقط. **الجدول فارغ حاليًا.**

## مرجع مشروع Supabase

| الخاصية | القيمة |
|---|---|
| Project Ref | `mqcfmwtdaymrmwvthqyw` |
| Project URL | https://mqcfmwtdaymrmwvthqyw.supabase.co |
| PostgreSQL Host | `db.mqcfmwtdaymrmwvthqyw.supabase.co:5432` |
| Database | `postgres` |
| المستخدم | `postgres` |
| متغيرات الاتصال | `.env.example` — `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_DB_HOST` |

> نهج الربط: للقراءة فقط عبر Supabase REST API / PostgreSQL. لا تُنفّذ هجرات مدمّرة.

## الجداول المرتبطة

### 1. `interface_registry` — سجل الواجهات (0 صفوف)

| العمود | النوع | القيود / الافتراضي |
|---|---|---|
| `id` | int | **PK** |
| `interface_id` | varchar | **UNIQUE** |
| `name` | varchar | |
| `description` | text | |
| `interface_type` | varchar | DEFAULT `'custom'` |
| `route_path` | varchar | |
| `html_content` | text | |
| `created_by` | varchar | DEFAULT `'system'` |
| `status` | varchar | DEFAULT `'active'` |
| `created_at` | timestamp | |

## استعلامات نموذجية (تعمل على الجداول الفعلية)

```sql
-- قائمة الواجهات النشطة (list active interfaces)
SELECT interface_id, name, interface_type, route_path, created_by, status, created_at
FROM interface_registry
WHERE status = 'active'
ORDER BY created_at DESC;

-- الواجهات حسب النوع (by type)
SELECT interface_type, COUNT(*) AS count
FROM interface_registry
GROUP BY interface_type
ORDER BY count DESC;

-- الواجهات حسب المنشئ
SELECT created_by, COUNT(*) AS count
FROM interface_registry
GROUP BY created_by
ORDER BY count DESC;

-- تفاصيل واجهة عبر route_path
SELECT interface_id, name, description, route_path, html_content
FROM interface_registry
WHERE route_path = :route_path;
```

## ملاحظات

- **لا هجرات مدمّرة** (No destructive migrations). الربط للقراءة فقط.
- **الجدول فارغ حاليًا** (0 صفوف)؛ الاستعلامات صحيحة لكنها ستعي نتائج فارغة حتى تُسجَّل أول واجهة.
- `interface_id` هو المعرّف المنطقي الفريد؛ `route_path` يحدد مسار العرض.
- متغيرات الاتصال الكاملة في `.env.example` (المالك: zoorooz).
