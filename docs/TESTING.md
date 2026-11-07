# Testing

## Running

```sh
uv run pytest --cov=otel_span_lint
```

## Policy

- Coverage must be at least 80%.
- Tests must reproduce bugs before fixes are applied.
- Tests are deterministic, relying on no external network or clock.

## Structure

- `tests/test_otel_span_lint.py`: Contains acceptance tests for all seven rules, CLI error paths, and edge cases like duplicates or empty spans.