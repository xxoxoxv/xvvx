# Training Service

خدمة تدريب LoRA + Model Registry + Data Pipeline ضمن AMOS-Federation.

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
