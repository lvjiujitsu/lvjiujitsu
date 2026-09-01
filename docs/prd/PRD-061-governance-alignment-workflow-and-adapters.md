# PRD-061: Governance alignment — workflow and adapters

## Summary

Bring into LV JIU JITSU the governance improvements not yet absorbed, without importing any foreign domain: the complete Django reading checklist in `docs/AGENT-WORKFLOW.md` and the Context7, browser priority ladder, and explicit skill synchronization blocks in `docs/PLATFORM-ADAPTERS.md`.

## Demand type

Governance review + documentation regeneration. No functional code change.

## Current problem

- LV's `docs/AGENT-WORKFLOW.md` is condensed: it summarizes the Django reading in a single line and does not explicitly include `signals`, `tasks`, and `management commands`, nor the anchor "a text search is for locating, not for replacing reading".
- LV's `docs/PLATFORM-ADAPTERS.md` lacks three necessary blocks:
  1. **Mandatory Context7** with the trigger list (library, framework, SDK, API, CLI, config);
  2. **A browser priority ladder** across four levels (internal → an authenticated session → Playwright MCP → a limitation report);
  3. **Skill synchronization** with explicit paths (`.claude/skills/...`, `.cursor/skills/...`) and verification by hash/content.
- LV uses a governance bootstrap but does not record which local file owns each governance rule, which makes future divergence easier.

## Goal

1. Expand `docs/AGENT-WORKFLOW.md` to the complete Django checklist and the reading anchor.
2. Add the Context7, browser ladder, and explicit synchronization blocks to `docs/PLATFORM-ADAPTERS.md`, keeping LV's skill names (`lv-*`).
3. Record in `CLAUDE.md` where the governance bootstrap lives, for future resynchronization.
4. Do not change `AGENTS.md` beyond what is needed to keep the references coherent.

## Context Ledger

### Files read in full

- `docs/AGENT-WORKFLOW.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/PRD-059-lean-governance-for-claude-codex-and-cursor.md`
- `CLAUDE.md`
- `AGENTS.md`

### Adjacent files consulted

### Internet / official documentation

