# Índice de PRDs

Índice canônico de `docs/prd/`. Toda PRD usa `PRD-<NNN>-<slug>.md` com número único — ver `docs/PRD-STANDARD.md`.

Antes de criar uma PRD nova, conferir o último número desta tabela (não usar `ls` isolado, que não revela gaps reservados).

## Renumeração de duplicatas (PRD-079)

Em 2026-06-30 havia números duplicados: `008`, `009`, `014`, `015`, `016`, `021`, `028`. Para cada par, o documento com referências de entrada (citado por outra PRD) ou continuidade temática ficou no número original; o outro foi renumerado para o próximo número livre, sem perda de conteúdo (rename via `git mv`, título interno e referências cruzadas atualizados via `rg`).

| Número original | Arquivo mantido no número | Arquivo renumerado | Novo número |
|---|---|---|---|
| 008 | `PRD-008-adjust-instructor-and-student-panels-for-schedule-check-in-and-attendance-history.md` | `PRD-008-adjust-instructor-and-student-panels-for-schedule-check-in-and-attendance-history.md` | `PRD-022` |
| 009 | `PRD-009-shop-at-the-authenticated-portal-with-pre-order-arrival-queue-and-student-history.md` | `PRD-009-shop-at-the-authenticated-portal-with-pre-order-arrival-queue-and-student-history.md` | `PRD-055` |
| 014 | `PRD-014-admin-panel-as-portal-persona.md` | `PRD-014-admin-panel-as-portal-persona.md` | `PRD-090` |
| 015 | `PRD-015-initial-graduation-in-registration.md` | `PRD-015-initial-graduation-in-registration.md` | `PRD-086` |
| 016 | `PRD-016-identity-in-the-side-menu.md` | `PRD-016-identity-in-the-side-menu.md` | `PRD-087` |
| 021 | `PRD-021-separate-payment-steps-in-the-registration-wizard.md` | `PRD-021-separate-payment-steps-in-the-registration-wizard.md` (superada pelo PRD-040) | `PRD-088` |
| 028 | `PRD-028-home-and-people-in-full-screen.md` | `PRD-028-home-and-people-in-full-screen.md` | `PRD-089` |

Os números `022` e `055` eram gaps livres (nunca usados) e foram reaproveitados antes de abrir números novos no final da sequência (`086`–`090`).

## Tabela completa

**Próximo número livre: 192**

Status extraído da seção `## Final status` de cada arquivo, nunca
digitado à mão. Regenerar com `python scripts/build_prd_index.py`.

