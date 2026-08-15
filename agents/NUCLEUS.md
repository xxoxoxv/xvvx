# Agents — النواة

## الهدف
الوكلاء: الهويات، التدريب، النشر، الاعتماد، والتطور. كل وكيل مواطن في الدولة الرقمية له دور وصلاحيات وميزانية.

## الواجهة
- `identities/` — هويات الوكلاء
- `capabilities/` — مصفوفة المهارات
- `lifecycle/` — دورة الحياة
- `registry/` — السجل
- `evolution/` — التطور: التقطير، التقييم، التكرار، التدريب
- (Supabase: agents, agent_population — 342 وكيل، school_results — 6 نتائج)

## الحالة
stub — الهيكل موجود + evolution منقول

## الخطوات التالية
- ربط سجل الوكلاء بقاعدة البيانات
- تفعيل طابور التدريب (Supabase: agent_training_queue)
- ربط نتائج التدريب (Supabase: school_results)

## اختبار الدخان
```bash
test -f NUCLEUS.md && echo "agents: OK" || echo "agents: FAIL"
```
