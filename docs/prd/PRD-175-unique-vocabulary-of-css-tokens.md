# PRD-175: Unified CSS Token Vocabulary

## Summary

Unify CSS token names around the shared core semantic vocabulary while preserving values, and correct **three tokens used in `var()` without any declaration**—a defect predating this PRD that fails silently by falling back to the initial value. Also correct section 4 of the UI contract, which authorized divergent names.

## Demand type

UI refactoring and latent-defect correction. No business-rule, schema, or route change.

## Current problem

- The brand accent used `--brand-red`, `--brand-red-strong`, and `--brand-red-muted`. The name embedded a color, binding the token to the palette: changing red would require renaming the token everywhere.
- **Three tokens were used without ever being declared:** `--brand-primary` and `--card` in `css/auth/register.css`, and `--surface-muted` in `css/home/dashboard.css`. Their properties fell back to the initial value without a console error.
- The authentication family used `--auth-brand` and `--auth-brand-strong`, propagating the old vocabulary into the component.
- Section 4 of `docs/UI-SCREEN-CONTRACT.md` stated that "the core declares roles, not concrete names: the token name belongs to the identity." That rule authorized the divergence.

## Goal

Each role has one name, without an embedded color. No `var()` use lacks a declaration. Renaming changes no pixel.

## Context Ledger

### Files read in full

- all 7 CSS files under `static/system/`, including `css/lv/base.css`
- sections 4 and 9 of `docs/UI-SCREEN-CONTRACT.md`

### Adjacent files consulted

- `git show HEAD:` for `css/auth/register.css` and `css/home/dashboard.css`, to date the orphaned tokens
- inventory of the 79 distinct token names in use, with a presence matrix

### Internet / official documentation

- CSS Custom Properties, unresolved `var()` behavior: https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties#custom_property_fallback_values

### Context7 / MCPs / tools verified

- In-app browser on port 8002, listing every token used by the stylesheets loaded on each page and verifying that each resolves.

### Limitations found

- An unresolved `var()` **does not** produce an empty string: the property becomes invalid at computed-value time and falls back to its initial or inherited value. Searching for an empty property does not find the defect.
- Internal routes require a session. Coverage for pages that could not be reached came from a static completeness check across all files.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

Explicit operator instruction: correct token convergence and validate in the browser, one route at a time. Date: 2026-07-27.

## Execution prompt

### Persona

Person responsible for the product's visual system.

### Action

Rename tokens to the shared vocabulary while preserving values, declare what was missing, and correct the contract.

### Context

Renaming a token while preserving its value changes no pixel. Declaring a missing token **does** change a pixel, for the better: the property stops falling back to the initial value.

### Constraints

- preserve values during every rename;
- token names do not embed colors;
- an orphan receives the token for the role it represented, not a new value;
- validate both themes in the browser.

### Acceptance criteria

- [x] brand accent uses `--accent`, `--accent-strong`, and `--accent-muted`, with no color in the name;
- [x] authentication family uses `--auth-accent` and `--auth-accent-strong`;
- [x] all three orphaned tokens remapped to their corresponding role token;
- [x] zero tokens used without a declaration;
- [x] section 4 of the contract declares the canonical name of each role;
- [x] login and registration validated in both themes in the browser;
- [x] full suite passes with the case count preserved.

### Expected evidence

Token-completeness verification, per-route browser measurements, and suite output.

### Output format

Diff, browser evidence, and updated PRD.

## Scope

- `static/system/css/**/*.css` and JavaScript files that read tokens
- section 4 of `docs/UI-SCREEN-CONTRACT.md`

## Out of scope

- Existing token values: the palette does not change.
- `--auth-cyan-soft` and other component tokens without a counterpart in the primary vocabulary.
- Theme unification into one file—see `Pending`.

## Impacted files

| File | Change |
|---|---|
| 8 CSS files | accent renamed from `--brand-red*` to `--accent*` |
| 1 CSS file | authentication family aligned |
| 2 CSS files | orphaned tokens remapped to role tokens |
| `docs/UI-SCREEN-CONTRACT.md` | section 4 rewritten with 19 roles and each canonical name |

## Risks and edge cases

