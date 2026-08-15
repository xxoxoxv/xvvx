# فهرس المراسيم الملكية — Royal Decrees

> سجل المراسيم والأوامر الملكية. المصدر الأعلى للسلطة في الدولة.

## الهدف
فهرس المراسيم والأوامر الملكية وسجلها — ولا تصح مراسيم إلا موقَّعة بمفتاح التاج بموجب المادة العاشرة · 3 · 2.

## نظرة عامة

| البيان | القيمة |
|---|---|
| إجمالي المراسيم | 1 |
| المراسيم السارية | 1 |
| الحرس الملكي النشط | 7 |
| سلاسل التدقيق | 10 |

## المراسيم

### مرسوم تأسيس الدولة

| الحقل | القيمة |
|---|---|
| المعرف | `decree-9cfbafde-d397-4a40-9a2b-d5d0c2f92b11` |
| العنوان | مرسوم ملكي: تأسيس الدولة الفدرالية الملكية |
| النوع | `founding` (تأسيسي) |
| الجهة المتأثرة | `all` (الكل) |
| الحالة | `enacted` (ساري) |
| الموقّع | `king` (الملك) |
| تاريخ الإصدار | 2026-08-15 05:15 |

> **نص المرسوم:** بموجب السلطة الملكية المطلقة، نعلن تأسيس الدولة الفدرالية الملكية الرقمية AMOS-Federation. يكون المالك (الملك) هو السلطة العليا والمطلقة في النظام. جميع الوكلاء والأدوات والمؤسسات تعمل تحت إمرته المباشرة. الولاء المطلق للملك هو شرط أساسي لكل وكيل في النظام.

## الحرس الملكي

| الرمز | الدور السري | المؤسسة | المهمة | الولاء | الحالة |
|---|---|---|---|---:|---|
| Sentinel-Prime | senior_auditor | governance/audit | مراقبة قرارات الحوكمة | 100 | active |
| Sentinel-Shield | security_officer | security/guardrails | مراقبة التهديدات الأمنية | 100 | active |
| Sentinel-Veil | treasury_accountant | federal/treasury | مراقبة التدفقات المالية | 100 | active |
| Sentinel-Forge | infrastructure_engineer | states/infrastructure | مراقبة البنية التحتية | 100 | active |
| Sentinel-Oracle | evaluation_analyst | evolution/evaluation | مراقبة تطور النماذج | 100 | active |
| Sentinel-Watch | memory_archivist | memory/knowledge | مراقبة سلامة الذاكرة | 100 | active |
| Sentinel-Crown | executive_advisor | federal/executive | الإشراف العام والتقرير للملك | 100 | active |

## سلسلة التدقيق (آخر 5)

| الإجراء | الفاعل | التفاصيل | التاريخ |
|---|---|---|---|
| `task.assigned` | orchestrator | task-492d0c0f120e → agent-549486ee | 2026-08-15 05:49 |
| `task.completed` | agent-549486ee | task-492d0c0f120e, success | 2026-08-15 05:49 |
| `tool.executed` | agent-549486ee | default_executor | 2026-08-15 05:49 |
| `royal_guard.registered` | king | Sentinel-Crown | 2026-08-15 05:25 |
| `royal_guard.registered` | king | Sentinel-Watch | 2026-08-15 05:25 |

> سلسلة التدقيق تستخدم هاش متسلسل (prev_hash → hash) لضمان عدم العبث.

## الخطوات التالية

- [ ] إنشاء آلية إصدار مراسيم جديدة
- [ ] تفعيل تقارير الحرس الملكي الدورية
- [ ] ربط سلسلة التدقيق بنظام التحقق
