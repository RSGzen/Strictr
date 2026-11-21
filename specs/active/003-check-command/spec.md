---
id: "003"
title: "Check command"
status: in-progress
owner: "Ge Rui Sen"
created: 2026-11-21
updated: 2026-11-21
branch: "feat/003-check-command"
---

# Check command

## Context

Spec `002` approved the architecture and the verification contract. The current
product slice is the first runnable surface: `strictr check <paths> [--json]`.
There is no product CLI, tier, parser, or output renderer yet.

This spec is code development, not a documentation-only spec. It adds the first
runtime behavior to `src/strictr/` and the first black-box CLI tests in
`tests/acceptance/`. The architecture and contract remain the binding design; if
implementation exposes a genuine contract gap, the work stops and an ADR plus a
contract revision is proposed instead of silently diverging.

The planning decisions approved by the owner on 2026-11-21 are part of this
spec: full v0.1 scope, no verification-contract change, a test-only JSON Schema
dependency, an approved `AGENTS.md` update, version `0.0.0`, and an in-process
Tier 0 budget with real subprocess timeouts for later tiers. ADR 0008 records
the tools-to-core import boundary; ADR 0009 records the v0.1 execution
refinements.

## Goals

- Deliver a working `strictr check` command that runs Tier 0, ruff, one type
  checker, and the full pytest suite in deterministic order.
- Return one fail-closed evidence envelope that states what ran, what failed,
  what was skipped, and what was not inspected.
- Preserve parity with the project's existing tool configuration by invoking
  the existing tools as subprocesses in the project environment.
- Cover the public contract with schema, golden-fixture, unit, acceptance, and
  failure-mode tests.
- Keep runtime dependencies at zero.

## Non-goals

- MCP server, SDK, agent hooks, pre-commit hook, or SARIF output.
- Warm daemons, persistent workers, Strictr-owned caching, or concurrency.
- Test selection, test-impact analysis, or coverage gating.
- Docker, microVM, or any sandbox isolation claim.
- Auto-fix, code rewriting, or generated tests.
- A new Strictr configuration file.
- Multi-language support or a plugin registry.
- `--all` mode that continues after a failing tier.
- Color output, telemetry, or performance claims.
- Changing the verification contract, module boundaries, or the public JSON
  shape within spec `003`. A required change needs an ADR and a spec revision.

## Scenarios

1. An agent runs `strictr check src tests --json` in a clean project. All four
   tiers run, the suite passes, and stdout is one JSON object with
   `status: "pass"` and a complete scope ledger.
2. A patch introduces a ruff finding. Tier 1a fails, Tiers 1b and 2 are recorded
   as skipped with `earlier_tier_failed`, and exit code is 1.
3. A project has no type checker. Tier 1b is skipped with
   `no type checker found`, the overall status is `partial`, and exit code is 2.
4. A project has source code but no tests. pytest exits 5, Tier 2 is skipped
   with `no tests collected`, and the overall status can still be `pass`.
5. ruff is not installed. Tier 1a is `error`, later tiers are skipped, stdout is
   a valid error envelope in `--json` mode, and exit code is 2.
6. A caller passes a target outside the project root or a target that does not
   exist. Discovery fails before any tier executes, the envelope reports an
   error, and exit code is 2.
7. A hung type checker or test suite is terminated at the configured timeout;
   the tier is `error`, never `pass`.

## Acceptance criteria

- **AC-1:** WHEN the user runs `strictr check [paths]` or
  `python -m strictr check [paths]`, the CLI SHALL default paths to `.` when
  none are given; accept `--json`, `--type-checker mypy|pyright|none`, and
  `--timeout SECONDS`; support a top-level `strictr --version`; and reject
  invalid arguments with a stderr message and exit code 2.
- **AC-2:** WHEN `--json` is supplied to a valid `check` invocation, the CLI
  SHALL write exactly one UTF-8, newline-terminated JSON object to stdout and no
  other stdout output; progress, warnings, and tracebacks SHALL not appear on
  stdout. Argparse usage errors SHALL use stderr and exit code 2 without a JSON
  envelope.
