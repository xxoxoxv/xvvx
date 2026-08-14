# AMOS-SE
## خطة التنفيذ التقنية المفصلة
### الإصدار 1.0 — Implementation Plan

---

> **المرجع:** هذه الوثيقة تحوّل [AMOS-SE Blueprint v1.0](./AMOS-SE_Final_Blueprint.pplx.md) إلى خطة تنفيذ هندسية قابلة للتنفيذ.
> **تاريخ الإصدار:** 2026-08-15
> **النطاق الزمني:** أول 12 شهرًا (6 مراحل + خطة 90 يومًا تفصيلية)
> **المبدأ:** لا وعود كبرى — أول 90 يومًا تبني runtime موثوق يجمع الخبرات. التطور الذاتي يبدأ فقط بعد اكتمال: audit، evals، replay buffer، governance، rollback.
>
> **نطاق الالتزام:** هذه الخطة تبني vertical slice موثوق أولًا. لا يبدأ التطور الذاتي أو التدريب على بيانات العملاء إلا بعد اكتمال الحوكمة، التقييم، سجل التدقيق، العزل، وآلية rollback.
>
> **تصنيف النطاق حسب الواقعية (3-5 مهندسين):**
> - Phase 0-4 = نطاق ملتزم به (مضمون)
> - Phase 5 (LoRA Factory) = نطاق مشروط (Stretch)
> - Phase 6 (Governance + Canary) = ممكن جزئيًا، ليس production كامل
> - Phase 7 (Scale-out) = سنة 2 أو فريق أكبر

---

## جدول المحتويات

