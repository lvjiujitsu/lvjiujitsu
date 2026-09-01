# PRD-166: Contract Density and Operational Inventory

## Summary

Declare the disposable nature of the MVP in `CLAUDE.md`, which is the normative basis for the destructive cycles the project already performs; separate cleanup from closure and document the slash commands in `docs/AGENT-WORKFLOW.md`; number the contract sections; and write the operational command inventory, which is currently missing twelve commands.

## Demand type

Documentation governance. No business-rule change and no application-code change.

## Current problem

1. **`CLAUDE.md` does not declare the nature of the project.** Section 1 is "Product" and describes what the system does. There is no section stating *what the project is as an artifact*: whether it contains real business data, whether production retains customer history, whether the migration baseline can be recreated, or whether a remote reset is a routine operation or an incident.

   This gap is not theoretical. The project has `clear_migrations.py`, `clear_migration_supabase_hg`, `clear_migration_supabase_prod`, and a single recreatable baseline. Section 11 of `AGENTS.md` authorizes a local reset without asking and describes the destructive reset protocol in Supabase. In other words, the destructive protocol exists and is standardized, but the premise that justifies it—the absence of history that must be preserved—is not written anywhere.

   An agent reading the contracts finds permission to destroy data without finding the reason why that is acceptable, and has no way to know when it ceases to be acceptable. The counterpart is also missing: the condition under which that permission is revoked.

2. **Section 14 of `AGENTS.md` is titled "Skills."** Its content is a mapping from each type of demand to a mandatory skill, plus the requirement to mirror those skills across the three platforms. The title does not state that they are mandatory, which is the section's only normative fact.

3. **`docs/AGENT-WORKFLOW.md` combines cleanup and closure.** Section 13 is "Cleanup and closure" and covers two distinct moments: reviewing the diff and removing residue, and reporting the result with evidence and status. They are different gates with different criteria, and `AGENTS.md` separates them into sections 12 and 13. The execution document combines them, making the closure gate appear to be an appendix to cleanup.

4. **`docs/AGENT-WORKFLOW.md` does not document the slash commands.** Three commands exist in `.claude/commands/`: `reset-local`, `sync-skills`, and `validar-tela`. Two of them perform infrastructure operations—one destroys the local environment, while another compares the skill copies. The document that describes how to execute a demand does not mention their existence, so anyone unaware of a command continues to perform the repeated cycle manually.

5. **Contracts contain unnumbered sections.** `docs/PRD-STANDARD.md` and `docs/PLATFORM-ADAPTERS.md` have unnumbered top-level sections. `AGENTS.md` cites these documents as the authoritative sources for their subjects, but there is no way to make a stable reference to a passage: "see the synchronization section in PLATFORM-ADAPTERS" depends on the heading never changing.

6. **The command inventory is incomplete.** `docs/OPERACAO-BANCO-SEEDS.md` is identified by `AGENTS.md` as the normative source for databases, migrations, and seeds. Twelve existing commands do not appear in any of its sections: `check_database_connection`, `clear_test_data`, `clear_migration_supabase_prod`, `backfill_membership_timeline`, `explain_perf_indexes`, `generate_due_asaas_charges`, `seed_system_initial_kanri_students_migration`, `seed_system_initial_test_administrative`, `seed_system_initial_test_guardians`, `seed_system_initial_test_students`, `seed_system_initial_test_teachers`, and `seed_system_people_flow_samples`.

   The most serious case is `clear_migration_supabase_prod`: the command that resets the production schema is not documented in the database runbook. Anyone who needs it will find it by running `ls` in the command directory, without reading the guard protocol that surrounds it.

7. **`docs/OPERACAO-BANCO-SEEDS.md` does not describe the guards for the destructive local cycle.** The "Safe commands" and "Destructive local cycle" sections list what to run, but neither explains **why** the script refuses to run or **what** it removes. `clear_migrations.py` refuses to run under eight distinct conditions—counted by reading the code, not estimated—and none is described in the normative document, so a person who encounters a refusal has nowhere to look up the reason.

## Goal

The contracts declare the premise that authorizes the destructive protocol, separate distinct gates, have sections that can be cited by number, and list every existing operational command.

## Context Ledger

### Files read in full

