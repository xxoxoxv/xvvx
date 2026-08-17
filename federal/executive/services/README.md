# federal/executive/services/ — الخدمات التنفيذية

## التعريف
الخدمات التقنية الفعلية للسلطة التنفيذية. هنا تقيم api-gateway, orchestrator-service, agent-runtime-service. كل خدمة لها Dockerfile ومواصفاتها الخاصة.

## النطاق
FastAPI services, Dockerfiles, configuration files, health checks.

## المالك
Federal Council

## تاريخ الإنشاء
2026-08-15

## بصمة الهوية
يخضع هذا المجلد لقانون هوية الملفات (المادة الدستورية 009).
كل ملف داخله يجب أن يحتوي على ترويسة تعريفية.

## الخدمات المنفّذة

| الخدمة | المنفذ | الحالة |
|---|---:|---|
| api-gateway | 8000 | استقبال المهام، JWT، وسجل الوكلاء والأدوات |
| orchestrator | 8001 | تخطيط حتمي للمهام |
| agent-runtime | 8002 | هيكل تشغيلي؛ التنفيذ في الأسبوعين 7-8 |
| tool-registry | 8003 | هيكل تشغيلي؛ التنفيذ في الأسبوعين 7-8 |
| model-gateway | 8004 | هيكل تشغيلي؛ التنفيذ في الأسبوعين 9-10 |
| memory-service | 8005 | هيكل تشغيلي؛ التنفيذ في الأسابيع 11-13 |
| evaluation | 8006 | هيكل تشغيلي؛ التنفيذ في الأسبوعين 9-10 |
| critic | 8007 | هيكل تشغيلي؛ التنفيذ في الأسبوعين 9-10 |
| governance | 8009 | هيكل تشغيلي؛ التنفيذ في الأسابيع 11-13 |

## التشغيل

```bash
cp .env.example .env
make up
make run SERVICE=api-gateway PORT=8000
python -m pytest tests/ -q
```

كل خدمة تعرض `GET /health` و`GET /ready`. تحمي بوابة API مسارات `/v1` برمز JWT Bearer موقع بمفتاح `AMOS_JWT_SECRET`.

## تاريخ آخر تعديل
2026-08-17

## المحتويات
- `.dockerignore` — استبعاد الملفات غير اللازمة من سياق البناء
- `.env.example` — قالب للإعدادات البيئية
- `.pre-commit-config.yaml` — فحص الكود قبل كل commit
- `Dockerfile` — بناء صورة موحدة قابلة لتشغيل أي خدمة FastAPI
- `Makefile` — أوامر التطوير الشائعة
- `README.md` — بطاقة هوية هذا المجلد (المادة التاسعة)
- `docker-compose.yml` — تشغيل كل خدمات النظام محليًا للتطوير
- `pyproject.toml` — إعداد مشروع Python للخدمات
- `requirements.lock` — ملف تابع
- `.github/` — مجلد فرعي (1 عنصرًا) — انظر بطاقته
- `docs/` — مجلد فرعي (1 عنصرًا) — انظر بطاقته
- `migrations/` — مجلد فرعي (3 عنصرًا) — انظر بطاقته
- `src/` — مجلد فرعي (1 عنصرًا) — انظر بطاقته
- `tests/` — مجلد فرعي (49 عنصرًا) — انظر بطاقته
