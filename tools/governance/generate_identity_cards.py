#!/usr/bin/env python3
"""
مولِّد بطاقات الهوية للمواطنين المستوردين — Imported Identity Card Generator

الهدف: توليد بطاقة هوية (`README.md`) وترويسة هدف لكل مواطن مستورد في
       `agents/identities/imported/`، مشتقّة من بياناته الحقيقية في
       `upstream.yaml` و`identity.md` — لا نصًّا قالبيًا فارغًا.
النطاق: `agents/identities/imported/<domain>/<slug>/` فقط. لا يلمس هذه الأداة أي
        ملف خارج هذا المسار.
المالك: tools/governance — المجلس التأسيسي
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

## لماذا مولِّد لا كتابة يدوية
280 مواطنًا مستوردًا بياناتهم **موجودة أصلًا** ومهيكلة في `upstream.yaml`. كتابة
280 بطاقة باليد تُنتج نصًّا متكرّرًا عرضة للخطأ ويتعفّن عند تغيّر البيانات.
التوليد من المصدر يضمن أن البطاقة **تعكس الحقيقة دائمًا**: يُعاد تشغيل الأداة
فتتحدّث البطاقات. ولذلك تُشغَّل هذه الأداة بعد كل تعديل على السجل المستورد.

## ما لا تفعله هذه الأداة
لا تُلفّق التزامًا. المعلومات التي تكتبها كلها مقروءة من ملفات الوكيل نفسه:
اسمه، معرّفه، رابط مصدره، تصنيفه، مكانه، تخصصه، وحالات ترخيصه وأمنه ودمجه.
حيث لا تتوفر معلومة تُكتب حالتها الصريحة (`pending_review`) لا تُخترع.

الاستخدام:
    python tools/governance/generate_identity_cards.py            # توليد
    python tools/governance/generate_identity_cards.py --check    # فحص بلا كتابة
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
IMPORTED_ROOT = REPO_ROOT / "agents" / "identities" / "imported"

YAML_HEADER_SENTINEL = "# الهدف:"

# الحالات التي تُترجَم إلى عربية مفهومة في البطاقة
STATUS_AR = {
    "registered": "مسجَّل",
    "not_integrated": "غير مدموج",
    "integrated": "مدموج",
    "pending_review": "بانتظار المراجعة",
    "approved": "معتمد",
    "rejected": "مرفوض",
    "imported_candidate": "مرشَّح مستورد",
}


def _ar(value: str) -> str:
    return STATUS_AR.get(value, value)


def read_upstream(path: Path) -> dict[str, str]:
    """قراءة `upstream.yaml` بمحلّل بسيط — الملف مسطَّح بمفاتيح نصية فقط.

    لا نستخدم PyYAML لتفادي تبعية غير معلنة في أداة حكومية تعمل في CI.
    """
    data: dict[str, str] = {}
    key = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(YAML_HEADER_SENTINEL) or line.startswith("# "):
            continue
        m = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m:
            key = m.group(1)
            data[key] = m.group(2).strip().strip("'\"")
        elif key and line.startswith(("  ", "\t")):
            data[key] = (data[key] + " " + line.strip()).strip()
    return data


def read_specialization(identity_md: Path) -> str:
    """التخصص الدقيق من `identity.md` إن وُجد."""
    if not identity_md.exists():
        return ""
    m = re.search(r"التخصص الدقيق:\s*(.+)", identity_md.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else ""


def build_readme(agent_dir: Path, up: dict[str, str], spec: str, today: str) -> str:
    name = up.get("name", agent_dir.name)
    slug = up.get("slug", agent_dir.name)
    domain = agent_dir.parent.name
    # README.md يُدرَج دائمًا حتى تكون البطاقة ثابتة بين التوليد الأول وما بعده
    # (وإلا لتغيّرت المحتويات في كل تشغيل وفشلت بوابة --check بلا سبب حقيقي).
    contents = sorted(
        {f.name for f in agent_dir.iterdir() if f.is_file()} | {"README.md"}
    )

    spec_line = f"تخصصه الدقيق **{spec}**، و" if spec else ""
    src = up.get("source_url", "غير مسجَّل")
    src_md = f"[{src}]({src})" if src.startswith("http") else src

    return f"""# {name} — مواطن مستورد ({slug})

## التعريف
`{name}` مورد خارجي مستورد إلى الفدرالية كـ**موظف مرشَّح** لا كعضو عامل. سُجِّل
تحت المعرّف `{up.get('id', slug)}` من مصدره {src_md}، وصُنِّف أصلًا في
«{up.get('original_category', 'غير مصنَّف')}»، وأُسكِن في مجال `{domain}`،
و{spec_line}خُصِّص له المكان
`{up.get('assigned_place', 'غير مخصَّص')}` داخل بنية الدولة. لم يُنسخ كود مصدره
إلى المستودع — تُسجَّل هويته ومصدره فقط، منعًا لتضخّم المستودع ولالتباس
التراخيص. حالته الآن: استيراده **{_ar(up.get('import_status', 'غير معروف'))}**،
ودمجه **{_ar(up.get('integration_status', 'غير معروف'))}**، وترخيصه
**{_ar(up.get('license_status', 'غير معروف'))}**، وفحصه الأمني
**{_ar(up.get('security_status', 'غير معروف'))}**. لا يُمنح أي صلاحية تشغيل
إنتاجية قبل اجتياز الترخيص والفحص الأمني وتصنيف القدرات وتدريب المدرسة
(≥85%) وموافقة الحوكمة — تطبيقًا لمبدأ «المراقبة قبل الثقة».

