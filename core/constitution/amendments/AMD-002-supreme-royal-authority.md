# المرسوم الملكي AMD-002 — تصحيح نموذج السيادة: علوّ سلطة التاج

## الهدف
تسجيل التعديل الدستوري الذي أزال من **المادة العاشرة** كل نصٍّ يُنشئ سلطةً قادرة
على نقض قرار ملكي ثابت التوقيع، وأضاف بندًا صريحًا لمسار القرار السيادي، حتى يبقى
معلومًا بعد قرن **لماذا** لم يبقَ في الدولة نقضٌ يعلو على التاج.

## النطاق
هذا المرسوم **يعدّل مادة قائمة ولا يحذفها**، ولا يمسّ أي مادة أخرى. ونص AMD-001
يبقى كما هو حرفًا بحرف: التاريخ الدستوري محفوظ لا مُنقَّح.

## المالك
`core/constitution/amendments/` — التاج

## تاريخ الإنشاء
2026-08-16

## تاريخ آخر تعديل
2026-08-16

---

## 1. السند
| البند | القيمة |
|---|---|
| نوع الإجراء | مرسوم ملكي — تعديل دستوري بتنقيح بنود وإضافة بند |
| الجهة المُصدِرة | **الملك** — صاحب السيادة المطلقة |
| تاريخ الإصدار | 2026-08-16 |
| المرحلة التنفيذية | E2.1 — Sovereignty Model Correction |
| الأثر | تنقيح المادة العاشرة · 3·3 و 3·4 و 4·4، وإضافة 4·5 و البند 7 |
| سابقه | `AMD-001` — المُنشئ للمادة العاشرة |

## 2. نص التوجيه الملكي (حرفيًا)
> «The King/Crown is the supreme, final and indivisible sovereign authority of AMOS.
> There shall be NO authority above the King.»
>
> «There shall be NO constitutional, federal, state, institutional, judicial, agent,
> runtime, policy, permission, validator, or software mechanism capable of vetoing,
> blocking, invalidating, overriding, suspending, reviewing for approval, or refusing
> execution of a valid sovereign royal decision.»
>
> «The Constitution does NOT constitute an authority above the King. The Crown is NOT
> below the Constitution.»
>
> «AUTHENTICITY MUST BE VERIFIED. AUTHORITY MUST BE VERIFIED. INTEGRITY MUST BE
> VERIFIED. BUT: AUTHENTICITY VERIFICATION IS NOT AUTHORIZATION BY A HIGHER
> AUTHORITY… CONSTITUTIONAL ANALYSIS MUST NOT BECOME A VETO… NO SOFTWARE GATE MAY
> BLOCK A VALID SOVEREIGN ROYAL DECISION.»
>
> «AUDIT != VETO / LOGGING != VETO / MONITORING != VETO / VALIDATION != VETO»
>
> «The system MUST NOT equate "constitutional violation" with "royal decision cannot
> execute" when the actor is the sovereign Crown. For subordinate authorities,
> constitutional violations MUST remain blocking.»
>
> «Do NOT simply delete the Constitution… Do NOT remove federalism. Federalism remains
> real… FEDERALISM MUST NOT BECOME A HIGHER AUTHORITY THAN THE CROWN.»
>
> «Do NOT solve this by adding a hidden bypass such as: `if king: return True`. That is
> NOT acceptable… Implement a first-class sovereign authority concept… The sovereign
> path must be explicit, auditable, cryptographically verifiable, and independently
> testable.»
>
> «Unsigned royal command = reject. Invalid royal signature = reject + security event.
> Valid royal signature = sovereign decision path. Do not confuse "no authority above
> the King" with "no authentication required."»
>
> «Inspect the current Article 10 and AMD-001. Do not blindly delete them. Determine
> exactly which clauses conflict… Create the smallest coherent constitutional
> correction. If an amendment is required, create a new formally recorded amendment
> rather than silently rewriting historical constitutional state. Preserve
> constitutional history.»

