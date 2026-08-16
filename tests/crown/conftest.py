"""الهدف: تجهيزات مشتركة لاختبارات التاج — مفاتيح عابرة ومرساة ومراسم صالحة.

المالك: tests/crown/ — التاج
تاريخ الإنشاء: 2026-08-16
تاريخ آخر تعديل: 2026-08-16

كل مفتاح خاص في هذه التجهيزات **عابر في الذاكرة** يُولَّد عند تشغيل الاختبار
ويزول بانتهائه. ولا يُكتب مفتاح خاص إلى قرص ولا إلى المستودع، لأن اختبارًا يخزّن
مفتاحًا يُبطل الحماية التي يزعم إثباتها.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from core.crown.audit import CrownAudit
from core.crown.key_registry import (
    CrownKeyRecord,
    CrownKeyRegistry,
    KeyProvenance,
    KeyState,
    LineageKind,
)
from core.crown.trust_anchor import (
    DOMAIN_TAG_ANCHOR,
    AnchorSource,
    CrownTrustAnchor,
    SignedKeyManifest,
    TrustPlane,
)


def anchor_fingerprint(root_id: str, root_public_key_hex: str) -> str:
    """بصمة الأصل كما تحسبها المرساة — هي ما يُطبَع ويُثبَّت خارج القناة.

    وهي بصمة لا مفتاح: نشرها لا يضر، وتغييرها هو الهجوم الحقيقي.
    """
    import hashlib

    return hashlib.sha256(
        f"{DOMAIN_TAG_ANCHOR}:{root_id}:{root_public_key_hex.lower()}".encode()
    ).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment: datetime) -> str:
    return moment.replace(microsecond=0).isoformat()


class TransientSigner:
    """موقِّع عابر للاختبار: مفتاح Ed25519 في الذاكرة لا يُكتب ولا يُصدَّر.

    وسبب وجوده أن الاختبار الحقيقي يحتاج توقيعات حقيقية: اختبارٌ يُزيّف نتيجة
    التحقق لا يُثبت شيئًا عن التحقق.
    """

    def __init__(self) -> None:
        self._private = ed25519.Ed25519PrivateKey.generate()

    @property
    def public_hex(self) -> str:
        return self._private.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()

    def sign(self, payload: bytes) -> str:
        return self._private.sign(payload).hex()


@pytest.fixture
def root_signer() -> TransientSigner:
    """موقِّع الأصل — يوقّع بيان المفاتيح ولا يوقّع الأوامر."""
    return TransientSigner()


@pytest.fixture
def crown_signer() -> TransientSigner:
    """موقِّع التاج — يوقّع الأوامر الملكية ولا يوقّع البيان.

        الفصل بين هذا وسابقه ليس ترتيبًا شكليًّا: من وقّع البيان بمفتاح التاج جعل
        الشرعية تُصادق على نفسها.
    """
    return TransientSigner()


@pytest.fixture
def successor_signer() -> TransientSigner:
    return TransientSigner()


def make_provenance(
    *,
    ceremony_id: str = "CER-TEST-0001",
    ceremony_kind: str = "CROWN_GENESIS",
    witnesses: tuple[str, ...] = ("W1", "W2", "W3"),
) -> KeyProvenance:
    return KeyProvenance(
        ceremony_id=ceremony_id,
        ceremony_kind=ceremony_kind,
        keystore_kind="TEST_EPHEMERAL",
        attestation_ref="tests/crown/conftest.py",
        witnesses=witnesses,
        out_of_band_verified=True,
        notes="مفتاح عابر لاختبار تنفيذي.",
    )


@pytest.fixture
def registry(crown_signer: TransientSigner) -> CrownKeyRegistry:
    """سجل مفاتيح بمفتاح تأسيس نشط واحد."""
    reg = CrownKeyRegistry()
    reg.register(
        CrownKeyRecord(
            key_id="CROWN-K1",
            version=1,
            algorithm="Ed25519",
            public_key_hex=crown_signer.public_hex,
            state=KeyState.PENDING,
            lineage_kind=LineageKind.GENESIS,
            predecessor_key_id=None,
            registered_at=iso(utc_now() - timedelta(days=2)),
            provenance=make_provenance(),
        )
    )
    reg.activate("CROWN-K1", at=iso(utc_now() - timedelta(days=1)))
    return reg


@pytest.fixture
def independent_sources(root_signer: TransientSigner) -> tuple[AnchorSource, ...]:
    """ثلاثة مستويات مستقلة لا يملكها التطبيق: بصمة مطبوعة، وأصل خارج الشبكة، وإشهاد بشري."""
    fingerprint = anchor_fingerprint("ROOT-1", root_signer.public_hex)
    return (
        AnchorSource(
            plane=TrustPlane.PRINTED_FINGERPRINT,
            locator="سجل ورقي في خزانة محرزة",
            fingerprint=fingerprint,
            verified_at=iso(utc_now()),
            verifier="أمين السجل",
        ),
        AnchorSource(
            plane=TrustPlane.OFFLINE_ROOT,
            locator="أصل معزول خارج الشبكة",
            fingerprint=fingerprint,
            verified_at=iso(utc_now()),
            verifier="حافظ الأصل",
        ),
        AnchorSource(
            plane=TrustPlane.HUMAN_OUT_OF_BAND,
            locator="مطابقة شفوية بإشهاد",
            fingerprint=fingerprint,
            verified_at=iso(utc_now()),
            verifier="شاهد ثالث",
        ),
    )


@pytest.fixture
def anchor(
    root_signer: TransientSigner,
    independent_sources: tuple[AnchorSource, ...],
    registry: CrownKeyRegistry,
) -> CrownTrustAnchor:
    """مرساة ثقة مثبَّتة على بصمة المفتاح النشط بعد تحقق خارج القناة."""
    return CrownTrustAnchor(
        root_id="ROOT-1",
        root_public_key_hex=root_signer.public_hex,
        sources=independent_sources,
        pinned_active_fingerprint=registry.active_or_raise().fingerprint,
    )


def sign_manifest(
    signer: TransientSigner,
    reg: CrownKeyRegistry,
    *,
    root_key_id: str = "ROOT-1",
    mutate: dict[str, Any] | None = None,
) -> SignedKeyManifest:
    """وقّع بيان مفاتيح توقيعًا حقيقيًّا، مع إمكان تحريفه لاختبار الخصومة.

    و``mutate`` تُطبَّق **قبل** التوقيع أو **بعده** حسب ما يطلبه الاختبار: هنا تُطبَّق
    بعد التوقيع كي يمثّل التحريف عبثًا بالبيان لا توقيعًا صحيحًا لبيان آخر.
    """
    manifest = reg.manifest()
    payload = json.dumps(
        manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    from core.crown.key_registry import DOMAIN_TAG_MANIFEST

    signature = signer.sign(DOMAIN_TAG_MANIFEST.encode() + b"\n" + payload.encode())
    if mutate:
        manifest = {**manifest, **mutate}
    return SignedKeyManifest(
        manifest=manifest, signature_hex=signature, root_key_id=root_key_id
    )


@pytest.fixture
def audit() -> CrownAudit:
    return CrownAudit()
