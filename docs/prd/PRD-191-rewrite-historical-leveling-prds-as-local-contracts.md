# PRD-191: Rewrite historical leveling PRDs as local contracts

## Contract correction

The `documentation.isolation` gate declared by this PRD is revoked by operator
decision. A system does not host an isolation gate against other systems:
measuring and enforcing alignment belongs to the central audit repository, which
issues correction PRDs and runs its own quality gates. Verification of the
outcome recorded here is therefore external to this repository. The
documentation work described below remains valid; only the gate requirement is
withdrawn.

## Summary

Historical leveling PRDs describe local contracts through non-local relational context and a comparative baseline. Their local requirements and completed outcomes must be preserved without relying on that context.

## Demand type

Historical contract isolation defect.

## Current problem

Historical leveling PRDs describe local contracts through non-local relational context and a comparative baseline. Their local requirements and completed outcomes must be preserved without relying on that context.

## Goal

Express every declared leveling outcome as an autonomous local contract supported only by local evidence.

## Context Ledger

### Files read in full

- `docs/prd/PRD-168-duplicate-prd-number-guard-and-settings-hygiene.md`
- `docs/prd/PRD-169-leveling-of-protocol-contracts.md`
- `docs/prd/PRD-170-leveling-of-product-contracts.md`
- `docs/prd/PRD-171-leveling-of-infrastructure-and-environment.md`
- `docs/prd/PRD-172-structural-cleanup-and-code-without-comment.md`
- `docs/prd/PRD-173-common-core-of-the-visual-contract.md`
- `docs/prd/PRD-174-taxonomy-of-the-operational-runbook.md`
- `docs/prd/PRD-175-unique-vocabulary-of-css-tokens.md`
- `docs/prd/PRD-177-autonomous-agents-and-triggers.md`

### Adjacent files consulted

- `AGENTS.md`
- `docs/prd/PRD-164-self-contained-contracts-and-standardisation-of-the-ci.md`

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

Rewrite the relational and comparative rationale in the declared historical PRDs without changing their local outcomes.

### Context

This change is documentation-only. Preserve protocol, product, infrastructure, clean-code, visual, runbook, CSS, and agent outcomes.

### Constraints

- Do not add knowledge of any external product or repository.
- Do not weaken or remove destructive automation unrelated to this finding.
- Do not print or persist sensitive values.
- Do not add comments or docstrings.

### Acceptance criteria

- [x] The declared historical PRDs contain no non-local identity, comparative baseline, or non-local flow.
- [x] Protocol, product, infrastructure, clean-code, visual, runbook, CSS, and agent outcomes remain expressed as local requirements.
- [x] Completed implementation evidence and final statuses remain factually intact.
- [x] Local business terminology and internal module relationships are not removed as false positives.
- [x] The local PRD index gate passes; alignment verification is conducted by the central audit, external to this repository.
- [x] The complete local test suite and applicable quality gates pass.
- [x] No comments or docstrings are introduced.
- [x] No external product reference or dependency is introduced.

### Expected evidence

Focused regression output, complete quality-gate output, and a sanitized final diff.

### Output format

Record implementation, commands, results, deviations, cleanup, and remaining work in this PRD.

## Audit reference

- Gate: none in this repository; verification is conducted by the central audit
- Finding: `historical-leveling-cross-product-comparisons`
- Severity: `high`

## Scope

Resolve only finding `historical-leveling-cross-product-comparisons` and the local files required by it.

## Out of scope

- Unrelated business rule changes.
- External repository changes.
- Opportunistic refactors that require a separate PRD.

## Impacted files

- `docs/prd/PRD-168-duplicate-prd-number-guard-and-settings-hygiene.md`
- `docs/prd/PRD-169-leveling-of-protocol-contracts.md`
- `docs/prd/PRD-170-leveling-of-product-contracts.md`
- `docs/prd/PRD-171-leveling-of-infrastructure-and-environment.md`
- `docs/prd/PRD-172-structural-cleanup-and-code-without-comment.md`
- `docs/prd/PRD-173-common-core-of-the-visual-contract.md`
- `docs/prd/PRD-174-taxonomy-of-the-operational-runbook.md`
- `docs/prd/PRD-175-unique-vocabulary-of-css-tokens.md`
- `docs/prd/PRD-177-autonomous-agents-and-triggers.md`

