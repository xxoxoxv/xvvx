#!/usr/bin/env python3
"""الهدف: ترحيل هوية R4 بسياسة الدليل التاريخي (OPTION 2) — لا هوية بلا دليل.

النطاق: tools/migrations
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-17

R4-G (المراجَع). ما تغيّر عن النسخة الأولى ولماذا
------------------------------------------------

النسخة الأولى من هذا الترحيل كانت تُنشئ هوية كانونية **لكل** صفّ في
`agent_population`. قياس القاعدة الحقيقية (Supabase، PostgreSQL 17) أظهر أن هذا
غير مقبول:

- `agent_population` = 5116 صفًّا، كلها `agent_id` متمايز، لكنها تحمل **24 اسمًا
  متميزًا فقط** لأن `seed_initial_population` نُفِّذ مرارًا؛ فالأغلبية صفوف بذر
  مكرّرة لا هويّات تشغيلية.
- `agents` = 0 صفًّا.
- `EMPLOYABLE_STATUSES` تضمّ `registered`، و5068 من تلك الصفوف حالتها
  `registered`؛ فترحيلها كلها كان سيُدخل 5068 وكيلًا **قابلًا للتوزيع** إلى
  مسار التنفيذ دفعة واحدة.

القرار المعتمد: **OPTION 2 — APPLY ONLY TO ROWS WITH ACTUAL HISTORICAL
EVIDENCE.** الصفّ لا يُرحَّل إلا إذا أثبت سجلّ النظام أنه استُخدم فعلًا.

السياسة المنفَّذة حرفيًّا
-----------------------

1. لا تُرحَّل 5116 صفًّا تلقائيًّا.
2. الاسم **ليس** هوية.
3. `(name, role)` **ليست** هوية.
4. لا هوية كانونية لصفوف البذر (seed-only).
5. الصفوف ذات الدليل التاريخي وحدها تتأهّل.
6. الدليل التاريخي = حالة غير `registered`، أو نتائج مدرسة، أو خبرات، أو أي
   مرجع/سجل تاريخي حقيقي في جداول النظام (`EVIDENCE_SOURCES`).
7. الدليل غير الكافي لإثبات الهوية ⇒ لا تُخترَع هوية (يُسجَّل `unresolved`).
8. لا يُحذَف صفّ سكّاني قديم.
9. لا تُفقَد provenance: المعرّف نفسه يُحفَظ، والتصنيف يُوثَّق.
10. لا يُنشأ سجل ثالث.

المعرّف المستعمل للهوية هو **نفس** `agent_population.agent_id`، فارتباط
`school_results` / `experiences` / `agent_health_checks` التاريخي يبقى صحيحًا
بلا إعادة تسمية ولا معرّف جديد.

الأوضاع
-------

    python tools/migrations/r4_unify_agent_identity.py                 # DRY-RUN (افتراضي)
    python tools/migrations/r4_unify_agent_identity.py --backup out.json
    python tools/migrations/r4_unify_agent_identity.py --emit-sql      # SQL معاملاتي مكافئ
    python tools/migrations/r4_unify_agent_identity.py --apply         # تنفيذ فعلي

`--emit-sql` يوجد لأن بعض البيئات (منها القاعدة الحقيقية لهذا المشروع) لا تُتيح
`DATABASE_URL` للعميل بل قناة SQL فقط؛ فالسياسة نفسها تُطبَّق هناك عبر SQL
مكافئ ومعاملاتي بدل ترحيل يدوي غير قابل للمراجعة.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import namedtuple
from pathlib import Path
from typing import Any

_SERVICES_SRC = Path(__file__).resolve().parents[2] / "federal/executive/services/src"
if str(_SERVICES_SRC) not in sys.path:
    sys.path.insert(0, str(_SERVICES_SRC))

#: الحالة التي تعني «بُذِر ولم يُستخدم» — وجودها وحدها ليس دليلًا.
#: قيمة حرفية لا استيرادًا: هذا الملفّ سكربت يعدّل `sys.path` قبل أي استيراد من
#: حزمة الخدمات، فتبقى استيراداته داخل الدوال لا في رأس الملفّ.
SEED_STATE = "registered"

#: ميزانية افتراضية للهوية حين لا يحملها الصفّ السكّاني.
DEFAULT_TOKEN_BUDGET = 10_000


#: جدول يحمل أثرًا تاريخيًّا لاستخدام وكيل فعلًا.
#: `namedtuple` لا `dataclass` عن قصد: هذا الملفّ يُحمَّل في الاختبارات عبر
#: `importlib.util.spec_from_file_location` بلا تسجيل في `sys.modules`، و
#: `dataclasses` يحتاج الوحدة مسجَّلة فيسقط بـ AttributeError.
EvidenceSource = namedtuple("EvidenceSource", "table column kind")  # noqa: PYI024


#: كل ما يُعتدّ به دليلًا تاريخيًّا. يُقاس بالوجود الفعلي للجدول، فالجدول
#: المفقود يُعلَن `unavailable` ولا يُعتبر «لا دليل» بصمت.
EVIDENCE_SOURCES: tuple[EvidenceSource, ...] = (
    EvidenceSource("school_results", "agent_id", "history"),
    EvidenceSource("experiences", "agent_id", "history"),
    EvidenceSource("agent_health_checks", "agent_id", "history"),
    EvidenceSource("agent_isolations", "agent_id", "history"),
    EvidenceSource("agent_treatments", "agent_id", "history"),
    EvidenceSource("specialization_results", "agent_id", "history"),
    EvidenceSource("retirement_records", "agent_id", "history"),
    EvidenceSource("reviews", "agent_id", "history"),
    EvidenceSource("executive_roles", "agent_id", "reference"),
    EvidenceSource("treasury_transactions", "agent_id", "reference"),
    EvidenceSource("university_outputs", "author_agent_id", "reference"),
    EvidenceSource("institutions", "head_agent_id", "reference"),
    EvidenceSource("tasks", "assigned_agent", "reference"),
)


# ── الوصول للقاعدة ───────────────────────────────────────────────────────────


def _sessions() -> list[Any]:
    """جلستان: محرِّك السجل الكانوني ومحرِّك السكّان (قد يكونا نفس القاعدة)."""
    from amos_federation.common.database import get_session_factory
    from amos_federation.services.agent_runtime.population import get_population_registry

    return [get_session_factory()(), get_population_registry()._Session()]


def _resolve_tables() -> tuple[dict[str, Any], list[str]]:
    """أي جلسة تملك أي جدول دليل. الجدول غير الموجود يُعلَن، لا يُهمَل بصمت."""
    from sqlalchemy import inspect

    owners: dict[str, Any] = {}
    unavailable: list[str] = []
    sessions = _sessions()
    try:
        available: list[tuple[Any, set[str]]] = [
            (session, set(inspect(session.get_bind()).get_table_names())) for session in sessions
        ]
        for source in EVIDENCE_SOURCES:
            for session, tables in available:
                if source.table in tables:
                    owners[source.table] = session
                    break
            else:
                unavailable.append(source.table)
    except Exception:  # أي فشل: تُغلَق الجلسات ثم يُعاد رفع الخطأ كما هو
        for session in sessions:
            session.close()
        raise
    return owners, unavailable


def _evidence_ids(owners: dict[str, Any]) -> tuple[dict[str, set[str]], dict[str, int]]:
    """معرّفات كل جدول دليل + عدد صفوفه المرجعية. لا تخمين: قراءة فعلية."""
    from sqlalchemy import text

    ids: dict[str, set[str]] = {}
    rows: dict[str, int] = {}
    for source in EVIDENCE_SOURCES:
        session = owners.get(source.table)
        if session is None:
            continue
        result = session.execute(
            text(
                # أسماء الجداول والأعمدة ثابتة في `EVIDENCE_SOURCES` أعلاه، لا مُدخَل مستخدم.
                f"SELECT {source.column} AS ref, COUNT(*) AS n "
                f"FROM {source.table} WHERE {source.column} IS NOT NULL "
                f"GROUP BY {source.column}"
            )
        ).all()
        ids[source.table] = {str(row[0]) for row in result}
        rows[source.table] = sum(int(row[1]) for row in result)
    return ids, rows


def _population_rows() -> list[dict[str, Any]]:
    from amos_federation.services.agent_runtime.population import (
        AgentPopulationModel,
        get_population_registry,
    )

    session = get_population_registry()._Session()
    try:
        return [
            {
                "agent_id": row.agent_id,
                "name": row.name,
                "role": row.role,
                "state": row.state,
                "permissions": json.loads(row.permissions or "[]"),
                "allowed_tools": json.loads(row.allowed_tools or "[]"),
                "token_budget": int(row.token_budget or 0),
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in session.query(AgentPopulationModel)
            .order_by(AgentPopulationModel.id.asc())
            .all()
        ]
    finally:
        session.close()


# ── التصنيف (DRY-RUN) ────────────────────────────────────────────────────────


def classify() -> dict[str, Any]:
    """تصنيف كل صفّ سكّاني بالدليل التاريخي وحده — بلا كتابة."""
    from amos_federation.services.executive_core.agent_identity import get_identity

    owners, unavailable = _resolve_tables()
    try:
        evidence_ids, evidence_rows = _evidence_ids(owners)
    finally:
        for session in set(owners.values()):
            session.close()

    population = _population_rows()
    population_ids = {row["agent_id"] for row in population}

    seen: dict[str, int] = {}
    for row in population:
        seen[row["agent_id"]] = seen.get(row["agent_id"], 0) + 1
    duplicate_identities = sorted(agent_id for agent_id, n in seen.items() if n > 1)

    evidenced: list[dict[str, Any]] = []
    seed_only: list[str] = []
    for row in population:
        reasons: list[str] = []
        if row["state"] and row["state"] != SEED_STATE:
            reasons.append(f"non_registered_status:{row['state']}")
        for table, ids in evidence_ids.items():
            if row["agent_id"] in ids:
                reasons.append(f"reference:{table}")
        if reasons:
            evidenced.append({**row, "evidence": reasons})
        else:
            seed_only.append(row["agent_id"])

    # مراجع تاريخية لمعرّفات لا صفّ سكّاني لها ولا هوية كانونية: لا تُخترَع هوية.
    orphan_references: dict[str, list[str]] = {}
    unresolved: set[str] = set()
    for table, ids in evidence_ids.items():
        orphans = sorted(
            agent_id
            for agent_id in ids
            if agent_id not in population_ids and get_identity(agent_id) is None
        )
        if orphans:
            orphan_references[table] = orphans
            unresolved.update(orphans)

    # الاسم/(الاسم،الدور) ليسا هوية: التصادم يُعلَن ولا يُدمَج.
    by_name: dict[str, list[str]] = {}
    by_name_role: dict[tuple[str, str], list[str]] = {}
    for row in evidenced:
        by_name.setdefault(row["name"], []).append(row["agent_id"])
        by_name_role.setdefault((row["name"], row["role"]), []).append(row["agent_id"])
    ambiguous_identities = [
        {"name": name, "role": role, "agent_ids": sorted(agent_ids)}
        for (name, role), agent_ids in sorted(by_name_role.items())
        if len(agent_ids) > 1
    ]

    to_create = [row for row in evidenced if get_identity(row["agent_id"]) is None]
    already = [row["agent_id"] for row in evidenced if get_identity(row["agent_id"]) is not None]

    return {
        "policy": "OPTION_2_HISTORICAL_EVIDENCE_ONLY",
        "total_population": len(population),
        "population_distinct_agent_ids": len(population_ids),
        "population_distinct_names": len({row["name"] for row in population}),
        "historically_evidenced_rows": len(evidenced),
        "canonical_agents_to_create": len(to_create),
        "already_canonical": len(already),
        "seed_only_rows": len(seed_only),
        "unresolved_rows": len(unresolved),
        "unresolved_identifiers": sorted(unresolved),
        "duplicate_identities": duplicate_identities,
        "orphan_references": orphan_references,
        "ambiguous_identities": ambiguous_identities,
        "evidence_rows_by_source": evidence_rows,
        "evidence_sources_unavailable": unavailable,
        "rows_deleted": 0,
        "columns_cleared": 0,
        "_evidenced": evidenced,
        "_to_create": to_create,
    }


def _public(report: dict[str, Any]) -> dict[str, Any]:
    """التقرير بلا الحقول الداخلية الضخمة."""
    return {key: value for key, value in report.items() if not key.startswith("_")}


# ── الترحيل ──────────────────────────────────────────────────────────────────


def migrate(*, apply: bool = False, backup_path: str | Path | None = None) -> dict[str, Any]:
    """ترحيل الصفوف ذات الدليل التاريخي وحدها. بلا `apply` = فحص فقط.

    الترحيل idempotent: التشغيل الثاني يُنشئ صفرًا. وغير مُدمِّر: لا حذف صفّ
    ولا تفريغ عمود. صفوف البذر لا تُلمَس ولا تُحذَف — تبقى موسومة legacy.
    """
    from amos_federation.services.executive_core.agent_identity import register_identity

    report = classify()
    to_create = report["_to_create"]

    if backup_path is not None:
        Path(backup_path).write_text(
            json.dumps(
                {
                    "taken_before_apply": apply,
                    "policy": report["policy"],
                    "evidenced_rows": report["_evidenced"],
                    "census": _public(report),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        report["backup_written_to"] = str(backup_path)

    created: list[str] = []
    failed: list[dict[str, str]] = []
    if apply:
        for row in to_create:
            try:
                register_identity(
                    row["agent_id"],
                    name=row["name"],
                    role=row["role"],
                    permissions=row["permissions"],
                    allowed_tools=row["allowed_tools"],
                    lifecycle_state=row["state"] or SEED_STATE,
                    token_budget=row["token_budget"] or DEFAULT_TOKEN_BUDGET,
                )
                created.append(row["agent_id"])
            except Exception as exc:  # الخطأ يُعلَن في التقرير، لا يُخفى ولا يُوقف الباقي
                failed.append({"agent_id": row["agent_id"], "error": str(exc)})

    result = _public(report)
    result["applied"] = apply
    result["identities_created"] = len(created) if apply else len(to_create)
    result["created_agent_ids"] = created if apply else [row["agent_id"] for row in to_create]
    result["failed"] = failed
    return result


# ── SQL مكافئ ومعاملاتي ──────────────────────────────────────────────────────


def evidence_predicate_sql(alias: str = "p") -> str:
    """شرط الدليل التاريخي كـ SQL — نفس السياسة، بلا اسم ولا (اسم،دور)."""
    clauses = [f"({alias}.state IS NOT NULL AND {alias}.state <> '{SEED_STATE}')"]
    clauses += [
        f"EXISTS (SELECT 1 FROM {source.table} r WHERE r.{source.column} = {alias}.agent_id)"
        for source in EVIDENCE_SOURCES
    ]
    return "\n     OR ".join(clauses)


def emit_sql() -> str:
    """ترحيل معاملاتي واحد لـ PostgreSQL، idempotent وغير مُدمِّر."""
    return f"""-- R4 OPTION 2 — APPLY ONLY TO ROWS WITH ACTUAL HISTORICAL EVIDENCE
