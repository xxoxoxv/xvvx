#!/usr/bin/env python3
"""الهدف: ترحيل قابل للتكرار — كل صفّ سكّاني تصبح له هوية كانونية واحدة.

النطاق: tools/migrations
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-16

R4-G. ما يفعله هذا الترحيل:

- لكل صفّ في `agent_population` بلا صفّ مقابل في `agents` (نفس `agent_id`):
  تُنشأ هوية كانونية بنفس المعرّف، وبنفس الاسم/الدور/الصلاحيات/الأدوات/الحالة
  المحفوظة في الصفّ السكّاني. الهوية التاريخية تُحفَظ كما هي — لا يُولَّد معرّف
  جديد ولا يُعاد تسمية وكيل.
- الصفوف التي لها هوية كانونية فعلًا: تُفحَص ولا تُكتَب. أي اختلاف في الحقول
  يُسجَّل في `conflicts` كدَين توفيق يدوي — لا تُحسم تلقائيًّا لأن السجل
  الكانوني قد يكون قد تغيّر عن قصد.
- لا يُحذَف أي صفّ ولا يُفرَّغ أي عمود. `agent_population` يبقى ملفًّا تدريبيًّا
  وإسقاطًا، بأعمدته المكرّرة كمرآة توافُقية مهجورة.

الترحيل idempotent: تشغيله مرّتين لا يُنشئ هويات مكرّرة (الثانية تجد الهوية
موجودة فتتخطّاها). التشغيل بلا `--apply` = فحص فقط (dry-run).

الاستخدام:
    python tools/migrations/r4_unify_agent_identity.py            # فحص
    python tools/migrations/r4_unify_agent_identity.py --apply    # تنفيذ
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_SERVICES_SRC = Path(__file__).resolve().parents[2] / "federal/executive/services/src"
if str(_SERVICES_SRC) not in sys.path:
    sys.path.insert(0, str(_SERVICES_SRC))

from amos_federation.services.agent_runtime.population import (  # noqa: E402
    AgentPopulationModel,
    get_population_registry,
)
from amos_federation.services.executive_core.agent_identity import (  # noqa: E402
    get_identity,
    register_identity,
)


def _profile_rows() -> list[dict[str, Any]]:
    registry = get_population_registry()
    session = registry._Session()  # noqa: SLF001 — أداة ترحيل داخلية
    try:
        rows = session.query(AgentPopulationModel).all()
        return [
            {
                "agent_id": row.agent_id,
                "name": row.name,
                "role": row.role,
                "state": row.state,
                "permissions": json.loads(row.permissions or "[]"),
                "allowed_tools": json.loads(row.allowed_tools or "[]"),
                "token_budget": int(row.token_budget or 0),
            }
            for row in rows
        ]
    finally:
        session.close()


def migrate(*, apply: bool = False) -> dict[str, Any]:
    """توحيد الهوية. يعيد تقريرًا بما أُنشئ وما يحتاج توفيقًا."""
    created: list[str] = []
    already: list[str] = []
    conflicts: list[dict[str, Any]] = []

    for row in _profile_rows():
        identity = get_identity(row["agent_id"])
        if identity is None:
            if apply:
                register_identity(
                    row["agent_id"],
                    name=row["name"],
                    role=row["role"],
                    permissions=row["permissions"],
                    allowed_tools=row["allowed_tools"],
                    lifecycle_state=row["state"] or "registered",
                    token_budget=row["token_budget"] or 10_000,
                )
            created.append(row["agent_id"])
            continue

        already.append(row["agent_id"])
        differences = {}
        if identity.name != row["name"]:
            differences["name"] = {"canonical": identity.name, "population": row["name"]}
        if identity.role != row["role"]:
            differences["role"] = {"canonical": identity.role, "population": row["role"]}
        if identity.lifecycle_state != row["state"]:
            differences["lifecycle_state"] = {
                "canonical": identity.lifecycle_state,
                "population": row["state"],
            }
        if sorted(identity.allowed_tools) != sorted(row["allowed_tools"]):
            differences["allowed_tools"] = {
                "canonical": list(identity.allowed_tools),
                "population": row["allowed_tools"],
            }
        if differences:
            conflicts.append({"agent_id": row["agent_id"], "differences": differences})

    return {
        "applied": apply,
        "identities_created": len(created),
        "created_agent_ids": created,
        "already_canonical": len(already),
        "reconciliation_conflicts": conflicts,
        "rows_deleted": 0,
        "columns_cleared": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="R4: توحيد هوية الوكيل والسكّان")
    parser.add_argument("--apply", action="store_true", help="تنفيذ فعلي (بدونه: فحص فقط)")
    args = parser.parse_args()
    report = migrate(apply=args.apply)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
