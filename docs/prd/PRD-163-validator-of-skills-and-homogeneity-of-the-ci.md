# PRD-163: Skill Validator and CI Homogeneity

## Summary

Create `scripts/validate_skill_frontmatter.py` and connect it to LV CI. This is the final CI-heterogeneity item, recorded as follow-up by PRD-162.

## Demand type

Governance and CI. No business-rule change.

## Current problem

The validator must check skills in CI: it requires all three platform directories, the same skill set in each, byte-for-byte content identical to `.claude/skills/`, and intact Codex metadata using UTF-8 with LF.

LV does not have the script. Its `.github/workflows/ci.yml` runs `manage.py check`, `makemigrations --check`, and the suite, but validates no skill. The mirroring rule exists in `docs/PLATFORM-ADAPTERS.md` and `.claude/commands/sync-skills.md` and depends on someone remembering to run the comparison manually.

The risk is not hypothetical: an `agents/openai.yaml` file can be corrupted with replacement characters and still be declared normalized, because a check that only verifies that YAML is parseable does not see it. Only a byte-level and encoding-level check defends against that.

## Goal

LV fails the build when a skill disappears from one platform, diverges from the source, or has corrupted Codex metadata — the same defense already used by the other two.

## Context Ledger

### Files read in full

- `.github/workflows/ci.yml`
- `.claude/commands/sync-skills.md`
- `docs/PLATFORM-ADAPTERS.md`
- All six `.claude/skills/*/SKILL.md` files
- All six `.agents/skills/*/agents/openai.yaml` files

### Adjacent files consulted

- `requirements.txt` (PyYAML)
- `.gitattributes`
- `docs/prd/PRD-162-hardened-remote-reset-documented-deployment-and-observability.md`

### Internet / official documentation

- [Claude Code — Agent Skills](https://docs.claude.com/en/docs/claude-code/skills)
- [GitHub Actions — `actions/setup-python`](https://github.com/actions/setup-python)

### Context7 / MCPs / tools verified

- Context7 available. Script uses only the standard library and PyYAML, already present in `requirements.txt`.

### Limitations found

- The job itself runs only on the next push; validation here is local.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: repository CI audit and follow-up recorded by PRD-162.
- User approval: explicit operator order on 2026-07-25 requesting complete parity after executing the PRDs.
- Date: 2026-07-26.

## Execution prompt

### Persona

Owner of LV multiplatform governance.

### Action

Create the validator with `lv-*` names and connect it to CI.

### Context

The projects share a governance framework. A rule nobody checks diverges again.

### Constraints

- Do not change the six already synchronized `SKILL.md` files.
- Script runs cross-platform without PowerShell dependency.

### Acceptance criteria

- [ ] `scripts/validate_skill_frontmatter.py` exists and validates frontmatter, coverage across all three platforms, content identical to source, and Codex metadata integrity.
- [ ] Script reports six skills on three platforms and 18 validated files.
- [ ] Script fails when an `openai.yaml` receives a replacement character. Verification: introduce corruption, observe failure, restore.
- [ ] `.github/workflows/ci.yml` runs the script and pins Python `3.12.10`.
- [ ] `manage.py check` passes and the suite is green.

### Expected evidence

Script output; encoding-regression test output; workflow diff.

### Output format

Diff and PRD updated with actual evidence.

## Scope

- `scripts/validate_skill_frontmatter.py`.
- CI validation step and Python pin.

## Out of scope

- Skill content.
- Any product change.

## Impacted files

- `scripts/validate_skill_frontmatter.py` (new)
- `.github/workflows/ci.yml`
- `docs/prd/README.md`

## Risks and edge cases

- Script requires a skill missing from one platform and breaks build: all six already exist on all three, verified before connecting to CI.
- PyYAML absent from CI environment: already present in `requirements.txt`.

## Rules and constraints

- Smallest correct change; English documentation.

## Plan

- [ ] Context and research
- [ ] Port script and adapt names
- [ ] Verify encoding-regression detection
- [ ] Connect to CI and pin Python
- [ ] Validation
- [ ] Cleanup audit

## Test plan

### Tests to author

No new Django behavior. Verification runs the script itself, including one negative case with introduced and reverted corruption.

### Execution authorization

- Status: authorized by the explicit operator order.

### Execution evidence

Script execution:

```
[OK] 6 skill(s) across 3 platforms: lv-cleanup-audit, lv-django-delivery,
 lv-prd, lv-prompt-builder, lv-task-intake, lv-ui-delivery
[OK] 6 intact Codex metadata file(s) in UTF-8 with LF.
18 skill file(s) validated.
```

Negative case, with a replacement character introduced in `.agents/skills/lv-prd/agents/openai.yaml` and then reverted:

```
--- with corruption ---
ValueError: Replacement character (corrupted encoding): .agents\skills\lv-prd\agents\openai.yaml
--- restored ---
18 skill file(s) validated.
```

## Visual validation

Not applicable. No template, CSS, or JavaScript changed.

## ORM validation

Not applicable.

## Quality validation

`python -m pip check` — `No broken requirements found.`

`ci.yml` remains valid YAML, loaded with `yaml.safe_load`. Job steps in order:

```
Checkout → Set up Python (3.12.10) → Install dependencies
→ Validate dependencies → Validate skill frontmatter
→ Django system check → Verify migration baseline → Run test suite
```

`manage.py check` — `System check identified no issues (0 silenced).`

## Evidence

- Script reports six skills across three platforms and 18 files.
- Proven failure for corrupted encoding.
- Clean `pip check`; valid `ci.yml` with two new steps.
- Clean `manage.py check`.

## Implemented

- Adopted `scripts/validate_skill_frontmatter.py` with `load_frontmatter`, `validate_platform_coverage`, and `validate_codex_metadata`.
- `.github/workflows/ci.yml` gained `Validate dependencies` (`pip check`) and `Validate skill frontmatter` steps.

## Cleanup findings

- LV CI already pinned Python `3.12.10`; no change needed there.
- With this PRD, all projects run the same CI checks: `pip check`, skill validator, `manage.py check`, `makemigrations --check`, and suite. Parity-audit item D13 is closed.
- No residue introduced.

## Follow-up PRDs

- Still open from PRD-162: remove `lv-pessoas-2026` from `docs/OPERACAO-BANCO-SEEDS.md` together with the decision about retiring `seed_system_people_flow_samples`.

## Deviations from plan

- In addition to the validator, added `pip check`, which CI did not run. Without it, CI homogeneity would remain incomplete, contrary to this PRD's goal.

## Pending

- Run CI for real: steps were verified locally, but the job runs only on the next push.
- Commit the working tree. No commit was made by the agent in this series.

## Final status

Completed. LV now fails the build when a skill disappears from a platform, diverges from source, or has corrupted Codex metadata — the same defense as the other two. All projects now run the same verification set.
