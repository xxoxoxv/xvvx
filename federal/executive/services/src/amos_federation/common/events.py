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
from datetime import datetime, timezone
from typing import Any

try:
    import nats
    _NATS_AVAILABLE = True
except ImportError:
    _NATS_AVAILABLE = False
    nats = None

import structlog

from amos_federation.common.config import settings

logger = structlog.get_logger()

# Subject prefix for all AMOS events
EVENT_SUBJECT_PREFIX = "amos_federation"

# Genesis hash for the first event in the chain
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
            cur.execute(
                "SELECT chain_hash FROM audit_log ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
            if row:
                return row["chain_hash"]
    except Exception as e:
        logger.warning("Could not fetch last chain hash, using genesis", error=str(e))
    return GENESIS_HASH


class EventPublisher:
    """ناشر الأحداث — يربط NATS + Audit Log + Hash Chain"""

    def __init__(self):
        self._nc = None

    async def connect(self):
        """الاتصال بـ NATS JetStream"""
        self._nc = await nats.connect(settings.nats_url)
        self._js = self._nc.jetstream()
        try:
            await self._js.add_stream(
                name=settings.nats_stream,
                subjects=[f"{EVENT_SUBJECT_PREFIX}.>"],
                max_age=settings.nats_retention_days * 86400,
            )
        except Exception:
            pass  # Stream already exists
        logger.info("event_publisher.connected", nats_url=settings.nats_url)

    async def close(self):
        """إغلاق الاتصال"""
        if self._nc:
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
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build event payload
        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "source": source,
            "data": data,
        }

        # Compute hash chain
        prev_hash = get_last_chain_hash()
        chain_hash = compute_chain_hash(prev_hash, event)

        # Insert into audit_log (append-only)
        action = f"{event_type}"
        with db_cursor() as cur:
            cur.execute(
                """INSERT INTO audit_log
                   (event_id, timestamp, event_type, actor_type, actor_id,
                    action, chain_hash, prev_hash, metadata)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
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

        # Publish to NATS
        subject = f"{EVENT_SUBJECT_PREFIX}.{event_type}"
        event_with_hash = {**event, "chain_hash": chain_hash}
        payload = json.dumps(event_with_hash, ensure_ascii=False).encode("utf-8")

        if self._nc:
            await self._js.publish(subject, payload)
            logger.info(
                "event.published",
                event_id=event_id,
                event_type=event_type,
                subject=subject,
                chain_hash=chain_hash[:20] + "...",
            )
        else:
            logger.warning("event.not_published_no_connection", event_id=event_id)

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
                    "FROM audit_log ORDER BY id ASC"
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
                    "metadata": row["metadata"] if isinstance(row["metadata"], dict) else json.loads(row["metadata"]),
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


# Singleton
event_publisher = EventPublisher()
