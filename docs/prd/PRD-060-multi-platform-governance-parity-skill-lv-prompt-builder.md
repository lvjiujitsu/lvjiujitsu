# PRD-060: Multi-platform governance parity + the lv-prompt-builder skill

## Summary

Bring LV JIU JITSU's governance up to the multi-platform governance standard, without porting facts from another domain. Close two protocol divergences (the missing Classification section in `docs/AGENT-WORKFLOW.md` and the absence of the `lv-prompt-builder` skill) and record a deliberate decision about `docs/UX-SCREEN-FLOWS.md`. The `lv-prompt-builder` skill turns a raw problem into the best execution prompt in the LV standard and then stops, without implementing.

## Demand type

Agent governance review + documentation regeneration + agent tooling.

## Current problem

- LV's `docs/AGENT-WORKFLOW.md` had no Classification section; its `§2` was "Preflight". The multi-platform standard defines Classification in `§2`, and the prompt builder skill references `docs/AGENT-WORKFLOW.md §2` for the demand categories — the reference would be broken without that section.
- The `lv-prompt-builder` skill did not exist on any of the three platforms (`.claude`, `.agents`, `.cursor`). Turning a raw problem into execution required manually assembling the intake, classification, skill choice, reading, and gates, and the predictable authorizations turn into scattered pauses.
- LV has no `docs/UX-SCREEN-FLOWS.md`, creating a structural asymmetry that needed a recorded decision.

## Goal

1. Insert Classification into LV's `docs/AGENT-WORKFLOW.md`, aligning the protocol with the standard and enabling the skill's `§2` reference, without rewriting what was already correct.
2. Create `lv-prompt-builder` on the three platforms, semantically identical, in the style of the five existing `lv-*` skills.
3. Register the skill in the `docs/PLATFORM-ADAPTERS.md` table.
4. Decide, with a reason, about `docs/UX-SCREEN-FLOWS.md`.
5. Document the context, scope, evidence, and status in this PRD.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md` (the header and the sources of truth)
- `.cursor/rules/protocol.mdc`
- `.claude/skills/lv-prd/SKILL.md`, `.agents/skills/lv-prd/SKILL.md`, `.cursor/skills/lv-prd/SKILL.md`
- `.agents/skills/lv-prd/agents/openai.yaml` (and the other four `openai.yaml` files)
- `docs/prd/PRD-059-lean-governance-for-claude-codex-and-cursor.md`
- Protocol reference: `AGENTS.md`, `CLAUDE.md`, `docs/AGENT-WORKFLOW.md`, `docs/PLATFORM-ADAPTERS.md`, `docs/UX-SCREEN-FLOWS.md`, `docs/prd/PRD-110-graduation-counts-cancelled-class.md`

### Adjacent files consulted

- the inventory of `docs/prd/` (the next free number = 060)
- the inventory of LV's `docs/` (3 wizard docs + UI-SCREEN-CONTRACT)
- the skill inventory across the three platforms
- a `grep` for references to `AGENT-WORKFLOW` and to `§N` sections in the repository

### Internet / official documentation

- [Claude Code: skills](https://code.claude.com/docs/en/skills) — verified in this session.

The applicable conclusion: `name` is optional (defaulting to the directory name) and `description` is recommended; `description` + `when_to_use` are truncated at **1,536 characters** in the listing; `disable-model-invocation: true` prevents automatic triggering and reserves the skill for `/name`; project skills live in `.claude/skills/<name>/SKILL.md`. Critical: **malformed YAML frontmatter makes Claude Code load the skill's body with empty metadata** — with no `description` to match — which is why the `description` was quoted (it contains `: `).

### Context7 / MCPs / tools verified

- Context7 not applicable: the change is documentation/configuration, with no new runtime library. The source of truth is the tool itself, verified in the official documentation.
- PyYAML available through an auxiliary `.venv` (LV does not install PyYAML by default; the same arrangement recorded in PRD-059).
- PowerShell, Git, `rg`, and `sha256sum` available.

### Limitations found

- Runtime discovery of the skills in Claude and Cursor requires reloading the tools; the end-to-end execution of `/lv-prompt-builder` was not exercised in this session.
- The change is documentation/configuration: there is no testable application behavior, UI, or persistence.
- `.claude/settings.local.json` shows as modified by a pre-existing user change; it was preserved and is out of scope.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: a parity audit + creating the skill on the three platforms + a decision about UX-SCREEN-FLOWS + a PRD.
- User approval: an explicit implementation order, with authorizations granted to create/edit governance and skills, read-only ORM, and `manage.py check`.
- Date: 2026-06-26.

## Execution prompt

### Persona

Agent governance and Django architecture engineer, driven by evidence, scope, and the smallest correct change.

### Action

Close LV's protocol divergences relative to the multi-platform standard and deliver the `lv-prompt-builder` skill on the three platforms, preserving LV's domain facts.

### Context

LV is a Django 5.2 monolith on Windows/PowerShell, with governance in `AGENTS.md`, `CLAUDE.md`, and `docs/`, five `lv-*` skills synchronized across `.claude`/`.agents`/`.cursor`, Asaas/Stripe payments, and a public wizard. The reference is about protocol, not domain.

### Constraints

- Do not port facts from any domain that is not this product's.
- Preserve LV's domain facts.
- The smallest correct change: update only the divergent protocol; do not rewrite what is correct.
- Do not change functional code, the database, migrations, seeds, or payments.
- The three copies of each skill must be semantically identical.

### Acceptance criteria

- [x] `docs/AGENT-WORKFLOW.md` has `## 2. Classificação` (`## 2. Classification`) with the demand categories, and the following sections were renumbered up to `§13` with no loss of content.
- [x] `lv-prompt-builder` exists in `.claude/skills/`, `.agents/skills/`, and `.cursor/skills/` with valid YAML frontmatter.
- [x] The three copies of `SKILL.md` are byte-identical.
- [x] Codex receives `agents/openai.yaml`, following the pattern of the other five skills.
- [x] The skill uses `disable-model-invocation: true` and generates the execution prompt in the format of `docs/PRD-STANDARD.md`, stopping without implementing.
- [x] `docs/PLATFORM-ADAPTERS.md` registers the skill in the Claude/Codex/Cursor columns.
- [x] The decision about `docs/UX-SCREEN-FLOWS.md` is recorded with a reason.
- [x] No fact from another domain leaked into the touched files.

