# Strictr

Deterministic verification for LLM-generated Python code.

Strictr is a verification tool: it parses candidate Python code, runs static
checks, optionally runs tests, and returns compact machine-readable
diagnostics. The goal is a fast, deterministic gate for coding agents, not an
LLM judge.

## Status

Bootstrap. The verification CLI does not exist yet. This repository currently
contains the SDD governance, specification templates, traceability tooling, and
CI foundation.

The first product slice will be `strictr check <paths> [--json]`.

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
- `docs/` — constitution, architecture, ADRs, testing and setup guides
- `scripts/` — repository tooling

Start with `AGENTS.md`, then read `docs/constitution.md` and the active spec.

## Documentation

- [AGENTS.md](AGENTS.md) — how to work in this repository
- [Engineering constitution](docs/constitution.md)
- [System overview](docs/architecture/system-overview.md)
- [Testing guide](docs/testing.md)
- [Repository setup](docs/repo-setup.md)

The SDD master guide is kept in `internal-docs/` locally and is git-ignored.

## License

MIT. See [LICENSE](LICENSE).
