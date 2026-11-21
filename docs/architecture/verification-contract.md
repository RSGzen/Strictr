# Verification Contract v1

Status: approved (spec `002` archived)
Owner: Ge Rui Sen
Last updated: 2026-11-21
Related: [system overview](system-overview.md),
[ADR 0004](../adr/0004-verification-contract-and-statuses.md)

## Purpose

This document defines the machine-readable result of `strictr check`. The
contract is the product's public interface; the implementation must conform to
it. It is versioned and tested independently of the tools.

## Top-level envelope

```json
{
  "schema_version": "1",
  "tool": {
    "name": "strictr",
    "version": "0.1.0"
  },
  "status": "fail",
  "scope": {
    "root": ".",
    "targets": ["src", "tests"],
    "files_checked": 42,
    "files_skipped": 0,
    "tests_collected": 120,
    "tests_run": 120,
    "tests_skipped": 0
  },
  "tiers": [
    {
      "id": "tier0",
      "name": "syntax",
      "status": "pass",
      "tool": null,
      "duration_ms": 12,
      "diagnostics": [],
      "skipped_reason": null,
      "meta": {}
    },
    {
      "id": "tier1-ruff",
      "name": "lint",
      "status": "fail",
      "tool": {"name": "ruff", "version": "0.17.5"},
      "duration_ms": 84,
      "diagnostics": [
        {
          "tier": "tier1-ruff",
          "source": "ruff",
          "path": "src/app.py",
          "line": 3,
          "column": 1,
          "end_line": 3,
          "end_column": 5,
          "code": "F401",
          "severity": "error",
          "message": "`os` imported but unused",
          "url": "https://docs.astral.sh/ruff/rules/unused-import"
        }
      ],
      "skipped_reason": null,
      "meta": {}
    }
  ],
  "timings": {
    "total_ms": 1200
  },
  "environment": {
    "python": "3.13.0",
    "platform": "win32",
    "root": "."
  },
  "trust": {
    "sandboxed": false,
    "warning": "Local execution; not a security boundary."
  },
  "warnings": []
}
```

Top-level rules:

- `schema_version` is a string. v1 is `"1"`.
- `status` is one of `pass`, `fail`, `partial`, `error`.
- `tool.version` is the Strictr package version.
- `scope` always describes what was and was not inspected.
- `tiers` is ordered by execution order.
- `trust` is always present and always states `sandboxed: false` in v0.1.
- `warnings` contains non-fatal messages that do not change `status`.

## Status model

### Overall status

| Status | Meaning | Exit code |
|---|---|---|
| `pass` | Every requested required tier ran and passed; optional skips are explicit | 0 |
| `fail` | At least one executed tier found errors | 1 |
| `partial` | A required check could not run, e.g. no type checker found | 2 |
| `error` | Missing required tool, crash, timeout, invalid output, or configuration error | 2 |

`pass` is not allowed when a requested required check was silently skipped.
`warnings` do not change the status.

### Tier status

| Status | Meaning |
|---|---|
| `pass` | The tier ran and found no failures |
| `fail` | The tier ran and found failures |
| `skipped` | The tier did not run; `skipped_reason` is required |
| `error` | The tier could not complete; `skipped_reason` or metadata explains why |

### Tier requirements

- Tier 0 (syntax) is always required.
- Tier 1a (ruff) is required. Missing ruff is `error`.
- Tier 1b (type checking) is required when a checker is configured or detected.
  No checker available is `partial`, unless the user explicitly chose
  `--type-checker none`.
- Tier 2 (tests) is required when tests exist. No tests is `skipped` and does not
  make the result `partial`. Missing pytest when tests exist is `error`.
- A user-disabled check is recorded as `skipped` with
  `skipped_reason: "disabled_by_user"` and is a deliberate reduction of scope.

### Fail-fast

The default pipeline stops after the first failing tier. Later tiers are
recorded as `skipped` with `skipped_reason: "earlier_tier_failed"`. Their
absence is never implied to be a pass.

## Scope ledger

| Field | Meaning |
|---|---|
| `root` | Project root, relative POSIX path |
| `targets` | Requested target paths |
| `files_checked` | Python files inspected by Tier 0/1 |
| `files_skipped` | Files excluded by ignore rules or explicit filters |
| `tests_collected` | Tests collected by pytest, if run |
| `tests_run` | Tests executed, if run |
| `tests_skipped` | Tests skipped by pytest, if run |

The scope ledger is the evidence that the result is not hidden. It is required
even when the result is `pass`.

## Diagnostic object