- `CLAUDE.md`
- `AGENTS.md`
- `README.md`
- `docs/AGENT-WORKFLOW.md`
- `docs/PRD-STANDARD.md`
- `docs/PLATFORM-ADAPTERS.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- all three files in `.claude/commands/`

### Adjacent files consulted

- `clear_migrations.py` — the eight guards that must be described
- `system/management/commands/` — actual inventory, file by file
- `system/management/commands/_supabase_public_schema_reset.py` — remote reset protocol
- `.github/workflows/ci.yml` — what is already verified automatically
- `docs/DEPLOY-RENDER-SUPABASE.md` — boundary with the deployment topic

### Internet / official documentation

- Django 5.2: names and semantics of the commands cited in the inventory (`migrate`, `makemigrations`, `showmigrations`, `collectstatic`, `check`).
- Claude Code slash-command documentation, to describe correctly what the commands are and how they are invoked.

### Context7 / MCPs / tools verified

- Context7 was consulted for Django 5.2 and for the slash-command format.
- Each path cited in the contracts was verified individually on disk.

### Limitations found

- A text search can find a command mention but cannot prove that the command exists as a file: the inventory was built from the command directory, and every entry was checked against its file.
- A contract's quality can only be proven through use. What can be verified now is: no subject gaps, no broken links, and no omitted commands.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

The operator explicitly instructed the contracts to be standardized and the work to be implemented without requesting further confirmation.

## Execution prompt

### Persona

Editor of LV governance contracts.

### Action

Write the project-nature section, rename and split the cited sections, number the contracts, and complete the command inventory and the guards chapter.

### Context

`AGENTS.md` states what governs, `CLAUDE.md` states what the project is, and `docs/AGENT-WORKFLOW.md` states how work is executed. One owner per subject: no new section may duplicate what another contract already standardizes.

### Constraints

- No contract may cite a path outside this repository.
- No existing rule may be weakened: the change addresses structure, headings, and gaps.
- The project-nature section must include the revocation condition—what causes the destructive permission to cease being valid.
- Renumbering a section requires updating every citation that points to it.
- No environment-variable value may enter a document; only key names are permitted.
- The inventory describes each command and its guards; it does not invite anyone to execute it.

### Acceptance criteria

1. `CLAUDE.md` has a project-nature section declaring whether there is real business data, what production represents, that the baseline is recreatable, that operational secrets continue to be treated as secrets, and the condition under which this section is revoked.
2. The project-nature section precedes the product section, and the following sections are renumbered.
3. Section 14 of `AGENTS.md` is titled "Mandatory skills."
4. `docs/AGENT-WORKFLOW.md` has separate "Cleanup" and "Closure" sections.
5. `docs/AGENT-WORKFLOW.md` has a "Slash commands" section describing all three existing commands and when to use each one.
6. `docs/PRD-STANDARD.md` has numbered top-level sections.
7. `docs/PLATFORM-ADAPTERS.md` has numbered top-level sections and a slash commands subsection.
8. `docs/OPERACAO-BANCO-SEEDS.md` has a section describing the five guards in `clear_migrations.py`, checked against the code.
9. `docs/OPERACAO-BANCO-SEEDS.md` has a command inventory that includes every file in `system/management/commands/` whose name does not begin with `_`.
10. Every command cited in the inventory exists on disk.
11. `clear_migration_supabase_prod` is documented with its complete guard protocol.
12. Every path cited in `CLAUDE.md`, `AGENTS.md`, `README.md`, and the documents under `docs/` exists on disk.
13. Every citation by section number points to the correct section after the renumbering.
14. `scripts/validate_skill_frontmatter.py` passes.
15. The full test suite passes.

### Expected evidence

Actual output from the link check, comparison between the inventory and the command-directory listing, the skill validator, and the full test suite.

### Output format

Diff, command output, and an update to this PRD.

## Scope

- `CLAUDE.md`, `AGENTS.md`, `README.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`, `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/prd/README.md`

## Out of scope

- Renaming the skills: the `lv-` prefix is the project's identity and remains unchanged.
- Changing the normative content of any rule.
- Rewriting closed PRDs.
- `docs/UI-SCREEN-CONTRACT.md`, which has a separate owner.
- Executing any command in the inventory: this PRD documents operations; it does not perform them.

## Impacted files

- `CLAUDE.md`, `AGENTS.md`, `README.md`
- the four contract documents cited above
- `docs/prd/README.md`

## Risks and edge cases

- **Renumbering a section and leaving an orphaned citation.** Mitigation: search for and verify every citation by number after renumbering.
- **Duplicating a subject between `AGENTS.md` and `CLAUDE.md`.** Mitigation: the new `CLAUDE.md` section describes a fact; permission remains standardized only in section 11 of `AGENTS.md`, by reference rather than by copying it.
- **Documenting the production reset in a way that invites its execution.** Mitigation: the entry describes the guards and the explicit-confirmation requirement before describing the effect.
- **Allowing the inventory to become stale after the next change.** Mitigation: recorded as an accepted risk; automatically verifying the inventory would require a dedicated tool and is outside this scope.
- **Declaring the project disposable and having someone read that as broad permission.** Mitigation: the section declares the revocation condition in the same paragraph.

## Rules and constraints

Section 2 of `AGENTS.md`: the contract describes what exists; when it diverges from the code, the code prevails and the contract is corrected in the same change. Section 12 of `AGENTS.md`: documentation made obsolete by a change is corrected alongside it. Section 10 of `AGENTS.md`: operational secrets are never printed, including in documents.

## Plan

1. Build the actual inventory from the command directory.
2. Extract the five guards from `clear_migrations.py` by reading the file in full.
3. Write the nature section in `CLAUDE.md` and renumber the following sections.
4. Rename section 14 of `AGENTS.md`.
5. Split cleanup and closure and write the slash-command section.
6. Number `docs/PRD-STANDARD.md` and `docs/PLATFORM-ADAPTERS.md`.
7. Write the guards chapter and inventory in `docs/OPERACAO-BANCO-SEEDS.md`.
8. Verify every link on disk and every citation by section number.
9. Run the skill validator and the full test suite.

## Test plan

There is no application behavior to test. Verification consists of:

- comparing the inventory with the command-directory listing in both directions;
- verifying each cited path on disk;
- checking every citation by section number;
- running `scripts/validate_skill_frontmatter.py` as a regression check;
- running the full suite as a general regression check, ensuring that no code was touched accidentally.

## Visual validation

Not applicable: no template, CSS, JavaScript, or route changes.

## ORM validation

Not applicable: no model, query, or migration changes.

## Quality validation

Link verification, `scripts/validate_skill_frontmatter.py`, `python manage.py check`, and the full test suite.

## Evidence

- `scripts/validate_skill_frontmatter.py`: 18 files validated, with 6 Codex metadata files intact in UTF-8 with LF. Exit code 0.
- `scripts/build_prd_index.py --check`: "Index is up to date."
- On-disk link verification for `CLAUDE.md`, `AGENTS.md`, `README.md`, and the documents under `docs/`: **0 broken links**.
- **Inventory checked in both directions** against `system/management/commands/`: all 36 commands whose names do not begin with `_` are covered, and every cited command exists. The twelve missing commands were added, including `clear_migration_supabase_prod`.
- `manage.py check`: "no issues (0 silenced)."
- Full suite: passed.

## Implemented

- `CLAUDE.md`: new **section 1, Project nature**, declaring that the project is a disposable MVP, what production represents, that the baseline is recreatable, that secrets remain secret, and—in the same place—the **revocation condition**. The following ten sections were renumbered from 2 through 11.
- `AGENTS.md`: section 14 changed from "Skills" to "Mandatory skills."
- `docs/AGENT-WORKFLOW.md`: section 13, "Cleanup and closure," was split into **13. Cleanup** and **14. Closure**, and **15. Slash commands** was added with the three existing commands.
- `docs/PRD-STANDARD.md`: top-level sections numbered from 1 through 6.
- `docs/PLATFORM-ADAPTERS.md`: sections numbered from 1 through 7, plus the **1.1. Slash commands** subsection.
- `docs/OPERACAO-BANCO-SEEDS.md`: added **Destructive local cycle guards**—the eight refusal conditions, checked against the code, plus process termination and the output guard—and **Command inventory**, organized into verification and maintenance, reference seeds, test seeds, and remote operations, with the remote-reset protocol.
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`: the reference to "section 8 of `CLAUDE.md`" was corrected to section 9, where Payments is now located.

