# PRD-173: Common Core of the Visual Contract

## Summary

Restructure `docs/UI-SCREEN-CONTRACT.md` into two parts: an eight-section normative core with stable headings and wording, and a product-specific tail from section 9 onward containing identity, roles, screen inventory, components, interaction patterns, and changelog. Tokens are declared by **role** in the core, the concrete palette moves to the identity section, and the duplicate numbering in sections 14/15 is eliminated.

## Demand type

Product contract. Normative documentation with no code, template, CSS, or JavaScript change.

## Current problem

The contract had 591 lines across 15 sections and four concrete defects:

1. **Numbering was inconsistent.** Section 14 was titled "UX Principles for AI-Generated Interfaces," but its subsections were numbered `15.1` through `15.7`—and the next section, `15`, was the Changelog. Thus, sections `15.6` and `15.7` belonged to no actual section 15, and the document had two competing numbering schemes. An internal reference to "section 15" was ambiguous.
2. **Tokens were declared only as a CSS block.** Section 5 provided the two themes as literal CSS without stating the role of each variable. For a new component, there was no way to choose among `--panel`, `--surface`, and `--surface-soft` without reading the stylesheets—and the `--auth-*` set used on access screens was not mentioned.
3. **The anti-KPI rule was at the end of the chain.** It lived as section `15.7`, after modal CRUD, as if it were another interaction pattern rather than a general prohibition applying to every screen.
4. **Normative and product rules occupied the same level.** "A color pill displays the color as a background or colored circle," which belongs to the material store, appeared in the same affordance block as "mandatory interactive states: default, hover, focus-visible, active, disabled," which applies everywhere.

## Goal

A contract with a single numbering scheme, separating normative material from product-specific material without losing any existing rule—including modal CRUD and the public wizard's terminal contract.

## Context Ledger

### Files read in full

