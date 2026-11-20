# Evaluation Plan

Status: approved (spec 001 archived)
Owner: Ge Rui Sen
Last updated: 2026-11-21
Related: [vision.md](vision.md), spec 001 (archived)

## Purpose

This document defines how Strictr is evaluated before performance, token, or
detection claims are made. The purpose is to make claims falsifiable and to
prevent benchmark theater.

Every numeric target in this document is a **conditional hypothesis** until it
is measured on the stated workload. It is not a product promise.

## Evaluation questions

1. **Parity:** Does Strictr report the same actionable findings as the
   underlying tools with the same configuration?
2. **Efficiency:** Does it reduce wall-clock latency, tool-call count, or
   diagnostic tokens in a realistic agent loop?
3. **Repair:** Does it reduce the number of repair iterations or tokens needed
   to reach a green state, or improve evidence quality at equal cost?
4. **Safety:** Can it produce a false pass, hide a skipped tier, or miss a
   failing test?
5. **Reliability:** Is it deterministic across repeated runs, platforms, and
   tool versions?
6. **Adoption:** Do agent-heavy users choose it over the raw command chain?

## Metrics

| Metric | Definition | Unit | Method |
|---|---|---|---|
| **End-to-end latency** | Time from invocation to process exit | ms | Wall-clock measurement, cold and warm, p50/p95 |
| **Tier latency** | Time spent in Tier 0, 1, and 2 | ms | Internal timings plus external wall clock |
| **Diagnostic tokens** | Tokens in the emitted failure evidence | tokens | Tokenizer count on raw vs compact output |
| **Tool-call count** | Number of CLI/MCP calls per verification | calls | Harness trace |
| **Parity** | Findings match direct tool runs after normalization | percentage / count | Diff against baseline tool outputs |
| **False pass** | A run reports pass while a required check failed or was skipped | count | Fault injection and full-suite oracle |
| **Detection** | Injected faults reported as failures | percentage | Mutation corpus |
| **False positive** | Clean input reported as failing | count | Clean corpus and real repositories |
| **Repair iterations** | Attempts before the agent reaches green | iterations | Controlled agent loop |
| **Repair tokens** | Total model tokens consumed in the loop | tokens | Harness accounting |
| **Test-selection safety** | Selected tests vs full suite on a failing change | false-pass rate | Full suite as oracle |
| **Flake rate** | Same input changes result across repeated runs | percentage | N repeated runs |
| **Timeout/error handling** | Crashed or hung tools produce `error`, not `pass` | count | Fault injection |
| **Cache stale rate** | Cached result differs from an uncached run | count | Paired runs after invalidation events |
| **Resource use** | CPU, memory, disk, worker startup | seconds / MB | Process and container metrics |
| **Adoption** | Install success, time to first result, replacement rate | count / minutes | Opt-in reports or study |

## Baseline configurations

Every experiment compares Strictr against at least one baseline:

| Baseline | Description | Purpose |
|---|---|---|
| **Raw cold chain** | `ruff`, then `mypy`, then `pytest`, each cold | The common script/CI pattern |
| **Raw warm chain** | `ruff`, warm `dmypy`/pyright, then `pytest` | The realistic local optimum |
| **IDE/LSP** | Editor diagnostics from ruff/pyright | Human inner-loop reference |
| **CI** | Repository pipeline | Authoritative outer gate |
| **Strictr cold** | v0.1 default | First-release measurement |
| **Strictr warm** | Later optimization | Post-v0.1 measurement |

The raw warm chain is the important baseline. Comparing only against a cold
chain makes the improvement look larger than it is.

## Workloads and corpus

### Fixture repositories

- **Small:** 10 Python files, 1 test file, no external dependencies.
- **Medium:** 100 Python files, 10 test files, one configured type checker.
- **Large:** 1,000 Python files, representative package layout, a test suite
  with shared fixtures.

Fixtures must be committed, deterministic, and free of network access.

### Real repositories

Use public Python repositories with pinned commits and compatible licenses.
Record the repository, commit, Python version, tool versions, and configuration.
Do not use private code in public reports.

### Fault corpus

Use mutation testing (`mutmut` or `cosmic-ray`) to inject known faults:

- syntax errors
- name and attribute errors
- type mismatches
- boundary and empty-input errors
- test-breaking logic changes
- security-relevant patterns where applicable

Each fault has a known expected failure tier. Clean baselines establish the
false-positive rate.

### Agent-loop benchmark

Build a controlled harness with a fixed model, prompt, repository, and task set.
The harness must be able to run:

- the raw cold chain
- the raw warm chain
- Strictr

Measure iterations, tokens, wall-clock time, and final correctness. Record the
model version and harness commit. Do not claim general model improvement from a
single model or task.

### Failure classes

Report results by class rather than a single aggregate:

- syntax
- lint
- type
- test failure
- boundary/empty input
- security
- tool crash/timeout
- missing tool

## Measurement protocol

### Latency

- Run each configuration at least 20 times per workload.
- Report p50 and p95, not just the mean.
- Separate cold and warm runs.
- Record hardware, OS, Python version, tool versions, and repository size.
- Use `hyperfine` or a comparable external timer for end-to-end latency.
- Exclude install time; report it separately.

### Tokens

- Count tokens with the tokenizer of the target model.
- Compare raw tool output with Strictr output for the same failure.
- Report the distribution, not only the best case.
- Track "actionable tokens" separately if a human or model evaluation can
  classify them.
