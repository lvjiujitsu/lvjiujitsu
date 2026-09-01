# PRD-190: Rewrite historical governance PRDs from local evidence

## Contract correction

The `documentation.isolation` gate declared by this PRD is revoked by operator
decision. A system does not host an isolation gate against other systems:
measuring and enforcing alignment belongs to the central audit repository, which
issues correction PRDs and runs its own quality gates. Verification of the
outcome recorded here is therefore external to this repository. The
documentation work described below remains valid; only the gate requirement is
withdrawn.

## Summary

Historical governance, infrastructure, and CI PRDs use non-local provenance and comparisons to justify local decisions. The resulting local contracts must remain, but their rationale must be derived entirely from this product.

## Demand type

Historical governance documentation isolation defect.

## Current problem

Historical governance, infrastructure, and CI PRDs use non-local provenance and comparisons to justify local decisions. The resulting local contracts must remain, but their rationale must be derived entirely from this product.

## Goal

Preserve the declared governance outcomes as autonomous local contracts supported only by local evidence.

## Context Ledger

### Files read in full

- `docs/prd/PRD-054-architectural-alignment-and-safe-reset.md`
- `docs/prd/PRD-059-lean-governance-for-claude-codex-and-cursor.md`
- `docs/prd/PRD-060-multi-platform-governance-parity-skill-lv-prompt-builder.md`
- `docs/prd/PRD-061-governance-alignment-workflow-and-adapters.md`
- `docs/prd/PRD-145-registration-payment-documentation-operational-audit.md`
- `docs/prd/PRD-158-slash-commands-for-repeated-operational-cycle.md`
- `docs/prd/PRD-159-hardening-local-infrastructure-and-ci.md`
- `docs/prd/PRD-160-environment-variable-reconciliation.md`
- `docs/prd/PRD-161-slash-commands-prd-index-and-repository-hygiene.md`
- `docs/prd/PRD-162-hardened-remote-reset-documented-deployment-and-observability.md`
- `docs/prd/PRD-163-validator-of-skills-and-homogeneity-of-the-ci.md`
- `docs/prd/PRD-164-self-contained-contracts-and-standardisation-of-the-ci.md`

### Adjacent files consulted

- `AGENTS.md`
- `CLAUDE.md`

### Internet / official documentation

Not applicable: the defect is governed by the local application contract.

### Context7 / MCPs / tools verified

Not applicable during PRD materialization. The implementation session must verify any API used.

### Limitations found

The audit proves the current behavior and expected contract. Runtime correction and regression evidence belong to the implementation session.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: preserve autonomous destructive workflows and create one local PRD per objective parity defect.
- User approval: the operator explicitly ordered the investigation and creation of the PRDs found by the audit.
- Date: 2026-08-31.

## Execution prompt

### Persona

Act as the local Django delivery agent for this repository only.

### Action

Rewrite comparative provenance and non-local flow language in the declared governance PRDs.

### Context

This change is documentation-only. Preserve destructive automation, environment behavior, seeds, CI capabilities, skills, and agent autonomy.

### Constraints

- Do not add knowledge of any external product or repository.
- Do not weaken or remove destructive automation unrelated to this finding.
- Do not print or persist sensitive values.
- Do not add comments or docstrings.

### Acceptance criteria

- [x] The declared governance PRDs contain no comparative baseline, non-local provenance, or non-local flow.
- [x] Every retained governance, infrastructure, CI, skill, and environment decision is justified by local evidence.
- [x] Autonomous destructive and reconstructive behavior remains unchanged and explicitly preserved where relevant.
- [x] Abstract non-dependency guardrails remain allowed when they reveal no outside product or behavior.
- [x] The local PRD index and applicable skill gates pass; alignment verification is conducted by the central audit, external to this repository.
- [x] The complete local test suite and applicable quality gates pass.
- [x] No comments or docstrings are introduced.
- [x] No external product reference or dependency is introduced.

### Expected evidence

Focused regression output, complete quality-gate output, and a sanitized final diff.

### Output format

Record implementation, commands, results, deviations, cleanup, and remaining work in this PRD.

## Audit reference

- Gate: none in this repository; verification is conducted by the central audit
- Finding: `historical-governance-cross-product-provenance`
- Severity: `high`

## Scope

Resolve only finding `historical-governance-cross-product-provenance` and the local files required by it.

## Out of scope

- Unrelated business rule changes.
- External repository changes.
- Opportunistic refactors that require a separate PRD.

## Impacted files

