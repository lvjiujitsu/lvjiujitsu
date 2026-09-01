# PRD-157: Contract Deduplication and CLAUDE.md Hygiene

## Summary

Assign one owner to every LV governance rule, move procedure currently living in `CLAUDE.md` to `AGENTS.md`, and remove facts from `CLAUDE.md` that age on their own.

## Demand type

Governance review.

## Current problem

**1. Procedure inside the facts file.** `CLAUDE.md:5` declares that “Procedures belong in `AGENTS.md`.” These lines contradict it:

| Line | Content | Actual nature |
|---|---|---|
| `CLAUDE.md:68` | “Record command and result” | procedure |
| `CLAUDE.md:132-135` | approved visual-proposal rule | procedure and permission |
| `CLAUDE.md:140-142` | production policy | permission |

**2. Factual duplication between `AGENTS.md` and `CLAUDE.md`.** `AGENTS.md:114-127` (§9 Django MVT) reproduces the layer tree from `CLAUDE.md:24-37`. Two maintenance points for the same fact — both copies answer the same question, unlike a legitimate case where each file answers a different question.

**3. Fact pinned to a patch level.** `CLAUDE.md:15` fixes “Python 3.12.10, Django 5.2.14 LTS.” Patch levels age with each `pip install -r requirements.txt`, and `requirements.txt`, not the contract, is the exact version source.

## Goal

After this PRD, changing an LV governance rule requires editing exactly one file, and `CLAUDE.md` contains only facts that do not expire.

## Context Ledger

### Files read in full

- `CLAUDE.md`, `AGENTS.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`
- `.claude/skills/*/SKILL.md` (six files)

### Adjacent files consulted

- `requirements.txt` — exact version source.
- `docs/UI-SCREEN-CONTRACT.md`, `docs/OPERACAO-BANCO-SEEDS.md` — candidate owners.

### Internet / official documentation

- [Django 5.2 LTS — release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/) — confirms that the LTS series is stable information; the patch is not.

### Context7 / MCPs / tools verified

- Context7 unavailable while drafting. Limitation recorded.

### Limitations found

- None.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: governance audit, 2026-07-22.
- User approval: explicit instruction to generate remediation PRDs.
- Date: 2026-07-22.

## Execution prompt

### Persona

LV Jiu Jitsu agent-governance maintainer.

### Action

Apply the ownership matrix, move procedure from `CLAUDE.md` to `AGENTS.md`, and unpin the patch level.

### Context

Ownership matrix to apply and record in `AGENTS.md` §2:

| Subject | Sole owner | Referenced by |
|---|---|---|
| Product, stack, environment, and port facts | `CLAUDE.md` | everyone |
| Precedence, language, authorization gates, closure | `AGENTS.md` | skills |
| Detailed lifecycle procedure | `docs/AGENT-WORKFLOW.md` | `AGENTS.md`, skills |
| PRD format and numbering | `docs/PRD-STANDARD.md` | `lv-prd` |
| Visual and flow contract | `docs/UI-SCREEN-CONTRACT.md` | `lv-ui-delivery` |
| Database, destructive cycle, and seeds | `docs/OPERACAO-BANCO-SEEDS.md` | `CLAUDE.md`, `AGENTS.md` |
| Tool-specific differences | `docs/PLATFORM-ADAPTERS.md` | `AGENTS.md` |

### Constraints

- A reference is one line containing a path, not a summary. A summary is lossy duplication.
- `AGENTS.md` §9 may retain the **responsibility table** by layer (protocol) if `CLAUDE.md` §2 retains only the **directory tree** (fact), and an explicit cross-reference states this. Otherwise, one copy must be removed.
- Do not change the semantics of any rule in this PRD — only decide where it lives.
- `CLAUDE.md` retains the command table; only the conduct instruction (“Record command and result”) is removed.

### Acceptance criteria

- [ ] `AGENTS.md` §2 contains the seven-row ownership matrix above.
- [ ] `CLAUDE.md:68` no longer contains a conduct instruction; the “Registrar comando e resultado” (“Record command and result”) rule exists in `AGENTS.md` or `docs/AGENT-WORKFLOW.md`, in exactly one place. Verification: `grep -rn "Registrar comando e resultado" --include=*.md .` returns one file.
- [ ] `CLAUDE.md:132-135` and `:140-142` no longer contain permission rules; corresponding content lives in `AGENTS.md`. After PRD-154 and PRD-155, anything remaining on those lines is fact or reference.
- [ ] The Django layer tree exists as a fact in exactly one file, and the cross-reference between `AGENTS.md` §9 and `CLAUDE.md` §2 is explicit.
- [ ] `CLAUDE.md:15` stops pinning a patch level. Required text: “Python 3.12 / Django 5.2 LTS,” with `requirements.txt` named as the exact source. Verification: `grep -n "3.12.10\|5.2.14" CLAUDE.md` returns empty.
- [ ] No other `CLAUDE.md` line pins a patch version, file count, or quantity that changes with use. Verification: recorded manual scan listing every number found and why it is stable.
- [ ] No reference points to a nonexistent file. Verification: for every path cited in `CLAUDE.md`, `AGENTS.md`, and `docs/*.md`, `test -f` returns true.
- [ ] `wc -l CLAUDE.md` and `wc -l AGENTS.md` recorded before and after.
- [ ] `.\.venv\Scripts\python.exe manage.py check` completes without errors.

### Expected evidence

- Diff of `CLAUDE.md`, `AGENTS.md`, and changed docs.
- Count `grep` output.
- Link-verifier output.
- Before/after `wc -l`.

### Output format

Diff + command outputs under `Evidence`.

## Scope

- `CLAUDE.md`: lines 15, 68, 132–135, 140–142, and §2.
- `AGENTS.md`: §2 (matrix) and §9.
- `docs/AGENT-WORKFLOW.md`: receives moved procedure if selected as owner.

## Out of scope

- Changing rule semantics (PRD-154, PRD-155).
- Skills (PRD-156).
- Slash commands (PRD-158).
- `docs/archive/static-documentation-legacy/` — archived legacy, not an active contract.

## Impacted files

| File | Nature |
|---|---|
| `CLAUDE.md` | procedure and pinned-version removal |
| `AGENTS.md` | new matrix; adjusted §9 |
| `docs/AGENT-WORKFLOW.md` | receives moved procedure |

## Risks and edge cases

| Risk | Mitigation |
|---|---|
| Move a rule and lose it | Each count `grep` requires exactly one remaining file, proving the rule survived somewhere. |
| Reference breaks after future rename | Criterion verifies existence of every cited path. |
| Ambiguity between directory tree and responsibility table | Criterion requires explicit cross-reference or removal of one copy. |
| Edit conflict with PRD-154 and PRD-155 touching the same lines | This PRD runs **after** both; dependency declared in `Final status`. |

## Rules and constraints

- English content; identifiers remain in English.
- Smallest correct diff.
- Do not create a new file.

## Plan

- [ ] Context and research
- [ ] Implementation
- [ ] Validation
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

No Django test.

### Execution authorization

- Status: authorized

### Execution evidence

Pending.

## Visual validation

Not applicable.

## ORM validation

Not applicable.

## Quality validation

Count `grep`, link verifier, `wc -l`, and `manage.py check`.

## Evidence

Pending.

## Implemented

Pending.

## Cleanup findings

Pending.

## Follow-up PRDs

- `PRD-158` — slash commands.

## Deviations from plan

Pending.

## Pending

Pending.

## Final status

Not started. Depends on PRD-154 and PRD-155, which rewrite the same `CLAUDE.md` lines.
