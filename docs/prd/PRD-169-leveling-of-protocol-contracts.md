# PRD-169: Protocol Contract Alignment

## Summary

The protocol contracts had identical section headings but divergent bodies. This PRD unifies `AGENTS.md`, `docs/PRD-STANDARD.md`, `docs/AGENT-WORKFLOW.md`, `docs/PLATFORM-ADAPTERS.md`, the three Cursor rules, and the three slash commands, adopting the most complete existing wording for each area. The two payment sections that lived in procedural documents were moved to `CLAUDE.md`, where product facts have an owner, and `/reset-local` and `/sync-skills` become manual-invocation commands.

## Demand type

Governance review. No Python-code, schema, or UI change.

## Current problem

- `AGENTS.md` had 14 sections with identical headings but different bodies. The source-of-truth table did not state who references each owner, so nothing prevented a rule from being repeated in two files.
- `docs/PRD-STANDARD.md` described a **different PRD template**. This project's standard did not break down `Visual validation` or separate read and write checks under `ORM validation`, and it did not say what to do with an inapplicable section.
- `docs/AGENT-WORKFLOW.md` had 201 lines versus 282 in the most complete document in the same area, without the rendering-audit checklist or the table of inputs, outputs, and criteria by stage.
- Section 11 of `docs/AGENT-WORKFLOW.md` and section 6 of `docs/PLATFORM-ADAPTERS.md` addressed payments. Gateway procedures are not agent protocol; they are product facts, and keeping them there created two owners for the same subject.
- `.claude/commands/reset-local.md` and `sync-skills.md` **did not have** `disable-model-invocation`. The first destroys the local database: without the key, an agent could initiate the destructive cycle on its own.
- `/validar-tela` did not require a rendering audit, even though the workflow makes it mandatory.

## Goal

Each protocol contract has one wording, varying only by project name, application name, and skill prefix. Payments have a single owner. What the contract says about command guards is true in the file.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`
- `docs/PRD-STANDARD.md`, `docs/AGENT-WORKFLOW.md`, `docs/PLATFORM-ADAPTERS.md`
- `.cursor/rules/protocol.mdc`, `.cursor/rules/django.mdc`, `.cursor/rules/ui.mdc`
- `.claude/commands/reset-local.md`, `.claude/commands/sync-skills.md`, `.claude/commands/validar-tela.md`

### Adjacent files consulted

- `.claude/settings.json`, `.claude/launch.json`, `.mcp.json`, `.codex/config.toml`, `.cursor/mcp.json`
- `scripts/validate_skill_frontmatter.py`, `scripts/build_prd_index.py`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`
- `docs/prd/PRD-168-duplicate-prd-number-guard-and-settings-hygiene.md`

### Internet / official documentation

- Claude Code slash-command frontmatter and `disable-model-invocation`: https://docs.claude.com/en/docs/claude-code/slash-commands

### Context7 / MCPs / tools verified

- Context7 was not consulted: the change is documentary and does not involve a library API.

### Limitations found

- The link checker used during validation treats the generic `` `SKILL.md` `` mention in section 14 as a path and reports a false positive. The result was checked manually, and this PRD introduced no broken link.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: the "best of each area" table was presented with the audit.
- User approval: ratified, and Stage 2 authorized with "pode dar andamento" ("you may proceed").
- Date: 2026-07-26.

## Execution prompt

### Persona

Person responsible for repository documentation governance.

### Action

Unify the nine protocol contracts, move payment content to `CLAUDE.md`, and correct the slash-command invocation guard.

### Context

Disposable MVP. A contract describes what exists; when it diverges from the file, the file prevails and the contract is corrected in the same change.

### Constraints

- vary only the project name, application name, and skill prefix;
- do not introduce a rule the repository does not yet satisfy;
- **no payment rule may be lost** during the move;
- the absolute prohibition on comments and docstrings **is not** introduced now.

### Acceptance criteria

- [x] `AGENTS.md` has one variant and a sources table with a "Who references it" column;
- [x] `docs/PRD-STANDARD.md` has one variant and the complete template;
- [x] `docs/AGENT-WORKFLOW.md` has one variant, including the input/output/criterion table and rendering-audit checklist;
- [x] `docs/PLATFORM-ADAPTERS.md` has one variant;
- [x] each of the three `.cursor/rules/*.mdc` files has one variant;
- [x] `sync-skills.md` and `validar-tela.md` each have one variant;
- [x] `reset-local.md` has an identical section structure, varying only in the seed sequence;
- [x] `/reset-local` and `/sync-skills` have `disable-model-invocation: true`;
- [x] every payment rule from the two removed sections is present in section 9 of `CLAUDE.md`;
- [x] zero project-name leakage between repositories;
- [x] `check`, `makemigrations --check --dry-run`, `build_prd_index.py --check`, and `validate_skill_frontmatter.py` pass.

