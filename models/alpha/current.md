# النموذج الحاكم — Alpha

## الهدف
النموذج المستقر الذي يخدم كل الوكلاء العاملين في الإنتاج.

## الهوية
- model_id: alpha-v1.0
- parent: none (initial)
- base: llama-3-8b-instruct
- training_method: none (base model)
- status: stable
- promoted: 2026-08-15

## المسؤوليات
- خدمة كل المهام التشغيلية اليومية
- توليد الإجابات للوكلاء العاملين
- الأساس الذي تُقاس عليه كل النسخ المرشحة

## بوابات الترقية (لا تنطبق على النسخة الأولى)
النسخة الأولى تُعين يدويًا كـ alpha بعد اختبارات أساسية.
النسخ اللاحقة تمر بـ 5 بوابات: تقييم → shadow → canary → مراجعة بشرية → تفعيل.

## خطة التراجع
- لا توجد نسخة سابقة (هذه هي الأولى)
- في الفشل: العودة لاستخدام النموذج الخارجي (Claude) مباشرة

## الموقع
- weights: s3://amos-federation/models/alpha/v1.0/
- adapter: none (base model)
- checksum: sha256:...

## Model BOM
- base_model: meta-llama/Meta-Llama-3-8B-Instruct
- training_data: none
- lora_config: none
- data_bom: none
