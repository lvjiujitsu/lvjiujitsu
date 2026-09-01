# PRD-164: Self-Contained Contracts and CI Standardization

## Summary

Remove every reference to other repositories from all LV JIU JITSU documentation and standardize the CI workflow. The project will describe itself exclusively through its own operation.

## Demand type

Documentation governance and CI. No business-rule change.

## Current problem

1. `CLAUDE.md` has an entire section pointing to two external repositories through absolute paths, presenting LV JIU JITSU as part of a set.
2. `.claude/commands/auditar-paridade.md` reads two external repositories through absolute paths and compares contracts. It is a shared flow inside a project that must be autonomous.
3. Twenty-nine PRDs under `docs/prd/` contain 282 occurrences of names and paths from other repositories, many in acceptance criteria and evidence sections.
4. The CI workflow structurally diverges from other workflows operated by the same owner without a recorded decision: job name, missing `timeout-minutes`, outdated action versions, and migration verification embedded in the same step as `check`.
5. `docs/references/PATTERNS-DE-OUTRO-PROJETO.md` has 308 lines describing patterns to import from another repository, including an external absolute path.

The practical effect is that an agent reading LV JIU JITSU contracts concludes that it must consult other repositories to operate this one. It does not and must not: an absolute path to another machine or project ages, breaks, and distracts.

## Goal

