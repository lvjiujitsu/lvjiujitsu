# PRD-170: Product Contract Alignment

## Summary

`CLAUDE.md`, `README.md`, `docs/OPERACAO-BANCO-SEEDS.md`, and `docs/DEPLOY-RENDER-SUPABASE.md` had incompatible structures. This PRD gives all four a core of identically titled sections, leaving only business-rule content unconstrained, and promotes the canonical order of the 21 seeds into a numbered table—the source that `/reset-local` and the runbook now reference instead of duplicating.

## Demand type

Governance review and documentation regeneration. No Python-code, schema, or UI change.

## Current problem

- `CLAUDE.md` had 11 sections with its own numbering, incompatible with the declared section core, and no section declaring what **does not** exist—leaving an agent free to propose a third gateway, a single `seed_test_data`, or a `requirements-dev.txt` file that never existed.
- `README.md` had 6 sections and 89 lines: no URL table, local cycle, license section, or validation commands.
- `docs/OPERACAO-BANCO-SEEDS.md` had 19 unnumbered sections organized by environment, with the order of the 21 seeds described in prose. Without a numbered table, `/reset-local` and the runbook retained copies of the list, which is exactly how one becomes outdated.
- `docs/DEPLOY-RENDER-SUPABASE.md` lacked "Expected logs" and "Post-deployment smoke test"—the two sections that explain how to tell whether deployment succeeded.
- None of the four described process termination during the destructive cycle, although `clear_migrations.py` terminates a Python process before deletion and waits up to 8 seconds for it to exit.

## Goal

The four product contracts have a core of sections with identical titles and order; product content is what differs. Seed ordering has one owner. Zero broken links.

## Context Ledger

### Files read in full

- `CLAUDE.md`, `README.md`
- `docs/OPERACAO-BANCO-SEEDS.md`, `docs/DEPLOY-RENDER-SUPABASE.md`
- `clear_migrations.py` — to describe process termination as implemented
- `system/tests/test_seed_docs_contract.py` — the test that validates this document

### Adjacent files consulted

- `lvjiujitsu/urls.py` and `system/urls.py` — actual routes, to avoid inventing surfaces
- `.claude/commands/reset-local.md`
- `system/management/commands/` — actual command inventory
- `docs/prd/PRD-169-leveling-of-protocol-contracts.md`

### Internet / official documentation

- Render, Build and Start Commands for a Python service: https://render.com/docs/deploy-django
- Supabase, Data API security: https://supabase.com/docs/guides/api/securing-your-api

### Context7 / MCPs / tools verified

- Context7 was not consulted: the change is documentary and does not involve a library API.

### Limitations found

- The link checker treats a negative mention (`no requirements-dev.txt`) and the generic phrase `` `SKILL.md` `` as paths and reports false positives. Both cases were checked manually.
- The CSS-token vocabulary cannot be unified by documentation alone: this project declares 49 tokens and **only three** (`--panel`, `--muted`, `--danger`) belong to the shared core vocabulary. Unification requires CSS refactoring and browser validation, which belongs in a separate PRD.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: a six-stage plan and the "best of each area" table.
- User approval: Stage 3 authorized with "pode seguir" ("you may proceed").
- Date: 2026-07-26.

## Execution prompt

### Persona

Person responsible for repository documentation governance.

### Action

Align the four product contracts around a shared section core and give seed ordering a single owner.

### Context

Disposable MVP. A contract describes what exists; when it diverges from the code, the code prevails and the contract is corrected in the same change.

### Constraints

- core with identical titles; product content remains unconstrained;
- no route, command, or variable may be invented—everything must be checked in the code;
- every cited seed name must exist: `test_seed_docs_contract.py` fails otherwise;
- do not change code in this PRD.

### Acceptance criteria

