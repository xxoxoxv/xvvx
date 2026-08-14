# خطة 90 يومًا التفصيلية

## الأسبوع 1-2: البنية الأساسية
- إنشاء مستودع Git + هيكل monorepo
- كتابة docker-compose.yml
- كتابة SQL migrations
- إعداد pre-commit + CI
- NATS JetStream + event publisher

## الأسبوع 3-4: Services Skeleton
- FastAPI skeleton لكل خدمة
- OpenTelemetry tracing
- Health checks

## الأسبوع 5-6: API + Orchestrator
- JWT auth
- POST/GET /v1/tasks
- Orchestrator planner

## الأسبوع 7-8: Agent Runtime + Tools
- Base Agent class
- Worker agent
- Tool registry + 10 manifests
- Tool sandbox

## الأسبوع 9-10: Model Gateway + E2E
- Model gateway + Claude API
- First end-to-end task
- E2E test suite

## الأسبوع 11-13: Memory + Hardening
- Memory service (Redis + Qdrant)
- Experience replay store
- Tenant isolation tests
- Sandbox hardening (gVisor/seccomp)
- Restore drills
- Load testing
- Demo نهائي

## نهاية الـ 90 يومًا
✓ Docker Compose مع 8 خدمات
✓ 4 خدمات AMOS-SE تعمل
✓ 3 وكلاء نشطون
✓ 10 أدوات مسجلة
✓ Model gateway + Claude API
✓ Memory + Experience replay
✓ Audit log
✓ CI/CD pipeline

✗ لا تدريب ذاتي بعد → الأشهر 4-9
