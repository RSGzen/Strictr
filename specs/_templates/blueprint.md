# Blueprint: <Title>

- Spec: `specs/active/NNN-slug/spec.md`
- Status: draft
- Owner: <name>

## Approach

<Chosen design and why. Alternatives considered.>

## Modules and boundaries

| Module | Responsibility | Change |
|---|---|---|
| <module> | <what it owns> | <new/modified> |

## Contracts

- CLI/API: <shape>
- Data/JSON schema: <version and fields>
- Errors: <codes, exit codes, messages>

## Failure modes

| Failure | Behavior | Test |
|---|---|---|
| <case> | <response> | <test id> |

## Security and trust boundaries

<Untrusted input, execution isolation, secrets, timeouts.>

## Test plan

| AC | Layer | Test | Command | Status |
|---|---|---|---|---|
| AC-1 | acceptance | `...` | `...` | todo |

## Tasks

- [ ] T-1: <task> — verify: `<exact command>` — AC: <AC-n>
- [ ] T-2: <task> — verify: `<exact command>` — AC: <AC-n>

## Rollback

<How to revert safely.>

## Open technical questions

- [ ] <Question — owner — deadline.>

## Retrospective

<Fill after completion: what worked, what did not, one change.>