- Never truncate evidence silently; truncation must be explicit.

### Parity

- Normalize findings to a common structure: path, line, column, code, message.
- Compare sets, not text formatting.
- Report missing findings, extra findings, and changed severity separately.
- Run on both clean and faulty repositories.
- Any unexplained missing finding blocks a release.

### Detection and false positives

- Run the mutation corpus and clean corpus.
- Report detection by fault class.
- Report false positives on clean code.
- Do not aggregate away failures in a single class.

### Repair efficiency

- Use a fixed agent harness and task set.
- Run each configuration multiple times; models are stochastic.
- Report iterations, tokens, wall-clock time, and final correctness.
- Record failures and abandoned runs, not only successes.
- Compare against the raw warm chain, not only cold commands.

### Test-selection safety

This is not a v0.1 feature. If it is proposed later:

- Build the selection map with a tracer that records every test, not only the
  first test to hit a line.
- Use the full suite as the oracle.
- Invert the measure: count **false passes**, not only skipped tests.
- Require an explicit "selected N of M; full suite not run" status.
- Treat a false pass as a release blocker.

### Reliability

- Repeat each run at least 20 times on the same input.
- Inject crashed tools, hung tools, invalid JSON, and missing executables.
- Verify that every abnormal path returns `error`, never `pass`.
- Test on Windows and Linux.
- Test paths with spaces and Unicode.

### Cache correctness

When caching is introduced:

- Invalidate on file content, tool version, config, environment, and dependency
  changes.
- Run paired cached/uncached comparisons.
- Count stale results, not only cache hits.

## Conditional targets

These are initial hypotheses. They must be revised after the first measurement.

| Area | Conditional target | Condition |
|---|---|---|
| Parity | 100% of actionable findings match the baseline | On the fixture and real-repo corpus |
| False passes | 0 | On the mutation corpus and full-suite oracle |
| Diagnostic tokens | ≥50% reduction on failure-heavy pytest cases | Same failure, same model tokenizer |
| Overall tokens | ≥20% reduction on mixed failures | Aggregate across the corpus |
| Cold latency | p95 ≤2 s for Tier 0–1 on small/medium fixtures | No warm session; local SSD |
| Warm latency | p95 ≤500 ms for unchanged tiers | After a warm session is introduced |
| Full check latency | p95 ≤5 s on a medium fixture | Tier 0–2, full tests |
| Repair efficiency | ≥30% fewer iterations or tokens, or equal cost with better evidence | Controlled agent loop vs raw warm chain |
| Flake rate | No new flaky results across 20 repeats | Same input and environment |
| Tool failure handling | 100% `error` status for crash/timeout/missing tool | Fault-injection tests |
| Adoption | Users replace the raw chain in the agent loop | Study or opt-in report |

A target is not a release gate until it has a measurement protocol.

## Kill criteria

Stop, narrow, or redesign if any of these hold:

- Parity cannot be demonstrated on the corpus.
- Any false pass appears in the mutation or full-suite oracle.
- No measurable token or iteration improvement over the raw warm chain.
- Agent harnesses consistently bypass the tool in favor of native hooks.
- The latency on a medium repository is worse than the raw warm chain.
- Executing untrusted code causes a security incident that the local-only
  warning did not reasonably mitigate.
- The product requires users to rewrite their tool configuration or tests.

## Public benchmark caveats

Public coding benchmarks are useful for directional comparison but not for
product proof:

- SWE-bench Verified is near saturation and has contamination concerns; OpenAI
  stopped evaluating it in 2026 for that reason.
- HumanEval-style benchmarks are saturated and do not measure verification-loop
  efficiency.
- Public benchmarks rarely measure token cost, false passes, or repair
  iterations.
- A custom, reproducible benchmark with mutation faults and a controlled agent
  loop is the primary evidence.

## Reporting template

Every evaluation report should include:

1. Commit and version under test.
2. Baseline configuration.
3. Repository, commit, and size.
4. Python and tool versions.
5. Hardware and OS.
6. Workload and fault classes.
7. Raw results, including failures and abandoned runs.
8. p50/p95 and confidence intervals where applicable.
9. Threats to validity.
10. Interpretation: what the result does and does not prove.

## Current status

No measurements have been run. All targets are hypotheses. The next evaluation
belongs to a later spec; `001-product-discovery` only defines the plan.

## References

- Mypy daemon: <https://mypy.readthedocs.io/en/latest/mypy_daemon.html>
- Test-impact-analysis false negatives: <https://github.com/breadMSA/pytest-tia>
- pytest-testmon limitations: <https://pypi.org/project/pytest-testmon/>
- Compiler-feedback repair research: <https://arxiv.org/pdf/2311.09868v5.pdf>
- Context rot: <https://redis.io/blog/context-rot>
- DORA 2025: <https://dora.dev/dora-report-2025>
- SWE-bench Verified caveats: <https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/>
- Epoch SWE-bench analysis: <https://epoch.ai/benchmarks/swe-bench-verified>
- SARIF overview: <https://www.sonarsource.com/resources/library/sarif/>
- OWASP workload sandboxing: <https://github.com/OWASP/AISVS/blob/main/1.0/research/chapters/C04-Infrastructure/C04-01-Workload-Sandboxing-Validation.md>