- `docs/UI-SCREEN-CONTRACT.md` (591 lines, previous version)
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/DEPLOY-RENDER-SUPABASE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`

### Adjacent files consulted

- `static/system/css/`—actual inventory of custom properties (40) and `@media` breakpoints
- `static/system/js/auth/login.js`, `static/system/js/home/dashboard.js`—the `lv-theme` key
- `system/urls.py`—canonical English routes and pt-BR aliases used in the screen inventory

### Internet / official documentation

- [WCAG 2.2—Target Size (Minimum) 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)—source of the 44-by-44-pixel touch target cited in the core, which the previous contract already referenced by guideline number.

### Context7 / MCPs / tools verified

Not applicable: the change does not involve a library, framework, SDK, or CLI whose version must be checked.

### Limitations found

The previous screen inventory listed modules as "routes removed from phase 1—reintroduced according to PRDs," a prose list that no longer matched `system/urls.py`, where the modules exist with canonical routes and aliases. Section 11 was rewritten from the actual routes.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

`lv-ui-delivery` does not apply: no screen changes, so there is no route to validate in a browser.

## Understanding approved

- Summary presented: restructuring the visual contract into a normative core (sections 1 through 8) plus a product tail (sections 9 through 14), with tokens by role.
- User approval: explicit operator instruction naming the eight core sections and emphasizing that sections `15.5` through `15.7` could not be lost.
- Date: 2026-07-26.

## Execution prompt

### Persona

Person responsible for the LV JIU JITSU visual contract.

### Action

Rewrite `docs/UI-SCREEN-CONTRACT.md` using the approved structure, with unique numbering and without losing any existing rule.

### Context

According to section 2 of `AGENTS.md`, this document owns the subject "visual contract, states, and evidence."

### Constraints

- Numbering becomes unique: no subsection may reference a section that does not exist.
- The core does not cite concrete token names.
- No mention of a project outside this repository.

### Acceptance criteria

- [x] The document has exactly 14 top-level sections in the approved order.
- [x] No subsection is numbered outside its containing section.
- [x] Section 4 declares token roles, not concrete names.
- [x] Section 9 maps roles to actual LV tokens, retains the concrete palette for both themes, and cites the `--auth-*` set.
- [x] Section 9 describes the breakpoints actually written in the stylesheets.
- [x] Content from section `15.5` (wireframes), `15.6` (modal CRUD), and `15.7` (anti-KPI) remains present: the first two in section 13, the third in the core.
- [x] The public wizard's terminal contract remains declared.
- [x] The changelog retains every previous entry and adds this PRD's entry.
- [x] Zero mentions of a project outside this repository.

### Expected evidence

Structural verification of the document and output from repository gates.

### Output format

Markdown, pt-BR, without secrets.

## Scope

- `docs/UI-SCREEN-CONTRACT.md`.

## Out of scope

- Convergence of the CSS-token vocabulary.
- Any template, CSS, or JavaScript change.
- Commit and push.

## Impacted files

| File | Change |
|---|---|
| `docs/UI-SCREEN-CONTRACT.md` | rewritten: 591 → 718 lines, 15 → 14 sections |
| `docs/AUDIT-2026-06-30-master-findings.md` | two section references annotated with the numbering used at the time |
| `docs/prd/README.md` | regenerated index |

## Risks and edge cases

- **Losing a rule while eliminating duplicate numbering.** Mitigated by inventorying the document block by block before writing: each `15.x` subsection was classified as normative (moves to the core) or product-specific (moves to the tail).
- **Rewriting the screen inventory with a nonexistent route.** Mitigated by extracting route prefixes directly from `system/urls.py`.
- **Documenting a nonexistent token.** Mitigated by measuring custom properties directly in the stylesheets.

## Rules and constraints

Sections 2 (single owner per subject), 5 (full reading), and 12 (cleanup) of `AGENTS.md`, plus `docs/PRD-STANDARD.md`.

## Plan

- [x] Context and research
- [ ] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

Test-first does not apply: this changes a normative document, with no executable behavior to cover.

## Test plan

### Tests to author

None.

### Execution authorization

- Status: authorized

### Execution evidence

The suite ran as a regression gate; see `Evidence`.

## Visual validation

### Design approval

Not applicable: no surface changed.

### Routes and states

Not applicable.

### Desktop

Not applicable.

### Mobile

Not applicable.

### Console and terminal

Not applicable.

### Screenshot / snapshot

Not applicable. No route changed.

## ORM validation

### Read-only checks

Not applicable.

### Mutating checks and authorization

Not applicable.

## Quality validation

Structural verification by script: section count and order, count of interaction-pattern subsections, and search for mentions of projects outside this repository.

## Evidence

Document structure:

```text
14 sections: 1. Purpose | 2. Sources of truth | 3. Mandatory principles |
4. Required CSS tokens | 5. Responsiveness | 6. Light and dark themes |
7. Required states and visual hierarchy | 8. Implementation rules,
validation, and stopping criterion | 9. Visual identity | 10. Roles and permissions |
11. Screen inventory | 12. Components | 13. Interaction patterns |
14. Changelog
patterns_13 = 4 (13.1 through 13.4)
cross_mentions = []
718 lines
```

Token inventory measured from the stylesheets and used to write section 9:

```text
--auth-bg --auth-border --auth-brand --auth-brand-strong --auth-card
--auth-card-border --auth-danger --auth-danger-soft --auth-focus --auth-info
--auth-info-soft --auth-input --auth-muted --auth-shadow --auth-success
--auth-success-soft --auth-text --auth-toggle --bg --border --border-soft
--brand-red --brand-red-muted --brand-red-strong --card-shadow
--card-shadow-hover --danger --danger-muted --focus-ring --info --info-muted
--input-bg --muted --panel --success --success-muted --surface --surface-soft
--text --warning --warning-muted
```

Measured breakpoints forming the basis of section 9:

```text
8x min-width:768px · 5x min-width:600px · 5x min-width:480px
4x max-width:520px · 3x min-width:720px · 3x min-width:640px
2x max-width:640px · 2x max-width:639px · 2x max-width:479px
1x min-width:900px · 1x min-width:540px · 1x min-width:1600px
```

Top-level routes extracted from `system/urls.py` and used as the basis of section 11:

```text
account/ administracao/ administration/ aulas/ cadastro/ calendar/ classes/
cronograma/ dashboard/ dependents/ financeiro/ financial/ graduacao/
graduation/ health/ home/ login/ logout/ loja/ materiais/ materials/
meus-materiais/ minha-mensalidade/ my-materials/ pagamentos/ password-change/
password-reset/ people/ pessoas/ plan-prices/ plan-tiers/ planos/ plans/
register/ requests/ reset/ store/ turmas/
```

Repository gates, all executed in this session:

```text
$ .\.venv\Scripts\python.exe manage.py check
System check identified no issues (0 silenced).

