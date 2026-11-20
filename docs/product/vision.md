# Product Vision

Status: draft for `001-product-discovery` approval
Owner: Ge Rui Sen
Last updated: 2026-11-20
Related: [evaluation.md](evaluation.md), `specs/active/001-product-discovery/spec.md`

## Positioning

Strictr is a local, deterministic verification gateway for agent-generated
Python patches. It runs existing tools with their existing configuration and
returns one compact, fail-closed evidence envelope.

It is not a linter, type checker, test runner, or LLM judge.

## Problem

An agent can already run `ruff`, `mypy`, and `pytest`. What it cannot cheaply get
is one trustworthy answer to four questions:

1. What was actually verified about this patch?
2. What failed, and where is the root cause?
3. What is the next minimal fix?
4. What was skipped or unverified?

The current pattern is a chain of independent commands. Each command starts a
process, loads configuration, parses code, emits a different format, and adds
noise to the agent's context. The agent then has to decide what to run, in what
order, and how to combine the results. The result is a slow, noisy, and
inconsistent verification loop with no single record of what was checked.

The bottleneck is the **verification evidence layer**, not the detection
capability of the underlying tools.

## Evidence and assumptions

### What we know

- Agentic workflows benefit from deterministic checks with clear pass/fail
  signals rather than model judgment.
- Compiler and test feedback improve repair quality, but feedback must be
  interpretable.
- Long, noisy contexts degrade model performance; compact evidence matters.
- Mypy's daemon is materially faster on repeated checks than cold runs.
- Test selection can produce false passes in dynamic Python; this is a safety
  risk, not just a performance optimization.
- Public coding benchmarks are saturating and have contamination concerns, so
  they are directional evidence, not product proof.

### What we assume

- Agent-heavy users will adopt a tool that reduces repair iterations or tokens
  while preserving the underlying tools' findings.
- A stable JSON envelope plus a single CLI/MCP call is more useful than a
  sequence of tool-specific outputs.
- Users prefer a local tool over a hosted service for source code verification.
- Zero-configuration defaults are necessary for adoption; a mandatory new config
  file is a barrier.

### What is not proven

- The size of the latency and token reduction in real agent loops.
- The detection rate on a representative fault population.
- Willingness to switch from raw commands or IDE-integrated diagnostics.
- That test selection can be made safe enough to enable by default.

These are evaluation questions, not marketing claims.

## Target users

### Primary

**Agent harness builders and AI-heavy solo developers.**

They run coding agents that edit Python repositories and need a verification
step inside the agent loop. Their constraints are latency, token budget, stable
tool output, and trust: a false pass is worse than a slow failure.

Jobs to be done:

- Verify a patch before presenting a diff or opening a PR.
- Know exactly which checks ran and which were skipped.
- Get a minimal, causal diagnostic that the agent can act on.
- Keep the project's existing tool configuration and versions.
- Avoid running four commands and pasting four logs into context.

### Secondary

**Teams with existing pre-commit and CI pipelines.**

They want a local inner-loop tool that produces the same findings as their
authoritative pipeline, plus a machine-readable record for review. They will
adopt only if the tool preserves parity and does not weaken gates.

### Not primary for v0.1

- Developers who only use an IDE and already have warm language-server feedback.
- Large monorepos that require distributed caching or build-system integration.
- Regulated environments that require strong isolation before executing code.
- Multi-language repositories. Strictr is Python-only in v0.1.

## Current alternatives and gap

| Alternative | Strength | Gap for the agent inner loop |
|---|---|---|
| Raw CLI chain (`ruff`, `mypy`, `pytest`) | Ubiquitous, exact, configurable | Multiple startups, formats, and round trips; no single evidence record |
| Pre-commit hooks | Fast local feedback; easy policy | Commit-time, not patch-level; still separate tools; easy to bypass |
| IDE / language server | Warm diagnostics, good human UX | Not headless, not scriptable, not a verification transaction |
| CI pipeline | Authoritative, isolated, auditable | Too slow for the inner loop; logs are noisy and remote |
| Agent hooks (`PostToolUse`, `Stop`) | Deterministic automation at the right moment | Usually call one command; no tiered, normalized result |
| MCP verification servers | Agent-native transport | Often single-tool, hosted, or lacking parity and fail-closed semantics |
| LLM-as-a-judge | Can reason about intent | Unreliable for mechanical errors; adds cost and nondeterminism |
| Formal verification / SMT | Strong guarantees | Too slow and expensive for the inner loop; not general-purpose |
| Unified linters/formatters | One tool, fast | Unifies lint and formatting, not type checking, tests, and evidence scope |

