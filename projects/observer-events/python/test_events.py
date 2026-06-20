"""unittest suite for the Observer / event-subscription EventBus.

Run directly (exits non-zero on failure):

    python3 projects/observer-events/python/test_events.py
"""

from __future__ import annotations

import unittest

from events import (
    ORDER_PLACED,
    AuditLog,
    EmailService,
    Event,
    EventBus,
    Metrics,
    place_order,
)


class EventBusTest(unittest.TestCase):
    def test_multiple_observers_all_notified(self) -> None:
        bus = EventBus()
        email, audit, metrics = EmailService(), AuditLog(), Metrics()
        bus.subscribe(ORDER_PLACED, email.on_order_placed)
        bus.subscribe(ORDER_PLACED, audit.on_order_placed)
        bus.subscribe(ORDER_PLACED, metrics.on_order_placed)

        errors = place_order(bus, "A-1", "ada@example.com", 12_500)

        self.assertEqual(errors, [])
        self.assertEqual(email.sent, ["Order A-1 confirmed for ada@example.com"])
        self.assertEqual(audit.entries, ["PLACED id=A-1 amount_cents=12500"])
        self.assertEqual(metrics.orders, 1)
        self.assertEqual(metrics.revenue_cents, 12_500)

    def test_observers_notified_in_subscription_order(self) -> None:
        bus = EventBus()
        order: list[str] = []
        bus.subscribe("e", lambda _e: order.append("first"))
        bus.subscribe("e", lambda _e: order.append("second"))
        bus.subscribe("e", lambda _e: order.append("third"))

        bus.emit("e")

        self.assertEqual(order, ["first", "second", "third"])

    def test_unsubscribe_via_returned_disposer(self) -> None:
        bus = EventBus()
        hits: list[int] = []
        dispose = bus.subscribe("tick", lambda _e: hits.append(1))

        bus.emit("tick")
        dispose()
        bus.emit("tick")

        self.assertEqual(hits, [1])
        self.assertEqual(bus.subscriber_count("tick"), 0)

    def test_unsubscribe_is_idempotent(self) -> None:
        bus = EventBus()
        listener = lambda _e: None  # noqa: E731
        bus.subscribe("e", listener)
        self.assertTrue(bus.unsubscribe("e", listener))
        # Removing again is safe and reports nothing was removed.
        self.assertFalse(bus.unsubscribe("e", listener))
        self.assertFalse(bus.unsubscribe("never-registered", listener))

    def test_failing_observer_does_not_break_others(self) -> None:
        bus = EventBus()
        email, metrics = EmailService(), Metrics()

        def flaky(_event: Event) -> None:
            raise RuntimeError("downstream webhook timed out")

        # The flaky observer sits BETWEEN two healthy ones to prove the
        # ones after it still run.
        bus.subscribe(ORDER_PLACED, email.on_order_placed)
        bus.subscribe(ORDER_PLACED, flaky)
        bus.subscribe(ORDER_PLACED, metrics.on_order_placed)

        errors = place_order(bus, "A-2", "grace@example.com", 9_900)

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], RuntimeError)
        self.assertEqual(email.sent, ["Order A-2 confirmed for grace@example.com"])
        self.assertEqual(metrics.orders, 1)
        self.assertEqual(metrics.revenue_cents, 9_900)

    def test_named_events_are_isolated(self) -> None:
        bus = EventBus()
        placed: list[str] = []
        cancelled: list[str] = []
        bus.subscribe("order.placed", lambda e: placed.append(e.payload["id"]))
        bus.subscribe("order.cancelled", lambda e: cancelled.append(e.payload["id"]))

        bus.emit("order.placed", id="A-3")

        self.assertEqual(placed, ["A-3"])
        self.assertEqual(cancelled, [])

    def test_emit_with_no_subscribers_is_safe(self) -> None:
        bus = EventBus()
        self.assertEqual(bus.emit("nobody.listening", id="A-4"), [])

    def test_listener_unsubscribing_during_emit_is_safe(self) -> None:
        # Iterating a copy means a listener can dispose itself mid-notify
        # without skipping or crashing the remaining listeners.
        bus = EventBus()
        seen: list[str] = []
        dispose: list = []

        def one_shot(_e: Event) -> None:
            seen.append("one_shot")
            dispose[0]()

        dispose.append(bus.subscribe("e", one_shot))
        bus.subscribe("e", lambda _e: seen.append("survivor"))

        bus.emit("e")
        bus.emit("e")

        self.assertEqual(seen, ["one_shot", "survivor", "survivor"])

    def test_event_payload_is_immutable(self) -> None:
        event = Event(name="e", payload={"id": "A-5"})
        with self.assertRaises(Exception):
            event.name = "other"  # type: ignore[misc]

    def test_negative_amount_rejected(self) -> None:
        bus = EventBus()
        with self.assertRaises(ValueError):
            place_order(bus, "A-6", "x@example.com", -1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
