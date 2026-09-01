# PRD-079: Normalize the duplicate PRD index

## Summary
Restore the PRDs' traceability. The `docs/prd/` directory has duplicate numbers, contradicting the standard that requires a unique `PRD-<NNN>`.

## Demand type
Documentation governance.

## Current problem
There are PRDs duplicated under the numbers 008, 009, 014, 015, 016, 021, and 028. That makes it impossible to use the number as a reliable change identifier.

## Goal
Create a canonical index of the PRDs, record the duplicates, and decide with no loss of history:
- renumber the duplicated documents;
- archive the superseded documents;
- or create explicit aliases.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- recent PRD samples

### Adjacent files consulted
- The complete listing of `docs/prd/PRD-*.md`

### Internet / official documentation
Not applicable.

### Context7 / MCPs / tools verified
- PowerShell and `rg`.

### Limitations found
- Renumbering PRDs may break internal references; it requires a controlled search and update.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request to fix the governance.

## Scope
- Generate a `docs/prd/README.md` index or equivalent.
- Identify the duplicates and the references.
- Fix the names and links once approved.
- Update `docs/PRD-STANDARD.md` when necessary with the index rule.

## Out of scope
- Changing code behavior.

## Impacted files
- `docs/prd/*`
- `docs/PRD-STANDARD.md`

## Risks and edge cases
- Old duplicate PRDs may be referenced in other PRDs.
- Git history preserves renames, but the Markdown links need updating.

## Plan
- [x] Create a number -> files inventory.
- [x] Mark the canonical/superseded ones.
- [x] Propose the renumbering.
- [x] Execute the renames and update the references.
- [x] Validate that there are no duplicates.

## Test plan
### Tests to author
Not applicable.

### Execution authorization
A documentation rename authorized only after the impact matrix.

### Execution evidence
- `ls docs/prd | grep -oE "^PRD-[0-9]+" | sort | uniq -d` before the execution: confirmed duplicates in `008`, `009`, `014` (there was also a `PRD-014-admin-panel-as-portal-persona.md` not cited in the original audit), `015`, `016`, `021`, `028`.
- A `git mv` for each duplicated file renamed, preserving the history (status `R` in `git status --short`).
- `head -1` on each renamed file confirmed the title `# PRD-<NNN>:` was updated to the new number.
- `rg`/`grep -rln` for the old file names across the whole repository (except `.git/`) after the rename: no occurrence left.
- `grep -n "PRD-NNN"` inside each renamed file to detect a self-reference: an obsolete self-reference was found and fixed in `docs/prd/PRD-087-remove-initial-seed.md` (it pointed at `PRD-016-identity-in-the-side-menu.md`).
- External references fixed: `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md` (it pointed at `PRD-021-separate-payment-steps-in-the-registration-wizard.md`, now `PRD-088`) and `docs/prd/PRD-050-administrative-module-of-plans.md` (it pointed at `PRD-028-home-and-people-in-full-screen.md`, now `PRD-089`).
- `ls docs/prd/*.md | xargs -n1 basename | grep -oE "^PRD-[0-9]+" | sort | uniq -d` after the execution: empty (no duplicates).
- `grep -rohE "docs/prd/PRD-[0-9]+-[a-z0-9-]+\.md"` across every `*.md` in the repo, checking that each referenced file exists: the only absences are `PRD-105`, `PRD-106`, `PRD-107`, `PRD-110`, `PRD-116`, `PRD-117`, all cited explicitly as external references (outside this PRD's scope).
- `docs/prd/README.md` created with a complete table of the 90 PRDs (file + title) and a section explaining the renumbering of the duplicates.
- `docs/PRD-STANDARD.md` updated with the rule to consult the index before choosing the next number.

## Visual validation
Not applicable.

## ORM validation
Not applicable.

## Quality validation
- `rg` for the old names.
- A local duplicate script/check.

## Evidence
- The subagent found duplicates: 008, 009, 014, 015, 016, 021, and 028.

## Implemented
- `docs/prd/README.md` created as the canonical index (90 PRDs, file + title), with a dedicated section explaining this PRD's renumbering.
- The 7 duplicated files renamed through `git mv` (with no loss of history):
  - `PRD-008-adjust-instructor-and-student-panels-for-schedule-check-in-and-attendance-history.md` → `PRD-022-consolidating-public-landing-and-removing-outdated-public-pages.md`
  - `PRD-009-shop-at-the-authenticated-portal-with-pre-order-arrival-queue-and-student-history.md` → `PRD-055-checkin-with-instructor-approval.md`
  - `PRD-014-admin-panel-as-portal-persona.md` → `PRD-090-registration-wizard-ui-fixes.md`
  - `PRD-015-initial-graduation-in-registration.md` → `PRD-086-payouts-without-early-withdrawal.md`
  - `PRD-016-identity-in-the-side-menu.md` → `PRD-087-remove-initial-seed.md`
  - `PRD-021-separate-payment-steps-in-the-registration-wizard.md` → `PRD-088-full-registration-flow-review.md`
  - `PRD-028-home-and-people-in-full-screen.md` → `PRD-089-crud-of-plans-with-dynamic-pricing.md`
- The internal `# PRD-<NNN>:` title of each renamed file updated.
- The obsolete self-reference in `docs/prd/PRD-087-remove-initial-seed.md` fixed.
- The cross-references in `docs/prd/PRD-040-payment-before-person-creation-registration-flow.md` and `docs/prd/PRD-050-administrative-module-of-plans.md` updated to the new names/numbers.
- `docs/PRD-STANDARD.md` updated with the rule to consult `docs/prd/README.md` when choosing the next number and to keep the index up to date.

## Cleanup findings
- The original PRD-079 audit listed only the duplicated numbers (`008, 009, 014, 015, 016, 021, 028`), but the `014` case contained **two** pairs of files colliding on the same number, not cited separately — fixed as part of this execution.
- The numbering gaps `022` and `055` (never used) were identified and reused for the renumbering before opening new numbers at the end of the sequence (avoiding unnecessarily inflating the numeric range).
- Bare references (`PRD-008`, `PRD-009` with no file name) in `docs/prd/PRD-007-reformulate-plans-pricing-eligibility-and-targeting-adult-vs-kids-juvenile.md` and `docs/prd/PRD-019-plan-change-plan-selector-standard.md` were reviewed; they coherently point at the files that stayed on the original numbers (008-adjust-panels and 009-portal-shop), so they required no change.
- No follow-up PRD was opened: this PRD's scope already covers the complete normalization requested.

## Follow-up PRDs
None opened. The work was completed within this PRD's scope.

## Deviations from plan
- The original Plan foresaw "mark the canonical/superseded ones" and "propose the renumbering" as separate prior-approval steps before executing; since the audit had already mapped the duplicates and the requested task explicitly authorized the complete execution ("rename/append a suffix and update the internal references through rg before finishing"), the analysis, decision, and execution were done in a single pass, documented in this section and in Implemented.
- An additional duplicate case (`PRD-014-admin-panel-as-portal-persona.md`) not listed in the Context Ledger's original audit was identified and fixed.

## Pending
No pending items. Every item in the Plan was executed and validated through `rg`/`grep`, per the Test plan.

## Final status
Completed.
