---
id: "004"
title: "Verification hardening and edge-case coverage"
status: draft
owner: "Ge Rui Sen"
created: 2026-11-22
updated: 2026-11-22
branch: "feat/004-verification-hardening"
---

# Verification hardening and edge-case coverage

## Context

Spec `003-check-command` delivered the `strictr check` CLI and its four tiers.
The post-`003` audit found remaining gaps in paths that are hard to reach but
important to trust: nested working directories, symlink display paths, non-UTF8
filenames on POSIX, human-output visibility for skipped/error evidence, real
configuration parity, redaction through real tool output, and the traceability
entry point's I/O failure paths.

This spec closes those gaps without changing the v1 verification contract. Most
of the behavior already exists; the work is to make it explicit, test it through
the CLI, and fix the small number of paths that are currently unsafe or silent.
No new configuration file, flag, tier, dependency, or JSON field is introduced.

This spec depends on `003` being merged to `main` first. The branch is based on
`main`; rebase it after `003` lands.

## Goals

- Lock the scope-ledger behavior for subdirectory invocations and in-root
  symlinks with executable tests.
- Keep JSON valid UTF-8 and human output safe when POSIX filenames are not
  valid UTF-8.
- Make human output show skipped-file counts and actionable error evidence
  instead of only a generic reason.
- Prove type-checker and pytest configuration parity through the real CLI,
  including pyright through an importable test module.
- Prove redaction and truncation on real pytest/ruff output.
- Cover the traceability entry point's environment, git, spec, and AC-report
  failure paths without changing its policy.
- Preserve the v1 contract, exit codes, and existing `003` frozen tests.

## Non-goals

- No new CLI flags, configuration file, tier, output field, or schema version.
- No real pyright dependency in CI; pyright coverage uses an importable fake
  module.
- No sandbox, network isolation, daemon, cache, concurrency, or test selection.
- No SARIF, MCP, SDK, or agent-hook work.
- No change to traceability policy; only its I/O entry path is covered.
- No config-parse-error policy change (`ConfigError` remains deferred).
- No pyright wrapper-to-executable fallback; deferred to a later spec.
- No broader `.pyi` acceptance matrix; existing `003` Tier 0 coverage remains.
- No Windows non-regular-file coverage; the POSIX FIFO test is the skipped-file
  case.
- No human color output.
- No performance or detection claims; no measurements in this spec.

## Scenarios

1. An agent runs `strictr check --json` from `project/src` with no targets. The
   root resolves to the project, the ledger records the invocation-relative root
   and the cwd subdirectory as the target, and only that subtree is checked.
2. A project contains `link.py` pointing at `real.py` inside the root. Strictr
   reports `link.py` in scope and diagnostics, not `real.py`.
3. A POSIX project contains a Python file whose name is not valid UTF-8. Strictr
   emits parseable UTF-8 JSON and human output does not crash.
4. A project has one non-regular `.py` candidate. Human output shows that one
   file was skipped, and JSON records `files_skipped: 1`.
5. A pytest collection error occurs. Human output includes the actionable
   collection message, not only `tool failed`.
6. A project configures mypy, both checkers, or pyright. The CLI records the
   configured selection and warnings, and a fake pyright module executes through
   the normal subprocess/parser path.
7. A project configures pytest `testpaths`. The CLI runs the configured suite,
   not the default directory.
8. A real pytest failure includes a secret or a very long assertion message.
   JSON output redacts/caps it and marks truncation.
9. Ruff returns more than 20 findings. JSON keeps 20 with an explicit total, and
   human output shows how many were hidden.
10. Traceability runs with missing environment variables or a failing git
    command. It exits 1 with a stderr message; a valid configuration exits 0.

## Acceptance criteria

- **AC-1:** WHEN `strictr check` is invoked from a project subdirectory with no
  targets, the CLI SHALL resolve the root with the `003` marker search, record
  `scope.root` relative to the invocation directory and `scope.targets` relative
  to the root (for example `root: ".."`, `targets: ["src"]`), and inspect only
  the requested subtree. Explicit and absolute targets SHALL normalize with the
  same rules.
