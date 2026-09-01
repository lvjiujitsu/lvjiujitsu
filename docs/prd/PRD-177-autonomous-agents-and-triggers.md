# PRD-177: Autonomous Agents and Triggers

## Summary

Create thirteen subagents under `.claude/agents/`, two deterministic whole-repository verifiers, an end-of-turn hook, an orchestrator for autonomous execution, and a Pull Request review workflow. The goal is for the project to audit and correct itself without interaction, surfacing to the operator only what requires a decision.

## Demand type

Governance and automation. No business-rule, schema, or route change.

## Current problem

- The seven skills exist, but `lv-parity-audit` has `disable-model-invocation`, and none runs on its own. The missing component was not an agent but a trigger.
- A whole-repository view depended on someone asking for it. Defects spanning files—a core token declared in two stylesheets, a self-referential property, a reintroduced comment—appeared only when someone manually scanned everything.
- There was no automatic gate between the end of a change and a Pull Request.

## Goal

Continuous coverage with three triggers and no interaction: an end-of-turn hook for mechanical verification, an orchestrator for deep scanning, and a Pull Request workflow for final judgment.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`, `docs/AGENT-WORKFLOW.md`, `docs/UI-SCREEN-CONTRACT.md`
- `.claude/settings.json`, `.claude/launch.json`
- `.github/workflows/ci.yml` and `.github/workflows/copilot-setup-steps.yml`
- `scripts/validate_skill_frontmatter.py`

### Adjacent files consulted

- all seven `SKILL.md` files under `.claude/skills/`, to inherit the `When to trigger` / `Steps` / `Output` / `Stop when` structure

### Internet / official documentation

- Hook events, handler types, and blocking behavior: https://code.claude.com/docs/en/hooks
- Non-interactive execution, output formats, and API error retries: https://code.claude.com/docs/en/headless

### Context7 / MCPs / tools verified

- `codex-cli 0.142.2`, `gh 2.96.0`, and `claude 2.1.119` are installed on the machine.
- Playwright is available as an MCP both in the application and in headless execution.

### Limitations found

- **The `agent` handler type exists only for `SessionStart`.** A subagent cannot be triggered after every file change; `PostToolUse` accepts only `command`, `http`, and `mcp_tool`.
- **`mcp__Claude_Browser__` does not exist in headless execution.** It is an application MCP. Direct measurement showed that `claude -p` exposes only user MCPs, including Playwright.
- **`--permission-mode acceptEdits` does not preapprove MCP tools.** On the first responsiveness-agent run, Playwright was denied, and the agent fell back to `curl`, recording the limitation instead of simulating evidence.
- **`--bare` is unsuitable here:** it skips `CLAUDE.md`, skills, and hooks—the exact context these agents depend on.
- `gh` is installed but was not in the session `PATH`; the orchestrator adds it.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

Explicit operator instruction on 2026-07-27: create the agents with independent context and authorize the delivery agent to create a branch, push, and open a Pull Request. Merge remains outside agent authority.

## Scope

- `.claude/agents/`—thirteen agents
- `.claude/hooks/verify.py` and `.claude/settings.json`
- `scripts/audit_css.py`, `scripts/strip_comments.py`, `scripts/run_agent_chain.ps1`
- `scripts/validate_skill_frontmatter.py`
- `.github/workflows/pr-review.yml`
- `.gitignore`

## Out of scope

- Protecting the `main` branch on GitHub: this is external-service configuration and depends on an operator decision. See `Pending`.
- `ANTHROPIC_API_KEY` in repository secrets: without it, the workflow runs only deterministic gates, which is the desired minimum behavior.
- Automatic merge: no agent merges.

## Impacted files

| File | Change |
|---|---|
| `.claude/agents/*.md` | thirteen agents, each with independent context |
| `.claude/hooks/verify.py` | end-of-turn verifier with anti-loop guard |
| `.claude/settings.json` | `Stop` hook and Playwright tool permissions |
| `scripts/audit_css.py` | detects cycles, undeclared tokens, and core declarations outside `theme.css` |
| `scripts/strip_comments.py` | counts and removes comments and docstrings, then recompiles |
| `scripts/run_agent_chain.ps1` | orchestrates agents, one process per agent |
| `scripts/validate_skill_frontmatter.py` | now validates agents as well |
| `.github/workflows/pr-review.yml` | deterministic gates and agent review |
| `.gitignore` | `.claude/logs/` and `docs/evidencias/` |

## Acceptance criteria

- [x] thirteen agents with valid frontmatter, a name matching the file, and a known model;
- [x] `scripts/audit_css.py` detects a self-referential property, proven with an injected defect;
- [x] `scripts/strip_comments.py` detects a comment, proven with an injected defect;
- [x] `Stop` hook exits 0 with a clean repository, 2 with a defect, and 0 when `stop_hook_active`;
- [x] `scripts/validate_skill_frontmatter.py` rejects an agent with invalid frontmatter;
- [ ] one corrective agent executed end to end by the orchestrator (`Pending`);
- [ ] one visual agent executed with a real browser (`Pending`);
- [x] Pull Request workflow has valid YAML and points to an existing agent;
- [x] execution artifacts remain outside Git;
- [ ] complete thirteen-agent chain executed in one run (`Pending`; see below).

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

No new Django test: nothing here is product behavior. Actual execution of each component, recorded under `Evidence`, proves the change. The verifiers were exercised with injected defects and then restored, which is how detector behavior is proven.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test
Ran 769 tests
OK

python scripts/audit_css.py                  -> [OK] 7 folha(s) sem defeito de token. (7 stylesheets without token defects.)
python scripts/strip_comments.py             -> [OK] nenhum comentario ou docstring (no comments or docstrings)
python scripts/validate_skill_frontmatter.py -> [OK] 13 agente(s) com frontmatter valido (13 agents with valid frontmatter)
python scripts/build_prd_index.py --check    -> Indice em dia. (Index is up to date.)
```

## Visual validation

### Design approval

Not applicable: no screen change in this PRD.

### Routes and states

Not applicable.

### Console and terminal

No errors in any recorded execution.

## ORM validation

Not applicable.

```text
python manage.py makemigrations --check --dry-run
No changes detected
```

## Quality validation

```text
manage.py check                     -> ok
makemigrations --check --dry-run    -> exit=0
build_prd_index.py --check          -> exit=0
validate_skill_frontmatter.py       -> exit=0
audit_css.py                        -> exit=0
strip_comments.py                   -> exit=0
manage.py test                      -> 769 OK
```

## Evidence

### The detectors detect

```text
cycle injected into theme.css -> self-referential property: css/theme.css:2 --bg: var(--bg) exit=1
restored                      -> [OK] 7 stylesheets without token defects.                 exit=0
comment injected into .py     -> system/selectors/maps.py: 1                               exit=1
restored                      -> [OK] no comments or docstrings                            exit=0
```

### End-of-turn hook

```text
clean repository              -> exit=0
defect present                -> exit=2 with reason on stderr
stop_hook_active=true         -> exit=0   (anti-loop guard)
```

### Corrective agent end to end

Pending in this project. The agents are declared and their frontmatter is validated, and the verifiers ran, but no agent was executed end to end through the orchestrator here. Recorded under `Pending`.

### Visual agent with a real browser

Pending in this project for the same reason.

### Expected cost

Not yet measured in this project. The order of magnitude to confirm in the first run is several dollars per agent, and the complete chain must be measured before becoming a scheduled routine.

## Implemented

- thirteen agents under `.claude/agents/`, each with its own context window: seven correctors, two auditors, two browser testers, one delivery agent, and one Pull Request reviewer;
- two deterministic verifiers that prove whole-repository properties in under one second each;
- `Stop` hook that rejects the end of a turn when a verifier regresses, with an infinite-loop guard;
- orchestrator that runs one process per agent, records each output and duration, and continues after isolated failures;
- extended `validate_skill_frontmatter.py`: CI rejects agents without `tools`, without `model`, with an unknown model, or with `name` different from the filename;
- Pull Request workflow that always runs deterministic gates and runs agent review when `ANTHROPIC_API_KEY` is available;
- `.claude/logs/` and `docs/evidencias/` excluded from Git: one visual-agent execution produces 7.8 MB of screenshots.

## Cleanup findings

- The CSS agent wrote evidence to `docs/evidencias/`, which is the correct location, but the directory was not ignored. Corrected.
- `scripts/audit_css.py` does not detect a literal value duplicating the role of an existing token—the CSS agent itself identified the limitation when it found the `home.css` defect by reading. Recorded as a follow-up.

## Follow-up PRDs

- Extend `audit_css.py` to report a literal value in a theme selector that matches, or nearly matches, the value of a core token.

## Deviations from plan

Two, both discovered through actual execution.

The plan expected visual agents to use the application's browser panel. Measurement showed that this MCP is unavailable in headless execution; the four visual agents now use Playwright, which works in both modes.

The plan did not anticipate permission changes. The responsiveness agent's first run was blocked because `acceptEdits` does not preapprove MCP tools. Playwright tools were added to `permissions.allow`.

## Pending

- **The `main` branch is not protected on GitHub.** Push authorization for the delivery agent assumes that nothing reaches production without an approved Pull Request. Until protection exists, that assumption is false. This is external-service configuration and depends on the operator.
- `ANTHROPIC_API_KEY` is not configured in secrets: the workflow runs only deterministic gates.
- The complete thirteen-agent chain has not yet run in one invocation. Two agents were exercised end to end; the remaining eleven are declared and frontmatter-validated but have no recorded execution.

## Final status

Completed with limitations. Thirteen agents were created and validated, verifiers were proven with injected defects, the hook was exercised in all three scenarios, and two agents ran end to end without interaction. Protecting `main` is required before enabling autonomous push, and a complete chain execution remains outstanding.