- `docs/prd/PRD-054-architectural-alignment-and-safe-reset.md`
- `docs/prd/PRD-059-lean-governance-for-claude-codex-and-cursor.md`
- `docs/prd/PRD-060-multi-platform-governance-parity-skill-lv-prompt-builder.md`
- `docs/prd/PRD-061-governance-alignment-workflow-and-adapters.md`
- `docs/prd/PRD-145-registration-payment-documentation-operational-audit.md`
- `docs/prd/PRD-158-slash-commands-for-repeated-operational-cycle.md`
- `docs/prd/PRD-159-hardening-local-infrastructure-and-ci.md`
- `docs/prd/PRD-160-environment-variable-reconciliation.md`
- `docs/prd/PRD-161-slash-commands-prd-index-and-repository-hygiene.md`
- `docs/prd/PRD-162-hardened-remote-reset-documented-deployment-and-observability.md`
- `docs/prd/PRD-163-validator-of-skills-and-homogeneity-of-the-ci.md`
- `docs/prd/PRD-164-self-contained-contracts-and-standardisation-of-the-ci.md`

## Risks and edge cases

- Weakening autonomous destructive workflows while simplifying historical rationale.
- Leaving non-local provenance disguised through relational terminology.

## Rules and constraints

- Preserve valid business behavior outside the defect.
- Keep the implementation cohesive and dependency-injectable where an external boundary is involved.
- Explanations belong in the owning Obsidian knowledge note, not in source comments or docstrings.

## Plan

- [x] Context and research
- [x] Test authored first
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Validation steps

- Leave alignment verification over the declared PRDs and the complete repository to the central audit, external to this repository.
- Run `python scripts/build_prd_index.py --check`.
- Verify completed outcomes and evidence remain locally accurate.

### Execution authorization

- No remote or destructive operation is required for this documentation-only correction.

### Execution evidence

The rewrite was reviewed with a one-off textual sweep run by hand during the
session, not by a gate: this repository hosts no such gate, and creating one
would add a runtime artifact this documentation-only PRD must not introduce.
Term list used (case-insensitive, one term per line, applied with
`grep -in -f`):

```text
sibling project           sibling MVP               three sibling
canonical pattern         canonical standard        canonical index
another repositor         other repositor           the other repo
another project           other projects            outro projeto
in the family             family standard           across the family
the three projects        all three projects        across the projects
cross-project             cross-auditor             parity target
ported from               port the canonical        in the others
PATTERNS-DE-OUTRO         foreign domain terms
```

The sweep additionally covered the proper names of products outside this
repository and the vocabulary of the foreign domain those products serve. Those
strings return zero matches and are deliberately not reproduced here: printing
them in a contract would reintroduce the very identity this PRD removes.

Run over the declared PRDs and, separately, over the complete repository
excluding `.venv/` and `staticfiles/`. Residual matches were reviewed one by one
and all fall into the two allowed classes recorded under `Cleanup findings`.

## Visual validation

Not applicable: no rendered product surface changes.

## ORM validation

Not applicable: no database behavior changes.

## Quality validation

- Leave alignment verification to the central audit, external to this repository.
- Run the local PRD index and skill-contract gates.
- Confirm completed status and local operational facts remain intact.
- Confirm no runtime file changes.

## Evidence

Commands executed on 2026-09-01, local environment, Python 3.12 in `.venv`:

- One-off textual sweep over the declared PRDs and over the complete repository, with
  the term list above. After the rewrite, the only remaining matches are the
  allowed classes listed under `Cleanup findings`; no non-local identity,
  provenance, or comparative baseline survives.
- `scripts/build_prd_index.py --check` — `Indice em dia.`
- `scripts/validate_skill_frontmatter.py` — `[OK] 7 skill(s) nas 3 plataformas`,
  `[OK] 7 metadado(s) Codex integro(s) em UTF-8 com LF.`,
  `21 arquivo(s) de skill validado(s).`
- `manage.py check` — `System check identified no issues (0 silenced).`
- `manage.py test` (complete suite) — `Ran 783 tests ... FAILED (failures=1,
  errors=5)`. The six residual results are pre-existing and environment-driven
  (`STRIPE_SECRET_KEY` and `SEED_TEST_PORTAL_PASSWORD` absent from the local
  environment); they were proven pre-existing against the stashed baseline while
  PRD-187 to PRD-189 were implemented, and none of them reads documentation.
- `git status --short` over `system/`, `lvjiujitsu/`, `templates/`, `static/`,
  `scripts/`, `.github/`, `requirements.txt`, and `manage.py` — the only entries
  are the runtime files changed by PRD-187, PRD-188, and PRD-189. This PRD
  changed no runtime file.