| N | Título | Status | Arquivo |
|---:|---|---|---|
| 001 | Client registration with CPF validation | — | [PRD-001-client-registration-with-cpf-validation.md](PRD-001-client-registration-with-cpf-validation.md) |
| 002 | Simplify class display during registration | — | [PRD-002-simplify-class-display-in-registration.md](PRD-002-simplify-class-display-in-registration.md) |
| 003 | Adjust the martial arts question during registration | — | [PRD-003-adjust-martial-arts-question-in-registration.md](PRD-003-adjust-martial-arts-question-in-registration.md) |
| 004 | Fix the materials catalog by variant | — | [PRD-004-correction-of-catalogue-of-materials-by-variant.md](PRD-004-correction-of-catalogue-of-materials-by-variant.md) |
| 005 | Fix materials by IBJJF rule and the selection UI | — | [PRD-005-correction-of-materials-by-rule-ibjjf-and-selection-ui.md](PRD-005-correction-of-materials-by-rule-ibjjf-and-selection-ui.md) |
| 006 | Standardize the plan change screen with the portal design system | — | [PRD-006-standardize-plan-change-screen-with-portal-design-system.md](PRD-006-standardize-plan-change-screen-with-portal-design-system.md) |
| 007 | Reformulate plans, pricing, eligibility, and Adult vs Kids/Juvenile targeting | — | [PRD-007-reformulate-plans-pricing-eligibility-and-targeting-adult-vs-kids-juvenile.md](PRD-007-reformulate-plans-pricing-eligibility-and-targeting-adult-vs-kids-juvenile.md) |
| 008 | Adjust the instructor and student panels for schedule, check-in, and attendance history | — | [PRD-008-adjust-instructor-and-student-panels-for-schedule-check-in-and-attendance-history.md](PRD-008-adjust-instructor-and-student-panels-for-schedule-check-in-and-attendance-history.md) |
| 009 | Shop in the authenticated portal with pre-orders, arrival queue, and student history | — | [PRD-009-shop-at-the-authenticated-portal-with-pre-order-arrival-queue-and-student-history.md](PRD-009-shop-at-the-authenticated-portal-with-pre-order-arrival-queue-and-student-history.md) |
| 010 | Graduation control module (belts, degrees, rules, and overview) | — | [PRD-010-graduation-control-module-belts-degrees-rules-and-overview.md](PRD-010-graduation-control-module-belts-degrees-rules-and-overview.md) |
| 011 | Home with a collapsed graduation section | — | [PRD-011-home-with-collapsed-graduation-section.md](PRD-011-home-with-collapsed-graduation-section.md) |
| 012 | Financial module and payouts | — | [PRD-012-financial-module-and-payouts.md](PRD-012-financial-module-and-payouts.md) |
| 013 | Instructor quick actions on the home | — | [PRD-013-instructor-home-quick-actions.md](PRD-013-instructor-home-quick-actions.md) |
| 014 | Administrative panel as a portal persona | — | [PRD-014-admin-panel-as-portal-persona.md](PRD-014-admin-panel-as-portal-persona.md) |
| 015 | Initial graduation during registration | — | [PRD-015-initial-graduation-in-registration.md](PRD-015-initial-graduation-in-registration.md) |
| 016 | Identity in the side menu | — | [PRD-016-identity-in-the-side-menu.md](PRD-016-identity-in-the-side-menu.md) |
| 017 | Auditable granular seeds | — | [PRD-017-verifiable-granular-seeds.md](PRD-017-verifiable-granular-seeds.md) |
| 018 | Mobile buttons on the instructor's home | — | [PRD-018-instructor-home-mobile-buttons.md](PRD-018-instructor-home-mobile-buttons.md) |
| 019 | Standardize the plan change screen with the registration `plan-selector` pattern | — | [PRD-019-plan-change-plan-selector-standard.md](PRD-019-plan-change-plan-selector-standard.md) |
| 020 | Plan change with balance→time, future credit, and automatic refund | — | [PRD-020-plan-change-balance-future-credit-and-auto-refund.md](PRD-020-plan-change-balance-future-credit-and-auto-refund.md) |
| 021 | Separate payment steps in the registration wizard | — | [PRD-021-separate-payment-steps-in-the-registration-wizard.md](PRD-021-separate-payment-steps-in-the-registration-wizard.md) |
| 022 | Consolidate the public landing page and remove outdated public pages | — | [PRD-022-consolidating-public-landing-and-removing-outdated-public-pages.md](PRD-022-consolidating-public-landing-and-removing-outdated-public-pages.md) |
| 023 | Optional seeds, `.env` orchestrator, initial data in JSON | — | [PRD-023-optional-seeds-env-orchestrator-initial-data-in-json.md](PRD-023-optional-seeds-env-orchestrator-initial-data-in-json.md) |
| 024 | Atomic, decoupled seed governance | — | [PRD-024-atomic-decoupled-seed-governance.md](PRD-024-atomic-decoupled-seed-governance.md) |
| 025 | Responsive redesign of the LV system | — | [PRD-025-responsive-redesign-of-the-lv-system.md](PRD-025-responsive-redesign-of-the-lv-system.md) |
| 026 | Responsive redesign of People | — | [PRD-026-responsive-redesign-of-people.md](PRD-026-responsive-redesign-of-people.md) |
| 027 | Responsive redesign of the master home | — | [PRD-027-responsive-admin-home-redesign.md](PRD-027-responsive-admin-home-redesign.md) |
| 028 | Home and People in full screen | — | [PRD-028-home-and-people-in-full-screen.md](PRD-028-home-and-people-in-full-screen.md) |
| 029 | Person editing with a proportional UI and graduation context | — | [PRD-029-person-editing-graduation-and-ui.md](PRD-029-person-editing-graduation-and-ui.md) |
| 030 | Login screen — implementation from scratch | — | [PRD-030-login-screen.md](PRD-030-login-screen.md) |
| 031 | Standardize the seed JSON files | — | [PRD-031-standardize-seed-json-files.md](PRD-031-standardize-seed-json-files.md) |
| 032 | Instructor payout seed | — | [PRD-032-instructor-payout-seed.md](PRD-032-instructor-payout-seed.md) |
| 033 | Seed for initial holidays | — | [PRD-033-seed-for-initial-holidays.md](PRD-033-seed-for-initial-holidays.md) |
| 034 | Temporary removal of screen tests | — | [PRD-034-temporary-screen-test-removal.md](PRD-034-temporary-screen-test-removal.md) |
| 035 | Subscription plan value seed | — | [PRD-035-subscription-plan-value-seed.md](PRD-035-subscription-plan-value-seed.md) |
| 036 | Payment icons in registration | — | [PRD-036-payment-icons-in-the-registration.md](PRD-036-payment-icons-in-the-registration.md) |
| 037 | Remove Stripe from the checkout and use Asaas | — | [PRD-037-remove-stripe-from-checkout-and-use-asaas.md](PRD-037-remove-stripe-from-checkout-and-use-asaas.md) |
| 038 | Redesign of the `Materiais e equipamentos` (`Materials and equipment`) step in the registration wizard | — | [PRD-038-materials-and-equipment-registration-wizard-step-redesign.md](PRD-038-materials-and-equipment-registration-wizard-step-redesign.md) |
| 039 | Standardize the registration flow — guardian, Asaas, home, plan multiplier | — | [PRD-039-registration-flow-guardian-asaas-home-multiplier.md](PRD-039-registration-flow-guardian-asaas-home-multiplier.md) |
| 040 | Uncompromising registration flow with payment before creating a Person | — | [PRD-040-payment-before-person-creation-registration-flow.md](PRD-040-payment-before-person-creation-registration-flow.md) |
| 041 | Stripe — recurring plans | — | [PRD-041-stripe-recurring-plans.md](PRD-041-stripe-recurring-plans.md) |
| 042 | Discount coupons | — | [PRD-042-discount-coupons.md](PRD-042-discount-coupons.md) |
| 043 | Home unified by permission | — | [PRD-043-home-unified-by-permission.md](PRD-043-home-unified-by-permission.md) |
| 044 | Home — functional and visual redesign | — | [PRD-044-home-functional-and-visual-redesign.md](PRD-044-home-functional-and-visual-redesign.md) |
| 045 | People module — list, detail, form, and delete confirmation | — | [PRD-045-people-list-and-detail.md](PRD-045-people-list-and-detail.md) |
| 046 | Student and instructor portal — enriched graduation + schedule management on the dashboard | — | [PRD-046-student-and-instructor-portal-graduation-schedule-dashboard-management.md](PRD-046-student-and-instructor-portal-graduation-schedule-dashboard-management.md) |
| 047 | Home dashboard — redesign with attendance modals and graduation history | — | [PRD-047-home-dashboard-redesign-with-presence-modules-and-graduation-history.md](PRD-047-home-dashboard-redesign-with-presence-modules-and-graduation-history.md) |
| 048 | Finances on the dashboard — the instructor's payout and the student's tuition | — | [PRD-048-student-instructor-financial-dashboard.md](PRD-048-student-instructor-financial-dashboard.md) |
| 049 | Instructor self check-in | — | [PRD-049-instructor-self-checkin.md](PRD-049-instructor-self-checkin.md) |
| 050 | Administrative plans module | — | [PRD-050-administrative-module-of-plans.md](PRD-050-administrative-module-of-plans.md) |
| 051 | Migration JSON for Kanri students | — | [PRD-051-json-for-the-migration-of-kanri-students.md](PRD-051-json-for-the-migration-of-kanri-students.md) |
| 052 | Kanri student migration seed | — | [PRD-052-seed-of-migration-of-students-kanri.md](PRD-052-seed-of-migration-of-students-kanri.md) |
| 053 | Safe Render/Supabase reset | — | [PRD-053-safe-render-supabase-reset.md](PRD-053-safe-render-supabase-reset.md) |
| 054 | Architectural alignment and safe reset | — | [PRD-054-architectural-alignment-and-safe-reset.md](PRD-054-architectural-alignment-and-safe-reset.md) |
| 055 | Check-in with instructor approval + parity in schedule management | — | [PRD-055-checkin-with-instructor-approval.md](PRD-055-checkin-with-instructor-approval.md) |
| 056 | Post-payment wizard — blocking backward navigation and rehydrating classes | — | [PRD-056-post-payment-wizard-navigation-and-rehydration.md](PRD-056-post-payment-wizard-navigation-and-rehydration.md) |
| 057 | Wizard simplification — state fixes and removal of development code | — | [PRD-057-wizard-simplification-state-correction-and-developer-code-removal.md](PRD-057-wizard-simplification-state-correction-and-developer-code-removal.md) |
| 058 | Asaas and Stripe webhook validation — local and staging | — | [PRD-058-asaas-stripe-webhook-validation-local-and-staging.md](PRD-058-asaas-stripe-webhook-validation-local-and-staging.md) |
| 059 | Lean governance for Claude, Codex, and Cursor | — | [PRD-059-lean-governance-for-claude-codex-and-cursor.md](PRD-059-lean-governance-for-claude-codex-and-cursor.md) |
| 060 | Multi-platform governance parity + the lv-prompt-builder skill | — | [PRD-060-multi-platform-governance-parity-skill-lv-prompt-builder.md](PRD-060-multi-platform-governance-parity-skill-lv-prompt-builder.md) |
| 061 | Governance alignment — workflow and adapters | — | [PRD-061-governance-alignment-workflow-and-adapters.md](PRD-061-governance-alignment-workflow-and-adapters.md) |
| 062 | Audit of the signal → idempotent service pattern | — | [PRD-062-signal-standard-auditing-idempotent-service.md](PRD-062-signal-standard-auditing-idempotent-service.md) |
| 063 | Person cascade deletion integrity | — | [PRD-063-person-cascade-deletion-integrity.md](PRD-063-person-cascade-deletion-integrity.md) |
| 064 | Public wizard — consolidating the state machine, authoritative rehydration, and post-payment continuity | — | [PRD-064-public-wizard-state-machine-authoritative-rehydration-and-post-payment-continuity.md](PRD-064-public-wizard-state-machine-authoritative-rehydration-and-post-payment-continuity.md) |
| 065 | Administrative hubs of the LV modules | — | [PRD-065-administrative-hubs-of-the-lv-modules.md](PRD-065-administrative-hubs-of-the-lv-modules.md) |
| 066 | Visual and modal CRUD pattern | — | [PRD-066-visual-and-modal-crud-pattern.md](PRD-066-visual-and-modal-crud-pattern.md) |
| 067 | People CSS parity — filters, KPIs, rows, and responsiveness | — | [PRD-067-css-parity-of-persons-filters-kpis-lines-and-responsiveness.md](PRD-067-css-parity-of-persons-filters-kpis-lines-and-responsiveness.md) |
| 068 | Progressive single login | — | [PRD-068-clean-people-rework-and-lv-foundation.md](PRD-068-clean-people-rework-and-lv-foundation.md) |
| 069 | The LV home with mature visual governance | — | [PRD-069-lv-home-with-mature-visual-governance.md](PRD-069-lv-home-with-mature-visual-governance.md) |
| 070 | Operational governance without a local lockdown | — | [PRD-070-operational-governance-without-local-lockdown.md](PRD-070-operational-governance-without-local-lockdown.md) |
| 071 | Aligning the legacy suite with the progressive scope | — | [PRD-071-alignment-of-the-suite-inherited-to-the-progressive-scope.md](PRD-071-alignment-of-the-suite-inherited-to-the-progressive-scope.md) |
| 072 | Fixes to the instructor home, attendance, and mobile | — | [PRD-072-corrections-of-the-instructor-s-home-front-desk-and-mobile.md](PRD-072-corrections-of-the-instructor-s-home-front-desk-and-mobile.md) |
| 073 | Administrative seeds and a consistent bootstrap | — | [PRD-073-administrative-seeds-and-consistent-bootstrap.md](PRD-073-administrative-seeds-and-consistent-bootstrap.md) |
| 074 | Cumulative operational roles and minimum permissions | — | [PRD-074-cumulative-operational-roles-and-permissions.md](PRD-074-cumulative-operational-roles-and-permissions.md) |
| 075 | UI foundation, English routes, and modal CRUD | — | [PRD-075-ui-foundation-routes-in-english-and-modal-crud.md](PRD-075-ui-foundation-routes-in-english-and-modal-crud.md) |
| 076 | Legacy, governance, and documentation audit | — | [PRD-076-legacy-audit-governance-and-documentation.md](PRD-076-legacy-audit-governance-and-documentation.md) |
| 077 | CRUD MVP of the martial arts academy | — | [PRD-077-crud-mvp-of-the-martial-arts-academy.md](PRD-077-crud-mvp-of-the-martial-arts-academy.md) |
| 078 | Active routes with missing templates | — | [PRD-078-active-routes-with-missing-templates.md](PRD-078-active-routes-with-missing-templates.md) |
| 079 | Normalize the duplicate PRD index | — | [PRD-079-normalize-duplicate-prd-index.md](PRD-079-normalize-duplicate-prd-index.md) |
| 080 | Refactor JavaScript without insecure innerHTML | — | [PRD-080-refactoring-javascript-without-insecure-innerhtml.md](PRD-080-refactoring-javascript-without-insecure-innerhtml.md) |
| 081 | Extract the registration and payment services from the wizard | — | [PRD-081-extract-registration-and-payment-services-from-the-wizard.md](PRD-081-extract-registration-and-payment-services-from-the-wizard.md) |
| 082 | README and requirements-dev aligned with LV | — | [PRD-082-readme-and-requirements-dev-aligned-with-lv.md](PRD-082-readme-and-requirements-dev-aligned-with-lv.md) |
| 083 | Archive the legacy documentation in static | — | [PRD-083-archiving-legacy-documentation-in-static.md](PRD-083-archiving-legacy-documentation-in-static.md) |
| 084 | CSS tokens and inline style removal | — | [PRD-084-css-tokens-and-inline-style-removal.md](PRD-084-css-tokens-and-inline-style-removal.md) |
| 085 | ASCII output in management commands under PowerShell | — | [PRD-085-output-of-ascii-in-management-commands-in-powershell.md](PRD-085-output-of-ascii-in-management-commands-in-powershell.md) |
| 086 | Payouts without early withdrawal | — | [PRD-086-payouts-without-early-withdrawal.md](PRD-086-payouts-without-early-withdrawal.md) |
| 087 | Remove inicial_seed | — | [PRD-087-remove-initial-seed.md](PRD-087-remove-initial-seed.md) |
| 088 | Full registration flow review — pre-registration, sequential payment, and explicit finalization | — | [PRD-088-full-registration-flow-review.md](PRD-088-full-registration-flow-review.md) |
| 089 | Plans CRUD with dynamic pricing | — | [PRD-089-crud-of-plans-with-dynamic-pricing.md](PRD-089-crud-of-plans-with-dynamic-pricing.md) |
| 090 | Registration wizard UI fixes | — | [PRD-090-registration-wizard-ui-fixes.md](PRD-090-registration-wizard-ui-fixes.md) |
| 091 | Operational roles UI in the person form | — | [PRD-091-operational-role-ui-on-person-form.md](PRD-091-operational-role-ui-on-person-form.md) |
| 092 | Home split into My area and Management | — | [PRD-092-home-split-my-area-and-management.md](PRD-092-home-split-my-area-and-management.md) |
| 093 | A guardian starting training and enrollment | — | [PRD-093-responsible-for-initiating-training-and-enrollment.md](PRD-093-responsible-for-initiating-training-and-enrollment.md) |
| 094 | Student check-in with a dual role and the instructor precondition | — | [PRD-094-student-checkin-dual-role-instructor-precondition.md](PRD-094-student-checkin-dual-role-instructor-precondition.md) |
| 095 | Canonical Obsidian seed order and documentation | — | [PRD-095-obsidian-seed-canonical-order-and-documentation.md](PRD-095-obsidian-seed-canonical-order-and-documentation.md) |
| 096 | UTF-8 encoding of the schedule template | — | [PRD-096-encoding-utf-8-from-the-schedule-template.md](PRD-096-encoding-utf-8-from-the-schedule-template.md) |
| 097 | Orphaned calendar views with no routes | — | [PRD-097-orphan-calendar-views-without-routes.md](PRD-097-orphan-calendar-views-without-routes.md) |
| 098 | Operational audit module | — | [PRD-098-operational-audit-module.md](PRD-098-operational-audit-module.md) |
| 099 | Person edit permission for support roles | — | [PRD-099-permission-to-edit-person-for-support.md](PRD-099-permission-to-edit-person-for-support.md) |
| 100 | The Profiles route versus operational roles | — | [PRD-100-routes-profiles-versus-operational-roles.md](PRD-100-routes-profiles-versus-operational-roles.md) |
| 101 | Public shop, pre-orders, and the student's history | — | [PRD-101-public-store-pre-orders-and-student-history.md](PRD-101-public-store-pre-orders-and-student-history.md) |
| 102 | Material category CRUD | — | [PRD-102-crud-of-category-of-material.md](PRD-102-crud-of-category-of-material.md) |
| 103 | Subscription actions in the person detail | — | [PRD-103-subscription-actions-in-person-detail.md](PRD-103-subscription-actions-in-person-detail.md) |
| 104 | Removing dead code from the registration wizard (onEnterCheckout) | — | [PRD-104-remove-dead-code-from-checkout-wizard.md](PRD-104-remove-dead-code-from-checkout-wizard.md) |
| 105 | A "My dependents" section on the guardian's home | — | [PRD-105-my-dependents-section-on-guardian-home.md](PRD-105-my-dependents-section-on-guardian-home.md) |
| 106 | The guardian cannot buy/see materials on a dependent's behalf | — | [PRD-106-guardian-material-purchase-for-dependent.md](PRD-106-guardian-material-purchase-for-dependent.md) |
| 107 | The instructor can approve a check-in for an already-cancelled regular class | — | [PRD-107-approve-checkin-for-cancelled-class.md](PRD-107-approve-checkin-for-cancelled-class.md) |
| 108 | The instructor payout counts a cancelled class; `TeacherFinancialView` is dead code | — | [PRD-108-instructor-payout-cancelled-class-and-dead-view.md](PRD-108-instructor-payout-cancelled-class-and-dead-view.md) |
| 109 | The administrative calendar crashes when an open class falls on a holiday | — | [PRD-109-calendar-crash-when-special-class-falls-on-holiday.md](PRD-109-calendar-crash-when-special-class-falls-on-holiday.md) |
| 110 | Graduation eligibility counts a cancelled class/open class | — | [PRD-110-graduation-counts-cancelled-class.md](PRD-110-graduation-counts-cancelled-class.md) |
| 111 | Staging seeds for N:N registration | — | [PRD-111-staging-seeds-registration-nn.md](PRD-111-staging-seeds-registration-nn.md) |
| 112 | A pending request for administrative access | — | [PRD-112-request-for-administrative-access-pending.md](PRD-112-request-for-administrative-access-pending.md) |
| 113 | An instructor's class and schedule request | — | [PRD-113-instructor-class-and-schedule-request.md](PRD-113-instructor-class-and-schedule-request.md) |
| 114 | Veteran plan (formerly Loyalty) eligibility by tenure | — | [PRD-114-veteran-plan-eligibility.md](PRD-114-veteran-plan-eligibility.md) |
| 115 | A sequential operational profile wizard | — | [PRD-115-sequential-operating-profile-wizard.md](PRD-115-sequential-operating-profile-wizard.md) |
| 116 | The student home with permissions, a modal schedule, and the loyalty period | — | [PRD-116-student-home-with-permissions-modal-schedule-and-loyalty.md](PRD-116-student-home-with-permissions-modal-schedule-and-loyalty.md) |
| 117 | Contractual loyalty for recurring plans | — | [PRD-117-contractual-fidelity-to-recurring-plans.md](PRD-117-contractual-fidelity-to-recurring-plans.md) |
| 118 | Adding a dependent after enrollment | — | [PRD-118-add-dependent-after-enrollment.md](PRD-118-add-dependent-after-enrollment.md) |
| 119 | A dependent with materials, idempotency, and a pending CPF | — | [PRD-119-dependent-material-idempotency-and-cpf.md](PRD-119-dependent-material-idempotency-and-cpf.md) |
| 120 | The dependent in a modal on the home | — | [PRD-120-modal-dependent-at-home.md](PRD-120-modal-dependent-at-home.md) |
| 121 | The client home with dependents, monthly fees, and a modal CRUD | — | [PRD-121-client-home-dependents-tuition-and-modal-crud.md](PRD-121-client-home-dependents-tuition-and-modal-crud.md) |
| 122 | Undoing a student's pending check-in | — | [PRD-122-undo-pending-student-checkin.md](PRD-122-undo-pending-student-checkin.md) |
| 123 | The client account modal with editing and deletion | — | [PRD-123-client-account-modal-with-editing-and-deletion.md](PRD-123-client-account-modal-with-editing-and-deletion.md) |
| 124 | A dependent with an upgrade to a family plan | — | [PRD-124-dependent-family-plan-upgrade.md](PRD-124-dependent-family-plan-upgrade.md) |
| 125 | Remote synchronization of the Stripe family upgrade | — | [PRD-125-remote-synchronization-of-the-stripe-family-upgrade.md](PRD-125-remote-synchronization-of-the-stripe-family-upgrade.md) |
| 126 | Preventing a duplicate Stripe charge on the same card between the main person and the dependent | — | [PRD-126-prevent-duplicate-stripe-charge-on-same-card-for-holder-and-dependent.md](PRD-126-prevent-duplicate-stripe-charge-on-same-card-for-holder-and-dependent.md) |
| 127 | The family discount as a single-tier modifier (a pricing rework) | — | [PRD-127-family-discount-single-tier-pricing.md](PRD-127-family-discount-single-tier-pricing.md) |
| 128 | The PlanTier/PlanPrice CRUD, the discount UI, and a real cancellation lock during the commitment period | — | [PRD-128-crud-plantier-planprice-discount-ui-and-cancellation-lock.md](PRD-128-crud-plantier-planprice-discount-ui-and-cancellation-lock.md) |
| 129 | Migrating the public registration (`register.js`) to the PlanTier/PlanPrice catalog | — | [PRD-129-migrate-public-registration-to-plantier-planprice-catalog.md](PRD-129-migrate-public-registration-to-plantier-planprice-catalog.md) |
| 130 | Migrating the plan change (upgrade/downgrade) to the PlanTier/PlanPrice catalog | — | [PRD-130-migrate-plan-change-to-plantier-planprice-catalog.md](PRD-130-migrate-plan-change-to-plantier-planprice-catalog.md) |
| 131 | Fixing the instructor's default presence when cancelling/restoring a class | — | [PRD-131-fix-default-instructor-present-on-cancel-and-restore-class.md](PRD-131-fix-default-instructor-present-on-cancel-and-restore-class.md) |
| 132 | Free transitions between plans + a monthly fee pause (a medical note and a freeze) | — | [PRD-132-free-plan-transitions-and-tuition-pause.md](PRD-132-free-plan-transitions-and-tuition-pause.md) |
| 133 | Payment method indicator, Stripe card change, and failed-payment history | — | [PRD-133-payment-indicator-and-stripe-card-change.md](PRD-133-payment-indicator-and-stripe-card-change.md) |
| 134 | Subscription and family event history — client information timeline and admin technical audit | — | [PRD-134-subscription-family-event-history-information-timeline-client-technical-audit-admin.md](PRD-134-subscription-family-event-history-information-timeline-client-technical-audit-admin.md) |
| 135 | Automated recurring Asaas billing synchronized with family discounts and historical timeline-event backfill | — | [PRD-135-recurring-asaas-billing-backfill-timeline.md](PRD-135-recurring-asaas-billing-backfill-timeline.md) |
| 136 | Silent failure of the "Pay tuition" button and confirmation of the Asaas address flow | — | [PRD-136-silent-failure-pay-tuition-address-flow-asaas.md](PRD-136-silent-failure-pay-tuition-address-flow-asaas.md) |
| 137 | Missing Recurring Stripe for Long Cycles and Broken Asaas Installments in the New Catalog | — | [PRD-137-recurring-stripe-long-cycles-and-broken-asaas-installments-in-new-catalog.md](PRD-137-recurring-stripe-long-cycles-and-broken-asaas-installments-in-new-catalog.md) |
| 138 | Architectural Audit — Single Flow and MVP Consistency | — | [PRD-138-architectural-audit-single-flow-and-consistency-of-mvp.md](PRD-138-architectural-audit-single-flow-and-consistency-of-mvp.md) |
| 139 | Full-Coverage Audit — File-by-File Inventory | — | [PRD-139-full-coverage-audit-file-by-file-inventory.md](PRD-139-full-coverage-audit-file-by-file-inventory.md) |
| 140 | Dependent Wizard Fixes | — | [PRD-140-dependent-wizard-fixes.md](PRD-140-dependent-wizard-fixes.md) |
| 141 | In-Depth Frontend Review — Identified Problems | — | [PRD-141-frontend-problem-review.md](PRD-141-frontend-problem-review.md) |
| 142 | Backend Review — Performance and Queries | — | [PRD-142-backend-performance-review.md](PRD-142-backend-performance-review.md) |
| 143 | MVT Review — Views, Models, and Forms | — | [PRD-143-mvt-views-models-and-forms-review.md](PRD-143-mvt-views-models-and-forms-review.md) |
| 144 | Implementation Backlog — July 2026 Scan (PRD-138 Through PRD-143) | — | [PRD-144-implementation-pending-items-july-2026-scan.md](PRD-144-implementation-pending-items-july-2026-scan.md) |
| 145 | Operational Audit of Registration, Payments, and Documentation | — | [PRD-145-registration-payment-documentation-operational-audit.md](PRD-145-registration-payment-documentation-operational-audit.md) |
| 146 | Public Instructor and Existing-Class Association | — | [PRD-146-public-instructor-and-link-to-existing-classes.md](PRD-146-public-instructor-and-link-to-existing-classes.md) |
| 147 | Post-Registration Functional Validation | — | [PRD-147-post-registration-functional-staging.md](PRD-147-post-registration-functional-staging.md) |
| 148 | Payout Activation for Publicly Registered Instructors | — | [PRD-148-instructor-payout-public-registration.md](PRD-148-instructor-payout-public-registration.md) |
| 149 | Single Requirements File — Eliminate `requirements-dev.txt` | — | [PRD-149-unique-requirements-eliminate-requirements-dev-txt.md](PRD-149-unique-requirements-eliminate-requirements-dev-txt.md) |
| 150 | Registration Validation + Existing-Instructor and Documentation Fixes | — | [PRD-150-registration-staging-existing-instructor-and-docs.md](PRD-150-registration-staging-existing-instructor-and-docs.md) |
| 151 | Close Post-Audit Gaps — admin.py, Plan Change/Cancellation Tests, and Real-Browser Validation | — | [PRD-151-close-post-audit-admin-test-and-real-browser-staging-gaps.md](PRD-151-close-post-audit-admin-test-and-real-browser-staging-gaps.md) |
| 152 | Password-Change Lifecycle — Signed-In, Forgotten Password with Default Password, and Admin Review | — | [PRD-152-password-change-cycle-validation-and-admin-review.md](PRD-152-password-change-cycle-validation-and-admin-review.md) |
| 153 | Fix the Recurring Stripe Billing-Period Filter in Public Registration | — | [PRD-153-fix-recurring-stripe-period-filter-in-public-registration.md](PRD-153-fix-recurring-stripe-period-filter-in-public-registration.md) |
| 154 | Disposable MVP Nature and Environment-Gate Removal | — | [PRD-154-disposable-mvp-and-gate-removal.md](PRD-154-disposable-mvp-and-gate-removal.md) |
| 155 | Conditional Authorization Gate — Align Skills with AGENTS.md | — | [PRD-155-conditional-authorization-gate.md](PRD-155-conditional-authorization-gate.md) |
| 156 | Skills — Structure, Real Commands, PRD Index, and Verifiable Synchronization | — | [PRD-156-skills-structure-actual-command-prd-index-and-verifiable-synchronization.md](PRD-156-skills-structure-actual-command-prd-index-and-verifiable-synchronization.md) |
| 157 | Contract Deduplication and CLAUDE.md Hygiene | — | [PRD-157-contract-deduplication-and-hygiene.md](PRD-157-contract-deduplication-and-hygiene.md) |
| 158 | Slash Commands for the Repeated Operational Lifecycle | — | [PRD-158-slash-commands-for-repeated-operational-cycle.md](PRD-158-slash-commands-for-repeated-operational-cycle.md) |
| 159 | Local Infrastructure and CI Hardening | — | [PRD-159-hardening-local-infrastructure-and-ci.md](PRD-159-hardening-local-infrastructure-and-ci.md) |
| 160 | Environment-Variable Reconciliation | — | [PRD-160-environment-variable-reconciliation.md](PRD-160-environment-variable-reconciliation.md) |
| 161 | Slash Commands, PRD Index, and Repository Hygiene | — | [PRD-161-slash-commands-prd-index-and-repository-hygiene.md](PRD-161-slash-commands-prd-index-and-repository-hygiene.md) |
| 162 | Hardened Remote Reset, Documented Deployment, and Observability | — | [PRD-162-hardened-remote-reset-documented-deployment-and-observability.md](PRD-162-hardened-remote-reset-documented-deployment-and-observability.md) |
| 163 | Skill Validator and CI Homogeneity | — | [PRD-163-validator-of-skills-and-homogeneity-of-the-ci.md](PRD-163-validator-of-skills-and-homogeneity-of-the-ci.md) |
| 164 | Self-Contained Contracts and CI Standardization | — | [PRD-164-self-contained-contracts-and-standardisation-of-the-ci.md](PRD-164-self-contained-contracts-and-standardisation-of-the-ci.md) |
| 165 | Honest Test Runner and Direct Dependencies | — | [PRD-165-honest-test-runner-and-direct-dependencies.md](PRD-165-honest-test-runner-and-direct-dependencies.md) |
| 166 | Contract Density and Operational Inventory | — | [PRD-166-contract-density-and-operation-inventory.md](PRD-166-contract-density-and-operation-inventory.md) |
| 167 | Secondary CI Workflow | — | [PRD-167-secondary-ci-workflow.md](PRD-167-secondary-ci-workflow.md) |
| 168 | Duplicate PRD Number Guard and Settings Hygiene | — | [PRD-168-duplicate-prd-number-guard-and-settings-hygiene.md](PRD-168-duplicate-prd-number-guard-and-settings-hygiene.md) |
| 169 | Protocol Contract Alignment | — | [PRD-169-leveling-of-protocol-contracts.md](PRD-169-leveling-of-protocol-contracts.md) |
| 170 | Product Contract Alignment | — | [PRD-170-leveling-of-product-contracts.md](PRD-170-leveling-of-product-contracts.md) |
| 171 | Infrastructure and Environment Alignment | — | [PRD-171-leveling-of-infrastructure-and-environment.md](PRD-171-leveling-of-infrastructure-and-environment.md) |
| 172 | Structural Cleanup and Comment-Free Code | — | [PRD-172-structural-cleanup-and-code-without-comment.md](PRD-172-structural-cleanup-and-code-without-comment.md) |
| 173 | Common Core of the Visual Contract | — | [PRD-173-common-core-of-the-visual-contract.md](PRD-173-common-core-of-the-visual-contract.md) |
| 174 | Operational Runbook Taxonomy | — | [PRD-174-taxonomy-of-the-operational-runbook.md](PRD-174-taxonomy-of-the-operational-runbook.md) |
| 175 | Unified CSS Token Vocabulary | — | [PRD-175-unique-vocabulary-of-css-tokens.md](PRD-175-unique-vocabulary-of-css-tokens.md) |
| 176 | Single Theme Stylesheet | — | [PRD-176-unique-theme-sheet.md](PRD-176-unique-theme-sheet.md) |
| 177 | Autonomous Agents and Triggers | — | [PRD-177-autonomous-agents-and-triggers.md](PRD-177-autonomous-agents-and-triggers.md) |
| 178 | Environment Files in the Shared Directory | — | [PRD-178-environment-in-the-shared-directory.md](PRD-178-environment-in-the-shared-directory.md) |
| 179 | Remote Environment Files Outside the Checkout | — | [PRD-179-remote-environment-outside-checkout.md](PRD-179-remote-environment-outside-checkout.md) |
| 180 | Missing Autonomous Agents and a Disguised PRD | — | [PRD-180-absent-autonomous-agents-and-disguised-prd.md](PRD-180-absent-autonomous-agents-and-disguised-prd.md) |
| 181 | Local Gates Missing from CI | — | [PRD-181-local-gates-missing-from-ci.md](PRD-181-local-gates-missing-from-ci.md) |
| 182 | Contracts Migrated to the Vault | — | [PRD-182-contracts-migrated-to-the-vault.md](PRD-182-contracts-migrated-to-the-vault.md) |
| 183 | Version-Control Hygiene | — | [PRD-183-versioning-hygiene.md](PRD-183-versioning-hygiene.md) |
| 184 | Minimal-Platform Load Budget | — | [PRD-184-minimal-platform-load-budget.md](PRD-184-minimal-platform-load-budget.md) |
| 185 | Checks Before Remote Operations | — | [PRD-185-checks-before-remote-operation.md](PRD-185-checks-before-remote-operation.md) |
| 186 | Environment-Key and Django-Version Contract | — | [PRD-186-environment-key-and-django-version-contract.md](PRD-186-environment-key-and-django-version-contract.md) |
| 187 | Validate the portal post-login redirect target | concluída | [PRD-187-validate-the-portal-post-login-redirect-target.md](PRD-187-validate-the-portal-post-login-redirect-target.md) |
| 188 | Replace the universal password-reset credential | concluída com limitações | [PRD-188-replace-the-universal-password-reset-credential.md](PRD-188-replace-the-universal-password-reset-credential.md) |
| 189 | Enforce the failed-login attempt limit | concluída | [PRD-189-enforce-the-failed-login-attempt-limit.md](PRD-189-enforce-the-failed-login-attempt-limit.md) |
| 190 | Rewrite historical governance PRDs from local evidence | concluída | [PRD-190-rewrite-historical-governance-prds-from-local-evidence.md](PRD-190-rewrite-historical-governance-prds-from-local-evidence.md) |
| 191 | Rewrite historical leveling PRDs as local contracts | concluída | [PRD-191-rewrite-historical-leveling-prds-as-local-contracts.md](PRD-191-rewrite-historical-leveling-prds-as-local-contracts.md) |
