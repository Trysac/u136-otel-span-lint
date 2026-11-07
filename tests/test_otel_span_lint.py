"""Behavior tests for the public API of otel_span_lint."""

from __future__ import annotations

import pytest

import otel_span_lint


def test_normalize_trims_and_lowercases() -> None:
    assert otel_span_lint.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        otel_span_lint.normalize(value)


def test_version_is_semver() -> None:
    parts = otel_span_lint.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
