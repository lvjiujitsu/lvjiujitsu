# PRD-076: Legacy, governance, and documentation audit

## Summary
Sanitize the divergences between the documentation, old PRDs, and the real code. The repo contains PRDs duplicated by number, documents in `static/documentation`, contracts declaring deliveries that are absent, legacy templates/assets, and large files that hinder maintenance.

## Demand type
Governance review + a controlled cleanup.

## Current problem
- There are PRDs duplicated by number (`PRD-008`, `PRD-009`, `PRD-014`, `PRD-015`, `PRD-016`, `PRD-021`, `PRD-028`).
- PRD-066 declares the modal foundation created, but the files do not exist.
- PRD-068 declares a "progressive single login" state, but the current code contains the home, registration, people, and plans.
- `static/documentation/` contains long architecture/PRD/map documents that look like legacy documentation versioned inside static.
- Large views and assets exist: `auth_views.py` ~47 KB, `calendar_views.py` ~24 KB, `person_views.py` ~20 KB, `register.js` ~135 KB, `dashboard.css` ~58 KB.
- The existing templates have decorative comments and inline scripts.

## Goal
Separate the source of truth from the legacy, remove only what is demonstrably orphaned, and create specific follow-ups for material refactorings without expanding scope automatically.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-066-visual-and-modal-crud-pattern.md`
- `docs/prd/PRD-068-clean-people-rework-and-lv-foundation.md`
- `docs/prd/PRD-065-administrative-hubs-of-the-lv-modules.md`

### Adjacent files consulted
- The inventory of `docs/prd`
- The inventory of `static/documentation`
- The inventory of `system/views`
- The inventory of templates and assets

### Internet / official documentation
- Not applicable to a documentation removal; the primary source is the repo.

### Context7 / MCPs / tools verified
- `rg`, PowerShell, and Git.

### Limitations found
- A safe removal requires confirming the absence of references and a product decision about the historical documents.
- Do not declare a "clean system" without a closed scope.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request, which asked to identify what is poorly implemented, inconsistent, deletable, sanitizable, or outside governance.

## Scope
- Create an inventory of the conflicting documents/PRDs.
- Classify the files into source of truth, legacy to archive, removable orphan, and debt with a PRD.
- Remove only demonstrably orphaned files and within the approved scope.
- Update the governance documentation to reflect reality.

## Out of scope
- Refactoring the large views in this PRD.
- Rewriting the wizard/registration.
- Deleting history without traceability.

## Impacted files
- `docs/prd/*`
- `static/documentation/*`
- the governance documentation, when necessary

## Risks and edge cases
- Old PRDs may contain useful context, even when they contradict the code.
- `static/documentation` may be served publicly by mistake; removing or migrating it needs to be intentional.
- Duplicate PRD numbers can break traceability.

## Rules and constraints
- Confirm a reference before removing.
- Material debt outside the scope becomes a new PRD.
- Do not edit `staticfiles/`.

## Plan
- [x] Generate an inventory with the references of every candidate document.
- [x] Propose a keep/archive/remove matrix.
- [x] Execute the small, proven removals/archivals.
- [x] Create follow-ups for the large refactorings (PRD-077 through PRD-085 already existed as follow-ups of this audit).

## Test plan
### Tests to author
Not applicable, apart from text-search checks.

### Execution authorization
A destructive removal of historical documentation requires specific confirmation unless it is unequivocally orphaned.

### Execution evidence
- `docs/archive/static-documentation-legacy/`: the 12 documents from `static/documentation/` were moved (not deleted) through `git mv`, confirming the absence of references with `rg` before and after (PRD-083).
- `docs/prd/`: `ls docs/prd | grep -oE 'PRD-[0-9]+' | sort | uniq -c` no longer returns any duplicate number (PRD-079).
- `system/views/auth_views.py`: reduced from ~47 KB to 537 lines after the services were extracted (PRD-081).
- `system/views/calendar_views.py`: 4 dead views (`AdminCalendarView`, `AdminToggleSessionView`, `AdminSpecialClassCreateView`, `AdminSpecialClassDeleteView`) removed, with no route/template/test (PRD-077).
- Missing templates: from 36 at the start down to 3 (the public/student shop, a documented pending item) — PRD-075, PRD-077, PRD-078.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 316 tests OK in the final state.

## Visual validation
Not applicable to this governance PRD; the real visual validation was recorded in the child PRDs (075, 077, 078).

## ORM validation
Not applicable.

## Quality validation
- `rg` for references before/after each removal/archival.
- `git diff --check`.
- The complete `manage.py test system` at the end of the cycle.

## Evidence
- `Get-ChildItem static/documentation` listed 12 large documents — resolved by PRD-083 (archived in `docs/archive/`).
- `Get-ChildItem docs/prd` showed duplicate numbers — resolved by PRD-079 (renumbered with `git mv`, with no loss of history).
- The views/assets inventory showed large files and an excessive concentration of behavior — `auth_views.py` resolved by PRD-081; `register.js`/`dashboard.css` remain large and go to PRD-084/080 (partly resolved, the complete dedupe still pending).

## Implemented
- This PRD did not implement code directly; its role was auditing and routing to specific PRDs. All the code was implemented in PRDs 073, 074, 075, 077, 078, 079, 080, 081, 083, 085.

## Cleanup findings
- Every finding of this audit has its own PRD with real execution evidence (not just a plan).
- Debt still open and not hidden: PRD-084 (CSS tokens/inline styling) continues with a partial dedupe; the public/student shop still has no template (documented in PRD-077/078).

## Follow-up PRDs
- PRD-084 to finish the token/CSS dedupe and remove the duplicated theme logic between `plans.js` and `lv/theme_toggle.js`.
- A new PRD (not numbered yet) for the public shop and the student's pre-order/history flow, if it becomes a priority.

## Deviations from plan
- This PRD's original scope (documentation/governance) ended up being mostly executed by more specific PRDs (077, 078, 079, 081, 083) generated from it; this PRD served as the "umbrella" that documented and then closed the cycle, without duplicating the work.

## Pending
- PRD-084: the final dedupe of the theme CSS/JS tokens across the modules.
- The public shop and the student's pre-order/history flow (outside the administrative CRUD's scope).

## Final status
Completed with limitations — every relevant finding of this audit was resolved by specific PRDs with real evidence (tests + the browser); the only remaining debt (complete CSS tokens and the public shop) is documented and not hidden.
