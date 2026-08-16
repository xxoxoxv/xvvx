# docs/security — التوثيق الأمني

## التعريف
هذا المجلد يوصف **الأمن كما هو منفَّذ**، لا كما نتمناه. وقاعدته الملزمة: كل ادّعاء
معماري هنا يقابله رمز قابل للتشغيل ومرجع اختبار، وكل ما لا يقابله شيء يُقال فيه
صريحًا إنه غير منفَّذ. فالوثيقة التي تبالغ في الأمن أخطر من غيابها، لأنها تُقنع
مالكها أنه محميّ فلا يبني الحماية.

## النطاق
**يدخل:** معمار حماية التاج، ونموذج التهديد، وحدّ البشر والبرمجية، وخارطة الأمن
المستقبلي.
**لا يدخل:** الدستور (`core/constitution/`)، ولا مبدأ العمل (`docs/governance/`)،
ولا مصفوفة الحقيقة (`docs/audit/`)، ولا الإجراءات الأمنية التنفيذية للأشخاص
والعتاد.

## المالك
التاج

## تاريخ الإنشاء
2026-08-16

## تاريخ آخر تعديل
2026-08-16

## المحتويات

| الملف | الدور |
|---|---|
| [`CROWN_SOVEREIGNTY_PROTECTION.md`](CROWN_SOVEREIGNTY_PROTECTION.md) | المعمار المرجعي: الهويات، والمرساة، والمفتاح، والدورة، والخلافة، والاسترداد، والأمر، والسجل، والاستمرارية، والحارس، والاحتواء |
| [`CROWN_THREAT_MODEL.md`](CROWN_THREAT_MODEL.md) | 38 تهديدًا بحال معالجتها ومسؤولها — **مولَّد** من `core/crown/threats.py` |
| [`HUMAN_SOFTWARE_BOUNDARY.md`](HUMAN_SOFTWARE_BOUNDARY.md) | ما تُثبته البرمجية وما لا تُثبته، وما تفعله عند حدّها |
| [`SECRET_BOUNDARIES.md`](SECRET_BOUNDARIES.md) | أين يسكن كل سرّ، وما يُنشر عمدًا، وبوابة منع عودة السرّ إلى الكود |
| [`CROWN_SECURITY_ROADMAP.md`](CROWN_SECURITY_ROADMAP.md) | قدرات مستقبلية غير منفَّذة: بعد الكمّي، والإشهاد، والجيوب، والهوية |

## القاعدة الذهبية

> **حماية الملك ليست سلطةً على الملك.**

## التحقق بالأمر

```bash
python -m core.crown.cli crown-check           # بوابة الحدود المطلقة (9 فحوص)
python -m core.crown.cli boundary              # حدّ البرمجية بالأرقام
python -m core.crown.cli threat-matrix         # مصفوفة التهديدات
python -m core.crown.cli substitution-matrix   # متجهات استبدال المرساة
python tools/governance/generate_crown_threat_doc.py --check
python -m pytest tests/crown/ -q --cov=core.crown --cov-branch
```

## المراجع
- التنفيذ: [`core/crown/`](../../core/crown/README.md)
- الاختبارات: [`tests/crown/`](../../tests/crown/README.md)
- نواة السيادة (E2.1، غير مُمَسّة): [`core/sovereignty/`](../../core/sovereignty/README.md)