## النطاق
**يدخل:** تسجيل هوية هذا المورد ومصدره وتخصصه وحالة تقييمه، وأثر تقدّمه في مسار
دورة الحياة `imported → classified → sandbox_review → school_training →
evaluation → employed | archived`.

**لا يدخل:** كود المصدر (غير مُستنسخ)، ومنح الصلاحيات (للحوكمة)، وأي تنفيذ
إنتاجي قبل الاعتماد، وأي وصول إلى أسرار أو مفاتيح.

## المالك
`{up.get('assigned_place', 'agents/identities/imported')}` — تحت إشراف
`agents/registry` والحوكمة الفدرالية.

## تاريخ الإنشاء
{up.get('pulled_at', 'غير مسجَّل')}

## تاريخ آخر تعديل
{today}

## المحتويات
{chr(10).join(f'- `{c}` — ' + ('هوية الوكيل كموظف مرشَّح: دوره وقدراته وممنوعاته ومعايير اعتماده' if c == 'identity.md' else 'مصدره وحالة سحبه وترخيصه وفحصه الأمني' if c == 'upstream.yaml' else 'بطاقة هوية هذا المجلد (المادة التاسعة)' if c == 'README.md' else 'ملف تابع') for c in contents)}

---
*بطاقة مولَّدة من بيانات هذا المواطن نفسها بأداة
[`tools/governance/generate_identity_cards.py`](../../../../../tools/governance/generate_identity_cards.py).
لا تُعدَّل يدويًا — عدّل `upstream.yaml` ثم أعد التوليد.*
"""


def build_yaml_header(up: dict[str, str], domain: str) -> str:
    name = up.get("name", "?")
    return f"""{YAML_HEADER_SENTINEL} تسجيل مصدر المواطن المستورد «{name}» وحالة سحبه وترخيصه وفحصه الأمني.
# النطاق: هذا الوكيل وحده. لا يحمل كودًا ولا صلاحيات — بيانات تسجيل فقط.
# المالك: agents/registry — تحت إشراف الحوكمة الفدرالية.
# المجال المخصص: {domain}
# ملاحظة: هذا الملف مصدر الحقيقة لبطاقة README.md المولَّدة في هذا المجلد.
#         بعد أي تعديل هنا، أعد تشغيل tools/governance/generate_identity_cards.py
"""


def run(check_only: bool = False) -> tuple[int, int]:
    """يرجع (عدد البطاقات المكتوبة/الناقصة، عدد الترويسات المكتوبة/الناقصة)."""
    if not IMPORTED_ROOT.is_dir():
        raise SystemExit(f"مسار الهويات المستوردة غير موجود: {IMPORTED_ROOT}")

    today = date.today().isoformat()
    readmes = headers = 0

    for upstream in sorted(IMPORTED_ROOT.rglob("upstream.yaml")):
        agent_dir = upstream.parent
        up = read_upstream(upstream)
        spec = read_specialization(agent_dir / "identity.md")

        raw = upstream.read_text(encoding="utf-8")
        if YAML_HEADER_SENTINEL not in raw:
            headers += 1
            if not check_only:
                header = build_yaml_header(up, agent_dir.parent.name)
                upstream.write_text(header + raw, encoding="utf-8")

        readme = agent_dir / "README.md"
        content = build_readme(agent_dir, up, spec, today)
        existing = readme.read_text(encoding="utf-8") if readme.exists() else ""
        # تجاهل فرق تاريخ آخر تعديل وحده حتى لا يُعاد كتابة 280 ملفًا كل يوم بلا سبب
        if _strip_mtime(existing) != _strip_mtime(content):
            readmes += 1
            if not check_only:
                readme.write_text(content, encoding="utf-8")

    return readmes, headers


def _strip_mtime(text: str) -> str:
    return re.sub(r"## تاريخ آخر تعديل\n\d{4}-\d{2}-\d{2}", "", text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="مولِّد بطاقات هوية المواطنين المستوردين")
    parser.add_argument("--check", action="store_true",
                        help="لا تكتب — أفشل إن كانت بطاقة أو ترويسة ناقصة أو قديمة")
    args = parser.parse_args(argv)

    readmes, headers = run(check_only=args.check)

    if args.check:
        if readmes or headers:
            print(f"[IDENTITY CARDS] ✗ ناقص أو قديم: {readmes} بطاقة · {headers} ترويسة.")
            print("  شغّل: python tools/governance/generate_identity_cards.py")
            return 1
        print("[IDENTITY CARDS] ✓ كل بطاقات المواطنين المستوردين مولَّدة ومحدَّثة.")
        return 0

    print(f"[IDENTITY CARDS] ✓ كُتبت {readmes} بطاقة و{headers} ترويسة.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