- **Renaming and breaking `var()`.** Replacement anchored on `(?<![-a-z])--token(?=\s*:)` and `var\(\s*--token(?![-a-z])`, preventing the `--brand-red` rule from affecting `--brand-red-strong`. Rules ran from the longest name to the shortest.
- **Changing appearance by declaring an orphan.** Where a token did not exist, the property fell back to the initial value. Making it resolve **is** a visual change and is the defect correction.
- **`--card` remapped to `--surface`.** The old name represented the card's embedded surface; `--surface` is the equivalent role already declared in `css/lv/base.css`.

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
Ran 769 tests in 307.090s
OK
exit=0
```

## Visual validation

### Design approval

Not applicable to renaming: the palette is unchanged. For the three orphaned tokens, the value becomes that of the already declared role token.

### Routes and states

`/login/` and `/register/`, both HTTP 200. Internal routes require a session and were covered by static completeness checks across all CSS.

### Desktop

Measurements in the in-app browser, with the server on port 8002:

```text
/login/     stylesheets=2  tokens used=8   UNRESOLVED: []
            light theme  --accent: #c41230  --bg: #f4f4f5
            dark theme   --accent: #e02244  --bg: #08090b
/register/  stylesheets=2  tokens used=10  UNRESOLVED: []
            fields=223
            light theme  body bg rgb(245,245,245) | text rgb(24,24,27)
            dark theme   body bg rgb(9,9,11)      | text rgb(250,250,250)
```

Tokens from the old vocabulary in served HTML: **0**.

### Mobile

Not measured in this PRD: no breakpoint rule changed, and this is a token-name change rather than a layout change.

### Console and terminal

No console messages. `manage.py check` produced no warning.

### Screenshot / snapshot

No screenshot: the browser panel could not compose frames in this session. Computed-value measurement is stronger evidence for tokens than an image—it proves the token resolves rather than only proving that the screen opened.

## ORM validation

Not applicable: no model, query, or migration change.

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

## Quality validation

```text
manage.py check                     -> ok
makemigrations --check --dry-run    -> exit=0
build_prd_index.py --check          -> exit=0
validate_skill_frontmatter.py       -> exit=0
pip check                           -> exit=0
manage.py test                      -> 769 OK
```

## Evidence

Orphaned tokens and proof that they predated this PRD:

```text
--card           in Git HEAD: uses=3 declarations=0
--surface-muted  in Git HEAD: uses=1 declarations=0
```

Applied remapping:

```text
--brand-red -> --accent                --brand-red-strong -> --accent-strong
--brand-red-muted -> --accent-muted    --brand-primary -> --accent
--card -> --surface                    --surface-muted -> --surface-soft
--auth-brand -> --auth-accent          --auth-brand-strong -> --auth-accent-strong
```

Token completeness afterward:

```text
declared: 41 | used: 41
used without declaration: 0
declared without use: 0
```

Shared core vocabulary: **from 3 to 12 names** (`--accent --bg --border --card-shadow --danger --info --muted --panel --success --surface --text --warning`).

Section 4 of the UI contract: **1 variant**.

## Implemented

- brand accent uses `--accent`, `--accent-strong`, and `--accent-muted`, without a color in the name;
- authentication family uses `--auth-accent` and `--auth-accent-strong`;
- all three orphans remapped to the token for their intended role;
- section 4 of the contract rewritten with 19 roles and the canonical name of each, plus two new rules: a component family uses `--<family>-text` and `--<family>-border`, and a token used without a declaration is a defect.

## Cleanup findings

- **The theme is declared in two files**, `css/lv/base.css` and `css/auth/register.css`, with repeated tokens. There is no single theme stylesheet.
- `--auth-cyan-soft` exists in the authentication family without a clear counterpart in the primary vocabulary.

## Follow-up PRDs

- Single theme stylesheet, with `base.css` as the source and `register.css` consuming tokens instead of redeclaring them.

## Deviations from plan

Two.

The plan was to rename tokens. The completeness check exposed three tokens used without declarations that predated this PRD—as confirmed by `git show HEAD:`. Correcting them entered scope because renaming around a latent defect would make that defect harder to find later.

Section 4 of the contract was not in scope. It entered because it stated that "the token name belongs to identity," exactly the opposite of what this PRD implements.

## Pending

- The single theme stylesheet recorded under `Follow-up PRDs`.
- Mobile validation and screenshot: the browser panel could not compose frames in this session, and no breakpoint rule changed.

## Final status

Completed. The project has a unified vocabulary without colors embedded in token names, three orphaned tokens were corrected with proof that they predated the change, and the 769-case suite passed.