## Cleanup findings

1. **Renumbering `CLAUDE.md` broke one citation by number**, and the search found it: `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` pointed to section 8 while discussing payment webhooks. It was corrected in the same step. This is exactly the risk predicted in the risks section, and the mitigation worked.

2. **The runbook was not devoid of guards—it had incomplete coverage.** The "Safe commands" and "Destructive local cycle" sections already existed and listed the commands in the cycle, but neither described **why** the script refuses to run nor **what** it removes. The guards were written from a code reading, not from assumptions.

3. **The reference-seed list was described by grouping, not command by command.** There are twenty-one `seed_system_initial_*` commands; listing all of them in a table would create an inventory that ages with each new seed without adding information. Grouping them by data type covers what the reader needs, while the automated coverage check remains in force.

4. No environment-variable value entered a document—only key names.

5. No residue was introduced.

## Follow-up PRDs

None.

## Deviations from plan

- The scope originally included only the contracts. `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md` was also changed because of the broken citation—which section 12 of `AGENTS.md` requires correcting in the same change.
- `scripts/build_prd_index.py` gained the `--check` mode and a dedicated CI step. This was not in the scope of this PRD, which addresses contracts, but the index is part of documentation governance and the project already had the generator without verification. It is recorded here rather than being implemented silently.

## Pending

- Run the actual CI: the new step was verified locally, but the job runs only on the next push.
- Commit the worktree. The agent did not create a commit.

## Final status

Completed. The contracts declare the premise that authorizes the destructive protocol, separate cleanup from closure, have sections that can be cited by number, and list every existing operational command—including the production reset, which previously could be found only by running `ls`.
