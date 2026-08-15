# الوكلاء المستوردون (Imported Agents)

المرحلة 1 — السحب. سحب كل إطار/وكيل خارجي من قائمة المصادر إلى مجلد خاص به حسب تخصصه، **دون نسخ كود المصدر** (لمنع تضخم المستودع ومشاكل التراخيص).

## البنية

```
agents/identities/imported/<domain>/<agent-slug>/
  identity.md      # هوية الوكيل كموظف مرشح
  upstream.yaml    # المصدر وحالة السحب والفحص
agents/registry/imported_citizens.yaml   # السجل المركزي
agents/registry/imported_agents_data.py  # بيانات المصادر
agents/registry/generate_imported.py      # مولّد المجلدات والسجل
```

## المبدأ

كل وكيل مستورد يبدأ بحالة `imported_candidate` ولا يُمنح أي صلاحية تشغيل إنتاجية قبل:
1. فحص الترخيص
2. فحص أمني أساسي
3. تصنيف القدرات
4. اجتياز تدريب المدرسة بنسبة ≥ 85%
5. موافقة الحوكمة

هذا يحقق مبدأ "المراقبة قبل الثقة" و"الموافقة المشروطة" من الدستور الفدرالي.

## التوزيع حسب المكان المخصص

يتوفر في `imported_citizens.yaml` تحت `domain_distribution`. كل مجال يطابق بنية المستودع الفدرالية (federal/executive، states/infrastructure، memory، security، ...).