Every LV JIU JITSU contract, document, and PRD describes only LV JIU JITSU. No absolute path leaves the repository. CI has an explicit, complete structure with one step per verification.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`, `README.md`
- `.claude/commands/auditar-paridade.md`, `reset-local.md`, `sync-skills.md`, `validar-tela.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PLATFORM-ADAPTERS.md`, `docs/PRD-STANDARD.md`, `docs/UI-SCREEN-CONTRACT.md`, `docs/OPERACAO-BANCO-SEEDS.md`, `docs/DEPLOY-RENDER-SUPABASE.md`
- `.github/workflows/ci.yml`
- Every PRD returned by the search
- `scripts/validate_skill_frontmatter.py`

### Adjacent files consulted

- The six `.claude/skills/*/SKILL.md` files
- `.cursor/rules/*.mdc`
- `docs/prd/README.md`

### Internet / official documentation

- [GitHub Actions — Workflow syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [GitHub Actions — `jobs.<job_id>.timeout-minutes`](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions#jobsjob_idtimeout-minutes)
- [`actions/checkout`](https://github.com/actions/checkout)
- [`actions/setup-python`](https://github.com/actions/setup-python)

### Context7 / MCPs / tools verified

- Context7 available. Workflow-syntax references come from the official documentation above.

### Limitations found

- PRDs are historical records. Rewriting them removes context from past decisions. The operator explicitly decided to clean PRDs as well. Technical content and internal traceability are preserved; only external references are removed.
- The CI job runs for real only on the next push.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: contracts presented the project as part of a repository set with external absolute paths.
- User approval: explicit operator order — “Each project must believe it operates independently and exclusively, without interconnection, so cross-mentions are extremely harmful. Shared flows must not exist.” Scope confirmed as contracts and all PRDs, standardized CI runner, and removal of the cross-audit command.
- Date: 2026-07-26.

## Execution prompt

### Persona

Owner of LV JIU JITSU governance contracts.

### Action

Remove every external reference from contracts and PRDs, delete the cross-audit command, and rewrite the CI workflow with explicit structure.

### Constraints

- No repository file may cite another repository by name or path.
- Preserve technical PRD content: remove the external reference, retain the decision and evidence.
- Where a PRD said “ported from another project,” state the rule directly without external provenance.
- Do not change code behavior.

### Acceptance criteria

- [x] No versioned repository file contains another repository’s name/path or phrases equivalent to “sibling project(s).” Verification: case-insensitive textual search returns zero occurrences outside `.venv/`, `staticfiles/`, and `db.sqlite3`.
- [x] No versioned file contains an absolute path outside the repository. Verification: search for `C:\Users\whsf\Documents\GitHub\` returns only paths pointing to this repository.
- [x] `.claude/commands/auditar-paridade.md` does not exist.
- [x] `CLAUDE.md` has no section about other repositories.
- [x] `.github/workflows/ci.yml` declares `runs-on: ubuntu-latest`, `timeout-minutes`, `actions/checkout@v5`, and `actions/setup-python@v5`, with `python-version` equal to `.python-version` content.
- [x] CI has one step per verification in this order: `pip check`, skill validator, `manage.py check`, `makemigrations --check --dry-run`, suite.
- [x] `ci.yml` is valid YAML. Verification: `yaml.safe_load` succeeds.
- [x] `python manage.py check` passes and the suite is green.

### Expected evidence

Text-search output; workflow structure read back from file; check and suite output.

### Output format

Diff and PRD updated with actual evidence.

## Scope

- Clean `CLAUDE.md` and every contract with external references.
- Remove `.claude/commands/auditar-paridade.md`.
- Clean PRDs containing occurrences.
- Rewrite `.github/workflows/ci.yml`.

## Out of scope

- Code, model, migration, or route behavior changes.
- PRD technical content beyond external references.

## Impacted files

- `CLAUDE.md`
- `.claude/commands/auditar-paridade.md` (removed)
- `docs/references/PATTERNS-DE-OUTRO-PROJETO.md` (removed)
- `.github/workflows/ci.yml`
- `docs/prd/*.md`
- `docs/prd/README.md`

## Risks and edge cases

- Removing a reference may leave a sentence without a subject: rewrite each occurrence instead of blind replacement.
- Old PRD acceptance criterion citing another project as source: state the rule directly while preserving what was verifiable.
- Text search false positives in `.venv/` or binary files: verification explicitly excludes those paths.

## Rules and constraints

- English documentation; identifiers remain in English.
- Contract describes what exists.

## Plan

- [x] Context and research
- [x] Clean active contracts
- [x] Remove cross-audit command
- [x] Clean PRDs
- [x] Rewrite CI workflow
- [x] Validation
- [x] Cleanup audit

## Test plan

### Tests to author

No new Django behavior. Verification uses text search and local execution of CI steps.

### Execution authorization

- Status: authorized by explicit operator order on 2026-07-26.

### Execution evidence

Complete suite, `.\.venv\Scripts\python.exe manage.py test`:

```
Ran 741 tests in 264.629s

OK
```

External-reference detector scanning every repository `.md` outside `.venv/`, `.git/`, and `staticfiles/`:

```
lvjiujitsu: 0 occurrence(s)
```

## Visual validation

Not applicable. No template, CSS, or JavaScript changed.

## ORM validation

Not applicable.

## Quality validation

Workflow structure read back from file:

```
job=ci  runs-on=ubuntu-latest  steps=8
```

Eight steps, in the same order across all projects: Checkout, Set up Python (3.12.10), Install dependencies, Validate dependencies (`pip check`), Validate skill frontmatter, Django system check, Verify migration baseline (`makemigrations --check --dry-run`), Run test suite.

Local simulation of each step using the CI environment:

```
pip check:        No broken requirements found.
validate skills:  18 skill file(s) validated.
django check:     System check identified no issues (0 silenced).
migrations:       No changes detected
```

`ci.yml` is valid YAML loaded with `yaml.safe_load`.

## Evidence

- Zero external references across the repository.
- No absolute path outside the repository.
- `.claude/commands/auditar-paridade.md` absent.
- CI with identical explicit structure and one step per verification.
- Complete suite green.

## Implemented

- Removed `CLAUDE.md` section 11, which pointed to another repository and an external bootstrap.
- `README.md` no longer cites the removed command.
- Removed `.claude/commands/auditar-paridade.md`.
- Removed `docs/references/PATTERNS-DE-OUTRO-PROJETO.md` — 308 lines that existed to import another repository’s patterns.
- Rewrote three external mentions in `docs/UI-SCREEN-CONTRACT.md`.
- Removed external paths from `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` and its archived counterpart.
- Cleaned 29 PRDs; removed 24 external absolute-path lines.
- Renamed three PRDs: `PRD-054-architectural-alignment-and-safe-reset.md`, `PRD-066-visual-and-modal-crud-pattern.md`, and `PRD-069-lv-home-with-mature-visual-governance.md`, updating references.
- Rewrote `.github/workflows/ci.yml`: switched from `windows-latest` to `ubuntu-latest` with the standard eight-step structure.
- Regenerated PRD index through `scripts/build_prd_index.py`.

## Cleanup findings

- `PRD-054` originally scoped two repositories. External sections were removed and the reduction recorded in a note inside the PRD so future readers understand the gap.
- `PRD-070` listed skills with another project’s prefix in an LV synchronization record. Corrected to actual `lv-*` names.
- No residue introduced.

## Follow-up PRDs

None.

## Deviations from plan

- CI runner changed from `windows-latest` to `ubuntu-latest` by operator decision. Tests do not depend on Windows: the only PowerShell-using component is `clear_migrations.py`, which does not run in CI.
- First cleanup attempt used automatic term replacement and produced nonsensical sentences. It was reverted with `git checkout` across 115 tracked PRDs and redone through full-phrase replacement. Untracked PRDs without a revert path were corrected manually, including PRD-154 and PRD-158, which were not part of this series.

## Pending

- Run CI for real: all eight steps were verified locally, but the job runs only on the next push.
- Commit the working tree. No commit was made by the agent.

## Final status

Completed. No repository file cites another repository, the imported-pattern file was removed, and CI now runs on `ubuntu-latest` with the same eight-step structure. Complete 741-test suite passes.
