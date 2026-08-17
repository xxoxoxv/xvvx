"""الهدف: تنصيب التاج وحفظ مفتاحه العام والتحقق التعميّ من هوية الملك.

المالك: core/sovereignty/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

المفتاح الخاص للملك لا يُحفَظ في المستودع ولا في أي نظام تشغيلي للدولة، بأي حال
(المادة العاشرة · 6 · 3). هذه الوحدة تعرف المفتاح العام فقط.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

_LOG = logging.getLogger("amos.sovereignty.crown")

_REPO_ROOT = Path(__file__).resolve().parents[2]
CROWN_KEYS_PATH = _REPO_ROOT / "royal" / "crown" / "CROWN_KEYS.json"


class CrownError(Exception):
    """خطأ في شؤون التاج."""


class CrownNotProvisionedError(CrownError):
    """التاج غير مُنصَّب — الاختصاص الملكي مُجمَّد لا منقول (المادة العاشرة · 6 · 2)."""


class CrownTamperError(CrownError):
    """سجل مفاتيح التاج معبوث به."""


@dataclass(frozen=True, slots=True)
class Crown:
    """التاج المُنصَّب: هوية الملك ومفتاحه العام."""

    key_id: str
    public_key_hex: str
    provisioned_at: str
    holder: str

    @property
    def public_key(self) -> ed25519.Ed25519PublicKey:
        try:
            raw = bytes.fromhex(self.public_key_hex)
        except ValueError as exc:
            raise CrownTamperError(f"مفتاح التاج العام غير صالح: {exc}") from exc
        if len(raw) != 32:
            raise CrownTamperError(
                f"طول مفتاح Ed25519 يجب أن يكون 32 بايت، وُجد {len(raw)}."
            )
        return ed25519.Ed25519PublicKey.from_public_bytes(raw)

    def verify(self, message: bytes, signature: bytes) -> bool:
        """تحقق تعميّ حقيقي من توقيع الملك.

        فشل التحقق حدث أمني — محاولة انتحال صفة ملكية — فيُسجَّل ولا يُبتلع.
        """
        try:
            self.public_key.verify(signature, message)
        except InvalidSignature as exc:
            _LOG.warning(
                "فشل تحقق توقيع ملكي مقابل مفتاح التاج «%s»: %s — "
                "محاولة انتحال صفة ملكية محتملة.",
                self.key_id,
                exc.__class__.__name__,
            )
            return False
        return True


def _read_registry(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CrownTamperError(f"سجل مفاتيح التاج غير قابل للقراءة: {exc}") from exc
    if not isinstance(data, dict):
        raise CrownTamperError("سجل مفاتيح التاج يجب أن يكون كائن JSON.")
    return data


def load_crown(path: Path | None = None) -> Crown:
    """حمّل التاج المُنصَّب، أو ارفع CrownNotProvisionedError.

    الرفض هو الافتراض: أي نقص في السجل يُعامَل كعدم تنصيب، لا كتنصيب جزئي.
    """
    keys_path = path or CROWN_KEYS_PATH
    if not keys_path.exists():
        raise CrownNotProvisionedError(
            f"التاج غير مُنصَّب: لا يوجد {keys_path}. "
            "الاختصاص الملكي الحصري مُجمَّد ولا يُمنَح لأي طرف آخر."
        )
    data = _read_registry(keys_path)
    if data.get("status") != "provisioned":
        raise CrownNotProvisionedError(
            f"التاج غير مُنصَّب: الحالة «{data.get('status')}». "
            "الاختصاص الملكي الحصري مُجمَّد."
        )
    active_id = data.get("active_key_id")
    keys = data.get("keys")
    if not active_id or not isinstance(keys, list):
        raise CrownTamperError("سجل مفاتيح التاج ناقص: يلزم active_key_id و keys.")
    for entry in keys:
        if isinstance(entry, dict) and entry.get("key_id") == active_id:
            if entry.get("revoked"):
                raise CrownNotProvisionedError(
                    f"مفتاح التاج النشط «{active_id}» مسحوب. التاج غير مُنصَّب."
                )
            public_key_hex = entry.get("public_key_hex")
            if not isinstance(public_key_hex, str) or not public_key_hex:
                raise CrownTamperError(f"المفتاح «{active_id}» بلا مفتاح عام.")
            return Crown(
                key_id=active_id,
                public_key_hex=public_key_hex,
                provisioned_at=str(entry.get("provisioned_at", "")),
                holder=str(entry.get("holder", "الملك")),
            )
    raise CrownTamperError(
        f"المفتاح النشط «{active_id}» غير موجود في سجل المفاتيح."
    )


def crown_is_provisioned(path: Path | None = None) -> bool:
    """هل التاج مُنصَّب؟ لا يرفع استثناءً — لكن السبب يُسجَّل ولا يُبتلع."""
    try:
        load_crown(path)
    except CrownError as exc:
        _LOG.info("التاج غير متاح: %s", exc)
        return False
    return True


def provision_crown(
    private_key_out: Path,
    *,
    holder: str = "الملك",
    key_id: str | None = None,
    registry_path: Path | None = None,
) -> Crown:
    """مراسم التنصيب: توليد زوج مفاتيح، نشر العام، وكتابة الخاص خارج المستودع.

    يرفض الكتابة داخل المستودع (المادة العاشرة · 6 · 3)، ويرفض استبدال تاج
    مُنصَّب (المادة العاشرة · 3 · 1 — replace_crown_key).
    """
    keys_path = registry_path or CROWN_KEYS_PATH
    private_key_out = private_key_out.expanduser().resolve()

    if private_key_out.is_relative_to(_REPO_ROOT):
        raise CrownError(
            "المفتاح الخاص للملك لا يُحفَظ داخل المستودع بأي حال "
            f"(المادة العاشرة · 6 · 3). المسار المرفوض: {private_key_out}"
        )

    if crown_is_provisioned(keys_path):
        raise CrownError(
            "التاج مُنصَّب بالفعل. استبدال مفتاح التاج فعل ممنوع "
            "(المادة العاشرة · 3 · 1 — replace_crown_key)."
        )

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_hex = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        .hex()
    )
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    resolved_key_id = key_id or f"crown-{now[:10]}"

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    private_key_out.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(private_key_out), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(pem)
        handle.flush()
        os.fsync(handle.fileno())

    registry = {
        "_note": (
            "سجل مفاتيح التاج. المفتاح العام فقط. "
            "المفتاح الخاص للملك لا يُحفَظ في المستودع (المادة العاشرة · 6 · 3)."
        ),
        "status": "provisioned",
        "active_key_id": resolved_key_id,
        "keys": [
            {
                "key_id": resolved_key_id,
                "holder": holder,
                "algorithm": "Ed25519",
                "public_key_hex": public_hex,
                "provisioned_at": now,
                "revoked": False,
            }
        ],
    }
    keys_path.parent.mkdir(parents=True, exist_ok=True)
    keys_path.write_text(
        json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return load_crown(keys_path)