- [Claude Code: skills](https://code.claude.com/docs/en/skills)
- [Cursor: Rules](https://cursor.com/docs/rules)
- [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Agent Skills specification](https://agentskills.io/specification)

### Context7 / MCPs / tools verified

- A documentation change; Context7 does not apply to governance content.
- PowerShell, Git, and `rg` available.
- The internal browser available, not applicable to documentation files.

### Limitations found

- There is no functional change that would justify a Django test or visual validation.
- Synchronizing the `lv-*` skills across Claude/Codex/Cursor requires reloading the tools after the edit.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: consolidate LV's documentation governance into its own contracts, without importing any external domain.
- User approval: an explicit request for complete PRDs for sequential implementation.
- Date: 2026-06-28.

## Execution prompt

### Persona

Agent governance engineer on a Django monolith.

### Action

Edit two of LV's governance documents and add a factual reference to `CLAUDE.md`, preserving LV's facts and skill names.

### Context

LV is a Django 5.2 monolith (MVT, `services/`, `selectors/`) operated on Windows/PowerShell, Render, and Supabase, with versioned common governance.

### Constraints

- Do not change functional code, templates, CSS, or JavaScript.
- Do not copy facts from any domain that is not this product's into LV.
- Keep LV's skill names (`lv-task-intake`, `lv-prd`, `lv-ui-delivery`, `lv-django-delivery`, `lv-cleanup-audit`, `lv-prompt-builder`).
- One source of truth per responsibility; short permanent content.

### Acceptance criteria

- [x] `docs/AGENT-WORKFLOW.md` explicitly lists models, forms, services, selectors, views, URLs, templates, CSS/JS, tests, settings, signals, tasks, and management commands in the reading checklist.
- [x] `docs/AGENT-WORKFLOW.md` includes the anchor "a text search is for locating, not for replacing reading".
- [x] `docs/PLATFORM-ADAPTERS.md` contains a Context7 block with the triggers.
- [x] `docs/PLATFORM-ADAPTERS.md` contains a four-level browser priority ladder.
- [x] `docs/PLATFORM-ADAPTERS.md` contains a synchronization block with the explicit paths of the three skill copies and verification by hash/content.
- [x] `CLAUDE.md` declares where this repository's governance bootstrap lives.
- [x] No reference to a foreign domain was introduced into LV.

### Expected evidence

- The diff of the two documents and of `CLAUDE.md`.
- A text search confirming the required terms.
- A search confirming the absence of foreign domain terms in the new sources.

### Output format

A short summary, evidence, limitations, and status.

## Scope

- `docs/AGENT-WORKFLOW.md`
- `docs/PLATFORM-ADAPTERS.md`
- `CLAUDE.md` (only §11)
- this PRD.

## Out of scope

- Django code, templates, CSS, JavaScript.
- The skills themselves (the content of the `SKILL.md` files) — skill parity is the already existing PRD-060.
- The database, migrations, seeds, deploy, payments.

## Impacted files

- `docs/AGENT-WORKFLOW.md`
- `docs/PLATFORM-ADAPTERS.md`
- `CLAUDE.md`
- this PRD.

## Risks and edge cases

- Copying text verbatim from outside this repository and dragging in foreign names or domain terms.
- Inflating the documents beyond the short-content principle.
- Divergence between the documented browser ladder and the tools actually available in LV.

## Rules and constraints

- The smallest correct change.
- Keep coherence with `AGENTS.md` and with PRD-059.
- Do not claim visual validation for a documentation change.

## Plan

- [ ] Context and research
- [ ] Expand `AGENT-WORKFLOW.md`
- [ ] Expand `PLATFORM-ADAPTERS.md`
- [ ] Declare in `CLAUDE.md` where this repository's governance bootstrap lives
- [ ] Validate the terms and the absence of an external domain
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

Not applicable.

### Execution authorization

- Status: not requested.

### Execution evidence

Django tests not run.

## Visual validation

Not applicable. No screen will be changed.

## ORM validation

Not applicable.

## Quality validation

- A text search for the required terms.
- A search for improper external domain terms.
- `git diff --check`.
- A full review of the diff.

## Evidence

- `rg -n "models, forms, services, selectors|Busca textual localiza|Context7 é obrigatório|Prioridade de validação visual|\\.claude/skills|bootstrap canônico" docs\AGENT-WORKFLOW.md docs\PLATFORM-ADAPTERS.md CLAUDE.md` confirmed the required literal terms. Their English meanings are "text search locates," "Context7 is mandatory," "visual-validation priority," and "canonical bootstrap."
  The exact Portuguese anchors in that reproducible command mean "text search locates," "Context7 is mandatory," "visual validation priority," and "canonical bootstrap," respectively.
- A case-insensitive search for foreign domain vocabulary in `docs/AGENT-WORKFLOW.md`, `docs/PLATFORM-ADAPTERS.md`, and `CLAUDE.md` returned only terms that already belonged to LV: `GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` and PRD-058.
- `git diff --check -- docs/AGENT-WORKFLOW.md docs/PLATFORM-ADAPTERS.md CLAUDE.md` reported no whitespace error; only LF/CRLF normalization warnings.

## Implemented

- `docs/AGENT-WORKFLOW.md` received the classification step, the text-search anchor, and an expanded Django checklist with `signals`, `tasks`, and `management commands`.
- `docs/PLATFORM-ADAPTERS.md` received the Context7 trigger block, the four-level visual validation priority, and the explicit skill synchronization across `.agents`, `.claude`, and `.cursor`.
- `CLAUDE.md` now declares where this repository's governance bootstrap lives.

## Cleanup findings

- No functional residue introduced.
- The LF/CRLF warnings remain a characteristic of the workspace on Windows.

## Follow-up PRDs

None foreseen.

## Deviations from plan

None so far.

## Pending

- Reload the tools to reflect the updated governance.

## Final status

**Completed with limitations** — the documentation change applied and validated through a text search/diff; reloading the tools is outside the scope of editing files.