```json
{
  "tier": "tier1-types",
  "source": "mypy",
  "path": "src/app.py",
  "line": 12,
  "column": 9,
  "end_line": 12,
  "end_column": 15,
  "code": "operator",
  "severity": "error",
  "message": "Unsupported operand types for + (\"int\" and \"str\")",
  "test": null,
  "exception": null,
  "url": null
}
```

Rules:

- `path` is relative to the project root and uses `/` regardless of OS.
- `line` and `column` are 1-based. `end_line` and `end_column` are optional.
- `severity` is `error`, `warning`, or `note`.
- `code` is the tool's rule/error code when available; otherwise a stable
  Strictr code such as `syntax-error` or `tool-timeout`.
- `test` is the pytest node ID when the diagnostic comes from a test.
- `exception` is the exception class name when available.
- `url` is an optional rule documentation link.
- Messages and evidence are capped and redacted. Truncation is explicit.

## Tier result

| Field | Meaning |
|---|---|
| `id` | Stable tier ID: `tier0`, `tier1-ruff`, `tier1-types`, `tier2-pytest` |
| `name` | Human name |
| `status` | Tier status |
| `tool` | Tool name and version, or `null` |
| `duration_ms` | Tier wall time |
| `diagnostics` | Ordered diagnostics |
| `skipped_reason` | Required when `skipped` or `error` is a skip/error reason |
| `meta` | Small structured metadata, e.g. selected type checker |

## Truncation and limits

- Maximum diagnostics per tier: 20.
- Maximum message length: 2,000 characters.
- Maximum optional evidence length: 500 characters.
- When a limit is reached, keep the first N in deterministic order, set
  `meta.truncated: true`, and record the original count in
  `meta.total_diagnostics`.
- Never truncate silently. The envelope must make missing evidence visible.

## Ordering

Diagnostics are ordered deterministically:

1. Tier order.
2. Path ascending.
3. Line ascending.
4. Column ascending.
5. Code ascending.
6. Message ascending.

Tier results are in execution order.

## Human output

- Default output is concise: overall status, scope, first failures, and a local
  trust warning.
- Human output goes to stdout.
- Logs and the trust warning go to stderr.
- `--json` suppresses human output; stdout contains JSON only.
- Colors are used only when stdout is a TTY and `NO_COLOR` is not set.

## JSON output

- `--json` writes one JSON object to stdout and nothing else.
- Progress logs, warnings, and tracebacks go to stderr.
- The JSON is UTF-8 and newline-terminated.
- Consumers must key on `schema_version` and tolerate additive fields.

## Versioning

- `schema_version` changes only for breaking contract changes.
- Additive fields are allowed within v1.
- Removing or renaming a field requires a new schema version and an ADR.
- The contract is tested by JSON Schema and golden fixtures. The machine-readable
  schema is
  [`verification-contract.schema.json`](verification-contract.schema.json).

## Trust metadata

```json
"trust": {
  "sandboxed": false,
  "warning": "Local execution; not a security boundary."
}
```

v0.1 is local-only. `trust.sandboxed` is always `false` and is not configurable.
Running pytest or importing target code can execute arbitrary code. A future
isolation spec may change this field; consumers must read it rather than assume.

## Examples

### Pass

```json
{
  "schema_version": "1",
  "status": "pass",
  "scope": {"files_checked": 3, "files_skipped": 0},
  "tiers": [
    {"id": "tier0", "status": "pass", "diagnostics": []},
    {"id": "tier1-ruff", "status": "pass", "diagnostics": []},
    {"id": "tier1-types", "status": "pass", "diagnostics": []},
    {"id": "tier2-pytest", "status": "pass", "diagnostics": []}
  ],
  "trust": {"sandboxed": false, "warning": "Local execution; not a security boundary."},
  "warnings": []
}
```

### Partial

```json
{
  "schema_version": "1",
  "status": "partial",
  "scope": {"files_checked": 3},
  "tiers": [
    {"id": "tier1-types", "status": "skipped", "skipped_reason": "no type checker found"}
  ],
  "trust": {"sandboxed": false, "warning": "Local execution; not a security boundary."},
  "warnings": ["No type checker found; install mypy or pyright for a full pass."]
}
```

### Error

```json
{
  "schema_version": "1",
  "status": "error",
  "tiers": [
    {"id": "tier1-ruff", "status": "error", "skipped_reason": "ruff not found"}
  ],
  "trust": {"sandboxed": false, "warning": "Local execution; not a security boundary."},
  "warnings": []
}
```