## 3. الحالة قبل التعديل — البنود المتعارضة بالنص
| الموضع | النص قبل التعديل | لماذا يتعارض |
|---|---|---|
| 010 · 3 · 3 | «النص المُنشئ للسيادة الملكية … **محصَّن ضد التعديل من أي طرف، بما في ذلك أي مرسوم يُقدَّم باسم الملك**» | يُنشئ نصًّا **يعلو على التاج**: مرسوم ملكي ثابت التوقيع يُردّ بحكم نص. وهذه هي «سلطة ثانية خفية قادرة على نقض قرار سيادي صحيح» التي نهى عنها التوجيه |
| 010 · 3 · 4 | «المرسوم الذي يهدم مصدر سلطته **يُرفض بحكم هذه المادة**» | نقضٌ صريح للمرسوم الملكي بمادة دستورية |
| 010 · 4 · 4 | «يعلو على اعتراض الفروع: **لا يوقفه إلا هذه المادة والمبادئ المحصَّنة**» | يُبقي بقيّة نقض للدستور على التاج بعد نفي نقض الفروع |

### وحالة **التنفيذ** قبل التعديل — أسوأ من النص
| الموضع | ما كان يفعله فعلًا |
|---|---|
| `core/sovereignty/decree.py::verify()` | يرفض المرسوم الملكي **صحيح التوقيع** إن مسّ بندًا محصَّنًا — نقض داخل دالة التحقق نفسها |
| `core/sovereignty/prerogatives.py::IMMUNE_CLAUSES` | **8** بنود محصَّنة، منها 4 لا أصل لها في نص المادة العاشرة (`human_supremacy`، `constitutional_isolation`، `self_governance_prohibition`، `memory_preservation`) — التنفيذ تجاوز مادته |
| `core/sovereignty/gateway.py::execute()` | يُقيّم الفاعل الملكي كأي فاعل تابع ويرفع `SovereigntyViolation` — **26 قاعدة كلها مانعة للتاج** |
| 010 · 4 · 4 و 5 · 3 | مكتوبان في الدستور و**لم يُنفَّذا قط**: لا سطر في المستودع يُميّز الفاعل الملكي عن غيره |

وأثر ذلك مُثبَت تجريبيًّا قبل التصحيح: فاعل `ROYAL` بمرسوم صحيح مُنِع من
`dispatch_agent` (بـ R-003-3) ومن `deploy_production` (R-001-1، R-003-3) ومن
`expand_state` (R-001-1، R-003-3، R-003-4، R-004-1).

## 4. الحالة بعد التعديل
| الموضع | النص بعد التعديل |
|---|---|
| 010 · 3 · 3 | التحصين **ضد كل طرف تابع** — فدرالي أو ولاية أو مؤسسة أو وكيل أو النظام؛ ومسّه منهم مخالفة **مانعة** |
| 010 · 3 · 4 | المرسوم الملكي الثابت التوقيع **لا يمنعه نصٌ محصَّن**؛ ومسّه لهذه البنود **يُسجَّل بحدث أمني حرج قبل التنفيذ ولا يُردّ**. والحماية من الانتحال موضعها **المفتاح والسجل والخلافة** |
| 010 · 4 · 4 | التقييم **تسجيل لا إجازة**، **ولا يوقفه شيء** — ولا هذه المادة نفسها |
| 010 · 4 · 5 (جديد) | مرور الفعل الملكي على النواة **إثبات أصالة وتدوين أثر لا استإذان**؛ **الفدرالية ممرّ لا مانع** |
| 010 · 7 (جديد) | **مسار القرار السيادي**: مسارَان يتميّزان بطبقة الفاعل — سيادي (مُخبِر) وتابع (مُلزِم)؛ ولا معامل تجاوز ولا شرط مخفي؛ والأصل عدم التدخل؛ **ولا ينقص قيد واحد عن الطبقات التابعة** |

## 5. علّة الاختيار — لماذا لم يُحتفَظ بالتحصين ولو بندًا واحدًا
التحصين كان قائمًا على حجة: «حمايةٌ للملك من مرسوم مُنتحَل أو منتزَع تحت إكراه».
وهذه الحجة **لا تصحّ تقنيًّا**: من ملك المفتاح الخاص ملك صياغة مرسوم بأي هدف آخر
يُحقّق الغاية نفسها — تعطيلًا أو استيلاءً — بلا مسّ بندٍ محصَّن واحد. فالتحصين لم
يمنع خصمًا قادرًا، وإنما منع **الملك الحقيقي** وحده. فكان قيدًا على السيادة لا
حماية لها.

