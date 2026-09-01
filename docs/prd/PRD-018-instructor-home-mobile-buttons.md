# PRD-018: Mobile buttons on the instructor's home

## Summary of the implementation
Adjust the responsiveness of the controls on the instructor home so that, on a phone, the action buttons take the full width of the row.

## Demand type
Targeted responsive UI fix.

## Current problem
In a 375px mobile viewport, the `Meu financeiro` (`My finances`), `Criar aulão` (`Create open class`), and `Gerir cronograma` (`Manage schedule`) buttons and the `Mais sobre a graduação` (`More about the graduation`) summary are only as wide as their content, producing empty areas and inconsistent alignment inside the cards.

## Goal
On small screens, each primary action of the instructor home cards must take the full row, preserving the current desktop behavior.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `templates/home/instructor/dashboard.html`
- `templates/graduation/_progress_card.html`
- `templates/base.html`

### Adjacent files consulted
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`
- `system/tests/test_graduation.py`
- visual browser observations at `http://localhost:8000/home/instructor/`

### Internet / official documentation
- Not applicable. A local CSS fix.

### MCPs / tools verified
- PowerShell — OK — file reading and command execution.
- Browser Use — OK for the page DOM; the screenshot through CDP was unavailable due to a timeout.
- Local Playwright — OK, run outside the sandbox for visual validation and layout metrics.

### Limitations found
- None.

## Execution prompt
### Persona
Development agent specializing in Django MVT and responsive CSS, following SDD + visual validation.

### Action
Fix the responsiveness of the selected buttons on the instructor home.

### Context
The instructor home uses Django templates and the shared `portal.css`.

### Constraints
- no migrations
- no business rule changes
- no inline CSS
- update the version of the CSS asset referenced in the template
- validate in a real mobile viewport

### Acceptance criteria
- [x] At 375px wide, `Meu financeiro` (`My finances`) must take the card's full row.
- [x] At 375px wide, `Criar aulão` (`Create open class`) and `Gerir cronograma` (`Manage schedule`) must take full rows.
- [x] At 375px wide, `Mais sobre a graduação` (`More about the graduation`) must take the card's full row.
- [x] On desktop, the buttons must keep an inline layout when there is room.
- [x] `manage.py check` must pass.
- [x] `collectstatic --noinput` must pass.

### Expected evidence
- A mobile screenshot or visual inspection.
- Browser console with no critical errors.
- `manage.py check`.
- `collectstatic --noinput`.

### Output format
Implemented code + validation evidence + final status.

## Scope
- Responsive CSS in `static/system/css/portal/portal.css`.
- CSS cache busting in `templates/base.html`.

## Out of scope
- Changing the instructor home flow.
- Changing copy, routes, or permissions.
- Creating migrations.

## Impacted files
- `docs/prd/PRD-018-instructor-home-mobile-buttons.md`
- `static/system/css/portal/portal.css`
- `templates/base.html`

## Risks and edge cases
- A global action rule may affect other dashboards on mobile; that is acceptable when the context is also a card action button.
- Desktop must not be affected because the rule will be limited to the mobile breakpoint.

## Rules and constraints
- SDD before code
- no hardcoded secrets
- no migrations
- mandatory visual validation

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and modeling
- [x] 3. Visual Red tests / validation
- [x] 4. Implementation
- [x] 5. Full validation
- [x] 6. Final cleanup
- [x] 7. Documentation update

## Visual validation
### Desktop
Validated in Playwright with a 1024x768 viewport. The actions container kept `display:flex`, `flex-direction: row`; `Criar aulão` (`Create open class`) and `Gerir cronograma` (`Manage schedule`) stayed on the same row.

### Mobile
Validated in Playwright with a 375x667 viewport. Final widths:
- `Meu financeiro` (`My finances`): 321px of the container's 321px.
- `Mais sobre a graduação` (`More about the graduation`): 321px of the container's 321px.
- `Criar aulão` (`Create open class`): 321px of the container's 321px.
- `Gerir cronograma` (`Manage schedule`): 321px of the container's 321px.

### Browser console
No console errors during the Playwright validation.

### Terminal
`manage.py check`, `collectstatic --noinput`, the targeted tests, and the full suite were executed.

## ORM validation
### Database
Not applicable.

### Shell checks
Not applicable.

### Flow integrity
Do not change routes or persistence.

## Quality validation
### No hardcoding
No secrets or variable data.

### No brittle conditional structures
CSS by breakpoint.

### No `except: pass`
Not applicable.

### No error masking
Not applicable.

### No unnecessary comments or docstrings
Do not add unnecessary code comments.

## Evidence
- `manage.py check`: no issues.
- `manage.py collectstatic --noinput`: 165 files copied.
- Targeted tests: 4 tests OK for the instructor home and the graduation card.
- Full suite: `manage.py test --verbosity 2` passed with 329 tests.
- Playwright mobile validation: 375x667 viewport, four controls with a width equal to the container and a console with no errors.
- Playwright desktop validation: the 1024x768 viewport kept the actions inline.

## Implemented
- Adjusted `static/system/css/portal/portal.css` so `.dashboard-section-heading > div` does not capture `.dashboard-section-actions` containers.
- At the `max-width: 520px` breakpoint, dashboard actions stack in a column, at full width and normal height.
- `summary.graduation-progress-summary` now takes the full width on mobile.
- Updated the cache-busting of `portal.css` in `templates/base.html`.

## Deviations from plan
- Browser Use loaded the page DOM, but the screenshot through CDP timed out. Visual validation was completed with local Playwright.

## Pending
- None.
