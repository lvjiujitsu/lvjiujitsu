# PRD-084: CSS tokens and inline style removal

## Summary
Consolidate the visual tokens and remove inline colors/styles from the templates and CSS. The contract requires tokens and forbids stray visual exceptions.

## Demand type
UI/UX refactoring + visual governance.

## Current problem
- The CSS contains literal colors beyond the tokens.
- The templates use `style=`.
- There is inline theme JavaScript in the standalone pages.
- People, Plans, the Home, the Wizard, and the Calendar use divergent visual foundations.

## Goal
Unify the visual system:
- tokens in a base file;
- no `style=` in functional templates;
- no duplicated inline theme;
- assets versioned correctly.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `static/system/css/auth/register.css`
- `static/system/css/home/dashboard.css`
- `static/system/css/people/people.css`
- `static/system/css/plans/plans.css`
- the main existing templates

### Adjacent files consulted
- PRD-075
- PRD-080

### Internet / official documentation
Not applicable.

### Context7 / MCPs / tools verified
- PowerShell and `rg`.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request.

## Scope
- Inventory the literal colors and `style=`.
- Consolidate the tokens in a shared foundation.
- Migrate the modules by priority.

## Out of scope
- A product redesign outside the modules touched.

## Impacted files
- `static/system/css/*`
- the existing templates
- `static/system/js/lv/theme.js`

## Risks and edge cases
- Changing broad CSS with no browser may cause a visual regression.
- Some inline styles may be legitimate dynamic data and need a safe alternative.

## Plan
- [ ] Inventory and classification.
- [ ] Remove the inline theme through PRD-075.
- [ ] Migrate the CSS per module.
- [ ] Validate desktop/mobile/themes.

## Test plan
### Tests to author
- Manual visual tests through the browser.
- `node --check` when the JavaScript changes.

### Execution authorization
Authorized locally.

### Execution evidence
Pending.

## Visual validation
Mandatory.

## ORM validation
Not applicable.

## Quality validation
- `rg "style=|#[0-9a-fA-F]{3,8}|rgba\\("` with justified exceptions.
- The internal browser.

## Evidence
- The subagent confirmed hardcoding in the CSS and inline styles in the templates.

## Implemented
Pending.

## Cleanup findings
Pending.

## Follow-up PRDs
Pending.

## Deviations from plan
Pending.

## Pending
Pending.

## Final status
Not completed.
