# PRD-161: Slash Commands, PRD Index, and Repository Hygiene

## Summary

Close LV’s agent-surface and traceability gaps: `.claude/commands/` exists empty, the 159-PRD index has no status column, `LICENSE` is missing, `.gitattributes` covers only shell files, runtime logs sit at the root, and `launch.json` contains a machine-specific absolute path. Supersedes PRD-158.

## Demand type

Repository governance and hygiene. No business-rule change.

## Current problem

1. `.claude/commands/` exists and is empty. The operator repeats four cycles each session — `auditar-paridade`, `reset-local`, `sync-skills`, and `validar-tela` — with no command to invoke them. PRD-158 recorded the intention and remains not started.
2. `docs/prd/README.md` lists 159 PRDs with file and title but no status column. Determining any PRD's state requires opening it and finding `## Final status`, which is absent in about 65 old PRDs. The index must carry the status column and the next-free-number declaration.
3. The index has no next-free-number declaration, which has already produced duplicates — PRD-079 documents renumbering seven duplicated numbers.
4. `LICENSE` does not exist. The project distributes under MIT.
5. `.gitattributes` covers only `*.sh text eol=lf`, without `* text=auto`.
6. The working-tree root physically contains `runserver-codex.log` (15 KB), `runserver-codex.err.log` (26 KB), `.codex-runtime/` with two logs, and `__pycache__/` directories. Git ignores them, but they pollute the working tree; the root must stay clean.
7. `.claude/launch.json` points to a machine-specific absolute path (`C:/Users/whsf/...`), instead of a relative path with a stable configuration label.
8. `docs/UI-SCREEN-CONTRACT.md` has section `## 15.` at line 351 before `## 14. Changelog` at line 555.
9. `PRD-154` says “Not started” in its body, but PRDs 155, 156, and 159, which depend on it, are complete.
10. `.github/workflows/copilot-setup-steps.yml` exists but is described in neither `CLAUDE.md` nor `README.md`.

## Goal

LV has the same surface artifacts as its references, the PRD index answers each PRD’s state without opening the file, and the working tree is clean.

## Context Ledger

### Files read in full

- `docs/prd/README.md`
- `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-154-disposable-mvp-and-gate-removal.md`
- `docs/prd/PRD-158-slash-commands-for-repeated-operational-cycle.md`
- `.claude/launch.json`, `.gitattributes`, `.gitignore`
- `CLAUDE.md`, `AGENTS.md`, `README.md`
- `.github/workflows/ci.yml`, `.github/workflows/copilot-setup-steps.yml`

### Adjacent files consulted

- The six `.claude/skills/*/SKILL.md` files
- `clear_migrations.py`
- `docs/OPERACAO-BANCO-SEEDS.md`

### Internet / official documentation

