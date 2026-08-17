# Training Service

خدمة تدريب LoRA + Model Registry + Data Pipeline ضمن AMOS-Federation.

## التعريف
خدمة التدريب: تُجهّز بيانات التدريب من سجل الخبرات، وتحاكي تدريب LoRA بمقاييس
حتمية، وتسجّل النماذج مع بطاقاتها وتتبّع حالاتها.

## النطاق
البيانات والتدريب وسجل النماذج فقط. **التدريب محاكاة** لا تدريبًا فعليًّا حتى
اليوم، فلا تُنسب إليها قدرة تدريب مُثبَتة. ولا يدخل هنا استدعاء نموذج وقت التشغيل
(موضعه بوابة النماذج).

## المالك
federal/executive/services/

## تاريخ الإنشاء
2026-08-15

## المسؤولية
- استخراج وتنظيف وتوازن بيانات التدريب من سجل الخبرات
- محاكاة تدريب LoRA (PEFT) مع مقاييس حتمية
- تسجيل النماذج مع Model Cards
- تتبع حالة النماذج (registered → trained → evaluated → promoted)

## APIs
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/datasets` | إنشاء مجموعة بيانات من الخبرات |
| GET | `/v1/datasets` | عرض مجموعات البيانات |
| GET | `/v1/datasets/{id}` | استرجاع مجموعة بيانات |
| POST | `/v1/models/train` | تدريب LoRA (محاكاة) |
| GET | `/v1/models` | عرض النماذج |
| GET | `/v1/models/{id}` | استرجاع نموذج |
| PATCH | `/v1/models/{id}/status` | تحديث حالة نموذج |
| GET | `/v1/models/{id}/card` | استرجاع Model Card |

## المنفذ
8010

## تاريخ آخر تعديل
2026-08-15

## المحتويات
- `README.md` — بطاقة هوية هذا المجلد (المادة التاسعة)
- `data_pipeline.py` — AMOS-Federation Data Collection Pipeline
- `main.py` — AMOS-Federation Training Service
- `model_registry.py` — AMOS-Federation Model Registry
