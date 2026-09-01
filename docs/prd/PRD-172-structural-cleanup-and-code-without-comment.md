# PRD-172: Structural Cleanup and Comment-Free Code

## Summary

Remove archived legacy documentation, the empty test file, and the exception carried by the index generator; delete every code comment and docstring; correct a BOM in a Python file; make the rule absolute in section 10 of `AGENTS.md`; and eliminate the last mention of a project outside this repository.

## Demand type

Cleanup and governance review. No behavior, schema, or route change.

## Current problem

- `docs/archive/static-documentation-legacy/` contained **12** architecture documents superseded by the current contracts. A superseded document that remains in the repository may be read as if it were still authoritative.
- `system/tests/test_class_catalog.py` had **0 bytes**: a test file that tests nothing and suggests coverage that does not exist.
- `docs/prd/AUDIT-2026-06-30-master-findings.md` is not a numbered PRD and forced `scripts/build_prd_index.py` to carry a named exception in `KNOWN_EXCEPTIONS`, which the index contract does not allow.
- `system/tests/test_services.py` began with a UTF-8 BOM. Python runs it because the loader removes the BOM, but any tool that reads the file as plain text fails with `invalid non-printable character U+FEFF`.
- Section 10 of `AGENTS.md` said "do not add comments or docstrings **by default**," with the exception "retain only a non-inferable contract or real risk." That exception kept 94 comments and 88 docstrings alive.
- `docs/prd/PRD-164` mentioned an outside project by name in five places.

## Goal

No superseded documents under `docs/`; only numbered PRDs under `docs/prd/`; an index generator without a custom exception; zero comments and zero docstrings outside `migrations/`; an absolute rule in the contract; and zero mentions of projects outside this repository.

## Context Ledger

### Files read in full

- `AGENTS.md`, section 13 of `docs/AGENT-WORKFLOW.md`
- `scripts/build_prd_index.py`
- `docs/prd/PRD-164-self-contained-contracts-and-standardisation-of-the-ci.md`
- all 65 `.py` files containing comments or docstrings

### Adjacent files consulted

- `system/tests/test_seed_docs_contract.py`, which validates `docs/OPERACAO-BANCO-SEEDS.md`
- all 12 documents under `docs/archive/static-documentation-legacy/`, to confirm that their content already exists in the current contracts

### Internet / official documentation

- Python, `ast.get_docstring` and `tokenize.COMMENT`: https://docs.python.org/3/library/ast.html
- Python, `utf-8-sig` and BOMs in source code: https://docs.python.org/3/library/codecs.html#module-encodings.utf_8_sig

### Context7 / MCPs / tools verified

- Context7 was not consulted: removal uses the Python standard library.

### Limitations found

- Removing a docstring that is the **only** body of a function or class produces a syntax error. The remover detects this situation and substitutes `pass`.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: residual Stage 5 plus Stage 6, with the option "Everything: py, html, css, js."
- User approval: selected at the opening of the audit and reaffirmed with "continue until finished."
- Date: 2026-07-26.

## Execution prompt

### Persona

Engineer responsible for repository hygiene.

### Action

Remove superseded documentation and residue, delete comments and docstrings through syntactic analysis, make the rule absolute, and complete self-containment.

### Context

Documentation lives in Obsidian, in `conhecimento-<project>.md`; the rationale lives in the PRD; operational instructions live under `docs/`.

### Constraints

- remove comments with `ast` and `tokenize`, never with a regular expression;
- exclude `migrations/`;
- every seed name cited in `docs/OPERACAO-BANCO-SEEDS.md` must continue to exist: `test_seed_docs_contract.py` fails otherwise;
- the suite must pass with the same case count.

### Acceptance criteria

- [x] `docs/archive/` removed;
- [x] `docs/prd/` contains only numbered PRDs and `README.md`;
- [x] `KNOWN_EXCEPTIONS` restored to `{"README.md"}`;
- [x] `system/tests/test_class_catalog.py` removed;
- [x] `system/tests/test_services.py` has no BOM;
- [x] zero comments and zero docstrings in `.py` files outside `migrations/`;
- [x] zero comments in `.html`, `.css`, and `.js` files;
- [x] section 10 of `AGENTS.md` contains an absolute prohibition;
- [x] zero mentions of outside projects in versioned files;
- [x] `conhecimento-lvjiujitsu.md` created;
- [x] `check`, `makemigrations --check --dry-run`, index, skills, `pip check`, and the full suite pass with the case count preserved.

### Expected evidence

Before-and-after counts, suite output, index-generator verification, and self-containment scan.

### Output format

Diff, command output, and the updated PRD.

## Scope

- `docs/archive/static-documentation-legacy/`.
- `docs/prd/AUDIT-2026-06-30-master-findings.md`, moved to `docs/`.
- `scripts/build_prd_index.py`, only `KNOWN_EXCEPTIONS`.
- `system/tests/test_class_catalog.py`.
- Every `.py` file outside `migrations/`, plus `.html`, `.css`, and `.js` files.
- Section 10 of `AGENTS.md` and section 13 of `docs/AGENT-WORKFLOW.md`.
- `docs/prd/PRD-164`, only outside-project mentions.

## Out of scope

