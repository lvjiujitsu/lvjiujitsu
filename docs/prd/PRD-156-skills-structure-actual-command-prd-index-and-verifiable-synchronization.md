# PRD-156: Skills — Structure, Real Commands, PRD Index, and Verifiable Synchronization

## Summary

Standardize LV’s six skills with stop criteria and output blocks, replace generic commands with the actual interpreter, align `lv-prd` with the canonical-index rule, and make synchronization of all three copies part of the cleanup cycle.

## Demand type

Governance review.

## Current problem

**1. Audit without output or stopping condition.** `.claude/skills/lv-cleanup-audit/SKILL.md:8-15` says “Read the task’s complete diff” without naming a command, defining audit output, or specifying completion. It is impossible to know whether the skill ran.

**2. Generic command conflicts with explicit contract.** `.claude/skills/lv-django-delivery/SKILL.md:38` says “run `manage.py check`,” and `:20-23` says “run local tests” without a command. `CLAUDE.md:59-65` defines the real commands with `.\.venv\Scripts\python.exe`. An agent following the skill runs global Python.

**3. PRD numbering contradicts the standard.** `.claude/skills/lv-prd/SKILL.md:11` says “Find the next free number,” while `docs/PRD-STANDARD.md:7-8` forbids relying only on `ls` — which does not reveal reserved gaps or duplicates — and requires using and updating `docs/prd/README.md`.

**4. Nothing triggers synchronization of all three copies.** `docs/PLATFORM-ADAPTERS.md:66-76` requires `.claude/`, `.agents/`, and `.cursor/` to be identical and hash-compared. No lifecycle skill triggers this verification. Today all six are identical through manual discipline, not process.

**5. `lv-prompt-builder` missing from the skill table.** `docs/PRD-STANDARD.md:20-26` lists five skills; `AGENTS.md:178` recognizes six.

## Goal

After this PRD, running any LV skill produces predictably formatted output, ends on a declared condition, and uses commands that work when copied.

## Context Ledger

### Files read in full

- `.claude/skills/lv-task-intake/SKILL.md`, `lv-prd`, `lv-django-delivery`, `lv-ui-delivery`, `lv-cleanup-audit`, `lv-prompt-builder`
- `AGENTS.md`, `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`

### Adjacent files consulted

- `.agents/skills/`, `.cursor/skills/` — six copies each, verified identical.
- `docs/prd/README.md` — existing canonical index.
- `.claude/launch.json` — port 8000.

### Internet / official documentation

- [Anthropic — Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) — frontmatter and guidance that `description` should declare when to trigger.

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

LV Jiu Jitsu skill maintainer.

### Action

Restructure all six skills, correct commands, align `lv-prd` with the index, and add synchronization verification to `lv-cleanup-audit`.

### Context

Required structure for every LV `SKILL.md` after this PRD:

```md
---
name: <slug>
description: "<when to trigger + what it delivers>"
---

# <Title>

## When to trigger
## Steps
## Output
## Stop when
```

`Output` contains a literal block with that skill’s fixed fields.
`Stop when` contains completion conditions, including at least one failure condition.

Required `lv-cleanup-audit` output:

```text
Audited diff: <command executed>
Findings fixed in scope: <list or "none">
Follow-up created: <PRD-NNN or "none">
Skill copies synchronized: <yes | not applicable>
Status: clean | with follow-up
```

### Constraints

- A `description` containing `": "` must be quoted. Only `lv-prompt-builder` currently has this case and is already correct — preserve it.
- Every skill command uses `.\.venv\Scripts\python.exe manage.py <cmd>`.
- Canonical `localhost:8000` port is written literally wherever a skill instructs starting the server.
- The `lv-prompt-builder:15` stop guard (“stop and ask ONE objective question”) is the reference pattern — replicate the idea in others, do not remove it.
- Changing a skill requires synchronizing all three copies in the same delivery.

### Acceptance criteria

