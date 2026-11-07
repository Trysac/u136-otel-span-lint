"""Tests for otel_span_lint exercising all rules, CLI, edge cases, and error paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from otel_span_lint import (
    Finding,
    SpanLintError,
    lint_document,
    lint_file,
)
from otel_span_lint.__main__ import main


def _make_doc(spans: list[dict[str, object]]) -> dict[str, object]:
    return {
        "resourceSpans": [
            {
                "scopeSpans": [
                    {
                        "spans": spans,
                    }
                ]
            }
        ]
    }


def test_acceptance_1_server_missing_required_attrs() -> None:
    """A SERVER span (kind 2) with 'http.request.method' but no 'url.path' or 'url.scheme' yields
    two Findings with rule 'SPAN001', severity 'error' and messages 'missing required attribute url.path'
    and 'missing required attribute url.scheme'."""
    span = {
        "traceId": "0123456789abcdef0123456789abcdef",
        "spanId": "0123456789abcdef",
        "name": "GET",
        "kind": 2,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "GET"}},
        ],
    }
    findings = lint_document(_make_doc([span]))
    assert len(findings) == 2
    assert findings[0] == Finding(
        rule="SPAN001",
        severity="error",
        trace_id="0123456789abcdef0123456789abcdef",
        span_id="0123456789abcdef",
        span_name="GET",
        message="missing required attribute url.path",
    )
    assert findings[1] == Finding(
        rule="SPAN001",
        severity="error",
        trace_id="0123456789abcdef0123456789abcdef",
        span_id="0123456789abcdef",
        span_name="GET",
        message="missing required attribute url.scheme",
    )


def test_acceptance_2_deprecated_attribute() -> None:
    """An attribute 'http.method' yields rule 'SPAN002' severity 'warning' with message
    'deprecated attribute http.method, use http.request.method'."""
    span = {
        "traceId": "trace1",
        "spanId": "span1",
        "name": "GET",
        "kind": 1,
        "attributes": [
            {"key": "http.method", "value": {"stringValue": "GET"}},
        ],
    }
    findings = lint_document(_make_doc([span]))
    assert len(findings) == 1
    assert findings[0] == Finding(
        rule="SPAN002",
        severity="warning",
        trace_id="trace1",
        span_id="span1",
        span_name="GET",
        message="deprecated attribute http.method, use http.request.method",
    )


def test_acceptance_3_invalid_method() -> None:
    """'http.request.method' = 'FETCH' yields 'SPAN003' with message 'invalid http.request.method FETCH',
    while 'GET' and '_OTHER' pass."""
    span_fetch = {
        "traceId": "trace1",
        "spanId": "span1",
        "name": "test",
        "kind": 1,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "FETCH"}},
        ],
    }
    findings_fetch = lint_document(_make_doc([span_fetch]))
    assert len(findings_fetch) == 1
    assert findings_fetch[0] == Finding(
        rule="SPAN003",
        severity="error",
        trace_id="trace1",
        span_id="span1",
        span_name="test",
        message="invalid http.request.method FETCH",
    )

    # Adversarial neighbors around method token
    for bad_method in ["fetch", "GET1", "GET ", "_other", "POST-EXTRA"]:
        span_bad = {
            "traceId": "t",
            "spanId": "s",
            "name": "t",
            "kind": 1,
            "attributes": [{"key": "http.request.method", "value": {"stringValue": bad_method}}],
        }
        f = lint_document(_make_doc([span_bad]))
        assert any(x.rule == "SPAN003" for x in f)

    span_get = {
        "traceId": "trace2",
        "spanId": "span2",
        "name": "GET",
        "kind": 1,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "GET"}},
        ],
    }
    assert lint_document(_make_doc([span_get])) == []

    span_other = {
        "traceId": "trace3",
        "spanId": "span3",
        "name": "HTTP",
        "kind": 1,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "_OTHER"}},
        ],
    }
    assert lint_document(_make_doc([span_other])) == []


def test_acceptance_4_status_code() -> None:
    """'http.response.status_code' given as intValue '200' passes, as stringValue '200' or intValue '99' yields 'SPAN004'."""
    span_valid = {
        "traceId": "t1",
        "spanId": "s1",
        "name": "ok",
        "kind": 1,
        "attributes": [
            {"key": "http.response.status_code", "value": {"intValue": "200"}},
        ],
    }
    assert lint_document(_make_doc([span_valid])) == []

    span_string = {
        "traceId": "t2",
        "spanId": "s2",
        "name": "bad_str",
        "kind": 1,
        "attributes": [
            {"key": "http.response.status_code", "value": {"stringValue": "200"}},
        ],
    }
    findings_str = lint_document(_make_doc([span_string]))
    assert len(findings_str) == 1
    assert findings_str[0].rule == "SPAN004"
    assert findings_str[0].severity == "error"

    span_99 = {
        "traceId": "t3",
        "spanId": "s3",
        "name": "bad_99",
        "kind": 1,
        "attributes": [
            {"key": "http.response.status_code", "value": {"intValue": "99"}},
        ],
    }
    findings_99 = lint_document(_make_doc([span_99]))
    assert len(findings_99) == 1
    assert findings_99[0].rule == "SPAN004"

    span_600 = {
        "traceId": "t4",
        "spanId": "s4",
        "name": "bad_600",
        "kind": 1,
        "attributes": [
            {"key": "http.response.status_code", "value": {"intValue": "600"}},
        ],
    }
    findings_600 = lint_document(_make_doc([span_600]))
    assert len(findings_600) == 1
    assert findings_600[0].rule == "SPAN004"


def test_acceptance_5_server_span_name() -> None:
    """A SERVER span named 'GET /users/123' with 'http.route' = '/users/{id}' yields 'SPAN005' with
    message \"span name should be 'GET /users/{id}'\", while names 'GET /users/{id}' and, without http.route, 'GET' pass."""
    span_wrong = {
        "traceId": "t1",
        "spanId": "s1",
        "name": "GET /users/123",
        "kind": 2,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "GET"}},
            {"key": "url.path", "value": {"stringValue": "/users/123"}},
            {"key": "url.scheme", "value": {"stringValue": "http"}},
            {"key": "http.route", "value": {"stringValue": "/users/{id}"}},
        ],
    }
    findings = lint_document(_make_doc([span_wrong]))
    assert len(findings) == 1
    assert findings[0] == Finding(
        rule="SPAN005",
        severity="warning",
        trace_id="t1",
        span_id="s1",
        span_name="GET /users/123",
        message="span name should be 'GET /users/{id}'",
    )

    span_correct_route = {
        "traceId": "t2",
        "spanId": "s2",
        "name": "GET /users/{id}",
        "kind": 2,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "GET"}},
            {"key": "url.path", "value": {"stringValue": "/users/123"}},
            {"key": "url.scheme", "value": {"stringValue": "http"}},
            {"key": "http.route", "value": {"stringValue": "/users/{id}"}},
        ],
    }
    assert lint_document(_make_doc([span_correct_route])) == []

    span_no_route = {
        "traceId": "t3",
        "spanId": "s3",
        "name": "GET",
        "kind": 2,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "GET"}},
            {"key": "url.path", "value": {"stringValue": "/users/123"}},
            {"key": "url.scheme", "value": {"stringValue": "http"}},
        ],
    }
    assert lint_document(_make_doc([span_no_route])) == []

    # Test _OTHER method in server span name format
    span_other_route = {
        "traceId": "t4",
        "spanId": "s4",
        "name": "HTTP /custom",
        "kind": 2,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "_OTHER"}},
            {"key": "url.path", "value": {"stringValue": "/custom"}},
            {"key": "url.scheme", "value": {"stringValue": "http"}},
            {"key": "http.route", "value": {"stringValue": "/custom"}},
        ],
    }
    assert lint_document(_make_doc([span_other_route])) == []