- **AC-3:** WHEN human output is used, the CLI SHALL write overall status,
  scope, and the first failures to stdout, and SHALL write warnings and the
  local-execution trust warning to stderr exactly once.
- **AC-4:** THE CLI SHALL exit 0 for `pass`, 1 for `fail`, and 2 for `partial`
  or `error`; it SHALL never return 0 when a requested required tier was skipped
  or errored.
- **AC-5:** WHEN targets are supplied, the CLI SHALL resolve one project root,
  normalize targets relative to it, reject missing targets and targets outside
  the root, and record `root`, `targets`, `files_checked`, and `files_skipped`
  in the scope ledger.
- **AC-6:** IF no `.py` or `.pyi` files are discovered, THEN the CLI SHALL
  return `error` with exit code 2 and an actionable reason; it SHALL not return
  `pass`.
- **AC-7:** Tier 0 SHALL parse every discovered `.py` and `.pyi` file; IF
  parsing fails, THEN the tier SHALL be `fail` with diagnostics containing path,
  line, column, and message, and later tiers SHALL be recorded as skipped. IF
  the in-process Tier 0 budget is exceeded, THEN the tier SHALL be `error` and
  later tiers SHALL be recorded as skipped.
- **AC-8:** Tier 1a SHALL run ruff with the project configuration, JSON output,
  and fixing disabled; findings SHALL be normalized and deterministically
  ordered; a missing ruff, crash, timeout, or invalid JSON SHALL be `error`; the
  ruff version SHALL be recorded.
- **AC-9:** Tier 1b SHALL select a type checker using the ADR 0005 precedence;
  WHEN both mypy and pyright are configured it SHALL use mypy and add a warning;
  a configured but unavailable checker SHALL be `error`; no available checker
  SHALL be `partial`; `--type-checker none` SHALL be `skipped` with
  `disabled_by_user` and SHALL not make the run `partial`.
- **AC-10:** Tier 1b SHALL run the selected checker, normalize mypy JSON Lines
  or pyright JSON into contract diagnostics, map errors, warnings, and notes,
  return `fail` when errors are found, and return `error` on crash, timeout, or
  invalid output; the checker version SHALL be recorded.
- **AC-11:** Tier 2 SHALL run the full pytest suite with a JUnit XML file in a
  temporary directory outside the repository; it SHALL parse failures, errors,
  skips, file and line information, test node IDs, and test counts; pytest exit
  code 5 SHALL be `skipped` with `no tests collected`, exit codes 2, 3, and 4
  SHALL be `error`, missing pytest when tests exist SHALL be `error`, and
  invalid XML SHALL be `error`.
- **AC-12:** THE pipeline SHALL stop after the first `fail` or `error` tier,
  record every later tier as `skipped` with `earlier_tier_failed`, and compute
  overall status with precedence `error > fail > partial > pass`.
- **AC-13:** THE tool runner SHALL execute without a shell from the project
  root, capture output as UTF-8 with replacement on decoding errors, enforce the
  ADR 0007 defaults and the `--timeout` override, terminate the process tree on
  timeout, and return `error` for a timeout or missing executable.
- **AC-14:** THE envelope SHALL cap diagnostics at 20 per tier, messages at
  2,000 characters, order diagnostics by path, line, column, code, and message,
  mark truncation explicitly, redact known secret patterns, and always include
  `trust.sandboxed: false` with the local-execution warning.
- **AC-15:** JSON output SHALL validate against the checked-in contract JSON
  Schema and golden fixtures; golden files SHALL contain no absolute paths or
  tool versions; additive fields SHALL remain allowed within schema version 1.
- **AC-16:** `README.md`, `CHANGELOG.md`, and `AGENTS.md` SHALL document the
  check command, and `docs/architecture/system-overview.md` SHALL record that
  spec `003` implements the architecture.

## Constraints

- Python 3.12 or newer; CI covers Python 3.13 on Linux and Windows.
- No runtime third-party dependencies. `jsonschema` is a test-only development
  dependency approved for contract validation.