### Expected evidence

Variant count by file after normalization; line-by-line verification of the moved payment content; output from the four gates.

### Output format

Documentation diff and the PRD updated with evidence.

## Scope

- `AGENTS.md`
- `docs/PRD-STANDARD.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PLATFORM-ADAPTERS.md`
- `.cursor/rules/protocol.mdc`, `django.mdc`, `ui.mdc`
- `.claude/commands/reset-local.md`, `sync-skills.md`, `validar-tela.md`
- section 9 of `CLAUDE.md`, only to receive the moved payment content

## Out of scope

- The rest of `CLAUDE.md`, `README.md`, `docs/OPERACAO-BANCO-SEEDS.md`, `docs/DEPLOY-RENDER-SUPABASE.md`, and `docs/UI-SCREEN-CONTRACT.md`.
- `requirements.txt`, `.gitignore`, and the environment-key set.
- Removing comments and docstrings.
- The bodies of the six skills.
- `docs/archive/static-documentation-legacy/` and the three wizard guides.

## Impacted files

| File | Change |
|---|---|
| `AGENTS.md` | 187 → 226 lines; sources table with owner and referrers |
| `docs/PRD-STANDARD.md` | 105 → 164 lines; complete template; rule for inapplicable sections |
| `docs/AGENT-WORKFLOW.md` | 201 → 333 lines; stages table, rendering checklist, section 11 Payments removed |
| `docs/PLATFORM-ADAPTERS.md` | 88 → 125 lines; platform matrix, section 6 Payments removed |
| `.cursor/rules/protocol.mdc` | 16 lines; no material change |
| `.cursor/rules/django.mdc` | 12 → 13 lines |
| `.cursor/rules/ui.mdc` | 12 → 13 lines |
| `.claude/commands/reset-local.md` | 105 → 126 lines; adds `disable-model-invocation`, port guard, file guard, and `check` |
| `.claude/commands/sync-skills.md` | 59 → 79 lines; adds `disable-model-invocation` and the `openai.yaml` check |
| `.claude/commands/validar-tela.md` | 55 → 65 lines; rendering and state audit |
| `CLAUDE.md` | section 9 receives four payment rules from procedural documents |

## Risks and edge cases

- Moving payments to `CLAUDE.md` could lose the most important rule in the set—"do not simulate payment by inference or declare confirmation without gateway and ORM evidence." Verification was performed item by item and is recorded in the Evidence section.
- `disable-model-invocation` on `/reset-local` and `/sync-skills` prevents the model from invoking them on its own. That is precisely the goal: the first is destructive, and the second is an audit requested by the operator.
- The new port guard terminates a process. It does so only when the command line matches `manage.py runserver localhost:8000`; for any other PID, it aborts and reports it.
- `reset-local.md` still has three variants because of the sequence of 21 seeds. This is product data owned by `docs/OPERACAO-BANCO-SEEDS.md`.

## Rules and constraints

- Section 2 of `AGENTS.md`: one owner per subject; when a contract diverges from the file, the file prevails.
- Section 12 of `AGENTS.md`: material debt outside scope becomes a follow-up, not a silent implementation.

## Plan

- [x] Context and research
- [x] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

None. The change is documentary and has no testable behavior: content parity and link integrity are what can be verified, using the command recorded in the Evidence section.

