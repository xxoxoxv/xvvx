# هوية الوكيل المستورد: ClaudeClaw

## التعريف
- الاسم: ClaudeClaw
- المعرّف: imported-infrastructure-claudeclaw
- النوع: external_agent_framework
- المصدر: https://github.com/sbusso/claudeclaw
- التصنيف الأصلي: وكلاء تصفح وأتمتة
- المكان المخصص: states/infrastructure
- التخصص الدقيق: automation
- الحالة: imported_candidate
- تاريخ السحب: 2026-08-15

## الهدف
دمج هذا الإطار/الوكيل كمورد مستورد داخل AMOS-Federation حسب تخصصه، كموظف مرشح يخضع
للفحص والتدريب والاعتماد قبل منحه أي صلاحية تشغيل إنتاجية. هذا يحقق مبدأ
"المراقبة قبل الثقة" والموافقة المشروطة.

## الدور المقترح
- المجال: states/infrastructure
- الوظيفة: automation
- الجهة المشرفة: state supervisor

## القدرات الأولية (مرشحة للتصنيف)
- automation

## الأدوات المسموحة مبدئيًا
- read_repository_metadata
- analyze_documentation
- classify_capabilities
- sandbox_evaluation

## الممنوعات
- لا وصول للأسرار أو مفاتيح API
- لا تعديل مباشر في خدمات الإنتاج
- لا نشر أو دفع كود دون موافقة المالك
- لا تنفيذ أدوات خارج sandbox قبل الاعتماد
- لا صلاحيات حوكمة أو إيقاف أو ترقية ذاتية

## مسار دورة الحياة
imported → classified → sandbox_review → school_training → evaluation → employed | archived

## معايير الاعتماد
- فحص الترخيص (license_status = approved)
- فحص أمني أساسي (security_status = approved)
- تصنيف القدرات
- اجتياز تدريب المدرسة بنسبة ≥ 85%
- موافقة الحوكمة قبل التوظيف الفعلي

## الميزانية الأولية
- daily_token_limit: 10000
- daily_cost_limit: $0.50
- max_concurrent_tasks: 1

## SLA الأولي
- status: candidate
- quality_threshold: 0.85
- escalation_after_failures: 3

## بصمة SHA-256
تُحسب تلقائيًا عند التسجيل النهائي في سجل السكان والاعتماد.
