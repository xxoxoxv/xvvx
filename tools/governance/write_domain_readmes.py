#!/usr/bin/env python3
"""
مُنشئ بطاقات هوية أقاليم المستودع — Domain README Writer (E3)
الهدف: كتابة `README.md` لكل إقليم يفتقده، بحيث يكون «التعريف» منقولًا حرفيًا عن
       «الهدف» المُعلَن في `NUCLEUS.md` لذلك الإقليم، و«النطاق» و«المالك» مكتوبين
       يدويًا في جدول هذا الملف — لا مُخترَعين ولا مُستنسَخين بقالب واحد.
النطاق: الأقاليم المدرجة في `SCOPES` أدناه فقط. لا يلمس README قائمًا.
المالك: tools/governance/
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المبدأ (المادة التاسعة + E3): الحقول المشتقّة تُولَّد، وحقول الحكم تُكتَب.
«التعريف» هنا **نقل** عن إعلان بشري سابق في `NUCLEUS.md`، و«النطاق» **كتابة**
يدوية لكل إقليم. ولا يُستعمل هذا الملف لتوليد نطاق لم يقرأه إنسان.

وتُعلَن حالة الإقليم بصدق: إقليم لا يحوي إلا `NUCLEUS.md` يُقال فيه إنه بلا محتوى
تنفيذي — لا يُوصَف بقدرة لم تُثبَت (تعريف «منجَز» = قدرة مُثبَتة).

الاستخدام:
    python tools/governance/write_domain_readmes.py .
    python tools/governance/write_domain_readmes.py . --check
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# النطاق والمالك — مكتوبان يدويًا لكل إقليم بعد قراءة محتواه
# path: (النطاق, المالك)
SCOPES: dict[str, tuple[str, str]] = {
    # ── أقاليم الجذر ───────────────────────────────────────────────
    "core": (
        "الدستور ومحرّكه، والسيادة الملكية، والذاكرة، والميثاق، والمواصفات. "
        "لا يدخل هنا كود خدمة ولا واجهة ولا أداة تشغيل.",
        "المجلس التأسيسي",
    ),
    "institutions": (
        "مؤسسات الدولة غير الفدرالية: البنك والمحكمة والمصنع والجامعة وسجلّها. "
        "لا يدخل هنا فرع من فروع السلطة الثلاث (موضعها `federal/`).",
        "المجلس التأسيسي",
    ),
    "interfaces": (
        "كل نقطة دخول إلى الدولة من خارجها: API وCLI وواجهة الويب وسجلّها. "
        "لا يدخل هنا منطق أعمال — الواجهة تنقل ولا تقرّر.",
        "المجلس التأسيسي",
    ),
    "royal": (
        "ما يخصّ التاج: المراسيم، ومفاتيح التاج، وزر التوقف الطارئ، وحوكمة الملك، "
        "ومواصفات أثر التدقيق. لا يدخل هنا قرار فرع فدرالي.",
        "التاج",
    ),
    "runtime": (
        "زمن التشغيل: المحرك، والمجدول، والمهام، والأحداث، والسيناريوهات، والمواصفات. "
        "لا يدخل هنا نص حاكم ولا واجهة خارجية.",
        "المجلس التأسيسي",
    ),
    "ops": (
        "تشغيل الدولة ومراقبتها واستمرارها: الرصد، والاستمرارية، والخلافة، "
        "والكبسولات الزمنية. لا يدخل هنا كود ميزة.",
        "المجلس التأسيسي",
    ),
    "tests": (
        "كل اختبار يُثبت قدرة في الدولة: دستورية، وسيادية، وتكامل، وشامل، ودخان. "
        "لا يدخل هنا كود إنتاجي.",
        "المجلس التأسيسي",
    ),
    # ── مواصفات وفروع ─────────────────────────────────────────────
    "core/specs": (
        "مواصفات النواة المكتوبة قبل بنائها: النواة وتحديث الذاكرة. "
        "المواصفة تصف ما يجب أن يكون، ولا تُقاس بها القدرة — الاختبار يقيسها.",
        "core/",
    ),
    "royal/specs": (
        "مواصفات ما يخصّ التاج، وأولها مواصفة أثر التدقيق (`audit_trail.md`).",
        "royal/",
    ),
    "runtime/specs": (
        "مواصفات زمن التشغيل: دورة حياة المهمة، وتسجيل الأحداث.",
        "runtime/",
    ),
    "runtime/engine": (
        "محرك تنفيذ الوكلاء وحده. التوقيت في `runtime/scheduler/`، "
        "وتعريف المهمة في `runtime/tasks/`.",
        "runtime/",
    ),
    "runtime/scheduler": (
        "توقيت تنفيذ المهام وترتيب أولوياتها. لا ينفّذ المهمة بنفسه.",
        "runtime/",
    ),
    "runtime/tasks": (
        "تعريف المهمة وحالاتها وانتقالاتها. لا يشمل تنفيذها.",
        "runtime/",
    ),
    "runtime/events": (
        "سجل أحداث الدولة وفهرسه. لا يشمل عقود الأحداث "
        "(موضعها `docs/implementation/event-contracts.md`).",
        "runtime/",
    ),
    "runtime/scenarios": (
        "سيناريوهات تشغيل مكتوبة تُشتقّ منها اختبارات شاملة، أولها تنفيذ مهمة واحدة.",
        "runtime/",
    ),
    # ── المؤسسات ───────────────────────────────────────────────────
    "institutions/bank": (
        "البنك المركزي: السياسة النقدية والميزانية وإصدار العملة الرقمية. "
        "جداوله `treasury_transactions` و`treasury_budgets` و`treasury_reports`.",
        "institutions/",
    ),
    "institutions/court": (
        "المحكمة الدستورية: النظر في مخالفات الدستور وإصدار الأحكام. "
        "لا تملك تعديل الدستور (المادة العاشرة · 2 · 1).",
        "institutions/",
    ),
    "institutions/factory": (
        "مصنع الوكلاء: توليد الوكلاء وتجهيزهم. لا يمنح هوية بلا سجل "
        "(`agents/registry/`).",
        "institutions/",
    ),
    "institutions/university": (
        "الجامعة: تدريب الوكلاء وتقييم مهاراتهم.",
        "institutions/",
    ),
    "institutions/registry": (
        "سجل المؤسسات وفهرسه، مرتبطًا بجدول `institutions`. "
        "لا يشمل سجل الوكلاء ولا سجل الأدوات.",
        "institutions/",
    ),
    # ── الواجهات ───────────────────────────────────────────────────
    "interfaces/api": (
        "عقد واجهة HTTP للدولة ونقاطها. لا يشمل تنفيذ الخدمات "
        "(موضعه `federal/executive/services/`).",
        "interfaces/",
    ),
    "interfaces/cli": (
        "خريطة أوامر سطر الأوامر ومدخلاته. لا يشمل منطق ما تنفّذه الأوامر.",
        "interfaces/",
    ),
    "interfaces/web": (
        "واجهة الويب، وأولها لوحة المالك (`owner_dashboard.md`).",
        "interfaces/",
    ),
    # ── وثائق ──────────────────────────────────────────────────────
    "docs/contracts/schemas": (
        "مخططات JSON Schema لكيانات الدولة وأحداثها — العقد الشكلي للبيانات. "
        "لا يشمل عقود الأحداث السلوكية ولا سجل المخططات التشغيلي.",
        "docs/",
    ),
    "docs/maturity": (
        "معايير نضج المستودع: نضج التكامل المستمر، ومعايير الاستخراج، "
        "والحوكمة طويلة المدى، وسياسة الإصدارات.",
        "docs/",
    ),
    "federal/executive/services/src/amos_federation/governance": (
        "حوكمة الخدمات التنفيذية داخل حزمة `amos_federation`، وأولها سجل المخططات. "
        "لا يشمل الحوكمة الدستورية (موضعها `core/`).",
        "federal/executive/services/",
    ),
    "federal/executive/services/src/amos_federation/governance/schema-registry": (
        "سجل مخططات الأحداث التي تتبادلها الخدمات وقت التشغيل، "
        "وأولها `task.created`.",
        "federal/executive/services/",
    ),
    # ── الاختبارات ─────────────────────────────────────────────────
    "tests/e2e": (
        "اختبارات شاملة تمرّ بالدولة من مدخلها إلى أثرها. "
        "لا يدخل هنا اختبار وحدة.",
        "tests/",
    ),
    "tests/integration": (
        "اختبارات تكامل بين مكوّنين أو أكثر. لا تشمل المسار الكامل.",
        "tests/",
    ),
    "tests/smoke": (
        "اختبارات دخان تُثبت أن أركان الدولة قائمة وتستجيب، تُشغَّل عند كل دفع.",
        "tests/",
    ),
}

# أقاليم الحرّاس (`stubs`) — لا `NUCLEUS.md` فيها، فتُكتَب تعريفاتها يدويًا
GUARDS: dict[str, tuple[str, str, str]] = {
    # path: (التعريف, النطاق, المالك)
    "agents/stubs": (
        "حرّاس إقليم الوكلاء: تحقّقات صغيرة تُشغَّل في اختبار الدخان لتثبت أن سجل "
        "الوكلاء قائم ومقروء.",
        "فحص وجود سجل الوكلاء وسلامته فقط. لا يعدّل سجلًا ولا ينشئ وكيلًا.",
        "agents/",
    ),
    "core/stubs": (
        "حرّاس النواة: تحقّق من أن ذاكرة الدولة قائمة ومقروءة.",
        "فحص الذاكرة فقط. لا يمسّ نص الدستور ولا يكتب في الذاكرة.",
        "core/",
    ),
    "docs/stubs": (
        "حرّاس الوثائق: تحقّق من أن بنية الوثائق قائمة.",
        "فحص وجود الوثائق وبنيتها. لا يقيس صحة مضمونها.",
        "docs/",
    ),
    "federal/stubs": (
        "حرّاس الإقليم الفدرالي: تحقّق من أن الخزانة الفدرالية قائمة ومقروءة.",
        "فحص الخزانة فقط. لا ينفّذ معاملة ولا يعدّل ميزانية.",
        "federal/",
    ),
    "institutions/stubs": (
        "حرّاس المؤسسات: تحقّق من أن سجل المؤسسات قائم ومقروء.",
        "فحص السجل فقط. لا ينشئ مؤسسة ولا يغيّر حالتها.",
        "institutions/",
    ),
    "interfaces/stubs": (
        "حرّاس الواجهات: تحقّق من أن سجل الواجهات قائم ومقروء.",
        "فحص السجل فقط. لا يفتح منفذًا ولا يستدعي واجهة.",
        "interfaces/",
    ),
    "ops/stubs": (
        "حرّاس العمليات: تحقّق من أن أثر التدقيق قائم ومقروء.",
        "فحص أثر التدقيق فقط. لا يكتب فيه ولا يحذف منه.",
        "ops/",
    ),
    "royal/stubs": (
        "حرّاس التاج: تحقّق من أن حرّاس الدولة وسجلّاتها الملكية قائمة.",
        "فحص فقط. لا يوقّع مرسومًا ولا يمسّ مفتاح التاج.",
        "royal/",
    ),
    "runtime/stubs": (
        "حرّاس زمن التشغيل: تحقّق من أن المهام والأحداث قائمة ومقروءة.",
        "فحص المهام والأحداث فقط. لا ينفّذ مهمة ولا ينشر حدثًا.",
        "runtime/",
    ),
    "states/stubs": (
        "حرّاس الولايات: تحقّق من أن سياسات الولايات قائمة ومقروءة.",
        "فحص السياسات فقط. لا يعدّل سياسة ولا ينشئ ولاية.",
        "states/",
    ),
    "tests/stubs": (
        "حرّاس الاختبارات: تحقّق من أن بنية الاختبارات قائمة.",
        "فحص بنية الاختبارات. لا يُغني عن اختبار حقيقي ولا يُحتسب إثباتًا لقدرة.",
        "tests/",
    ),
    "tools/stubs": (
        "حرّاس الأدوات: تحقّق من أن سجل الأدوات قائم ومقروء.",
        "فحص السجل فقط. لا يشغّل أداة ولا يمنح صلاحية.",
        "tools/",
    ),
}

# تعريفات مكتوبة يدويًا لأقاليم لا `NUCLEUS.md` فيها ولا هي حرّاس
DEFINITIONS: dict[str, str] = {
    "docs/contracts/schemas": (
        "مخططات JSON Schema التي تُعرِّف شكل كيانات الدولة وأحداثها: الوكيل، "
        "والمؤسسة، والواجهة، والذاكرة، والحدث، والموافقة، وحلقة التنفيذ، والرصد. "
        "هي العقد الشكلي الذي تُقاس عليه أي حمولة قبل قبولها."
    ),
}

_NUCLEUS_GOAL = re.compile(r"^##\s*الهدف\s*\n(.+?)(?=\n##\s|\Z)", re.M | re.S)
_NUCLEUS_STATE = re.compile(r"^##\s*الحالة\s*\n(.+?)(?=\n##\s|\Z)", re.M | re.S)
_TITLE = re.compile(r"^#\s+(.+)$", re.M)


def _read_nucleus(d: Path) -> tuple[str, str, str]:
    """(العنوان، الهدف، الحالة) من `NUCLEUS.md` — أو فراغ إذا لم يوجد."""
    n = d / "NUCLEUS.md"
    if not n.exists():
        return "", "", ""
    t = n.read_text(encoding="utf-8")
    title = m.group(1).strip() if (m := _TITLE.search(t)) else ""
    goal = " ".join((m.group(1).strip() if (m := _NUCLEUS_GOAL.search(t)) else "").split())
    state = " ".join((m.group(1).strip() if (m := _NUCLEUS_STATE.search(t)) else "").split())
    return title, goal, state


def _has_executable_content(d: Path) -> bool:
    """هل في الإقليم شيء غير `NUCLEUS.md` و`README.md`؟"""
    for p in d.iterdir():
        if p.name.startswith((".", "__")):
            continue
        if p.is_dir():
            return True
        if p.name not in {"NUCLEUS.md", "README.md"}:
            return True
    return False


def build_readme(root: Path, rel: str) -> str:
    d = root / rel
    title, goal, state = _read_nucleus(d)
    name = rel.split("/")[-1]

    if rel in GUARDS:
        definition, scope, owner = GUARDS[rel]
        heading = f"# {rel} — حرّاس الإقليم"
        source_note = ""
    else:
        scope, owner = SCOPES[rel]
        if goal:
            definition = goal
            source_note = (
                "\n> **مصدر التعريف:** منقول عن «الهدف» في "
                "[`NUCLEUS.md`](NUCLEUS.md) لهذا الإقليم، لا مُنشأ هنا.\n"
            )
        elif rel in DEFINITIONS:
            definition = DEFINITIONS[rel]
            source_note = ""
        else:
            raise SystemExit(
                f"لا هدف مُعلَنًا في {rel}/NUCLEUS.md ولا تعريف يدويًا في DEFINITIONS "
                f"— لا يُخترع تعريف. اكتب أحدهما أولًا."
            )
        heading = f"# {title or rel}"

    # الحالة تُقال بصدق: بلا محتوى تنفيذي = بلا قدرة مُثبَتة
    if rel in GUARDS:
        status = (
            "**حرّاس فحص فقط.** هذه التحقّقات لا تُثبت قدرة الإقليم، بل تُثبت أنه "
            "قائم ومقروء. إثبات القدرة موضعه `tests/`."
        )
    elif not _has_executable_content(d):
        status = (
            "**بلا محتوى تنفيذي بعد.** لا يحوي هذا الإقليم إلا نواته ("
            f"`NUCLEUS.md`){f' — وحالتها المُعلَنة: {state}' if state else ''}. "
            "فلا يُنسب إليه قدرة حتى يوجد كود واختبار يُثبتها "
            "(انظر [تعريف «منجَز»](../docs/audit/DEFINITION_OF_DONE.md))."
        )
    else:
        status = f"**قائم.** الحالة المُعلَنة في النواة: {state}." if state else "**قائم.**"

    return f"""{heading}
{source_note}
## التعريف
{definition}

