-- =============================================================================
-- AMOS-Federation Migration 004 — توحيد مرجعية جدول tasks
-- الهدف: إلغاء تنافس نموذجين على نفس الجدول، وجعل TaskModel المرجع الوحيد.
-- النطاق: federal/executive/services
-- المالك: ديوان التدقيق
-- تاريخ الإنشاء: 2026-08-16
-- =============================================================================
--
-- السبب الجذري:
--   كان في المستودع **مخطَّطان متنافسان** لجدول `tasks`:
--     (أ) `migrations/001_init.sql` — مفتاح `id UUID` + عمود `task_id VARCHAR UNIQUE`.
--     (ب) نموذج ORM `TaskModel` في `common/database.py` — مفتاح `id` هو معرّف
--         المهمة نفسه، **ولا يوجد عمود `task_id` إطلاقًا**.
--   وكان `api_gateway/store.py` يكتب SQL خامًا يخاطب `tasks.task_id`، فيفشل على
--   أي قاعدة أُنشئت من ORM ثم **يرجع صامتًا إلى الذاكرة**، فتبدو الكتابة ناجحة
--   وهي لا تُحفظ. أُزيل ذلك المسار الخام في نفس نقطة التفتيش.
--
-- القرار (بأمر المالك، E2.2-G):
--   طبقة قاعدة البيانات هي مصدر الحقيقة الدائم للمهام، و`TaskModel` هو النموذج
--   الدائم الأساسي. `id` هو معرّف المهمة. الذاكرة ليست مصدر حقيقة.
--
-- هذه الهجرة تُصلح النشرات التي طُبِّق عليها 001_init.sql فقط. القواعد المُنشأة
-- من ORM متوافقة أصلًا ولا يغيّرها هذا الملف.
--
-- تحذير: الخطوة 3 تُسقط عمودًا. لا تُطبَّق قبل أخذ نسخة احتياطية.
-- =============================================================================

BEGIN;

-- الخطوة 1: نقل معرّف المهمة النصي إلى العمود المرجعي `id`.
-- ينفَّذ فقط إن كان العمود القديم `task_id` موجودًا فعلًا.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'tasks' AND column_name = 'task_id'
    ) THEN
        -- `id` كان UUID في المخطَّط القديم؛ يصبح نصًّا ليحمل معرّف المهمة.
        ALTER TABLE tasks ALTER COLUMN id DROP DEFAULT;
        ALTER TABLE tasks ALTER COLUMN id TYPE VARCHAR(255) USING id::text;

        -- الخطوة 2: نقل القيم — كل صف يأخذ معرّف مهمته المنطقي.
        UPDATE tasks SET id = task_id WHERE task_id IS NOT NULL AND id <> task_id;

        -- الخطوة 3: إسقاط العمود المتنافس بعد نقل قيمه.
        ALTER TABLE tasks DROP COLUMN task_id;
    END IF;
END $$;

-- الخطوة 4: مواءمة الأعمدة التي يعرّفها TaskModel ولا يعرّفها 001_init.sql.
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS plan JSONB DEFAULT '[]'::jsonb;
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

COMMIT;

-- التحقق بعد التطبيق (يجب أن يعيد صفرًا):
--   SELECT count(*) FROM information_schema.columns
--   WHERE table_name = 'tasks' AND column_name = 'task_id';
