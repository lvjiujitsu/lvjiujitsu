# PRD-111: Staging seeds for N:N registration

## Summary
Create local, auditable fixtures to visually validate the person registration combinations in LV JIU JITSU: a student, a student with a dependent, a guardian with a dependent, a student with an administrative upgrade, a student with an administrative upgrade and a dependent, an instructor, an instructor with a dependent, a back-office-only person, a back-office person who also trains, and a guardian who also trains.

## Demand type
A local operational seed + a controlled visual validation script.

## Current problem
- Manual coverage of People depends on creating registrations one by one through the interface.
- The N:N combinations of person, dependent, operational role, class, martial experience, belt, and blood type are not available in a single local load.
- The visual test of assigning/removing an administrative profile, deleting a student, and toggling roles needs clean, predictable accounts.

## Goal
- Add extensive JSONs in `static/initial_data` with fictitious, complete data for staging.
- Create explicitly manual Django commands to load those fixtures.
- Cover every blood type, experience with and without jiu-jitsu, other martial arts, adult/kids belts, and N:N relationships.
- Document a paused, controlled, sequential checklist for validating every possibility in the browser.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `system/constants.py`
- `system/models/person.py`
- `system/models/class_membership.py`
- `system/models/graduation.py`
- `system/models/class_group.py`
- `system/services/registration.py`
- `system/services/administrative_training.py`
- `system/services/portal_capabilities.py`
- `system/utils/person_data.py`
- `system/management/commands/seed_system_initial_person_type.py`
- `static/initial_data/initial_teachers.json`
- `static/initial_data/seed_system_initial_belt_ranks.json`
- `static/initial_data/seed_system_initial_class_categories.json`
- `static/initial_data/seed_system_initial_ibjjf_age_categories.json`
- `static/initial_data/seed_system_initial_class_catalog.json`

### Adjacent files consulted
- `system/tests/test_commands.py`
- `docs/prd/README.md`
- The existing files in `static/initial_data`
- The existing files in `system/management/commands`

### Internet / official documentation
- Django 5.2 docs via Context7:
  - `https://docs.djangoproject.com/en/5.2/howto/custom-management-commands/`
  - `https://docs.djangoproject.com/en/5.2/topics/testing/tools/`

### Context7 / MCPs / tools verified
- Context7 `Django`: custom commands must live in `management/commands`, modules starting with `_` do not become public commands, testable output must use `self.stdout.write`, and tests can call `call_command` while capturing `stdout`.

### Limitations found
- A person with no real fighting experience must keep the martial fields empty or semantically neutral; forcing a belt/martial date in those cases would falsify the data.
- The fixtures depend on the base seeds for person types, belts, IBJJF categories, class categories, initial instructors, and the class catalog.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
The current request authorizes creating the JSONs, the commands/fixtures, and a validation PRD for full staging of the registration possibilities.

## Scope
- Create four staging JSON files in English:
  - `seed_system_initial_test_teachers.json`
  - `seed_system_initial_test_students.json`
  - `seed_system_initial_test_administrative.json`
  - `seed_system_initial_test_guardians.json`
- Create four corresponding manual commands:
  - `seed_system_initial_test_teachers`
  - `seed_system_initial_test_students`
  - `seed_system_initial_test_administrative`
  - `seed_system_initial_test_guardians`
- Create a common importer to avoid duplicating the logic for the person, the portal account, the enrollments, the operational roles, the graduations, the assistant instructor assignments, and the relationships.
- Create focused tests for parsing, idempotency, and critical coverage.
- Update the operational seed documentation.

## Out of scope
- Changing the public wizard's rules.
- Running the seed automatically during the canonical bootstrap.
- Creating real payments or real Stripe/Asaas customers, or any remote data.
- Visually validating every screen in this PRD; the script below defines the later one-by-one staging pass.

