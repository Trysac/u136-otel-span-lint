# Security

## Threat Model

### Defended

1. **Denial of Service (DoS)**: Protected against resource exhaustion via file size limits (50MiB default) and span count limits (1,000,000 default).
2. **Information Disclosure**: Error messages are truncated to 200 characters to prevent dumping sensitive attributes or trace bodies.
3. **Memory Safety**: No arbitrary code execution; utilizes stdlib `json` for parsing.

### Not Defended

1. **Adversarial inputs**: The linter relies on standard JSON parsing and structure validation; it is not hardened against malicious OTLP payloads designed to induce pathological parser behavior beyond standard DoS protections.