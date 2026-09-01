# PRD-082: README and requirements-dev aligned with LV

## Summary
Fix the onboarding and the documented commands. `CLAUDE.md` cites `requirements-dev.txt`, but the file does not exist; `README.md` describes a generic kit and Cursor rules that do not match the current repo.

## Demand type
Documentation governance + configuration.

## Current problem
- `CLAUDE.md` recommends `.\.venv\Scripts\pip.exe install -r requirements-dev.txt`.
- `requirements-dev.txt` does not exist.
- `README.md` describes neither the LV product nor the real operational flow.

## Goal
Have a correct minimal onboarding:
- an LV README;
- an explicit decision about `requirements-dev.txt`;
- local commands coherent with `CLAUDE.md` and `docs/OPERACAO-BANCO-SEEDS.md`.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `requirements.txt`

### Adjacent files consulted
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/PLATFORM-ADAPTERS.md`

### Internet / official documentation
Not applicable.

### Context7 / MCPs / tools verified
- PowerShell.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
Authorized by the current request.

## Scope
- Replace the generic README.
- Create `requirements-dev.txt` or remove the reference from `CLAUDE.md`.
- Validate the documented commands.

## Out of scope
- Changing production dependencies without need.

## Impacted files
- `README.md`
- `CLAUDE.md`
- `requirements-dev.txt`

## Risks and edge cases
- Duplicating dependencies may misalign the environments.
- The README must not expose secrets or destructive remote commands.

## Plan
- [x] Decide whether the dev requirements file is necessary.
- [x] Update the README.
- [x] Validate the installation/proportional checks.

## Test plan
### Tests to author
Not applicable.

### Execution authorization
Authorized locally.

### Execution evidence
- `rg -n "requirements-dev" --no-ignore -g '!staticfiles/**' -g '!docs/prd/PRD-059*' -g '!docs/prd/PRD-082*' .` → only `CLAUDE.md:59` and `README.md:41`, both referencing the now-existing file.
- `.\.venv\Scripts\python.exe manage.py check` → `System check identified no issues (0 silenced).`
- `.\.venv\Scripts\pip.exe install -r requirements-dev.txt` → the installation completed successfully (`Successfully installed PyYAML-6.0.2`), with no conflict with `requirements.txt`.

## Visual validation
Not applicable.

## ORM validation
Not applicable.

## Quality validation
- `rg requirements-dev`
- the applicable check command.

## Evidence
- The subagent confirmed the reference to a non-existent file.
- `requirements.txt` read in full: 49 production dependencies, with no governance validation tool (PyYAML) among them.
- PRD-059 had already decided to create `requirements-dev.txt` with PyYAML for the skills validator, but the file never came to exist in the working tree (likely lost before the commit). This PRD reapplies that decision.

## Implemented
- `requirements-dev.txt` created at the root with `-r requirements.txt` plus `PyYAML==6.0.2`, aligned with the decision recorded in PRD-059 (the dependency used by the skills validator).
- `README.md` replaced (it described the generic/Cursor governance kit) with a README specific to LV JIU JITSU: the product, the stack, the `system/` structure, the local setup, useful commands, agent governance, and documentation links coherent with `CLAUDE.md` and `docs/OPERACAO-BANCO-SEEDS.md`.
- `CLAUDE.md` was not changed: the reference to `.\.venv\Scripts\pip.exe install -r requirements-dev.txt` (line 59) now points at an existing file, so no correction was needed there.

## Cleanup findings
- No residue introduced. No other file referenced the generic README or depended on the old content.
- No additional material debt was found within this PRD's scope that would justify a new follow-up PRD.

## Follow-up PRDs
None.

## Deviations from plan
- No deviation from the PRD's original plan.

## Pending
- No pending items in this scope. Installing `requirements-dev.txt` remains optional and is only necessary when the local environment is going to run the skills validator (PyYAML), as already documented in `docs/PLATFORM-ADAPTERS.md`.

## Final status
Completed.
