---
id: "002"
title: "Architecture and verification contract"
status: in-progress
owner: "Ge Rui Sen"
created: 2026-11-21
updated: 2026-11-21
branch: "docs/002-architecture-and-tech-stack"
---

# Architecture and verification contract

## Context

Spec `001` locked the product: agent-first, local-only v0.1, Tier 0–1 plus
compact pytest, conditional evaluation targets, and explicit non-goals.

Before writing `003-check-command`, the project needs an approved architecture
and a stable result contract. This spec defines the module boundaries, execution
model, statuses, exit codes, and the decisions that would be expensive to
reverse after implementation.

## Goals

- Define a modular monolith with explicit tier and tool adapters.
- Make the verification envelope and status model the public interface.
- Specify tool execution, type-checker selection, pytest integration, trust
  boundary, timeouts, and process termination.
- Record the six architecture decisions as ADRs.
- Update repository entry points so implementation can follow the documents.

## Non-goals

- No product CLI, tiers, parsers, or runtime behavior.
- No MCP server, SDK, pre-commit hook, or SARIF output.
- No daemons, persistent workers, caching, or test selection.
- No Docker or microVM isolation.
- No benchmark execution or measured performance claims.
- No additional languages.

## Scenarios

- An implementer reads the architecture and contract and can build
  `003-check-command` without inventing status semantics or module boundaries.
- A reviewer checks that every v0.1 decision traces to the vision, the contract,
  or an ADR.
- A future adapter (MCP, SARIF, sandbox) can be added without changing the core
  result contract.

## Acceptance criteria

- **AC-1:** `docs/architecture/system-overview.md` SHALL define the C4 context
  and components, module boundaries, import rules, data flow, tier model, status
  model, tool execution, type-checker selection, pytest integration, trust
  boundary, performance model, failure modes, testing, extension seams, and ADR
  index.
- **AC-2:** `docs/architecture/verification-contract.md` SHALL define the
  versioned envelope, status and exit model, scope ledger, diagnostic and tier
  objects, truncation, ordering, human/JSON behavior, versioning, trust metadata,
  and examples.
- **AC-3:** `docs/adr/0002` through `0007` SHALL exist with context, decision,
  consequences, and confirmation; each SHALL be linked from the architecture.
- **AC-4:** The architecture SHALL specify subprocess execution in the project
  environment, type-checker precedence, full-suite pytest via JUnit XML,
  timeouts, process-tree termination, Windows behavior, and the local-only trust
  boundary.
- **AC-5:** `AGENTS.md` and `README.md` SHALL link the architecture and contract,
  and `docs/architecture/system-overview.md` SHALL be consistent with the six
  ADRs.

## Constraints

- Python 3.12+ and Windows/Linux.
- No runtime third-party dependencies.
- The contract is the implementation contract for `003`; it must be
  unambiguous.
- The six ADRs are the only architecture decision records for this spec.
- Architecture documents contain no product code and no speculative
  implementation.

## Open questions

Resolved by this spec:

- Architecture style: modular monolith with ports/adapters lite.
- Tool execution: subprocess in the project environment.
- Result contract: custom JSON v1, SARIF later.
- Type checker: auto-detect with explicit override.
- Pytest: full suite via JUnit XML.
- Trust: local-only with explicit warning.

Deferred to later specs:

- Packaging and distribution details.
- Warm sessions, cache, and concurrency.
- MCP/SDK transport.
- Sandbox technology and network policy.
- Test selection.
- SARIF export.

## Revision log

| Date | Version | Change | Author |
|---|---|---|---|
| 2026-11-21 | 0.1 | Initial architecture and contract spec | Ge Rui Sen |
| 2026-11-21 | 0.2 | Architecture docs, contract, and six ADRs implemented; awaiting PR | Ge Rui Sen |
