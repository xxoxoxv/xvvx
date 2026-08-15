# نضج CI والاختبارات — CI & Test Maturity

> **المجال:** docs/maturity
> **المرحلة:** P9 — النضج والفصل المستقبلي
> **الحالة:** معيار (Criteria)
> **تاريخ الإنشاء:** 2026-08-15
> **المرجع:** `.github/workflows`

---

## 1. الهدف
تعريف مستويات نضج التكامل المستمر (CI) والاختبارات، كشرط مسبق للاستخراج والفصل المستقبلي.

## 2. مستويات النضج
| المستوى | الوصف | الحالة الحالية |
|---|---|---|
| L1 — اختبارات دخان | تحقق نصي لكل مجال | ✓ 12/12 (P3 + استكمال) |
| L2 — اختبارات وحدة | اختبارات دوال الوكلاء/الأدوات | TODO |
| L3 — اختبارات تكامل | اختبار الحلقة الكاملة (P5) | مواصفة ✓، تنفيذ TODO |
| L4 — CI تلقائي | تشغيل تلقائي على كل push | ✓ وظيفة smoke في `.github/workflows/ci.yml` (P9) |
| L5 — تغطية ≥ 80% | تقارير تغطية | ✓ 87.8% خط + بوابة fail_under=80 (P9) |

## 3. خط أنابيب CI المقترح
```mermaid
graph LR
    P[Push] --> L[Linter] --> S[Smoke Tests] --> U[Unit Tests]
    U --> I[Integration Tests] --> C[Coverage Report]
    C -->|≥80%| M[Merge to main]
    C -->|<80%| F[Fail]
```

## 4. اختبارات الدخان الحالية
موجودة في `tests/smoke/run_smoke_tests.py` — تغطي 11 مجالاً (واجهات+سياسات الولايات متوقعة فارغة في P3).

## 5. خارطة طريق النضج
1. **P9** — إضافة اختبارات وحدة (L2) لكل stub.
2. **P9** — تنفيذ اختبار تكامل الحلقة (L3) وفق `runtime/scenarios/single_task_execution.md`.
3. **P9 ✓** — وظيفة CI لتشغيل اختبارات الدخان تلقائيًا (L4).
4. **P9 ✓** — رفع التغطية إلى ≥80% مع بوابة `fail_under=80` في `pyproject.toml` (L5).
5. **مستقبلي** — رفع تغطية الأفرع (branch) فوق 80%.

## 6. اختبار القبول
```bash
test -f docs/maturity/ci_maturity.md && grep -q "L5" docs/maturity/ci_maturity.md \
  && echo "ci_maturity: OK" || echo "ci_maturity: FAIL"
```

## 7. بوابة التغطية (L5)
أُضيف إعداد `[tool.coverage]` إلى `federal/executive/services/pyproject.toml`:

- `source = ["amos_federation"]` — قياس تغطية الحزمة فقط.
- `branch = true` — تفعيل تغطية الأفرع.
- `fail_under = 80` — فشل CI إن هبطت التغطية عن 80%.
- `omit` — استبعاد نقاط الدخول `*/services/*/main.py` و `__main__.py`.

### النتائج الحالية (P9)
| المؤشر | القيمة |
|---|---|
| اختبارات ناجحة | 591 passed / 8 skipped |
| تغطية الأسطر | 87.8% |
| بوابة fail_under=80 | PASS |
| وظيفة CI | `coverage` في `.github/workflows/ci.yml` |

### تشغيل التغطية محليًا
```bash
cd federal/executive/services
pip install -e ".[dev]"
pytest tests/ --cov --cov-report=term-missing
```
