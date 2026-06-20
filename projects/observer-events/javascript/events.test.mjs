// Tests for the Observer / event-subscription EventBus using node:assert.
// Run (exits non-zero on failure):
//   node projects/observer-events/javascript/events.test.mjs

import assert from "node:assert/strict";
import {
  ORDER_PLACED,
  AuditLog,
  EmailService,
  EventBus,
  Metrics,
  placeOrder,
} from "./events.mjs";

// All observers are notified.
{
  const bus = new EventBus();
  const email = new EmailService();
  const audit = new AuditLog();
  const metrics = new Metrics();
  bus.subscribe(ORDER_PLACED, email.onOrderPlaced);
  bus.subscribe(ORDER_PLACED, audit.onOrderPlaced);
  bus.subscribe(ORDER_PLACED, metrics.onOrderPlaced);

  const errors = placeOrder(bus, { id: "A-1", customer: "ada@example.com", amountCents: 12_500 });

  assert.deepEqual(errors, []);
  assert.deepEqual(email.sent, ["Order A-1 confirmed for ada@example.com"]);
  assert.deepEqual(audit.entries, ["PLACED id=A-1 amount_cents=12500"]);
  assert.equal(metrics.orders, 1);
  assert.equal(metrics.revenueCents, 12_500);
}

// Observers fire in subscription order.
{
  const bus = new EventBus();
  const order = [];
  bus.subscribe("e", () => order.push("first"));
  bus.subscribe("e", () => order.push("second"));
  bus.subscribe("e", () => order.push("third"));
  bus.emit("e");
  assert.deepEqual(order, ["first", "second", "third"]);
}

// Unsubscribe via the returned disposer.
{
  const bus = new EventBus();
  const hits = [];
  const dispose = bus.subscribe("tick", () => hits.push(1));
  bus.emit("tick");
  dispose();
  bus.emit("tick");
  assert.deepEqual(hits, [1]);
  assert.equal(bus.subscriberCount("tick"), 0);
}

// Unsubscribe is idempotent.
{
  const bus = new EventBus();
  const listener = () => {};
  bus.subscribe("e", listener);
  assert.equal(bus.unsubscribe("e", listener), true);
  assert.equal(bus.unsubscribe("e", listener), false);
  assert.equal(bus.unsubscribe("never-registered", listener), false);
}

// One failing observer does not break the others.
{
  const bus = new EventBus();
  const email = new EmailService();
  const metrics = new Metrics();
  bus.subscribe(ORDER_PLACED, email.onOrderPlaced);
  bus.subscribe(ORDER_PLACED, () => {
    throw new Error("downstream webhook timed out");
  });
  bus.subscribe(ORDER_PLACED, metrics.onOrderPlaced);

  const errors = placeOrder(bus, { id: "A-2", customer: "grace@example.com", amountCents: 9_900 });

  assert.equal(errors.length, 1);
  assert.match(errors[0].message, /webhook/);
  assert.deepEqual(email.sent, ["Order A-2 confirmed for grace@example.com"]);
  assert.equal(metrics.orders, 1);
  assert.equal(metrics.revenueCents, 9_900);
}

// Named events are isolated from each other.
{
  const bus = new EventBus();
  const placed = [];
  const cancelled = [];
  bus.subscribe("order.placed", (e) => placed.push(e.payload.id));
  bus.subscribe("order.cancelled", (e) => cancelled.push(e.payload.id));
  bus.emit("order.placed", { id: "A-3" });
  assert.deepEqual(placed, ["A-3"]);
  assert.deepEqual(cancelled, []);
}

// Emitting with no subscribers is safe.
{
  const bus = new EventBus();
  assert.deepEqual(bus.emit("nobody.listening", { id: "A-4" }), []);
}

// A listener may unsubscribe itself mid-notification without skipping others.
{
  const bus = new EventBus();
  const seen = [];
  let dispose;
  dispose = bus.subscribe("e", () => {
    seen.push("one_shot");
    dispose();
  });
  bus.subscribe("e", () => seen.push("survivor"));
  bus.emit("e");
  bus.emit("e");
  assert.deepEqual(seen, ["one_shot", "survivor", "survivor"]);
}

// The event object is frozen so observers cannot mutate it.
{
  const bus = new EventBus();
  let captured;
  bus.subscribe("e", (event) => {
    captured = event;
  });
  bus.emit("e", { id: "A-5" });
  assert.throws(() => {
    "use strict";
    captured.name = "other";
  }, TypeError);
}

// Negative amount is rejected before any observer runs.
{
  const bus = new EventBus();
  assert.throws(() => placeOrder(bus, { id: "A-6", customer: "x@example.com", amountCents: -1 }), /positive/);
}

// Non-function listeners are rejected.
{
  const bus = new EventBus();
  assert.throws(() => bus.subscribe("e", 42), TypeError);
}

console.log("ok");
