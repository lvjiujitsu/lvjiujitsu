# PRD-154: Disposable MVP Nature and Environment-Gate Removal

## Summary

Declare in the contract that LV Jiu Jitsu is a disposable MVP — local, HG, and production are simulations with no real data — and remove rules that treat production as sacred or block completion because of documentation divergence.

## Demand type

Governance review.

## Current problem

Three rules written for a product with real customer data are being applied to an MVP where nothing is real:

| Location | Passage | Effect |
|---|---|---|
| `CLAUDE.md:141` | “Production is not an experimentation environment” | Blocks the destructive cycle in a database recreated through migrations + seeds |
| `CLAUDE.md:97`, `AGENTS.md:145`, `AGENT-WORKFLOW.md:103` | “explicit environment confirmation” for every HG write | HG is disposable; the gate protects nothing and is enforced three times |
| `AGENTS.md:14` | “Divergence between sources blocks completion until resolved” | Hard stop for documentation inconsistency in a repository with seven governance documents that inevitably diverge |

The third rule is the most expensive: any divergence among `CLAUDE.md`, `AGENTS.md`, `AGENT-WORKFLOW.md`, and the six skills becomes a reason to block, and this audit found six active divergences.

LV also does not declare the disposable nature of its environment anywhere.

## Goal

After this PRD, an agent reading `CLAUDE.md` and `AGENTS.md` concludes that reset, migrate, seeds, and deployment are normal operations in any environment, and that documentation divergence is recorded at closure instead of blocking delivery.

## Context Ledger

### Files read in full

- `CLAUDE.md`, `AGENTS.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`
- `.claude/skills/lv-task-intake/SKILL.md`, `lv-prd`, `lv-django-delivery`, `lv-ui-delivery`, `lv-cleanup-audit`, `lv-prompt-builder`

### Adjacent files consulted

- `.claude/settings.json`, `.claude/settings.local.json` — `deny` and `ask` already empty.
- `.claude/launch.json` — port 8000.

### Internet / official documentation

- [Django — environment-specific settings](https://docs.djangoproject.com/en/5.2/topics/settings/) — environment separation is configuration, not an approval policy.

### Context7 / MCPs / tools verified

- Context7 unavailable while drafting. Limitation recorded; no invented reference.

### Limitations found

- `.env`, `.env.hg`, and `.env.prod` were not read.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: project-governance audit, 2026-07-22.
- User approval: explicit instruction to generate remediation PRDs per repository.
- Date: 2026-07-22

## Execution prompt

### Persona

LV Jiu Jitsu agent-governance maintainer.

### Action

Edit `CLAUDE.md`, `AGENTS.md`, and `docs/AGENT-WORKFLOW.md` to declare the MVP nature, replace the environment gate with an irreversibility gate, and downgrade the divergence-blocking rule.

### Context

Read all three files in full. All three occurrences of the HG gate must be handled in the same delivery.

### Constraints

- Technical guards in code remain: `SUPABASE_RESET_CONFIRM`, `DJANGO_ENVIRONMENT`, `DJANGO_DEBUG=False`. Remove the **documentation** permission gate, not the execution guard.
- Do not change skills in this PRD — that is PRD-155 and PRD-156.
- Smallest correct diff: replace the sentence, do not rewrite the section.
- The payment domain (Asaas, Stripe) is **not** covered by the relaxation. Sandbox charges remain external actions and require explicit authorization.

### Acceptance criteria

- [ ] `CLAUDE.md` gains a numbered `Project nature` section declaring: disposable MVP; local, HG, and production without real data; production is a simulation; every environment reconstructible through migrations + seeds.
- [ ] That section includes a revocation clause: when real student data or real production charges exist, the gates return. Without this clause, the criterion is not met.
- [ ] `CLAUDE.md:141` no longer contains “Produção não é ambiente de experimentação” (“Production is not an experimentation environment”). Verification: `grep -n "não é ambiente de experimentação" CLAUDE.md` returns empty.
- [ ] No project file contains “confirmação explícita de ambiente” (“explicit environment confirmation”). Verification: `grep -rn "confirmação explícita de ambiente" CLAUDE.md AGENTS.md docs/` returns empty.
- [ ] The gate table in `docs/AGENT-WORKFLOW.md` classifies by irreversibility: an irreversible action **outside** the repository (push, external deployment, payment-gateway call, real email delivery) requires authorization; everything the repository can reconstruct is normal operation.
- [ ] `migrate`, reset, and seeds in HG and production appear in the table as authorized without additional confirmation.
- [ ] `AGENTS.md:14` no longer blocks. Required text: divergence between sources is resolved using §1 precedence and recorded at closure; it does not interrupt delivery. Verification: `grep -n "bloqueia a conclusão" AGENTS.md` returns empty.
- [ ] `CLAUDE.md` declares the project’s canonical local port.
- [ ] `CLAUDE.md` declares what **does not** exist in LV, following the explicit environment-negation pattern.
- [ ] `.\.venv\Scripts\python.exe manage.py check` completes without errors after the edits.

### Expected evidence

- Diff of project files.
- Literal output from the project’s verification `grep` commands.
- `manage.py check` output.

### Output format

Diff + command outputs under `Evidence`.

## Scope

- `CLAUDE.md`: new section; corrections at `:97` and `:141`; rewritten §11; explicit-negation block.
- `AGENTS.md`: downgrade `:14`; reduce `:145` to a reference.
- `docs/AGENT-WORKFLOW.md`: `:103` and gate table.

## Out of scope

- Skills (PRD-155, PRD-156).
- General deduplication (PRD-157).
- Slash commands (PRD-158).
- Any relaxation of payment rules.

## Impacted files

| File | Nature |
|---|---|
| `CLAUDE.md` | edit + new section |
| `AGENTS.md` | edit |
| `docs/AGENT-WORKFLOW.md` | edit |

## Risks and edge cases

| Risk | Mitigation |
|---|---|
| Relaxation interpreted as permission to operate real charges | Explicit restriction: payment remains an external action requiring authorization. Acceptance criteria do not change any Asaas/Stripe rule. |
| Removing the divergence blocker hides a real inconsistency | Replacement rule requires **recording** divergence at closure; it stops blocking, not appearing. |
| Partial correction leaves one of three HG-gate copies | Criterion uses one `grep` across all three files, not per-file inspection. |
| Revocation clause forgotten | Dedicated acceptance criterion. |

## Rules and constraints

- English content; identifiers remain in English.
- Do not create a new file.

## Plan

- [ ] Context and research
- [ ] Implementation
- [ ] Validation
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

No automated test. Verify with `grep` and `manage.py check`.

### Execution authorization

- Status: authorized

### Execution evidence

Pending.

## Visual validation

Not applicable.

## ORM validation

Not applicable.

## Quality validation

The three acceptance-criteria `grep` commands plus `manage.py check`.

## Evidence

Pending.

## Implemented

Pending.

## Cleanup findings

Pending.

## Follow-up PRDs

- `PRD-155` — conditional authorization gate in skills.
- `PRD-156` — skill structure and PRD index.
- `PRD-157` — CLAUDE.md deduplication and hygiene.
- `PRD-158` — slash commands.

## Deviations from plan

Pending.

## Pending

Pending.

## Final status

Not started.