- The three `docs/wizard-step-plan-*.md` guides referenced by section 12 of `CLAUDE.md`.
- Generated `migrations/0001_initial.py`.
- Historical PRDs, whose text is a record.
- `docs/UI-SCREEN-CONTRACT.md` and CSS tokens.
- Creating a single `seed_test_data`.
- Changing single quotes in `settings.py`.
- The five code-convergence items recorded in PRD-171.

## Impacted files

| File | Change |
|---|---|
| `docs/archive/` | removed; 12 documents |
| `docs/prd/AUDIT-2026-06-30-master-findings.md` | moved to `docs/` |
| `scripts/build_prd_index.py` | `KNOWN_EXCEPTIONS` restored to `{"README.md"}` |
| `system/tests/test_class_catalog.py` | removed; 0 bytes |
| `system/tests/test_services.py` | UTF-8 BOM removed |
| 65 `.py` files | 94 comments and 88 docstrings removed |
| 7 `.css`/`.js` files | 158 comments removed |
| 3 `.html` files | 38 comments removed |
| `AGENTS.md` | section 10 now contains an absolute prohibition; 226 → 233 lines |
| `docs/AGENT-WORKFLOW.md` | section 13 refers to section 10 |
| `docs/prd/PRD-164` | no outside-project names |

## Risks and edge cases

- **Moving the audit file** could break the index generator, which listed it as an exception. The file was moved first, then the exception was removed, followed by a passing `--check`.
- **Removing the empty test** does not change the suite count: 0 bytes produces 0 cases. The count before and after is 769, confirming this.
- **A docstring as the only body** would produce a syntax error; handled with `pass`.
- **The BOM** caused the remover to fail parsing before any write. Reading with `utf-8-sig` and writing without a BOM corrected both problems at once.
- **Regex-based removal** would have corrupted strings containing `#` or `/*`. Therefore, the process used `ast` for docstrings and `tokenize` for comments.

## Rules and constraints

- Section 10 of `AGENTS.md`, using its new wording.
- Section 12 of `AGENTS.md`: material debt outside scope becomes a follow-up.

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

No new test. The 769-case suite is the test, and `system/tests/test_seed_docs_contract.py` already covers the contract between the database runbook and actual commands.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test
Ran 769 tests in 265.968s
OK
exit=0
```

The count is identical to the count before cleanup—the removed test file had 0 cases.

## Visual validation

### Design approval

Not applicable: no visual change.

### Routes and states

Not applicable.

### Desktop

Not applicable.

### Mobile

Not applicable.

### Console and terminal

`manage.py check` produced no warning.

### Screenshot / snapshot

Not applicable. Comments in CSS and Django templates have no visual effect: CSS comments are discarded by the parser, and HTML comments appear in the served HTML but do not render.

## ORM validation

### Read-only checks

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

### Mutating checks and authorization

No write was executed.

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

Comment counts before and after, using the same counter:

```text
before: py 94 comments + 88 docstrings | css/js 158 | html 38
after:  py  0 comments +  0 docstrings | css/js   0 | html  0
```

Index generator after removing the exception:

```text
KNOWN_EXCEPTIONS = {"README.md"}
normalized build_prd_index.py: 205 lines
build_prd_index.py --check      -> Indice em dia (Index is up to date), exit=0
```

Self-containment scan:

```text
versioned files: 0 outside-project mentions
```

## Implemented

- removed `docs/archive/static-documentation-legacy/`, containing 12 documents;
- moved the audit file to `docs/`, and restored `KNOWN_EXCEPTIONS` to `{"README.md"}`—the index generator now has a single variant;
- removed `system/tests/test_class_catalog.py`;
- removed the UTF-8 BOM from `system/tests/test_services.py`;
- removed 94 comments and 88 docstrings from 65 `.py` files using `ast` and `tokenize`;
- removed 158 comments from 7 `.css` and `.js` files and 38 from 3 `.html` files;
- made the rule in section 10 of `AGENTS.md` absolute, with generated files as its sole exception;
- made section 13 of `docs/AGENT-WORKFLOW.md` refer to section 10;
- removed outside-project names from `docs/prd/PRD-164`;
- created `conhecimento-lvjiujitsu.md`, covering the public-registration flow, redirect/webhook/database separation, and known pitfalls.

## Cleanup findings

- `scripts/build_prd_index.py` uses `description=__doc__` in `argparse`; without a docstring, `--help` displays `None`.
- The three `docs/wizard-step-plan-*.md` guides remain loose in the root of `docs/`, now referenced by section 12 of `CLAUDE.md` but outside the taxonomy of the other contracts.

## Follow-up PRDs

None added. The open items remain those recorded in PRDs 170 and 171.

## Deviations from plan

One. The BOM in `system/tests/test_services.py` was not anticipated; it appeared as a parsing failure during the remover's dry run. Correcting it entered scope because it was the same type of hygiene defect and, without the correction, that file would have been excluded from removal.

## Pending

- `scripts/build_prd_index.py --help` displays `None`.
- The three wizard guides outside the `docs/` taxonomy.
- Items inherited from PRDs 170 and 171, including the branch remote.

## Final status

Completed. Superseded documentation was removed; `docs/prd/` contains only numbered PRDs; the index generator has a single variant; there are zero comments and zero docstrings outside `migrations/`; the contract rule is absolute; there are zero outside-project mentions; and the 769-case suite passed with its count preserved.
