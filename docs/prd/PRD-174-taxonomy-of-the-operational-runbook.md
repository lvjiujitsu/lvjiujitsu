# PRD-174: Operational Runbook Taxonomy

## Summary

Rewrite the LV operations runbook in Obsidian (`obsidian/projetos/comandos-powershell-lvjiujitsu.md`) into a taxonomy of nine numbered sections. The runbook gains the previously missing sections—environments, screens, production, seeds in a table, publishing, and common errors—and now declares the actual remote-reset guards.

## Demand type

Operational documentation outside the repository. No code change.

## Current problem

The runbook had 183 lines and was the least complete of the three. It had six concrete problems:

1. **There was no production section.** The document covered staging and local environments. The `prod` environment—which has `.env.prod`, `clear_migration_supabase_prod`, and `SUPABASE_RESET_CONFIRM=RESET_PROD`—appeared nowhere, although section 6 of `docs/OPERACAO-BANCO-SEEDS.md` describes it in full.
2. **The order was reversed.** The document opened with STAGING and addressed local operation only afterward, even though local is where daily work occurs.
3. **The remote-reset guards were incomplete, and the default behavior was wrong by omission.** The runbook showed `python manage.py clear_migration_supabase_hg` immediately below two environment variables without saying that, without `--execute`, the command **only simulates**; it also omitted `DJANGO_DEBUG=False`, the Supabase host, and `SUPABASE_PROJECT_REF`. A reader following the runbook would expect immediate destruction where there is only simulation and would trust two guards where there are seven.
4. **The 21 seeds were not in a table.** They appeared only as a continuous block inside the destructive cycle, without identifying which variable each requires. `seed_system_initial_teacher` fails without `SEED_INITIAL_TEACHER_PASSWORD`, and this was undocumented.
5. **There was no common-errors table, screens table, or publishing section.**
6. **The interpreter diverged.** The runbook used `Activate.ps1` followed by `python`, while the repository treats `.\.venv\Scripts\python.exe` as the canonical path, independent of execution policy or prior activation.

## Goal

A runbook covering all three environments, whose claims about destructive operations match actual command behavior and whose sections can each be cited by number.

## Context Ledger

### Files read in full

