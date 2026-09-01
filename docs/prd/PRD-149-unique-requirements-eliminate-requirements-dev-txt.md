# PRD-149: Single Requirements File — Eliminate `requirements-dev.txt`

## Summary
Consolidate dependencies into a single `requirements.txt` (including `PyYAML`) and remove `requirements-dev.txt`, aligning local onboarding and the Render build around the same file. The decision is based on official evidence: on Render Free, the cost of installing PyYAML is negligible relative to 512 MB of RAM.

## Demand type
Dependency configuration + documentation governance.

## Current problem
- Two files existed: `requirements.txt` (production / Render) and `requirements-dev.txt` (`-r requirements.txt` + `PyYAML==6.0.2`).
- PRD-059 / PRD-082 introduced the split to isolate PyYAML (skill validator) from deployment.
- This created onboarding friction (`CLAUDE.md` and `README.md` prescribed different paths) without measurable benefit on Render Free.
- There was uncertainty about whether PyYAML “weakened” the service on the Free tier.

## Goal
- One dependency file: `requirements.txt`.
- Documentation and local/deployment commands reference only that file.
- Decision recorded with official sources about Render Free impact.
- Remove `requirements-dev.txt` without regressing the skill validator (PyYAML remains available through `requirements.txt`).

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `requirements.txt`
- `requirements-dev.txt`
- `docs/PRD-STANDARD.md`
- `docs/prd/PRD-082-readme-and-requirements-dev-aligned-with-lv.md` (previous decision)
- Relevant passages from `docs/prd/PRD-059-lean-governance-for-claude-codex-and-cursor.md`

### Adjacent files consulted
- `docs/OPERACAO-BANCO-SEEDS.md` (Render build)
- `docs/prd/README.md` (number 149)
- `.github/workflows/copilot-setup-steps.yml` (already used only `requirements.txt`)
- Repository search for `requirements-dev` / `PyYAML` / `import yaml`

