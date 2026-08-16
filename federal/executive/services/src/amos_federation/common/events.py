"""
AMOS-Federation Event Publisher + Hash Chain
الهدف: نشر الأحداث على NATS JetStream مع سلسلة كتل للتدقيق
النطاق: كل الخدمات التي تنشر أحداثًا
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

import hashlib
import json
import uuid
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

try:
    import nats

    _NATS_AVAILABLE = True
except ImportError:
    _NATS_AVAILABLE = False
    nats = None

import structlog

from amos_federation.common.config import settings
from amos_federation.common.database import db_cursor

logger = structlog.get_logger()

# بادئة subject لكل أحداث AMOS
EVENT_SUBJECT_PREFIX = "amos_federation"

# البصمة التأسيسية لأول حدث في السلسلة
GENESIS_HASH = "sha256:0000000000000000000000000000000000000000000000000000000000000000"


def compute_chain_hash(prev_hash: str, event_data: dict[str, Any]) -> str:
    """
    حساب بصمة SHA-256 للحدث الحالي.
    chain_hash = SHA256(prev_hash + canonical_json(event_data))
    """
    canonical = json.dumps(event_data, sort_keys=True, ensure_ascii=False)
    combined = f"{prev_hash}:{canonical}"
    return f"sha256:{hashlib.sha256(combined.encode('utf-8')).hexdigest()}"


def get_last_chain_hash() -> str:
    """الحصول على آخر بصمة في سلسلة التدقيق من قاعدة البيانات."""
    try:
        with db_cursor() as cur:
            cur.execute("SELECT chain_hash FROM audit_log ORDER BY seq DESC LIMIT 1")
            row = cur.fetchone()
            if row:
                return row["chain_hash"]
    except Exception as e:
        logger.warning("Could not fetch last chain hash, using genesis", error=str(e))
    return GENESIS_HASH


class EventPublisher:
    """ناشر الأحداث — يربط NATS JetStream (إن توفّر) أو EventBus المحلي + Audit Log + Hash Chain"""

    def __init__(self):
        self._nc = None
        self._local_bus = None

    async def connect(self):
        """الاتصال بـ NATS JetStream أو EventBus المحلي"""
        if _NATS_AVAILABLE:
            try:
                self._nc = await nats.connect(settings.nats_url)
                self._js = self._nc.jetstream()
                with suppress(Exception):
                    await self._js.add_stream(
                        name=settings.nats_stream,
                        subjects=[f"{EVENT_SUBJECT_PREFIX}.>"],
                        max_age=settings.nats_retention_days * 86400,
                    )
                logger.info("event_publisher.connected", nats_url=settings.nats_url)
                return
            except Exception as e:
                logger.warning("event_publisher.nats_unavailable", error=str(e))

        # Fallback: EventBus محلي دائم
        from amos_federation.common.event_bus import get_event_bus

        self._local_bus = get_event_bus()
        logger.info("event_publisher.using_local_bus")

    async def close(self):
        """إغلاق الاتصال"""
        if self._nc:  # pragma: no branch - requires live NATS connection (production-only)
            await self._nc.drain()
            await self._nc.close()

    async def publish(
        self,
        event_type: str,
        source: str,
        data: dict[str, Any],
        actor_type: str = "system",
        actor_id: str | None = None,
    ) -> str:
        """
        نشر حدث على NATS + تسجيل في audit_log مع hash chain.

        Args:
            event_type: نوع الحدث (مثل task.created)
            source: الخدمة المصدرة (مثل api-gateway)
            data: بيانات الحدث
            actor_type: نوع الفاعل (system, agent, human, governance)
            actor_id: معرّف الفاعل

        Returns:
            event_id المُنشأ
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()

        # بناء حمولة الحدث
        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "source": source,
            "data": data,
        }

        # حساب سلسلة البصمات
        prev_hash = get_last_chain_hash()
        chain_hash = compute_chain_hash(prev_hash, event)

        # إدراج في سجل التدقيق الملحق فقط عند توفر قاعدة البيانات.
        action = f"{event_type}"
        try:
            with db_cursor() as cur:
                cur.execute(
                    """INSERT INTO audit_log
                       (event_id, timestamp, event_type, actor_type, actor_id,
                        action, chain_hash, prev_hash, metadata)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        event_id,
                        timestamp,
                        event_type,
                        actor_type,
                        actor_id,
                        action,
                        chain_hash,
                        prev_hash,
                        json.dumps(data, ensure_ascii=False),
                    ),
                )
        except Exception as error:
            logger.warning(
                "event.audit_not_persisted",
                event_id=event_id,
                event_type=event_type,
                error=str(error),
            )

        # نشر الحدث إلى NATS أو EventBus المحلي
        subject = f"{EVENT_SUBJECT_PREFIX}.{event_type}"
        event_with_hash = {**event, "chain_hash": chain_hash}

        if self._nc:  # pragma: no branch - requires live NATS connection (production-only)
            payload = json.dumps(event_with_hash, ensure_ascii=False).encode("utf-8")
            await self._js.publish(subject, payload)
            logger.info(
                "event.published",
                event_id=event_id,
                event_type=event_type,
                subject=subject,
                chain_hash=chain_hash[:20] + "...",
            )
        elif self._local_bus:  # pragma: no branch - requires connect() fallback (production-only)
            self._local_bus.publish(subject, event_with_hash)
            logger.info(
                "event.published_local",
                event_id=event_id,
                event_type=event_type,
                subject=subject,
            )
        else:
            # محاولة استخدام EventBus بدون اتصال صريح
            from amos_federation.common.event_bus import get_event_bus

            get_event_bus().publish(subject, event_with_hash)
            logger.info("event.published_fallback", event_id=event_id, subject=subject)

        return event_id

    async def verify_chain(self) -> bool:
        """
        التحقق من سلامة سلسلة الكتل في audit_log.
        يعيد True إذا كانت السلسلة سليمة، False إذا وُجد تلاعب.
        """
        try:
            with db_cursor() as cur:
                cur.execute(
                    "SELECT event_id, chain_hash, prev_hash, metadata "
                    "FROM audit_log ORDER BY seq ASC"
                )
                rows = cur.fetchall()
        except Exception as e:
            logger.error("chain.verify_failed", error=str(e))
            return False

        prev_hash = GENESIS_HASH
        for row in rows:
            expected_hash = compute_chain_hash(
                prev_hash,
                {
                    "event_id": row["event_id"],
                    "metadata": row["metadata"]
                    if isinstance(row["metadata"], dict)
                    else json.loads(row["metadata"]),
                },
            )
            if row["chain_hash"] != expected_hash:
                logger.error(
                    "chain.broken",
                    event_id=row["event_id"],
                    expected=expected_hash[:20] + "...",
                    actual=row["chain_hash"][:20] + "...",
                )
                return False
            prev_hash = row["chain_hash"]

        logger.info("chain.verified", total_events=len(rows))
        return True


# الكائن المفرد
event_publisher = EventPublisher()
