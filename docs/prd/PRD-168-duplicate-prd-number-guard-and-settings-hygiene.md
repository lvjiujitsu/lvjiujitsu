# PRD-168: Duplicate PRD Number Guard and Settings Hygiene

## Summary

The PRD index generator promised to reveal duplicate numbers but did not do so. This PRD implements the guard, creates a suite that fixes the generator's behavior, and makes two security headers explicit in `settings.py`.

## Demand type

Governance and infrastructure. No business-rule, schema, or visual change.

## Current problem

- The docstring in `scripts/build_prd_index.py` states that the index "is the only source that reveals a reserved gap and duplicate number." The code only calculates `max(number) + 1` and never compares numbers with one another, so two files with the same `PRD-<NNN>` pass `--check` without an alert.
- This project had no tests for the generator. The behavior of `--check`, the three-digit format, and the generator's refusal conditions were not fixed by tests.
- `settings.py` repeated the `{"hg", "prod"}` literal in three environment guards without a named constant and did not declare `SECURE_CONTENT_TYPE_NOSNIFF` or `X_FRAME_OPTIONS`. Both values match the Django 5.2 defaults, but they remain invisible to readers of the file and to `check --deploy`.

## Goal

`build_prd_index.py --check` fails when two files claim the same number and names the collision in its message; generator behavior is covered by tests; environment guards use a named constant; and the security posture is declared rather than inherited.

## Context Ledger

### Files read in full

- `scripts/build_prd_index.py`
- `lvjiujitsu/settings.py`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `AGENTS.md`, `CLAUDE.md`

### Adjacent files consulted

- `system/tests/test_settings_hosts.py`
- `.github/workflows/ci.yml`
- `templates/` — 15 uses of `<iframe>`, all with `src="about:blank"` populated by JavaScript, plus 4 uses of the `xframe_options` decorator

### Internet / official documentation

- Django 5.2, `X_FRAME_OPTIONS` and clickjacking: https://docs.djangoproject.com/en/5.2/ref/clickjacking/
- Django 5.2, `SECURE_CONTENT_TYPE_NOSNIFF`: https://docs.djangoproject.com/en/5.2/ref/settings/#secure-content-type-nosniff

### Context7 / MCPs / tools verified

- Context7 was not consulted: the change uses a Django API already in use in the project, and the official documentation for the pinned version answered the outstanding questions.

### Limitations found

- None. Every required command ran locally.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

Authorized by the operator in the 2026-07-26 session, with explicit instructions to address red defects and guards in the first stage.

## Execution prompt

### Persona

Django engineer responsible for repository governance.

### Action

Implement duplicate-number detection in the index generator, create the generator test suite, and make the environment and header guards explicit.

### Context

Disposable MVP, recreatable local database, no real data. The PRD index is the canonical source of the next number, according to section 6 of `AGENTS.md`.

### Constraints

- smallest correct change;
- no new comments or docstrings;
- no new environment variable;
- no schema change;
- `X_FRAME_OPTIONS` must not break the `<iframe>` modals.

### Acceptance criteria

- [x] `collect_prd_files()` rejects a `docs/prd/` directory with a repeated number and names the conflicting files in the message;
- [x] `build_prd_index.py --check` returns 1 in that case and writes nothing;
- [x] `system/tests/test_prd_index_generator.py` exists and covers ordering, preservation of headings and notes, three-digit formatting, status, refusal conditions, and `--check` mode;
- [x] `REMOTE_ENVIRONMENTS` replaces all three repetitions of the literal;
- [x] `SECURE_CONTENT_TYPE_NOSNIFF` and `X_FRAME_OPTIONS` are declared;
- [x] `manage.py check`, `makemigrations --check --dry-run`, and the full suite pass.

### Expected evidence

Actual output from `build_prd_index.py --check`, the focused suite, and the full suite.

### Output format

Minimal diff and the PRD updated with evidence.

## Scope

- `scripts/build_prd_index.py` — duplicate guard in `collect_prd_files()`.
- `system/tests/test_prd_index_generator.py` — new file.
- `lvjiujitsu/settings.py` — `REMOTE_ENVIRONMENTS`, `SECURE_CONTENT_TYPE_NOSNIFF`, and `X_FRAME_OPTIONS`.

## Out of scope

- Aligning `AGENTS.md`, `CLAUDE.md`, and documents under `docs/`.
- Removing repository comments and docstrings.
- Unifying `requirements.txt` and the set of environment keys.
- Removing `docs/archive/static-documentation-legacy/`.

