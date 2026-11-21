# ADR 0007: Local trust boundary, timeouts, and process termination

- Status: accepted; Tier 0 budget refined by [ADR 0009](0009-v0-1-execution-refinements.md)
- Date: 2026-11-21
- Decision makers: Ge Rui Sen

## Context

Strictr runs type checkers and pytest against generated code. Importing target
modules and running tests executes arbitrary code with the user's privileges.
v0.1 is local-only and is not a sandbox. The product must say this clearly, bound
execution with timeouts, and avoid leaking secrets into diagnostics.

## Decision drivers

- Honest trust claims.
- No hung processes from an agent loop.
- Windows and Linux behavior.
- Minimal runtime dependencies.
- Clear path from local mode to future isolation.

## Considered options

1. **Local execution with an explicit warning.**
   Matches v0.1 scope; fast to build; not a security boundary.
2. **Docker from v0.1.**
   Stronger isolation, but adds startup cost, lifecycle complexity, and a hard
   dependency.
3. **MicroVM from v0.1.**
   Strongest isolation, but out of scope for a first local CLI.
4. **No timeout, rely on the user.**
   Unacceptable for agent loops.

## Decision

v0.1 uses local execution with explicit trust metadata:

- `trust.sandboxed` is always `false`.
- The human output prints a one-time warning; JSON includes the trust object.
- No network isolation is claimed.
- Targets are confined to the project root; no shell is used.
- Temporary JUnit files are created outside the repository and cleaned up.
- Diagnostics are capped and known secret patterns are redacted.
- No telemetry.

Timeouts and process termination:

- Defaults: Tier 0 10 s, ruff 30 s, type checker 180 s, pytest 300 s.
- Tier 0 is an in-process budget checked between files; hard process termination
  applies to subprocess tiers (ADR 0009).
- A CLI timeout override applies to the selected tiers and their version checks
  (ADR 0009).
- On timeout, the tier is `error`, never `pass`.
- On POSIX, start the child in a new session and kill the process group.
- On Windows, use a new process group and terminate the tree with
  `taskkill /T /F`.
- Capture stdout/stderr as UTF-8 with replacement on decoding errors.

Isolation is deferred to a separate spec. That spec must define the isolation
technology, network policy, filesystem mounts, resource limits, and how the
trust metadata changes.

## Consequences

Good:

- The trust claim is honest and machine-readable.
- Hung tools cannot block the agent indefinitely.
- The runner is a single seam for later sandboxing.

Bad:

- v0.1 can execute malicious code.
- Process-tree termination has platform-specific behavior to test.
- A future sandbox will change startup latency and packaging.

## Confirmation

- Tests cover timeout, crash, missing executable, invalid output, and process
  cleanup on Windows and Linux.
- The contract test asserts `trust.sandboxed is false`.
- Documentation and human output include the warning.
