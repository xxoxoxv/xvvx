# بروتوكول المفتاح الكهربائي — Kill Switch Protocol

> **المجال:** royal/security
> **المرحلة:** P8 — الحوكمة والأمن والمراقبة
> **الحالة:** بروتوكول (Protocol)
> **تاريخ الإنشاء:** 2026-08-15
> **الجداول:** `audit_entries` · `event_store`

---

## 1. الهدف
تعريف المفتاح الكهربائي (kill-switch) الذي يوقف كل عمليات الدولة فورًا عند الطوارئ القصوى، مع ضمان قابلية الإقلاع من جديد بأمان.

## 2. متى يُفعّل
- خطر أمني جسيم (اختراق واسع).
- فقدان تحكم في الوكلاء.
- أمر ملكي مباشر من المالك.

## 3. إجراء الإيقاف
1. **إيقاف المهام النشطة** — كل `in_progress` ← `pending` (مع تعليق).
2. **تعليق الوكلاء** — إيقاف استدعاء الأدوات.
3. **تجميد الخزانة** — منع المعاملات.
4. **حفظ الحالة** — كتابة حدث `amos_federation.royal.kill_switch_activated`.
5. **وضع الصيانة** — فقط owner يمكنه التشغيل.

## 4. إجراء الإقلاع (Recovery)
1. مراجعة أسباب التفعيل.
2. فحص السلامة (states/health لكل الوكلاء).
3. إعادة التفعيل التدريجي (مجال بمجال).
4. حدث `amos_federation.royal.kill_switch_deactivated`.

## 5. ضمانات
- التفعيل حصري للمالك (owner).
- لا يمكن تجاوزه آليًا؛ يتطلب مصادقة بشرية.
- كل تفعيل/إقلاع مُسجَّل في `audit_entries` و`event_store`.

## 6. اختبار القبول
```bash
test -f royal/security/kill-switch/protocol.md && grep -q "kill_switch" royal/security/kill-switch/protocol.md \
  && echo "kill_switch_protocol: OK" || echo "kill_switch_protocol: FAIL"
```
