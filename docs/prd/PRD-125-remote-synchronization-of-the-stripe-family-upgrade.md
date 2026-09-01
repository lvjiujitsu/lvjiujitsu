# PRD-125: Remote synchronization of the Stripe family upgrade

## Summary
Define the remote synchronization of a Stripe subscription when a main person with an active recurring plan adds a dependent and migrates to a family plan.

## Demand type
A technical payment follow-up outside PRD-124's scope.

## Current problem
PRD-124 fixes the wizard, the local validation, and the local creation of the family order/monthly fee. It does not change the main person's already-existing remote Stripe subscription. For main people with a `stripe_subscription_id`, the local state can be correct while the remote subscription is still on the previous plan.

## Goal
Create a transactional rule to migrate an existing Stripe subscription to the correct family plan, preserving the webhook, the local history, and idempotency.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `stripe:stripe-best-practices`
- `lv-cleanup-audit`

## Scope
- Map the local `Membership.stripe_subscription_id` to the Stripe subscription item.
- Define when to use an immediate switch, proration, or a new Checkout Session.
- Persist enough metadata for the webhook reconciliation.
- Cover the idempotency of the checkout return/webhook.
- Test the family upgrade with an active Stripe subscription.

## Out of scope
- Creating new commercial prices.
- Changing the Asaas flow.
- Implementing without explicit approval.

## Acceptance criteria
- [ ] A main person with an active Stripe subscription can migrate to a family plan without duplicating the remote subscription.
- [ ] The webhook confirms the local family plan and keeps the `stripe_subscription_id` correct.
- [ ] A webhook retry/refresh does not duplicate the order or the membership.
- [ ] A Stripe failure does not cancel the previous local plan.
- [ ] The focused tests pass.

## Evidence planned
- The official Stripe documentation on updating a subscription/subscription items and Checkout Sessions.
- Unit tests with Stripe mocks.
- Local validation with the Stripe CLI when approved.

## Status
Proposed, not implemented.