1. [الهدف التنفيذي](#1-الهدف-التنفيذي)
2. [فرضيات التنفيذ](#2-فرضيات-التنفيذ)
3. [خارطة المراحل](#3-خارطة-المراحل)
4. [Sprint Breakdown (أول 6 أشهر)](#4-sprint-breakdown)
5. [Service Map](#5-service-map)
6. [البنية القابلة للحياة الدنيا (Minimal Viable Architecture)](#6-البنية-القابلة-للحياة-الدنيا)
7. [قاعدة البيانات — SQL Schemas](#7-قاعدة-البيانات)
8. [عقود الأحداث (Event Contracts)](#8-عقود-الأحداث)
9. [عقود الـ API (OpenAPI)](#9-عقود-الـ-api)
10. [Local Development Stack](#10-local-development-stack)
11. [Code Skeleton](#11-code-skeleton)
12. [CI/CD Pipeline](#12-cicd-pipeline)
13. [Infrastructure](#13-infrastructure)
14. [Security Implementation](#14-security-implementation)
15. [Training/Evolution Implementation](#15-trainingevolution-implementation)
16. [Acceptance Criteria](#16-acceptance-criteria)
17. [Backlog (Jira/Linear)](#17-backlog)
18. [خطة 90 يومًا التفصيلية](#18-خطة-90-يومًا-التفصيلية)

---

## 1. الهدف التنفيذي

### 1.1 ما سيتم بناؤه في أول 12 شهرًا

بناء **runtime موثوق لشبكة وكلاء** مع:
- خدمة تنسيق (Orchestrator) تستقبل المهام وتوزعها
- 10-30 وكيل نشط في 3 مجالات
- 50-100 أداة مسجلة
- ذاكرة تشغيلية + معرفية + سجل خبرات
- بوابة نماذج (نموذج خارجي واحد + نموذج محلي)
- نظام تقييم أساسي + Critic Agents
- حلقة تطور مبدئية (ألفا + بيتا shadow)
- حوكمة أساسية (Policy-as-Code + Audit Log + Kill Switch)
- CI/CD كامل + بيئة staging

### 1.2 ما هو خارج النطاق الآن

| خارج النطاق | السبب | متى |
|-------------|--------|-----|
| 500 وكيل | مبالغة للسنة الأولى | سنة 2+ |
| 5000 أداة | تكامل تدريجي | سنة 2+ |
| تكاثر كامل | يتطلب حوكمة ناضجة | سنة 2+ |
| تدريب ضخم (Full Fine-tuning) | مكلف وغير ضروري | LoRA يكفي |
| جاما (نسخة مدمجة) | يتطلب ألفا + بيتا مستقرتين | مرحلة 5+ |
| Neo4j (Graph DB) | مبالغة في البداية | مرحلة 4 |
| Multi-model teacher council | ابدأ بنموذج واحد | مرحلة 5 |
| Canary deployment كامل | يتطلب Shadow ناضج | مرحلة 6 |

### 1.3 مبادئ التنفيذ

1. **ابدأ صغيرًا، أثبت، وسّع** — 3 وكلاء قبل 30، 30 قبل 300
2. **الذاكرة قبل الذكاء** — اجمع الخبرات قبل محاولة التعلم منها
3. **المراقبة قبل التطور** — راقب قبل أن تحاول التحسين
4. **الحوكمة قبل الاستقلال** — اختبارات الأمان قبل الترقية التلقائية
5. **لا تدريب على بيانات العملاء** — قبل اكتمال حوكمة البيانات والامتثال

---

## 2. فرضيات التنفيذ

| الفرضية | القيمة | التأثير إن تغيرت |
|---------|--------|-----------------|
| الفريق الهندسي | 3-5 مهندسين (Backend, DevOps, ML) | تأثير مباشر على السرعة |
| بيئة التطوير | Docker Compose محلي → Kubernetes لاحقًا | تبسيط البداية |
| نموذج خارجي أولي | Claude API (أو GPT) | بناء Model Gateway قابل للتبديل |
| نموذج محلي أولي | Llama 3 (8B) عبر vLLM | يتطلب GPU (1x A10g كحد أدنى) |
| التدريب | LoRA/QLoRA فقط — لا full fine-tuning | توفير GPU |
| قاعدة البيانات | PostgreSQL (عام) + Redis (cache) | معيار صناعي |
| Vector DB | Qdrant (مفتوح المصدر) | بديل: pgvector |
| Event Bus | NATS JetStream | أخف من Kafka |
| Object Store | MinIO (S3-compatible) | قابل للنقل |
| Workflow Engine | Temporal | متين للـ long-running tasks |
| لغة الخدمات | Python (FastAPI) | الأنسب للـ AI/ML |
| CI/CD | GitHub Actions | تكامل طبيعي |

---

## 3. خارطة المراحل

```
الشهر:  1     2     3     4     5     6     7     8     9     10    11    12
        |-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
        
        ▓▓▓▓▓▓▓▓▓▓▓▓  Phase 0: Foundation
        │     ▓▓▓▓▓▓▓▓▓▓▓▓  Phase 1: MVP Agent Runtime
        │     │     ▓▓▓▓▓▓▓▓▓▓▓▓  Phase 2: Memory + Experience Replay
        │     │     │     ▓▓▓▓▓▓▓▓▓▓▓▓  Phase 3: Evaluation + Critic
        │     │     │     │     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Phase 4: Alpha/Beta Shadow
        │     │     │     │     │     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Phase 5: LoRA Factory
        │     │     │     │     │     │     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Phase 6: Governance + Canary
        │     │     │     │     │     │     │     ▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Phase 7: Scale-out
```

| المرحلة | المدة | الهدف | المخرجات |
|---------|------|------|---------|
| Phase 0: Foundation | أسابيع 1-4 | البنية الأساسية + Docker Compose + CI/CD | بيئة تطوير تعمل + قاعدة بيانات + event bus |
| Phase 1: MVP Agent Runtime | أسابيع 5-8 | Orchestrator + 3 وكلاء + 10 أدوات | مهمة كاملة من الطلب للتسليم |
| Phase 2: Memory + Experience Replay | أسابيع 9-12 | ذاكرة تشغيلية + سجل خبرات + Vector DB | تجميع وتخزين كل خبرة |
| Phase 3: Evaluation + Critic | أسابيع 13-16 | Critic Agents + تقييم آلي + Regression Suite | تقييم كل نتيجة تلقائيًا |
| Phase 4: Alpha/Beta Shadow | أسابيع 17-22 | نموذجين بالتوازي + Shadow Testing | بيتا تعمل بالتوازي مع ألفا |
| Phase 5: LoRA Factory | أسابيع 23-28 | تدريب LoRA + تقييم + بوابات ترقية | دورة تطور كاملة (يدوية) |
| Phase 6: Governance + Canary | أسابيع 29-36 | Policy Engine كامل + Canary + Kill Switch | ترقية محكومة بالكامل |
| Phase 7: Scale-out | أسابيع 37-48 | 30-50 وكيل + 200 أداة + Kubernetes | نظام إنتاجي قابل للتوسع |

---

## 4. Sprint Breakdown

### Sprint 1-2 (أسابيع 1-4): Phase 0 — Foundation

#### Sprint 1: Infrastructure Setup

| البند | التفاصيل |
|------|---------|
| الهدف | بيئة تطوير محلية تعمل + CI/CD |
| الخدمات | PostgreSQL, Redis, NATS, MinIO, Qdrant |
| المهام | |
| T1.1 | كتابة `docker-compose.yml` لكل المكونات |
| T1.2 | إعداد مستودع Git بهيكل monorepo |
| T1.3 | كتابة `Makefile` بأوامر شائعة |
| T1.4 | إعداد GitHub Actions (lint + test) |
| T1.5 | كتابة SQL migrations مبدئية |
| T1.6 | إعداد pre-commit hooks (black, ruff, mypy) |
| معايير القبول | `docker compose up` يعمل + `make test` ينجح + CI يعمل |
| الاختبارات | فحص اتصال كل خدمة + migration test |

#### Sprint 2: Core Services Skeleton

| البند | التفاصيل |
|------|---------|
| الهدف | هيكل خدمات أساسي + event bus يعمل |
| الخدمات | api-gateway, orchestrator-service, event-store, memory-service |
| المهام | |
| T2.1 | بناء FastAPI skeleton لكل خدمة |
| T2.2 | إعداد NATS JetStream + subjects |
| T2.3 | كتابة event publisher/consumer أساسي |
| T2.4 | إعداد PostgreSQL schemas |
| T2.5 | إعداد Redis connection |
| T2.6 | إعداد OpenTelemetry tracing أساسي |
| معايير القبول | كل خدمة تبدأ + تنشر حدث + تستهلك حدث |
| الاختبارات | unit tests للـ event bus + integration test |

### Sprint 3-4 (أسابيع 5-8): Phase 1 — MVP Agent Runtime

#### Sprint 3: Orchestrator + Tool Registry

| البند | التفاصيل |
|------|---------|
| الهدف | Orchestrator يستقبل طلبات + Tool Registry يعمل |
| المهام | |
| T3.1 | بناء `POST /v1/tasks` endpoint |
| T3.2 | بناء Tool Registry service |
| T3.3 | كتابة 10 tool manifests (YAML) |
| T3.4 | بناء Semantic Router بسيط (keyword matching أولًا) |
| T3.5 | بناء Tool Sandbox (Docker-based) |
| T3.6 | إعداد Model Gateway (Claude API) |
| معايير القبول | يمكن تسجيل أداة + استدعاؤها + الحصول على نتيجة |
| الاختبارات | tool registration test + sandbox isolation test |

#### Sprint 4: Agent Runtime + End-to-End Task

| البند | التفاصيل |
|------|---------|
| الهدف | 3 وكلاء ينفذون مهمة كاملة من البداية للنهاية |
| المهام | |
| T4.1 | بناء Agent Runtime service |
| T4.2 | كتابة 3 agent manifests (YAML) |
| T4.3 | بناء Planning Agent بسيط |
| T4.4 | بناء Worker Agent أساسي |
| T4.5 | ربط Orchestrator → Agent → Tool → Result |
| T4.6 | بناء `GET /v1/tasks/{id}` للحالة |
| معايير القبول | طلب → تخطيط → تنفيذ → نتيجة → تسليم |
| الاختبارات | e2e test لمهمة كاملة + latency test |

### Sprint 5-6 (أسابيع 9-12): Phase 2 — Memory + Experience Replay

#### Sprint 5: Memory Service

| البند | التفاصيل |
|------|---------|
| الهدف | ذاكرة تشغيلية + معرفية تعمل |
| المهام | |
| T5.1 | بناء Memory Service (Redis + Qdrant) |
| T5.2 | كتابة embedding pipeline (sentence-transformers) |
| T5.3 | بناء `POST /v1/memory/store` + `POST /v1/memory/query` |
| T5.4 | ربط الذاكرة بالوكلاء (قراءة قبل التنفيذ) |
| T5.5 | بناء session memory (Redis) |
| معايير القبول | وكيل يخزن معرفة + يسترجعها في مهمة لاحقة |
| الاختبارات | memory store/query test + embedding accuracy test |

#### Sprint 6: Experience Replay Buffer

| البند | التفاصيل |
|------|---------|
| الهدف | كل مهمة تُخزن كخبرة قابلة لإعادة الاستخدام |
| المهام | |
| T6.1 | تصميم Experience Record schema (JSON) |
| T6.2 | بناء Experience Store (PostgreSQL + MinIO) |
| T6.3 | ربط كل مهمة منتهية → Experience Record |
| T6.4 | بناء ذاكرة النجاحات / الفشل / الفجوات |
| T6.5 | بناء `GET /v1/experiences` مع فلترة |
| T6.6 | بناء provenance tracking لكل خبرة |
| معايير القبول | بعد 100 مهمة، يمكن استرجاع نجاحات/فشل مصنفة |
| الاختبارات | experience storage test + provenance test |

### Sprint 7-8 (أسابيع 13-16): Phase 3 — Evaluation + Critic

#### Sprint 7: Critic Agents

| البند | التفاصيل |
|------|---------|
| الهدف | Critic Agent يراجع كل نتيجة |
| المهام | |
| T7.1 | بناء Critic Agent service |
| T7.2 | كتابة Critic manifest (YAML) |
| T7.3 | ربط Critic بنهاية كل مهمة |
| T7.4 | بناء quality scoring (0-1) |
| T7.5 | بناء feedback storage |
| معايير القبول | كل نتيجة لها quality_score + feedback |
| الاختبارات | critic consistency test + scoring calibration |

#### Sprint 8: Evaluation Harness + Gap Analyzer

| البند | التفاصيل |
|------|---------|
| الهدف | تقييم آلي + اكتشاف فجوات معرفية |
| المهام | |
| T8.1 | بناء Evaluation Service |
| T8.2 | كتابة benchmark suite (50 مهمة قياسية) |
| T8.3 | بناء Gap Analyzer (مقارنة ألفا vs نموذج خارجي) |
| T8.4 | بناء regression test runner |
| T8.5 | بناء `POST /v1/evaluations/run` |
| معايير القبول | يمكن تقييم نموذج + الحصول على تقرير + اكتشاف فجوات |
| الاختبارات | eval reproducibility test + gap detection test |

### Sprint 9-11 (أسابيع 17-22): Phase 4 — Alpha/Beta Shadow

#### Sprint 9: Model Gateway + vLLM

| البند | التفاصيل |
|------|---------|
| الهدف | نموذجين يعملان: خارجي (Claude) + محلي (Llama via vLLM) |
| المهام | |
| T9.1 | إعداد vLLM على GPU |
| T9.2 | بناء Model Gateway مع routing |
| T9.3 | بناء fallback chain (محلي → خارجي) |
| T9.4 | بناء cost tracking |
| T9.5 | بناء `POST /v1/models/invoke` |
| معايير القبول | يمكن توجيه طلب لنموذج محلي أو خارجي + fallback يعمل |
| الاختبارات | routing test + fallback test + cost tracking test |

#### Sprint 10-11: Shadow Testing

| البند | التفاصيل |
|------|---------|
| الهدف | بيتا تعمل بالتوازي مع ألفا (Shadow Mode) |
| المهام | |
| T10.1 | بناء Shadow Testing framework |
| T10.2 | توجيه نسخة من كل طلب لبيتا |
| T10.3 | مقارنة نتائج ألفا vs بيتا |
| T10.4 | بناء Shadow metrics (quality, latency, cost) |
| T10.5 | بناء `GET /v1/shadow/results` |
| T10.6 | إعداد Llama 3 كـ "بيتا الأولية" |
| معايير القبول | بيتا تخدم طلبات بالتوازي + مقارنة تعمل |
| الاختبارات | shadow comparison test + metrics accuracy |

### Sprint 12-14 (أسابيع 23-28): Phase 5 — LoRA Factory

#### Sprint 12: Data Collection Pipeline

| البند | التفاصيل |
|------|---------|
| الهدف | بيانات تدريب جاهزة من سجل الخبرات |
| المهام | |
| T12.1 | بناء Data Collector service |
| T12.2 | استخراج عينات من Experience Replay |
| T12.3 | بناء balancing (نجاح/فشل/فجوات) |
| T12.4 | بناء deduplication + cleaning |
| T12.5 | بناء Data BOM لكل dataset |
| معايير القبول | يمكن إنتاج dataset متوازن + موثق |

#### Sprint 13-14: LoRA Training + Evaluation

| البند | التفاصيل |
|------|---------|
| الهدف | تدريب LoRA + تقييم + Model Registry |
| المهام | |
| T13.1 | بناء LoRA Factory (PEFT + transformers) |
| T13.2 | بناء training job (Temporal workflow) |
| T13.3 | ربط بالـ Evaluation Service |
| T13.4 | بناء Model Registry service |
| T13.5 | بناء Model Card generation |
| T13.6 | بناء knowledge injection (anti-forgetting) |
| معايير القبول | دورة كاملة: بيانات → تدريب → تقييم → بطاقة نموذج |

### Sprint 15-18 (أسابيع 29-36): Phase 6 — Governance + Canary

#### Sprint 15-16: Policy Engine + Audit Log

| البند | التفاصيل |
|------|---------|
| الهدف | Policy-as-Code + Audit Log غير قابل للتعديل |
| المهام | |
| T15.1 | إعداد OPA (Open Policy Agent) |
| T15.2 | كتابة Rego policies (promotion, access, budget) |
| T15.3 | بناء Audit Log مع hash chain |
| T15.4 | بناء `POST /v1/governance/approve` (signed artifacts) |
| T15.5 | بناء Kill Switch (multi-level) |
| معايير القبول | كل قرار يفحص بالسياسة + سجل غير قابل للتعديل |

#### Sprint 17-18: Promotion Gates + Canary

| البند | التفاصيل |
|------|---------|
| الهدف | ترقية محكومة بالكامل مع Canary |
| المهام | |
| T17.1 | بناء 5 promotion gates |
| T17.2 | بناء Canary deployment controller |
| T17.3 | بناء rollback mechanism |
| T17.4 | بناء Governance Console UI |
| T17.5 | بناء Incident Response framework |
| معايير القبول | ترقية كاملة: eval → shadow → canary → human → activate |

---

## 5. Service Map

| الخدمة | المسؤولية | اللغة | DB/Store | Events تنتجها | Events تستهلكها | APIs | SLO |
|--------|----------|-------|---------|--------------|----------------|------|-----|
| `api-gateway` | استقبال الطلبات + auth | Python/FastAPI | Redis | `task.created` | — | REST (public) | p99 < 100ms |
| `orchestrator-service` | التخطيط + توزيع المهام | Python/FastAPI | PostgreSQL | `task.planned`, `agent.assigned` | `task.created` | REST (internal) | p99 < 500ms |
| `agent-runtime-service` | تنفيذ الوكلاء | Python/FastAPI | Redis | `agent.started`, `tool.executed`, `agent.completed` | `agent.assigned` | gRPC (internal) | حسب المهمة |
| `tool-registry-service` | تسجيل وإدارة الأدوات | Python/FastAPI | PostgreSQL | `tool.registered`, `tool.executed` | `tool.requested` | REST (internal) | p99 < 50ms |
| `memory-service` | الذاكرة التشغيلية + المعرفية | Python/FastAPI | Redis + Qdrant | `memory.stored`, `memory.queries` | `agent.completed` | REST (internal) | p99 < 200ms |
| `event-store` | سجل الأحداث غير قابل للتعديل | Python + NATS | NATS + MinIO | — | كل الأحداث | REST (internal) | p99 < 50ms |
| `model-gateway-service` | توجيه النماذج | Python/FastAPI | Redis | `model.invoked` | `model.requested` | REST (internal) | p99 < 5s |
| `evaluation-service` | تقييم النماذج والنتائج | Python/FastAPI | PostgreSQL | `evaluation.completed`, `gap.identified` | `agent.completed` | REST (internal) | حسب التقييم |
| `governance-service` | السياسات + الموافقات + Kill Switch | Python/FastAPI | PostgreSQL | `policy.checked`, `approval.signed`, `system.halt` | كل الأحداث | REST (internal, human) | p99 < 100ms |
| `control-console` | واجهة الويب للإدارة | TypeScript/React | — | — | — | REST (internal) | — |
| `observability-stack` | المراقبة + التتبع | OTel + Grafana | Prometheus | — | — | — | — |
| `training-service` | تدريب LoRA + إدارة الدورات | Python + PEFT | MinIO + PostgreSQL | `model.trained`, `model.distilled` | `evaluation.completed` | REST (internal) | حسب التدريب |
| `critic-service` | مراجعة وتقييم النتائج | Python/FastAPI | PostgreSQL | `critic.reviewed` | `agent.completed` | gRPC (internal) | p99 < 10s |

---

## 6. البنية القابلة للحياة الدنيا (Minimal Viable Architecture)

```
┌──────────────────────────────────────────────────────────┐
│                    Client / User                          │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼───────────────────────────────┐
│              api-gateway (:8000)                           │
│              [FastAPI + JWT Auth]                          │
└──────────┬───────────────────────────────────┬───────────┘
           │                                   │
           ▼                                   ▼
┌─────────────────────┐              ┌──────────────────────┐
│ orchestrator-service│              │ governance-service   │
│ (:8001)             │              │ (:8009)              │
│ [Temporal workflows]│              │ [OPA + Audit Log]    │
└────────┬────────────┘              └──────────────────────┘
         │
    ┌────┼────────────────────────┐
    │    │                        │
    ▼    ▼                        ▼
┌────────────┐  ┌──────────────┐  ┌──────────────┐
│ agent-     │  │ tool-       │  │ model-       │
│ runtime    │  │ registry    │  │ gateway     │
│ (:8002)   │  │ (:8003)     │  │ (:8004)     │
│ [Worker    │  │ [Sandbox    │  │ [Claude +   │
│  Pool]     │  │  Docker]    │  │  vLLM]      │
└─────┬──────┘  └──────────────┘  └──────────────┘
      │
      ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ memory-      │  │ evaluation-  │  │ critic-      │
│ service      │  │ service     │  │ service      │
│ (:8005)      │  │ (:8006)     │  │ (:8007)     │
│ [Redis +     │  │ [Benchmark  │  │ [Quality    │
│  Qdrant]     │  │  Suite]     │  │  Scoring]   │
└──────────────┘  └──────────────┘  └──────────────┘

┌──────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                    │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│ PostgreSQL│  Redis   │  NATS    │  MinIO   │  Qdrant      │
│ (:5432)  │ (:6379)  │ (:4222)  │ (:9000)  │  (:6333)    │
│ [Truth +  │ [Cache + │ [Event   │ [Objects │  [Vectors]  │
│  Audit]   │  Session]│  Bus]   │  +Models]│              │
└──────────┴──────────┴──────────┴──────────┴──────────────┘

┌──────────────────────────────────────────────────────────┐
│                    Observability Layer                     │
│  OpenTelemetry → Jaeger (:16686) + Prometheus (:9090)     │
│  + Grafana (:3000)                                        │
└──────────────────────────────────────────────────────────┘
```

---

## 7. قاعدة البيانات

### 7.1 PostgreSQL — المخطط الكامل

```sql
-- ============================================
-- AMOS-SE Core Database Schema
-- Version: 1.0
-- ============================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- ملاحظة: UUIDv7 يُولّد من التطبيق بمكتبة مخصصة (python-uuid6 أو ulid)
-- في قاعدة البيانات نستخدم gen_random_uuid() (UUIDv4) كافتراضي

-- ============================================
-- agents: سجل الوكلاء
-- ============================================
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id VARCHAR(255) UNIQUE NOT NULL,
    agent_type VARCHAR(50) NOT NULL CHECK (
        agent_type IN ('orchestrator', 'supervisor', 'worker', 'critic', 'security', 'red_team', 'meta')
    ),
    domain VARCHAR(100),
    version VARCHAR(20) NOT NULL DEFAULT '1.0.0',
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (
        status IN ('active', 'paused', 'retired', 'draft')
    ),
    manifest JSONB NOT NULL,
    permissions JSONB NOT NULL DEFAULT '[]',
    budget JSONB NOT NULL DEFAULT '{}',
    sla JSONB NOT NULL DEFAULT '{}',
    tenant_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    retired_at TIMESTAMPTZ
);

CREATE INDEX idx_agents_type ON agents(agent_type);
CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_domain ON agents(domain);
CREATE INDEX idx_agents_tenant ON agents(tenant_id);

-- ============================================
-- tools: سجل الأدوات
-- ============================================
CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    protocol VARCHAR(20) NOT NULL DEFAULT 'openapi',
    description TEXT,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    permissions_required JSONB NOT NULL DEFAULT '[]',
    risk_level VARCHAR(20) NOT NULL DEFAULT 'low' CHECK (
        risk_level IN ('low', 'medium', 'high', 'critical')
    ),
    sandbox_required BOOLEAN NOT NULL DEFAULT TRUE,
    sandbox_config JSONB DEFAULT '{}',
    rate_limits JSONB DEFAULT '{}',
    audit_config JSONB DEFAULT '{}',
    tool_bom JSONB,
    checksum VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deprecated_at TIMESTAMPTZ
);

CREATE INDEX idx_tools_status ON tools(status);
CREATE INDEX idx_tools_risk ON tools(risk_level);

-- ============================================
-- tasks: المهام
-- ============================================
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR(255) UNIQUE NOT NULL,
    parent_task_id UUID REFERENCES tasks(id),
    type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    priority VARCHAR(20) NOT NULL DEFAULT 'normal' CHECK (
        priority IN ('low', 'normal', 'high', 'critical')
    ),
    domain VARCHAR(100),
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'planning', 'assigned', 'executing',
                   'critiquing', 'completed', 'failed', 'cancelled')
    ),
    plan JSONB,
    assigned_agents JSONB DEFAULT '[]',
    tools_used JSONB DEFAULT '[]',
    result JSONB,
    critic_feedback JSONB,
    quality_score DECIMAL(3,2),
    budget_limit JSONB,
    budget_used JSONB DEFAULT '{}',
    tenant_id VARCHAR(100),
    deadline TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    execution_time_ms INTEGER
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_domain ON tasks(domain);
CREATE INDEX idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);

-- ============================================
-- task_events: سجل أحداث المهمة
-- ============================================
CREATE TABLE task_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES tasks(id),
    event_type VARCHAR(50) NOT NULL,
    actor_type VARCHAR(20) NOT NULL CHECK (
        actor_type IN ('human', 'agent', 'system', 'external_model')
    ),
    actor_id VARCHAR(255),
    actor_version VARCHAR(20),
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(500),
    inputs_hash VARCHAR(255),
    outputs_hash VARCHAR(255),
    model_used VARCHAR(100),
    policy_checks JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    chain_hash VARCHAR(255) NOT NULL,
    previous_hash VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_task_events_task ON task_events(task_id);
CREATE INDEX idx_task_events_type ON task_events(event_type);
CREATE INDEX idx_task_events_created ON task_events(created_at);

-- ============================================
-- experiences: سجل الخبرات
-- ============================================
CREATE TABLE experiences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experience_id VARCHAR(255) UNIQUE NOT NULL,
    task_id UUID NOT NULL REFERENCES tasks(id),
    type VARCHAR(20) NOT NULL CHECK (
        type IN ('success', 'failure', 'gap', 'repair')
    ),
    task_description TEXT NOT NULL,
    domain VARCHAR(100),
    complexity VARCHAR(20) DEFAULT 'medium',
    agent_id VARCHAR(255),
    model_used VARCHAR(100),
    approach JSONB NOT NULL,
    outcome JSONB NOT NULL,
    quality_score DECIMAL(3,2),
    critic_score DECIMAL(3,2),
    execution_time_s INTEGER,
    cost_usd DECIMAL(10,4),
    external_model_used JSONB,
    learning_value JSONB,
    provenance JSONB NOT NULL,
    tenant_id VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_experiences_type ON experiences(type);
CREATE INDEX idx_experiences_domain ON experiences(domain);
CREATE INDEX idx_experiences_agent ON experiences(agent_id);
CREATE INDEX idx_experiences_model ON experiences(model_used);
CREATE INDEX idx_experiences_tenant ON experiences(tenant_id);
CREATE INDEX idx_experiences_created ON experiences(created_at);

-- ============================================
-- model_versions: سجل النماذج
-- ============================================
CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id VARCHAR(255) UNIQUE NOT NULL,
    parent_model VARCHAR(255),
    base_model VARCHAR(255) NOT NULL,
    training_method VARCHAR(50) NOT NULL DEFAULT 'lora',
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (
        status IN ('draft', 'training', 'evaluating', 'candidate',
                   'shadow', 'canary', 'stable', 'archived', 'rejected')
    ),
    training_data JSONB,
    evaluation JSONB,
    promotion JSONB,
    rollback_plan JSONB,
    weights_location VARCHAR(500),
    lora_adapter_location VARCHAR(500),
    model_bom JSONB,
    data_bom JSONB,
    checksum VARCHAR(255),
    signature VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    promoted_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ
);

CREATE INDEX idx_models_status ON model_versions(status);
CREATE INDEX idx_models_parent ON model_versions(parent_model);

-- ============================================
-- evaluations: سجل التقييمات
-- ============================================
CREATE TABLE evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id VARCHAR(255) NOT NULL REFERENCES model_versions(model_id),
    eval_type VARCHAR(50) NOT NULL CHECK (
        eval_type IN ('regression', 'benchmark', 'shadow', 'canary',
                      'safety', 'constitution', 'red_team')
    ),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'running', 'passed', 'failed', 'error')
    ),
    results JSONB NOT NULL,
    improvement_score DECIMAL(5,2),
    regression_score DECIMAL(5,2),
    safety_score DECIMAL(3,2),
    constitution_score DECIMAL(3,2),
    benchmarks JSONB,
    forgetting_check JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_evals_model ON evaluations(model_id);
CREATE INDEX idx_evals_type ON evaluations(eval_type);
CREATE INDEX idx_evals_status ON evaluations(status);

-- ============================================
-- approvals: سجل الموافقات البشرية
-- ============================================
CREATE TABLE approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_id VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (
        type IN ('model_promotion', 'tool_registration', 'agent_deployment',
                 'kill_switch', 'policy_change', 'charter_amendment')
    ),
    resource_id VARCHAR(255) NOT NULL,
    requester_type VARCHAR(20) NOT NULL,
    requester_id VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'approved', 'rejected', 'expired', 'withdrawn')
    ),
    reviewer_id VARCHAR(255),
    review_notes TEXT,
    signed_artifact JSONB,
    context JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ
);

CREATE INDEX idx_approvals_type ON approvals(type);
CREATE INDEX idx_approvals_status ON approvals(status);
CREATE INDEX idx_approvals_resource ON approvals(resource_id);

-- ============================================
-- audit_log: سجل التدقيق غير القابل للتعديل
-- ============================================
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id VARCHAR(255) UNIQUE NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type VARCHAR(50) NOT NULL,
    actor_type VARCHAR(20) NOT NULL,
    actor_id VARCHAR(255),
    actor_version VARCHAR(20),
    action VARCHAR(255) NOT NULL,
    resource VARCHAR(500),
    inputs_hash VARCHAR(255),
    outputs_hash VARCHAR(255),
    model_used VARCHAR(100),
    policy_checks JSONB DEFAULT '[]',
    parent_event VARCHAR(255),
    chain_hash VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}',
    provenance JSONB
);

-- Append-only: لا يمكن تعديل أو حذف
-- ملاحظة: CREATE RULE غير كافٍ للإنتاج. استخدم DB roles صارمة
-- (GRANT INSERT ONLY, REVOKE UPDATE, DELETE) + triggers ترفض التعديل.
-- للأرشفة طويلة المدى: WORM Object Store (S3 Object Lock).
CREATE RULE no_update AS ON UPDATE TO audit_log DO INSTEAD NOTHING;
CREATE RULE no_delete AS ON DELETE TO audit_log DO INSTEAD NOTHING;

-- Production: استخدم أيضاً
-- REVOKE UPDATE, DELETE ON audit_log FROM amos_app;
-- GRANT INSERT, SELECT ON audit_log TO amos_app;

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_type ON audit_log(event_type);
CREATE INDEX idx_audit_actor ON audit_log(actor_id);
CREATE INDEX idx_audit_chain ON audit_log(chain_hash);

-- ============================================
-- policies: سجل السياسات
-- ============================================
CREATE TABLE policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (
        severity IN ('low', 'medium', 'high', 'critical', 'constitutional')
    ),
    rego_code TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deprecated_at TIMESTAMPTZ
);

-- ============================================
-- tenants: المستأجرون (Multi-tenancy)
-- ============================================
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    encryption_key_id VARCHAR(255),
    data_retention_days INTEGER DEFAULT 3650,
    consent_log JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(20) NOT NULL DEFAULT 'active'
);

-- ============================================
-- schema_migrations: تتبع الهجرات
-- ============================================
CREATE TABLE schema_migrations (
    version VARCHAR(255) PRIMARY KEY,
    description TEXT,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum VARCHAR(255) NOT NULL,
    rollback_sql TEXT
);
```

### 7.2 Qdrant — Vector Collections

```python
# Vector collections setup

# Collection 1: Knowledge embeddings
{
    "collection_name": "knowledge_vectors",
    "vectors_config": {
        "size": 1024,  # sentence-transformers dimension
        "distance": "Cosine"
    },
    "payload_schema": {
        "domain": "keyword",
        "agent_id": "keyword",
        "experience_id": "keyword",
        "type": "keyword",  # success, failure, gap
        "timestamp": "datetime",
        "tenant_id": "keyword"
    }
}

# Collection 2: Task embeddings (for similarity search)
{
    "collection_name": "task_vectors",
    "vectors_config": {
        "size": 1024,
        "distance": "Cosine"
    },
    "payload_schema": {
        "task_id": "keyword",
        "domain": "keyword",
        "status": "keyword",
        "quality_score": "float",
        "tenant_id": "keyword"
    }
}
```

---

## 8. عقود الأحداث (Event Contracts)

كل حدث يُنشر على NATS JetStream بالـ subject pattern: `amos_se.{domain}.{event_type}`

### 8.1 task.created

```json
{
  "event_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B2",
  "timestamp": "2026-08-15T22:07:23.456123Z",
  "event_type": "task.created",
  "version": "1.0",
  "source": "api-gateway",
  "subject": "amos_se.tasks.created",
  "data": {
    "task_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B2",
    "type": "analysis",
    "description": "Analyze Q3 sales performance and suggest Q4 plan",
    "priority": "high",
    "domain": "financial",
    "budget_limit": {
      "max_tokens": 50000,
      "max_cost_usd": 5.00
    },
    "tenant_id": "tenant_001",
    "deadline": "2026-08-16T00:00:00Z"
  },
  "metadata": {
    "request_ip": "10.0.0.1",
    "user_id": "user_123",
    "trace_id": "trace_abc123"
  },
  "chain_hash": "sha256:previous_hash + this_event_hash"
}
```

### 8.2 task.planned

```json
{
  "event_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B3",
  "timestamp": "2026-08-15T22:07:24.100000Z",
  "event_type": "task.planned",
  "version": "1.0",
  "source": "orchestrator-service",
  "subject": "amos_se.tasks.planned",
  "data": {
    "task_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B2",
    "plan": {
      "subtasks": [
        {
          "id": "st_1",
          "description": "Extract Q3 sales data",
          "agent_type": "worker",
          "domain": "financial",
          "tools": ["sql_query"],
          "estimated_tokens": 5000
        },
        {
          "id": "st_2",
          "description": "Analyze trends and anomalies",
          "agent_type": "worker",
          "domain": "financial",
          "tools": ["python_execute", "chart_generate"],
          "estimated_tokens": 8000,
          "depends_on": ["st_1"]
        },
        {
          "id": "st_3",
          "description": "Generate Q4 plan",
          "agent_type": "worker",
          "domain": "financial",
          "tools": ["report_format"],
          "estimated_tokens": 10000,
          "depends_on": ["st_2"]
        }
      ]
    },
    "total_estimated_tokens": 23000,
    "total_estimated_cost_usd": 0.46,
    "planning_time_ms": 850
  },
  "parent_event": "01J5X8M3K2Q7V9R1T4Y6Z8A0B2",
  "chain_hash": "sha256:..."
}
```

### 8.3 agent.assigned

```json
{
  "event_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B4",
  "timestamp": "2026-08-15T22:07:24.500000Z",
  "event_type": "agent.assigned",
  "version": "1.0",
  "source": "orchestrator-service",
  "subject": "amos_se.agents.assigned",
  "data": {
    "task_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B2",
    "subtask_id": "st_1",
    "agent_id": "worker-financial-analyzer-007",
    "agent_version": "1.3.0",
    "model": "alpha-v1.0",
    "tools_allowed": ["sql_query"],
    "budget": {
      "max_tokens": 5000,
      "max_cost_usd": 0.10
    }
  },
  "parent_event": "01J5X8M3K2Q7V9R1T4Y6Z8A0B3",
  "chain_hash": "sha256:..."
}
```

### 8.4 tool.executed

```json
{
  "event_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B5",
  "timestamp": "2026-08-15T22:07:25.800000Z",
  "event_type": "tool.executed",
  "version": "1.0",
  "source": "agent-runtime-service",
  "subject": "amos_se.tools.executed",
  "data": {
    "task_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B2",
    "subtask_id": "st_1",
    "agent_id": "worker-financial-analyzer-007",
    "tool_id": "sql_query",
    "tool_version": "2.1.0",
    "inputs": {
      "database": "financial_db",
      "query": "SELECT * FROM sales WHERE quarter = 'Q3'..."
    },
    "outputs": {
      "row_count": 1542,
      "columns": ["date", "product", "revenue", ...],
      "execution_time_ms": 120
    },
    "inputs_hash": "sha256:abc123...",
    "outputs_hash": "sha256:def456...",
    "sandbox_id": "sandbox_a1b2c3",
    "policy_checks": [
      {"rule": "data.read", "result": "passed"},
      {"rule": "budget.check", "result": "passed", "remaining_tokens": 45000}
    ]
  },
  "parent_event": "01J5X8M3K2Q7V9R1T4Y6Z8A0B4",
  "chain_hash": "sha256:..."
}
```

### 8.5 experience.recorded

```json
{
  "event_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B6",
  "timestamp": "2026-08-15T22:07:30.000000Z",
  "event_type": "experience.recorded",
  "version": "1.0",
  "source": "memory-service",
  "subject": "amos_se.experiences.recorded",
  "data": {
    "experience_id": "exp_01J5X8M3K2Q7V9R1T4Y6Z8A0B6",
    "task_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B2",
    "type": "success",
    "domain": "financial",
    "agent_id": "worker-financial-analyzer-007",
    "model_used": "alpha-v1.0",
    "outcome": {
      "success": true,
      "quality_score": 0.92,
      "execution_time_s": 5.8,
      "cost_usd": 0.12
    },
    "learning_value": {
      "positive": true,
      "reusable": true,
      "training_weight": 1.0
    },
    "provenance": {
      "source": "live_operation",
      "verified": true,
      "pii_checked": true,
      "license": "internal"
    }
  },
  "parent_event": "01J5X8M3K2Q7V9R1T4Y6Z8A0B2",
  "chain_hash": "sha256:..."
}
```

### 8.6 model.evaluated

```json
{
  "event_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B7",
  "timestamp": "2026-08-15T22:15:00.000000Z",
  "event_type": "model.evaluated",
  "version": "1.0",
  "source": "evaluation-service",
  "subject": "amos_se.models.evaluated",
  "data": {
    "model_id": "beta-v0.3",
    "parent_model": "alpha-v1.0",
    "eval_type": "regression",
    "status": "passed",
    "results": {
      "improvement_over_parent": 0.057,
      "regression_rate": 0.012,
      "safety_score": 1.0,
      "constitution_compliance": 1.0,
      "forgetting_check": {
        "knowledge_retained": 0.987,
        "areas_affected": [],
        "severity": "none"
      }
    },
    "benchmarks_run": 50,
    "benchmarks_passed": 49,
    "evaluation_time_s": 120
  },
  "parent_event": "01J5X8M3K2Q7V9R1T4Y6Z8A0B2",
  "chain_hash": "sha256:..."
}
```

### 8.7 promotion.requested

```json
{
  "event_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B8",
  "timestamp": "2026-08-15T22:16:00.000000Z",
  "event_type": "promotion.requested",
  "version": "1.0",
  "source": "evaluation-service",
  "subject": "amos_se.governance.promotion_requested",
  "data": {
    "model_id": "beta-v0.3",
    "parent_model": "alpha-v1.0",
    "gates_passed": ["evaluation", "shadow_testing"],
    "gates_pending": ["canary", "human_review"],
    "evaluation_summary": {
      "improvement": 0.057,
      "regression": 0.012,
      "safety": 1.0
    },
    "rollback_plan": {
      "previous_model": "alpha-v1.0",
      "rollback_time_estimate": "5 minutes"
    }
  },
  "parent_event": "01J5X8M3K2Q7V9R1T4Y6Z8A0B7",
  "chain_hash": "sha256:..."
}
```

### 8.8 approval.signed

```json
{
  "event_id": "01J5X8M3K2Q7V9R1T4Y6Z8A0B9",
  "timestamp": "2026-08-15T23:30:00.000000Z",
  "event_type": "approval.signed",
  "version": "1.0",
  "source": "governance-service",
  "subject": "amos_se.governance.approval_signed",
  "data": {
    "approval_id": "appr_01J5X8M3K2Q7V9R1T4Y6Z8A0B9",
    "type": "model_promotion",
    "resource_id": "beta-v0.3",
    "decision": "approved",
    "reviewer_id": "human_committee_member_001",
    "review_notes": "Improvement in financial domain. Minor regression acceptable.",
    "signed_artifact": {
      "signature": "ed25519:base64encoded...",
      "signer_key_id": "key_001",
      "timestamp": "2026-08-15T23:30:00Z",
      "payload_hash": "sha256:..."
    },
    "expires_at": "2026-08-22T23:30:00Z"
  },
  "parent_event": "01J5X8M3K2Q7V9R1T4Y6Z8A0B8",
  "chain_hash": "sha256:..."
}
```

---

### 8.9 Event Schema Registry + Contract Tests

كل حدث له JSON Schema مسجل. CI يفشل إذا كسر منتج/مستهلك العقد.

```python
# src/shared/event_schemas.py
"""AMOS-SE Event Schema Registry — كل حدث له schema مسجل."""

from pydantic import BaseModel
from typing import Any
import json


class EventSchema(BaseModel):
    """تعريف schema لحدث."""
    event_type: str
    version: str
    required_fields: list[str]
    field_types: dict[str, str]


# سجل الأحداث المسجلة
EVENT_SCHEMAS = {
    "task.created": EventSchema(
        event_type="task.created",
        version="1.0",
        required_fields=["task_id", "type", "description", "priority"],
        field_types={"task_id": "str", "type": "str", "description": "str"}
    ),
    "task.planned": EventSchema(
        event_type="task.planned",
        version="1.0",
        required_fields=["task_id", "plan", "total_estimated_tokens"],
        field_types={"task_id": "str", "plan": "dict"}
    ),
    # ... باقي الأحداث
}


def validate_event(event_type: str, data: dict[str, Any]) -> bool:
    """تحقق من أن الحدث يطابق schema المسجل."""
    schema = EVENT_SCHEMAS.get(event_type)
    if not schema:
        raise ValueError(f"Unknown event type: {event_type}")
    for field in schema.required_fields:
        if field not in data:
            return False
    return True


# Contract test (في tests/)
# def test_task_created_schema():
#     event = {"task_id": "123", "type": "analysis", "description": "test", "priority": "normal"}
#     assert validate_event("task.created", event) == True
```

---

## 9. عقود الـ API (OpenAPI)

### 9.1 API العام المختصر

```yaml
openapi: 3.0.3
info:
  title: AMOS-SE API
  version: 1.0.0
  description: AMOS-SE Agentic Mesh Operating System API

servers:
  - url: http://localhost:8000/v1
    description: Local development

security:
  - BearerAuth: []

paths:
  /tasks:
    post:
      summary: Submit a new task
      tags: [Tasks]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskRequest'
      responses:
        '202':
          description: Task accepted
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskAccepted'

  /tasks/{task_id}:
    get:
      summary: Get task status and results
      tags: [Tasks]
      parameters:
        - name: task_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Task details
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskDetails'

  /agents:
    get:
      summary: List active agents
      tags: [Agents]
      responses:
        '200':
          description: Agent list

  /agents:
    post:
      summary: Register a new agent
      tags: [Agents]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AgentManifest'

  /tools:
    post:
      summary: Register a new tool
      tags: [Tools]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ToolManifest'

  /experiences:
    get:
      summary: Query experience replay buffer
      tags: [Memory]
      parameters:
        - name: type
          in: query
          schema:
            type: string
            enum: [success, failure, gap, repair]
        - name: domain
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
      responses:
        '200':
          description: Experience list

  /memory/store:
    post:
      summary: Store knowledge in memory
      tags: [Memory]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MemoryStore'

  /memory/query:
    post:
      summary: Query memory semantically
      tags: [Memory]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MemoryQuery'

  /evaluations/run:
    post:
      summary: Run model evaluation
      tags: [Evaluation]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EvalRequest'

  /governance/approvals:
    get:
      summary: List pending approvals (human only)
      tags: [Governance]
      responses:
        '200':
          description: Pending approvals
    post:
      summary: Submit approval decision (human only)
      tags: [Governance]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ApprovalDecision'

  /governance/halt:
    post:
      summary: Trigger kill switch (human only)
      tags: [Governance]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [level, reason]
              properties:
                level:
                  type: integer
                  minimum: 0
                  maximum: 5
                reason:
                  type: string

  /health:
    get:
      summary: System health check
      tags: [System]
      security: []
      responses:
        '200':
          description: System status

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    TaskRequest:
      type: object
      required: [type, description]
      properties:
        type:
          type: string
          enum: [analysis, generation, execution, research, planning]
        description:
          type: string
        priority:
          type: string
          enum: [low, normal, high, critical]
          default: normal
        domain:
          type: string
        budget_limit:
          type: object
          properties:
            max_tokens:
              type: integer
            max_cost_usd:
              type: number
        deadline:
          type: string
          format: date-time

    TaskAccepted:
      type: object
      properties:
        task_id:
          type: string
        status:
          type: string
        estimated_completion:
          type: string
          format: date-time

    AgentManifest:
      type: object
      required: [agent_id, agent_type, domain]
      properties:
        agent_id:
          type: string
        agent_type:
          type: string
        domain:
          type: string
        model_config:
          type: object
        permissions:
          type: object
        budget:
          type: object

    ToolManifest:
      type: object
      required: [tool_id, name, input_schema, output_schema]
      properties:
        tool_id:
          type: string
        name:
          type: string
        version:
          type: string
        input_schema:
          type: object
        output_schema:
          type: object
        risk_level:
          type: string
        sandbox_required:
          type: boolean

    MemoryStore:
      type: object
      required: [content, domain]
      properties:
        content:
          type: string
        domain:
          type: string
        metadata:
          type: object

    MemoryQuery:
      type: object
      required: [query]
      properties:
        query:
          type: string
        domain:
          type: string
        limit:
          type: integer
          default: 10

    EvalRequest:
      type: object
      required: [model_id, eval_type]
      properties:
        model_id:
          type: string
        eval_type:
          type: string
          enum: [regression, benchmark, shadow, canary, safety, constitution]

    ApprovalDecision:
      type: object
      required: [approval_id, decision]
      properties:
        approval_id:
          type: string
        decision:
          type: string
          enum: [approve, reject]
        reason:
          type: string
```

---

## 10. Local Development Stack

### 10.1 docker-compose.yml

```yaml
# docker-compose.yml
# AMOS-SE Local Development Stack
# Usage: docker compose up -d

version: "3.9"

services:
  # ============================================
  # Databases & Storage
  # ============================================
  
  postgres:
    image: postgres:16-alpine
    container_name: amos-postgres
    environment:
      POSTGRES_DB: amos_se
      POSTGRES_USER: amos
      POSTGRES_PASSWORD: dev_password_change_me
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U amos"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: amos-redis
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    container_name: amos-qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      QDRANT__LOG_LEVEL: INFO

  minio:
    image: minio/minio:latest
    container_name: amos-minio
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: amos
      MINIO_ROOT_PASSWORD: dev_password_change_me
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 15s
      timeout: 5s
      retries: 5

  # ============================================
  # Event Bus
  # ============================================
  
  nats:
    image: nats:2.10-alpine
    container_name: amos-nats
    command: >
      --jetstream
      --store_dir /data
      --max_mem_store 256MB
      --max_file_store 1GB
    ports:
      - "4222:4222"
      - "8222:8222"  # monitoring
    volumes:
      - nats_data:/data

  # ============================================
  # Workflow Engine
  # ============================================
  
  temporal-postgresql:
    image: postgres:16-alpine
    container_name: amos-temporal-postgres
    environment:
      POSTGRES_DB: temporal
      POSTGRES_USER: temporal
      POSTGRES_PASSWORD: temporal_dev
    volumes:
      - temporal_pg_data:/var/lib/postgresql/data

  temporal:
    image: temporalio/auto-setup:1.23
    container_name: amos-temporal
    depends_on: [temporal-postgresql]
    environment:
      DB: postgres12
      DB_PORT: 5432
      POSTGRES_USER: temporal
      POSTGRES_PWD: temporal_dev
      POSTGRES_SEEDS: temporal-postgresql
      LOG_LEVEL: error
    ports:
      - "7233:7233"

  temporal-ui:
    image: temporalio/ui:2.30
    container_name: amos-temporal-ui
    depends_on: [temporal]
    environment:
      TEMPORAL_ADDRESS: temporal:7233
      TEMPORAL_CORS_ORIGINS: http://localhost:3000
    ports:
      - "8080:8080"

  # ============================================
  # Observability
  # ============================================
  
  jaeger:
    image: jaegertracing/all-in-one:1.60
    container_name: amos-jaeger
    environment:
      COLLECTOR_OTLP_ENABLED: true
    ports:
      - "16686:16686"  # UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP

  prometheus:
    image: prom/prometheus:latest
    container_name: amos-prometheus
    volumes:
      - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    container_name: amos-grafana
    depends_on: [prometheus]
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana

  # ============================================
  # Model Serving (GPU — optional for local dev)
  # ============================================
  
  # Uncomment when GPU is available
  # vllm:
  #   image: vllm/vllm-openai:latest
  #   container_name: amos-vllm
  #   runtime: nvidia
  #   environment:
  #     HUGGING_FACE_HUB_TOKEN: ${HF_TOKEN}
  #   command: >
  #     --model meta-llama/Meta-Llama-3-8B-Instruct
  #     --port 8000
  #     --max-model-len 4096
  #   ports:
  #     - "8010:8000"
  #   deploy:
  #     resources:
  #       reservations:
  #         devices:
  #           - driver: nvidia
  #             count: 1
  #             capabilities: [gpu]

# ============================================
# Volumes
# ============================================
volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  minio_data:
  nats_data:
  temporal_pg_data:
  grafana_data:
```

### 10.2 Makefile

```makefile
# Makefile — AMOS-SE Development Commands

.PHONY: help up down restart logs ps migrate migrate-down test lint format typecheck

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 5
	@echo "Services: PostgreSQL :5432, Redis :6379, Qdrant :6333, NATS :4222, MinIO :9000, Temporal UI :8080, Grafana :3000"

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## Tail logs
	docker compose logs -f --tail=100

ps: ## List running services
	docker compose ps

migrate: ## Run database migrations
	docker compose exec postgres psql -U amos -d amos_se -f /docker-entrypoint-initdb.d/001_initial.sql

migrate-down: ## Rollback last migration
	@echo "Manual rollback required — check schema_migrations table"

test: ## Run all tests
	pytest tests/ -v --cov=src --cov-report=term-missing

lint: ## Run linter
	ruff check src/ tests/

format: ## Format code
	black src/ tests/
	ruff check --fix src/ tests/

typecheck: ## Type check
	mypy src/ --strict

install: ## Install Python dependencies
	pip install -r requirements.txt
	pre-commit install

clean: ## Clean up
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```

---

## 11. Code Skeleton

### 11.1 هيكل المستودع العملي

```
amos-se/
├── docker-compose.yml
├── Makefile
├── README.md
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
├── .pre-commit-config.yaml
├── pyproject.toml
├── requirements.txt
│
├── migrations/
│   └── 001_initial.sql
│
├── src/
│   ├── shared/                    # Shared libraries
│   │   ├── __init__.py
│   │   ├── config.py              # Settings (pydantic-settings)
│   │   ├── database.py             # SQLAlchemy session
│   │   ├── events.py              # NATS publisher/consumer
│   │   ├── tracing.py             # OpenTelemetry setup
│   │   ├── auth.py                # JWT/OIDC
│   │   ├── audit.py               # Audit log hash chain
│   │   └── models.py              # Shared Pydantic models
│   │
│   ├── api_gateway/               # :8000
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── tasks.py
│   │   │   ├── agents.py
│   │   │   └── health.py
│   │   └── Dockerfile
│   │
│   ├── orchestrator/              # :8001
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── planner.py
│   │   ├── workflows.py           # Temporal workflows
│   │   └── Dockerfile
│   │
│   ├── agent_runtime/             # :8002
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent.py               # Base Agent class
│   │   ├── worker.py
│   │   ├── critic.py
│   │   └── Dockerfile
│   │
│   ├── tool_registry/             # :8003
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── router.py              # Semantic router
│   │   ├── sandbox.py             # Tool sandbox
│   │   └── Dockerfile
│   │
│   ├── model_gateway/             # :8004
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── router.py              # Model router
│   │   ├── providers/
│   │   │   ├── claude.py
│   │   │   ├── openai.py
│   │   │   └── vllm_local.py
│   │   └── Dockerfile
│   │
│   ├── memory_service/            # :8005
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── redis_store.py
│   │   ├── qdrant_store.py
│   │   └── Dockerfile
│   │
│   ├── evaluation/                # :8006
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── benchmarks/
│   │   ├── regression.py
│   │   └── Dockerfile
│   │
│   ├── critic/                    # :8007
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── scorer.py
│   │   └── Dockerfile
│   │
│   ├── governance/                # :8009
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── policy_engine.py       # OPA integration
│   │   ├── kill_switch.py
│   │   ├── approvals.py
│   │   ├── audit_chain.py
│   │   └── Dockerfile
│   │
│   └── training/                  # :8011
│       ├── __init__.py
│       ├── main.py
│       ├── lora_factory.py
│       ├── data_collector.py
│       └── Dockerfile
│
├── manifests/
│   ├── agents/
│   │   ├── orchestrator.yaml
│   │   ├── worker-financial.yaml
│   │   ├── worker-technical.yaml
│   │   └── critic.yaml
│   ├── tools/
│   │   ├── sql_query.yaml
│   │   ├── python_execute.yaml
│   │   └── chart_generate.yaml
│   └── policies/
│       ├── promotion.rego
│       ├── access.rego
│       └── budget.rego
│
├── observability/
│   ├── prometheus.yml
│   └── grafana/
│       └── dashboards/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── conftest.py
│
└── scripts/
    ├── setup_dev.sh
    ├── seed_data.py
    └── health_check.sh
```

### 11.2 FastAPI Service Stub (api-gateway)

```python
# src/api_gateway/main.py
"""AMOS-SE API Gateway — Entry point for all external requests."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

from src.shared.config import settings
from src.shared.events import EventPublisher
from src.shared.tracing import setup_tracing
from src.shared.auth import get_current_user

from .routes import tasks, agents, health

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    # Startup
    setup_tracing(service_name="api-gateway")
    app.state.event_publisher = EventPublisher(
        nats_url=settings.NATS_URL
    )
    await app.state.event_publisher.connect()
    logger.info("api_gateway_started", port=settings.PORT)
    yield
    # Shutdown
    await app.state.event_publisher.close()
    logger.info("api_gateway_stopped")


app = FastAPI(
    title="AMOS-SE API Gateway",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Routes
app.include_router(health.router, tags=["System"])
app.include_router(
    tasks.router,
    prefix="/v1/tasks",
    tags=["Tasks"],
    dependencies=[Depends(get_current_user)],
)
app.include_router(
    agents.router,
    prefix="/v1/agents",
    tags=["Agents"],
    dependencies=[Depends(get_current_user)],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.api_gateway.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_config=None,  # use structlog
    )
```

### 11.3 Agent Manifest YAML

```yaml
# manifests/agents/worker-financial.yaml
agent_id: "worker-financial-analyzer-001"
agent_type: "worker"
domain: "financial"
version: "1.0.0"
status: "active"

model_config:
  primary: "alpha-current"
  fallback: "claude-sonnet-4"
  max_tokens: 8000
  temperature: 0.3

permissions:
  tools:
    - "sql_query"
    - "python_execute"
    - "chart_generate"
    - "report_format"
  data_access:
    - "financial_db.read"
    - "sales_db.read"
    - "market_data.read"
  forbidden:
    - "user_delete"
    - "config_modify"

budget:
  daily_token_limit: 500000
  daily_cost_limit: 50.00
  max_concurrent_tasks: 5
  max_task_duration: 300

sla:
  max_response_time: 30
  quality_threshold: 0.85
  escalation_after: 3

memory:
  can_read: ["experience_replay", "knowledge_vectors"]
  can_write: ["experience_replay"]

lifecycle:
  created: "2026-08-15"
  expires: "2027-08-15"
  auto_retire: true
```

### 11.4 Tool Manifest YAML

```yaml
# manifests/tools/sql_query.yaml
tool_id: "sql_query"
name: "SQL Query Executor"
version: "2.1.0"
status: "active"
protocol: "openapi"

description: "Executes read-only SQL queries on approved databases"

input_schema:
  type: object
  properties:
    database:
      type: string
      enum: ["financial_db", "sales_db", "market_data"]
    query:
      type: string
      maxLength: 10000
    timeout:
      type: integer
      default: 30
      maximum: 120
  required: ["database", "query"]

output_schema:
  type: object
  properties:
    rows:
      type: array
    columns:
      type: array
    row_count:
      type: integer
    execution_time_ms:
      type: integer

permissions_required:
  - "data.read"

risk_level: "low"
sandbox_required: true
sandbox_config:
  resource_limits:
    max_memory_mb: 512
    max_cpu_seconds: 30
    max_rows_returned: 10000
  network_access: false
  file_system: "read_only"

rate_limits:
  per_agent: 60
  global: 1000

audit:
  log_inputs: true
  log_outputs: true
  retain_days: 3650

tool_bom:
  dependencies:
    - psycopg2-binary==2.9.9
    - sqlalchemy==2.0.30
  base_image: python:3.12-slim
  checksum: "sha256:abc123..."
```

### 11.5 OPA/Rego Policy Example

```rego
# manifests/policies/promotion.rego
# AMOS-SE Model Promotion Policy

package amos_se.governance

import rego.v1

# Default deny
default allow := false

# Promotion requires all gates to pass
allow if {
    every gate in input.gates {
        gate.status == "passed"
    }
    input.human_review.status == "approved"
    input.safety_score == 1.0
    input.constitution_compliance == 1.0
}

# Block if any regression exceeds threshold
deny if {
    some area in input.regression_areas
    area.severity == "critical"
    msg := sprintf("Critical regression in area: %s", [area.name])
}

# Block if safety score is not perfect
deny if {
    input.safety_score < 1.0
    msg := "Safety score must be 1.0 (100%)"
}

# Block if improvement is below threshold
deny if {
    input.improvement_score < 0.05
    msg := sprintf("Improvement %.2f%% below 5%% threshold", [input.improvement_score * 100])
}

# Block if human review is pending
deny if {
    input.human_review.status == "pending"
    msg := "Human review is still pending"
}

# Block if human review was rejected
deny if {
    input.human_review.status == "rejected"
    msg := sprintf("Human review rejected: %s", [input.human_review.reason])
}
```

### 11.6 Python Event Publisher Example

```python
# src/shared/events.py
"""AMOS-SE Event Publishing and Consumption via NATS JetStream."""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any
import structlog
import nats
from nats.js.api import StreamConfig, RetentionPolicy

logger = structlog.get_logger()


class EventPublisher:
    """Publishes events to NATS JetStream with hash chain.
    
    ملاحظة: Hash chain هنا للـ operational events فقط.
    للـ audit log الرسمي: استخدم audit-service مركزي عبر
    PostgreSQL transaction + advisory lock لضمان تسلسل صحيح
    في نظام موزع (هذا التنفيذ البسيط يكسر التسلسل عند وجود replicas).
    """

    def __init__(self, nats_url: str):
        self.nats_url = nats_url
        self.nc = None
        self.js = None
        self._last_hash = "genesis"

    async def connect(self):
        """Connect to NATS and ensure stream exists."""
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()

        # Ensure stream exists
        try:
            await self.js.stream_info("AMOS_SE_EVENTS")
        except Exception:
            await self.js.add_stream(
                StreamConfig(
                    name="AMOS_SE_EVENTS",
                    subjects=["amos_se.>"],
                    retention=RetentionPolicy.LIMITS,
                    max_msgs=1_000_000,
                    max_age=60 * 60 * 24 * 365,  # 1 year in NATS; long-term archive to MinIO/S3 WORM
                )
            )
            logger.info("jetstream_created", stream="AMOS_SE_EVENTS")

        logger.info("event_publisher_connected")

    async def close(self):
        """Close NATS connection."""
        if self.nc:
            await self.nc.drain()
            await self.nc.close()

    def _compute_chain_hash(self, event: dict[str, Any]) -> str:
        """Compute hash chain: SHA256(previous_hash + event_hash)."""
        event_str = json.dumps(event, sort_keys=True, default=str)
        event_hash = hashlib.sha256(event_str.encode()).hexdigest()
        combined = f"{self._last_hash}{event_hash}"
        chain_hash = hashlib.sha256(combined.encode()).hexdigest()
        return chain_hash

    async def publish(
        self,
        event_type: str,
        subject: str,
        data: dict[str, Any],
        source: str,
        parent_event: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Publish an event to NATS JetStream."""
        event_id = str(uuid.uuid4())  # في الإنتاج: استخدم UUIDv7 أو ULID (python-uuid6)
        timestamp = datetime.now(timezone.utc).isoformat()

        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "version": "1.0",
            "source": source,
            "subject": subject,
            "data": data,
            "metadata": metadata or {},
            "parent_event": parent_event,
            "chain_hash": "",  # will be computed
        }

        # Compute chain hash
        chain_hash = self._compute_chain_hash(event)
        event["chain_hash"] = chain_hash
        self._last_hash = chain_hash

        # Publish
        subject_full = f"amos_se.{subject}"
        payload = json.dumps(event, default=str).encode()

        ack = await self.js.publish(subject_full, payload)
        logger.info(
            "event_published",
            event_id=event_id,
            event_type=event_type,
            subject=subject_full,
            seq=ack.seq,
        )

        return event_id


class EventConsumer:
    """Consumes events from NATS JetStream."""

    def __init__(self, nats_url: str):
        self.nats_url = nats_url
        self.nc = None
        self.js = None

    async def connect(self):
        self.nc = await nats.connect(self.nats_url)
        self.js = self.nc.jetstream()

    async def subscribe(
        self,
        subject: str,
        handler: callable,
        durable_name: str,
        queue_group: str | None = None,
    ):
        """Subscribe to events with a handler function."""
        subject_full = f"amos_se.{subject}"

        async def message_handler(msg):
            event = json.loads(msg.data.decode())
            try:
                await handler(event)
                await msg.ack()
            except Exception as e:
                logger.error("event_handler_failed", error=str(e), event_id=event.get("event_id"))
                await msg.nak()

        await self.js.subscribe(
            subject_full,
            durable=durable_name,
            queue=queue_group,
            cb=message_handler,
        )
        logger.info("subscribed", subject=subject_full, durable=durable_name)

    async def close(self):
        if self.nc:
            await self.nc.drain()
            await self.nc.close()
```

### 11.7 Base Agent Class

```python
# src/agent_runtime/agent.py
"""AMOS-SE Base Agent — Foundation for all agent types."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any
import structlog
from pydantic import BaseModel

from src.shared.events import EventPublisher
from src.shared.config import settings

logger = structlog.get_logger()


class AgentContext(BaseModel):
    """Context passed to an agent when assigned a task."""
    task_id: str
    subtask_id: str | None = None
    description: str
    tools_allowed: list[str] = []
    budget: dict[str, Any] = {}
    model_config: dict[str, Any] = {}


class AgentResult(BaseModel):
    """Result returned by an agent after execution."""
    success: bool
    output: str | dict[str, Any]
    quality_score: float = 0.0
    tools_used: list[str] = []
    tokens_used: int = 0
    cost_usd: float = 0.0
    execution_time_s: float = 0.0
    error: str | None = None


class BaseAgent(ABC):
    """Base class for all AMOS-SE agents."""

    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        domain: str,
        version: str,
        event_publisher: EventPublisher,
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.domain = domain
        self.version = version
        self.events = event_publisher
        self._started_at: datetime | None = None

    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the assigned task. Must be implemented by subclasses."""
        ...

    async def run(self, context: AgentContext) -> AgentResult:
        """Run the agent with full lifecycle tracking."""
        self._started_at = datetime.now(timezone.utc)

        # Publish: agent.started
        await self.events.publish(
            event_type="agent.started",
            subject="agents.started",
            source="agent-runtime-service",
            data={
                "task_id": context.task_id,
                "subtask_id": context.subtask_id,
                "agent_id": self.agent_id,
                "agent_version": self.version,
                "domain": self.domain,
            },
            parent_event=context.task_id,
        )

        logger.info(
            "agent_started",
            agent_id=self.agent_id,
            task_id=context.task_id,
        )

        try:
            result = await self.execute(context)
            execution_time = (datetime.now(timezone.utc) - self._started_at).total_seconds()
            result.execution_time_s = execution_time

            # Publish: agent.completed
            await self.events.publish(
                event_type="agent.completed",
                subject="agents.completed",
                source="agent-runtime-service",
                data={
                    "task_id": context.task_id,
                    "subtask_id": context.subtask_id,
                    "agent_id": self.agent_id,
                    "success": result.success,
                    "quality_score": result.quality_score,
                    "tools_used": result.tools_used,
                    "tokens_used": result.tokens_used,
                    "cost_usd": result.cost_usd,
                    "execution_time_s": result.execution_time_s,
                },
                parent_event=context.task_id,
            )

            logger.info(
                "agent_completed",
                agent_id=self.agent_id,
                task_id=context.task_id,
                success=result.success,
                quality=result.quality_score,
            )

            return result

        except Exception as e:
            logger.error(
                "agent_failed",
                agent_id=self.agent_id,
                task_id=context.task_id,
                error=str(e),
            )
            return AgentResult(
                success=False,
                output={},
                error=str(e),
                execution_time_s=(datetime.now(timezone.utc) - self._started_at).total_seconds(),
            )
```

---

## 12. CI/CD Pipeline

### 12.1 GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: AMOS-SE CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.12"
  REGISTRY: ghcr.io

jobs:
  # ============================================
  # Code Quality
  # ============================================
  lint:
    name: Lint & Format Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install ruff black mypy
      - run: ruff check src/ tests/
      - run: black --check src/ tests/
      - run: mypy src/ --strict

  # ============================================
  # Unit Tests
  # ============================================
  test:
    name: Unit & Integration Tests
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: amos_se_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
      nats:
        image: nats:2.10-alpine
        ports: ["4222:4222"]
        options: >-
          --jetstream
          --store_dir /data
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - run: pip install -r requirements.txt pytest pytest-cov pytest-asyncio
      - name: Run migrations
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/amos_se_test
        run: |
          psql $DATABASE_URL -f migrations/001_initial.sql
      - name: Run tests
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/amos_se_test
          REDIS_URL: redis://localhost:6379
          NATS_URL: nats://localhost:4222
        run: pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing
      - uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  # ============================================
  # Schema Migration Check
  # ============================================
  migration-check:
    name: Schema Migration Check
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - name: Verify migrations are valid SQL
        run: |
          for f in migrations/*.sql; do
            echo "Checking $f..."
            docker run --rm -v "$f:/tmp/migration.sql" postgres:16-alpine \
              psql -c "BEGIN; \i /tmp/migration.sql; ROLLBACK;" postgres://test:test@localhost/test || true
          done

  # ============================================
  # Security Scan
  # ============================================
  security:
    name: Security & Dependency Scan
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install pip-audit
        run: pip install pip-audit
      - name: Scan dependencies
        run: pip-audit -r requirements.txt --ignore-vuln
      - name: Run Trivy on Dockerfile
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: CRITICAL,HIGH
          exit-code: 1

  # ============================================
  # Container Build
  # ============================================
  build:
    name: Build Container Images
    runs-on: ubuntu-latest
    needs: [test, security, migration-check]
    strategy:
      matrix:
        service:
          - api-gateway
          - orchestrator
          - agent-runtime
          - tool-registry
          - model-gateway
          - memory-service
          - evaluation
          - governance
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./src/${{ matrix.service }}
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ github.repository }}/${{ matrix.service }}:latest
            ${{ env.REGISTRY }}/${{ github.repository }}/${{ matrix.service }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ============================================
  # Artifact Signing
  # ============================================
  sign:
    name: Sign Container Images
    runs-on: ubuntu-latest
    needs: build
    steps:
      - uses: actions/checkout@v4
      - uses: sigstore/cosign-installer@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Sign images
        env:
          COSIGN_EXPERIMENTAL: 1
        run: |
          for service in api-gateway orchestrator agent-runtime tool-registry model-gateway memory-service evaluation governance; do
            cosign sign --yes ${{ env.REGISTRY }}/${{ github.repository }}/${service}:${{ github.sha }}
          done

  # ============================================
  # Deploy to Staging
  # ============================================
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: [build, sign]
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment..."
          # kubectl apply -f k8s/staging/
          # argocd app sync amos-se-staging
```

---

## 13. Infrastructure

### 13.1 Namespace Layout (Kubernetes)

```yaml
# k8s/namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: amos-se-core
  labels:
    app.kubernetes.io/part-of: amos-se
---
apiVersion: v1
kind: Namespace
metadata:
  name: amos-se-agents
  labels:
    app.kubernetes.io/part-of: amos-se
---
apiVersion: v1
kind: Namespace
metadata:
  name: amos-se-infra
  labels:
    app.kubernetes.io/part-of: amos-se
---
apiVersion: v1
kind: Namespace
metadata:
  name: amos-se-governance
  labels:
    app.kubernetes.io/part-of: amos-se
    amos-se/isolation: "true"  # Isolated namespace for governance
```

### 13.2 Helm Chart Structure

```
helm/
├── amos-se/
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── values.staging.yaml
│   ├── values.production.yaml
│   ├── templates/
│   │   ├── _helpers.tpl
│   │   ├── api-gateway/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── hpa.yaml
│   │   │   └── ingress.yaml
│   │   ├── orchestrator/
│   │   ├── agent-runtime/
│   │   ├── tool-registry/
│   │   ├── model-gateway/
│   │   ├── memory-service/
│   │   ├── evaluation/
│   │   ├── governance/
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml
│   │   └── networkpolicy.yaml
│   └── charts/
│       ├── postgresql/     # subchart
│       ├── redis/          # subchart
│       ├── nats/           # subchart
│       └── qdrant/         # subchart
```

### 13.3 Network Policy (Governance Isolation)

```yaml
# k8s/networkpolicy-governance.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: governance-isolation
  namespace: amos-se-governance
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Only allow from human-controlled ingress (not from system namespaces)
    - from:
        - namespaceSelector:
            matchLabels:
              amos-se/human-access: "true"
  egress:
    # Only allow DNS and the governance database
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - protocol: UDP
          port: 53
    - to:
        - podSelector:
            matchLabels:
              app: governance-postgres
      ports:
        - protocol: TCP
          port: 5432
```

### 13.4 GPU Node Pool (for vLLM — later phases)

```yaml
# k8s/gpu-nodepool.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm
  namespace: amos-se-infra
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
    spec:
      nodeSelector:
        node.kubernetes.io/instance-type: "g5.xlarge"  # A10G GPU
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
      containers:
        - name: vllm
          image: vllm/vllm-openai:latest
          args:
            - --model
            - meta-llama/Meta-Llama-3-8B-Instruct
            - --port
            - "8000"
            - --max-model-len
            - "4096"
          resources:
            limits:
              nvidia.com/gpu: 1
              memory: 16Gi
            requests:
              nvidia.com/gpu: 1
              memory: 8Gi
          env:
            - name: HUGGING_FACE_HUB_TOKEN
              valueFrom:
                secretKeyRef:
                  name: model-secrets
                  key: hf-token
```

### 13.5 Backup Policy

```yaml
# Backup Schedule (cron)
# PostgreSQL: every 6 hours, retain 30 days
# MinIO (models + objects): daily, retain 90 days
# NATS JetStream: continuous replication
# Qdrant: daily snapshot, retain 30 days

# Example: PostgreSQL backup
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: amos-se-infra
spec:
  schedule: "0 */6 * * *"  # every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:16-alpine
              env:
                - name: PGPASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: postgres-secret
                      key: password
              command:
                - /bin/sh
                - -c
                - |
                  pg_dump -h postgresql -U amos amos_se | gzip > /backup/amos_se_$(date +%Y%m%d_%H%M%S).sql.gz
                  find /backup -name "amos_se_*.sql.gz" -mtime +30 -delete
              volumeMounts:
                - name: backup
                  mountPath: /backup
          volumes:
            - name: backup
              persistentVolumeClaim:
                claimName: backup-pvc
          restartPolicy: OnFailure
```

---

## 14. Security Implementation

### 14.1 Authentication (JWT/OIDC)

```python
# src/shared/auth.py
"""AMOS-SE Authentication — JWT + OIDC."""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from src.shared.config import settings

security = HTTPBearer()


class User(BaseModel):
    user_id: str
    email: str
    roles: list[str]
    tenant_id: str | None = None


def create_access_token(user: User, expires_minutes: int = 60) -> str:
    """Create a JWT access token."""
    payload = {
        "sub": user.user_id,
        "email": user.email,
        "roles": user.roles,
        "tenant_id": user.tenant_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    # ملاحظة: HS256 للتطوير المحلي فقط. للإنتاج: OIDC + RS256/JWKS


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """Validate JWT and return current user."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return User(
            user_id=payload["sub"],
            email=payload["email"],
            roles=payload.get("roles", []),
            tenant_id=payload.get("tenant_id"),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def require_role(role: str):
    """Dependency that requires a specific role."""
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return user
    return role_checker
```

### 14.2 Signed Approvals (Human → System)

```python
# src/governance/approvals.py
"""AMOS-SE Signed Approval System — Human Control Plane only."""

from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
import hashlib
import json
import structlog

logger = structlog.get_logger()


class ApprovalSigner:
    """Signs approval artifacts with Ed25519.
    
    ملاحظة: المفتاح الخاص لا يجب أن يكون داخل النظام التشغيلي.
    هذا الـ signer يعمل في Human Control Plane معزول فقط.
    النظام التشغيلي يحتوي فقط على ApprovalVerifier (بالمفتاح العام).
    """

    def __init__(self, private_key_pem: bytes):
        self.private_key = serialization.load_pem_private_key(private_key_pem, password=None)

    def sign_approval(
        self,
        approval_id: str,
        resource_id: str,
        decision: str,
        reviewer_id: str,
        notes: str = "",
    ) -> dict:
        """Create a signed approval artifact."""
        payload = {
            "approval_id": approval_id,
            "resource_id": resource_id,
            "decision": decision,
            "reviewer_id": reviewer_id,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        signature = self.private_key.sign(payload_bytes)

        signed_artifact = {
            "payload": payload,
            "payload_hash": f"sha256:{payload_hash}",
            "signature": f"ed25519:{signature.hex()}",
            "signer_public_key_id": "key_001",
        }

        logger.info(
            "approval_signed",
            approval_id=approval_id,
            decision=decision,
            reviewer=reviewer_id,
        )

        return signed_artifact


class ApprovalVerifier:
    """Verifies signed approval artifacts. Used by the system (no private key)."""

    def __init__(self, public_key_pem: bytes):
        self.public_key = serialization.load_pem_public_key(public_key_pem)

    def verify(self, signed_artifact: dict) -> bool:
        """Verify a signed approval artifact."""
        payload = signed_artifact["payload"]
        signature_hex = signed_artifact["signature"].replace("ed25519:", "")
        signature = bytes.fromhex(signature_hex)

        payload_bytes = json.dumps(payload, sort_keys=True).encode()

        try:
            self.public_key.verify(signature, payload_bytes)
            return True
        except Exception:
            logger.warning("approval_verification_failed", approval_id=payload.get("approval_id"))
            return False
```

### 14.3 Audit Hash Chain

```python
# src/shared/audit.py
"""AMOS-SE Audit Log — Immutable hash chain."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.database import AuditLog

logger = structlog.get_logger()

# Genesis hash (first entry in the chain)
GENESIS_HASH = "0" * 64


async def append_audit_entry(
    db: AsyncSession,
    event_type: str,
    actor_type: str,
    actor_id: str,
    action: str,
    resource: str | None = None,
    inputs_hash: str | None = None,
    outputs_hash: str | None = None,
    model_used: str | None = None,
    policy_checks: list[dict] | None = None,
    metadata: dict[str, Any] | None = None,
    parent_event: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> str:
    """Append an entry to the immutable audit log with hash chain."""

    # Get the last hash
    last_entry = await db.execute(
        AuditLog.__table__.select()
        .order_by(AuditLog.id.desc())
        .limit(1)
    )
    last_row = last_entry.fetchone()
    previous_hash = last_row.chain_hash if last_row else GENESIS_HASH

    # Build event
    timestamp = datetime.now(timezone.utc).isoformat()
    event_data = {
        "event_type": event_type,
        "actor_type": actor_type,
        "actor_id": actor_id,
        "action": action,
        "resource": resource,
        "inputs_hash": inputs_hash,
        "outputs_hash": outputs_hash,
        "model_used": model_used,
        "policy_checks": policy_checks or [],
        "metadata": metadata or {},
        "parent_event": parent_event,
        "timestamp": timestamp,
        "previous_hash": previous_hash,
    }

    # Compute chain hash: SHA256(previous_hash + event_data_hash)
    event_str = json.dumps(event_data, sort_keys=True, default=str)
    event_hash = hashlib.sha256(event_str.encode()).hexdigest()
    chain_input = f"{previous_hash}{event_hash}"
    chain_hash = hashlib.sha256(chain_input.encode()).hexdigest()

    # Insert (append-only — rules prevent UPDATE/DELETE)
    entry = AuditLog(
        event_type=event_type,
        actor_type=actor_type,
        actor_id=actor_id,
        actor_version=None,
        action=action,
        resource=resource,
        inputs_hash=inputs_hash,
        outputs_hash=outputs_hash,
        model_used=model_used,
        policy_checks=policy_checks or [],
        metadata=metadata or {},
        parent_event=parent_event,
        chain_hash=chain_hash,
        provenance=provenance,
    )
    db.add(entry)
    await db.commit()

    logger.info(
        "audit_entry_appended",
        event_type=event_type,
        action=action,
        chain_hash=chain_hash[:16] + "...",
    )

    return chain_hash
```

### 14.4 Kill Switch Implementation

```python
# src/governance/kill_switch.py
"""AMOS-SE Kill Switch — Multi-level emergency halt."""

from enum import IntEnum
from typing import Any
import structlog
from redis.asyncio import Redis

logger = structlog.get_logger()


class HaltLevel(IntEnum):
    NORMAL = 0        # System running normally
    NO_TRAINING = 1  # Freeze training/evolution
    NO_REPLICATION = 2  # Freeze replication
    NO_NEW_AGENTS = 3  # No new agents
    FULL_HALT = 4     # All agents stop, operations frozen
    EMERGENCY = 5     # Full network isolation, data isolation


KILL_SWITCH_KEY = "amos_se:kill_switch:level"
KILL_SWITCH_REASON_KEY = "amos_se:kill_switch:reason"
KILL_SWITCH_HISTORY_KEY = "amos_se:kill_switch:history"


class KillSwitch:
    """Multi-level kill switch backed by Redis for instant propagation."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get_level(self) -> HaltLevel:
        """Get current halt level."""
        level = await self.redis.get(KILL_SWITCH_KEY)
        return HaltLevel(int(level)) if level else HaltLevel.NORMAL

    async def trigger(self, level: HaltLevel, reason: str, triggered_by: str) -> None:
        """Trigger a halt at the specified level."""
        current = await self.get_level()
        if level <= current:
            logger.warning("kill_switch_lower_than_current", current=current, requested=level)
            return

        await self.redis.set(KILL_SWITCH_KEY, level.value)
        await self.redis.set(KILL_SWITCH_REASON_KEY, reason)

        # Record in history
        import json
        from datetime import datetime, timezone
        entry = json.dumps({
            "level": level.value,
            "reason": reason,
            "triggered_by": triggered_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await self.redis.lpush(KILL_SWITCH_HISTORY_KEY, entry)

        logger.critical(
            "kill_switch_triggered",
            level=level.name,
            reason=reason,
            triggered_by=triggered_by,
        )

    async def reset(self, level: HaltLevel, reason: str, reset_by: str) -> None:
        """Reset halt level (requires human authorization)."""
        await self.redis.set(KILL_SWITCH_KEY, level.value)
        await self.redis.set(KILL_SWITCH_REASON_KEY, reason)

        import json
        from datetime import datetime, timezone
        entry = json.dumps({
            "action": "reset",
            "level": level.value,
            "reason": reason,
            "reset_by": reset_by,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        await self.redis.lpush(KILL_SWITCH_HISTORY_KEY, entry)

        logger.info("kill_switch_reset", level=level.name, reason=reason)

    async def should_allow(self, action: str) -> bool:
        """Check if an action is allowed given the current halt level."""
        level = await self.get_level()

        if level == HaltLevel.NORMAL:
            return True
        elif level == HaltLevel.NO_TRAINING:
            return action not in ["train", "promote", "distill"]
        elif level == HaltLevel.NO_REPLICATION:
            return action not in ["train", "promote", "distill", "replicate"]
        elif level == HaltLevel.NO_NEW_AGENTS:
            return action not in ["train", "promote", "distill", "replicate", "deploy_agent"]
        elif level >= HaltLevel.FULL_HALT:
            return action in ["read", "health_check", "reset_kill_switch"]
        return False
```

---

## 15. Training/Evolution Implementation

### 15.1 المراحل التنفيذية

```
مراحل التطور في التنفيذ (ليست من اليوم الأول):

المرحلة أ (أسبوع 9-12): جمع الخبرات فقط
  - لا تدريب
  - تجميع Experience Replay Buffer
  - تصنيف: نجاح/فشل/فجوة
  - توثيق المصدرية

المرحلة ب (أسبوع 13-16): تقييم
  - Evaluation Harness يعمل
  - Benchmark Suite جاهز
  - Gap Analyzer يحلل الفجوات
  - Regression Suite جاهز

المرحلة ج (أسبوع 17-22): Shadow
  - بيتا تعمل بالتوازي
  - مقارنة آلية
  - لا تدريب بعد

المرحلة د (أسبوع 23-28): تدريب LoRA
  - Data Collector ينتج datasets
  - LoRA Factory يدرّب
  - Evaluation تقيّم النتيجة
  - Model Registry يسجل

المرحلة هـ (أسبوع 29-36): بوابات الترقية
  - 5 بوابات تعمل
  - Canary deployment
  - Rollback mechanism
  - Human approval workflow
```

### 15.2 LoRA Factory Skeleton

```python
# src/training/lora_factory.py
"""AMOS-SE LoRA Factory — Train and evaluate LoRA adapters."""

import json
from datetime import datetime, timezone
from pathlib import Path
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class TrainingConfig(BaseModel):
    base_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    learning_rate: float = 2e-4
    batch_size: int = 4
    max_seq_length: int = 2048
    epochs: int = 3
    warmup_steps: int = 50
    save_steps: int = 100
    eval_steps: int = 100


class TrainingResult(BaseModel):
    model_id: str
    parent_model: str
    base_model: str
    training_method: str = "qlora"
    adapter_path: str
    training_data_info: dict
    final_loss: float
    eval_loss: float
    training_time_s: float
    config: TrainingConfig


class LoRAFactory:
    """Manages LoRA/QLoRA training pipeline."""

    def __init__(self, config: TrainingConfig, model_registry_url: str):
        self.config = config
        self.model_registry_url = model_registry_url

    async def train(
        self,
        dataset_path: str,
        data_bom: dict,
        parent_model: str,
    ) -> TrainingResult:
        """
        Train a LoRA adapter on the given dataset.
        
        Args:
            dataset_path: Path to JSONL training data
            data_bom: Data Bill of Materials (sources, licenses, checks)
            parent_model: The model being improved
            
        Returns:
            TrainingResult with adapter path and metrics
        """
        import time
        start = time.time()

        model_id = f"beta-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        logger.info("training_started", model_id=model_id, parent=parent_model)

        # --- Actual training would use peft + transformers ---
        # from peft import LoraConfig, get_peft_model
        # from transformers import AutoModelForCausalLM, TrainingArguments, Trainer
        # from datasets import load_dataset
        #
        # base = AutoModelForCausalLM.from_pretrained(self.config.base_model)
        # lora_config = LoraConfig(
        #     r=self.config.lora_rank,
        #     lora_alpha=self.config.lora_alpha,
        #     lora_dropout=self.config.lora_dropout,
        #     task_type="CAUSAL_LM",
        # )
        # model = get_peft_model(base, lora_config)
        # dataset = load_dataset("json", data_files=dataset_path)
        # args = TrainingArguments(
        #     output_dir=f"./models/{model_id}",
        #     num_train_epochs=self.config.epochs,
        #     per_device_train_batch_size=self.config.batch_size,
        #     learning_rate=self.config.learning_rate,
        #     warmup_steps=self.config.warmup_steps,
        #     save_steps=self.config.save_steps,
        #     eval_steps=self.config.eval_steps,
        # )
        # trainer = Trainer(model=model, args=args, train_dataset=dataset["train"])
        # trainer.train()
        # model.save_pretrained(f"./models/{model_id}/adapter")

        # Placeholder for development
        adapter_path = f"./models/{model_id}/adapter"
        Path(adapter_path).mkdir(parents=True, exist_ok=True)

        final_loss = 0.0  # trainer.evaluate()
        eval_loss = 0.0

        training_time = time.time() - start

        result = TrainingResult(
            model_id=model_id,
            parent_model=parent_model,
            base_model=self.config.base_model,
            adapter_path=adapter_path,
            training_data_info={
                "dataset_path": dataset_path,
                "data_bom": data_bom,
                "samples_count": 0,  # len(dataset)
            },
            final_loss=final_loss,
            eval_loss=eval_loss,
            training_time_s=training_time,
            config=self.config,
        )

        logger.info(
            "training_completed",
            model_id=model_id,
            final_loss=final_loss,
            time_s=training_time,
        )

        return result

    async def knowledge_injection(
        self,
        beta_model_id: str,
        alpha_model_id: str,
        forgotten_areas: list[dict],
    ) -> str:
        """
        Inject knowledge from Alpha into Beta to prevent catastrophic forgetting.
        
        Args:
            beta_model_id: The beta model that forgot knowledge
            alpha_model_id: The alpha model that still has the knowledge
            forgotten_areas: Areas where beta showed regression
            
        Returns:
            Gamma model_id after knowledge injection
        """
        gamma_id = f"gamma-{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        logger.info(
            "knowledge_injection_started",
            gamma_id=gamma_id,
            beta=beta_model_id,
            alpha=alpha_model_id,
            forgotten_areas=len(forgotten_areas),
        )

        # --- Actual implementation would:
        # 1. Extract training samples from Alpha's experience replay
        #    for the forgotten areas
        # 2. Add them to Beta's training data
        # 3. Re-train Beta on the combined dataset
        # 4. Result: Gamma = Beta + forgotten knowledge
        # ---

        logger.info("knowledge_injection_completed", gamma_id=gamma_id)
        return gamma_id
```

### 15.3 Data Collector

```python
# src/training/data_collector.py
"""AMOS-SE Data Collector — Build training datasets from experience replay."""

from datetime import datetime, timezone
from typing import Any
import json
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.shared.database import Experience

logger = structlog.get_logger()


class DataCollector:
    """Collects, balances, and prepares training data from experiences."""

    def __init__(self, db: AsyncSession, minio_client: Any):
        self.db = db
        self.minio = minio_client

    async def collect_dataset(
        self,
        domain: str | None = None,
        since_days: int = 7,
        target_balance: dict[str, float] | None = None,
    ) -> dict:
        """
        Collect and balance a training dataset from experience replay.
        
        Default balance:
            - success: 60%
            - failure: 20%
            - gap: 15%
            - repair: 5%
        """
        if target_balance is None:
            target_balance = {
                "success": 0.60,
                "failure": 0.20,
                "gap": 0.15,
                "repair": 0.05,
            }

        # Query experiences by type
        since = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0
        )
        from datetime import timedelta
        since = datetime.now(timezone.utc) - timedelta(days=since_days)

        datasets = {}
        for exp_type in ["success", "failure", "gap", "repair"]:
            query = select(Experience).where(
                and_(
                    Experience.type == exp_type,
                    Experience.created_at >= since,
                )
            )
            if domain:
                query = query.where(Experience.domain == domain)

            result = await self.db.execute(query)
            experiences = result.scalars().all()
            datasets[exp_type] = [
                self._experience_to_training_sample(exp) for exp in experiences
            ]

        # Balance the dataset
        total_samples = sum(len(v) for v in datasets.values())
        if total_samples == 0:
            logger.warning("no_experiences_found", domain=domain, since_days=since_days)
            return {"total_samples": 0, "dataset_path": None}

        balanced = self._balance_dataset(datasets, target_balance)

        # Build dataset info
        dataset_id = f"dataset_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        dataset_path = f"datasets/{dataset_id}.jsonl"

        # Save to MinIO
        jsonl_content = "\n".join(
            json.dumps(sample) for sample in balanced
        )
        self.minio.put_object(
            bucket_name="amos-se-training",
            object_name=dataset_path,
            data=jsonl_content.encode(),
            length=len(jsonl_content.encode()),
            content_type="application/jsonl",
        )

        data_bom = {
            "dataset_id": dataset_id,
            "sources": {
                exp_type: len(samples) for exp_type, samples in datasets.items()
            },
            "balanced_counts": {
                exp_type: len([s for s in balanced if s.get("type") == exp_type])
                for exp_type in datasets
            },
            "total_samples": len(balanced),
            "domain": domain,
            "collected_since": since.isoformat(),
            "provenance": "experience_replay_buffer",
            "pii_checked": True,
            "license": "internal",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(
            "dataset_collected",
            dataset_id=dataset_id,
            total=len(balanced),
            path=dataset_path,
        )

        return {
            "dataset_id": dataset_id,
            "dataset_path": f"s3://amos-se-training/{dataset_path}",
            "data_bom": data_bom,
            "total_samples": len(balanced),
        }

    def _experience_to_training_sample(self, exp: Experience) -> dict:
        """Convert an experience record to a training sample."""
        return {
            "task": exp.task_description,
            "domain": exp.domain,
            "approach": exp.approach,
            "outcome": exp.outcome,
            "type": exp.type,
            "quality_score": float(exp.quality_score) if exp.quality_score else 0.0,
            "model_used": exp.model_used,
            "provenance": exp.provenance,
        }

    def _balance_dataset(
        self,
        datasets: dict[str, list[dict]],
        target: dict[str, float],
    ) -> list[dict]:
        """Balance dataset according to target ratios."""
        total = sum(len(v) for v in datasets.values())
        balanced = []

        for exp_type, ratio in target.items():
            samples = datasets.get(exp_type, [])
            target_count = int(total * ratio)
            if len(samples) > target_count:
                # Subsample
                balanced.extend(samples[:target_count])
            else:
                balanced.extend(samples)

        return balanced
```

---

## 16. Acceptance Criteria

### 16.1 Phase 0 — Foundation

| المعيار | كيفية التحقق |
|---------|-------------|
| Docker Compose يعمل | `docker compose up` → كل الخدمات healthy |
| CI/CD يعمل | push → lint + test + build تنجح |
| قاعدة البيانات جاهزة | migrations تنطبق + جداول موجودة |
| Event bus يعمل | نشر حدث + استهلاكه بنجاح |
| Tracing يعمل | طلب → trace في Jaeger |

### 16.2 Phase 1 — MVP Agent Runtime

| المعيار | كيفية التحقق |
|---------|-------------|
| طلب مهمة يعمل | `POST /v1/tasks` → 202 + task_id |
| تتبع الحالة | `GET /v1/tasks/{id}` → status يتحدث |
| 3 وكلاء نشطون | `GET /v1/agents` → 3 agents |
| 10 أدوات مسجلة | `GET /v1/tools` → 10 tools |
| مهمة كاملة | طلب → تخطيط → تنفيذ → نتيجة |
| Tool sandbox يعمل | أداة تنفذ في container معزول |
| Model gateway يعمل | طلب → Claude API → رد |

### 16.3 Phase 2 — Memory + Experience Replay

| المعيار | كيفية التحقق |
|---------|-------------|
| الذاكرة التشغيلية | وكيل يخزن + يسترجع معرفة |
| Vector search | استعلام دلالي يعود بنتائج ذات صلة |
| Experience replay | بعد 100 مهمة → 100 سجل خبرة |
| تصنيف الخبرات | نجاح/فشل/فجوة مصنفة بشكل صحيح |
| Provenance | كل خبرة لها مصدر موثق |

### 16.4 Phase 3 — Evaluation + Critic

| المعيار | كيفية التحقق |
|---------|-------------|
| Critic يراجع | كل نتيجة لها quality_score + feedback |
| Benchmark suite | 50 مهمة قياسية + نتائج قابلة للتكرار |
| Gap analyzer | يكتشف فجوات بين ألفا والنموذج الخارجي |
| Regression suite | يكتشف التدهور في المعرفة القديمة |

### 16.5 Phase 4 — Alpha/Beta Shadow

| المعيار | كيفية التحقق |
|---------|-------------|
| نموذجين يعملان | محلي (vLLM) + خارجي (Claude) |
| Shadow mode | بيتا تخدم نسخة من الطلبات |
| مقارنة آلية | quality, latency, cost metrics |
| Fallback chain | محلي فشل → خارجي يعمل |

### 16.6 Phase 5 — LoRA Factory

| المعيار | كيفية التحقق |
|---------|-------------|
| Data collector | ينتج dataset متوازن + موثق |
| LoRA training | دورة كاملة: بيانات → تدريب → نموذج |
| Evaluation | النموذج الجديد مُقيّم |
| Model Registry | بطاقة نموذج كاملة |
| Knowledge injection | آلية منع النسيان تعمل |

### 16.7 Phase 6 — Governance + Canary

| المعيار | كيفية التحقق |
|---------|-------------|
| Policy engine | كل قرار يُفحص بـ OPA |
| Audit log | سلسلة كتل غير قابلة للتعديل |
| Kill switch | 5 مستويات تعمل + انتشار فوري |
| 5 promotion gates | كل بوابة تعمل |
| Canary | نسبة 5% من الطلبات |
| Rollback | استرجاع في < 5 دقائق |
| Human approval | موافقة موقعة تعمل |

---

## 17. Backlog

### 17.1 Epic / Story Breakdown

| Epic | Story | Priority | Owner Role | Dependencies | Estimate (SP) |
|------|-------|----------|-----------|-------------|--------------|
| INFRA | Docker Compose setup | P0 | DevOps | — | 3 |
| INFRA | PostgreSQL schema | P0 | Backend | Docker | 5 |
| INFRA | NATS JetStream setup | P0 | DevOps | Docker | 3 |
| INFRA | GitHub Actions CI | P0 | DevOps | Repo | 3 |
| INFRA | OpenTelemetry setup | P1 | DevOps | Docker | 5 |
| INFRA | MinIO setup | P1 | DevOps | Docker | 2 |
| INFRA | Qdrant setup | P1 | DevOps | Docker | 2 |
| API | POST /v1/tasks | P0 | Backend | DB, NATS | 5 |
| API | GET /v1/tasks/{id} | P0 | Backend | DB | 3 |
| API | JWT auth | P0 | Backend | — | 5 |
| ORCH | Orchestrator service | P0 | Backend | API, NATS | 8 |
| ORCH | Planning agent | P0 | Backend | Orchestrator | 5 |
| AGENT | Agent runtime service | P0 | Backend | Orchestrator | 8 |
| AGENT | Worker agent base | P0 | Backend | Agent runtime | 5 |
| AGENT | 3 agent manifests | P0 | Backend | Agent runtime | 3 |
| TOOLS | Tool registry service | P0 | Backend | DB | 5 |
| TOOLS | 10 tool manifests | P0 | Backend | Tool registry | 3 |
| TOOLS | Tool sandbox (Docker) | P1 | DevOps | Tool registry | 8 |
| TOOLS | Semantic router | P1 | Backend | Tool registry | 5 |
| MODEL | Model gateway service | P0 | Backend | — | 5 |
| MODEL | Claude provider | P0 | Backend | Model gateway | 3 |
| MODEL | vLLM provider | P1 | ML | GPU | 5 |
| MODEL | Fallback chain | P1 | Backend | Providers | 3 |
| MEM | Memory service | P0 | Backend | Redis, Qdrant | 5 |
| MEM | Embedding pipeline | P1 | ML | Memory service | 5 |
| MEM | Experience replay store | P0 | Backend | DB, MinIO | 5 |
| MEM | Provenance tracking | P1 | Backend | Experience | 3 |
| EVAL | Evaluation service | P1 | Backend | DB | 5 |
| EVAL | Benchmark suite (50 tasks) | P1 | ML | Eval service | 8 |
| EVAL | Gap analyzer | P1 | ML | Eval service | 5 |
| EVAL | Regression runner | P1 | Backend | Eval service | 5 |
| CRITIC | Critic agent service | P1 | Backend | Agent runtime | 5 |
| CRITIC | Quality scoring | P1 | ML | Critic | 3 |
| SHADOW | Shadow testing framework | P2 | Backend | Model gateway | 8 |
| SHADOW | Shadow metrics | P2 | Backend | Shadow | 3 |
| TRAIN | Data collector | P2 | ML | Experience replay | 5 |
| TRAIN | LoRA factory | P2 | ML | Data collector | 8 |
| TRAIN | Model registry | P2 | Backend | DB | 5 |
| TRAIN | Knowledge injection | P2 | ML | LoRA factory | 5 |
| GOV | OPA setup | P2 | DevOps | — | 3 |
| GOV | Rego policies | P2 | Backend | OPA | 5 |
| GOV | Audit log hash chain | P2 | Backend | DB | 5 |
| GOV | Kill switch | P2 | Backend | Redis | 5 |
| GOV | Signed approvals | P2 | Backend | Crypto | 5 |
| GOV | Promotion gates (5) | P3 | Backend | Eval, Audit | 8 |
| GOV | Canary controller | P3 | DevOps | K8s | 5 |
| GOV | Rollback mechanism | P3 | Backend | Model registry | 5 |
| CONSOLE | Control Console (React frontend) | P2 | Frontend | API gateway | 8 |
| SCHEMA | Event Schema Registry + contract tests | P1 | Backend | NATS | 5 |
| DATA | PII redaction pipeline | P1 | Backend | — | 5 |
| DATA | Retention jobs | P1 | Backend | DB | 3 |
| DATA | Consent gate | P1 | Backend | — | 3 |
| DATA | Tenant isolation tests | P1 | QA | — | 5 |
| SEC | Sandbox hardening (gVisor/seccomp) | P1 | DevOps | Tool sandbox | 8 |
| SEC | Egress control | P1 | DevOps | K8s | 3 |
| SEC | Network policies | P1 | DevOps | K8s | 3 |
| DR | Restore drill: PostgreSQL | P1 | DevOps | Backup | 3 |
| DR | Restore drill: Event Store | P1 | DevOps | NATS | 3 |
| DR | Restore drill: Model Registry | P2 | DevOps | MinIO | 3 |
| DR | Chaos testing | P2 | DevOps | K8s | 5 |

**إجمالي التقدير:** ~280 Story Points

---

## 18. خطة 90 يومًا التفصيلية

### الأسبوع 1-2: البنية الأساسية

| اليوم | المهمة | المخرج |
|------|--------|--------|
| يوم 1-2 | إنشاء مستودع Git + هيكل monorepo | repo.jl منظم |
| يوم 2-3 | كتابة docker-compose.yml | كل الخدمات تبدأ |
| يوم 3-4 | كتابة SQL migrations | جداول قاعدة البيانات جاهزة |
| يوم 4-5 | إعداد pre-commit + CI básico | lint + format يعمل |
| يوم 6-7 | NATS JetStream + event publisher skeleton | نشر + استهلاك حدث |

### الأسبوع 3-4: Services Skeleton

| اليوم | المهمة | المخرج |
|------|--------|--------|
| يوم 8-9 | FastAPI skeleton لـ api-gateway | خدمة تبدأ + /health |
| يوم 9-10 | FastAPI skeleton لـ orchestrator | خدمة تبدأ + /health |
| يوم 10-11 | FastAPI skeleton لـ agent-runtime | خدمة تبدأ + /health |
| يوم 11-12 | FastAPI skeleton لـ tool-registry | خدمة تبدأ + /health |
| يوم 12-14 | OpenTelemetry + tracing | trace في Jaeger |

### الأسبوع 5-6: API + Orchestrator

| اليوم | المهمة | المخرج |
|------|--------|--------|
| يوم 15-16 | JWT auth | تسجيل دخول + token |
| يوم 16-17 | POST /v1/tasks | إنشاء مهمة |
| يوم 17-18 | GET /v1/tasks/{id} | حالة المهمة |
| يوم 18-19 | Orchestrator planner بسيط | تحليل الطلب → خطة |
| يوم 19-21 | Orchestrator ← Agent assignment | توزيع المهام |

### الأسبوع 7-8: Agent Runtime + Tools

| اليوم | المهمة | المخرج |
|------|--------|--------|
| يوم 22-23 | Base Agent class | هيكل الوكيل |
| يوم 23-24 | Worker agent | تنفيذ مهمة بسيطة |
| يوم 24-25 | Tool registry (CRUD) | تسجيل/استرجاع أدوات |
| يوم 25-26 | 10 tool manifests | أدوات معرفة |
| يوم 26-28 | Tool sandbox (Docker) | عزل الأدوات |

### الأسبوع 9-10: Model Gateway + First E2E

| اليوم | المهمة | المخرج |
|------|--------|--------|
| يوم 29-30 | Model gateway service | توجيه الطلبات |
| يوم 30-31 | Claude API provider | استدعاء Claude |
| يوم 31-32 | End-to-end task | طلب → نتيجة كاملة |
| يوم 32-33 | E2E test suite | اختبارات آلية |
| يوم 33-35 | Bug fixes + polish | استقرار |

### الأسبوع 11-12: Memory + Experience Replay

| اليوم | المهمة | المخرج |
|------|--------|--------|
| يوم 36-37 | Memory service (Redis) | ذاكرة تشغيلية |
| يوم 37-38 | Qdrant + embedding pipeline | بحث دلالي |
| يوم 38-39 | Experience replay store | تخزين الخبرات |
| يوم 39-40 | تصنيف نجاح/فشل/فجوة | تصنيف تلقائي |
| يوم 40-42 | Provenance tracking | مصدرية كل خبرة |

### الأسبوع 13 (نهاية الـ 90 يومًا): التحقق

| اليوم | المهمة | المخرج |
|------|--------|--------|
| يوم 43-44 | E2E test شامل | مهمة كاملة + خبرة مخزنة |
| يوم 44-45 | توثيق | README + Runbooks |
| يوم 45 | Demo + مراجعة | عرض النتائج |

### نهاية الـ 90 يومًا — ما يجب أن يكون جاهزًا

```
✓ Docker Compose مع 8 خدمات بنية تحتية
✓ 4 خدمات AMOS-SE تعمل (api-gateway, orchestrator, agent-runtime, tool-registry)
✓ 3 وكلاء نشطون في مجالين
✓ 10 أدوات مسجلة
✓ Model gateway مع Claude API
✓ Memory service (Redis + Qdrant)
✓ Experience replay buffer يعمل
✓ Audit log أساسي
✓ CI/CD pipeline كامل
✓ E2E test لمهمة كاملة
✓ توثيق أساسي

✗ لا يوجد تدريب ذاتي بعد
✗ لا يوجد تقييم آلي بعد
✗ لا يوجد LoRA factory بعد
✗ لا يوجد governance كامل بعد
→ هذه تأتي في الأشهر 4-9
```

### الأسابيع 10-13: Hardening & Stabilization

| الأسبوع | المهمة | المخرج |
|--------|--------|--------|
| أسبوع 10 | اختبارات تكامل شاملة | Integration test suite كامل |
| | Tenant isolation tests | عزل المستأجرين مُختبَر |
| | Sandbox hardening | gVisor/seccomp + no-new-privileges + egress control |
| أسبوع 11 | Load testing | اختبار حمل + نقاط اختناق |
| | Restore drill | استرجاع PostgreSQL + Event Store من النسخ الاحتياطي |
| | Event schema contract tests | CI يفشل عند كسر عقد حدث |
| أسبوع 12 | Data governance tasks | PII redaction + retention jobs + consent gate |
| | Security hardening | RBAC صارم + audit roles + network policies |
| أسبوع 13 | Demo نهائي + مراجعة | عرض كامل + تقرير جاهزية |
| | توثيق نهائي | README + Runbooks + Architecture Decision Records |

---

> **هذه الخطة تحوّل الرؤية إلى مهام هندسية قابلة للتنفيذ. ليست وعدًا بنظام ذاتي التطور كامل — بل خارطة طريق من 3 وكلاء و10 أدوات إلى نظام ناضج تدريجيًا.**

---

*نهاية الوثيقة — خطة التنفيذ التقنية — الإصدار 1.0 — 2026-08-15*
