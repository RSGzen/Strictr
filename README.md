# Strictr

Deterministic verification for LLM-generated Python code.

Strictr is a verification tool: it parses candidate Python code, runs static
checks, optionally runs tests, and returns compact machine-readable
diagnostics. The goal is a fast, deterministic gate for coding agents, not an
LLM judge.

## Status

Architecture approved. Spec `003-check-command` is approved and in progress; the
contract schema and golden fixtures have landed, but the verification CLI does
not exist yet. This repository contains the SDD governance, product vision,
evaluation plan, architecture, verification contract, specification templates,
workflow roles, traceability tooling, and CI foundation.

The first product slice is `003-check-command`: `strictr check <paths>
[--json]`.

## Quick start

```powershell
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

## Repository map

- `src/strictr/` — package code
- `tests/` — unit and acceptance tests
- `specs/` — active and archived specifications
- `docs/product/` — product vision and evaluation plan
- `docs/sdd-workflow.md` — Planner, Task Worker, and Integrator roles
- `docs/` — constitution, architecture, ADRs, testing and setup guides
- `scripts/` — repository tooling

Start with `AGENTS.md`, then read the product vision, the constitution, and the
active spec.

## Documentation

- [AGENTS.md](AGENTS.md) — how to work in this repository
- [Product vision](docs/product/vision.md) — problem, users, scope, non-goals
- [Evaluation plan](docs/product/evaluation.md) — metrics, benchmarks, kill criteria
- [Engineering constitution](docs/constitution.md)
- [SDD workflow](docs/sdd-workflow.md) — Planner, Task Worker, and Integrator roles
- [System overview](docs/architecture/system-overview.md)
- [Verification contract](docs/architecture/verification-contract.md)
- [Architecture decisions](docs/adr/)
- [Testing guide](docs/testing.md)
- [Repository setup](docs/repo-setup.md)

The SDD master guide is kept in `internal-docs/` locally and is git-ignored.

## License

MIT. See [LICENSE](LICENSE).
