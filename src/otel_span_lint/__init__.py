"""Lint OpenTelemetry spans from OTLP JSON against HTTP semantic conventions v1.26.0."""

from __future__ import annotations

import logging

from .errors import SpanLintError, SpanLintErrorCode
from .linter import lint_document, lint_file
from .models import Finding, Severity
from .semconv import DEFAULT_RULES, RuleTable

logging.getLogger(__name__).addHandler(logging.NullHandler())

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_RULES",
    "Finding",
    "RuleTable",
    "Severity",
    "SpanLintError",
    "SpanLintErrorCode",
    "__version__",
    "lint_document",
    "lint_file",
]