### Expected evidence

- Strict YAML parsing of the copies and the metadata.
- An identical SHA-256 across the three copies.
- A character count of the `description` below 1,536.
- A text search against leakage of another domain's terms.
- `git diff --check`.

### Output format

A short summary, real evidence, what was not validated, pending items, and status.

## Scope

- `.claude/skills/lv-prompt-builder/SKILL.md` (new)
- `.agents/skills/lv-prompt-builder/SKILL.md` (new)
- `.agents/skills/lv-prompt-builder/agents/openai.yaml` (new)
- `.cursor/skills/lv-prompt-builder/SKILL.md` (new)
- `docs/AGENT-WORKFLOW.md` (inserting Classification + renumbering)
- `docs/PLATFORM-ADAPTERS.md` (registering the skill)
- this PRD.

## Out of scope

- `docs/UX-SCREEN-FLOWS.md` (the decision not to create it — see Cleanup findings).
- Changing the five existing skills, `AGENTS.md`, or `CLAUDE.md`.
- Django code, templates, CSS, JavaScript, data, migrations, seeds, payments, deploy, or push.
- Running the `lv-prompt-builder` skill or any derived demand.

## Impacted files

The files listed in the scope.

## Risks and edge cases

- The skill auto-invoked in the wrong context: mitigated by `disable-model-invocation: true`.
- Malformed frontmatter loading the skill with no `description`: mitigated by quoting the `description` (it contains `: `); validated by PyYAML.
- Renumbering AGENT-WORKFLOW breaking references: checked through `grep` — no source references the document's numbered sections.
- A generated prompt that pre-approves a safety gate: the skill explicitly lists the gates that cannot be consolidated (mutating ORM, migrations, migrate, reset, seeds, a real Asaas/Stripe charge/webhook, push, deploy).
- Leakage of another domain's facts: mitigated by a text sweep; the only match was the false positive "categoria principal" (a Brazilian Portuguese adjective).

## Rules and constraints

- The smallest correct change; one source of truth per responsibility.
- The official source before inference.
- Short permanent content; procedure in the skill.
- Explicit failure or limitation.

## Plan

- [x] Context and research
- [ ] Test authored first, when applicable
- [x] Implementation
- [ ] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

Not applicable. The delivery is instructions/documentation and configuration, with no testable application behavior.

### Execution authorization

- Status: not requested.

### Execution evidence

Django tests not run.

## Visual validation

Not applicable. There is no template, CSS, JavaScript, or screen.

## ORM validation

Not applicable. There is no persistence.

## Quality validation

