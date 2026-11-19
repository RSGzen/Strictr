# ADR 0001: Python toolchain and repository foundation

- Status: accepted
- Date: 2026-11-19
- Decision makers: RSGzen

## Context

Strictr is a new Python verification tool that will be developed primarily with
an AI coding agent. The bootstrap needs a small, reproducible toolchain before
product code exists.

## Decision drivers

- Deterministic local and CI behavior on Windows and Linux.
- Fast feedback and a committed lockfile.
- Strict typing and formatting without a large dependency surface.
- A CLI that is easy to test and package.
- No runtime dependency for the v0.1 verification core.

## Considered options

### Package and environment management

1. **uv** — fast resolver, lockfile, dependency groups, Python version support.
2. pip + venv + requirements files — ubiquitous, but slower and more manual.
3. Poetry — capable, but heavier than needed.

### CLI framework

1. **argparse** — standard library, no runtime dependency.
2. Typer/Click — better ergonomics, but a runtime dependency before the CLI
   shape is known.

### Static quality

1. **ruff + mypy strict** — fast formatting/linting and strict typing.
2. ruff only — insufficient for typed contracts.
3. pyright — viable, but mypy is the reference implementation and simpler to
   run as a subprocess later.

### Test runner

1. **pytest** — fixtures, markers, plugin hooks; also the tool Strictr will
   invoke for tier 2.

## Decision

- Python **3.12+**; develop on 3.13.
- **uv** for environments, locking, and dependency groups.
- **src layout** with package `strictr`.
- **hatchling** as the build backend.
- **ruff** for formatting and linting.
- **mypy --strict** for `src` and `scripts`.
- **pytest** with strict markers for tests.
- **argparse** for the first CLI.
- External verification tools are invoked as subprocesses, not imported as
  libraries.
- The package has **no runtime third-party dependencies** in v0.1.

## Consequences

Good:

- Reproducible installs and fast CI.
- A small runtime footprint for a security-sensitive verifier.
- Strict typing forces explicit contracts.

Bad:

- uv must be installed by contributors.
- argparse requires more manual CLI wiring than Typer.
- mypy strict can be noisy on tests; tests are excluded from strict scope
  initially.

Follow-up:

- Revisit Typer if the CLI grows beyond simple subcommands.
- Add coverage reporting after the first product slice.
- Add packaging and publishing only when a release is planned.

## Confirmation

- CI runs `uv sync --locked`, ruff, mypy, and pytest.
- `pyproject.toml` and `uv.lock` are committed.
- No runtime dependencies appear in the project until an ADR justifies them.