- [x] All six `SKILL.md` files contain `## When to trigger`, `## Steps`, `## Output`, `## Stop when`. Verification: `grep -c "^## Parar quando" .claude/skills/*/SKILL.md` returns 1 for each of six files.
- [x] Every `## Stop when` contains at least one failure condition (evidence not produced, tool unavailable, failing test).
- [x] `lv-cleanup-audit` contains the literal output block above and an explicit diff command in its steps.
- [x] Zero `manage.py` occurrences without the project interpreter. Verification: `grep -rn "manage.py" .claude/skills/ | grep -v "venv"` returns empty.
- [x] `lv-django-delivery` literally cites `.\.venv\Scripts\python.exe manage.py check` and `.\.venv\Scripts\python.exe manage.py test --verbosity 2`.
- [x] `lv-ui-delivery` literally cites `localhost:8000`.
- [x] `.claude/skills/lv-prd/SKILL.md:11` instructs consulting **and updating** `docs/prd/README.md` as the canonical index without depending on `ls`. Verification: `grep -n "próximo número livre" .claude/skills/lv-prd/SKILL.md` returns empty; the searched literal means "next free number."
- [x] `lv-cleanup-audit` adds a step that, when the diff touches `*/skills/*/SKILL.md`, compares all three copies and fails the audit if they diverge.
- [x] The `docs/PRD-STANDARD.md` skill table lists **all six**, with `lv-prompt-builder` marked as manual invocation.
- [x] For every changed skill, `diff .claude/skills/<n>/SKILL.md .agents/skills/<n>/SKILL.md` and the `.cursor/` equivalent return empty.
- [ ] All six skills still appear in the tool listing after reload — proof that frontmatter remains valid.

### Expected evidence

- Diff of six skills and mirrors.
- Structure and command `grep` output.
- Synchronization `diff` output.
- Recognized-skill listing.

### Output format

Diff + command outputs under `Evidence`.

## Scope

- Six `SKILL.md` files under `.claude/skills/` and mirrors under `.agents/` and `.cursor/`.
- `docs/PRD-STANDARD.md` — skill table.

## Out of scope

- Creating a new skill.
- Conditional authorization gate (PRD-155).
- Deduplicating rules across layers (PRD-157).
- Slash commands (PRD-158).

## Impacted files

| File | Nature |
|---|---|
| `.claude/skills/lv-task-intake/SKILL.md` | restructuring |
| `.claude/skills/lv-prd/SKILL.md` | restructuring + index rule |
| `.claude/skills/lv-django-delivery/SKILL.md` | restructuring + real commands |
| `.claude/skills/lv-ui-delivery/SKILL.md` | restructuring + real port |
| `.claude/skills/lv-cleanup-audit/SKILL.md` | restructuring + output + sync |
| `.claude/skills/lv-prompt-builder/SKILL.md` | restructuring |
| `.agents/skills/*`, `.cursor/skills/*` | mirroring |
| `docs/PRD-STANDARD.md` | skill table |

## Risks and edge cases

| Risk | Mitigation |
|---|---|
| Break YAML and make the skill disappear from listing | Criterion requires confirming all six after reload; quoting rule explicitly stated. |
| Synchronization check becomes noise in every diff | Step triggers only when diff touches `*/skills/*/SKILL.md`. |
| `## Stop when` becomes decorative | Criterion requires a failure condition, not only success. |
| Lose `lv-prompt-builder` guard during restructuring | Explicit constraint preserves it. |

## Rules and constraints

- English content; identifiers remain in English.
- A skill does not receive a new governance rule; rules go to the owner defined in PRD-157.

## Plan

- [x] Context and research
- [x] Implementation
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

No Django test. Verify through `grep`, `diff`, and skill listing.

### Execution authorization

- Status: authorized

### Execution evidence

- All six skills have exactly four operational sections.
- Search for `manage.py` without `.\.venv\Scripts\python.exe` across all three trees: empty.
- PyYAML parser validated all 18 `SKILL.md` files.
- SHA-256 hashes confirmed identical copies per skill.

## Visual validation

Not applicable.

## ORM validation

Not applicable.

## Quality validation

Structure and command `grep`, mirror `diff`, and skill listing.

## Evidence

- Six skills restructured with trigger, steps, output, and stopping conditions.
- Django commands use the real interpreter.
- `lv-prd` uses and updates the canonical index.
- `lv-cleanup-audit` runs an explicit diff and validates synchronization.
- `docs/PRD-STANDARD.md` includes manual `lv-prompt-builder`.

## Implemented

All 18 copies are synchronized with valid frontmatter. No generic Django command remains.

## Cleanup findings

PRD-155 was implemented in the same delivery to avoid an inconsistent intermediate synchronization.

## Follow-up PRDs

- `PRD-157` — deduplication and `CLAUDE.md` hygiene.
- `PRD-158` — slash commands.

## Deviations from plan

Tool reload/listing was unavailable inside the already-started session; strict YAML parsing of all 18 copies served as substitute validation.

## Pending

Reload/list skills in the tool after restarting the session.

## Final status

**Completed with limitation**: all file/command/hash criteria passed; tool reload was not observable in this session.