- `obsidian/projetos/comandos-powershell-lvjiujitsu.md` (183 lines, previous version)
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/DEPLOY-RENDER-SUPABASE.md`
- `CLAUDE.md`, `AGENTS.md`

### Adjacent files consulted

- `.env.example`—canonical set of 71 keys used in section 5.3 and basis for correcting `STRIPE_PUBLIC_KEY`
- `system/urls.py`—canonical routes and aliases forming the basis of section 2
- `system/management/commands/`—actual inventory, including `explain_perf_indexes`, `backfill_membership_timeline`, and `generate_due_asaas_charges`

### Internet / official documentation

- [Stripe CLI—listen](https://docs.stripe.com/cli/listen)—confirmation of webhook forwarding to the local endpoint, retained in section 3.5.

### Context7 / MCPs / tools verified

Not applicable: no new library.

### Limitations found

The runbook lives in Obsidian, outside the repository and outside Git. No automated gate verifies that it remains truthful. The repository contains `system/tests/test_seed_docs_contract.py`, which covers seed names cited in **versioned** documentation—the Obsidian runbook is outside its reach.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: align the runbook around identically titled sections while retaining actual commands and losing no content.
- User approval: explicit operator instruction that common errors, seeds with environment prerequisites, and publishing sections must exist and contain what is true for this project.
- Date: 2026-07-26.

## Execution prompt

### Persona

LV operator writing the project's own runbook.

### Action

Rewrite the runbook into the nine-section taxonomy, using this project's actual commands and adding the missing production section.

### Context

The runbook is an operational shortcut; the standard lives in `docs/OPERACAO-BANCO-SEEDS.md` and `docs/DEPLOY-RENDER-SUPABASE.md`.

### Constraints

- No invented commands.
- No secrets: key names only.
- No mention of a project outside this repository.
- No lost content: Stripe CLI, ngrok, and sandbox checkout triggering remain.

### Acceptance criteria

- [x] Nine numbered sections in this order: Environments, Screen architecture, Local, Seeds, Staging, Production, Publish changes, Common errors, References.
- [x] A production section exists with read-only checks, reset, and reload.
- [x] Remote-reset guards list all seven conditions, including `SUPABASE_PROJECT_REF` and `--execute`, and the text states that the command simulates without `--execute`.
- [x] The 21 seeds appear in a table with each environment prerequisite.
- [x] A common-errors table exists with symptom, cause, and correction.
- [x] A publishing section states that a push triggers Auto-Deploy.
- [x] A screens table exists with canonical route, pt-BR alias, function, and access.
- [x] The payment-gateway section remains, with Stripe CLI, ngrok, and the checkout `trigger`.
- [x] Every cited command exists in the repository.
- [x] Zero mentions of a project outside this repository.

### Expected evidence

Structural verification of the document and checking each command and key against the repository.

### Output format

Markdown, pt-BR, with PowerShell blocks.

## Scope

- `obsidian/projetos/comandos-powershell-lvjiujitsu.md`.

## Out of scope

- Commit and push.
- Verification in the Stripe and Asaas dashboards.

## Impacted files

| File | Change |
|---|---|
| `obsidian/projetos/comandos-powershell-lvjiujitsu.md` | rewritten: 183 → 544 lines, nine-section taxonomy |
| `docs/prd/README.md` | regenerated index |

## Risks and edge cases

- **Documenting a nonexistent environment key.** This was a real risk: the draft used `STRIPE_PUBLISHABLE_KEY`, while the project key is `STRIPE_PUBLIC_KEY`. It was detected by checking `.env.example` and corrected before closure.
- **Documenting a nonexistent command.** Mitigated by checking every name against `system/management/commands/`.
- **Describing reset as destructive by default.** Corrected: the text now states that, without `--execute`, the command lists objects and removes nothing.

## Rules and constraints

Sections 2 and 10 (secrets are never printed) of `AGENTS.md`, plus section 1 of `CLAUDE.md`.

## Plan

- [x] Context and research
- [ ] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

Test-first does not apply: the file is outside the repository, and there is no executable behavior to cover.

## Test plan

### Tests to author

None.

### Execution authorization

- Status: authorized

### Execution evidence

The suite ran as a repository regression gate; see `Evidence`.

## Visual validation

Not applicable: no surface changed.

### Design approval

Not applicable.

### Routes and states

Not applicable.

### Desktop

Not applicable.

### Mobile

Not applicable.

### Console and terminal

Not applicable.

### Screenshot / snapshot

Not applicable.

## ORM validation

### Read-only checks

Not applicable.

### Mutating checks and authorization

Not applicable.

## Quality validation

Environment keys checked against `.env.example`, command names checked against the actual directory, section headings verified, and mentions of projects outside this repository searched.

## Evidence

Gateway keys verified in `.env.example`, forming the basis of the correction:

```text
STRIPE_SECRET_KEY  STRIPE_PUBLIC_KEY  STRIPE_WEBHOOK_SECRET
STRIPE_PLAN_SYNC_ENABLED  ASAAS_API_KEY  ASAAS_API_URL  ASAAS_WEBHOOK_TOKEN
```

`STRIPE_PUBLISHABLE_KEY` does not exist in the project; the runbook declares `STRIPE_PUBLIC_KEY`.

Resulting structure:

```text
1. Environments | 2. Screen architecture | 3. LOCAL—SQLITE (3.1 through 3.5) |
4. Seeds—order and independence (4.1 demonstration and historical import) |
5. STAGING—RENDER + SUPABASE (5.1 through 5.7) |
6. PRODUCTION—RENDER + SUPABASE (6.1 through 6.3) | 7. Publish changes |
8. Common errors | 9. References
544 lines · outside-project mentions = []
```

Section 3.5, unique to this project, is the only subsection not anticipated by the other levels of the taxonomy—and exists because only this product has a payment gateway.

Repository gates, all executed in this session:

```text
$ .\.venv\Scripts\python.exe manage.py check
System check identified no issues (0 silenced).

