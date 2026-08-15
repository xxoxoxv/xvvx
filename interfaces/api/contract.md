# عقد API — Interfaces API Contract

> **المجال:** interfaces/api
> **المرحلة:** P7 — الواجهات
> **الحالة:** مواصفة عقد (API Contract)
> **تاريخ الإنشاء:** 2026-08-15
> **المواءمة:** `interface_registry` Supabase + `docs/contracts/schemas/interface.schema.json`

---

## 1. الهدف
تعريف عقد API كامل لنقاط دخول الدولة البرمجية، بحيث يستطيع الوكلاء والأدوات الخارجية التفاعل مع المحرك عبر REST.

## 2. القواعد العامة
- **النمط:** REST + JSON.
- **الإصدار:** `/api/v1/...`.
- **المصادقة:** Bearer token (من `interface_registry`).
- **عزل المستأجرين:** تمرير `X-Tenant-Id` في كل طلب.
- **الترقية:** التزام توافقي الإصدارات (لا كسر متوافق عكسيًا).

## 3. نقاط النهاية (Endpoints)

### المهام (Tasks)
| الطريقة | المسار | الوصف |
|---|---|---|
| `POST` | `/api/v1/tasks` | إنشاء مهمة (`task.created`) |
| `GET` | `/api/v1/tasks/{id}` | استرجاع مهمة وحالتها |
| `PATCH` | `/api/v1/tasks/{id}/status` | تحديث حالة المهمة (انتقال) |
| `GET` | `/api/v1/tasks/{id}/events` | سلسلة أحداث المهمة (correlation_id) |

### الوكلاء (Agents)
| الطريقة | المسار | الوصف |
|---|---|---|
| `GET` | `/api/v1/agents` | قائمة الوكلاء (من `agent_population`) |
| `POST` | `/api/v1/agents/{id}/assign/{taskId}` | إسناد مهمة |

### الأدوات (Tools)
| الطريقة | المسار | الوصف |
|---|---|---|
| `GET` | `/api/v1/tools` | سجل الأدوات |
| `POST` | `/api/v1/tools/{id}/execute` | تنفيذ أداة (`tool.executed`) |

### التدقيق والذاكرة
| الطريقة | المسار | الوصف |
|---|---|---|
| `GET` | `/api/v1/audit/{taskId}` | مسار تدقيق المهمة |
| `GET` | `/api/v1/memory?domain=` | استرجاع الذكريات حسب المجال |

## 4. بنية الرد الموحّدة
```json
{
  "ok": true,
  "data": { },
  "correlation_id": "task-...",
  "timestamp": "2026-08-15T16:00:00Z"
}
```
الأخطاء: `{ "ok": false, "error": { "code": "...", "message": "..." } }`.

## 5. حدود المعدل (Rate Limits)
| الدور | الحد |
|---|---|
| وكيل | 100 طلب/دقيقة |
| أداة | 60 طلب/دقيقة |
| مالك (owner) | غير محدود |

## 6. اختبار القبول
```bash
test -f interfaces/api/contract.md && grep -q "/api/v1/tasks" interfaces/api/contract.md \
  && echo "api_contract: OK" || echo "api_contract: FAIL"
```