def test_acceptance_6_status_error_and_timestamp() -> None:
    """A span with status code 2 and no 'error.type' yields 'SPAN006' severity 'warning';
    endTimeUnixNano smaller than startTimeUnixNano yields 'SPAN007' severity 'error'."""
    span_status = {
        "traceId": "t1",
        "spanId": "s1",
        "name": "internal-op",
        "kind": 1,
        "status": {"code": 2},
    }
    f1 = lint_document(_make_doc([span_status]))
    assert len(f1) == 1
    assert f1[0] == Finding(
        rule="SPAN006",
        severity="warning",
        trace_id="t1",
        span_id="s1",
        span_name="internal-op",
        message="status error without error.type",
    )

    # With error.type present
    span_status_ok = {
        "traceId": "t1",
        "spanId": "s1",
        "name": "internal-op",
        "kind": 1,
        "status": {"code": 2},
        "attributes": [{"key": "error.type", "value": {"stringValue": "TimeoutError"}}],
    }
    assert lint_document(_make_doc([span_status_ok])) == []

    span_time = {
        "traceId": "t2",
        "spanId": "s2",
        "name": "inverted-time",
        "kind": 1,
        "startTimeUnixNano": "2000000",
        "endTimeUnixNano": "1000000",
    }
    f2 = lint_document(_make_doc([span_time]))
    assert len(f2) == 1
    assert f2[0] == Finding(
        rule="SPAN007",
        severity="error",
        trace_id="t2",
        span_id="s2",
        span_name="inverted-time",
        message="endTimeUnixNano smaller than startTimeUnixNano",
    )


