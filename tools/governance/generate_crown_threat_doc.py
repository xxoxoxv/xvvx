"""الهدف: توليد وثيقة نموذج تهديد التاج من مكتبة التهديدات نفسها لا من الذاكرة،
حتى لا تنفصل الوثيقة عن التنفيذ. تُشغَّل بلا وسائط للكتابة، وبـ`--check` للتحقق.

المالك: التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from core.crown.threats import (  # noqa: E402
    ALL_THREATS,
    DetectionCapability,
    MitigationStatus,
    ThreatDomain,
    boundary_report,
)

TARGET = REPO_ROOT / "docs" / "security" / "CROWN_THREAT_MODEL.md"

STATUS_MARK = {
    MitigationStatus.IMPLEMENTED_AND_TESTED: "منفَّذ ومختبَر",
    MitigationStatus.PARTIALLY_IMPLEMENTED: "منفَّذ جزئيًّا",
    MitigationStatus.MODELLED_NOT_IMPLEMENTED: "مُنمذَج بلا تنفيذ",
    MitigationStatus.OUT_OF_SOFTWARE_SCOPE: "خارج مقدرة البرمجية",
}

DETECTION_MARK = {
    DetectionCapability.DETECTABLE_BY_SOFTWARE: "تكشفه البرمجية",
    DetectionCapability.PARTIALLY_DETECTABLE: "كشف جزئي",
    DetectionCapability.DIGITAL_TRACE_ONLY: "أثر رقمي فقط",
    DetectionCapability.NOT_DETECTABLE_BY_SOFTWARE: "لا تكشفه البرمجية",
}

DOMAIN_TITLE = {
    ThreatDomain.CRYPTOGRAPHIC: "التعمية",
    ThreatDomain.SOFTWARE_SUPPLY_CHAIN: "سلسلة التوريد البرمجية",
    ThreatDomain.RUNTIME: "بيئة التشغيل",
    ThreatDomain.AGENT_BEHAVIOR: "سلوك الوكلاء",
    ThreatDomain.GOVERNANCE: "الحوكمة",
    ThreatDomain.IDENTITY: "الهوية",
    ThreatDomain.AUDIT: "السجل",
    ThreatDomain.PHYSICAL: "المادي",
    ThreatDomain.MEDICAL: "الطبي",
    ThreatDomain.PSYCHOLOGICAL: "النفسي والإكراه",
    ThreatDomain.COMMUNICATIONS: "الاتصالات",
    ThreatDomain.SPECULATIVE: "التخميني",
}

HEADER = """# نموذج تهديد التاج

## الهدف
تسمية ما يهدّد سيادة التاج تسميةً صريحة، وقولُ الحق في كل تهديد: هل تكشفه
البرمجية أم لا، وهل مُعالَج ومختبَر أم مُنمذَج بلا تنفيذ أم خارج مقدرتها أصلًا،
ومن يملك الاستجابة. **وهذه الوثيقة مولَّدة من `core/crown/threats.py` نفسه**
بـ`tools/governance/generate_crown_threat_doc.py`، فلا تتحرر من التنفيذ ولا
تُحرَّر بيدٍ: عدِّل المكتبة ثم أعد التوليد.

## النطاق
تهديدات التاج: أصالة الملك، وسلطة التاج، وهويته التعمية، ومرساة الثقة، وقناة
الأمر، ودورة حياة المفتاح، والسجل، وبيئة التشغيل، والحارس، والاسترداد، والخلافة،
والاستمرارية. **لا يدخل:** تهديدات الفدرالية والمؤسسات (مرحلة أخرى).

## المالك
التاج

## تاريخ الإنشاء
2026-08-16

## تاريخ آخر تعديل
2026-08-16

## المحتويات
| القسم | الموضوع |
|---|---|
| 1 | الحصيلة بالأرقام |
| 2 | التهديدات بالنطاقات |
| 3 | ما لا يُعالَج اليوم |
| 4 | قاعدة الادّعاء |

---

## 1. الحصيلة بالأرقام
"""

FOOTER_RULE = """
## 4. قاعدة الادّعاء

