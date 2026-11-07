"""CLI entrypoint for otel-span-lint."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict

from .errors import SpanLintError
from .linter import lint_file


def main(argv: Sequence[str] | None = None) -> int:
    """CLI main function."""
    parser = argparse.ArgumentParser(description="Lint OpenTelemetry spans from OTLP JSON files.")
    parser.add_argument("file", help="Path to OTLP JSON file")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    try:
        findings = lint_file(args.file)
    except SpanLintError as err:
        sys.stderr.write(f"Error: {err}\n")
        return 2
    except Exception as err:  # pragma: no cover
        sys.stderr.write(f"Unexpected error: {err}\n")
        return 2

    if args.format == "json":
        out = [asdict(f) for f in findings]
        sys.stdout.write(json.dumps(out, indent=2) + "\n")
    else:
        for f in findings:
            sys.stdout.write(
                f"trace={f.trace_id} span={f.span_id} {f.rule} {f.severity} {f.message}\n"
            )

    has_errors = any(f.severity == "error" for f in findings)
    has_warnings = any(f.severity == "warning" for f in findings)

    if has_errors:
        return 1
    if args.strict and has_warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
