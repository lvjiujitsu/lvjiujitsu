# PRD-158: Slash Commands for the Repeated Operational Lifecycle

## Summary

Populate the currently empty `.claude/commands/` directory with commands for tasks the operator repeats each session: complete local reset, visual validation, synchronization of all three skill copies, and repository parity audit.

## Demand type

New governance feature.

## Current problem

`.claude/commands/` exists and is empty. Recurring tasks are still typed manually or described in prose inside skills:

**1. Local destructive lifecycle.** Documented in `docs/OPERACAO-BANCO-SEEDS.md` as `clear_migrations.py` → `makemigrations` → `test` → `migrate` → 21 canonical seeds → `runserver`. This is the project’s longest and most repeated task, and the most vulnerable to interruption midway — leaving the database erased and the system offline.

**2. Visual validation.** Described in prose in `lv-ui-delivery`: real route, happy path, edge case, desktop, mobile, console, screenshot. Nothing guarantees every step occurs.

**3. Synchronization of all three skill copies.** `docs/PLATFORM-ADAPTERS.md:66-76` requires byte-for-byte comparison among `.claude/`, `.agents/`, and `.cursor/`. Today all six are identical through manual discipline. No command verifies this.

**4. Repository parity audit.** Performed manually on 2026-07-22 with an ad hoc rubric. It will recur.

## Goal

After this PRD, each of the four tasks is one command with preconditions verified before any destructive action and standardized output.

## Context Ledger

### Files read in full

- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/AGENT-WORKFLOW.md`
- `.claude/skills/lv-ui-delivery/SKILL.md`
- `.claude/launch.json`, `.claude/settings.json`, `.claude/settings.local.json`

### Adjacent files consulted

- `system/management/commands/` — actual seed inventory.
- `clear_migrations.py`.

### Internet / official documentation

- [Anthropic — Slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands) — `.claude/commands/` format, frontmatter, and arguments.

### Context7 / MCPs / tools verified

- Context7 unavailable while drafting. Limitation recorded.

### Limitations found

- The exact list of 21 canonical seeds must be read from `docs/OPERACAO-BANCO-SEEDS.md` during implementation, not copied from this PRD.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: governance audit, 2026-07-22.
- User approval: explicit instruction to generate remediation PRDs.
- Date: 2026-07-22.

## Execution prompt

### Persona

LV Jiu Jitsu agent-automation maintainer.

### Action

Create four files under `.claude/commands/`.

### Context

| File | Invocation | Purpose |
|---|---|---|
| `.claude/commands/reset-local.md` | `/reset-local` | Local destructive lifecycle through a running server |
| `.claude/commands/validar-tela.md` | `/validar-tela <route>` | Visual validation with mandatory evidence |
| `.claude/commands/sync-skills.md` | `/sync-skills` | Compare all three copies of each skill |
| `.claude/commands/auditar-paridade.md` | `/auditar-paridade` | Apply governance rubric A–H |

`/auditar-paridade` rubric: A role separation, B actionability, C frontmatter, D lifecycle coverage, E verifiability, F non-contradiction, G specificity, H maintainability.

### Constraints

- Every command uses `.\.venv\Scripts\python.exe`.
- `/reset-local` reads seed order from `docs/OPERACAO-BANCO-SEEDS.md` and does not maintain a second list. If they diverge, the command fails instead of choosing.
- `/reset-local` verifies seed-required variables **before** erasing the database.
- `/reset-local` refuses to run when `DJANGO_ENV_FILE` points to `.env.hg` or `.env.prod`.
- `/reset-local` stops on the first error and reports the failed step.
- `/validar-tela` does not declare success without a recorded screenshot.
- `/sync-skills` reports divergence and asks for the copy direction; it does not overwrite autonomously.
- `/auditar-paridade` uses at most two subagents, one per project.
- No command may trigger a payment-gateway action.

### Acceptance criteria

- [ ] All four files exist under `.claude/commands/` and appear in the tool listing after reload.
- [ ] Every file has frontmatter with `description`; `": "` is quoted when present.
- [ ] `/reset-local` aborts **without erasing** `db.sqlite3` when a seed-required variable is empty. Verification: execute under that condition and prove through `ls db.sqlite3` that the file remains.
- [ ] `/reset-local` rejects `DJANGO_ENV_FILE=.env.hg` without executing any step.
- [ ] Under normal conditions, `/reset-local` ends with the server responding at `http://localhost:8000/` with HTTP 200.
- [ ] When interrupted by an error, `/reset-local` names the failed step and does not execute later steps.
- [ ] The command reads seed order from `docs/OPERACAO-BANCO-SEEDS.md`; it contains no second copy of the list. Verification: inspect the command file.
- [ ] `/validar-tela` produces output marking each item individually and includes the screenshot path.
- [ ] `/sync-skills` compares six skills in all three folders and reports `idêntico` (“identical”) or `divergente` (“divergent”) for each, with every divergent path.
- [ ] `/auditar-paridade` produces a table with all eight criteria per project and a defect list with `file:line`.
- [ ] `docs/AGENT-WORKFLOW.md` gains a section listing all four commands and when to use each.
- [ ] `docs/PLATFORM-ADAPTERS.md` records that slash commands are Claude-only in this phase, with the equivalent manual procedure for Codex and Cursor.