- The package version stays `0.0.0`; `tool.version` reads `strictr.__version__`.
- The architecture module boundaries are binding, as refined by ADR 0008. No
  generic engine, plugin registry, dependency-injection framework, event bus, or
  async runtime.
- Tool commands run from the project root, use argument lists, never a shell,
  and use the current interpreter for `mypy` and `pytest`.
- `ruff` is resolved with `shutil.which`; `pyright` prefers
  `sys.executable -m pyright` when the Python wrapper is importable, then falls
  back to `shutil.which("pyright")`.
- Every JSON `path` is relative to the project root and uses `/` regardless of
  operating system. Display paths are not resolved through symlinks; resolution
  is used only for target confinement.
- `files_checked` is the number of discovered Python files in the requested
  scope, including files offered to Tier 0 before a budget abort.
- `files_skipped` counts enumerated `.py` and `.pyi` files rejected by
  Strictr's own ignore rules or explicit filters, such as non-regular files. A
  symlink that resolves outside the root is an error, not a skipped file. Files
  excluded by Git ignore rules are outside the candidate set and are not counted.
- Tool-level errors do not invent diagnostics without a file path. They use
  `skipped_reason` plus a small redacted `meta.error`; diagnostics are reserved
  for findings that have a path. This keeps the contract diagnostic shape
  valid without adding fields.
- Pytest failure evidence is placed in the diagnostic `message`, capped at
  2,000 characters, with the exception class in `exception`. No `evidence`
  field is added in v1.
- Human output has no color in v0.1. This is compliant with the contract's
  "colors only when" rule.
- Top-level warnings aggregate discovery warnings first, then tier warnings in
  execution order, deduplicated by exact string.
- Fixture projects are excluded from `ruff` and from pytest collection so
  intentional failures do not break the repository gate.
- Tests declare `pytest.mark.spec("003")` and tag every covered AC with
  `pytest.mark.ac("AC-n")`.
- Strictr performs no network access; invoked tools are not network-isolated and
  may perform their own network access. No telemetry and no unmeasured
  performance or detection claims.

## Open questions

Resolved by this spec:

- [x] Scope: full v0.1 `check` command, all four tiers — owner, 2026-11-21.
- [x] Verification contract changes: none in `003`; resolve gaps inside the
  current contract — owner, 2026-11-21.
- [x] JSON Schema validation: `jsonschema` as a test-only dependency — owner,
  2026-11-21.
- [x] `AGENTS.md` update: approved — owner, 2026-11-21.
- [x] Package version: keep `0.0.0` — owner, 2026-11-21.
- [x] Tier 0 timeout: in-process budget checked between files; no subprocess
  parser worker — owner, 2026-11-21.
- [x] No-path behavior: default to `.` — owner, 2026-11-21.
- [x] `--timeout` is one finite positive float that overrides every subprocess
  tier and version check for the run — owner, 2026-11-21.
- [x] Missing pytest with no test candidates or pytest configuration is a
  deliberate skip, not an error — owner, 2026-11-21.

Deferred to later specs:

- An `evidence` field, pytest locals, and richer assertion evidence.
- SARIF export, MCP/SDK transport, warm sessions, caching, and concurrency.
- Test selection with a full-suite false-pass evaluation.
- Sandbox isolation and a changed trust model.
- Color output and additional human-output polish.
- Performance measurements against the evaluation plan.

## Revision log

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-11-21 | 0.1 | Initial draft; planning decisions recorded | Ge Rui Sen |
| 2026-11-21 | 1.0 | ACs and blueprint approved; implementation not started | Ge Rui Sen |
| 2026-11-21 | 1.1 | Implementation started; T-2 contract schema work | Ge Rui Sen |
| 2026-11-21 | 1.2 | Clarified JSON usage errors, `earlier_tier_failed`, symlink confinement, and pyright resolution | Ge Rui Sen |
| 2026-11-21 | 1.3 | Clarified version scope, Tier 0 budget, files ledger, warnings, and network boundary | Ge Rui Sen |
