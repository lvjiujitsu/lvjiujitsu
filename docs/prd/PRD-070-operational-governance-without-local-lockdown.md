# PRD-070: Operational governance without a local lockdown

## Summary
Remove from LV JIU JITSU's active contracts the policy that blocked tests, the local ORM, migrations, migrate, a local reset, and seeds until a new authorization, adopting `http://localhost:8000` as the canonical local URL and keeping barriers only for remote environments, production, external payments, deploy, and push.

## Demand type
Governance + operational Django + visual validation.

## Goal
Allow agents to run the complete local cycle needed to deliver the requested goal, including tests, migrations, seeds, admin creation, and authenticated visual validation.

## Context Ledger
- `AGENTS.md`
- `CLAUDE.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `.agents/skills/lv-task-intake/SKILL.md`
- `.agents/skills/lv-prd/SKILL.md`
- `.agents/skills/lv-ui-delivery/SKILL.md`
- `.agents/skills/lv-django-delivery/SKILL.md`
- `.agents/skills/lv-cleanup-audit/SKILL.md`
- `.claude/skills/lv-*`
- `.cursor/skills/lv-*`
- `.cursor/rules/*.mdc`
- `.claude/settings.json`
- `.claude/launch.json`

## Official documentation
- Context7 `/websites/djangoproject_en_5_2`: `migrate` applies the migrations and creates the tables; the test runner uses a separate test database; management commands go through `manage.py`.

## Approval
The user explicitly authorized: seeds, migrations, any command, tests, admin creation, and visual validation.

## Scope
- LV's active governance.

- The local execution of the LV cycle up to an authenticated Home.

## Out of scope
- Changing the history of old PRDs that record past evidence.
- Deploy, push, HG/production, or real external payments.
- Exposing secrets from `.env`.

## Acceptance criteria
- The active documents do not require a new authorization for local tests, the local ORM, local migrations, a local migrate, a local reset, and local seeds when the task asks for an operational delivery.
- The canonical local URL documented as `http://localhost:8000`.
- `http://lv.localhost:8000` does not render the LV application as an alternative host.
- The LV skills synchronized across `.agents`, `.claude`, and `.cursor`.

- LV runs `makemigrations`, `migrate`, the necessary seeds, `create_admin_superuser`, proportional tests, and visual validation at `localhost:8000`.

## Evidence
- Context7 `/websites/djangoproject_en_5_2`: `migrate` applies the migrations and creates the tables; the test runner uses a separate test database.
- An active search found no `lv.localhost`, `127.0.0.1`, `testes somente` (`tests only`), `somente sob autorização` (`only with authorization`), `não executar testes` (`do not run tests`), or `não executado por política` (`not executed by policy`) in active contracts outside historical PRDs.
  The exact Portuguese search patterns mean "tests only," "only with authorization," "do not run tests," and "not executed due to policy," respectively.
- The hash of the LV skills: `.agents`, `.claude`, and `.cursor` synchronized for `lv-task-intake`, `lv-prd`, `lv-ui-delivery`, `lv-django-delivery`, `lv-cleanup-audit`, and `lv-prompt-builder`.
- The hash of the skills: `.agents`, `.claude`, and `.cursor` synchronized for `lv-task-intake`, `lv-prd`, `lv-ui-delivery`, `lv-django-delivery`, and `lv-cleanup-audit`.
- `manage.py makemigrations`: created `system/migrations/0001_initial.py`.
- `manage.py test system.tests.test_home_dashboard system.tests.test_admin_hubs_contract --verbosity 2`: 3 tests OK.
- `manage.py migrate`: applied every migration, including `system.0001_initial`.
- `manage.py create_admin_superuser`: the admin created; then restored by the same command after the visual validation.
- `seed_system_initial_person_type`: 5 types created.
- `seed_system_initial_belt_ranks`: 13 belts created.
- `seed_system_people_flow_samples`: 5 sample people created/updated.
- The local ORM: 1 user, 1 superuser, 5 person types, 5 people, 13 belts, and 1 class.
- `manage.py check`: 0 issues.
- `manage.py showmigrations system`: `[X] 0001_initial`.
- The browser at `http://localhost:8000/login/`: a real login with the temporary local admin.
- The browser at `http://localhost:8000/home/`: the authenticated Home rendered with no console errors.
- `settings.ALLOWED_HOSTS`: `['127.0.0.1', 'localhost']`, with no wildcard in the local environment.
- `manage.py test system.tests.test_settings_hosts --verbosity 2`: 2 tests OK.
- `http://localhost:8000/`: 200, the title `LV Jiu Jitsu | Acesso` (`LV Jiu Jitsu | Access`).
- `http://lv.localhost:8000/`: 400 for an invalid host.
- Screenshots:
  - `test_screenshots/prd-070-home-validation/desktop-light.png`
  - `test_screenshots/prd-070-home-validation/desktop-dark.png`
  - `test_screenshots/prd-070-home-validation/mobile-light.png`
  - `test_screenshots/prd-070-home-validation/mobile-dark.png`
- Visual metrics: desktop and mobile with no horizontal overflow; the `Pessoas` (`People`) and `Django Admin` quick links; the `Branca · 4º` (`White · 4th`), `Azul · 1º` (`Blue · 1st`), and `Preta · 1º` (`Black · 1st`) badges.
- `manage.py test --verbosity 2`: 226 tests run; 217 OK and 9 errors from old contracts still pointing at templates removed outside the progressive scope (`calendar`, `people`, `plans`, `register`).

## Implemented
- LV's active governance updated in `AGENTS.md`, `CLAUDE.md`, `docs/AGENT-WORKFLOW.md`, `docs/OPERACAO-BANCO-SEEDS.md`, `docs/PLATFORM-ADAPTERS.md`, `docs/UI-SCREEN-CONTRACT.md`, the skills, the Cursor rules, and the Claude launch config.
- The active governance updated, including `.claude/settings.json`.
- The bootstrap updated so it does not reintroduce the local lockdown.
- The canonical local URL documented as `http://localhost:8000`.
- LV's local operational cycle run up to the admin + an authenticated Home.

## Cleanup findings
- The historical PRDs keep their old evidence and were not rewritten.
- The full suite's failures are legacy from modules/templates removed outside the current PRD; they were not masked.
- A follow-up recorded in `docs/prd/PRD-071-alignment-of-the-suite-inherited-to-the-progressive-scope.md`.
- The admin had a temporary local password only for the visual login and was restored through `create_admin_superuser`.

## Final status
Completed, with a legacy suite finding outside the progressive scope.
