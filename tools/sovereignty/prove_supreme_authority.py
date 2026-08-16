"""الهدف: إثبات تشغيلي حيّ لعلوّ السلطة الملكية — مسارات القرار الثلاثة.

المالك: tools/sovereignty/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

ليس هذا عرضًا توضيحيًا ولا محاكاة: يُنصَّب تاج حقيقيّ وتُوقَّع مراسيم بمفتاح
Ed25519 حقيقيّ، ثم تُمرّر على البوابة نفسها التي تستخدمها الدولة. وتُطبَع
النتيجة كما وقعت لا كما يُراد لها أن تكون.

والمفتاح الخاص يُكتب في مجلد مؤقت وحده — لا في المستودع أبدًا (المادة
العاشرة · 6 · 3).

المسارات المُثبَتة:
  أ — مرسوم ملكي ثابت التوقيع ⇒ تنفيذ، والمخالفات تُسجَّل ولا تمنع.
  ب — نفس الأفعال من طرف تابع ⇒ منعٌ دستوريّ كما كان قبل E2.1.
  ج — انتحال الصفة الملكية ⇒ رفض + حدث أمني + لا تنفيذ.

التشغيل من جذر المستودع:
    python tools/sovereignty/prove_supreme_authority.py
"""
from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# تُشغّل الأداة من أي موضع: جذر المستودع أبو مجلدي هذا الملف.
# تهيئة المسار تسبق استيراد `core` ضرورةً، فـ E402 مكتوم هنا **قصدًا** وموضعيًّا
# لا بإعداد يُضعف المدقّق على المستودع كله.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import core.sovereignty.crown as crown_mod  # noqa: E402
from core.constitutional_engine.model import ActionRequest, Branch  # noqa: E402
from core.sovereignty.crown import provision_crown  # noqa: E402
from core.sovereignty.decree import RoyalDecree, sign_decree  # noqa: E402
from core.sovereignty.gateway import (  # noqa: E402
    RoyalImpersonation,
    SovereignGateway,
    SovereigntyViolation,
)

tmp = Path(tempfile.mkdtemp())
key_path = tmp / "crown.pem"
registry = tmp / "CROWN_KEYS.json"
provision_crown(key_path, registry_path=registry)
crown_mod.CROWN_KEYS_PATH = registry  # توجيه القراءة للسجل المؤقت

from cryptography.hazmat.primitives import serialization  # noqa: E402

priv = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
key_id = crown_mod.load_crown().key_id

CASES = [
    ("dispatch_agent", "agent-7", "critical"),
    ("deploy_production", "prod", "critical"),
    ("expand_state", "state-12", "fateful"),
    ("amend_constitution", "A003", "fateful"),
    ("pardon", "agent-99", "critical"),
]


def royal_request(action, target, criticality):
    decree = sign_decree(
        RoyalDecree(
            decree_id=f"RD-{action}",
            action=action,
            target=target,
            issued_at=datetime.now(timezone.utc).isoformat(),
            justification="إثبات E2.1",
            key_id=key_id,
        ),
        priv,
    )
    return ActionRequest(
        actor=Branch.ROYAL,
        action=action,
        target=target,
        criticality=criticality,
        royal_decree=decree,
    )


print("=" * 72)
print("أ — المسار السيادي: مرسوم ملكي ثابت التوقيع")
print("=" * 72)
FAILURES: list[str] = []
gw = SovereignGateway()
for action, target, crit in CASES:
    req = royal_request(action, target, crit)
    try:
        out = gw.execute(req, lambda: "نُفِّذ")
        rec = gw.records[-1]
        print(f"  ✓ {action:22} → {out} · طبقة={rec.authority_layer} "
              f"· ملاحظات مُسجَّلة={len(rec.advisory_articles)} {list(rec.advisory_articles)}")
    except (SovereigntyViolation, RoyalImpersonation) as exc:
        FAILURES.append(f"سيادي مرفوض: {action} — {type(exc).__name__}")
        print(f"  ✗ {action:22} → رُفض! {type(exc).__name__}: {exc}")

print()
print("=" * 72)
print("ب — المسار التابع: نفس الأفعال بلا مرسوم (يجب أن تبقى مرفوضة)")
print("=" * 72)
gw2 = SovereignGateway()
for action, target, crit in CASES:
    req = ActionRequest(actor=Branch.EXECUTIVE, action=action, target=target,
                        criticality=crit)
    try:
        gw2.execute(req, lambda: "نُفِّذ")
        FAILURES.append(f"تابع نُفِّذ رغم المخالفة: {action}")
        print(f"  ✗ {action:22} → نُفِّذ! (خلل: التابع تجاوز الدستور)")
    except SovereigntyViolation as exc:
        arts = ", ".join(exc.verdict.blocking_articles)
        print(f"  ✓ {action:22} → مُنع بالمواد {arts}")

print()
print("=" * 72)
print("ج — انتحال الصفة الملكية: توقيع مزيّف ومرسوم مفقود")
print("=" * 72)
gw3 = SovereignGateway()
bad = royal_request("pardon", "agent-1", "critical")
tampered = RoyalDecree.from_dict({**bad.royal_decree.to_dict(),
                                  "signature_hex": "aa" * 64})
for label, req in [
    ("توقيع غير صحيح", ActionRequest(actor=Branch.ROYAL, action="pardon",
                                     target="agent-1", criticality="critical",
                                     royal_decree=tampered)),
    ("بلا مرسوم", ActionRequest(actor=Branch.ROYAL, action="pardon",
                                target="agent-1", criticality="critical")),
]:
    try:
        gw3.execute(req, lambda: "نُفِّذ")
        FAILURES.append(f"منتحِل نُفِّذ: {label}")
        print(f"  ✗ {label:20} → نُفِّذ! (خلل أمني جسيم)")
    except RoyalImpersonation as exc:
        print(f"  ✓ {label:20} → رُفض · حدث={exc.event_kind.value}")
    except SovereigntyViolation as exc:
        # الرفض واقع، لكنه جاء من المسار الدستوري لا من إثبات الأصالة —
        # فالحدث الأمني غائب، وهذا خللٌ يُسجَّل بنصّه لا يُبتلع.
        FAILURES.append(f"رفض بلا حدث أمني: {label} — {exc}")
        print(f"  ~ {label:20} → رُفض دستوريًّا بلا حدث أمني: {exc}")

print()
print("الأحداث الأمنية المُسجَّلة في مسار الانتحال:",
      [e.kind.value for e in gw3.security_log.events])
print("الأحداث الأمنية في المسار السيادي:",
      sorted({e.kind.value for e in gw.security_log.events}))

print()
print("=" * 72)
if FAILURES:
    print("✗ الإثبات ساقط — نُقض مسار أو أكثر:")
    for f in FAILURES:
        print(f"    - {f}")
    raise SystemExit(1)
print("✓ الإثبات تام: السيادي نُفِّذ، والتابع مُنع، والمنتحِل رُفض بحدث أمني.")
raise SystemExit(0)
