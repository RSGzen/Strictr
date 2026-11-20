# Blueprint: Architecture and verification contract

- Spec: `specs/active/002-architecture-and-tech-stack/spec.md`
- Status: in-progress (all tasks verified locally; awaiting PR)
- Owner: Ge Rui Sen

## Approach

Write the result contract first, then the architecture around it, then the six
decision records. Update repository entry points and add docs tests that verify
the required sections and links.

No product code is added. The architecture is deliberately a modular monolith
with explicit `Tier` and `ToolRunner` seams, not a plugin framework or daemon
system.

## Modules and boundaries

| File | Responsibility | Change |
|---|---|---|
| `docs/architecture/system-overview.md` | Layers, boundaries, data flow, execution and trust model | Rewritten |
| `docs/architecture/verification-contract.md` | Versioned envelope, statuses, diagnostics, examples | New |
| `docs/adr/0002-verification-pipeline.md` | Architecture style and module boundaries | New |
| `docs/adr/0003-subprocess-tool-execution.md` | Subprocess and project environment | New |
| `docs/adr/0004-verification-contract-and-statuses.md` | JSON contract and fail-closed statuses | New |
| `docs/adr/0005-type-checker-selection.md` | mypy/pyright precedence | New |
| `docs/adr/0006-pytest-integration.md` | JUnit XML and full-suite policy | New |
| `docs/adr/0007-trust-boundary-and-timeouts.md` | Local trust, timeouts, process tree, redaction | New |
| `AGENTS.md` | Read order and architecture links | Modified |
| `README.md` | Documentation links | Modified |
| `CHANGELOG.md` | Architecture entry | Modified |
| `tests/unit/test_architecture_docs.py` | Docs contract tests | New |

## Contracts

The public contract is `docs/architecture/verification-contract.md` v1. The
architecture is its implementation plan. The ADRs define the reversible and
expensive-to-reverse decisions.

## Failure modes

| Failure | Behavior | Test |
|---|---|---|
| Architecture and contract disagree on status | Review and docs test | `test_contract_status_and_exit_model` |
| Missing ADR section | Docs test fails | `test_six_adrs_exist_with_required_sections` |
| ADR not linked from architecture | Docs test fails | `test_architecture_links_adrs` |
| Entry points do not link the contract | Docs test fails | `test_entry_points_link_architecture_docs` |
| Product code leaks into architecture spec | Review checklist | Manual review |
| Speculative daemon/cache/MCP design | Review checklist | Manual review |

## Security and trust boundaries

The architecture explicitly states local-only execution, no sandbox, no network
isolation, path confinement, timeouts, process-tree termination, and redaction.
The contract always includes `trust.sandboxed: false` for v0.1.

## Test plan

| AC | Layer | Test | Command | Status |
|---|---|---|---|---|
| AC-1 | docs | `test_system_overview_has_required_sections`, `test_module_boundaries_and_data_flow` | `uv run pytest tests/unit/test_architecture_docs.py -q` | pass |
| AC-2 | docs | `test_contract_has_required_sections`, `test_contract_status_and_exit_model` | same | pass |
| AC-3 | docs | `test_six_adrs_exist_with_required_sections`, `test_architecture_links_adrs` | same | pass |
| AC-4 | docs | `test_execution_policies_documented` | same | pass |
| AC-5 | docs | `test_entry_points_link_architecture_docs` | same | pass |

## Tasks

- [x] T-1: Write the system overview — verify: `uv run pytest tests/unit/test_architecture_docs.py -q` — AC: AC-1
- [x] T-2: Write the verification contract — verify: same — AC: AC-2
- [x] T-3: Write ADRs 0002–0007 — verify: same — AC: AC-3
- [x] T-4: Document execution, type-checker, pytest, and trust policies — verify: same — AC: AC-4
- [x] T-5: Update `AGENTS.md`, `README.md`, and `CHANGELOG.md` — verify: same — AC: AC-5
- [x] T-6: Add architecture docs tests — verify: `uv run pytest tests/unit/test_architecture_docs.py -q` — AC: AC-1..AC-5
- [x] T-7: Run the full gate and traceability — verify: `uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest -q` — AC: AC-1..AC-5

## Review checklist

- [ ] The contract is unambiguous about `pass`, `fail`, `partial`, and `error`.
- [ ] Exit codes match the contract everywhere.
- [ ] Tier requirements and skip reasons are consistent.
- [ ] Type-checker precedence is deterministic.
- [ ] Pytest full-suite and no-tests behavior are explicit.
- [ ] Trust is local-only and not described as a sandbox.
- [ ] No daemons, cache, MCP, SARIF, or test selection leaked into v0.1.
- [ ] The six ADRs are linked and do not contradict each other.
- [ ] Product docs remain the source of product scope; architecture does not
      re-litigate it.

## Rollback

Revert the architecture commit. No runtime behavior or data is affected.

## Open technical questions

Deferred to `003` or later: exact parser field mappings, CLI flag names,
timeout override syntax, and packaging. The architecture defines the boundaries;
the implementation spec defines the exact code.

## Retrospective

Fill after merge.