### Expected evidence

- Contents of all four files.
- Successful `/reset-local` output ending in HTTP 200.
- `/reset-local` output for both rejection paths, proving `db.sqlite3` survived.
- `/sync-skills` output evaluating all six skills.
- Diff of `docs/AGENT-WORKFLOW.md` and `docs/PLATFORM-ADAPTERS.md`.

### Output format

Command contents + execution outputs under `Evidence`.

## Scope

- Four new files under `.claude/commands/`.
- Registration in `docs/AGENT-WORKFLOW.md` and `docs/PLATFORM-ADAPTERS.md`.

## Out of scope

- Anything outside this project — out of scope.
- Changing `clear_migrations.py` or any management command.
- Changing seed order.
- Automating sandbox payment flows.

## Impacted files

| File | Nature |
|---|---|
| `.claude/commands/reset-local.md` | creation |
| `.claude/commands/validar-tela.md` | creation |
| `.claude/commands/sync-skills.md` | creation |
| `.claude/commands/auditar-paridade.md` | creation |
| `docs/AGENT-WORKFLOW.md` | edit |
| `docs/PLATFORM-ADAPTERS.md` | edit |

## Risks and edge cases

| Risk | Mitigation |
|---|---|
| Erase database and fail during seed because a variable is missing | Verify precondition before `clear`, with a dedicated acceptance criterion proving file survival. |
| Trigger against HG or production | Reject by `DJANGO_ENV_FILE`, with a dedicated criterion. |
| Command seed list diverges from runbook | Command reads from runbook; a second copy is prohibited and verified by inspection. |
| Command touches billing | Explicit constraint; none of the four commands invokes a payment flow. |
| `/auditar-paridade` exhausts context | Limit of two subagents with reading restricted to contracts. |

## Rules and constraints

- English content; identifiers remain in English.
- Commands orchestrate existing contracts; they introduce no new rule.

## Plan

- [ ] Context and research
- [ ] Implementation
- [ ] Validation
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

No Django test. Verification is actual execution, including both rejection paths.

### Execution authorization

- Status: authorized

### Execution evidence

Pending.

## Visual validation

Validate `/validar-tela` against a real LV route, with desktop and mobile screenshots.

## ORM validation

Not applicable.

## Quality validation

Execute all four commands, including error paths.

## Evidence

Pending.

## Implemented

Pending.

## Cleanup findings

Pending.

## Follow-up PRDs

- None planned.

## Deviations from plan

Pending.

## Pending

Pending.

## Final status

Superseded by `PRD-161`, which created all four slash commands under `.claude/commands/`: `reset-local`, `sync-skills`, `validar-tela`, and `auditar-paridade`.

The PRD-154 dependency is no longer blocking. The original concern was that the command might carry environment gates PRD-154 intended to relax; the delivered `/reset-local` has no gate of its own — it only warns the operator in advance about guards already enforced by `clear_migrations.py`. If PRD-154 changes the remote-environment policy, the command does not need to change.