- [Claude Code — Slash commands](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Claude Code — Agent Skills](https://docs.claude.com/en/docs/claude-code/skills)
- [Git — `gitattributes`](https://git-scm.com/docs/gitattributes)
- [Open Source Initiative — MIT License](https://opensource.org/license/mit)

### Context7 / MCPs / tools verified

- Context7 available in the session. Slash-command format was checked against the official documentation above.

### Limitations found

- Automatic status extraction requires every PRD to have `## Final status`. About 65 old PRDs do not. They receive status `—`, without retroactively rewriting content.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: repository parity audit.
- User approval: explicit operator order on 2026-07-25.
- Date: 2026-07-25.

## Execution prompt

### Persona

Owner of LV’s agent surface and repository hygiene.

### Action

Create four LV-adapted slash commands, add status and next-free-number information to the PRD index, create `LICENSE`, expand `.gitattributes`, clean the working tree, make `launch.json` relative, and fix the identified documentation inconsistencies.

### Context

The project shares a governance framework. Slash commands, the PRD index, `.gitattributes`, and root cleanliness are the items to bring to the declared standard.

### Constraints

- Every slash command uses actual LV commands: local `clear_migrations.py`, the 21 `seed_system_initial_*` commands, and port 8000.
- The index is not rewritten manually: status comes from the file.
- Do not delete a tracked file without checking history.
- Do not retroactively rewrite old PRD content.

### Acceptance criteria

- [ ] `.claude/commands/` contains `auditar-paridade.md`, `reset-local.md`, `sync-skills.md`, and `validar-tela.md`, each with valid `description` frontmatter, steps, and stop criteria.
- [ ] `reset-local.md` describes LV’s real lifecycle: `clear_migrations.py`, `migrate`, `create_admin_superuser`, and 21 seeds in canonical `docs/OPERACAO-BANCO-SEEDS.md` order on port 8000. Verification: every cited command exists under `system/management/commands/`.
- [ ] `sync-skills.md` compares all three platforms and all six skills and agrees with `docs/PLATFORM-ADAPTERS.md` about the canonical directory.
- [ ] `docs/prd/README.md` gains a Status column per PRD, extracted from each file’s `## Final status`, using `—` when absent.
- [ ] `docs/prd/README.md` declares “Próximo número livre” (“Next free number”) on its own line, with value 162 after this series.
- [ ] The number of table data rows equals the number of `PRD-*.md` files under `docs/prd/`. Verification: compare counts.
- [ ] `LICENSE` exists with MIT text.
- [ ] `.gitattributes` declares `* text=auto`, `*.sh text eol=lf`, and `*.yaml text eol=lf`.
- [ ] `runserver-codex.log`, `runserver-codex.err.log`, and `.codex-runtime/` are absent from the working tree and remain covered by `.gitignore`. Verification: root listing.
- [ ] `.claude/launch.json` uses a relative `.venv` interpreter path, label `Django Dev Server`, and `autoPort: false`.
- [ ] `docs/UI-SCREEN-CONTRACT.md` sections are in increasing numeric order, with Changelog last.
- [ ] `docs/prd/PRD-154-*.md` status is coherent with PRDs 155, 156, and 159 being complete, or those PRDs’ declared dependency is corrected. Record the decision.
- [ ] `README.md` describes both `.github/workflows/` workflows.
- [ ] `docs/prd/PRD-158-*.md` is marked superseded by this PRD.
- [ ] `python manage.py check` passes and the suite is green.

### Expected evidence

Listing of `.claude/commands/`; compared counts of index rows and PRD files; root listing; check and suite output.

### Output format

Diff and PRD updated with actual evidence.

## Scope

- Four slash commands under `.claude/commands/`.
- Status column and next free number in the PRD index.
- `LICENSE` and `.gitattributes`.
- Root residue cleanup.
- Relative `launch.json`.
- Correct section order in the UI contract, PRD-154 status, and workflow description.

## Out of scope

- Environment-variable reconciliation (PRD-160).
- Remote reset, deployment, and observability (PRD-162).
- Rewriting old PRDs without a status section.
- Any model, migration, or product-flow change.

## Impacted files

- `.claude/commands/auditar-paridade.md` (new)
- `.claude/commands/reset-local.md` (new)
- `.claude/commands/sync-skills.md` (new)
- `.claude/commands/validar-tela.md` (new)
- `.claude/launch.json`
- `.gitattributes`, `LICENSE` (new)
- `docs/prd/README.md`
- `docs/prd/PRD-154-disposable-mvp-and-gate-removal.md`
- `docs/prd/PRD-158-slash-commands-for-repeated-operational-cycle.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `README.md`

## Risks and edge cases

- Adding `* text=auto` could cause mass renormalization: inspect the resulting diff and record as a deviation if broad.
- Slash command cites nonexistent command: verify each name against `system/management/commands/` before closure.
- Reordering UI-contract sections may break an anchor used by another PRD: search anchor references before moving.
- Removing root logs may lose diagnostics: they are old development-server execution logs with no historical value.

## Rules and constraints

- English documentation; identifiers remain in English.
- Smallest correct change; do not edit `staticfiles/`.
- Contract describes what exists, not what is desired.

## Plan

- [ ] Context and research
- [ ] Create four slash commands
- [ ] Reformulate PRD index with status and next free number
- [ ] `LICENSE` and `.gitattributes`
- [ ] Clean root and adjust `launch.json`
- [ ] Fix UI contract, PRD-154 status, and workflow description
- [ ] Validation
- [ ] Cleanup audit

## Test plan

### Tests to author

No new Django behavior. Verification uses inspection commands: compare index-row count with PRD-file count, confirm existence of every command cited in slash commands, and list root.

### Execution authorization

- Status: authorized by the operator’s explicit 2026-07-25 order.

### Execution evidence

Complete suite, `.\.venv\Scripts\python.exe manage.py test`:

```
Ran 722 tests in 224.415s

OK
```

`manage.py check` — `System check identified no issues (0 silenced).`

## Visual validation

Not applicable. No template, CSS, or JavaScript changed. Renumbering `UI-SCREEN-CONTRACT.md` sections is documentation-only and changes no screen.

## ORM validation

Not applicable.

## Quality validation

Slash commands created with valid frontmatter:

```
auditar-paridade.md ok
reset-local.md ok
sync-skills.md ok
validar-tela.md ok
```

Every `seed_system_initial_*` command cited in `reset-local.md` was checked against `system/management/commands/`; no nonexistent name.

PRD index regenerated from files:

```
162 PRD(s) indexed. Next free number: 163.
 —: 71
 completed: 55
 completed with limitations: 28
 not started: 4
 not completed: 3
 superseded: 1
```

Cross-count between index and disk:

```
complete table rows: 162
PRD files: 162
```

UI-contract sections in increasing order, with Changelog last:

```
## 13. Stop criterion
## 14. UX principles for AI-generated interfaces
## 15. Changelog
```

Clean root: `runserver-codex.log`, `runserver-codex.err.log`, and `.codex-runtime/` no longer exist in the working tree. `git ls-files` confirmed none were tracked.

## Evidence

- Four slash commands with valid frontmatter and verified real commands.
- Index has 162 rows for 162 files, with status extracted from disk.
- `LICENSE` and `.gitattributes` present.
- UI contract sections in order.
- Root free of residue; 722-test suite passes.

## Implemented

- `.claude/commands/` gained `reset-local.md`, `sync-skills.md`, `validar-tela.md`, and `auditar-paridade.md`, adapted to LV: 21 seeds in canonical order, four required lifecycle variables, port 8000, and `http://localhost:8000/login/` as confirmation.
- Created `scripts/build_prd_index.py`: regenerates the `docs/prd/README.md` table by extracting each file’s `## Final status` and calculating the next free number.
- Regenerated `docs/prd/README.md` with a Status column and a standalone next-free-number line. PRD-079 renumbering block preserved.
- Created MIT `LICENSE`.
- `.gitattributes` now declares `* text=auto`, `*.sh`, `*.yaml`, and `*.yml`.
- `.gitignore` now covers `.codex-runtime/`.
- `.claude/launch.json` uses a relative path, label `Django Dev Server`, and `autoPort: false`.
- `docs/UI-SCREEN-CONTRACT.md`: UX principles became section 14 and Changelog became 15.
- `docs/prd/PRD-158-*.md` marked superseded by this PRD, explaining why PRD-154 no longer blocks.
- `README.md` describes both workflows, slash commands, skill mirroring, and index regeneration.

## Cleanup findings

- **Audit finding about PRD-154 was not confirmed.** Reading the files showed `PRD-155:211` and `PRD-159:203` explicitly say “PRD-154 was not implemented” and exclude it from scope. They do not depend on it as a satisfied prerequisite; they intentionally excluded it. “Not started” status is correct and nothing changed.
- **Real divergence found outside scope:** LV's `CLAUDE.md` and `AGENTS.md` do not declare the disposable-MVP nature the project actually has. That is exactly the objective of still-open PRD-154. It was not implemented here — it has an owner and is outside this PRD.
- `.gitattributes` with `* text=auto` caused no mass renormalization.
- Index backup was created before regeneration and discarded after verification.

## Follow-up PRDs

- PRD-162 — hardened remote reset, documented deployment, and observability.
- PRD-154 remains open and remains the correct place to declare the disposable-MVP nature in LV contracts.

## Deviations from plan

- The plan called for adding a status column. Implementation created `scripts/build_prd_index.py` rather than hand-editing the table because the criterion required status to be extracted from the file and “never typed manually” — with 162 PRDs, manual editing would not survive the next PRD.
- The plan treated PRD-154 inconsistency as a defect to fix. Verification refuted the finding; nothing changed, and the refutation is recorded under `Cleanup findings`.
- Index-row counting required a more specific pattern than `^| [0-9]`: PRD-079’s renumbering block also contains lines in that format. With the correct pattern, 162 rows match 162 files.

## Pending

- Commit the working tree. No commit was made by the agent in this series.
- Run `scripts/build_prd_index.py` in CI to prevent index drift. Not done here to avoid mixing with PRD-162 infrastructure scope.

## Final status

Completed. All four slash commands exist and cite only real commands, the regenerable PRD index reports every PRD’s state without opening files, foundational artifacts are at parity, and the working-tree root is clean. Complete 722-test suite passes.
