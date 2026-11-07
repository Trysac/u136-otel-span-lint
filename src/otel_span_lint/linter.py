"""Core linting implementation for OTLP JSON documents."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .errors import SpanLintError
from .models import Finding
from .semconv import DEFAULT_RULES, RuleTable

KIND_SERVER = 2
KIND_CLIENT = 3

STATUS_CODE_ERROR = 2


def _extract_attributes(raw_attrs: Any) -> dict[str, Any]:
    """Extract span attributes where the last key wins."""
    if not isinstance(raw_attrs, list):
        return {}
    result: dict[str, Any] = {}
    for item in raw_attrs:
        if isinstance(item, dict) and "key" in item and isinstance(item["key"], str):
            val_container = item.get("value")
            result[item["key"]] = val_container
    return result


def _get_attribute_raw_string(val_container: Any) -> str | None:
    if not isinstance(val_container, dict):
        return None
    if "stringValue" in val_container and isinstance(val_container["stringValue"], str):
        return val_container["stringValue"]
    return None


def _truncate_msg(val: str, max_chars: int = 200) -> str:
    if len(val) <= max_chars:
        return val
    return val[:max_chars]


def lint_document(
    doc: Mapping[str, Any],
    *,
    rules: RuleTable = DEFAULT_RULES,
    max_spans: int = 1_000_000,
) -> list[Finding]:
    """Lint an OTLP JSON document mapping against OpenTelemetry conventions.

    Findings are ordered by document order of spans, then rule code, then attribute key.
    """
    if not isinstance(doc, Mapping):
        raise SpanLintError("document must be a mapping", code="invalid_document")

    if "resourceSpans" not in doc:
        raise SpanLintError("missing resourceSpans key", code="invalid_document")

    resource_spans = doc["resourceSpans"]
    if not isinstance(resource_spans, list):
        raise SpanLintError("resourceSpans must be a list", code="invalid_document")

    findings: list[Finding] = []
    span_count = 0

    for r_span in resource_spans:
        if not isinstance(r_span, dict):
            continue
        scope_spans = r_span.get("scopeSpans")
        if not isinstance(scope_spans, list):
            continue
        for s_span in scope_spans:
            if not isinstance(s_span, dict):
                continue
            spans = s_span.get("spans")
            if not isinstance(spans, list):
                continue
            for span in spans:
                span_count += 1
                if span_count > max_spans:
                    raise SpanLintError(
                        f"document exceeds maximum of {max_spans} spans",
                        code="too_many_spans",
                    )
                if not isinstance(span, dict):
                    continue
                span_findings = _lint_single_span(span, rules)
                findings.extend(span_findings)

    return findings


def _lint_single_span(span: dict[str, Any], rules: RuleTable) -> list[Finding]:
    trace_id = str(span.get("traceId", ""))
    span_id = str(span.get("spanId", ""))
    span_name = str(span.get("name", ""))

    kind_raw = span.get("kind", 0)
    try:
        kind = int(kind_raw)
    except (ValueError, TypeError):
        kind = 0

    raw_attrs = span.get("attributes")
    attrs = _extract_attributes(raw_attrs)

    is_http = any(k.startswith("http.") for k in attrs)

    # Collect candidates: (rule_code, attr_key, Finding)
    candidates: list[tuple[str, str, Finding]] = []

    if is_http:
        # SPAN001: Missing required attributes
        if kind == KIND_SERVER:
            for req in rules.server_required:
                if req not in attrs:
                    candidates.append(
                        (
                            "SPAN001",
                            req,
                            Finding(
                                rule="SPAN001",
                                severity="error",
                                trace_id=trace_id,
                                span_id=span_id,
                                span_name=span_name,
                                message=f"missing required attribute {req}",
                            ),
                        )
                    )
        elif kind == KIND_CLIENT:
            for req in rules.client_required:
                if req not in attrs:
                    candidates.append(
                        (
                            "SPAN001",
                            req,
                            Finding(
                                rule="SPAN001",
                                severity="error",
                                trace_id=trace_id,
                                span_id=span_id,
                                span_name=span_name,
                                message=f"missing required attribute {req}",
                            ),
                        )
                    )

        # SPAN002: Deprecated attribute
        for old_attr, new_attr in rules.deprecated_renames:
            if old_attr in attrs:
                candidates.append(
                    (
                        "SPAN002",
                        old_attr,
                        Finding(
                            rule="SPAN002",
                            severity="warning",
                            trace_id=trace_id,
                            span_id=span_id,
                            span_name=span_name,
                            message=f"deprecated attribute {old_attr}, use {new_attr}",
                        ),
                    )
                )

        # SPAN003: Invalid method
        if "http.request.method" in attrs:
            method_container = attrs["http.request.method"]
            method_val = _get_attribute_raw_string(method_container)
            if method_val is None or method_val not in rules.allowed_methods:
                shown_val = _truncate_msg(str(method_val if method_val is not None else ""))
                candidates.append(
                    (
                        "SPAN003",
                        "http.request.method",
                        Finding(
                            rule="SPAN003",
                            severity="error",
                            trace_id=trace_id,
                            span_id=span_id,
                            span_name=span_name,
                            message=f"invalid http.request.method {shown_val}",
                        ),
                    )
                )

        # SPAN004: http.response.status_code not an intValue in 100-599
        if "http.response.status_code" in attrs:
            status_container = attrs["http.response.status_code"]
            valid_status = False
            if isinstance(status_container, dict) and "intValue" in status_container:
                int_raw = status_container["intValue"]
                try:
                    status_code = int(int_raw)
                    if 100 <= status_code <= 599:
                        valid_status = True
                except (ValueError, TypeError):
                    valid_status = False
            if not valid_status:
                candidates.append(
                    (
                        "SPAN004",
                        "http.response.status_code",
                        Finding(
                            rule="SPAN004",
                            severity="error",
                            trace_id=trace_id,
                            span_id=span_id,
                            span_name=span_name,
                            message="http.response.status_code must be an intValue in 100-599",
                        ),
                    )
                )

        # SPAN005: Server span name
        if kind == KIND_SERVER:
            method_str: str | None = None
            if "http.request.method" in attrs:
                m = _get_attribute_raw_string(attrs["http.request.method"])
                if m is not None:
                    method_str = "HTTP" if m == "_OTHER" else m
            elif "http.method" in attrs:
                m = _get_attribute_raw_string(attrs["http.method"])
                if m is not None:
                    method_str = "HTTP" if m == "_OTHER" else m

            route_str: str | None = None
            if "http.route" in attrs:
                route_str = _get_attribute_raw_string(attrs["http.route"])

            if method_str is not None:
                expected_name = f"{method_str} {route_str}" if route_str is not None else method_str
                if span_name != expected_name:
                    candidates.append(
                        (
                            "SPAN005",
                            "http.route" if "http.route" in attrs else "http.request.method",
                            Finding(
                                rule="SPAN005",
                                severity="warning",
                                trace_id=trace_id,
                                span_id=span_id,
                                span_name=span_name,
                                message=f"span name should be '{expected_name}'",
                            ),
                        )
                    )

    # SPAN006: status error without error.type (applies to all spans)
    status_obj = span.get("status")
    if isinstance(status_obj, dict):
        status_code_raw = status_obj.get("code", 0)
        try:
            code_int = int(status_code_raw)
        except (ValueError, TypeError):
            code_int = 0
        if code_int == STATUS_CODE_ERROR and "error.type" not in attrs:
            candidates.append(
                (
                    "SPAN006",
                    "error.type",
                    Finding(
                        rule="SPAN006",
                        severity="warning",
                        trace_id=trace_id,
                        span_id=span_id,
                        span_name=span_name,
                        message="status error without error.type",
                    ),
                )
            )

    # SPAN007: end before start (applies to all spans)
    start_raw = span.get("startTimeUnixNano")
    end_raw = span.get("endTimeUnixNano")
    if start_raw is not None and end_raw is not None:
        try:
            start_nano = int(start_raw)
            end_nano = int(end_raw)
            if end_nano < start_nano:
                candidates.append(
                    (
                        "SPAN007",
                        "",
                        Finding(
                            rule="SPAN007",
                            severity="error",
                            trace_id=trace_id,
                            span_id=span_id,
                            span_name=span_name,
                            message="endTimeUnixNano smaller than startTimeUnixNano",
                        ),
                    )
                )
        except (ValueError, TypeError):
            pass

    # Sort candidates by rule code, then attribute key
    candidates.sort(key=lambda x: (x[0], x[1]))
    return [item[2] for item in candidates]


def lint_file(
    path: str | Path,
    *,
    rules: RuleTable = DEFAULT_RULES,
    max_bytes: int = 52_428_800,
    max_spans: int = 1_000_000,
) -> list[Finding]:
    """Lint an OTLP JSON file.

    Raises:
        SpanLintError: if the file size exceeds max_bytes, JSON is invalid, or structure is invalid.
    """
    p = Path(path)
    try:
        file_size = os.path.getsize(p)
    except OSError as err:
        raise SpanLintError(f"cannot read file: {err}", code="invalid_document") from err

    if file_size > max_bytes:
        raise SpanLintError(
            f"file size {file_size} exceeds limit of {max_bytes} bytes",
            code="input_too_large",
        )

    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as err:
        raise SpanLintError(f"invalid json in file: {err}", code="invalid_json") from err
    except UnicodeDecodeError as err:
        raise SpanLintError(f"unicode decode error: {err}", code="invalid_json") from err

    return lint_document(data, rules=rules, max_spans=max_spans)
