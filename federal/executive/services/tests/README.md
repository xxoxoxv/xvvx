# tests/

## التعريف
اختبارات وحدات وتكامل خفيف للخدمات التنفيذية دون الحاجة إلى PostgreSQL أو NATS.

## النطاق
تغطي الإعدادات وسلسلة التدقيق والمصادقة والصحة وبوابة الواجهات والمنسق ومخططات الأحداث.

## المالك
federal/executive/services

## تاريخ الإنشاء
2026-08-15

## تاريخ آخر تعديل
2026-08-17

## المحتويات
- `README.md` — بطاقة هوية هذا المجلد (المادة التاسعة)
- `__init__.py` — AMOS-Federation Tests Package
- `conftest.py` — Pytest configuration for AMOS-Federation tests.
- `test_agent_runtime.py` — اختبارات وقت تشغيل الوكلاء
- `test_api_gateway.py` — اختبارات بوابة الواجهات
- `test_auth.py` — اختبارات المصادقة
- `test_benchmark.py` — اختبارات المعيار القياسي ومحلل الفجوات
- `test_common_branches.py` — اختبارات الأفرع للوحدات المشتركة
- `test_config.py` — اختبارات الإعدادات
- `test_control_console.py` — اختبارات منصة التحكم البشري (Phase 7)
- `test_critic.py` — اختبارات خدمة الناقد
- `test_durable_bus_branches.py` — اختبارات الحالات الحدية لـ DurableEventBus
- `test_e2e.py` — اختبارات شاملة من البداية للنهاية (E2E)
- `test_edge_branches.py` — اختبارات أفرع حدية إضافية لرفع تغطية الأفرع فوق 80%
- `test_event_bus.py` — اختبارات نظام الأحداث (Event Bus)
- `test_event_schemas.py` — اختبارات مخططات الأحداث
- `test_expansion.py` — اختبارات التوسع السكاني + التخصص + الجامعات + التقاعد (Phase 11)
- `test_experience.py` — اختبارات خدمة التقييم والخبرات
- `test_federation.py` — اختبارات المؤسسات الفدرالية + الحوكمة الكاملة (Phase 9)
- `test_governance.py` — اختبارات Governance: Policy Engine + Kill Switch + Promotion Gates + Canary
- `test_governance_phase3.py` — اختبارات الحوكمة التأسيسية (Phase 3)
- `test_hash_chain.py` — اختبارات Hash Chain
- `test_health.py` — اختبارات صحة الخدمات
- `test_health_system.py` — اختبارات النظام الصحي المؤسسي للوكلاء (Phase 8)
- `test_inmemory_stores.py` — اختبارات مخازن الذاكرة (In-Memory Stores)
- `test_memory_service.py` — اختبارات خدمة الذاكرة
- `test_model_gateway.py` — اختبارات بوابة النماذج
- `test_model_layer.py` — اختبارات النماذج الحقيقية (Phase 5)
- `test_models.py` — اختبارات النماذج الأساسية
- `test_orchestrator.py` — اختبارات المنسق
- `test_persistence.py` — اختبارات استمرارية البيانات (Persistence)
- `test_phase12_states.py` — AMOS-Federation Phase 12 — Federal States Tests
- `test_phase13_factories.py` — AMOS-Federation Phase 13 — Federal Factories Tests
- `test_phase14_15_learning.py` — AMOS-Federation Phase 14-15 — Learning Loop + Evaluation Tests
- `test_phase16_security.py` — AMOS-Federation Phase 16 — Production Security Tests
- `test_phase17_system_life.py` — AMOS-Federation Phase 17 — System Life + Launch Tests
- `test_phase1_postgres.py` — AMOS-Federation Phase 1 Tests: PostgreSQL Persistence
- `test_phase2_events.py` — AMOS-Federation Phase 2 — Contract Tests
- `test_phase3_governance.py` — AMOS-Federation Phase 3 — Governance Foundation Tests
- `test_phase4_tools.py` — AMOS-Federation Phase 4 — Real Tools Tests
- `test_phase5_models.py` — AMOS-Federation Phase 5 — Real Models Tests
- `test_phase6_population.py` — AMOS-Federation Phase 6 — Population & School Tests
- `test_phase7_health.py` — AMOS-Federation Phase 7-8 — Health, Isolation & Treatment Tests
- `test_population.py` — اختبارات السكان الأوائل (Phase 6)
- `test_real_tools.py` — اختبارات الأدوات الحقيقية (Phase 4)
- `test_shadow.py` — اختبارات Shadow Testing و Cost Tracking
- `test_tool_registry.py` — اختبارات سجل الأدوات
- `test_training.py` — اختبارات Training Service: Data Pipeline + Model Registry
- `test_treasury.py` — اختبارات الخزانة الفدرالية والعملة الرقمية (Phase 10)