- [x] `CLAUDE.md` has a core of 11 declared sections, with sections 12+ free for business rules;
- [x] `CLAUDE.md` has the "What does not exist in this project" section;
- [x] `README.md` has the 10 declared sections, with a URL table;
- [x] `docs/DEPLOY-RENDER-SUPABASE.md` has the 10 declared sections;
- [x] `docs/OPERACAO-BANCO-SEEDS.md` has the 6 declared numbered sections;
- [x] the 21 seeds appear in a numbered table, with the variable required by each step;
- [x] `test_seed_docs_contract.py` passes after the rewrite;
- [x] the document describes process termination as the code performs it;
- [x] `check` and `build_prd_index.py --check` pass;
- [ ] `docs/UI-SCREEN-CONTRACT.md` aligned—**not delivered**; see `Pending`.

### Expected evidence

List of section titles by file; seed-contract test output; link-checker and gate output.

### Output format

Documentation diff and the PRD updated with evidence.

## Scope

- `CLAUDE.md`
- `README.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/DEPLOY-RENDER-SUPABASE.md`

## Out of scope

- `docs/UI-SCREEN-CONTRACT.md`—see `Pending` and `Follow-up PRDs`.
- Convergence of the CSS-token vocabulary.
- `requirements.txt`, `.gitignore`, and the environment-key set.
- Removal of comments and docstrings.
- `docs/archive/static-documentation-legacy/`, the three wizard guides, and `docs/prd/AUDIT-2026-06-30-master-findings.md`.

## Impacted files

| File | Change |
|---|---|
| `CLAUDE.md` | 165 → 295 lines; core of 11 sections, "What does not exist" section, path/responsibility table, section 12 Public registration, section 13 Payments, section 14 Graduation/plans/transfers |
| `README.md` | 89 → 137 lines; 10 sections, URL table by surface, local cycle, validation, license |
| `docs/OPERACAO-BANCO-SEEDS.md` | 269 → 349 lines; 6 numbered sections, 21 seeds in a table with required variable, documented guards and output guard |
| `docs/DEPLOY-RENDER-SUPABASE.md` | 155 → 211 lines; adds "Expected logs" and "Post-deployment smoke test" |

## Risks and edge cases

- `test_seed_docs_contract.py` fails if the document cites a nonexistent seed command. The table of 21 seeds was checked against `system/management/commands/`, and the test ran after the rewrite.
- The `seed_system_initial_test_*` reference with an asterisk does not match the test regex, so the four actual names were written out in full in the demonstration-seeds section.
- Describing process termination accurately may seem alarming: the command kills a Python process. The protection is real and documented—it never kills its own PID, its direct parent, or its ancestors, because the virtual environment's `python.exe` is a shim that appears as an ancestor.
- Numbering sections creates stable references (`§2.1`, `§3`) now used by `reset-local.md` and `CLAUDE.md`. Future renumbering would break those references.

## Rules and constraints

- Section 2 of `AGENTS.md`: one owner per subject; when a contract diverges from the code, the code prevails.
- Section 10 of `AGENTS.md`: secrets are never printed; when reading an environment, report key names only.
- Section 12 of `AGENTS.md`: material debt outside scope becomes a follow-up.

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

No new test. `system/tests/test_seed_docs_contract.py` already covers the contract between this document and the actual commands and served as the guardrail for the rewrite.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test system.tests.test_seed_docs_contract --verbosity 2
Ran 2 tests in 0.001s
OK
exit=0
```

```text
python manage.py check
System check identified no issues (0 silenced).
exit=0
```

The full suite of 769 cases ran in PRD-169, before this documentation change; no Python file was touched here.

## Visual validation

### Design approval

Not applicable: no visual change.

### Routes and states

Not applicable. The routes cited in `CLAUDE.md` and `README.md` were extracted from `system/urls.py`, not invented.

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

No query was required: there was no model, query, or migration change.

### Mutating checks and authorization

No write was executed.

## Quality validation

```text
python manage.py check                        -> no issues, exit=0
python scripts/build_prd_index.py --check     -> Indice em dia (Index is up to date), exit=0
```

Link checker after the change:

```text
CLAUDE.md: 24 references, 1 broken  -> false positive: "no requirements-dev.txt"
AGENTS.md: 13 references, 1 broken  -> false positive: generic `SKILL.md` phrase
README.md: 14 references, 0 broken
```

## Evidence

Section titles by file:

```text
CLAUDE.md — core, variants=1:
  1. Project nature | 2. Product | 3. Stack | 4. Layered architecture
  5. Local contracts | 6. Local commands | 7. Database and migrations | 8. Seeds
  9. Environments | 10. UI and validation | 11. References
  (12+ free: here, Public registration, Payments, and Graduation/plans/transfers)

