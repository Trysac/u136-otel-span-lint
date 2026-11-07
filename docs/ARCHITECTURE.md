# Architecture

## Pipeline

1. **Validation**: `lint_file` checks file size against `max_bytes` (50MB default). `lint_document` checks span counts against `max_spans` (1,000,000 default).
2. **Attribute Extraction**: Transforms OTLP list-based attribute structures into a dict. If keys duplicate, the last one wins.
3. **Identification**: Spans are identified as HTTP when any attribute key starts with `http.`.
4. **Rule Evaluation**: Applies seven specific rules:
    - SPAN001: Missing required attributes (error).
    - SPAN002: Deprecated attribute usage (warning).
    - SPAN003: Invalid HTTP method (error).
    - SPAN004: Invalid `http.response.status_code` (error).
    - SPAN005: Incorrect server span name format (warning).
    - SPAN006: Missing `error.type` on status error (warning).
    - SPAN007: End time before start time (error).
5. **Output**: Findings are returned as a list, ordered by document order, then rule code, then attribute key.