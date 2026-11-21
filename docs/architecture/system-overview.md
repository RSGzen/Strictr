# System Overview

Status: architecture in progress (spec `002`)
Owner: Ge Rui Sen
Last updated: 2026-11-21
Related: [verification contract](verification-contract.md),
[product vision](../product/vision.md), [evaluation plan](../product/evaluation.md)

## Scope

This document defines the v0.1 architecture for Strictr: a local, deterministic
verification gateway for agent-generated Python patches.

In scope:

- Python only.
- Tier 0 parse, Tier 1 ruff, Tier 1 type checking, Tier 2 pytest.
- Local execution with an explicit not-a-sandbox warning.
- Human output and a versioned JSON envelope.

Implementation spec: `003-check-command`, after this architecture is approved.

Out of scope for v0.1:

- Patch application and rollback sessions.
- Warm daemons, persistent workers, or Strictr-owned caches.
- Test selection or test-impact analysis.
- Hypothesis/property fuzzing.
- Docker, microVM, or other sandbox isolation.
- MCP server and agent hooks.
- SARIF output.
- Additional languages.

The product decisions are binding in
[vision.md](../product/vision.md). The output contract is binding in
[verification-contract.md](verification-contract.md).

## C4 Level 1 — Context

```text
Agent harness / developer
        │  strictr check <paths> [--json]
        ▼
    Strictr CLI
        │  deterministic evidence envelope
        ▼
Agent harness / developer
```

Strictr does not call an LLM. It invokes existing tools with the project's
configuration and returns one verification transaction.

## C4 Level 2 — Components

```text
┌─────────────────────────────────────────────────────────────┐
│ Primary adapters                                            │
│  CLI (argparse)              SDK/MCP (later)                │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│ Application                                                 │
│  CheckService / Pipeline                                    │
│   - tier order, fail-fast, scope ledger, exit status        │
│  Discovery                                                  │
│   - root, targets, git-aware file list                      │
└───────────┬───────────────────────────────┬─────────────────┘
            │                               │
┌───────────▼──────────────────┐   ┌────────▼────────────────┐
│ Tiers                        │   │ Output                  │
│  tier0_ast                   │   │  human                  │
│  tier1_ruff                  │   │  JSON                   │
│  tier1_types                 │   │  SARIF (later)          │
│  tier2_pytest                │   └─────────────────────────┘
└───────────┬──────────────────┘
            │
┌───────────▼─────────────────────────────────────────────────┐
│ Infrastructure                                               │
│  ToolRunner: subprocess, timeout, process tree, UTF-8        │
│  Parsers: ruff JSON, mypy JSON, pyright JSON, pytest JUnit   │
│  Version capture, temp files, environment                    │
└─────────────────────────────────────────────────────────────┘
```

## Module boundaries

```text
src/strictr/
├── __init__.py
├── __main__.py
├── cli.py                 # argparse and output switch
├── app.py                 # explicit wiring
├── core/
│   ├── models.py          # Status, Diagnostic, TierResult, CheckResult
│   ├── pipeline.py        # fail-fast execution and result assembly
│   ├── discovery.py       # project root, targets, file discovery
│   ├── protocols.py       # Tier, ToolRunner
│   └── errors.py
├── tiers/
│   ├── ast_tier.py
│   ├── ruff_tier.py
│   ├── types_tier.py
│   └── pytest_tier.py
├── tools/
│   ├── runner.py
│   └── parsers/
│       ├── ruff.py
│       ├── mypy.py
│       ├── pyright.py
│       └── pytest_junit.py
├── output/
│   ├── human.py
│   └── json_output.py
└── traceability.py        # repository tooling, not product verification
```

| Layer | Responsibility | May import | Must not import |
|---|---|---|---|
| `core` | Models, pipeline, discovery, protocols | stdlib | `tiers`, `tools`, `output`, `cli` |
| `tiers` | One verification stage per tier | `core`, `tools` | `cli`, `output` |
| `tools` | Subprocess runner and pure parsers | stdlib, `core.errors` | `tiers`, `cli`, `output` |
| `output` | Render a completed result | `core` | `tiers`, `tools`, `cli` |
| `cli` / `app` | Parse input, wire adapters, set exit code | all of the above | — |
| `traceability` | Repository policy checks | stdlib | product runtime code |

Rules:

