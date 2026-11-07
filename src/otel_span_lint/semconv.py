"""Bundled semantic conventions for OpenTelemetry HTTP spans.

Source: open-telemetry/semantic-conventions v1.26.0
Docs: docs/http/http-spans.md
Transcribed: 2026-11-06
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RuleTable:
    """Rule configuration table defining required attributes, methods, and deprecated renames."""

    server_required: tuple[str, ...]
    client_required: tuple[str, ...]
    allowed_methods: frozenset[str]
    deprecated_renames: tuple[tuple[str, str], ...]


# Bundled data transcribed from semantic-conventions v1.26.0
DEFAULT_RULES = RuleTable(
    server_required=("http.request.method", "url.path", "url.scheme"),
    client_required=("http.request.method", "server.address", "server.port", "url.full"),
    allowed_methods=frozenset(
        {
            "CONNECT",
            "DELETE",
            "GET",
            "HEAD",
            "OPTIONS",
            "PATCH",
            "POST",
            "PUT",
            "TRACE",
            "_OTHER",
        }
    ),
    deprecated_renames=(
        ("http.method", "http.request.method"),
        ("http.status_code", "http.response.status_code"),
        ("http.url", "url.full"),
        ("http.scheme", "url.scheme"),
        ("http.user_agent", "user_agent.original"),
    ),
)
