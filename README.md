# Strictr

Deterministic verification for LLM-generated Python code.

Strictr is a verification tool: it parses candidate Python code, runs static
checks, optionally runs tests, and returns compact machine-readable
diagnostics. The goal is a fast, deterministic gate for coding agents, not an
LLM judge.

## Status

Architecture approved. Spec `003-check-command` is implemented and archived: the
v0.1 check command runs Tier 0 syntax parsing, ruff, mypy or pyright, and the full
pytest suite. The contract schema, golden fixtures, CLI, and acceptance tests are
in place. Spec `004-verification-hardening` is implemented and archived; it adds
edge-case coverage without changing the v0.1 contract. There is no active spec.

## Usage

Run the check command from the project root:

```powershell
uv run strictr check src tests
uv run strictr check --json
uv run strictr check . --type-checker pyright --timeout 60
uv run python -m strictr check
uv run strictr --version
```

No paths means `.`. `--json` writes one compact JSON envelope to stdout.
`--type-checker` accepts `mypy`, `pyright`, or `none`. `--timeout SECONDS`
overrides every subprocess tier and version check for the run.

Strictr runs tools locally with the user's privileges. It is not a sandbox.

| Exit code | Meaning |
|---|---|
| 0 | `pass` |
| 1 | `fail` |
| 2 | `partial` or `error` |

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
- `docs/sdd-workflow.md` — single-agent phase workflow and context gates
- `docs/` — constitution, architecture, ADRs, testing and setup guides
- `scripts/` — repository tooling

Start with `AGENTS.md`, then read the product vision, the constitution, and the
specs under `specs/` (active work first, then the archive).

## Documentation

- [AGENTS.md](AGENTS.md) — how to work in this repository
- [Product vision](docs/product/vision.md) — problem, users, scope, non-goals
- [Evaluation plan](docs/product/evaluation.md) — metrics, benchmarks, kill criteria
- [Engineering constitution](docs/constitution.md)
- [SDD workflow](docs/sdd-workflow.md) — single-agent phases and context gates
- [System overview](docs/architecture/system-overview.md)
- [Verification contract](docs/architecture/verification-contract.md)
- [Architecture decisions](docs/adr/)
- [Testing guide](docs/testing.md)
- [Repository setup](docs/repo-setup.md)

The SDD master guide is kept in `internal-docs/` locally and is git-ignored.

## License

MIT. See [LICENSE](LICENSE).
