# PRD-083: Archive the legacy documentation in static

## Summary
Assess and move/remove the Markdown documents versioned in `static/documentation`, which are not the current source of truth and may be served as public assets.

## Demand type
Documentation governance + cleanup.

## Current problem
`static/documentation/` contains 12 long Markdown files with old PRDs/maps. The current sources of truth are `AGENTS.md`, `CLAUDE.md`, `docs/`, and `docs/prd/`.

## Goal
Remove the parallel documentation source:
- archive it in `docs/archive/` when there is historical value;
- remove it when demonstrably obsolete;
- or update the reference when some document is still canonical.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- the inventory of `static/documentation`

### Adjacent files consulted
- `docs/`
- `docs/prd/`

### Internet / official documentation
Not applicable.

### Context7 / MCPs / tools verified
- PowerShell and `rg`.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved
The diagnosis is authorized; the final removal requires confirmation when there is no proof it is orphaned.

## Scope
- Inventory the references.
- Classify each document.
- Execute the decision, moving or removing it.

## Out of scope
- Rewriting the product documentation.

## Impacted files
- `static/documentation/*`
- a possible `docs/archive/*`

## Risks and edge cases
- The documents may contain useful historical context.
- Keeping docs in `static` may expose operational information.

## Plan
- [x] `rg` for each filename.
- [x] A keep/move/remove matrix.
- [x] Execute the approved decision.

## Test plan
### Tests to author
Not applicable (a documentation change, with no code behavior).

### Execution authorization
Authorized by the current request (execute PRD-083's Plan).

### Execution evidence
- `rg -l --hidden -g '!.git' -g '!static/documentation/*' "<filename>" .` for each of the 12 files: no occurrence outside `static/documentation/` for any of the file names. Result: all orphaned (with no reference in code, templates, docs, or settings).
- `rg -l --hidden -g '!.git' "static/documentation|documentation/" .` before the move: it returned only `docs/prd/PRD-076-legacy-audit-governance-and-documentation.md` and `docs/prd/PRD-083-archiving-legacy-documentation-in-static.md` (the audit/PRD describing the finding, not real consumption).
- A content inspection (`Documento_Go_Live_e_Hardening_LV_JIU_JITSU.md` and others): they cite `pytest`, an `AuditLog` model, a `PDV` module, and the `CRITICAL_EXPORT_CONTROL_FILE` variable. `rg -l "class AuditLog|class PDV|CRITICAL_EXPORT_CONTROL_FILE" system/` found no occurrence in the current code — confirming that the 12 documents describe an earlier phase of the system, obsolete today.
- After the `git mv` of the 12 files: `rg -l --hidden -g '!.git' "static/documentation" .` went back to returning only the two audit PRDs (as expected, that is the decision's historical record).
- `git diff --check` → output with no whitespace errors on the lines added by the rename (only pre-existing LF/CRLF warnings in files not touched by this task).

## Visual validation
Not applicable.

## ORM validation
Not applicable.

## Quality validation
- `rg` for references before/after.
- `git diff --check`.

## Evidence
- The subagent identified 12 `.md` files in `static/documentation` with 5,415 lines.

## Implemented
- The classification of the 12 files in `static/documentation/`: all orphaned (with no reference in code, templates, settings, or other docs beyond the PRD-076/PRD-083 audit trail itself) and all describing an earlier phase of the product (they cite `pytest`, `AuditLog`, `PDV`, `CRITICAL_EXPORT_CONTROL_FILE` — none of which exists in the current code).
- Decision: archive (not remove), for the potential historical value and because they are currently served as a public asset inside `static/`, which was the risk identified in the PRD.
- The 12 files moved through `git mv` from `static/documentation/` into `docs/archive/static-documentation-legacy/`, preserving the file history in git:
  - `Documento_Arquitetura_App_System_LV_JIU_JITSU.md`
  - `Documento_Estrategia_de_Testes_e_Gates_LV_JIU_JITSU.md`
  - `Documento_Fluxos_Criticos_e_Fontes_de_Verdade_LV_JIU_JITSU.md`
  - `Documento_Go_Live_e_Hardening_LV_JIU_JITSU.md`
  - `Documento_Mapeamento_Modulos_System_LV_JIU_JITSU.md`
  - `Documento_Stripe_Implementacao_LV_JIU_JITSU.md`
  - `Documento_Unico_Mapeamento_Forms_Serializers_LV_JIU_JITSU_v5.md`
  - `Documento_Unico_Mapeamento_Models_LV_JIU_JITSU.md`
  - `Documento_Unico_Mapeamento_Templates_LV_JIU_JITSU.md`
  - `Documento_Unico_Mapeamento_Views_LV_JIU_JITSU.md`
  - `PRD_Implementacao_Completa_LV_JIU_JITSU.md`
  - `PRD_implementacao_FINAL_LV_JIU_JITSU.md`
- `static/documentation/` ended up empty (the directory was implicitly removed, since git does not version an empty directory).

## Cleanup findings
- No code residue points at `static/documentation/`; no Django route serves that path explicitly (it was served only as a generic static file through `staticfiles`/`static/`).
- No duplication created: the moved files do not collide with names already existing in `docs/` or `docs/archive/`.

## Follow-up PRDs
No follow-up identified within this PRD's scope. There is no need for a new PRD; the move closes PRD-076's finding regarding `static/documentation`.

## Deviations from plan
- The original Plan did not specify the exact destination inside `docs/archive/`; the `docs/archive/static-documentation-legacy/` subdirectory was created to isolate this batch of legacy documents without mixing it with other future `docs/archive/` files.

## Pending
- No technical pending items. It is recommended that the owner review whether any of the 12 archived documents still has reference value, to decide on a definitive discard in a future cycle (outside this PRD's scope, which only required removing the parallel source from `static/`).

## Final status
Completed.