`system/tests/test_seed_docs_contract.py` already reads `docs/OPERACAO-BANCO-SEEDS.md`, which is outside the scope of this PRD, and ran as part of the suite.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test
Ran 769 tests in 292.150s
OK
exit=0
```

The suite ran in this session to confirm the absence of regressions; no new test was added.

## Visual validation

### Design approval

Not applicable: no visual change.

### Routes and states

Not applicable: no route changed.

### Desktop

Not applicable.

### Mobile

Not applicable.

### Console and terminal

`manage.py check` produced no warning.

### Screenshot / snapshot

Not applicable: the change is documentary.

## ORM validation

### Read-only checks

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

### Mutating checks and authorization

No write was executed.

## Quality validation

```text
python manage.py check                        -> no issues, exit=0
python scripts/build_prd_index.py --check     -> Indice em dia (Index is up to date), exit=0
python scripts/validate_skill_frontmatter.py  -> 18 arquivos validados (18 files validated), exit=0
python -m pip check                           -> No broken requirements, exit=0
```

## Evidence

Variants by file after normalizing project name, application name, and skill prefix across the three repositories in the same area:

```text
AGENTS.md                          variants=1  lines=226/226/226
docs/PRD-STANDARD.md               variants=1  lines=164/164/164
docs/AGENT-WORKFLOW.md             variants=1  lines=333/333/333
docs/PLATFORM-ADAPTERS.md          variants=1  lines=125/125/125
.claude/commands/sync-skills.md    variants=1  lines=79/79/79
.claude/commands/validar-tela.md   variants=1  lines=65/65/65
.cursor/rules/protocol.mdc         variants=1  lines=16/16/16
.cursor/rules/django.mdc           variants=1  lines=13/13/13
.cursor/rules/ui.mdc               variants=1  lines=13/13/13
.claude/commands/reset-local.md    variants=3  lines=111/126/97
```

Verification of the payment content moved to section 9 of `CLAUDE.md`:

| Source rule | Destination |
|---|---|
| read the complete flow and Asaas/Stripe documents | already covered by the last line of section 9, which points to the guide and PRD-058 |
| verify settings and environment without exposing secrets | already covered by section 10 of `AGENTS.md` |
| separate redirect, server-to-server webhook, and database confirmation | new line in section 9 |
| local Asaas requires a valid public HTTPS URL | already existed in section 9 |
| local Stripe may require the Stripe CLI and a temporary secret | new line in section 9 |
| do not simulate payment by inference or declare confirmation without gateway and ORM evidence | new line in section 9, in bold |
| an external flow may require Chrome, a tunnel, or the gateway dashboard | new line in section 9 |

No rule was lost: three already had coverage, and four became explicit in section 9.

Slash-command frontmatter:

```text
reset-local    disable-model-invocation: true
sync-skills    disable-model-invocation: true
validar-tela   argument-hint: "<route>"
```

## Implemented

- unified `AGENTS.md`, with an owner-and-referrers table;
- `docs/PRD-STANDARD.md` with the complete template and the rule for inapplicable sections;
- unified `docs/AGENT-WORKFLOW.md`, with the stages table and rendering-audit checklist;
- unified `docs/PLATFORM-ADAPTERS.md`;
- payments with a single owner: the two procedural sections were removed and their content consolidated into section 9 of `CLAUDE.md`;
- the three Cursor rules unified;
- `/reset-local` and `/sync-skills` restricted to manual invocation—the highest-impact correction in this PRD, because the destructive cycle had been invocable by the model;
- `/validar-tela` now requires states and a rendering audit.

## Cleanup findings

- `system/tests/test_class_catalog.py` has 0 lines: empty test file.
- `docs/archive/static-documentation-legacy/` contains 12 architecture documents superseded by the current contracts.
- `docs/prd/AUDIT-2026-06-30-master-findings.md` is not a numbered PRD and forces the generator to retain a named exception in `KNOWN_EXCEPTIONS`.
- `docs/wizard-step-plan-*.md`: three standalone guides in the root of `docs/`.
- `settings.py` uses single quotes while the other files in this area use double quotes.
- `.env` declares `DJANGO_DEBUG=1` instead of `True`.
- There is no `seed_test_data`: fictional data comes from four `seed_system_initial_test_*` seeds, breaking the pairing with `clear_test_data`.
- The local `stage` branch has no corresponding remote; the remote is `origin/stage-visual`.
- `.claude/settings.local.json` exactly duplicates `settings.json`.
- `.github/workflows/copilot-setup-steps.yml` exists only here.

## Follow-up PRDs

The next stages were already agreed with the operator: product contracts, infrastructure and environment, structure, and comment/docstring cleanup.

## Deviations from plan

Two.

The plan called for moving the absolute prohibition on comments and docstrings into section 10 at this stage. It was postponed until the cleanup stage: prohibiting them in Stage 2 and removing them in Stage 6 would leave the contract claiming for four stages that the code satisfied a rule it did not, which is exactly what section 2 prohibits.

`CLAUDE.md` was outside the declared scope and received four lines. The alternative was to remove the payment sections from the procedural documents and trust the next stage to restore the rules—which would temporarily lose the most important guard in the set. The edit was limited to section 9 and is recorded here.

## Pending

- The ten cleanup findings above, distributed across Stages 3, 4, 5, and 6. The branch without a remote and `settings.local.json` depend on an operator decision.

## Final status

Completed. Nine of the ten files have a single variant; the tenth has an identical structure and its own seed sequence because that is product data. Payments have one owner and no rule was lost. Four gates passed, and the suite had no regression.
