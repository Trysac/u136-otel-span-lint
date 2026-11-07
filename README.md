# otel-span-lint

Lint OpenTelemetry spans from OTLP JSON against OpenTelemetry HTTP semantic conventions v1.26.0.

## The Problem

Instrumentation drifts from the OpenTelemetry semantic conventions: services still send `http.method`, forget `server.address` on client spans, or name server spans after raw URLs. This breaks dashboards and causes metric cardinality explosions. This library lints OTLP JSON exports against an explicit, bundled subset of the HTTP conventions with stable rule codes.

## Installation

`pip install trysac-otel-span-lint`

## Usage

```python
from otel_span_lint import lint_document

doc = {
    "resourceSpans": [
        {
            "scopeSpans": [
                {
                    "spans": [
                        {
                            "traceId": "0123456789abcdef0123456789abcdef",
                            "spanId": "0123456789abcdef",
                            "name": "GET",
                            "kind": 2,
                            "attributes": [
                                {"key": "http.request.method", "value": {"stringValue": "GET"}}
                            ],
                        }
                    ]
                }
            ]
        }
    ]
}
findings = lint_document(doc)
for f in findings:
    print(f.rule, f.severity, f.message)
```

## API Summary

- `lint_document(doc: Mapping[str, Any], *, rules: RuleTable = DEFAULT_RULES, max_spans: int = 1_000_000) -> list[Finding]`
- `lint_file(path: str | Path, *, rules: RuleTable = DEFAULT_RULES, max_bytes: int = 52_428_800, max_spans: int = 1_000_000) -> list[Finding]`
- `Finding(rule: str, severity: Literal['error', 'warning'], trace_id: str, span_id: str, span_name: str, message: str)`
- `RuleTable`: Configuration table for server/client required attributes and allowed methods.
- `SpanLintError`: Raised for inputs that are invalid (code `invalid_document`, `invalid_json`) or exceed limits (code `input_too_large`, `too_many_spans`).

## Why not manual review or Weaver?

Manual review is non-deterministic and tedious. Weaver is a general-purpose semantic convention enforcement tool for the OpenTelemetry specification, but `otel-span-lint` provides a dependency-free, lightweight CI check specifically for exported JSON without requiring a complex runtime or extensive configuration.

## Security

See [docs/SECURITY.md](docs/SECURITY.md) for the threat model and mitigation limits.