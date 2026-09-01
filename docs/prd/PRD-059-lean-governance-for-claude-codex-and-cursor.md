# PRD-059: Lean governance for Claude, Codex, and Cursor

## Summary

Apply short, verifiable governance to LV JIU JITSU, separating the universal protocol, the project's facts, database/payment operations, and the Claude, Codex, and Cursor adaptations.

## Demand type

Agent governance review + documentation regeneration.

## Current problem

- `AGENTS.md` and `CLAUDE.md` repeat procedures and history.
- The Claude commands and the Cursor rules duplicate the protocol.
- Tests are described as automatic execution, against the user's current policy.
- Asaas appears inside the universal protocol.
- `CLAUDE.md` declares Stripe as legacy, but the code, settings, seed, and PRD-058 confirm recurring Stripe is active.
- There are no equivalent, synchronized skills for the three tools.

## Goal

Consolidate a flow that:

1. gathers the full context and current research before the change;
2. confirms understanding in a minimal way;
3. uses SDD and test-first authoring;
4. runs tests only after authorization;
5. requires an approved proposal and the internal browser for UI;
6. keeps the special Asaas/Stripe, database, and seed operations in their own documents;
7. audits the scope at the end without expanding it automatically.

## Context Ledger

### Files read in full

- `AGENTS.md`
- `CLAUDE.md`
- `.claude/commands/*.md`
- `.claude/settings.json`
- every rule in `.cursor/rules/`
- `mcp.json`
- `lvjiujitsu/settings.py`
- `clear_migrations.py`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/GUIA-PREENCHIMENTO-CLAUDE-MD.md`
- `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md`
- `docs/prd/PRD-054-architectural-alignment-and-safe-reset.md`
- `docs/prd/PRD-058-asaas-stripe-webhook-validation-local-and-staging.md`
- `system/services/stripe_checkout.py`
- `system/views/stripe_views.py`
- `system/management/commands/seed_system_initial_subscription_plans_stripe.py`
- `system/services/asaas_checkout.py`
- `system/views/asaas_views.py`

### Adjacent files consulted

- the inventory of `system/management/commands/`
- `requirements.txt`
- the wizard guides in `docs/wizard-step-*.md`
- the reusable governance bootstrap.

### Internet / official documentation

- [Claude Code: project memory](https://code.claude.com/docs/en/memory)
- [Claude Code: skills](https://code.claude.com/docs/en/skills)
- [Claude Code Desktop](https://code.claude.com/docs/en/desktop)
- [Codex: AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
- [Codex: Agent Skills](https://developers.openai.com/codex/skills)
- [Codex: in-app browser](https://developers.openai.com/codex/app/browser)
- [Cursor: Rules](https://cursor.com/docs/rules)
- [Cursor: Agent Skills](https://cursor.com/docs/skills)
- [Agent Skills specification](https://agentskills.io/specification)
- [Django 5.2 testing](https://docs.djangoproject.com/en/5.2/topics/testing/overview/)
- [Django transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/)

### Context7 / MCPs / tools verified

- The Context7 research on Django and Playwright recorded.
- PowerShell 7.6.0, Python 3.12.10, Git, and `rg` available.
- The internal browser available at `http://localhost:8000/`, but not applicable to documentation/configuration files.

### Limitations found

- `.claude/settings.local.json` already contains a user change and will be preserved.
- `system/migrations/0001_initial.py` is already deleted in the worktree and will not be restored or changed.
- Runtime discovery of the skills in Claude and Cursor requires reloading the tools.
- Django tests were not authorized and are not necessary for this change.

## Required skills

- `skill-creator`

After the implementation:

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: apply the governance bootstrap to LV, preserving the facts and pre-existing changes.
- User approval: an explicit implementation request.
- Date: 2026-06-25.

## Execution prompt

### Persona

Governance, Django, and payment integrations engineer.

### Action

Reorganize LV's instructions and configurations, create equivalent skills, and remove the legacy duplication.

### Context

LV is a Django 5.2 monolith with the `system` app, Asaas and Stripe payments, Render/Supabase, a public wizard, and local operation on Windows/PowerShell.

### Constraints

- Do not change functional code.
- Do not touch the user's pre-existing changes.
- Do not run tests, mutating ORM operations, migrations, a reset, or seeds.
- Do not invent gateway state.
- Keep Asaas/Stripe out of the universal protocol.
- Do not claim visual validation for a documentation change.

### Acceptance criteria