- No generic `engines/base.py` abstraction. Python is the only language.
- No plugin registry. Add one only when a second language or third-party adapter
  exists.
- Parsers are pure functions: bytes/JSON/XML in, diagnostics out.
- Explicit construction in `app.py`; no dependency-injection framework.

## Data flow

1. Parse CLI arguments.
2. Resolve the project root from `pyproject.toml`, `.git`, or the target path.
   Reject targets outside the root.
3. Discover `.py` and `.pyi` files. Inside a git repository, use
   `git ls-files -co --exclude-standard`; otherwise use a safe recursive walk
   that skips virtual environments, caches, and build directories.
4. Tier 0: parse each file with `ast.parse`. On syntax failure, stop.
5. Tier 1a: run `ruff check --output-format=json`. On findings, stop.
6. Tier 1b: select and run one type checker with JSON output. On errors, stop.
7. Tier 2: run the full `pytest` suite with `--junitxml` in a temporary path.
   Parse failures into compact diagnostics.
8. Assemble the envelope: status, scope, tier results, diagnostics, timings,
   environment, trust warning, and warnings.
9. Render human output or JSON and map the result to an exit code.

Fail-fast is the v0.1 default. The pipeline is a list of tiers so a future
`--all` mode can run later tiers while preserving the same result contract.

## Tier model

| Tier | Name | Tool | Required by default | Failure behavior |
|---|---|---|---|---|
| 0 | Syntax | stdlib `ast` | Yes | `fail`; later tiers skipped |
| 1a | Lint | `ruff` | Yes | `fail`; later tiers skipped |
| 1b | Types | `mypy` or `pyright` | If configured or available | `fail`; missing configured tool is `error`; no checker is `partial` |
| 2 | Tests | `pytest` | If tests exist | `fail`; missing pytest with tests is `error`; no tests is `skipped` |

Tier 1b selection is defined in [ADR 0005](../adr/0005-type-checker-selection.md).
Test integration is defined in [ADR 0006](../adr/0006-pytest-integration.md).

## Status and exit model

The full contract is in
[verification-contract.md](verification-contract.md).

| Overall status | Meaning | Exit |
|---|---|---|
| `pass` | All requested required tiers ran and passed; optional skips are explicit | 0 |
| `fail` | At least one executed tier found errors | 1 |
| `partial` | A required check could not run, e.g. no type checker | 2 |
| `error` | Missing required tool, crash, timeout, invalid output, or config error | 2 |

A tier status is `pass`, `fail`, `skipped`, or `error`. A skipped required tier
makes the overall result `partial`; a skipped optional tier does not. No result
can be `pass` if a requested check was silently omitted.

## Tool execution

Full decision: [ADR 0003](../adr/0003-subprocess-tool-execution.md).

- Run tools as subprocesses, never as imported libraries.
- Run from the project root with the project's configuration.
- Use the project environment: `sys.executable -m mypy`, `sys.executable -m
  pytest`, and `ruff`/`pyright` resolved from the environment.
- Do not invoke a shell.
- Capture stdout/stderr, enforce timeouts, and terminate the process tree.
- Decode as UTF-8 with replacement on decoding errors.
- Record tool versions in the envelope.
- Missing required tools produce `error` with an actionable message.

This preserves parity with the tools the project already uses and avoids
version coupling in Strictr's own environment.

## Type-checker selection

Full decision: [ADR 0005](../adr/0005-type-checker-selection.md).

Precedence:

1. Explicit `--type-checker mypy|pyright|none`.
2. Mypy configuration present.
3. Pyright configuration present.
4. Mypy executable available.
5. Pyright executable available.
6. Otherwise `partial` with reason `no type checker found`.

If both mypy and pyright are configured, use mypy and emit a warning; the user
can override with `--type-checker pyright`. A configured checker that is not
installed is an `error`, not a skip. `--type-checker none` is an explicit
reduction of scope and is recorded in the envelope.

## Pytest integration

Full decision: [ADR 0006](../adr/0006-pytest-integration.md).

- Run the full test suite by default. No test selection in v0.1.
- Use `pytest --junitxml=<temp>` and parse the XML with the standard library.
- Map `testcase` `file`/`line`, failure/error text, and test IDs into compact
  diagnostics.
- `pytest` exit code 5 (no tests collected) is `skipped`, not `fail`.
- `pytest` exit codes 2/3/4 are `error`.
- Missing pytest when tests exist is `error`.
- Locals and assertion rewriting details are deferred to a later custom plugin.

