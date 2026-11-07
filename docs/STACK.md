# Stack

## Used

| Tool | Why |
|---|---|
| Python >= 3.10 | Supports required modern type hinting features. |
| uv | Manages environments and builds across platforms efficiently. |
| hatchling | Minimalist, standards-compliant build backend. |
| ruff | Combines linting and formatting for performance. |
| mypy (strict) | Validates type safety for public API stability. |
| pytest + pytest-cov | Ensures 80%+ branch coverage. |

## Discarded

| Tool | Why not |
|---|---|
| Poetry | Slower build/resolve times compared to uv. |
| black + isort + flake8 | Redundant; superseded by ruff's unified toolset. |
| tox / nox | CI matrix handles portability; local checks are sufficient. |