### Internet / official documentation
| Source | Conclusion | Limitation |
|---|---|---|
| [Render — Deploy for Free](https://render.com/docs/free) | Free web service: **512 MB RAM / 0.1 CPU**; 15-minute spin-down; bandwidth and pipeline-minute limits. Documentation does **not** mention PyYAML or restrictions on specific Python packages. | OOM problems on Free are generic (application heap, heavy seeds, multiple workers), not attributable to one lightweight package. |
| [Render — Instance Types](https://render.com/docs/compute-plans) / [Pricing](https://render.com/pricing) | Confirms Free = 512 MB / 0.1 CPU. | Does not detail per-pip-dependency footprint. |
| [PyPI — PyYAML](https://pypi.org/project/PyYAML/) | `PyYAML 6.0.2` wheel ≈ **184 KB**; `6.0.3` ≈ 184 KB. Minimal package. | Wheel size ≠ runtime RSS if code uses `yaml.load` on huge files. |
| [SO — MemoryError with PyYAML](https://stackoverflow.com/questions/40422307/python-yaml-returns-memoryerror) | High consumption occurs when **parsing large YAML** (tens of MB of file → GB of RAM). | Irrelevant when PyYAML is merely installed and Django/Gunicorn does **not** import/parse YAML in production. |
| Community reports of OOM on Free | Typical OOM: LangChain/ONNX, boot-time seeds, multiple workers — stacks of hundreds of MB. | No report found linking Free OOM to the **mere installation** of PyYAML. |

**Decision summary:** in LV, PyYAML serves the skill validator (local tooling). There is no YAML use on the `system/` request path. Installing PyYAML during the Render build makes **no material difference** to Free-tier RAM/CPU; the Free risk remains the application’s 512 MB envelope (Django + Gunicorn + Pillow, etc.), not this ~184 KB package.

### Context7 / MCPs / tools verified
- Context7 `/yaml/pyyaml`: PyYAML supports Python 3.8+; pip installation; typical `yaml.safe_load` / `safe_dump` usage.
- Local shell: `PyYAML 6.0.2` present in `.venv`.
- Web search + fetch of Render Free documentation.

### Limitations found
- Gunicorn process RSS on Render Free was not measured before/after (would require deployment and Dashboard access; outside local scope).
- PRD-059/082 remain historical; this PRD supersedes the operational decision to split production/development dependencies.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
The current request authorized research + PRD + consolidation into one `requirements.txt` and reference updates.

## Execution prompt
### Persona
LV configuration/governance agent.
### Action
Move `PyYAML==6.0.2` to `requirements.txt`; delete `requirements-dev.txt`; update `CLAUDE.md`, `README.md`, and the PRD index.
### Context
The Render build already uses `pip install -r requirements.txt`. Copilot CI already uses only this file.
### Constraints
Do not change other pins; do not touch HG/production beyond the next deployment; do not introduce extra tools in this scope.
### Acceptance criteria
Single file; aligned docs; local checks pass; clean `rg` outside historical PRDs.
### Expected evidence
Diff, `pip install` / `pip check`, `manage.py check`, and `rg requirements-dev`.
### Output format
Updated PRD + changed files.

## Scope
- Add `PyYAML==6.0.2` to `requirements.txt`.
- Remove `requirements-dev.txt`.
- Update commands in `CLAUDE.md` and `README.md`.
- Index this PRD in `docs/prd/README.md`.
- Record the Render Free / PyYAML decision and research.

## Out of scope
- Changing any other dependency pin.
- Adding a lint/test tool suite to requirements.
- Deployment / Render Dashboard change.
- Rewriting PRD-059 / PRD-082.
- RSS measurement in HG/production.

## Impacted files
- `requirements.txt`
- `requirements-dev.txt` (removed)
- `CLAUDE.md`
- `README.md`
- `docs/prd/PRD-149-unique-requirements-eliminate-requirements-dev-txt.md`
- `docs/prd/README.md`

## Risks and edge cases
- If runtime later parses large YAML through PyYAML under Gunicorn on Free, the risk is no longer “installation only” — that does not occur today.
- Orphan references → mitigated; only historical PRDs cite `requirements-dev`.

## Rules and constraints
- Smallest correct change.
- One dependency source of truth for local and Render.
- Explicit `PyYAML==6.0.2` pin.

## Plan
- [x] Research Render Free + PyYAML (official sources/PyPI).
- [x] Move PyYAML to `requirements.txt`.
- [x] Remove `requirements-dev.txt`.
- [x] Update `CLAUDE.md` and `README.md`.
- [x] Update `docs/prd/README.md` index.
- [x] Validate with `pip install` / `manage.py check` / `rg`.
- [x] Cleanup audit (`lv-cleanup-audit`).

## Test plan
### Tests to author
Not applicable (no Django behavioral change).

### Execution authorization
Local commands authorized by the current prompt.

### Execution evidence
- `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` → all dependencies satisfied, including `PyYAML==6.0.2` (line 37).
- `.\.venv\Scripts\python.exe -m pip check` → `No broken requirements found.`
- `.\.venv\Scripts\python.exe manage.py check` → `System check identified no issues (0 silenced).`
- `Test-Path requirements-dev.txt` → `False`.
- Note: direct `pip.exe` was blocked by Windows App Control; `python -m pip` was used as a valid workaround.
- `rg requirements-dev` → only historical PRDs (059, 082, 139, AUDIT) + this PRD + index entry; clean `CLAUDE.md`/`README.md`.

## Visual validation
Not applicable.

## ORM validation
Not applicable.

## Quality validation
- Diff: +`PyYAML==6.0.2` in `requirements.txt`; removal of `requirements-dev.txt`; docs point only to `requirements.txt`.

## Evidence
### Research
- Render Free: 512 MB / 0.1 CPU — [docs/free](https://render.com/docs/free).
- PyYAML wheel ≈ 184 KB — [PyPI](https://pypi.org/project/PyYAML/).
- Conclusion: installing PyYAML makes **no practical difference** on Free; Free-tier OOM comes from large applications/dependencies, not this package.

### Implementation
- `git diff --stat`: `CLAUDE.md`, `README.md`, `docs/prd/README.md`, `requirements.txt` (+1), `requirements-dev.txt` (deleted).

## Implemented
- `PyYAML==6.0.2` in `requirements.txt`.
- `requirements-dev.txt` removed.
- `CLAUDE.md` and `README.md` use only `requirements.txt`.
- PRD index updated with PRD-149.
- Obsidian `projetos/comandos-powershell-lvjiujitsu.md` aligned (matrix 04, A00, B04, §E, parity, sources).
- Claude MEMORY: `feedback_requirements_unico.md` entry + link in `MEMORY.md`.

## Cleanup findings
- No active orphan reference to `requirements-dev.txt` outside historical documentation (PRDs 059/082/139).
- `lv-*` skills and Cursor rules did not cite `requirements-dev` — no change necessary.
- External documentation (Obsidian + MEMORY) corrected after the identified gap.

## Follow-up PRDs
None.

## Deviations from plan
- `pip.exe` blocked by App Control policy; validation used `python -m pip` (same effect).

## Pending
None.

## Final status
**Completed** (with limitation: Render Free RSS was not measured after deployment; immaterial to the decision given the package size and absence of YAML parsing at runtime).
