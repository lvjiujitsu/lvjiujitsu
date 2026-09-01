# PRD-068: Progressive single login

## Summary
The progressive initial state of LV JIU JITSU: keep only the login screen and the files directly linked to it through the contract reference. Any template, CSS, JavaScript, or image not mapped here must stay absent until a future PRD recreates the corresponding module.

## Demand type
A local destructive UI cleanup and a minimal login reimplementation.

## Current problem
There were still home, people, shell, modal, and icon templates and assets not authorized for the initial stage. That contradicts the progressive strategy requested.

## Goal
Leave the project with only the login's visual surface renderable, plus its direct assets.

## Scope
The files allowed at this stage:
- `templates/auth/base_auth.html`
- `templates/login/login_form.html`
- `static/system/css/auth/login.css`
- `static/system/js/auth/login.js`
- `static/system/js/lv/theme_boot.js`
- `static/system/img/favicon-lv.svg`
- `static/system/img/logo-lv-dark.png`
- `static/system/img/logo-lv-white.png`

## Out of scope
- The home.
- People.
- The authenticated shell.
- The CRUD modal.
- The complete registration.
- Finance, materials, classes, graduation, and the calendar.
- Seeds, migrations, the database, and automated tests.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Acceptance criteria
- No template outside `templates/auth/base_auth.html` and `templates/login/login_form.html`.
- No CSS outside `static/system/css/auth/login.css`.
- No JavaScript outside `static/system/js/auth/login.js` and `static/system/js/lv/theme_boot.js`.
- No image outside the login's favicon and logos.
- `/login/` renders with the mapped files.

## Validation
- The `templates` inventory: only `templates/auth/base_auth.html` and `templates/login/login_form.html`.
- The `static/system` inventory: only `static/system/css/auth/login.css`, `static/system/js/auth/login.js`, `static/system/js/lv/theme_boot.js`, `favicon-lv.svg`, `logo-lv-dark.png`, `logo-lv-white.png`.
- The Django Client at `/login/`: `status 200`.
- The HTML contains `system/css/auth/login.css`, `system/js/auth/login.js`, `system/js/lv/theme_boot.js`, `logo-lv-dark.png`, and `logo-lv-white.png`.
- `node --check static/system/js/auth/login.js`: success.

## Final status
Completed.