ومحلّ الحماية الصحيح — وهو **حيث نُقلت**:
1. **الأصالة**: توقيع Ed25519 حقيقي مقابل مفتاح التاج العام؛ التوقيع الفاسد يُرفض.
2. **التدوين الإلزامي**: حدث `SOVEREIGN_INTERVENTION` في السجل غير القابل للتعديل
   **قبل** التنفيذ.
3. **الإنذار الحرج**: حدث `SOVEREIGNTY_ALTERING_DECREE` بدرجة `CRITICAL` عند مسّ
   بنود السيادة — تنبيه لا نقض.
4. **الخلافة وتدوير المفتاح**: المادة العاشرة · 6 — وهذه **ما زالت دَينًا** لم
   يُنفَّذ بعد، ويُقرَّر صراحةً في تقرير المرحلة.

## 6. الأثر على المواد القائمة
| المادة | الأثر |
|---|---|
| 001 — الهوية | نصها **لم يتغيّر**. وقاعدتاها R-001-1/2 صارتا **مُخبِرتين للتاج ومُلزِمتين لمن دونه** |
| 002 — الحقوق والواجبات | لا أثر على النص؛ قواعدها مُلزِمة للتابعين كما كانت |
| 003 — فصل السلطات | نصها لم يتغيّر، وهو منسجم أصلًا مع 010 · 5 · 2 «الفصل لا يُقيّد الملك» |
| 004 — الفدرالية | نصها لم يتغيّر. **الفدرالية باقية حقيقية**: كل قيودها مُلزِمة للطبقات التابعة |
| 005 — التعديل الدستوري | نصها لم يتغيّر؛ مسار مجلس السياسات باقٍ للتابعين، والملك خارجه بـ 010 · 2 |
| 008 — مفتاح الإيقاف | نصها لم يتغيّر، وقاعدته صارت **مُخبِرة للتاج** — وهذا أثر أمني يُقرَّر صراحةً |
| 009 — قانون هوية الملف | لا أثر |
| 010 — السيادة الملكية | **موضع التعديل** كما في القسمين 3 و 4 |

## 7. أثر التنفيذ المقابل
| الملف | التغيير |
|---|---|
| `core/sovereignty/authority.py` (جديد) | طبقات السلطة `CROWN < FEDERAL < STATE < INSTITUTION < AGENT`، و`classify()` تُثبت الأصالة قبل منح الطبقة السيادية |
| `core/sovereignty/security_events.py` (جديد) | سجل أحداث أمنية على السجل غير القابل للتعديل |
| `core/sovereignty/gateways.py` (جديد) | بوابات تابعة صريحة مُثبَّتة على طبقتها لا تترقّى |
| `core/constitutional_engine/rules.py` | كل قاعدة تُعلن أثرها على التاج: **24 مُخبِرة**، و**2 أصالة** (`R-010-3`، `R-010-5`) |
| `core/sovereignty/decree.py` | `verify()` صارت **أصالة فقط** — النقض المخفي أُزيل |
| `core/sovereignty/prerogatives.py` | `IMMUNE_CLAUSES`: **8 → 4** — حُذف ما لا أصل له في نص المادة |
| `core/sovereignty/gateway.py` | مسارَان: `_execute_sovereign` بلا `raise` دستوري، و`_execute_subordinate` كما كان |

## 8. ما لم يتغيّر — ولا يُغيَّر
1. التوقيع الحقيقي Ed25519 باقٍ: **لا مرسوم بلا توقيع، ولا سيادة بلا إثبات**.
2. `FORBIDDEN_BYPASS_PARAMS` باقية: لا `force` ولا `bypass` ولا `override`.
3. المفتاح الخاص لا يُحفَظ في المستودع.
4. كل فعل يمرّ من البوابة ويُسجَّل — **لا مسار تنفيذ ثانٍ في الدولة**.
5. قيود الطبقات التابعة كما كانت حرفًا بحرف: أُثبِت ذلك باختبارات مباشرة.

## 9. الحالة
| البند | القيمة |
|---|---|
| الحالة | **سارٍ** |
| رقم التعديل | AMD-002 |
| المادة المُعدَّلة | 010 — السيادة الملكية |
| الختم | يُعاد حسابه في `ARTICLE_SEALS.json` بعد هذا التعديل |