The gap: a **local, parity-preserving, fail-closed, compact verification
transaction** that an agent can call across tiers and trust.

## Value proposition

- **One transaction:** one invocation returns status, scope, diagnostics,
  timings, and tool versions.
- **Parity:** findings match the underlying tools run with the project's
  configuration.
- **Compact evidence:** root-cause diagnostics instead of raw runner logs.
- **Honest scope:** skipped tiers and tests are explicit; a partial run is never
  reported as a pass.
- **Local-first:** source code stays on the developer's machine.
- **Additive:** keep the existing tools and CI; Strictr wraps them.

## Product principles

1. **Deterministic over judgment.** Use compilers, type checkers, and tests.
   No LLM in the verification path.
2. **Fail closed.** Missing tools, crashes, and timeouts are errors, not passes.
3. **Parity first.** A faster or prettier result that disagrees with the tools is
   worse than no result.
4. **Evidence over prose.** Emit structured, minimal, causal diagnostics.
5. **Additive.** Do not replace the ecosystem or force a new configuration.
6. **Explicit trust.** v0.1 runs locally without isolation and says so.
7. **Small scope.** Ship the narrow loop first; earn every optimization with
   measurements.
8. **No hidden skips.** Every unverified area appears in the result.

## Decisions locked

These decisions are binding for v0.1 and the first architecture spec:

- **Primary user:** agent-first. Agent harness builders and AI-heavy developers
  are the wedge; general IDE users are not.
- **Trust stance:** local-only execution in v0.1, with an explicit warning that
  it is not a sandbox. Real isolation is a later spec.
- **v0.1 scope:** Tier 0 (parse) and Tier 1 (ruff plus an available type
  checker), plus compact pytest output. Full tests run by default; no test
  selection.
- **Metrics:** thresholds are conditional hypotheses, not promises. See
  [evaluation.md](evaluation.md).
- **Non-goals:** the locked list below.
- **Language:** Python only.
- **Distribution:** a local CLI and Python package; MCP and SDK integrations
  come after the envelope is stable.

## Goals

- **G1 — Trustworthy evidence.** Every result states what ran, what passed,
  what failed, and what was skipped.
- **G2 — Fewer loops.** Reduce repair iterations or tokens in a controlled agent
  loop without hiding findings.
- **G3 — Parity.** Produce the same actionable findings as direct tool runs.
- **G4 — Adoptable.** Work in an existing Python repository with zero new
  configuration and a short install.
- **G5 — Measured.** Every performance or detection claim is backed by a
  reproducible evaluation.
- **G6 — Extensible later.** Add patch sessions, warm sessions, MCP, isolation,
  and test selection only after the core envelope is stable.

## Non-goals (locked for v0.1)

- Not a replacement for `ruff`, `mypy`/`pyright`, or `pytest`.
- No LLM-as-a-judge and no LLM calls in the verification path.
- No auto-fix or code rewriting.
- No generated tests treated as proof of correctness.
- No formal verification, SMT, or symbolic execution.
- No multi-language support.
- No test selection or test-impact analysis in v0.1. The full suite is the
  default; selection is a later, opt-in feature with a false-pass evaluation.
- No Hypothesis/property fuzzing in v0.1.
- No warm daemons, persistent workers, or caching required in v0.1. Optimize
  only after the cold path is measured.
- No Docker, microVM, or sandbox isolation in v0.1. Execution is local and
  explicitly not a security boundary.
- No MCP server in v0.1. CLI and Python API first; MCP after the schema is
  stable.
- No CI replacement. CI remains the authoritative outer gate.
- No coverage gate and no telemetry without explicit consent.

## Scope and phases

### v0.1 — the verification gateway

