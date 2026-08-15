# -*- coding: utf-8 -*-
"""مولّد هويات الوكلاء المستوردين — المرحلة 1 (السحب).
ينشئ لكل وكيل: مجلد خاص به + identity.md + upstream.yaml
وينشئ سجلاً مركزياً: agents/registry/imported_citizens.yaml
ولا ينسخ أي كود مصدر (منع تضخم المستودع)."""
import os
import re
import hashlib
import yaml
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(ROOT))  # AMOS-Fedration
IDENTITIES_BASE = os.path.join(REPO, "agents", "identities", "imported")
REGISTRY_FILE = os.path.join(REPO, "agents", "registry", "imported_citizens.yaml")
IMPORT_DATE = date.today().isoformat()

# بيانات الوكلاء
import sys
sys.path.insert(0, os.path.dirname(__file__))
from imported_agents_data import AGENTS, DOMAIN_PATH


def slugify(name: str) -> str:
    """تحويل اسم الوكيل إلى slug آمن للمسار."""
    s = name.lower()
    # إزالة الأقواس ومحتواها
    s = re.sub(r"\s*\(.*?\)\s*", "", s)
    # استبدال الأحرف غير الحرفية
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if not s:
        s = "agent"
    return s


def agent_id(domain: str, slug: str) -> str:
    short = domain.replace("states-", "").replace("federal-", "fed")
    return f"imported-{short}-{slug}"


def capabilities_for(spec: str) -> list:
    """قدرات أولية مقترحة حسب التخصص."""
    base = {
        "orchestration": ["multi_agent_coordination", "task_decomposition", "tool_routing"],
        "coding": ["code_generation", "code_review", "refactoring", "debugging"],
        "browser-automation": ["web_navigation", "form_filling", "data_extraction"],
        "research": ["information_retrieval", "synthesis", "citation"],
        "memory": ["long_term_storage", "semantic_search", "context_management"],
    }
    return base.get(spec, [spec.replace("-", "_")])


def budget_for(domain: str) -> dict:
    """ميزانية أولية محافظة لكل المرشحين."""
    if domain == "federal-executive":
        return {"daily_token_limit": 20000, "daily_cost_limit": 1.00, "max_concurrent_tasks": 2}
    return {"daily_token_limit": 10000, "daily_cost_limit": 0.50, "max_concurrent_tasks": 1}


