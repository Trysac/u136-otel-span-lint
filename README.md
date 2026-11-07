# otel-span-lint

[![PyPI version](https://img.shields.io/pypi/v/trysac-otel-span-lint)](https://pypi.org/project/trysac-otel-span-lint/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-otel-span-lint)](LICENSE)
[![CI](https://github.com/Trysac/u136-otel-span-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u136-otel-span-lint/actions/workflows/ci.yml)

Lint OpenTelemetry spans from OTLP JSON against a bundled table of HTTP semantic conventions v1.26.0: required, deprecated and malformed attributes

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-otel-span-lint
# or
uv add trysac-otel-span-lint
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import otel_span_lint

# normalize() trims surrounding whitespace and lower-cases the text.
print(otel_span_lint.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    otel_span_lint.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
