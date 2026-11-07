# Use bundled semantic convention table with deterministic sorting

Status: accepted (generated, pending human review)

## Context

OpenTelemetry semantic conventions evolve across versions. CI checks need strict, reproducible linting results without network access or live schema registries.

## Decision

Bundle an explicit, immutable RuleTable transcribed from semantic-conventions v1.26.0 for HTTP spans into src/otel_span_lint/semconv.py, and enforce deterministic finding ordering by (document span order, rule code, attribute key).

## Consequences

Linting behavior is completely reproducible, stdlib-only, dependency-free, and resilient to schema drift.
