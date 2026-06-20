# Further learning resources

Curated, canonical primary sources for this repo's named learning tech:
design patterns (with a focus on Observer / event subscription) across Python
and Node, and the event-driven / DDD ideas they grow into.

Last verified: 2026-06-21

## Observer / event-subscription pattern

- **Design Patterns: Elements of Reusable Object-Oriented Software** (Gamma,
  Helm, Johnson, Vlissides; Addison-Wesley) -- the original GoF book; the
  Observer chapter is the canonical statement of the pattern's intent,
  participants, and consequences.
- **Refactoring.Guru -- Observer** -- https://refactoring.guru/design-patterns/observer
  -- approachable, language-by-language walkthrough of structure, applicability,
  and pros/cons; good cross-check against your implementation.

## Python-native event/observer idioms

- **Python `unittest` documentation** -- https://docs.python.org/3/library/unittest.html
  -- the stdlib test framework used by the Python tests here; covers TestCase,
  assertions, and `unittest.main`.
- **Python data classes (`dataclasses`)** -- https://docs.python.org/3/library/dataclasses.html
  -- `frozen=True` dataclasses model the immutable event payload; the value-object
  building block referenced in the repo's "records/data classes" theme.
- **`typing` / `collections.abc.Callable`** -- https://docs.python.org/3/library/typing.html
  -- typing callables is how Python expresses "an observer is just a function",
  the modern, class-free form of the GoF pattern.
- **blinker** -- https://blinker.readthedocs.io/ -- the de-facto Python signal
  library (used by Flask); the production upgrade target with weak references,
  named senders, and namespaced signals.

## JavaScript / Node-native event idioms

- **Node.js `events` (EventEmitter)** -- https://nodejs.org/api/events.html -- the
  built-in observer in Node: `.on` / `.emit` / `.once` / `.off`; the direct
  upgrade target for the JS implementation here.
- **Node.js `assert`** -- https://nodejs.org/api/assert.html -- the assertion
  module backing the `.test.mjs` tests in this repo.
- **MDN -- EventTarget** -- https://developer.mozilla.org/en-US/docs/Web/API/EventTarget
  -- the web-standard subject/observer API (`addEventListener` / `dispatchEvent`),
  usable in browsers and Workers; pairs with AbortController for unsubscription.
- **MDN -- AbortController** -- https://developer.mozilla.org/en-US/docs/Web/API/AbortController
  -- the standard "disposer" mechanism that mirrors the unsubscribe function this
  project's `subscribe` returns.
- **RxJS** -- https://rxjs.dev -- reactive Observables/Subjects for when you need
  streams of events over time, composition operators, and back-pressure.

## Event-driven architecture & Domain Events (DDD)

- **Martin Fowler -- Domain Event** -- https://martinfowler.com/eaaDev/DomainEvent.html
  -- defines the past-tense domain fact (`OrderPlaced`) that this in-process bus
  evolves into within DDD.
- **microservices.io -- Transactional Outbox pattern** -- https://microservices.io/patterns/data/transactional-outbox.html
  -- the canonical pattern for durable, reliable event publishing; the bridge from
  in-memory Observer to a real broker.
- **Apache Kafka documentation** -- https://kafka.apache.org/documentation/ -- a
  durable, ordered, replayable log; the "use a message queue/broker instead" answer
  when ordering and durability matter.
- **RabbitMQ tutorials** -- https://www.rabbitmq.com/tutorials -- publish/subscribe
  and routing with acknowledgements and dead-letter queues; the other common broker
  upgrade target.
