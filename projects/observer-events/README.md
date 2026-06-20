# Observer / Event Subscription

The same Observer (event-subscription) pattern in Python and JavaScript, using
only the standard library / runtime built-ins.

An `EventBus` (the *Subject*) lets observers `subscribe`/`unsubscribe` to a
**named** event and be notified with a payload when that event is emitted. The
worked domain is an order pipeline: placing an order fans out to three
independent observers -- an email service, an audit log, and a metrics counter --
none of which know about each other, and none imported by the code that places
the order.

Last verified: 2026-06-21

## Intent

Define a one-to-many dependency so that when one object changes state, all its
dependents are notified automatically -- without the subject knowing the
concrete observers. New reactions are added by subscribing, not by editing the
subject.

## Problem

`place_order` needs to trigger several side effects (confirmation email, audit
trail, metrics, maybe a webhook). The naive version hard-codes every call:

```python
def place_order(...):
    save(order)
    email.send(...)      # place_order now imports email,
    audit.write(...)     # audit, metrics, webhooks, ...
    metrics.increment()  # every new reaction edits this function
```

That couples the order code to every downstream concern, makes it hard to test
in isolation, and means one slow/failing side effect can sink the others. The
Observer pattern inverts this: `place_order` just announces "order.placed" and
each concern subscribes itself.

## Implementation

- `python/events.py` -- `EventBus` with `subscribe` (returns an `unsubscribe`
  disposer), `unsubscribe`, and `emit`. Observers are plain `Callable`s (the
  "functions over classes" form of the GoF pattern). Events are a frozen
  `dataclass` so an observer cannot mutate the payload seen by the next one.
- `javascript/events.mjs` -- `EventBus` backed by a `Map<string, Set>` with the
  same API and the `subscribe -> unsubscribe` disposer idiom.

Two behaviours are deliberately demonstrated:

1. **Unsubscribe.** `subscribe` returns a disposer function; calling it removes
   the observer so later emits skip it. `unsubscribe` is idempotent.
2. **Failure isolation.** Each observer call is wrapped in try/except (try/catch)
   so one throwing observer does **not** stop the others. The caught errors are
   *returned* from `emit`, not swallowed, so callers/tests can inspect them.

`emit` iterates over a snapshot of the observer list, so an observer that
unsubscribes itself (or another) during notification cannot corrupt iteration.

## Run

```bash
python3 projects/observer-events/python/events.py
node projects/observer-events/javascript/events.mjs
```

## Test

```bash
python3 projects/observer-events/python/test_events.py && node projects/observer-events/javascript/events.test.mjs
```

Python tests use `unittest`; JavaScript tests use `node:assert/strict`. Both are
non-interactive and exit non-zero on failure.

## Tradeoffs

- **Pro:** the subject is decoupled from observers; reactions are added/removed
  without touching the emitter; each observer is trivially unit-testable.
- **Pro:** failure isolation keeps one bad observer from breaking the flow.
- **Con:** control flow becomes implicit -- reading `place_order` no longer tells
  you everything that happens. Debugging "who reacts to this event?" needs a
  registry or grep.
- **Con:** notification is **synchronous and in-process** here. A slow observer
  blocks the emitter; nothing is persisted; if the process crashes mid-emit, the
  remaining observers never run.
- **Con:** ordering between observers is only "subscription order"; relying on it
  is fragile.

## When NOT to use it

Reach past an in-process event bus when:

- **Ordering or transactional guarantees matter.** If side effects must happen in
  a strict sequence, or all-or-nothing with the main write, prefer explicit calls
  (a Unit of Work / orchestrator) over fan-out.
- **Durability / delivery guarantees matter.** If a reaction must survive a crash,
  retry, or run in another service, use a real **message queue / broker**
  (RabbitMQ, Kafka, SQS, Redis Streams) with acknowledgements and a dead-letter
  queue -- not an in-memory list of callbacks.
- **There is exactly one consumer and it is stable.** Two coupled objects that
  always go together do not need the indirection; just call the method. Observer
  earns its keep only with multiple, varying, optional reactions.
- **Back-pressure / async work matters.** A long-running or I/O-bound observer
  should be a queued job, not a synchronous callback that stalls the emitter.

## Upgrade path

This hands-on is the from-scratch foundation. Map it to language-native and
production tools later:

- **Python -> callables / `blinker`.** Our `Callable` observers already are the
  idiomatic form. To get weak references (auto-cleanup when an observer is GC'd),
  named senders, and namespaced signals, swap `EventBus` for
  [`blinker`](https://blinker.readthedocs.io/): `signal("order.placed").connect(...)`
  / `.send(...)`. For async, replace synchronous `emit` with `asyncio` tasks or an
  `asyncio.Queue`.
- **JavaScript -> `EventTarget` / `EventEmitter`.** In the browser/Workers, an
  `EventTarget` + `CustomEvent` plus `AbortController` gives the same subscribe /
  dispatch / unsubscribe with standard semantics. In Node, `node:events`'
  `EventEmitter` (`.on` / `.emit` / `.off`) is the built-in equivalent; our
  disposer mirrors its `.off`. For streams of events over time, RxJS `Subject`.
- **Domain events in DDD.** Rename events to past-tense domain facts
  (`OrderPlaced`) raised by aggregates and dispatched after the transaction
  commits. To make delivery durable, adopt the **transactional outbox**: write
  events to an outbox table in the same DB transaction, then a relay publishes
  them to a broker. This is the bridge from "in-process Observer" to
  "event-driven architecture" and is exactly where the *When NOT to use it*
  caveats push you.

## Exercises

1. **Wildcard / catch-all observers.** Add support for subscribing to `"*"` so a
   single logger receives every event regardless of name. Add tests in both
   languages proving it fires for `order.placed` and `order.cancelled`.
2. **Once-only subscription.** Add `subscribe_once` / `subscribeOnce` that
   auto-unsubscribes after the first delivery (mirror Node's `EventEmitter.once`).
   Test that a second `emit` does not call it.
3. **Async observers in JS.** Make `emit` `await` async observers and aggregate
   their rejections with `Promise.allSettled`, still isolating failures. Add a
   test with one observer that rejects and one that resolves.
4. **Replace the bus with the native idiom.** Re-implement the JS demo on a
   `node:events` `EventEmitter` (or browser `EventTarget`) and the Python demo on
   `blinker`-style signals (or stick to stdlib callables), keeping the *same*
   tests green to prove the API shapes line up.
5. **Sketch the outbox.** Add an `OutboxObserver` that, instead of acting, appends
   the event to a list "to be published later", and write a test that drains the
   outbox. Note in a comment why this is the first step toward durable delivery.
```