## Impacted files

| File | Change |
|---|---|
| `scripts/build_prd_index.py` | duplicate-number detection |
| `system/tests/test_prd_index_generator.py` | new file, 24 cases |
| `lvjiujitsu/settings.py` | remote-environment constant and two declared headers |
| `docs/prd/README.md` | regenerated index |

## Risks and edge cases

- `X_FRAME_OPTIONS = "DENY"` would block same-origin `<iframe>` content if the views depended on the global value. Verified before applying: all 15 project `<iframe>` elements load `about:blank` and receive content through JavaScript, while views requiring an exception already use the `xframe_options` decorator. The applied value is the same one Django already used by default, so behavior does not change—only visibility does.
- The duplicate guard is retroactive: a repository that already contains a collision will start failing in CI until it renumbers a file. This project had no collision.

## Rules and constraints

- Section 6 of `AGENTS.md`: the number comes from `docs/prd/README.md`, not from `ls`.
- Section 7 of `AGENTS.md`: do not declare Red or Green without actual output.
- Section 10 of `AGENTS.md`: no comments or docstrings by default.

## Plan

1. Implement the guard in `collect_prd_files()`.
2. Create the generator suite, including the duplicate case.
3. Observe the suite passing.
4. Verify actual `<iframe>` usage before declaring `X_FRAME_OPTIONS`.
5. Apply `REMOTE_ENVIRONMENTS` and the two headers.
6. Run `check`, `makemigrations --check --dry-run`, and the full suite.
7. Regenerate `docs/prd/README.md`.

## Test plan

### Tests to author

- `test_duplicate_number_makes_generator_fail`
- `test_check_fails_when_a_number_is_duplicated`
- `test_next_free_number_keeps_three_digits`
- the remaining generator and `--check` cases (24 total, counting the subclass that reruns the battery).

### Execution authorization

Local tests authorized by section 7 of `AGENTS.md`. Isolated test database.

### Execution evidence

```text
python manage.py test system.tests.test_prd_index_generator --verbosity 2
Ran 24 tests in 0.072s
OK
exit=0
```

```text
python manage.py test
Ran 769 tests in 292.150s
OK
exit=0
```

## Visual validation

Not applicable: no route, template, CSS, or JavaScript was changed. `X_FRAME_OPTIONS` received the value Django already applied by default, and `<iframe>` usage was audited before the change.

## ORM validation

Not applicable: no model, query, or migration change.

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

## Quality validation

```text
python manage.py check
System check identified no issues (0 silenced).
exit=0
```

```text
python scripts/build_prd_index.py --check
Indice em dia. (Index is up to date.)
exit=0
```

```text
python scripts/validate_skill_frontmatter.py
[OK] 6 skill(s) nas 3 plataformas (across 3 platforms)
18 arquivo(s) de skill validado(s). (18 skill files validated.)
exit=0
```

## Evidence

- duplicate guard exercised against a directory with a collision: the message names the number and conflicting files;
- generator suite: 24 cases, passed;
- full suite: 769 cases, passed (745 before this PRD).

## Implemented

- duplicate-number detection in `collect_prd_files()`, with a message naming each collision;
- `system/tests/test_prd_index_generator.py` with 24 cases;
- `REMOTE_ENVIRONMENTS` replacing the three repetitions of the literal;
- declared `SECURE_CONTENT_TYPE_NOSNIFF` and `X_FRAME_OPTIONS`.

## Cleanup findings

- `system/tests/test_class_catalog.py` has 0 lines: empty test file.
- `docs/archive/static-documentation-legacy/` contains 12 architecture documents superseded by the current contracts.
- `docs/prd/AUDIT-2026-06-30-master-findings.md` is not a numbered PRD and forces the generator to retain a named exception in `KNOWN_EXCEPTIONS`.
- `docs/wizard-step-plan-*.md`: three standalone guides in the root of `docs/`, outside the taxonomy of the other contracts.
- `settings.py` uses single quotes while the other files in this area use double quotes.
- `.env` declares `DJANGO_DEBUG=1` instead of `True`.

## Follow-up PRDs

Reserved in `docs/prd/README.md` according to the stages agreed with the operator: protocol-contract alignment, product-contract alignment, infrastructure and environment, and structure plus comment/docstring cleanup.

## Deviations from plan

None.

## Pending

- The six cleanup findings listed above belong to the structure and cleanup stages, not this PRD.

## Final status

Completed.
