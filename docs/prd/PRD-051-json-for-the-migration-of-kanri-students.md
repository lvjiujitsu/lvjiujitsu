# PRD-051: Migration JSON for Kanri students

## Summary of the implementation
Create auditable JSON artifacts, one per student, with the data extracted from Kanri to support a future migration to the LV JIU JITSU system.

## Demand type
Documentation regeneration and preparation of migration data.

## Current problem
The students' data lives in Kanri, and there is still no versionable local file with a structured capture for analysis, review, and a future import.

## Goal
Add the `static/initial_data/kanri_students_migration/` folder with one JSON per student, containing only the operational fields requested for the migration review: email, name, sex, birth date, document, phone, address, guardian, finances, progression, and history, with no records created in the database and no Django migrations created.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `system/models/person.py`
- `system/forms/person_forms.py`
- `system/models/graduation.py`
- `system/models/class_membership.py`
- `system/models/plan.py`
- `system/models/membership.py`
- `system/constants.py`
- `static/initial_data/initial_teachers.json`
- `static/initial_data/initial_administrative.json`
- `static/initial_data/seed_system_initial_belt_ranks.json`
- `static/initial_data/seed_system_initial_class_categories.json`
- `static/initial_data/seed_system_initial_class_catalog.json`
- `system/management/commands/seed_system_initial_teacher.py`
- `docs/prd/PRD-031-standardize-seed-json-files.md`

### Adjacent files consulted
- `static/initial_data/`
- `docs/prd/`
- `system/management/commands/`

### Internet / official documentation
- Not applicable. The task uses an authenticated page already opened by the user and the repository's local contracts.

### MCPs / tools verified
- PowerShell — OK — version `7.6.0`
- Local Python — OK — `.\.venv\Scripts\python.exe --version` returned `Python 3.12.10`
- Browser MCP — OK — an authenticated Kanri session reachable at `https://kanri-app.com.br/teacher/students`
- ripgrep — OK — `rg --files` and contract searches executed

### Limitations found
- The workspace already had unrelated changes before this task; they will not be reverted.
- This PRD implements no importer and creates no records in the local database.
- Sensitive personal data will be kept only in the local artifact requested by the user.

## Execution prompt
### Persona
Development agent specializing in Django, following SDD + TDD + migration data governance.

### Action
Create individual migration JSON files with the students extracted from Kanri.

### Context
The project uses initial data in `static/initial_data/`; the current destination models include `Person`, `PortalAccount`, `Graduation`, `ClassEnrollment`, and `Membership`, but this stage must produce only a data artifact for review.

### Constraints
- do not create records in the database
- do not create or edit migrations
- do not run `makemigrations` or `migrate`
- do not include authenticity tokens, passwords, or disposable form fields
- remove metadata, URLs, images, helper groups, gateway IDs, and unrequested fields
- mandatory JSON validation

### Acceptance criteria
- [x] The `static/initial_data/kanri_students_migration/` folder exists.
- [x] There is one JSON file per student extracted from Kanri.
- [x] Each JSON has only the top-level fields `email`, `nome`, `sexo`, `nascimento`, `tipo_documento`, `n_documento`, `telefone`, `endereco`, `responsavel`, `financeiro`, `evolucao`, and `historico`.
- [x] Password, CSRF/authenticity token, and submit fields are not persisted.
- [x] Every JSON is parseable by Python.
- [x] The file count matches the listing extracted from Kanri.
- [x] The consolidated `static/initial_data/initial_kanri_students_migration.json` does not remain as a final artifact.
- [x] No Django migration is created or changed by this task.

### Expected evidence
- Python validation loading the JSON and checking the count.
- `manage.py check`.
- `git status --short` showing only this task's files besides the pre-existing changes.

### Output format
A PRD + a folder of individual migration JSON files + validation evidence.

## Scope
- Extract the student listing from Kanri.
- Enter the students' edit pages through the browser's authenticated session.
- Capture and keep only the main fields, the address, guardian, finances, progression, and history when present in the DOM.
- Create local individual JSON files for review.

## Out of scope
- Creating an import seed/management command.
- Creating `Person`, `PortalAccount`, `Graduation`, `ClassEnrollment`, or `Membership` records.
- Downloading or keeping images/photos.
- Keeping source metadata, URLs, helper groups, gateway IDs, or unrequested fields inside the final JSON files.
- Changing templates, views, services, models, or migrations.

