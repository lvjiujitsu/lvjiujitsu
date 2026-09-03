# PRD-003: Declare only required direct runtime dependencies

## Context

Requirements mix the common platform with domain dependencies, pin a Django patch different from the installed environment, and keep obsolete direct declarations.

## Required reading and research

Local contracts and involved source files; Obsidian project notes; Context7 Django 5.2 documentation. Official sources: https://docs.djangoproject.com/en/5.2/topics/testing/overview/ ; https://learn.chatgpt.com/docs/build-skills ; https://code.claude.com/docs/en/hooks . Installed distribution metadata establishes dependency contents and reverse requirements. Remote Supabase state is outside this local audit.

## Required skills

Skill Creator, OpenAI Docs and Supabase for the relevant configuration and safety contracts. This is an explicitly requested scoped audit, not a scheduled autonomous delivery cycle.

## Understanding approved

Summary presented: audit this repository, fix functional drift and record supported domain exceptions. User approval: explicit request to audit, delete and edit the named surfaces. Date: 2026-09-02.

## Execution prompt

Persona: Django maintainer. Action: correct the stated defect in this repository. Context: common tooling and domain-specific behavior. Constraints: preserve existing user changes and secrets; no remote mutation or publication. Acceptance criteria:

- [x] Shared behavior is consistent and project identifiers resolve locally.
- [x] Domain exceptions have actual consumers and Obsidian justification.
- [x] Relevant checks pass with recorded evidence.

Expected evidence: commands, outputs and focused regression tests. Output format: implementation, validation and limitations.

## Scope

requirements.txt; Obsidian dependency justifications.

## Out of scope

Product redesign, schema changes, real local database reset, remote reset, network payment requests, commit, push and deployment.

## Impacted files

requirements.txt; Obsidian dependency justifications.

## Risks and edge cases

Cross-project process termination; environment path selection; absent or stale command names; transitive dependencies mistaken for unused packages; stale local settings; missing vault.

## Rules and constraints

Shared structure before documented project-specific configuration. Preserve application business behavior. Test destructive guards with temporary fixtures and mocked processes only.

## Plan

- [x] Context and research
- [x] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

Tests were authored before the fixes. The initial run reproduced foreign-process termination, shared-environment lookup failure, remote-file masking and missing --check behavior. A separate failing test reproduced omission of untracked source files. Final focused and full suites passed. Tests for remote resets mock all connections and cursors. Execution was authorized by the user request and local contracts.

## Visual validation

No interface layout or browser-flow change. Only 60 Django comment tokens and blank-line indentation were removed; equivalent non-comment template content was checked using the Django lexer. No visual redesign or screenshot is claimed.

## ORM validation

Read-only checks: Django checks and migration drift as applicable. Mutating checks and authorization: isolated test databases only; no real database reset.

## Quality validation

All shared checks passed. The quality scan covers tracked and untracked source and accepts UTF-8 BOM files. After it exposed 60 pre-existing Django comments in three templates, only comment tokens and blank-line indentation were removed, preserving non-comment content.

## Evidence

Full Django suite: 829 tests in 233.487s, exit 0. One Windows symbolic-link test skipped; junction and mocked containment scenarios passed. All 38 skill contract tests passed (23 autonomous, 9 visual, 6 clean). Local reset preflight, Django check, migration dry-run, local schema, pip check, CSS, quality and PRD index checks returned 0. Hook executed successfully from outside the repository. Skill Creator validated six compatible skills/adapters and YAML parsed for all metadata.

## Implemented

Requirements now start with the same seven framework/deployment dependencies and pinned versions, followed by evidenced domain dependencies. Removed unused PyYAML. Django is pinned to 5.2.16, matching the installed environment. No blind removal of framework, platform or transitive dependencies.

## Cleanup findings

Removed obsolete references and duplicate maintenance behavior. Tests relying on removed cleanup APIs were updated to assert the current ownership guard. The obsolete test requiring docs/OPERACAO-BANCO-SEEDS.md was removed because that contract moved to the external vault; 363 command references in current runbook code blocks were checked against existing command modules. Original adapter relative links were already valid and remain valid.

## Follow-up PRDs

None required to finish this local scope. Further product-wide standardization remains a separate user-directed stage.

## Deviations from plan

At the start, the PRD directories contained no files; their indices were initialized during this audit. The reservation ledger starts this batch at 001. Existing reservations are preserved.

## Pending

No remaining local implementation work in this scope. No remote reset, deployment, real local database reset, external gateway request, commit or push was requested or executed. Before a future HG deployment, the operator must apply the reviewed Build Command in Obsidian with session-scoped SUPABASE_RESET_CONFIRM=RESET_HG; no Dashboard was changed.

## Final status

Concluída localmente. Validation limits: remote infrastructure and interactive agent discovery were not exercised; test logs explicitly record Windows skips.
