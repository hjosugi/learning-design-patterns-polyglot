"""Observer / event-subscription pattern in pure stdlib Python.

Intent
------
Let one object (the *Subject*, here an ``EventBus``) notify many
*observers* when something happens, WITHOUT the subject knowing who the
observers are or what they do. Observers ``subscribe`` to a named event
and are called with a payload when that event is ``emit``-ed.

This decouples "something happened" (an order was placed) from "things
that should react to it" (send an email, write an audit log, bump a
metric). New reactions can be added or removed without editing the code
that emits the event.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# An observer is just a callable that accepts the event payload.
# Using a plain Callable (instead of an Observer base class) is the
# Pythonic, "functions over classes" version of the GoF pattern.
Listener = Callable[["Event"], None]


@dataclass(frozen=True)
class Event:
    """The payload delivered to every observer of a named event.

    Frozen so an observer cannot mutate the event and surprise the next
    observer in the list. ``name`` lets a single listener be reused for
    several event types if desired.
    """

    name: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class EventBus:
    """The Subject. Holds subscriptions keyed by event name.

    Observers register interest in a *named* event. ``emit`` walks the
    current observers for that name and calls each one. A subscriber that
    raises does NOT stop the remaining subscribers from running, and the
    error is collected so a caller (or a test) can inspect what failed.
    """

    # name -> ordered list of listeners. Insertion order is preserved by
    # dict/list, so observers are notified in subscription order.
    _subscribers: dict[str, list[Listener]] = field(default_factory=dict)

    def subscribe(self, event_name: str, listener: Listener) -> Callable[[], None]:
        """Register ``listener`` for ``event_name``.

        Returns an ``unsubscribe`` callable. Returning a disposer (rather
        than forcing the caller to keep the original function around to
        pass back) is the same ergonomic idiom used by Node's
        ``EventTarget``/``AbortController`` and by libraries like blinker.
        """
        self._subscribers.setdefault(event_name, []).append(listener)

        def unsubscribe() -> None:
            self.unsubscribe(event_name, listener)

        return unsubscribe

    def unsubscribe(self, event_name: str, listener: Listener) -> bool:
        """Remove ``listener`` from ``event_name``.

        Returns ``True`` if a subscription was removed, ``False`` if the
        listener was not registered (idempotent: calling twice is safe).
        """
        listeners = self._subscribers.get(event_name)
        if not listeners or listener not in listeners:
            return False
        listeners.remove(listener)
        if not listeners:
            del self._subscribers[event_name]
        return True

    def emit(self, event_name: str, **payload: Any) -> list[Exception]:
        """Notify every observer of ``event_name`` with an :class:`Event`.

        We iterate over a *copy* of the listener list so a listener that
        unsubscribes (itself or another) during notification does not
        corrupt the iteration.

        One failing observer must not break the others, so each call is
        wrapped in try/except. Caught exceptions are returned to the
        caller instead of being swallowed silently.
        """
        event = Event(name=event_name, payload=dict(payload))
        errors: list[Exception] = []
        for listener in list(self._subscribers.get(event_name, [])):
            try:
                listener(event)
            except Exception as exc:  # noqa: BLE001 - isolation is the point
                errors.append(exc)
        return errors

    def subscriber_count(self, event_name: str) -> int:
        """How many observers are currently subscribed to ``event_name``."""
        return len(self._subscribers.get(event_name, []))


# ---------------------------------------------------------------------------
# Concrete domain: an order/stock pipeline.
#
# When an order is placed we want three independent reactions. None of
# them know about each other, and the code that places the order does not
# import any of them directly -- it only talks to the EventBus.
# ---------------------------------------------------------------------------

ORDER_PLACED = "order.placed"


class EmailService:
    """Observer that "sends" a confirmation email (records it instead)."""

    def __init__(self) -> None:
        self.sent: list[str] = []

    def on_order_placed(self, event: Event) -> None:
        order = event.payload
        self.sent.append(f"Order {order['id']} confirmed for {order['customer']}")


class AuditLog:
    """Observer that records an immutable trail of what happened."""

    def __init__(self) -> None:
        self.entries: list[str] = []

    def on_order_placed(self, event: Event) -> None:
        order = event.payload
        self.entries.append(f"PLACED id={order['id']} amount_cents={order['amount_cents']}")


class Metrics:
    """Observer that increments a counter and sums revenue."""

    def __init__(self) -> None:
        self.orders = 0
        self.revenue_cents = 0

    def on_order_placed(self, event: Event) -> None:
        self.orders += 1
        self.revenue_cents += event.payload["amount_cents"]


def place_order(bus: EventBus, order_id: str, customer: str, amount_cents: int) -> list[Exception]:
    """Domain action: persist the order (omitted) then announce it.

    The function returns whatever errors the observers raised so that a
    failure to, say, send an email does not silently disappear -- but it
    also does NOT abort the other observers.
    """
    if amount_cents < 0:
        raise ValueError("amount must be positive")
    return bus.emit(ORDER_PLACED, id=order_id, customer=customer, amount_cents=amount_cents)


def _demo() -> None:
    bus = EventBus()
    email, audit, metrics = EmailService(), AuditLog(), Metrics()

    bus.subscribe(ORDER_PLACED, email.on_order_placed)
    bus.subscribe(ORDER_PLACED, audit.on_order_placed)
    bus.subscribe(ORDER_PLACED, metrics.on_order_placed)

    # A flaky observer: one that explodes. It must not block the others.
    def flaky(_event: Event) -> None:
        raise RuntimeError("downstream webhook timed out")

    bus.subscribe(ORDER_PLACED, flaky)

    errors = place_order(bus, "A-1001", "ada@example.com", 12_500)
    print(f"emails: {email.sent}")
    print(f"audit:  {audit.entries}")
    print(f"metrics: orders={metrics.orders} revenue_cents={metrics.revenue_cents}")
    print(f"observer errors (isolated): {[str(e) for e in errors]}")


if __name__ == "__main__":
    _demo()