README.md — identical across all three:
  Stack | Structure | Local setup | Complete local cycle | Server and URLs
  Validation | Environments | Governance | License

docs/DEPLOY-RENDER-SUPABASE.md — identical across all three:
  1. Services | 2. Exact commands | 3. Health check | 4. Environment Variables
  5. Supabase | 6. Auto-deploy | 7. Destructive remote reset | 8. Expected logs
  9. Post-deployment smoke test | 10. References

docs/OPERACAO-BANCO-SEEDS.md — identical across all three:
  1. Environments | 2. Command inventory | 3. Seeds—order and independence
  4. Local—SQLite | 5. Staging—Supabase | 6. Production—Supabase
```

Measured CSS-token vocabulary: 49 tokens here, of which **only 3** (`--panel`, `--muted`, `--danger`) belong to the shared core vocabulary. This evidence justifies treating convergence as a separate PRD.

## Implemented

- `CLAUDE.md` with an 11-section core, the "What does not exist in this project" section, and product rules in sections 12 through 14, including the payment guard received from PRD-169;
- `README.md` with 10 sections, a URL table by surface, and a note about English route aliases;
- `docs/DEPLOY-RENDER-SUPABASE.md` with "Expected logs," "Post-deployment smoke test," and a warning that a remote reset does not recreate gateway state;
- `docs/OPERACAO-BANCO-SEEDS.md` with 6 numbered sections and the 21 seeds in a table, including the variable required by each step—now the single source referenced by `/reset-local` instead of being duplicated;
- accurate description of process termination, including the 8-second wait and use of `taskkill` without `/T`.

## Cleanup findings

- `system/tests/test_class_catalog.py` has 0 lines: empty test file.
- `docs/archive/static-documentation-legacy/` contains 12 documents superseded by the current contracts.
- `docs/prd/AUDIT-2026-06-30-master-findings.md` is not a numbered PRD and forces the index generator to retain a named exception.
- `docs/wizard-step-plan-*.md`: three standalone guides in the root of `docs/`, now referenced by section 12 of `CLAUDE.md` but outside the taxonomy of the other contracts.
- `.env` declares `DJANGO_DEBUG=1` instead of `True`.
- `.claude/settings.local.json` exactly duplicates `settings.json`.
- There is no `seed_test_data`: the counterpart to `clear_test_data` consists of four `seed_system_initial_test_*` seeds.

## Follow-up PRDs

- Align `docs/UI-SCREEN-CONTRACT.md` around a normative core and product inventory.
- Converge the CSS-token vocabulary onto the shared core vocabulary, with visual validation of affected routes in both themes.
- Next agreed stages: infrastructure and environment, structure, and comment/docstring cleanup.

## Deviations from plan

One. `docs/UI-SCREEN-CONTRACT.md` was in the stage scope and **was not delivered**. The reason is recorded in `Pending`; it is not an information blocker but a decision not to half-restructure a 591-line contract whose normative and product material are interleaved.

## Pending

- **`docs/UI-SCREEN-CONTRACT.md` was not aligned.** The normative material that the core must absorb is in sections 1, 2, 3, 5, 6, 7, 11, 12, 13, and 14.1–14.4, while product material—identity, roles, screen inventory, components, and patterns 15.5 through 15.7—is interleaved with it. Restructuring without reading the entire tail would erase existing patterns. It becomes a separate PRD with this plan: an eight-section core (purpose, sources, principles, tokens by role, responsiveness, themes, states and hierarchy, validation and stopping criterion), followed by a free-form tail from section nine onward (visual identity, roles, screen inventory, components, interaction patterns, changelog).
- The seven cleanup findings above.

## Final status

Completed with limitations. Four of the five product contracts were aligned around an identical section core, and the order of the 21 seeds has a single owner and test coverage. The UI contract remained out of scope, with the reason and plan recorded.
