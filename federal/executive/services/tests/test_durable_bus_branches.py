"""
اختبارات الحالات الحدية لـ DurableEventBus
الهدف: تغطية الأفرع غير المغطاة في publish/poll/ack/replay/list_consumers
المالك: federal/executive/services
تاريخ الإنشاء: 2026-08-15
"""

from amos_federation.common.durable_event_bus import DurableEventBus


class TestDurableEventBusEdges:
    """حالات حدية لتغطية الأفرع الفائتة في DurableEventBus."""

    def _bus(self) -> DurableEventBus:
        return DurableEventBus()

    def test_publish_invalid_subject_still_stored(self) -> None:
        # validate_event returns False for malformed subject -> warning logged
        bus = self._bus()
        record = bus.publish("invalid-subject", {"k": "v"})
        assert "event_id" in record
        assert record["data"] == {"k": "v"}

    def test_handler_exception_is_caught(self) -> None:
        bus = self._bus()
        calls: list[dict] = []

        def bad_handler(event: dict) -> None:
            calls.append(event)
            raise RuntimeError("boom")

        bus.subscribe("amos_federation.edges.handler_error", bad_handler)
        # should not raise — handler error is caught and logged
        bus.publish("amos_federation.edges.handler_error", {"n": 1})
        assert len(calls) == 1

    def test_wildcard_handler_matching(self) -> None:
        bus = self._bus()
        calls: list[dict] = []
        bus.subscribe("amos_federation.edges.*", lambda e: calls.append(e))
        bus.publish("amos_federation.edges.created", {"x": 1})
        assert len(calls) >= 1

    def test_poll_subject_none_returns_all(self) -> None:
        bus = self._bus()
        bus.publish("amos_federation.poll.none1", {"a": 1})
        bus.publish("amos_federation.poll.none2", {"b": 2})
        rows = bus.poll("consumer-none", subject=None, limit=50)
        assert len(rows) >= 2

    def test_poll_subject_filtered(self) -> None:
        bus = self._bus()
        bus.publish("amos_federation.poll.filtered", {"a": 1})
        rows = bus.poll("consumer-filt", subject="amos_federation.poll.filtered", limit=10)
        assert all(r["subject"] == "amos_federation.poll.filtered" for r in rows)
        assert len(rows) >= 1

    def test_ack_missing_event_returns_false(self) -> None:
        bus = self._bus()
        assert bus.ack("consumer-x", "amos_federation.ack.missing", "evt-nonexistent") is False

    def test_ack_creates_then_updates_offset(self) -> None:
        bus = self._bus()
        subject = "amos_federation.ack.update"
        record = bus.publish(subject, {"v": 1})
        event_id = record["event_id"]
        # first ack creates the offset
        assert bus.ack("consumer-upd", subject, event_id) is True
        # second ack updates the existing offset
        assert bus.ack("consumer-upd", subject, event_id) is True

    def test_replay_from_offset(self) -> None:
        bus = self._bus()
        subject = "amos_federation.replay.offset"
        rec1 = bus.publish(subject, {"i": 1})
        rec2 = bus.publish(subject, {"i": 2})
        # ack first event -> offset set to rec1
        bus.ack("consumer-rep", subject, rec1["event_id"])
        # replay from offset -> should return rec2 onwards (not from beginning)
        rows = bus.replay("consumer-rep", subject=subject, from_beginning=False, limit=10)
        ids = [r["event_id"] for r in rows]
        assert rec2["event_id"] in ids
        assert rec1["event_id"] not in ids

    def test_replay_from_beginning(self) -> None:
        bus = self._bus()
        subject = "amos_federation.replay.beginning"
        bus.publish(subject, {"i": 1})
        rows = bus.replay("consumer-reb", subject=subject, from_beginning=True, limit=10)
        assert len(rows) >= 1

    def test_list_consumers(self) -> None:
        bus = self._bus()
        subject = "amos_federation.list.consumers"
        record = bus.publish(subject, {"v": 1})
        bus.ack("consumer-list", subject, record["event_id"])
        consumers = bus.list_consumers()
        assert any(c["consumer_name"] == "consumer-list" for c in consumers)

    def test_count_with_subject(self) -> None:
        bus = self._bus()
        subject = "amos_federation.count.subject"
        bus.publish(subject, {"v": 1})
        assert bus.count(subject=subject) >= 1