## Impacted files
- `docs/prd/PRD-051-json-for-the-migration-of-kanri-students.md`
- `static/initial_data/kanri_students_migration/*.json`

## Risks and edge cases
- The Kanri data may be incomplete or inconsistent; the JSON must preserve the raw value.
- Some kids belts do not fit directly into `Person.jiu_jitsu_belt`; in those cases the mapping must use a graduation snapshot and keep the raw field.
- Students may have multiple groups; the JSON must preserve every selected group and must not silently pick a single class.
- The financial and attendance history may be paginated or only partially rendered by Kanri; the JSON must record what was observed on the page.

## Rules and constraints
- SDD before code/persisted data
- no hardcoded credentials
- no error masking
- no migrations
- mandatory full reading
- mandatory validation

## Plan
- [x] 1. Context and full reading
- [x] 2. Contracts and modeling
- [x] 3. Extraction of the Kanri listing
- [x] 4. Extraction of the edit pages
- [x] 5. JSON generation
- [x] 6. Full validation
- [x] 7. Final cleanup
- [x] 8. Documentation update

## Visual validation
### Desktop
Not applicable; there is no UI change in the LV system.
### Mobile
Not applicable.
### Browser console
Not applicable to the LV system; the Browser MCP will be used only as the Kanri extraction source.
### Terminal
Validate the JSON and `manage.py check`.

## ORM validation
### Database
There will be no database change.
### Shell checks
Load the JSON and check the metadata/count.
### Flow integrity
No Django flow is changed at this stage.

## Quality validation
### No hardcoding
The JSON preserves the extracted data; it adds no credentials or secrets.
### No brittle conditional structures
Not applicable to production code.
### No `except: pass`
Not applicable.
### No error masking
Extraction failures must be recorded in the JSON under `extraction_errors`.
### No unnecessary comments or docstrings
Not applicable.

## Evidence
- Browser MCP — the Kanri listing read across 14 pages, totaling 199 students.
- Browser MCP — edit pages processed: 199 of 199; failures: 0.
- A temporary consolidated file generated and then removed: `static/initial_data/initial_kanri_students_migration.json`.
- The final folder generated: `static/initial_data/kanri_students_migration/`.
- Individual files generated: 199.
- `.\.venv\Scripts\python.exe -c "...json.loads..."` — passed: `{'students': 199, 'list_record_count': 199, 'detail_record_count': 199, 'errors': 0}`.
- Validation of the individual files — passed: `{'files': 199, 'unique_source_ids': 199, 'first': '100531-felipe-juca-delmondes.json', 'last': '99901-maicon-douglas.json'}`.
- Final sanitization — passed: `{'files': 199, 'top_level_fields': ['email', 'endereco', 'evolucao', 'financeiro', 'historico', 'n_documento', 'nascimento', 'nome', 'responsavel', 'sexo', 'telefone', 'tipo_documento']}`.
- A search for removed metadata/fields — no occurrences of `schema_version`, `source`, `target_`, `field_mapping`, `extraction`, `student_id`, `edit_url`, `selected_groups`, `photo`, `stripe`, `asaas`, `password`, `authenticity_token`, `csrf`.
- `Test-Path static\initial_data\initial_kanri_students_migration.json` — returned `False`.
- Recursive validation of forbidden fields — passed: `{'forbidden_password_or_auth_fields': 0}`.
- `.\.venv\Scripts\python.exe manage.py check` — passed: `System check identified no issues (0 silenced).`

## Implemented
- The `static/initial_data/kanri_students_migration/` folder created.
- 199 individual JSON files created, one per student, named following the `<source_id>-<name-slug>.json` pattern.
- Each file was sanitized to contain only: `email`, `nome`, `sexo`, `nascimento`, `tipo_documento`, `n_documento`, `telefone`, `endereco`, `responsavel`, `financeiro`, `evolucao`, and `historico`.
- The consolidated `static/initial_data/initial_kanri_students_migration.json` removed to avoid an "everything in one" artifact.
- Metadata, URLs, images, helper groups, Stripe/Asaas IDs, password, authentication, CSRF, token, and submit removed.

## Deviations from plan
- No functional deviation.
- The capture of internal tables preserves only the rows rendered in the DOM of Kanri's edit page; if Kanri paginates any tab internally, that pagination must be handled in a future stage.

## Pending
- Create a future importer/seed to turn this JSON into `Person`, `Graduation`, `ClassEnrollment`, `PortalAccount`, and `Membership`.
- Manually review sensitive data and ambiguous fields before any real import.