def test_acceptance_7_limits_and_errors(tmp_path: Path) -> None:
    """lint_file on a file of 52_428_801 bytes raises SpanLintError with code 'input_too_large';
    a document with 1_000_001 spans raises code 'too_many_spans'; a document without 'resourceSpans' raises code 'invalid_document'."""
    large_file = tmp_path / "large.json"
    with large_file.open("wb") as f:
        f.seek(52_428_800)
        f.write(b"x")
    assert large_file.stat().st_size == 52_428_801

    with pytest.raises(SpanLintError) as exc_info:
        lint_file(large_file)
    assert exc_info.value.code == "input_too_large"

    # too_many_spans check
    dummy_spans = [{"traceId": f"t{i}", "spanId": f"s{i}", "name": "span"} for i in range(5)]
    doc = _make_doc(dummy_spans)
    with pytest.raises(SpanLintError) as exc_info:
        lint_document(doc, max_spans=4)
    assert exc_info.value.code == "too_many_spans"

    # missing resourceSpans
    with pytest.raises(SpanLintError) as exc_info:
        lint_document({"other": 123})
    assert exc_info.value.code == "invalid_document"

    with pytest.raises(SpanLintError) as exc_info:
        lint_document([1, 2, 3])  # type: ignore
    assert exc_info.value.code == "invalid_document"

    with pytest.raises(SpanLintError) as exc_info:
        lint_document({"resourceSpans": "not a list"})
    assert exc_info.value.code == "invalid_document"


def test_acceptance_8_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """main(['spans.json']) prints 'trace=<traceId> span=<spanId> SPAN001 error missing required attribute url.path'
    lines and returns 1 when any error exists, 0 with only warnings, 1 with warnings and '--strict',
    and 2 for unreadable input; '--format', 'json' prints a JSON array of findings."""
    span_err = {
        "traceId": "traceA",
        "spanId": "spanA",
        "name": "GET",
        "kind": 2,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "GET"}},
            {"key": "url.scheme", "value": {"stringValue": "https"}},
        ],
    }
    err_file = tmp_path / "err_spans.json"
    err_file.write_text(json.dumps(_make_doc([span_err])), encoding="utf-8")

    exit_code = main([str(err_file)])
    captured = capsys.readouterr()
    assert exit_code == 1
    expected_line = "trace=traceA span=spanA SPAN001 error missing required attribute url.path\n"
    assert expected_line in captured.out

    # JSON output format
    exit_code_json = main([str(err_file), "--format", "json"])
    captured_json = capsys.readouterr()
    assert exit_code_json == 1
    parsed = json.loads(captured_json.out)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["rule"] == "SPAN001"

    # Warning only
    span_warn = {
        "traceId": "traceW",
        "spanId": "spanW",
        "name": "warn",
        "kind": 1,
        "attributes": [
            {"key": "http.method", "value": {"stringValue": "GET"}},
        ],
    }
    warn_file = tmp_path / "warn_spans.json"
    warn_file.write_text(json.dumps(_make_doc([span_warn])), encoding="utf-8")

    exit_code_warn = main([str(warn_file)])
    assert exit_code_warn == 0
    captured_warn = capsys.readouterr()
    assert "SPAN002 warning" in captured_warn.out

    # Warning with --strict
    exit_code_strict = main([str(warn_file), "--strict"])
    assert exit_code_strict == 1

    # Unreadable / missing input
    exit_code_missing = main([str(tmp_path / "nonexistent.json")])
    assert exit_code_missing == 2
    captured_err = capsys.readouterr()
    assert "Error:" in captured_err.err