- Strict YAML parsing (PyYAML) of the 18 `SKILL.md` copies (6 skills × 3 platforms) and of the 6 `openai.yaml` files: all valid.
- The SHA-256 of the three copies of `lv-prompt-builder/SKILL.md`.
- A character count of the `description`.
- A sweep against leakage of another domain's terms.
- `git diff --check`.

## Evidence

- `git status --short`: new `.claude/`, `.agents/`, and `.cursor/skills/lv-prompt-builder/`; modified `docs/AGENT-WORKFLOW.md` and `docs/PLATFORM-ADAPTERS.md`. `.claude/settings.local.json` remains as the user's pre-existing change, untouched.
- An identical SHA-256 across the three copies of `SKILL.md`: `371a7aa9bb0928661bddd2155799c120a3bb830b58e12c5c06ab6fcce4b2224b`.
- Strict YAML parsing: 18 `SKILL.md` + 6 `openai.yaml` reported as valid; `lv-prompt-builder` with `name`, `description`, `argument-hint`, and `disable-model-invocation: true`.
- The skill's `description` at 354 characters, below the listing's 1,536 limit.
- `docs/AGENT-WORKFLOW.md` with sections `## 1` through `## 13`, with `## 2. Classificação` (`## 2. Classification`) as the new one; `grep` confirmed no source references the document's numbered sections.
- The anti-external-domain sweep over the touched files, using a term list built from vocabulary foreign to this product, returned no match.
- `git diff --check`: no whitespace error; only Windows LF→CRLF normalization warnings.
- The official source confirmed in this session: [Claude Code: skills](https://code.claude.com/docs/en/skills) — the 1,536-character cap, `disable-model-invocation`, the `.claude/skills/` location, and the malformed frontmatter behavior.

## Implemented

- `## 2. Classificação` (`## 2. Classification`) inserted into `docs/AGENT-WORKFLOW.md`, with the multi-platform standard's demand categories, and the Preflight→ORM→Cleanup sections renumbered to `§3`–`§13`, preserving the original text and LV's facts (including the Payments section).
- The `lv-prompt-builder` skill created on the three platforms, semantically identical, in the style of the five `lv-*` skills, with the Receive, Classify, Decide gates, Generate the prompt, Stop, and Restrict steps, in prompt-only mode (`disable-model-invocation: true`).
- The Codex `agents/openai.yaml` created for the skill, following the pattern of the others.
- The `description` quoted to guarantee valid YAML frontmatter despite the internal `: `.
- `docs/PLATFORM-ADAPTERS.md` registers the skill in the three columns, with a note about manual invocation.

## Cleanup findings

- The diff re-audited: six files in the approved scope, plus this PRD; the pre-existing `.claude/settings.local.json` preserved.
- Every reference in the skill (`AGENTS.md`, `CLAUDE.md`, the `docs/` contracts, and the `lv-*` skills) exists; no invented route, file, command, or source.
- **The decision about `docs/UX-SCREEN-FLOWS.md`: do not create it now.** Reason: LV already governs generic screen, state, role, and action-hierarchy patterns in `docs/UI-SCREEN-CONTRACT.md`, and the concrete flows live in the three `docs/wizard-step-plan-*.md` files and in the screen PRDs; creating a mirrored document would duplicate correct content and risk importing facts from a foreign domain. The `lv-prompt-builder` skill itself (and the `SKILL.md` provided) already omits `UX-SCREEN-FLOWS` from the contract list, reflecting that decision. Reopen it when there is a cross-cutting screen flow not covered by the current contracts.
- The reference prompt-builder exists only in `.claude`; LV closes the gap by delivering the skill on the three platforms at once.
- No dead code, hardcoding, duplication, stray placeholder, or divergent documentation in scope.

## Follow-up PRDs

None. The skill's multi-platform parity was delivered in this PRD; no material debt remains.

## Deviations from plan

- "Test authored first" and "Refactor" do not apply: the delivery is an instruction document and configuration, with no testable application behavior.
- The `description` had to be quoted (it was not in the literal `SKILL.md` provided) to satisfy the "valid frontmatter" criterion; the text was preserved in full.

## Pending

- Reload Claude Code, Codex, and Cursor for runtime discovery of the skill; the end-to-end execution of `/lv-prompt-builder` was not exercised in this session.

## Final status

**Completed with limitations**: the Classification in AGENT-WORKFLOW, the `lv-prompt-builder` skill on the three platforms, the adapter registration, the decision about UX-SCREEN-FLOWS, and this PRD were implemented and structurally validated; runtime activation of the skills depends on reloading the tools.
