"""Typed errors for otel_span_lint."""

from __future__ import annotations

from typing import Literal

SpanLintErrorCode = Literal[
    "input_too_large",
    "too_many_spans",
    "invalid_document",
    "invalid_json",
]


class SpanLintError(Exception):
    """Base exception raised for invalid inputs or limits exceeded in span linting."""

    def __init__(self, message: str, code: SpanLintErrorCode) -> None:
        # Ensure error messages never exceed a safe bounded length
        truncated = message if len(message) <= 200 else message[:197] + "..."
        super().__init__(truncated)
        self.code: SpanLintErrorCode = code
