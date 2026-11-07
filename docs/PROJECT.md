# Project record

## Objective

Lint OTLP JSON files against HTTP semantic conventions v1.26.0 (required attributes, deprecations, and malformations).

## Scope

- Public API, library-style usage, CLI execution, type safety, and documentation.

## Out-of-Scope

- Database, messaging, or GenAI conventions.
- Protobuf-native OTLP.
- Live collector integration.
- Schema-URL transformations.

## Effort metrics

| Metric | Value |
|---|---|
| Tokens (input / output) | 404869 / 15660 |
| Hours (human) | pending measurement |
| Cost (USD) | 0.1008 |

## Factory run u136 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | gemini-3.8-flash | yes | 4403 | 12917 | 0 | 0 | 0.0259 |
| fix-1 | gemini-3.8-flash | no | 14786 | 166 | 0 | 10511 | 0.0125 |
| audit | gemini-3.1-flash-lite | no | 54190 | 680 | 0 | 156721 | 0.0185 |
| docs | gemini-3.1-flash-lite | no | 164258 | 1897 | 0 | 0 | 0.0439 |

Total: $0.1008. Prices: Anthropic list prices.
