# PRD-071: Aligning the legacy suite with the progressive scope

## Summary
Record PRD-070's finding: LV's full suite still contains tests for modules/templates removed in the progressive reset, while the current stage recreated only Login and the Home.

## Problem
`manage.py test --verbosity 2` ran 226 tests. The result was 217 OK and 9 errors from `TemplateDoesNotExist`/a missing file in old contracts:

- `calendar` expects the calendar template.
- `people` expects the People list/detail templates.
- `plans` expects the plan templates.
- `register` expects `templates/login/register.html`.

Those modules were not recreated at this stage and must not be masked by silent skips.

## Goal
Decide on and execute one of the strategies:

1. Remove or archive the legacy tests of the modules not yet reimplemented.
2. Recreate minimal contracts per module when each progressive PRD authorizes that module.
3. Separate the suites per stage (`current_scope` vs `legacy_future_scope`) so the regression status reflects the real scope.

## Out of scope
- Recreating the complete People, Plans, Calendar, or public Registration modules in this PRD.
- Creating silent skips with no traceability.
- Changing the history of old PRDs.

## Evidence
- `manage.py test system.tests.test_home_dashboard system.tests.test_admin_hubs_contract --verbosity 2`: 3 tests OK.
- `manage.py test --verbosity 2`: 226 tests, 9 errors in the contracts of removed templates.

## Acceptance criteria
- The suite proportional to the progressive scope runs green.
- The remaining legacy tests are explicitly separated, removed, or linked to future PRDs.
- No test points at a non-existent template without a scope decision.

## Final status
Recorded for a later decision.
