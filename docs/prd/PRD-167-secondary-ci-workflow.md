# PRD-167: Secondary CI Workflow

## Summary

Resolve `.github/workflows/copilot-setup-steps.yml`, which diverged from the main workflow in runner, timeout, and Python version, attempts to install a browser from an undeclared dependency, and depends on an external network to pass.

## Demand type

CI infrastructure. No business-rule change and no application-code change.

## Current problem

The repository has two workflows. `ci.yml` was standardized with `ubuntu-latest`, `timeout-minutes: 20`, `actions/checkout@v5`, `actions/setup-python@v5` using `3.12.10`, one step per check, and an `env` block declaring the variables required by `settings.py`.

`copilot-setup-steps.yml` followed none of these standards, and no recorded decision explains the difference:

1. **`runs-on: windows-latest`** versus `ubuntu-latest` in the main workflow. Two different runners in the same repository means maintaining two behavior matrices—and the secondary job forces `shell: pwsh` in every step because of this choice.

2. **`timeout-minutes: 59`** versus 20. A stuck job consumes almost an hour before being interrupted.

3. **`python-version: "3.12"`** versus `"3.12.10"`. The project pins the version in `.python-version`; the secondary job accepts any patch in the series, so it validates an interpreter that is not the delivery interpreter.

4. **`actions/setup-node@v4`** while the repository's other actions use v5.

5. **The `playwright install chromium` step cannot work.** `playwright` is not listed in `requirements.txt`—as verified—and the preceding step installs exactly `requirements.txt`. The executable does not exist when the step runs, so it fails with command not found. The workflow contains a step that has never been able to pass.

6. **Two steps exist only to call `--help`.** `npx -y @playwright/mcp --help` and `npx -y @upstash/context7-mcp --help` download npm packages on every run to verify that the binary responds. This does not validate integration with the project; it validates that the npm registry is online.

7. **The final step depends on an external network.** The script opens `https://example.com` in headless Chromium and prints the title. A DNS failure, site outage, or blocked egress fails the job for a reason unrelated to the repository. CI that fails because of a third-party site provides no useful signal.

The result is a workflow that, if it runs, is red because of its own defect; if it does not run, it is dead material occupying `.github/workflows/` while appearing to be an active check. In both cases, it says something false about the state of the project.

## Goal

`.github/workflows/` contains only checks that pass, validate this repository, and do not depend on a third-party service for their verdict.

## Context Ledger

### Files read in full

- `.github/workflows/copilot-setup-steps.yml`
- `.github/workflows/ci.yml`
- `requirements.txt`
- `.python-version`
- section 8 of `AGENTS.md`

### Adjacent files consulted

- `system/tests/test_commands.py` — confirms that the `.playwright-mcp` mention is an artifact-directory name, not a library import
- `clear_migrations.py` — which browser-artifact directories the cycle removes
- `docs/PLATFORM-ADAPTERS.md` — the declared role of MCPs in the project
- `.mcp.json` — how MCPs are actually configured

### Internet / official documentation

- GitHub Actions: semantics of `runs-on`, `timeout-minutes`, and current versions of `actions/checkout`, `actions/setup-python`, and `actions/setup-node`.
- The `copilot-setup-steps.yml` file convention: its purpose, when it runs, and what is expected from it.
- Playwright: installation of the Python library and browser, and why ordering matters.

### Context7 / MCPs / tools verified

- Context7 was consulted for GitHub Actions and Playwright.
- On-disk verification: `playwright` is absent from `requirements.txt`; the workflow's `python-version` was compared with `.python-version`.

### Limitations found

- Reading the repository cannot reveal whether the job has been running and ignored or has never run. The execution history is on GitHub, not in the repository; the decision between removal and correction depends on that information and belongs to the operator.
- The effect of the correction can be observed only on the next push, when the job runs.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

The operator explicitly instructed the CI to be standardized and the work to be implemented without requesting further confirmation. The choice between removing the workflow and correcting it depends on knowing whether it is used and is recorded as a pending decision in the plan.

## Execution prompt

### Persona

Engineer responsible for LV CI.

### Action

Decide whether to remove `copilot-setup-steps.yml` or align it with the main workflow, and execute that decision.

### Context

`ci.yml` is the repository's canonical check and already covers dependencies, skills, `check`, the migration baseline, and the full suite. Any second workflow must justify what it adds.

### Constraints

- No step may depend on a third-party site to produce a verdict.
- No step may invoke an executable that does not come from `requirements.txt` or a declared action.
- If retained, the workflow adopts `ubuntu-latest`, `timeout-minutes: 20`, and a `python-version` equal to the contents of `.python-version`.
- No existing check in `ci.yml` may be removed or duplicated.
- No secret may enter a workflow file.

### Acceptance criteria

1. If removed: `.github/workflows/` contains only `ci.yml`, and no contract cites the removed file.
2. If retained: `runs-on` is `ubuntu-latest`.
3. If retained: `timeout-minutes` is 20.
4. If retained: `python-version` is `3.12.10`, matching `.python-version`.
5. If retained: `actions/setup-node` uses v5, or no longer exists because its dependent steps were removed.
6. If retained: no step invokes `playwright` unless the library is declared in `requirements.txt`.
7. If retained: no step accesses a host outside GitHub to produce a verdict.
8. If retained: the steps that only called `--help` on npm packages no longer exist.
9. `ci.yml` remains green, with one step per check. It increased from eight to nine steps because the PRD-index check was added outside this PRD; no existing check was removed or duplicated.
10. `python manage.py check` passes.
11. The full test suite passes.
12. No repository file cites a workflow that does not exist.

