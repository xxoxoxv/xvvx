# خريطة الخدمات

## الهدف
خريطة خدمات الدولة: منفذ كل خدمة ومسؤوليتها وقاعدتها وهدف خدمتها (SLO)، ليُعرف من يفعل ماذا وبأي التزام.

| الخدمة | المنفذ | المسؤولية | DB | SLO |
|--------|--------|----------|------|-----|
| api-gateway | 8000 | استقبال الطلبات + auth | Redis | p99 < 100ms |
| orchestrator | 8001 | التخطيط + توزيع المهام | PostgreSQL | p99 < 500ms |
| agent-runtime | 8002 | تنفيذ الوكلاء | Redis | حسب المهمة |
| tool-registry | 8003 | إدارة الأدوات | PostgreSQL | p99 < 50ms |
| model-gateway | 8004 | توجيه النماذج | Redis | p99 < 5s |
| memory-service | 8005 | الذاكرة | Redis + Qdrant | p99 < 200ms |
| evaluation | 8006 | تقييم النماذج | PostgreSQL | حسب التقييم |
| critic | 8007 | مراجعة النتائج | PostgreSQL | p99 < 10s |
| governance | 8009 | السياسات + Kill Switch | PostgreSQL | p99 < 100ms |
| control-console | 3000 | واجهة الويب | — | — |