- `strictr check <paths> [--json]`.
- Tier 0: parse Python files and report syntax diagnostics.
- Tier 1: run `ruff` and an available type checker with the project's config.
- Tier 2: when tests exist and are not disabled, run `pytest` and emit compact
  failure evidence.
- Human-readable output by default; stable JSON envelope for tools.
- Exit codes: `0` pass, `1` fail, `2` tool/config error.
- Timeouts and explicit skipped/error statuses.
- Local execution warning in documentation and output where relevant.

### Later, with separate specs

- Patch application and rollback sessions.
- MCP server and agent hooks.
- Warm sessions and incremental caching.
- Opt-in test selection with a full-suite safety mode.
- Sandboxed execution (Docker or microVM).
- SARIF export and CI annotations.
- Property-based crash probing and other experimental oracles.
- Additional languages.

## Adoption path

1. **Shadow mode:** run Strictr alongside the current commands; compare findings.
2. **JSON mode:** use the compact envelope in an agent loop.
3. **Agent integration:** expose one verification call through the CLI, then a
   Python API, then MCP and hooks.
4. **Optimize:** add caching or warm sessions only if the evaluation shows the
   cold path is the bottleneck.
5. **CI:** keep the existing pipeline authoritative; optionally consume the same
   envelope for review annotations.

The migration contract is: same findings, fewer turns and tokens, explicit
scope, and no lock-in.

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| False confidence from a partial or stale run | Agent ships a bug; trust is lost | Fail-closed statuses; full tests by default; parity tests |
| Divergence from underlying tools | Users cannot rely on results | Same configs and versions; parity corpus in CI |
| Tool output and version drift | Parsers break silently | Canned-output tests; versioned schema; explicit tool versions |
| Executing untrusted code locally | Arbitrary code execution | Document clearly; timeouts; isolation in a later spec |
| Benchmark theater | Optimizes the demo, not the product | Pre-registered metrics; custom mutation and agent-loop benchmarks |
| Scope creep back to the “unified engine” | Delays the first release | Locked non-goals; one spec at a time |
| Agent harnesses bypass the tool | No adoption | CLI/JSON first, then MCP and hooks; measure actual use |
| Windows process and path differences | Broken local experience | Test matrix; normalized paths; no shell-specific assumptions |
| Performance disappointment | Users return to raw commands | Measure cold path; publish conditions, not slogans |

## Open questions

The following are intentionally not decided in 001:

- Exact benchmark corpus and thresholds (owned by `evaluation.md`).
- Which type checker is the default, and how to choose when both are installed.
- Packaging and distribution details.
- Whether SARIF export belongs in v0.1 or later.
- The timing and transport for MCP integration.
- Telemetry or local usage reports, and their privacy model.
- The order of agent-harness integrations.

## Success and kill criteria

Success and kill criteria are defined in
[evaluation.md](evaluation.md#kill-criteria). In summary:

- Success requires parity, a measurable reduction in tokens or iterations, a
  trustworthy scope record, and real agent-loop adoption.
- The project should stop or narrow if it cannot prove parity, produces a false
  pass, or shows no measurable gain over a warm IDE/pre-commit workflow.

## References

- Mypy daemon: <https://mypy.readthedocs.io/en/latest/mypy_daemon.html>
- Test-impact-analysis false negatives: <https://github.com/breadMSA/pytest-tia>
- pytest-testmon limitations: <https://pypi.org/project/pytest-testmon/>
- Compiler-feedback repair research: <https://arxiv.org/pdf/2311.09868v5.pdf>
- Context rot: <https://redis.io/blog/context-rot>
- DORA 2025 AI-assisted development report: <https://dora.dev/dora-report-2025>
- Why SWE-bench Verified is no longer used: <https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/>
- SARIF overview: <https://www.sonarsource.com/resources/library/sarif/>
- OWASP workload sandboxing validation: <https://github.com/OWASP/AISVS/blob/main/1.0/research/chapters/C04-Infrastructure/C04-01-Workload-Sandboxing-Validation.md>
- Agent hooks and verification practice: <https://developer.vonage.com/en/blog/beyond-vibe-coding-best-practices-2026>
