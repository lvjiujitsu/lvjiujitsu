# PRD-002: Simplify class display during registration

## Summary of the implementation
Reduce verbosity in the class step of the registration wizard by displaying only the information needed for the user's decision on mobile: the class name without unnecessary repetition, a short summary, and a schedule grouped by day in the `Horário - Professor` (`Time - Instructor`) format.

## Demand type
Targeted fix

## Current problem
The class step of registration is too long on mobile. The card repeats `Jiu Jitsu Adulto` (`Adult Jiu-Jitsu`), displays a verbose schedule structure by day and instructor, and retains redundant visual elements, increasing scrolling and reducing readability.

## Goal
Present classes in a more compact and direct way, preserving the current selection and eligibility behavior while making the content easier for the end user to read.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/prd/PRD-001-client-registration-with-cpf-validation.md`
- `lvjiujitsu/urls.py`
- `system/urls.py`
- `system/views/auth_views.py`
- `system/forms/registration_forms.py`
- `system/services/class_overview.py`
- `templates/login/register.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `system/tests/test_forms.py`
- `system/tests/test_class_portal_views.py`
- the relevant section of `system/tests/test_views.py` for the registration flow
- the relevant sections of `static/system/css/auth/login.css`
- the relevant sections of `static/system/css/portal/class-catalog.css`

### Adjacent files consulted
- search results from `system/models/` and `system/services/` used to map the class and schedule flow
- `git status --short`

### Internet / official documentation
- Not applicable to the proposed fix.

### MCPs / tools verified
- PowerShell shell in the workspace — working — `Get-Location`
- ripgrep — working — `rg --files ...`
- Playwright/browser MCP — pending verification in this execution

### Limitations found
- During preflight, `CLAUDE.md` was misaligned with the actual repository; the discrepancy was corrected during this delivery.

## Execution prompt
### Persona
Development agent specializing in server-rendered Django with progressive JavaScript, following SDD + TDD.

### Action
Simplify class presentation in the registration step without changing the flow's eligibility, selection, or persistence logic.

### Context
The registration wizard uses `registration-wizard-clean.js` to render class cards dynamically from the payload serialized by `get_registration_catalog_payload()`. The problem is in the mobile presentation layer of the class step.

### Constraints
- no hardcoded business rules
- no error masking
- no migrations
- mandatory full reading of the impacted flow
- mandatory visual validation
- Brazilian Portuguese interface

### Acceptance criteria
- [ ] The class card in registration must not repeat `Jiu Jitsu Adulto` (`Adult Jiu-Jitsu`) unnecessarily.
- [ ] The class's expandable area must prioritize `Dia da semana` (`Day of the week`) and simple lines in the `Horário - Professor` (`Time - Instructor`) format.
- [ ] Secondary information that is not essential to the immediate choice must not clutter the screen.
- [ ] Class selection, eligibility, and the registration payload must continue to work.
- [ ] The layout must be shorter and more readable on mobile.
- [ ] The browser console must remain free of critical JavaScript errors.

### Expected evidence
- passing automated tests
- `manage.py check` with no errors
- `collectstatic --noinput` with no errors
- `showmigrations` consistent with project policy
- visual validation of the class step in a browser
- console with no critical JavaScript errors

### Output format
Implemented code + tests/contract adjustments + actual validation evidence + documented limitations

## Scope
- reduce the visual density of the wizard's class cards
- simplify the organization of the schedule by time and instructor
- maintain compatibility with the current selection flow

## Out of scope
- changing eligibility business rules
- changing registration persistence
- changing public catalog pages outside the wizard
- creating migrations

## Impacted files
- `static/system/js/auth/registration-wizard-clean.js`
- `static/system/css/auth/login.css`
- `system/tests/test_views.py` or another necessary contract test

## Risks and edge cases
- losing the distinction between different physical classes that share the same logical name
- losing too much useful information when summarizing instructors and times
- visual regression on small screens due to the grid change
- indirect impact on the family plan if class selection no longer reflects the current state correctly

## Rules and constraints
- SDD before code
- TDD for behavior that can reasonably be covered by the current contract
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

## Plan
- [ ] 1. Confirm the current state of the class step
- [ ] 2. Define the minimum visual contract and the smallest necessary adjustment
- [ ] 3. Write the test/contract adjustment (Red)
- [ ] 4. Implement simplified rendering (Green)
- [ ] 5. Adjust the styles of the summarized block (Refactor)
- [ ] 6. Validate technically
- [ ] 7. Validate visually on mobile
- [ ] 8. Record evidence and limitations

## Visual validation
### Desktop
- verify that the card remains functional and selectable

### Mobile
- verify reduced height and clear schedule readability

### Browser console
- no critical JavaScript errors

### Terminal
- no stack traces

## ORM validation
### Database
- there is no schema change

### Shell checks
- not applicable beyond the integrity of the rendering and submission flow

### Flow integrity
- class selection must continue to populate the hidden field/multiple select correctly

## Quality validation
### No hardcoding
- keep eligibility and audience rules sourced from the existing catalog

### No brittle conditional structures
- extract simple, focused helpers for the new summary

### No `except: pass`
- no silent error suppression

### No error masking
- keep flow failures visible through the existing validation

### No unnecessary comments or docstrings
- follow the file's current standard

## Evidence
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` → 186 tests passing
- `.\.venv\Scripts\python.exe manage.py check` → no errors
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` → 2 static files updated, no errors
- `.\.venv\Scripts\python.exe manage.py showmigrations` → only `system.0001_initial`, with no new migrations
- Visual validation through Playwright at `http://127.0.0.1:8000/register/` on mobile and desktop → the step 3 card displays `Treinos disponíveis` (`Available training sessions`) and lines in the `06:30 - Layon Quirino` format
- Browser console inspected through Playwright → 0 errors and 0 critical warnings
- Template asset cache-busting updated to ensure the browser receives the new JavaScript and CSS
- Temporary screenshot artifacts removed after validation

## Implemented
- The registration payload now exposes `compact_schedule_sections` by day, with entries ready in the `horário - professor` (`time - instructor`) format
- The wizard renderer now consumes the compact summary instead of building a verbose tabular schedule
- The solo-flow card no longer repeats `Jiu Jitsu Adulto` (`Adult Jiu-Jitsu`) in the internal header and now uses `Treinos disponíveis` (`Available training sessions`)
- The expandable summary was reduced to `Ver horários da semana` (`View weekly schedule`)
- The old schedule CSS was simplified into a short, mobile-readable list
- Asset versions in `templates/login/register.html` were incremented to invalidate the cache

## Deviations from plan
- The asset versions in the template had to be updated because the browser continued serving the previous JavaScript and CSS, preventing actual validation of the change.
- `CLAUDE.md` had to be rewritten with factual project data to remove the discrepancy found during preflight.

## Pending
- No functional pending items were identified for this fix.