## Risks and edge cases

- Removing valid domain-family terminology that belongs to this product.
- Changing a completed technical contract while removing its comparative narrative.

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
- Verify each completed local contract remains accurate after rewriting.

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
- Run the local PRD index gate.
- Confirm each completed local contract and evidence record remains accurate.
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

Rewritten lines, all of them prose only, with every completed outcome and every
number preserved:

- `PRD-168` (1 line): the authorization record keeps the operator's decision to
  address red defects and guards in the first stage, without the staged
  multi-product framing. The index remains the canonical source of the next
  number, which is local vocabulary and was preserved.
- `PRD-170` (15 lines): the section core of `CLAUDE.md`, `README.md`,
  `docs/OPERACAO-BANCO-SEEDS.md`, and `docs/DEPLOY-RENDER-SUPABASE.md` is stated
  as the declared local requirement — 11, 10, 6, and 10 sections — instead of as
  sameness with other products. The CSS-token measurement keeps its numbers: 49
  tokens declared here, of which only three belong to the shared core vocabulary.
  The `Completed with limitations` status and the untouched UI contract are
  unchanged.
- `PRD-171` (14 lines): pinned versions, `LOGGING`, `.gitignore`, `.env`,
  `copilot-setup-steps.yml`, and the five pending convergence items are expressed
  as local requirements. The `clear_migrations.py` behavior (`taskkill /F`
  without `/T`, wait of up to eight seconds) and the reason
  `SUPABASE_RESET_CONFIRM` is absent from `.env.example` are preserved verbatim
  in substance.
- `PRD-172` (14 lines): the cleanup outcome is "zero mentions of projects
  outside this repository"; `KNOWN_EXCEPTIONS` is stated as `{"README.md"}`
  rather than as a family standard. The 769-case suite record is intact.
- `PRD-173` (3 lines) and `PRD-174` (4 lines): the isolation criteria read "a
  project outside this repository". Every occurrence of "canonical route",
  "canonical alias", "canonical seeds", and "canonical path" was preserved —
  that is this repository's own vocabulary, not provenance.
- `PRD-175` (6 lines): the token vocabulary is unified around the shared core
  vocabulary. The measurement "from 3 to 12 names" and the list of twelve tokens
  are unchanged, as is the single variant of section 4 of the UI contract.
- `PRD-177` (1 line): the operator instruction keeps independent agent context,
  the authorization to branch, push, and open a Pull Request, and the rule that
  merge stays outside agent authority.
- `PRD-169`: audited, no non-local provenance found.

Local business terminology was explicitly protected: `PRD-127`'s "same family
group" is the family-discount rule of this product and was not touched.

## Cleanup findings

- No false positive was removed. "Canonical route", "canonical alias",
  "canonical seeds", "canonical name", "canonical path", the three platform
  directories (`.agents`, `.claude`, `.cursor`), the two Supabase projects, and
  the family-discount vocabulary of the product were all preserved after
  line-by-line review.
- Every rewritten line was asserted against an expected fragment before
  replacement, so no line was replaced blindly and no adjacent content moved.
- Statuses parsed by `scripts/build_prd_index.py` were re-verified after the
  rewrite: `PRD-170` remains `concluída com limitações`, `PRD-172` and `PRD-175`
  remain `concluída`.

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
- Two evidence lines carried a measurement whose original form was comparative:
  `PRD-170`'s CSS-token count and `PRD-175`'s shared-vocabulary count. Both were
  rewritten around the shared core vocabulary, which is a concept this repository
  owns in section 4 of `docs/UI-SCREEN-CONTRACT.md`, so the numbers stayed exact
  and no measurement was invented.

## Pending

None.

## Final status

Concluída.