- [x] `AGENTS.md` must contain only the common protocol and references.
- [x] `CLAUDE.md` must contain only LV's current facts.
- [x] Asaas and Stripe must be documented as active integrations.
- [x] Detailed procedures must be separated by responsibility.
- [x] Tests must be written before the code when applicable, but run only after authorization.
- [x] UI must require an approved proposal and validation in the internal browser.
- [x] Five equivalent skills must exist in Claude, Codex, and Cursor.
- [x] Redundant Cursor rules and replaced Claude commands must be removed.
- [x] The MCP configurations must use each tool's conventions.
- [x] Pre-existing changes must remain intact.

### Expected evidence

- Validation of the 15 skill copies.
- A hash comparison across the platforms.
- JSON/TOML parsing.
- A text search for the critical policies.
- `git diff --check`.

### Output format

A short summary, evidence, limitations, pending items, and status.

## Scope

- `AGENTS.md`
- `CLAUDE.md`
- `requirements-dev.txt`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `.agents/skills/`
- `.claude/skills/`
- `.claude/commands/`
- `.claude/settings.json`
- `.mcp.json`
- `.codex/config.toml`
- `.cursor/mcp.json`
- `.cursor/rules/`
- `.cursor/skills/`
- this PRD.

## Out of scope

- Django code, templates, CSS, and JavaScript.
- Data, migrations, and seeds.
- Real payment validation.
- Deploy, push, or configuration of external dashboards.

## Impacted files

The sources and adapters listed in the scope.

## Risks and edge cases

- Blocking tests only in the documentation while leaving broad permission in the configuration.
- Removing Asaas/Stripe details without keeping an operational reference.
- Copying facts from another domain into LV.
- Divergence between the skill copies.
- Overwriting the user's local changes.

## Rules and constraints

- The smallest correct change.
- One source of truth per responsibility.
- Short permanent content.
- Evidence before conclusion.

## Plan

- [x] Context and research
- [x] Rewrite the common sources
- [x] Create the operational documents
- [x] Create and synchronize the skills
- [x] Simplify the adapters
- [x] Validate the structure
- [x] Cleanup audit
- [x] Documentation

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

- The skills validator.
- Configuration parsing.
- A search for conflicts.
- A full review of the diff.

## Evidence

- `AGENTS.md`: 179 lines / 6,246 bytes.
- `CLAUDE.md`: 147 lines / 5,214 bytes.
- 15 skill copies validated through `quick_validate.py`: 15 `Skill is valid!` results.
- An identical SHA-256 across `.agents`, `.claude`, and `.cursor` for the five skills.
- `.claude/settings.json`, `.mcp.json`, and `.cursor/mcp.json` loaded as JSON.
- `.codex/config.toml` loaded as TOML.
- The new files read as UTF-8 and with no trailing whitespace.
- `git diff --check` with no blocking error.
- The search found no template placeholders in LV and no declaration of Stripe as legacy in the new sources.
- References to the wizard, payments, PRD-040, PRD-058, and the Asaas/Stripe services exist.
- `.claude/settings.local.json` keeps historical test allows, but the project's `ask` prevails because Claude evaluates rules in `deny` → `ask` → `allow` order.
- The pre-existing change in `.claude/settings.local.json` and the deletion of `system/migrations/0001_initial.py` stayed out of scope.

## Implemented

- `AGENTS.md` reduced to the common protocol.
- `CLAUDE.md` reduced to factual context, with Asaas and Stripe active.
- The workflow, PRD standard, adapters, and database/seed operations documents created.
- The visual policy aligned with the internal browser and with tests under authorization.
- Five skills created in Claude, Codex, and Cursor.
- The Codex `agents/openai.yaml` metadata created in UTF-8.
- Redundant Claude commands removed.
- The Cursor rules reduced to protocol, Django, and UI.
- The MCPs separated per tool convention.
- `requirements-dev.txt` created with PyYAML for skill validation.
- The legacy `CLAUDE.md` filling guide removed.

## Cleanup findings

- Duplication removed between the sources, commands, and rules.
- The ambiguous `mcp.json` location removed.
- No TODO, placeholder, secret, temporary file, or divergent copy remained in scope.
- The documentation conflict of legacy Stripe × active Stripe was fixed based on the code, settings, seed, and PRD-058.
- No additional material debt was found that would justify a new PRD.

## Follow-up PRDs

None.

## Deviations from plan

- The official skills generator initially wrote `openai.yaml` in the Windows console encoding; the five files were replaced with UTF-8 and revalidated.
- PyYAML was not installed in LV's `.venv`; the validator was run with a `.venv` that already contains the approved dependency.
- There was no forward test with a subagent because the task did not authorize delegation.

## Pending

- Reload Claude Code, Codex, and Cursor to rediscover the skills and configurations.
- Install `requirements-dev.txt` in LV only when the local environment needs to run the validator.

## Final status

**Completed with limitations**: the governance and the skills were implemented and structurally validated; the runtime activation in Claude and Cursor depends on a reload.
