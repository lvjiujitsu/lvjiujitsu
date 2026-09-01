# PRD-005: Fix materials by IBJJF rule and the selection UI

## Summary of the implementation
Fix the registration materials catalog so it respects belt combinations by IBJJF graduation, keep LV gis in traditional colors, and adjust the UI for clear option/quantity selection and add-to-cart.

## Demand type
Targeted fix

## Current problem
Belts have an invalid color+size matrix (including disallowed kids combinations, such as M in brown/black), and the materials step in registration has incomplete CSS, breaking the visuals and usability of the dropdown/quantity/add button.

## Goal
Ensure a valid variant matrix, keep the seed at 2 units per variant, preserve per-category selection through a dropdown, and allow adding multiple combinations to the cart with good usability on desktop and mobile.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `system/services/seeding.py`
- `system/services/registration_checkout.py`
- `system/tests/test_product_models.py`
- `templates/login/register.html`
- `static/system/css/auth/login.css`

### Adjacent files consulted
- `static/system/js/auth/registration-wizard-clean.js`
- `system/views/product_views.py`
- `system/models/product.py`
- `docs/prd/PRD-004-correction-of-catalogue-of-materials-by-variant.md`

### Internet / official documentation
- IBJJF Uniform Requirements — `https://ibjjf.com/uniform`
- IBJJF Graduation System — `https://ibjjf.com/graduation-system`

### MCPs / tools verified
- Context7 MCP — ok — `npx -y @upstash/context7-mcp --help`
- Playwright MCP — ok — `npx -y @playwright/mcp@latest --headless --help`

### Limitations found
- No critical limitation for this fix.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD.

### Action
Implement the variant rule adjustment and the visual/functional fix for the materials step in registration.

### Context
The registration materials flow affects item selection, cart assembly, and the later per-variant stock decrement.

### Constraints
- no brittle hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

### Acceptance criteria
- [ ] Belts must not allow kids brown/black variants (M1-M3).
- [ ] LV gis must keep the traditional colors white, blue, and black.
- [ ] The seed must keep 2 units per variant.
- [ ] The materials step must show dropdown selection and a usable add button on desktop/mobile.

### Expected evidence
- passing product/seed tests
- a functional materials screen with no critical visual breakage

### Output format
Implemented code + tests + validation evidence

## Scope
- adjust the product/variant seed
- adjust color ordering in the catalog payload
- adjust the CSS of the materials step
- update the seed test

## Out of scope
- schema changes
- a full redesign of the registration step

## Impacted files
- `system/services/seeding.py`
- `system/services/registration_checkout.py`
- `system/tests/test_product_models.py`
- `static/system/css/auth/login.css`
- `templates/login/register.html`

## Risks and edge cases
- incompatibility of old drafts with removed variants
- rendering differences of the native select across browsers

## Rules and constraints
- SDD before code
- TDD for the implementation
- no hardcoding
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

## Plan
- [ ] 1. Adjust the variant matrix in the seed
- [ ] 2. Adjust color ordering for `Branca` (`White`)
- [ ] 3. Fix the styles of the materials step
- [ ] 4. Update the asset's cache-busting
- [ ] 5. Update the seed tests
- [ ] 6. Validate tests/checks
- [ ] 7. Final cleanup
- [ ] 8. Documentation update

## Visual validation
### Desktop
The option dropdown, quantity control, and add button render correctly.

### Mobile
The layout stays readable and the button takes an appropriate width.

### Browser console
No critical JavaScript error in the flow.

### Terminal
No stack trace in the tested flow.

## ORM validation
### Database
No new migrations.

### Shell checks
Optional for this fix.

### Flow integrity
The cart still serializes `variant_id` and quantity.

## Quality validation
### No hardcoding
The color/size matrix is centralized in constants.

### No brittle conditional structures
No new fragile branches.

### No `except: pass`
None introduced.

### No error masking
The flow keeps existing failures explicit.

### No unnecessary comments or docstrings
None introduced.

## Evidence
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` → 195 tests OK
- `.\.venv\Scripts\python.exe manage.py check` → no issues
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` → completed
- `.\.venv\Scripts\python.exe manage.py showmigrations` → no new migrations

## Implemented
- Belt seeds adjusted to the IBJJF matrix:
  - adult (`A1-A4`): white, blue, purple, brown, black
  - kids (`M1-M3`): white, grey, yellow, orange, green
- LV gis kept in the traditional colors (`Branco` — `White`, `Azul` — `Blue`, `Preto` — `Black`) with 2 units per variant
- Catalog ordering updated to recognize the color `Branca` (`White`)
- The CSS of the materials step in registration updated with:
  - a visible and usable option dropdown
  - a consistent quantity control
  - an add-to-cart button with correct styling/state
  - a cart preview with actions and desktop/mobile responsiveness
- Cache-busting of `registration-wizard-clean.js` updated in `register.html`
- Seed test adjusted to reflect the new rule and to forbid brown/black `M1-M3`

## Deviations from plan
None so far.

## Pending
- Run the final technical and visual validation.