def write_identity_md(path, agent_id, name, url, category, domain_path, spec):
    caps = capabilities_for(spec)
    caps_str = "\n".join(f"- {c}" for c in caps)
    content = f"""# هوية الوكيل المستورد: {name}

## التعريف
- الاسم: {name}
- المعرّف: {agent_id}
- النوع: external_agent_framework
- المصدر: {url}
- التصنيف الأصلي: {category}
- المكان المخصص: {domain_path}
- التخصص الدقيق: {spec}
- الحالة: imported_candidate
- تاريخ السحب: {IMPORT_DATE}

## الهدف
دمج هذا الإطار/الوكيل كمورد مستورد داخل AMOS-Federation حسب تخصصه، كموظف مرشح يخضع
للفحص والتدريب والاعتماد قبل منحه أي صلاحية تشغيل إنتاجية. هذا يحقق مبدأ
"المراقبة قبل الثقة" والموافقة المشروطة.

## الدور المقترح
- المجال: {domain_path}
- الوظيفة: {spec}
- الجهة المشرفة: {("federal" if domain_path.startswith("federal") else "state")} supervisor

## القدرات الأولية (مرشحة للتصنيف)
{caps_str}

## الأدوات المسموحة مبدئيًا
- read_repository_metadata
- analyze_documentation
- classify_capabilities
- sandbox_evaluation

## الممنوعات
- لا وصول للأسرار أو مفاتيح API
- لا تعديل مباشر في خدمات الإنتاج
- لا نشر أو دفع كود دون موافقة المالك
- لا تنفيذ أدوات خارج sandbox قبل الاعتماد
- لا صلاحيات حوكمة أو إيقاف أو ترقية ذاتية

## مسار دورة الحياة
imported → classified → sandbox_review → school_training → evaluation → employed | archived

## معايير الاعتماد
- فحص الترخيص (license_status = approved)
- فحص أمني أساسي (security_status = approved)
- تصنيف القدرات
- اجتياز تدريب المدرسة بنسبة ≥ 85%
- موافقة الحوكمة قبل التوظيف الفعلي

## الميزانية الأولية
- daily_token_limit: {budget_for(domain_path.split('/')[0] if '/' in domain_path else domain_path)['daily_token_limit']}
- daily_cost_limit: ${budget_for(domain_path.split('/')[0] if '/' in domain_path else domain_path)['daily_cost_limit']:.2f}
- max_concurrent_tasks: {budget_for(domain_path.split('/')[0] if '/' in domain_path else domain_path)['max_concurrent_tasks']}

## SLA الأولي
- status: candidate
- quality_threshold: 0.85
- escalation_after_failures: 3

## بصمة SHA-256
تُحسب تلقائيًا عند التسجيل النهائي في سجل السكان والاعتماد.
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def write_upstream_yaml(path, agent_id, name, url, category, domain_path, slug):
    data = {
        "id": agent_id,
        "name": name,
        "source_url": url,
        "source_type": "github_repository",
        "original_category": category,
        "assigned_place": domain_path,
        "slug": slug,
        "import_status": "registered",
        "integration_status": "not_integrated",
        "license_status": "pending_review",
        "security_status": "pending_review",
        "pulled_at": IMPORT_DATE,
        "notes": "Imported as a candidate employee; not active until evaluation and governance approval. Source code not vendored to avoid repo bloat.",
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def main():
    os.makedirs(IDENTITIES_BASE, exist_ok=True)
    citizens = []
    seen_ids = set()
    stats = {}
    for (name, url, category, domain, spec) in AGENTS:
        domain_path = DOMAIN_PATH.get(domain, domain)
        slug = slugify(name)
        aid = agent_id(domain, slug)
        # ضمان التفرّد
        base_aid = aid
        n = 2
        while aid in seen_ids:
            aid = f"{base_aid}-{n}"
            n += 1
        seen_ids.add(aid)

        agent_dir = os.path.join(IDENTITIES_BASE, domain, slug)
        os.makedirs(agent_dir, exist_ok=True)
        write_identity_md(os.path.join(agent_dir, "identity.md"), aid, name, url, category, domain_path, spec)
        write_upstream_yaml(os.path.join(agent_dir, "upstream.yaml"), aid, name, url, category, domain_path, slug)

        citizens.append({
            "id": aid,
            "name": name,
            "source_url": url,
            "original_category": category,
            "assigned_place": domain_path,
            "specialty": spec,
            "slug": slug,
            "status": "imported_candidate",
            "import_status": "registered",
            "integration_status": "not_integrated",
            "license_status": "pending_review",
            "security_status": "pending_review",
            "pulled_at": IMPORT_DATE,
        })
        stats[domain] = stats.get(domain, 0) + 1

    registry = {
        "meta": {
            "title": "سجل الوكلاء المستوردين — Imported Citizens Registry",
            "purpose": "تسجيل كل إطار/وكيل خارجي مستورد كموظف مرشح، قبل الفحص والتدريب والاعتماد",
            "owner": "agents/registry",
            "created": IMPORT_DATE,
            "total_imported": len(citizens),
            "stage": "1-sweep",
            "principle": "لا يُمنح أي وكيل مستورد صلاحية تشغيل إنتاجية قبل اجتياز الفحص والتدريب والموافقة",
        },
        "domain_distribution": stats,
        "citizens": citizens,
    }
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(registry, f, allow_unicode=True, sort_keys=False)

    print(f"OK: imported {len(citizens)} agents across {len(stats)} domains")
    print("Distribution:")
    for d, c in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {d}: {c}")
    print(f"Registry: {REGISTRY_FILE}")


if __name__ == "__main__":
    main()