- **AC-2:** WHEN a discovered or explicitly targeted `.py` or `.pyi` file is a
  symlink that resolves inside the project root, Strictr SHALL report the link
  path, not the resolved target path, in `scope.targets` and diagnostic paths;
  resolution SHALL be used only for confinement.
- **AC-3:** WHEN a POSIX file path contains bytes that are not valid UTF-8, the
  CLI SHALL emit a newline-terminated JSON object whose bytes are valid UTF-8
  and which parses against the v1 schema; human mode SHALL not raise
  `UnicodeEncodeError`. Valid Unicode paths SHALL remain readable in JSON, and
  only undecodable path characters SHALL be escaped.
- **AC-4:** WHEN `files_skipped` is greater than zero, human output SHALL include
  the skipped count. WHEN a tier has status `error`, human output SHALL include
  actionable error evidence: its diagnostics when present, otherwise its
  redacted `meta.error`, in addition to the skipped reason.
- **AC-5:** WHEN the project configures mypy, or both mypy and pyright, the CLI
  SHALL select mypy with `meta.selection: "config"` and emit the both-configured
  warning exactly once. WHEN `--type-checker pyright` is requested and the
  pyright Python wrapper is available, Strictr SHALL execute it as
  `sys.executable -m pyright`, normalize its JSON diagnostics, and record its
  version. A configured checker that cannot be probed SHALL be `error`.
- **AC-6:** WHEN the project pytest configuration defines `testpaths`, the CLI
  SHALL run the configured suite, record its test counts, and not collect test
  files outside those paths by default.
- **AC-7:** WHEN a real pytest failure contains a known secret pattern, JSON
  diagnostic messages SHALL redact it. WHEN real diagnostics exceed the message
  or count limits, JSON SHALL cap them, set `meta.truncated`, and record
  `meta.total_diagnostics` when count-capped; human output SHALL show the hidden
  diagnostic count.
- **AC-8:** `python scripts/check_traceability.py` SHALL exit 0 only when the
  environment, branch, title, spec, commits, and AC coverage pass; missing
  environment, a git collection failure, a malformed spec/AC report, or a policy
  error SHALL write a message to stderr and exit 1. The pure traceability policy
  SHALL remain unchanged.

## Constraints

- `003` must be merged to `main` before implementation starts. Rebase this branch
  on `main` after `003` lands.
- The v1 verification contract, schema, statuses, and exit codes are unchanged.
  Human output changes are additive lines; existing `003` frozen tests must not
  be edited.
- No runtime third-party dependencies. Tests may use the existing `jsonschema`
  development dependency.
- Python 3.12+; Windows and Linux CI. Non-UTF8 filesystem tests are POSIX-only
  and skip on Windows.
- No real pyright in CI. The pyright test module is a test fixture placed on
  `PYTHONPATH`; it must not be described as real pyright coverage.
- Traceability tests must not use the network. Git-facing behavior is faked or
  run in a temporary local repository.
- Fixture projects and generated files are copied or created under `tmp_path`;
  no test runs tools in the repository.
- Keep the branch small: one spec, one PR, one review cycle.

## Open questions

Owner decisions to confirm at Phase 1 approval:

- [ ] Nested-cwd ledger: the current behavior (`root` relative to the invocation
  directory, `targets` relative to the root) is the intended contract — owner,
  before T-1.
- [ ] Human output format: the exact skipped-count suffix and error-evidence
  indentation in the blueprint are approved — owner, before T-4.
- [ ] Non-UTF8 output: escaping lone surrogates while keeping valid Unicode
  readable is the approved representation — owner, before T-3.

Deferred to later specs:

- [ ] Pyright wrapper-to-executable fallback when the importable wrapper fails
  its probe.
- [ ] Fail-closed handling of unreadable or invalid project configuration
  (`ConfigError` is currently unused).
- [ ] `.pyi`-specific CLI acceptance coverage.
- [ ] Windows coverage for non-regular `.py` candidates; POSIX FIFO coverage is
  used instead.
- [ ] Human-output color and richer formatting.
- [ ] Traceability policy expansion beyond the current gate.

## Revision log

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-11-22 | 0.1 | Initial draft for the post-`003` hardening slice | Ge Rui Sen |