## النطاق
{scope}

## المالك
{owner}

## تاريخ الإنشاء
2026-08-16

## تاريخ آخر تعديل
<!-- يُملأ آليًا بـ stamp_readme_identity.py -->

## الحالة
{status}

## المحتويات
<!-- يُملأ آليًا بـ stamp_readme_identity.py -->

---
*بطاقة هوية إقليم — المادة التاسعة (قانون هوية الملفات). اسم `{name}` ثابت؛ ولا
يُضاف إلى هذا الإقليم ما يخرج عن نطاقه أعلاه.*
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="كتابة بطاقات هوية أقاليم المستودع")
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--check", action="store_true", help="لا يكتب؛ يفشل إذا نقص README")
    args = ap.parse_args()
    root = Path(args.root).resolve()

    targets = sorted(set(SCOPES) | set(GUARDS))
    missing, written = [], []
    for rel in targets:
        d = root / rel
        if not d.is_dir():
            print(f"  [تنبيه] إقليم غير موجود: {rel}", file=sys.stderr)
            continue
        target = d / "README.md"
        if args.check:
            if not target.exists():
                missing.append(rel)
            continue
        if target.exists():
            continue
        target.write_text(build_readme(root, rel), encoding="utf-8")
        written.append(rel)

    if args.check:
        if missing:
            print(f"✗ {len(missing)} إقليمًا بلا بطاقة هوية:")
            for m in missing:
                print(f"  - {m}")
            return 1
        print(f"✓ كل الأقاليم المسجّلة ({len(targets)}) لها بطاقة هوية.")
        return 0

    print(f"✓ كُتبت {len(written)} بطاقة هوية إقليم (من {len(targets)} مسجّلة).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