def test_client_missing_required_attributes() -> None:
    """Verify client spans (kind 3) require http.request.method, server.address, server.port, url.full."""
    span = {
        "traceId": "t_client",
        "spanId": "s_client",
        "name": "GET",
        "kind": 3,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "GET"}},
        ],
    }
    findings = lint_document(_make_doc([span]))
    rules = [f.rule for f in findings]
    messages = [f.message for f in findings]
    assert rules == ["SPAN001", "SPAN001", "SPAN001"]
    assert messages == [
        "missing required attribute server.address",
        "missing required attribute server.port",
        "missing required attribute url.full",
    ]


def test_all_deprecated_renames() -> None:
    """Verify all 5 bundled deprecated renames."""
    span = {
        "traceId": "t",
        "spanId": "s",
        "name": "test",
        "kind": 1,
        "attributes": [
            {"key": "http.method", "value": {"stringValue": "GET"}},
            {"key": "http.status_code", "value": {"intValue": "200"}},
            {"key": "http.url", "value": {"stringValue": "https://example.com"}},
            {"key": "http.scheme", "value": {"stringValue": "https"}},
            {"key": "http.user_agent", "value": {"stringValue": "Mozilla/5.0"}},
        ],
    }
    findings = lint_document(_make_doc([span]))
    messages = [f.message for f in findings]
    assert "deprecated attribute http.method, use http.request.method" in messages
    assert "deprecated attribute http.status_code, use http.response.status_code" in messages
    assert "deprecated attribute http.url, use url.full" in messages
    assert "deprecated attribute http.scheme, use url.scheme" in messages
    assert "deprecated attribute http.user_agent, use user_agent.original" in messages


def test_duplicate_attributes_last_wins() -> None:
    """Duplicate attribute keys: the last wins."""
    span = {
        "traceId": "t",
        "spanId": "s",
        "name": "test",
        "kind": 1,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "FETCH"}},  # invalid
            {"key": "http.request.method", "value": {"stringValue": "GET"}},  # valid
        ],
    }
    findings = lint_document(_make_doc([span]))
    # The last key was GET, so no SPAN003 error should be produced
    assert not any(f.rule == "SPAN003" for f in findings)


def test_non_http_spans() -> None:
    """Non-HTTP spans should only be subject to SPAN006 and SPAN007."""
    span = {
        "traceId": "t",
        "spanId": "s",
        "name": "db.query",
        "kind": 3,  # client, but not HTTP
        "attributes": [
            {"key": "db.system", "value": {"stringValue": "postgresql"}},
        ],
    }
    findings = lint_document(_make_doc([span]))
    assert findings == []


def test_invalid_json_file(tmp_path: Path) -> None:
    """Malformed json file raises invalid_json."""
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(SpanLintError) as exc_info:
        lint_file(bad_json)
    assert exc_info.value.code == "invalid_json"


def test_unicode_span_names() -> None:
    """Unicode names in spans are preserved accurately."""
    span = {
        "traceId": "t_uni",
        "spanId": "s_uni",
        "name": "GET /ユーザー",
        "kind": 2,
        "attributes": [
            {"key": "http.request.method", "value": {"stringValue": "GET"}},
            {"key": "url.path", "value": {"stringValue": "/ユーザー"}},
            {"key": "url.scheme", "value": {"stringValue": "https"}},
            {"key": "http.route", "value": {"stringValue": "/ユーザー"}},
        ],
    }
    findings = lint_document(_make_doc([span]))
    assert findings == []


def test_error_message_length_capping() -> None:
    """Errors truncate messages over 200 characters."""
    long_msg = "x" * 300
    err = SpanLintError(long_msg, code="invalid_document")
    assert len(str(err)) <= 200
    assert str(err).endswith("...")


def test_empty_resource_spans() -> None:
    """Empty resourceSpans or corrupt nested elements handled gracefully."""
    doc: dict[str, object] = {
        "resourceSpans": [
            "corrupt",
            {"scopeSpans": "corrupt"},
            {"scopeSpans": ["corrupt", {"spans": "corrupt"}]},
            {"scopeSpans": [{"spans": ["corrupt"]}]},
        ]
    }
    findings = lint_document(doc)
    assert findings == []