`Threat.__post_init__` يرفع `FalseMitigationClaimError` في حالين: أن يُدَّعى
تنفيذٌ بلا `test_refs`، أو أن يُدَّعى تنفيذٌ ضد تهديد أُفقُه **تخميني**. فرفع
الحال في الجدول لا يمرّ بتعديل نصّ، بل يستلزم اختبارًا قائمًا يُشير إليه
التهديد بالاسم — و`tests/crown/test_crown_threat_model.py::test_every_test_reference_resolves_to_an_existing_test`
يقرأ ملفات الاختبار بـ`ast` ويفشل عند أول مرجع معلَّق.

**ولا يُدَّعى في هذا النموذج أمنٌ مطلق، ولا حمايةٌ من تقنية لا وجود لها.**
التقنية غير المتحققة تُنمَذج فئةً، وتُوضَع استجابتها في
[`CROWN_SECURITY_ROADMAP.md`](CROWN_SECURITY_ROADMAP.md).

## المراجع
- المكتبة: [`core/crown/threats.py`](../../core/crown/threats.py)
- الحدّ البشري: [`HUMAN_SOFTWARE_BOUNDARY.md`](HUMAN_SOFTWARE_BOUNDARY.md)
- المعمار: [`CROWN_SOVEREIGNTY_PROTECTION.md`](CROWN_SOVEREIGNTY_PROTECTION.md)
- بالأمر: `python -m core.crown.cli threat-matrix` و`python -m core.crown.cli boundary`
"""


def render() -> str:
    report = boundary_report()
    out = [HEADER]
    out.append(
        "| المقياس | العدد |\n|---|---|\n"
        f"| مجموع التهديدات المُنمذَجة | {report['total_threats']} |\n"
        f"| تكشفه البرمجية | {report['detectable_by_software']} |\n"
        f"| يحتاج استجابة بشرية | {report['requires_human']} |\n"
        f"| منفَّذ ومختبَر | {report['implemented_and_tested']} |\n"
        f"| منفَّذ جزئيًّا | {report['partially_implemented']} |\n"
        f"| مُنمذَج بلا تنفيذ | {report['modelled_not_implemented']} |\n"
        f"| خارج مقدرة البرمجية | {report['out_of_software_scope']} |\n"
    )
    out.append("\n## 2. التهديدات بالنطاقات\n")
    for domain in ThreatDomain:
        rows = [t for t in ALL_THREATS if t.domain is domain]
        if not rows:
            continue
        out.append(f"\n### {DOMAIN_TITLE[domain]} — {domain.value} ({len(rows)})\n")
        out.append("| المعرّف | التهديد | الكشف | الحال | المسؤول |\n|---|---|---|---|---|\n")
        for t in rows:
            responsible = "البرمجية" if t.responsible.is_software else "بشر/إجراء"
            out.append(
                f"| `{t.threat_id}` | {t.title} | {DETECTION_MARK[t.detection]} "
                f"| {STATUS_MARK[t.mitigation_status]} | {responsible} |\n"
            )
    out.append("\n## 3. ما لا يُعالَج اليوم\n\n")
    out.append(
        "الصدق شرط الأمن، فهذه التهديدات مُعلَنة بلا ادّعاء حماية:\n\n"
        "| المعرّف | التهديد | الحال | لماذا |\n|---|---|---|---|\n"
    )
    for t in ALL_THREATS:
        if t.mitigation_status.claims_protection:
            continue
        why = t.notes or "خارج ما تُثبته البرمجية وحدها."
        out.append(
            f"| `{t.threat_id}` | {t.title} | {STATUS_MARK[t.mitigation_status]} | {why} |\n"
        )
    out.append(FOOTER_RULE)
    return "".join(out)


def main() -> int:
    content = render()
    if "--check" in sys.argv:
        if not TARGET.exists():
            print(f"✗ الوثيقة غير موجودة: {TARGET}")
            return 1
        if TARGET.read_text(encoding="utf-8") != content:
            print("✗ وثيقة نموذج التهديد لا تطابق مكتبة التهديدات — أعد التوليد.")
            return 1
        print(f"✓ {TARGET.relative_to(REPO_ROOT)} مطابقة للتنفيذ.")
        return 0
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(content, encoding="utf-8")
    print(f"✓ كُتبت {TARGET.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
