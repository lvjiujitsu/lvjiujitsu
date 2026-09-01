# PRD-176: Single Theme Stylesheet

## Summary

Centralize core tokens in `static/system/css/theme.css` and correct the screens that loaded `css/auth/register.css` without `css/lv/base.css`, leaving them without the full core—dependent registration, dependent-registration completion, and installment selection.

## Demand type

UI refactoring and latent-defect correction. No business-rule, schema, or route change.

## Current problem

- The core was declared in two files, `css/lv/base.css` and `css/auth/register.css`, with five divergent role values: `--bg` and `--border` in the light theme, and `--border` and `--border-soft` in both themes.
- `css/auth/register.css` declared only four roles. Templates loading that stylesheet **without** `css/lv/base.css` lacked the other eighteen: properties fell back to initial values without a console error. These were `dependents/dependent_registration.html`, `dependents/dependent_registration_done.html`, and `login/installment_select.html`.
- `css/dependents/dependent_registration.css` uses `--input-bg` in five places, while `--input-bg` existed only in `css/auth/register.css`.
- `color-scheme` appeared in three files.

## Goal

One role, one value, one file. Every screen opening a document receives the complete core in both themes, regardless of which page stylesheets it loads.

## Context Ledger

### Files read in full

- `css/lv/base.css`, `css/auth/register.css`, `css/auth/login.css`, and `css/dependents/dependent_registration.css`;
- all 9 templates that open a document;
- sections 4 and 9 of `docs/UI-SCREEN-CONTRACT.md`.

### Adjacent files consulted

- `git show HEAD:static/system/css/home/dashboard.css`, proving the two empty blocks predated this change;
- map of which templates load which stylesheets across the project's 10 CSS files.

### Internet / official documentation

- `color-scheme` and its interaction with native controls: https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme

### Context7 / MCPs / tools verified

- In-app browser on port 8002, measuring every token used by the stylesheets loaded on each route and verifying that each resolves in both themes.

### Limitations found

- An unresolved `var()` does not produce an empty string: the property becomes invalid at computed-value time and falls back to its initial or inherited value. Searching for an empty property does not find the defect.
- `/dependents/add/` requires a session. Its cascade was reproduced by injecting the served stylesheets in the order used by the template itself.
- The server started with `--noreload`, and the template loader is cached; template changes appear only after restart.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

Explicit operator instruction: correct the problem, validate in the browser one route at a time, start the system, and navigate. Date: 2026-07-27.

## Execution prompt

### Persona

Person responsible for the product's visual system.

### Action

Create the theme stylesheet, move the core into it, link it from every template that opens a document, and verify it in the browser.

### Context

Linking the stylesheet on the three screens that lacked the core **changes** pixels and is the correction: properties stop falling back to initial values.

### Constraints

- `lv/base.css` is canonical in conflicts because it is the stylesheet loaded by `lv/base.html`;
- promote `--input-bg` to the core with the value already used by `register.css`;
- page stylesheets retain only their own prefixed family;
- validate both themes.

### Acceptance criteria

- [x] `static/system/css/theme.css` declares all 23 core tokens in both themes;
- [x] no other stylesheet declares a core token at theme level;
- [x] `theme.css` linked from all 9 templates that open a document;
- [x] `color-scheme` declared in one file only;
- [x] public routes have the complete core and zero tokens used without declaration;
- [x] section 4 of the UI contract records the single-stylesheet rule;
- [x] full suite passes with the case count preserved.

### Expected evidence

Per-route browser measurements and suite output.

### Output format

Diff, browser evidence, and updated PRD.

## Scope

- `static/system/css/**/*.css`
- all 9 templates that open a document
- section 4 of `docs/UI-SCREEN-CONTRACT.md`

## Out of scope

- The `--auth-*` family in `css/auth/login.css`: it belongs to a component and remains there.
- Token values not involved in a conflict: the palette does not change outside the five divergent roles.

## Impacted files

| File | Change |
|---|---|
| `static/system/css/theme.css` | 23-token core in both themes, plus `color-scheme` |
| `static/system/css/lv/base.css` | 45 declarations removed |
| `static/system/css/auth/register.css` | 7 declarations removed |
| `static/system/css/auth/login.css` | 2 `color-scheme` declarations removed |
| `static/system/css/home/dashboard.css` | 2 pre-existing empty blocks removed |
| 9 templates | `theme.css` linked as the first stylesheet in `<head>` |
| `docs/UI-SCREEN-CONTRACT.md` | section 4 gains the single-theme-stylesheet rule |

## Risks and edge cases

- **Choosing the wrong value in a conflict.** `lv/base.css` prevailed because it is loaded by `lv/base.html`; `register.css` serves a subset of screens.
- **Changing `--input-bg` appearance by promoting it to the core.** Its value is unchanged from `register.css`: `#fafafa` in light mode and `#18181b` in dark mode. The difference is that it now exists where it previously did not.
- **A page losing a token after its local declaration is removed.** `theme.css` is linked from all 9 document-opening templates before any page stylesheet.
- **Template not reloaded.** The loader is cached; the server was restarted before measurement, and the measurement confirms `theme.css` in the served stylesheet list.