## Trust boundary

Full decision: [ADR 0007](../adr/0007-trust-boundary-and-timeouts.md).

v0.1 runs locally and is **not a sandbox**. Running pytest or importing target
code can execute arbitrary code with the user's privileges. The envelope always
includes:

```json
"trust": {
  "sandboxed": false,
  "warning": "Local execution; not a security boundary."
}
```

The human output prints the warning once. The JSON output contains no
unstructured warning on stdout. No network isolation is claimed. Paths are
confined to the project root, no shell is used, and diagnostics are capped and
redacted. Real isolation is a later spec.

## Performance model

v0.1 is a cold-path architecture:

- Each tool starts a process. Startup and tool execution dominate.
- Fail-fast avoids running later tiers after an early failure.
- Tier 0 and ruff are cheap; the type checker and pytest are the expensive
  stages.
- Strictr adds no cache, daemon, or persistent worker.
- Mypy's own incremental cache may be used by the tool; Strictr does not own it.
- The p95 targets in the evaluation plan are hypotheses, not guarantees.

Later, measured optimizations may add concurrent Tier 1 tools, warm
`dmypy`/pyright, content-addressed caching, or a warm pytest worker. None are
part of this architecture.

## Failure modes

| Failure | Tier result | Overall | Exit |
|---|---|---|---|
| Syntax error | `fail` | `fail` | 1 |
| Ruff findings | `fail` | `fail` | 1 |
| Type errors | `fail` | `fail` | 1 |
| Test failures | `fail` | `fail` | 1 |
| No tests collected | `skipped` | `pass` if other tiers pass | 0 |
| Type checker absent | `skipped` | `partial` | 2 |
| Configured type checker missing | `error` | `error` | 2 |
| Ruff missing | `error` | `error` | 2 |
| Pytest missing with tests | `error` | `error` | 2 |
| Tool timeout | `error` | `error` | 2 |
| Invalid JSON/XML | `error` | `error` | 2 |
| Target outside root | `error` | `error` | 2 |

## Security and redaction

- No shell invocation; arguments are lists.
- Targets are confined to the project root.
- Temporary JUnit files are created outside the repository and cleaned up.
- Diagnostics are capped by count and message length.
- Known secret patterns are redacted from messages and evidence.
- The local-only warning is not optional.
- No telemetry in v0.1.

## Testing

See [docs/testing.md](../testing.md). The architecture is tested through:

- Pure parser tests with canned ruff/mypy/pyright JSON and pytest JUnit XML.
- Tier tests with a fake `ToolRunner`.
- Acceptance tests against fixture projects using real tools.
- Contract tests for the JSON envelope and exit codes.
- Failure-mode tests for missing tools, crashes, timeouts, and invalid output.
- Windows and Linux CI.

## Extension seams

The architecture keeps these seams without implementing them now:

- **Primary adapters:** SDK, MCP, pre-commit hook, CI annotation.
- **Output adapters:** SARIF, GitHub annotations.
- **Performance:** warm sessions, cache, concurrency.
- **Selection:** opt-in test selection with full-suite safety mode.
- **Isolation:** Docker or microVM.
- **Additional languages:** new tiers behind the same result contract.

## Out of scope

- LLM judging or any LLM call in the verification path.
- Auto-fix.
- Generated tests as proof.
- Formal verification.
- Multi-language support.
- Test selection.
- Hypothesis fuzzing.
- Warm daemons or Strictr-owned caching.
- Sandbox isolation.
- MCP server.
- CI replacement.
- Coverage gating.
- Telemetry.

## ADR index

- [ADR 0002 — Verification pipeline and module boundaries](../adr/0002-verification-pipeline.md)
- [ADR 0003 — Subprocess tool execution and project environment](../adr/0003-subprocess-tool-execution.md)
- [ADR 0004 — Verification contract, statuses, and exit codes](../adr/0004-verification-contract-and-statuses.md)
- [ADR 0005 — Type-checker selection and configuration](../adr/0005-type-checker-selection.md)
- [ADR 0006 — Pytest integration and full-suite policy](../adr/0006-pytest-integration.md)
- [ADR 0007 — Local trust boundary, timeouts, and process termination](../adr/0007-trust-boundary-and-timeouts.md)
