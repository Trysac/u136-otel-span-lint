"""Data models for findings and rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warning"]


@dataclass(frozen=True, slots=True)
class Finding:
    """A single rule violation detected on an OpenTelemetry span."""

    rule: str
    severity: Severity
    trace_id: str
    span_id: str
    span_name: str
    message: str