-- idempotent (ON CONFLICT DO NOTHING) · غير مُدمِّر (لا DELETE ولا UPDATE على السكّان)
BEGIN;

INSERT INTO agents (
    id, name, role, status, permissions, allowed_tools,
    token_budget, tenant_id, created_at, updated_at
)
SELECT DISTINCT ON (p.agent_id)
    p.agent_id,
    p.name,
    p.role,
    COALESCE(NULLIF(p.state, ''), '{SEED_STATE}'),
    COALESCE(NULLIF(p.permissions, '')::json, '[]'::json),
    COALESCE(NULLIF(p.allowed_tools, '')::json, '[]'::json),
    COALESCE(NULLIF(p.token_budget, 0), {DEFAULT_TOKEN_BUDGET}),
    'default',
    COALESCE(p.created_at, now()),
    now()
FROM agent_population p
WHERE {evidence_predicate_sql("p")}
ORDER BY p.agent_id, p.created_at ASC NULLS LAST
ON CONFLICT (id) DO NOTHING;

COMMIT;
"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="R4 (OPTION 2): هوية كانونية للصفوف ذات الدليل التاريخي وحدها"
    )
    parser.add_argument("--apply", action="store_true", help="تنفيذ فعلي (بدونه: فحص فقط)")
    parser.add_argument("--backup", metavar="PATH", help="تصدير الصفوف المؤهَّلة قبل الكتابة")
    parser.add_argument("--emit-sql", action="store_true", help="طباعة SQL المعاملاتي المكافئ")
    args = parser.parse_args()

    if args.emit_sql:
        print(emit_sql())
        return 0

    report = migrate(apply=args.apply, backup_path=args.backup)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
