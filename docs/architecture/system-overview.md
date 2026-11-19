# System Overview

Status: planned v0.1. The product CLI does not exist yet; this document defines
the intended topology and boundaries for `001-check-command`.

## C4 Level 1 — Context

```text
Developer or coding agent
        │  runs `strictr check <paths> [--json]`
        ▼
    Strictr CLI
        │  deterministic diagnostics
        ▼
Developer or coding agent
```

Strictr does not call an LLM. It invokes deterministic tools and returns a
compact, stable result.

## C4 Level 2 — Containers

```text
┌──────────────────────────────────────────────────────┐
│ Strictr CLI                                          │
│  - argument parsing                                  │
│  - exit codes                                        │
│  - human and JSON output                             │
└───────────────────┬──────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────┐
│ Core orchestration                                   │
│  - selects target files                              │
│  - runs tiers in order                               │
│  - merges results and statuses                       │
│  - applies timeouts                                  │
└───────┬───────────────────────┬──────────────────────┘
        │                       │
┌───────▼─────────┐   ┌─────────▼──────────────────────┐
│ Tier 0: AST     │   │ Tier 1: Static and type        │
│ ast.parse       │   │ ruff, mypy or pyright          │
└───────┬─────────┘   └─────────┬──────────────────────┘
        │                       │
        └───────────┬───────────┘
                    │
┌───────────────────▼──────────────────────────────────┐
│ Tier 2: Tests (optional)                             │
│ pytest, timeout, compact failure extraction          │
└───────────────────┬──────────────────────────────────┘
                    │
┌───────────────────▼──────────────────────────────────┐
│ Diagnostics contract                                 │
│ versioned JSON envelope; relative POSIX paths; caps  │
└──────────────────────────────────────────────────────┘
```

## v0.1 scope

- One command: `check`.
- Tiers 0 and 1 are required; tier 2 runs only when tests are present.
- Missing external tools are reported as `skipped`, not as success.
- No daemons, Docker pool, MCP server, auto-fix, or Hypothesis generation.
- Execution is local. It is **not** a security sandbox; tests and target code
  run with the same trust as the user.

## Module boundaries

| Module | Responsibility | May import | Must not import |
|---|---|---|---|
| `strictr.cli` | Parse arguments, render output, set exit code | `strictr.core`, `strictr.diagnostics` | External tools directly |
| `strictr.core` | Orchestrate tiers, merge results, timeouts | `strictr.engines`, `strictr.diagnostics` | `strictr.cli` |
| `strictr.engines.python` | Tier 0–2 adapters for Python | `strictr.core` contracts, stdlib | `strictr.cli` |
| `strictr.diagnostics` | Normalize and serialize diagnostics | stdlib | `strictr.cli`, engines |
| `strictr.traceability` | Repository policy checker | stdlib | Product runtime code |

These modules are planned for `001`. The traceability module exists now as
repository tooling and does not participate in product verification.

## Main sequence: `strictr check`

1. Resolve target paths; reject paths outside the target root.
2. Parse each Python file with `ast.parse`. Record syntax diagnostics.
3. If parsing fails, skip later tiers for that file and return `fail`.
4. Run `ruff check --output-format=json` if available.
5. Run `mypy` or `pyright` with machine-readable output if available.
6. If tests exist and tier 2 is enabled, run `pytest` with a timeout.
7. Normalize diagnostics, cap field sizes, assign per-tier statuses.
8. Emit JSON or a human summary; exit `0` pass, `1` fail, `2` tool/config error.

## Trust boundaries

| Boundary | Risk | v0.1 decision |
|---|---|---|
| Target project code | Arbitrary code execution during import or tests | Local-only; document this; timeout; do not claim isolation |
| External tool output | Malformed or huge JSON | Validate, cap, and fail closed |
| Paths | Traversal or absolute-path leakage | Resolve against target root; emit relative paths |
| Diagnostics | Secrets in tracebacks or locals | Redact known secret patterns; cap content |
| CI | Untrusted fork PRs | Read-only token; no `pull_request_target` with untrusted code |

## External dependencies

- Python 3.12+
- `ruff` (optional at runtime; reported as skipped when absent)
- `mypy` or `pyright` (optional at runtime)
- `pytest` (optional at runtime; runs only when tests exist)

The Strictr package itself has no runtime third-party dependencies in v0.1.
