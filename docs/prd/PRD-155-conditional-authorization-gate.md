# PRD-155: Conditional Authorization Gate — Align Skills with AGENTS.md

## Summary

Fix the contradiction in which skills request approval unconditionally while `AGENTS.md` instructs the agent to proceed when the prompt already authorizes the scope. The gate becomes conditional in every source, using the same wording.

## Demand type

Governance review.

## Current problem

Two active contradictions both demand approval that the protocol has already waived.

**1. Intake template always asks.** `.claude/skills/lv-task-intake/SKILL.md:24` ends the response block with `Posso implementar?` (“May I implement?”), without a condition. This conflicts with:

- `AGENTS.md:48` — “proceed to execution when the current request already authorizes the scope”;
- `docs/AGENT-WORKFLOW.md:80` — “Before a change **not yet authorized**.”

A few lines later, the skill itself says to treat an explicit order as authorization. The template contradicts the rule beside it.

**2. Unconditional UI gate.** `.claude/skills/lv-ui-delivery/SKILL.md:25` says “request approval” without a condition, and `CLAUDE.md:132` states “A visual change requires an approved proposal before code.” This conflicts with `AGENTS.md:57` — “explicit approval **when the current request does not authorize** implementation.”

Observed effect: the operator must authorize the same thing twice — once in the prompt, once in the confirmation question — for every UI request.

## Goal

