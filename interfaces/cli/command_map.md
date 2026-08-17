# خريطة أوامر CLI — Command Map

> **المجال:** interfaces/cli
> **المرحلة:** P7 — الواجهات
> **الحالة:** مواصفة واجهة (CLI Spec)
> **تاريخ الإنشاء:** 2026-08-15
> **المواءمة:** عقد API في `interfaces/api/contract.md`

---

## 1. الهدف
تعريف واجهة سطر أوامر (CLI) للمالك والمشغّلين للتحكم في الدولة: إنشاء المهام، تفعيل الوكلاء، وتدقيق التدفقات.

## 2. بنية الأمر
```
amos <domain> <action> [flags]
```
الأمثلة: `amos task create`, `amos agent list`, `amos audit trail`.

## 3. خريطة الأوامر

### runtime — المهام والأحداث
| الأمر | الوصف | مقابل API |
|---|---|---|
| `amos task create --type=... --desc=...` | إنشاء مهمة | `POST /api/v1/tasks` |
| `amos task status <id>` | حالة المهمة | `GET /api/v1/tasks/{id}` |
| `amos task transition <id> --to=...` | انتقال حالة | `PATCH /api/v1/tasks/{id}/status` |
| `amos task events <id>` | سلسلة الأحداث | `GET /api/v1/tasks/{id}/events` |

### agents — الوكلاء
| الأمر | الوصف |
|---|---|
| `amos agent list [--domain=]` | قائمة الوكلاء |
| `amos agent assign <agentId> <taskId>` | إسناد مهمة |

### tools — الأدوات
| الأمر | الوصف |
|---|---|
| `amos tools list` | سجل الأدوات |
| `amos tools exec <id> --input=...` | تنفيذ أداة |

### royal — التدقيق
| الأمر | الوصف |
|---|---|
| `amos audit trail <taskId>` | مسار تدقيق المهمة |
| `amos audit flagged` | التدقيقات المعلّمة |

### core — الذاكرة
| الأمر | الوصف |
|---|---|
| `amos memory recall --domain=...` | استرجاع الذكريات |

### ops — العمليات
| الأمر | الوصف |
|---|---|
| `amos ops health` | فحوصات الوكلاء |
| `amos ops report` | تقرير حالة الدولة |

## 4. الأعلام المشتركة (Global Flags)
| العلم | الوصف |
|---|---|
| `--tenant=` | معرّف المستأجر |
| `--json` | خرج JSON خام |
| `--quiet` | خرج صامت (exit code فقط) |

## 5. اختبار القبول
```bash
test -f interfaces/cli/command_map.md && grep -q "amos task create" interfaces/cli/command_map.md \
  && echo "cli_map: OK" || echo "cli_map: FAIL"
```