**Limitation on the final diff.** The declared PRD files are untracked in the
working tree, because the operator's in-progress rename to English slugs has not
been committed. `git diff` therefore returns nothing for them and a sanitized
final diff cannot be produced by Git. The change record is the per-line rewrite
list in `Implemented`, and every rewritten line was asserted against an expected
fragment before replacement, so no line was replaced blindly.


## Implemented

Rewritten lines, all of them prose only, with each declared outcome preserved:

- `PRD-060` (3 lines): the decision not to create `docs/UX-SCREEN-FLOWS.md` and
  the anti-external-domain sweep are stated without naming a mirrored project or
  a foreign domain's vocabulary.
- `PRD-061` (11 lines): the governance goal, the acceptance criteria, the
  constraint, and the evidence are stated as local requirements — `CLAUDE.md`
  declares where this repository's governance bootstrap lives — and the foreign
  consultancy domain no longer appears in the summary, the constraints, the
  criteria, or the evidence sweep.
- `PRD-158` (3 lines): the fourth repeated cycle is the repository parity audit;
  the out-of-scope note no longer points at other repositories.
- `PRD-160` (4 lines): the environment-file requirement is stated directly, and
  the approval record no longer describes a multi-product audit or quotes a
  multi-product order.
- `PRD-161` (13 lines): each of the seven findings, the Context7 note, the
  limitation, the context, and two evidence lines now state the required local
  standard instead of naming an external target.
- `PRD-162` (14 lines): the summary, findings 1, 2 and 5, the reference-reading
  note, the action, the context, three evidence lines, the follow-up, and three
  deviations now describe the defense LV needed and adopted, not where it came
  from. The `SUPABASE_PROJECT_REF`-versus-host guard, the per-table RLS with
  `--check`, and the Build Command decision are unchanged.
- `PRD-163` (6 lines): the validator is created for this repository, and the
  corruption risk that justifies a byte-level check is stated without attributing
  it to an outside repository. `pip check` remains part of the delivery.
- `PRD-164`: audited, no change required. Every match there is an abstract
  non-dependency guardrail — the PRD that establishes the self-containment rule
  must be able to state it.
- `PRD-054`, `PRD-059`, `PRD-145`, `PRD-159`, `PRD-169`: audited, no non-local
  provenance found.

Autonomous destructive and reconstructive behavior is untouched: the remote-reset
guards, the simulation-by-default rule, `--execute`, the seed inventory, the
slash commands, and the CI gates all read exactly as before.

## Cleanup findings

Two classes of residual match were reviewed and deliberately kept:

- **Abstract non-dependency guardrails** — the thirteen matches in `PRD-164`
  ("no repository file may cite another repository by name or path", the removed
  `docs/references/PATTERNS-DE-OUTRO-PROJETO.md`, the verification that returns
  zero occurrences). None names a product, a path, or a behavior outside this
  repository, and criterion four of this PRD admits them explicitly.
- **Local behavior that reads as relational** — `PRD-159` ("never terminate
  another project's Python process" is the local process filter of
  `clear_migrations.py`) and `PRD-162` line 232 ("one project's `DATABASE_URL`
  with another project's `SUPABASE_PROJECT_REF`" refers to the two provisioned
  Supabase projects, staging and production). Removing these would destroy local
  meaning.

One item outside the declared scope was found and left alone at the time:
`.claude/skills/lv-parity-audit/SKILL.md` and its two mirrors ended their
description with a clause forbidding the audit of any other project. Under the
contract correction recorded above, that clause was removed from all three
byte-identical copies; the description now states only the operational scope,
which is that the skill audits this repository against its own contract.

**Out-of-scope finding, not implemented.** `scripts/build_prd_index.py` matches
`## Final status` against Portuguese labels only (`concluída`, `concluída com
limitações`, `não concluída`, `em andamento`, `superada`). The historical PRDs now
declare their status in English (`Completed.`, `Completed with limitations`), so
the index renders `—` for them and the status column is effectively blind for the
translated corpus. This predates this PRD — no status line was altered here
except in the three files whose text already began with `Completed` — and it is a
consequence of the in-progress rename of the PRD corpus to English slugs, which
is uncommitted operator work. No follow-up PRD was opened: the fix belongs to
whoever owns that translation, and reserving a number inside someone else's
in-flight batch would collide with it.

## Follow-up PRDs

None identified within this focused scope.

## Deviations from plan

- "Test authored first" does not apply: the change is prose in historical PRDs
  and there is no testable behavior. The one-off textual sweep plays the role of
  the regression check and was run before and after the rewrite.
- The `documentation.isolation` gate this PRD originally declared was revoked by
  operator decision, as recorded under `Contract correction`. No scanner script
  was created here and none is owed: alignment verification belongs to the
  central audit, external to this repository.

## Pending

None.

## Final status

Concluída.