## Impacted files
- `docs/prd/README.md`
- `docs/prd/PRD-111-staging-seeds-registration-nn.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `static/initial_data/seed_system_initial_test_teachers.json`
- `static/initial_data/seed_system_initial_test_students.json`
- `static/initial_data/seed_system_initial_test_administrative.json`
- `static/initial_data/seed_system_initial_test_guardians.json`
- `system/services/test_seed_fixtures.py`
- `system/management/commands/seed_system_initial_test_teachers.py`
- `system/management/commands/seed_system_initial_test_students.py`
- `system/management/commands/seed_system_initial_test_administrative.py`
- `system/management/commands/seed_system_initial_test_guardians.py`
- `system/tests/test_test_seed_fixtures.py`

## Coverage matrix
### Person and relationship
- [ ] A student with no dependent.
- [ ] A student with a dependent.
- [ ] A guardian with one dependent.
- [ ] A guardian with multiple dependents.
- [ ] A guardian who also trains.
- [ ] A dependent with two guardians.
- [ ] A student with an administrative upgrade.
- [ ] A student with an administrative upgrade and a dependent.
- [ ] A back-office-only person, who does not train.
- [ ] A back-office person who trains.
- [ ] A back-office person with a dependent.
- [ ] An instructor.
- [ ] An instructor with a dependent.
- [ ] An instructor with an additional operational role.

### Martial experience
- [ ] No martial arts experience.
- [ ] Jiu-jitsu white belt.
- [ ] Jiu-jitsu blue belt.
- [ ] Jiu-jitsu purple belt.
- [ ] Jiu-jitsu brown belt.
- [ ] Jiu-jitsu black belt.
- [ ] Jiu-jitsu red/black coral belt.
- [ ] Jiu-jitsu red/white coral belt.
- [ ] Jiu-jitsu red belt.
- [ ] Kids white, grey, yellow, orange, and green.
- [ ] Muay Thai.
- [ ] Judo.
- [ ] Karate.
- [ ] Boxing.
- [ ] Wrestling.
- [ ] Another discipline.

### Health and personal data
- [ ] A+
- [ ] A-
- [ ] B+
- [ ] B-
- [ ] AB+
- [ ] AB-
- [ ] O+
- [ ] O-
- [ ] Male biological sex.
- [ ] Female biological sex.
- [ ] A complete address.
- [ ] A complete emergency contact.
- [ ] Allergies and injuries filled in.

### Operation and portal
- [ ] An active portal account for local login.
- [ ] A person with no operational role.
- [ ] `academy-manager`.
- [ ] `class-assistant` scoped by class.
- [ ] `people-support`.
- [ ] `financial-operator`.
- [ ] `stock-operator`.
- [ ] `graduation-operator`.
- [ ] Multiple operational roles on the same person.
- [ ] Enrollment in an adult class.
- [ ] Enrollment in a kids class.
- [ ] Enrollment in a juvenile class.
- [ ] Enrollment in a women's class.
- [ ] An assistant instructor of a class.

## Acceptance criteria
- [x] The four JSONs exist in `static/initial_data` and use English keys.
- [x] Each entry has complete personal data; the semantic "no experience" exceptions stay empty only in the corresponding martial fields.
- [x] The fixtures cover every blood type, every planned belt, every planned discipline, and every planned N:N relationship.
- [x] The four commands are manual, idempotent, and do not enter any automatic seed flow.
- [x] The commands create/update `Person`, `PortalAccount`, `Graduation`, `ClassEnrollment`, `PersonOperationalRole`, `ClassInstructorAssignment`, and `PersonRelationship` according to the JSON.
- [x] Class/belt dependency failures produce a clear `CommandError` before any partial write.
- [x] A focused test validates the parsing, the minimum coverage, the idempotency, and the critical relationships.
- [x] `manage.py check` passes.

## Test plan
### Tests to author
- `system.tests.test_test_seed_fixtures`:
  - validates that every JSON parses;
  - validates the coverage of blood types, disciplines, belts, and the main tags;
  - runs the base dependencies and runs the four commands twice;
  - checks the portal accounts, the N:N relationships, the operational roles, and the enrollments.

### Execution authorization
Local, in Django's isolated test database.

### Expected evidence
- `.venv/Scripts/python.exe manage.py test system.tests.test_test_seed_fixtures --verbosity 2`
- `.venv/Scripts/python.exe manage.py check`

## Visual validation checklist
Run only after loading the base seeds and the staging seeds in the desired local environment.

### Preparation
1. Run the canonical dependency seeds:
   - `seed_system_initial_person_type`
   - `seed_system_initial_belt_ranks`
   - `seed_system_initial_ibjjf_age_categories`
   - `seed_system_initial_class_categories`
   - `seed_system_initial_teacher`
   - `seed_system_initial_class_catalog`
2. Run the staging seeds:
   - `seed_system_initial_test_students`
   - `seed_system_initial_test_guardians`
   - `seed_system_initial_test_administrative`
   - `seed_system_initial_test_teachers`
3. Use the local fixture password documented in the JSON/command.
4. Validate one item at a time, recording a screenshot and the result before moving on.

### Round 1: login and areas
1. Log in as a plain student: they must land in the student area with no management.
2. Log in as a student with a dependent: it must show their own data and the relationship with the dependent.
3. Log in as a guardian with a dependent: it must allow viewing the dependent.
4. Log in as a guardian who trains: it must keep their own student area and the guardian relationship.
5. Log in as an instructor: it must show the instructor area.
6. Log in as an instructor with a dependent: it must keep the instructor area and the family relationship.
7. Log in as a back-office-only person: it must show management, with no enrollment of their own.
8. Log in as a back-office person who trains: it must show management and their own enrollment/area where applicable.

### Round 2: People and N:N
1. Open the People list and filter by each relationship type.
2. Open the detail of the dependent with two guardians.
3. Open the detail of the student with a dependent.
4. Open the detail of the instructor with a dependent.
5. Open the detail of the back-office person with a dependent.
6. Check the graduation, the class, the emergency contact, and the address.

### Round 3: the administrative upgrade
1. Pick the plain student flagged for the administrative upgrade.
2. Assign the administrative operational role through the interface.
3. Log out/log in with the same account.
4. Confirm that the management area appeared.
5. Remove the operational role.
6. Log out/log in again.
7. Confirm that the management area stopped appearing and that the student area remained.

### Round 4: controlled deletion
1. Pick the student flagged as the deletion candidate.
2. Open the detail, confirm the dependencies shown.
3. Delete through the interface.
4. Confirm that they no longer appear in the list.
5. Try to log in with the deleted or removed account, according to the current flow's expected behavior.
6. Validate that the related dependents/guardians remained consistent.

### Round 5: martial and health coverage
1. Filter/open the people with each blood type.
2. Open the people with no martial experience and confirm that they do not display an improper belt.
3. Open the people with other disciplines and confirm the discipline/textual graduation.
4. Open the people with kids, adult, coral, and red belts.
5. Check that the allergies, injuries, emergency contact, and address show up complete.

## Risks and edge cases
- Running the commands out of order can fail because of a missing class or relationship target.
- People with no experience must not receive a fake graduation just to fill a field.
- Stackable operational roles can change the home according to recent PRDs; the visual script must record the observed behavior with a date.

## Plan
1. [x] Read the contracts, the models, the base seeds, and the official Django source.
2. [x] Create the common importer and the commands.
3. [x] Create the staging JSONs.
4. [x] Create the focused test.
5. [x] Update the seed documentation.
6. [x] Run the local validations.
7. [x] Review the diff and record the cleanup.

## Execution evidence
- Created `system/services/test_seed_fixtures.py` with an idempotent common importer.
- Created the manual commands:
  - `seed_system_initial_test_students`
  - `seed_system_initial_test_guardians`
  - `seed_system_initial_test_administrative`
  - `seed_system_initial_test_teachers`
- Created the JSONs:
  - `static/initial_data/seed_system_initial_test_students.json` with 13 entries.
  - `static/initial_data/seed_system_initial_test_guardians.json` with 6 entries.
  - `static/initial_data/seed_system_initial_test_administrative.json` with 6 entries.
  - `static/initial_data/seed_system_initial_test_teachers.json` with 6 entries.
- Updated `docs/OPERACAO-BANCO-SEEDS.md` with the local staging commands and the fake password `LvTest@2026`.
- Updated `docs/prd/README.md` with PRD-111.

## Visual validation
- Pending, to be run later one by one, per the checklist above.
- The registrations were loaded into the local database on 2026-07-01 to enable the browser validation.

## ORM validation
- The local command run:
  - `.venv/Scripts/python.exe manage.py shell -c "..."`
- Result:
  - `people 31`
  - `enrollments 17`
  - `relationships 11`
  - `roles 17`
  - `assignments 9`

## Quality validation
- `.venv/Scripts/python.exe manage.py test system.tests.test_test_seed_fixtures --verbosity 2` — 2 tests OK.
- `.venv/Scripts/python.exe manage.py check` — 0 problems.
- The local run of the new commands:
  - `seed_system_initial_test_students` — 13 created, 13 accounts, 2 relationships.
  - `seed_system_initial_test_guardians` — 6 created, 6 accounts, 7 relationships.
  - `seed_system_initial_test_administrative` — 6 created, 6 accounts, 13 roles, 1 relationship.
  - `seed_system_initial_test_teachers` — 6 created, 6 accounts, 6 class assignments, 1 relationship.

## Evidence
- The real evidence is recorded in Execution evidence, ORM validation, and Quality validation.

## Implemented
- Extensive local fixture JSONs covering 31 fictitious people.
- A common importer with `Person`, `PortalAccount`, `Graduation`, `ClassEnrollment`, `PersonOperationalRole`, `ClassInstructorAssignment`, and `PersonRelationship`.
- Four manual, idempotent Django commands.
- An automated contract and idempotency test.
- A paused, controlled visual validation script.

## Cleanup findings
- The scope's diff reviewed: the service, the commands, the JSONs, the focused test, the PRD, and the seed documentation.
- A cleanup adjustment applied: long lines wrapped in `system/services/test_seed_fixtures.py` and `system/tests/test_test_seed_fixtures.py`.
- A residual finding outside the scope: `docs/prd/README.md` already existed as an untracked file and did not list PRD-101 through PRD-110 in the table; this task only added PRD-111, without normalizing the pre-existing entries.

## Follow-up PRDs
- Pending only if the visual validation finds a UX failure or a rule outside the fixtures' scope.

## Deviations from plan
- No functional deviation. The naming uses `guardians` instead of `responsaveis` to keep the file and command names in English and aligned with the `guardian` domain term.

## Pending
- The manual visual validation in the browser, one possibility at a time, per the checklist.

## Final status
Completed with limitations.