$ .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
No changes detected

$ .\.venv\Scripts\python.exe scripts\build_prd_index.py --check
182 PRD(s) indexada(s). (182 PRDs indexed.)
Indice em dia. (Index is up to date.)

$ .\.venv\Scripts\python.exe scripts\validate_skill_frontmatter.py
[OK] 7 skill(s) nas 3 plataformas (across 3 platforms)
[OK] 7 metadado(s) Codex integro(s) em UTF-8 com LF. (7 Codex metadata files intact in UTF-8 with LF.)
21 arquivo(s) de skill validado(s). (21 skill files validated.)

$ .\.venv\Scripts\python.exe -m pip check
No broken requirements found.

$ .\.venv\Scripts\python.exe manage.py test
Ran 769 tests in 352.074s
OK
```

Suite count preserved: 769 tests, matching the previous run.

## Implemented

- rewrote the runbook into nine numbered sections, opening with local operation;
- created section 6: production with read-only checks, destructive reset, and reload;
- completed remote-reset guards in sections 5.4 and 6.2: seven conditions, including `SUPABASE_PROJECT_REF` matching the host and the `--execute` flag, plus a note that without it the command simulates;
- added a warning in section 5.4 that reset does not recreate gateway state: charges and subscriptions already created in Asaas and Stripe continue to exist there;
- placed all 21 seeds in a table with each environment prerequisite (`ADMIN_SUPERUSER_PASSWORD`, `SEED_INITIAL_TEACHER_PASSWORD`, `SEED_INITIAL_ADMINISTRATIVE_PASSWORD`) and a note that steps 12 and 13 are idempotent legacy steps;
- added section 4.1 with the four demonstration seeds, the `SEED_TEST_PORTAL_PASSWORD` requirement, `clear_test_data`, and the historical Kanri import;
- added section 2 with the screens table: canonical English route, pt-BR alias, function, and access;
- added section 1 with the three-environment table and a warning not to mix their cycles;
- preserved ngrok, Stripe CLI, `stripe listen`, checkout `trigger` with `client_reference_id`, success signals, and `generate_due_asaas_charges` in section 3.5, with a note that the latter writes to the gateway;
- added section 7 on publishing, with local gates, `git diff`, and a warning that push triggers Auto-Deploy;
- added a ten-row common-errors table, including actual refusal messages from `clear_migrations.py`, the `python-decouple` empty-value trap, Stripe webhook pointing to the wrong route, and divergent `SITE_BASE_URL`;
- standardized the interpreter as `.\.venv\Scripts\python.exe`, without relying on `Activate.ps1`;
- added a Render variables block containing `SUPABASE_PROJECT_REF`, `SITE_NAME`, `SITE_NAME_UPPER`, seed keys, and gateway keys, plus the explanation of why `SUPABASE_RESET_CONFIRM` is not registered;
- added `explain_perf_indexes`, `check_database_connection`, `makemigrations --check --dry-run`, `pip check`, and both contract gates to section 3.2.

## Cleanup findings

- The previous version described the destructive local cycle only by saying it "terminates only Python processes belonging to LV." The description was completed with what section 4.3 of `docs/OPERACAO-BANCO-SEEDS.md` records: `taskkill` operates by PID, without `/T`, waits up to 8 seconds, and never targets its own process, direct parent, or ancestors.
- The previous version cited "canonical seeds 1→21 in the order of `docs/OPERACAO-BANCO-SEEDS.md`" without listing them, while also showing the last two separately in a block. The table replaces both forms.
- The domain and staging service were in a loose list at the top; they moved to the service table in section 5.2.

## Follow-up PRDs

None.

## Deviations from plan

The interpreter was standardized as `.\.venv\Scripts\python.exe`, which the request did not explicitly require. This does not change command behavior and removes the dependency on `Activate.ps1` and execution policy, the only reason the previous runbook required an extra step.

## Pending

No known pending items in this runbook.

## Final status

Completed.
