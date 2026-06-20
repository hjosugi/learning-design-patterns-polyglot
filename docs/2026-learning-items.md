# 2026 Learning Items: Design Patterns Polyglot

Last verified: 2026-06-20

## Must Learn

### Patterns that still matter

- Strategy
- Factory
- Adapter
- Decorator
- Observer / event subscription
- Command
- Repository
- Unit of Work

### Modern alternatives

- functions over classes where simpler
- dependency injection without container abuse
- records/data classes/value objects
- discriminated unions and sealed types
- module boundaries before framework abstractions
- composition over inheritance

### Testing patterns

- contract tests
- characterization tests for legacy code
- test data builders
- fake vs mock
- approval tests for text output

## Repository Structure

```text
patterns/
  strategy/
    python/
    typescript/
    kotlin/
    java/
architecture/
  hexagonal/
  ddd/
testing/
  contract-tests/
  test-data-builders/
```

## Definition of Done

- Each pattern has `intent`, `problem`, `implementation`, `tests`, and `tradeoffs`.
- Each implementation has at least one test.
- Each pattern explains when not to use it.

