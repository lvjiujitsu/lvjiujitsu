# PRD-036: Payment icons in registration

## Summary of the implementation
Add visual identification for PIX and Card in the plan selection step of registration.

## Demand type
Targeted UI fix

## Current problem
The `Forma de pagamento` (`Payment method`) filter shows text only, making the step less visually clear.

## Goal
Show the PIX logo and the Visa/Mastercard brands in the payment method filter.

## Context Ledger
### Files read in full
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`
- `static/system/img/icons/pix.svg`
- `static/system/img/icons/credit-card.svg`

### Adjacent files consulted
- The visual evidence sent by the user from the browser at `http://localhost:8000/register/`.

### Internet / official documentation
- Not applicable.

### MCPs / tools verified
- Browser skill — loaded for in-browser visual validation.
- PowerShell — local reading and editing.

### Limitations found
- There were no local Visa/Mastercard assets; simple SVGs were created in `static/system/img/icons/`.

## Execution prompt
### Persona
Django/frontend development agent following SDD and visual validation.

### Action
Add logos to the PIX and Card filters.

### Context
The filters are rendered dynamically in `register.js` and styled in `register.css`.

### Constraints
- do not change business rules
- no inline CSS
- keep accessibility with visible text and `alt=""` on decorative images
- update the template's cache-busting

### Acceptance criteria
- [x] The PIX button shows the PIX logo.
- [x] The Card button shows the Mastercard and Visa brands.
- [x] The layout does not break on desktop.
- [x] `python manage.py check` passes.

### Expected evidence
- Visual validation in the browser.
- The check passing.

### Output format
A summary + evidence.

## Scope
- The SVG assets.
- The JavaScript rendering the filters.
- The icons' CSS.
- The asset version in the template.

## Out of scope
- Changing the checkout.
- Changing prices or plan filters.
- Creating new UI tests while the screens are being reimplemented.

## Impacted files
- `static/system/img/icons/mastercard.svg`
- `static/system/img/icons/visa.svg`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`
- `templates/login/register.html`

## Risks and edge cases
- The icons need to keep a fixed size so the filters do not shift.

## Rules and constraints
- no migrations
- mandatory visual validation
- separate CSS

## Plan
- [x] 1. Locate the filter rendering.
- [x] 2. Add the assets.
- [x] 3. Render the icons.
- [x] 4. Adjust the CSS and the cache-busting.
- [x] 5. Validate the check and the browser.

## Visual validation
Validated in the browser at `http://localhost:8000/register/`; the plan step showed 3 loaded images: PIX, Mastercard, and Visa.

## ORM validation
Not applicable.

## Quality validation
### No hardcoding
The static paths follow the `STATIC_URL` exposed by the template.

### No brittle conditional structures
The mapping is restricted to `pix` and `credit_card`.

### No `except: pass`
Not introduced.

### No error masking
Not applicable.

### No unnecessary comments or docstrings
Not introduced.

## Evidence
- `python manage.py check`: no issues.
- `python manage.py collectstatic --noinput`: 169 files copied.
- `python manage.py test`: 158 tests, OK.
- Browser: `#plan-filters-area .payment-method-icon` returned 3 loaded images with `complete=true`.
- Mobile browser 457x1280: 4 periodicity buttons on the same row, with badges on a second row; 2 payment buttons visible with an increased height.

## Implemented
- Added the `mastercard.svg` and `visa.svg` assets.
- The payment method buttons now render the PIX logo and the card brands.
- Added CSS for the icons' size/spacing.
- Updated the cache-busting of `register.css` and `register.js`.
- Adjusted the mobile responsiveness of the plan filters for larger buttons and better horizontal use.

## Deviations from plan
None.

## Pending
None.