$ .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
No changes detected

$ .\.venv\Scripts\python.exe scripts\build_prd_index.py --check
182 PRD(s) indexada(s). (182 PRDs indexed.)
Indice em dia. (Index is up to date.)

$ .\.venv\Scripts\python.exe scripts\validate_skill_frontmatter.py
[OK] 7 skill(s) nas 3 plataformas (across 3 platforms)
[OK] 7 metadado(s) Codex integro(s) em UTF-8 com LF. (7 Codex metadata files intact in UTF-8 with LF.)
21 arquivo(s) de skill validado(s). (21 skill files validated.)

$ .\.venv\Scripts\python.exe -m pip check
No broken requirements found.

$ .\.venv\Scripts\python.exe manage.py test
Ran 769 tests in 352.074s
OK
```

Suite count preserved: 769 tests, matching the previous run.

## Implemented

- rewrote `docs/UI-SCREEN-CONTRACT.md` with an eight-section core and a six-section tail; numbering is now unique;
- section 4 of the core declares fourteen token roles, separating mandatory roles from conditional ones;
- section 9 maps fourteen roles to actual tokens, preserves the CSS palette for both themes, records that `:root` is the light theme, and explains the role of the `--auth-*` set;
- section 9 documents the stylesheets' mobile-first strategy—the majority of breakpoints grow through `min-width`—and the `lv-theme` key applied by `theme_boot.js` before paint;
- section 11 was rewritten from actual routes, with a table of canonical English routes and pt-BR aliases replacing the prose list of "modules removed from phase 1";
- preserved the public wizard's terminal contract as section 11.4;
- section `15.6` (operational CRUD in a modal/dialog) moved intact to section `13.1`, including implementation, states, actual shared foundation, and the PRD-141 M-01 debt for standalone pages with an inline theme IIFE;
- section `15.7` (anti-KPI) moved into the core and gained the seven requirements that authorize an indicator;
- store affordances were separated into section `13.2`: color, size, and out-of-stock pills are product rules and moved out of the normative affordance block;
- section `15.5` (wireframes) became section `13.3`, retaining the four-step process and three reference prompts for hierarchy and grouping;
- the PRD state-machine mapping became section `13.4`;
- preserved LV-specific operational typography—13px on dense screens and 15px on the public form—in section 9;
- roles gained a note that accumulation is the rule: the same person may be both student and instructor;
- the changelog retains all previous entries, rewritten to one line each, and adds this PRD's entry.

## Cleanup findings

- The previous heading said, "Every implemented screen must derive from this contract"; the actual rule moved to the core and is stricter: every new **or reimplemented** screen derives from the contract and a specific PRD.
- The previous section 12 mixed validation order with testing policy ("Without actual execution, do not declare Red or Green"). The policy was retained in section 8.3 with the remaining evidence rules.
- The previous section 10 had a dated block in its title—"actual state—Jul/2026, PRD-144 P2." The date left the title while the content remained: the inventory describes what exists, and the changelog stores dates.
- `docs/AUDIT-2026-06-30-master-findings.md` cites the contract by section number in two findings, pointing to sections `9.1` and `9.2`. After renumbering, section 9 became Visual Identity, and the references would become traps. Both lines were annotated with the numbering used at the time and the current equivalents (`11.1` and `11.2`), preserving the historical record. No other file across the three repositories references the contract by section number—verified by searching `.md` and `.mdc` files, including skills, `.cursor/rules/`, and `/validar-tela`.

## Follow-up PRDs

None reserved in this PRD.

## Deviations from plan

Two rules were added to the core because they already applied in practice: the minimum-accessibility block and the stopping-criterion item for real Render or Supabase data absent from the repository. Section 11 was rewritten from `system/urls.py`—rewriting it was not planned, but retaining a list already contradicted by the code would preserve a defect.

## Pending

- Convergence of the CSS-token vocabulary.
- No visual validation was performed because no surface changed.

## Final status

Completed.