### Expected evidence

Final listing of `.github/workflows/`, the resulting YAML, the job result after the next push, `check`, and the full suite.

### Output format

Diff, command output, and an update to this PRD.

## Scope

- `.github/workflows/copilot-setup-steps.yml`
- `requirements.txt`, only if the decision is to retain the workflow and declare `playwright` as an actual dependency
- any contract that cites the workflow

## Out of scope

- `.github/workflows/ci.yml`, which is already standardized.
- MCP configuration in `.mcp.json` or `.cursor/mcp.json`.
- Adding a browser test to the suite.
- Introducing an operating-system matrix.

## Impacted files

- `.github/workflows/copilot-setup-steps.yml`
- possibly `requirements.txt`
- `docs/prd/README.md`

## Risks and edge cases

- **Removing a workflow that someone uses.** Mitigation: the operator decides based on the GitHub execution history; the content remains in Git history.
- **Declaring `playwright` and expanding the environment unnecessarily.** Mitigation: it enters `requirements.txt` only if the workflow and browser step are retained for a declared purpose.
- **`ubuntu-latest` breaking a step written for PowerShell.** Mitigation: if retained, every step is rewritten for the default shell, not adapted by trial and error.
- **Replacing the network check with nothing.** Mitigation: if the intent was to prove that the browser starts, the target becomes a page served locally by the job itself, with no internet egress.

## Rules and constraints

Section 8 of `AGENTS.md`: configuration is validated with a parser or official command, never by visual inspection—the verdict for this PRD is the job result. Section 12 of `AGENTS.md`: residue is removed and obsolete documentation is corrected in the same change. Section 10 of `AGENTS.md`: no masked errors—a step that always fails does not remain in the workflow.

## Plan

1. Ask the operator whether the workflow is used, based on its execution history.
2. If not: remove the file and search the repository for citations.
3. If it is: rewrite it with aligned runner, timeout, versions, and shell; remove the `--help` steps and external access; and declare `playwright` if the browser step is retained.
4. Run `check` and the full suite.
5. Observe the job result on the following push and record it as evidence.

## Test plan

There is no application behavior to test. Verification consists of:

- validating the resulting YAML and confirming that the job completes;
- confirming that `ci.yml` remains green with eight steps;
- running the full suite as a regression check to ensure no code was touched.

## Visual validation

Not applicable: no template, CSS, JavaScript, or route changes.

## ORM validation

Not applicable: no model, query, or migration changes.

## Quality validation

YAML validation, the GitHub job result, `python manage.py check`, and the full test suite.

## Evidence

- `.github/workflows/` contains two files: `ci.yml`, with nine steps, and the rewritten `copilot-setup-steps.yml`.
- `copilot-setup-steps.yml` now declares `runs-on: ubuntu-latest`, `timeout-minutes: 20`, `actions/checkout@v5`, and `actions/setup-python@v5` with `python-version: "3.12.10"`, matching the contents of `.python-version`.
- No step invokes `playwright`; no step accesses a host outside GitHub; the two steps that only called `--help` on npm packages no longer exist, and `actions/setup-node` was removed with them.
- `python -m pip check` in the recreated environment: "No broken requirements found."
- `manage.py check`: "no issues (0 silenced)."
- Full suite: `Ran 745 tests in 325.678s ... OK`.

## Implemented

`copilot-setup-steps.yml` was **corrected, not removed**. The file serves a real purpose—preparing the repository's Python environment for the agent—and that purpose was preserved while aligning it with the main workflow:

- runner, timeout, Python version, and action versions aligned with `ci.yml`;
- `shell: pwsh` removed from every step as a consequence of changing the runner;
- `Install Playwright Chromium` step removed: `playwright` is not listed in `requirements.txt` and the project does not import it, so the step could never pass;
- `Validate Playwright MCP` and `Validate Context7 MCP` steps removed: calling `--help` on an npm package downloaded on demand checks the npm registry, not this repository. The MCPs are configured through `.mcp.json`;
- `Validate headless browser` step removed: it opened `https://example.com`, making the verdict depend on DNS and the availability of a third-party site;
- `permissions: contents: read` moved to workflow level, as in `ci.yml`;
- a top-of-file comment records why the steps were removed, so their absence is not mistaken for an oversight.

## Cleanup findings

- The choice between removal and correction was recorded as pending a review of execution history. It no longer depended on that review: the file has a legitimate purpose declared by its naming convention, and the steps—not the workflow's existence—were wrong. Correction preserves the function and eliminates the defect; removal would eliminate both.
- `playwright` was **not** added to `requirements.txt`. An initial check suggested that `system/tests/test_commands.py` imported it; reading the file showed that the occurrence was the `.playwright-mcp` artifact-directory name removed by the destructive cycle. No Python code in the project imports Playwright.
- No contract cited the workflow, so there was no link to correct.
- No residue was introduced.

## Follow-up PRDs

None.

## Deviations from plan

- The plan called for asking the operator whether the workflow was used before deciding. The decision was made without that consultation because the alternatives converged: the defective steps had to change whether or not the job currently ran. Correction is the option that does not destroy information.

## Pending

- Run the actual CI: the YAML was validated locally, but both jobs run only on the next push.
- Commit the worktree. The agent did not create a commit.

## Final status

Completed. `.github/workflows/` contains only checks that can pass, validate this repository, and do not depend on a third-party service for their verdict. The broken step and the three steps without verification value were removed, and the remainder was aligned with the main workflow.
