# Learning Design Patterns Polyglot

Design patterns and architecture patterns compared across Python, TypeScript, Kotlin, and Java.

Last verified: 2026-06-20

## Runnable Starter Project

Start with one Strategy pattern exercise in two languages:

```bash
python3 projects/strategy-discount/python/strategy.py
node projects/strategy-discount/javascript/strategy.mjs
```

## Source Repositories

- `python-design-pattern`
- `ts-design-pattern`
- `kotlin-design-pattern`
- `design-java`

## What This Repo Teaches

This repo compares patterns by intent, not by class diagram.

Each pattern should answer:

- what problem it solves
- what simpler alternative should be tried first
- what the pattern looks like in Python, TypeScript, Kotlin, and Java
- what tests prove the pattern is doing useful work
- when the pattern becomes unnecessary ceremony
- how modern language features change the older GoF version

## Learning Path

1. Pattern intent
2. Minimal implementation
3. Tests
4. When to use
5. When not to use
6. Modern alternatives
7. Language-specific tradeoffs

## Planned Structure

```text
patterns/
  strategy/
  factory-method/
  adapter/
  decorator/
  observer/
architecture/
  hexagonal/
  ddd/
testing/
  contract-tests/
  test-data-builders/
docs/
  2026-learning-items.md
  repository-profile.md
```

## Standard Pattern Page

Each pattern directory should include:

- `intent.md`
- `when-to-use.md`
- `when-not-to-use.md`
- one implementation per language
- tests or a documented run command
- a short comparison table

## What Belongs Elsewhere

- full backend DDD applications belong in `learning-backend-ddd`
- language setup notes belong in `learning-build-systems`
- build tooling comparisons belong in `learning-build-systems`

## Repository Profile

See [docs/repository-profile.md](docs/repository-profile.md) for GitHub description, topics, public safety notes, and first milestones.
