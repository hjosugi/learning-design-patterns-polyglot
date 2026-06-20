// Observer / event-subscription pattern in plain Node (no dependencies).
//
// Intent: one Subject (the EventBus) notifies many observers when
// something happens, without knowing who they are or what they do.
// Observers `subscribe` to a named event and get called with a payload
// when that event is `emit`-ed. This decouples "an order was placed"
// from the reactions to it (email, audit log, metrics).

// The Subject. Subscriptions are stored per event name. We use a Map of
// name -> Set so observers are unique per (event, listener) pair and
// removal is O(1). Sets also preserve insertion order, so observers are
// notified in subscription order.
export class EventBus {
  #subscribers = new Map();

  // Register `listener` for `eventName`. Returns an `unsubscribe`
  // function -- the same disposer idiom as DOM addEventListener +
  // AbortController and as RxJS subscriptions. Callers do not have to
  // hold on to the original function to remove it later.
  subscribe(eventName, listener) {
    if (typeof listener !== "function") {
      throw new TypeError("listener must be a function");
    }
    let listeners = this.#subscribers.get(eventName);
    if (!listeners) {
      listeners = new Set();
      this.#subscribers.set(eventName, listeners);
    }
    listeners.add(listener);
    return () => this.unsubscribe(eventName, listener);
  }

  // Remove `listener` from `eventName`. Idempotent: returns true if a
  // subscription was removed, false if it was not registered.
  unsubscribe(eventName, listener) {
    const listeners = this.#subscribers.get(eventName);
    if (!listeners || !listeners.has(listener)) {
      return false;
    }
    listeners.delete(listener);
    if (listeners.size === 0) {
      this.#subscribers.delete(eventName);
    }
    return true;
  }

  // Notify every observer of `eventName` with an event object.
  //
  // We iterate over a snapshot ([...listeners]) so a listener that
  // unsubscribes during notification does not corrupt the iteration.
  //
  // One failing observer must not break the others, so each call is
  // wrapped in try/catch. Caught errors are returned to the caller
  // instead of being swallowed.
  emit(eventName, payload = {}) {
    const event = Object.freeze({ name: eventName, payload });
    const errors = [];
    const listeners = this.#subscribers.get(eventName);
    if (!listeners) {
      return errors;
    }
    for (const listener of [...listeners]) {
      try {
        listener(event);
      } catch (err) {
        errors.push(err);
      }
    }
    return errors;
  }

  subscriberCount(eventName) {
    return this.#subscribers.get(eventName)?.size ?? 0;
  }
}

// ---------------------------------------------------------------------------
// Concrete domain: an order/stock pipeline. Three independent reactions
// to one event, none aware of the others, none imported by place_order.
// ---------------------------------------------------------------------------

export const ORDER_PLACED = "order.placed";

export class EmailService {
  sent = [];
  onOrderPlaced = (event) => {
    const order = event.payload;
    this.sent.push(`Order ${order.id} confirmed for ${order.customer}`);
  };
}

export class AuditLog {
  entries = [];
  onOrderPlaced = (event) => {
    const order = event.payload;
    this.entries.push(`PLACED id=${order.id} amount_cents=${order.amountCents}`);
  };
}

export class Metrics {
  orders = 0;
  revenueCents = 0;
  onOrderPlaced = (event) => {
    this.orders += 1;
    this.revenueCents += event.payload.amountCents;
  };
}

// Domain action: persist (omitted) then announce. Returns the observer
// errors so a failed reaction is visible but does not abort the others.
export function placeOrder(bus, { id, customer, amountCents }) {
  if (amountCents < 0) {
    throw new Error("amount must be positive");
  }
  return bus.emit(ORDER_PLACED, { id, customer, amountCents });
}

function demo() {
  const bus = new EventBus();
  const email = new EmailService();
  const audit = new AuditLog();
  const metrics = new Metrics();

  bus.subscribe(ORDER_PLACED, email.onOrderPlaced);
  bus.subscribe(ORDER_PLACED, audit.onOrderPlaced);
  bus.subscribe(ORDER_PLACED, metrics.onOrderPlaced);

  // A flaky observer that throws. It must not block the others.
  bus.subscribe(ORDER_PLACED, () => {
    throw new Error("downstream webhook timed out");
  });

  const errors = placeOrder(bus, {
    id: "A-1001",
    customer: "ada@example.com",
    amountCents: 12_500,
  });

  console.log(`emails: ${JSON.stringify(email.sent)}`);
  console.log(`audit:  ${JSON.stringify(audit.entries)}`);
  console.log(`metrics: orders=${metrics.orders} revenue_cents=${metrics.revenueCents}`);
  console.log(`observer errors (isolated): ${JSON.stringify(errors.map((e) => e.message))}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  demo();
}