## Rules and constraints

- Section 8 of `AGENTS.md`: CSS changes are validated in the browser in both themes.
- Section 10 of `AGENTS.md`: smallest correct change, addressing the root cause.

## Plan

- [x] Context and research
- [x] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

No new test. The resolved browser value proves the change: a test reading CSS confirms a string, not resolution. The existing suite covers regression.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test
Ran 769 tests in 369.102s
OK
```

## Visual validation

### Design approval

On the three screens that loaded `register.css` without `base.css`, eighteen roles stop falling back to initial values. No value was invented: each is the value already declared by `lv/base.css`.

### Routes and states

`/login/` and `/register/`, both HTTP 200. `/dependents/add/` requires a session; its cascade was reproduced with the served stylesheets.

### Desktop

Measurements in the in-app browser, server on port 8002, using `cache: 'reload'`:

```text
route         stylesheets                         missing core     undeclared token
/login/       [theme.css, login.css]              []               []
/register/    [theme.css, base.css, register.css] []               []

/dependents/add/ (reproduced cascade: theme.css + register.css + dependent_registration.css)
  light theme  invalid core: []
  dark theme   invalid core: []
```

Before the change, `/dependents/add/` loaded only `register.css` and `dependent_registration.css`, and only four of the eighteen measured core roles had declarations.

Owner of `color-scheme` on measured routes: `:root, html[data-theme="light"]` and `html[data-theme="dark"]`, both in `theme.css`.

### Mobile

Not measured in this PRD: no breakpoint rule changed, and the change concerns where a token is declared rather than layout.

### Console and terminal

No console error messages. `manage.py check` produced no warning.

### Screenshot / snapshot

No screenshot: the browser panel could not compose frames in this session. Per-route computed values are stronger evidence for tokens than an image—they prove the token resolves rather than only proving that the screen opened.

## ORM validation

Not applicable: no model, query, or migration change.

```text
python manage.py makemigrations --check --dry-run
No changes detected
```

## Quality validation

```text
manage.py check                     -> ok
makemigrations --check --dry-run    -> exit=0
build_prd_index.py --check          -> exit=0
validate_skill_frontmatter.py       -> exit=0
manage.py test                      -> 769 OK
```

## Evidence

Core roles with divergent values between files before the change:

```text
--bg          [light] #f4f4f6 (base.css)  vs  #f5f5f5 (register.css)
--border      [light] #e2e2e8             vs  #e4e4e7
--border      [dark]  #2d2d32             vs  #2d2d30
--border-soft [light] #ebebef             vs  #f0f0f2
--border-soft [dark]  #222226             vs  #1f1f23
```

Core declarations removed from page stylesheets:

```text
lv/base.css         45
auth/register.css    7
auth/login.css       2
total               52
```

Theme-level token declarations afterward:

```text
theme.css        [:root, html[data-theme="light"]] 23   [html[data-theme="dark"]] 23
auth/login.css   [:root, html[data-theme="light"]] 18   [html[data-theme="dark"]] 18   -- --auth-* family
```

Core roles with divergent values between files: **from 5 to 0**.
Tokens declared in more than one file: **from 3 to 0**.
Document-opening templates without the complete core: **from 3 to 0**.

## Implemented

- `theme.css` as the sole owner of the 23 core tokens and `color-scheme`;
- 52 duplicate declarations removed from three stylesheets;
- `--input-bg` promoted to the core, allowing all five uses in `dependent_registration.css` to resolve;
- `theme.css` linked as the first stylesheet in all 9 templates that open a document, covering the three screens that previously did not receive the core;
- two empty blocks predating this change removed from `dashboard.css`;
- section 4 of the UI contract updated with the single-theme-stylesheet rule, prohibition on redeclaring the core, and prohibition on self-referential custom properties.

## Cleanup findings

- `.class-list { }` and `.attendance-list { }` were empty blocks present in `HEAD`. Removed.
- A merge of two rules onto one line caused by removing a block from `lv/base.css` was undone.

## Follow-up PRDs

None.

## Deviations from plan

One. The plan was to unify the theme stylesheet. The load map exposed three templates that open documents and load `register.css` without `base.css`, leaving them without eighteen core roles. Linking `theme.css` from them entered scope because that is exactly the problem a single stylesheet exists to solve.

## Pending

- Mobile validation and screenshot: the browser panel could not compose frames in this session, and no breakpoint rule changed.
- `/dependents/add/` was measured through cascade reproduction rather than authenticated navigation: entering a password is not an action the agent performs.

## Final status

Completed. There is one theme stylesheet, five value divergences were resolved, three screens missing the core were corrected, and the 769-case suite passed.
