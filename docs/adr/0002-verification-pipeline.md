# ADR 0002: Verification pipeline and module boundaries

- Status: accepted; tools imports refined by [ADR 0008](0008-tools-core-imports.md)
- Date: 2026-11-21
- Decision makers: Ge Rui Sen

## Context

Strictr must orchestrate several deterministic tools, return one result, and be
testable without invoking every real tool. It is Python-only in v0.1, but a CLI,
SDK, MCP adapter, SARIF exporter, cache, and sandbox are possible later.

The architecture must avoid two opposite failures: a flat script that cannot be
tested, and a speculative plugin framework for languages and tools that do not
exist yet.

## Decision drivers

- Parity with external tools.
- Testability of the pipeline and parsers.
- A stable result contract for agents.
- Windows and Linux support.
- Minimal runtime dependencies.
- Clear seams for later adapters without building them now.

## Considered options

1. **Flat procedural script.**
   Fast to start, but tool parsing and output become tangled; hard to test.
2. **Generic engine/plugin framework.**
   Flexible, but speculative for one language; adds indirection and registration
   complexity before there is a second implementation.
3. **Modular monolith with ports/adapters lite.**
   A pure core pipeline with explicit `Tier` and `ToolRunner` seams, concrete
   adapters, and explicit wiring.
4. **Microservices or separate worker processes.**
   Operationally heavy and unnecessary for a local CLI.

## Decision

Use a modular monolith with ports/adapters lite:

- `core`: models, pipeline, discovery, protocols, errors. No imports from
  `tiers`, `tools`, `output`, or `cli`.
- `tiers`: concrete Tier 0, ruff, type-checking, and pytest stages.
- `tools`: subprocess runner and pure parsers.
- `output`: human and JSON renderers.
- `cli`/`app`: argparse and explicit wiring.
- Two ports only: `Tier` and `ToolRunner`.
- No generic language engine, plugin registry, dependency-injection framework,
  event bus, or async runtime.

The pipeline is an ordered list of tiers with fail-fast in v0.1. The list-based
shape leaves room for a later `--all` mode and concurrent independent tools
without changing the result contract.

## Consequences

Good:

- Parsers and tiers can be unit-tested with canned outputs and fake runners.
- A future MCP/SDK adapter can call the same application service.
- A future language adds tiers without rewriting the core.
- No speculative abstraction tax.

Bad:

- Some wiring is explicit and repetitive.
- A future plugin ecosystem would require refactoring.
- The pipeline is not designed for distributed execution.

## Confirmation

- Architecture tests check module boundaries and required sections.
- The CLI, SDK, and MCP adapters, when added, call the same `CheckService`.
- A second language is the trigger for revisiting the abstraction, not a reason
  to build it now.