After this PRD, one authorization-gate wording exists, it is conditional, and the four sources that mention it use exactly that wording or reference its owner.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`, `docs/AGENT-WORKFLOW.md`
- `.claude/skills/lv-task-intake/SKILL.md`
- `.claude/skills/lv-ui-delivery/SKILL.md`
- `.claude/skills/lv-prompt-builder/SKILL.md`

### Adjacent files consulted

- `.agents/skills/`, `.cursor/skills/` — mirrors of the six skills.
- `docs/PLATFORM-ADAPTERS.md` §7 — requirement to synchronize all three copies.

### Internet / official documentation

- [Anthropic — Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) — a skill describes procedure; authorization policy belongs to the project protocol.

### Context7 / MCPs / tools verified

- Context7 unavailable while drafting. Limitation recorded.

### Limitations found

- None.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: governance audit, 2026-07-22.
- User approval: explicit instruction to generate remediation PRDs.
- Date: 2026-07-22.
- Execution approval: explicit 2026-07-25 prompt authorized correcting contradictions covered by PRDs 154–158.

## Execution prompt

### Persona

LV Jiu Jitsu agent-governance maintainer.

### Action

Define canonical gate wording in `AGENTS.md` and align `CLAUDE.md:132`, `lv-task-intake:24`, and `lv-ui-delivery:25` with it.

### Context

Canonical wording to adopt, written once in `AGENTS.md`:

```text
Request approval only when the current request does not authorize the scope.
An explicit and unambiguous implementation order authorizes the described scope.
An exploratory or ambiguous request, or one asking for a proposal, retains the gate.
Material scope expansion requires new approval regardless of the original prompt.
```

### Constraints

- The UI gate does not disappear: hierarchy, wireframe, and states remain mandatory before code. Only **requesting approval** becomes conditional; the design proposal is still produced.
- Do not relax the gate for scope expansion or irreversible external action.
- Changing a skill requires synchronizing `.claude/`, `.agents/`, and `.cursor/`.

### Acceptance criteria

- [x] `AGENTS.md` contains the four-line canonical wording above in one identifiable place.
- [x] `.claude/skills/lv-task-intake/SKILL.md` makes `Posso implementar?` (“May I implement?”) conditional, explicitly instructing the agent to **omit** it when there is an unambiguous implementation order.
- [x] `.claude/skills/lv-ui-delivery/SKILL.md:25` no longer says “request approval” unconditionally and references the `AGENTS.md` gate.
- [x] `CLAUDE.md:132` no longer states that every visual change requires an approved proposal; it states that every visual change requires a **design proposal**, with approval following the `AGENTS.md` gate.
- [x] The phrase “pedir aprovação” (“request approval”) and variants occur unconditionally in zero files. Verification: `grep -rn "pedir aprovação\|exige proposta aprovada" CLAUDE.md AGENTS.md docs/ .claude/skills/` — every remaining occurrence must have a condition or `AGENTS.md` reference; full output pasted under `Evidence` with a justification per line.
- [x] `lv-prompt-builder` retains its own stop guard (“stop and ask ONE objective question”), which is desired and must not be removed.
- [x] All three copies of each changed skill are identical. Verification: empty `diff` for `.agents/` and `.cursor/`.
- [ ] One flow test: given a prompt explicitly ordering implementation of a UI change, the agent produces a design proposal and proceeds to code **without** asking. Record a summarized transcript as evidence.

### Expected evidence

- Diff of `AGENTS.md`, `CLAUDE.md`, and the two skills plus mirrors.
- Complete `grep` output with per-line justification.
- Synchronization `diff` output.
- Summarized flow-test transcript.

### Output format

Diff + command outputs under `Evidence`.

## Scope

- `AGENTS.md`: canonical wording.
- `CLAUDE.md:132`.
- `.claude/skills/lv-task-intake/SKILL.md` and `.claude/skills/lv-ui-delivery/SKILL.md`, plus mirrors.

## Out of scope

- Restructuring skills into `When to trigger / Steps / Output / Stop when` (PRD-156).
- Environment gates (PRD-154).
- Payment rules.

## Impacted files

| File | Nature |
|---|---|
| `AGENTS.md` | canonical wording |
| `CLAUDE.md` | line 132 edit |
| `.claude/skills/lv-task-intake/SKILL.md` | conditional template |
| `.claude/skills/lv-ui-delivery/SKILL.md` | gate reference |
| `.agents/skills/*`, `.cursor/skills/*` | mirroring |

## Risks and edge cases

| Risk | Mitigation |
|---|---|
| Agent implements an ambiguous request | Wording conditions omission on an “explicit and unambiguous order”; exploratory requests retain the gate, stated in the rule itself. |
| Design proposal stops being produced | Explicit constraint: proposal remains mandatory; only approval becomes conditional. Acceptance criterion tests exactly this flow. |
| Scope expansion escapes | Fourth line of canonical wording covers it and is verified by the criterion. |
| Mirrors diverge | Empty `diff` is an acceptance criterion. |

## Rules and constraints

- English content; identifiers remain in English.
- Smallest correct diff.

## Plan

- [x] Context and research
- [x] Implementation
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

No Django test. The test is an agent-flow scenario described in the acceptance criterion.

### Execution authorization

- Status: authorized

### Execution evidence

- Current 2026-07-25 prompt recognized as an explicit order; execution began without a duplicate question.
- Search for `pedir aprovação` (`request approval`), `Posso implementar` (`May I implement`), and `exige proposta aprovada` (`requires an approved proposal`) confirmed only conditional uses or follow-up approval outside the initial gate.
- SHA-256 hashes for all three copies of each skill: identical.

## Visual validation

Not applicable — this is a protocol change, not a screen change. The flow test uses a UI request as its scenario.

## ORM validation

Not applicable.

## Quality validation

`grep` with per-line justification, mirror `diff`, and the flow test.

## Evidence

- `AGENTS.md` contains the canonical gate.
- `CLAUDE.md` requires a design proposal and references the gate.
- `lv-task-intake` includes `Posso implementar?` only when authorization is pending.
- `lv-ui-delivery` references the conditional gate.

## Implemented

Conditional gate implemented and synchronized across all three platforms.

## Cleanup findings

No residual unconditional occurrence in the initial gate. The follow-up approval rule in `AGENTS.md` remains because it handles material scope expansion.

## Follow-up PRDs

- `PRD-156` — skill structure.

## Deviations from plan

PRD-154 was not implemented: the current prompt authorized local hardening, not remote-environment relaxation.

## Pending

A specific interactive test with an actual UI change was not executed in this delivery because no visual change was in scope.

## Final status

**Completed with limitation**: contract, mirrors, and searches validated; interactive UI scenario not executed because there was no visual change in scope.
