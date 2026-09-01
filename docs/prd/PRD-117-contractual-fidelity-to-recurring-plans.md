# PRD-117: Contractual loyalty for recurring plans

## Summary
Create an explicit contractual field and rule for the commitment/loyalty period of recurring plans, separating the change/cancellation block date from the monthly fee's current monthly period.

## Demand type
A documentation follow-up for a financial rule outside PRD-116's scope.

## Current problem
- PRD-116 blocks the change/cancellation of a recurring Stripe plan using `Membership.current_period_end` as the operational date.
- The current model has no dedicated field for the commitment/loyalty end date, the acceptance of the terms, or a contractual term different from the monthly period.

## Goal
- Define where to store the commitment/loyalty end date.
- Record the acceptance of the terms applied to the recurring plan.
- Separate the monthly renewal, the paid period, and the contractual loyalty period.
- Update the home, the change/cancellation endpoints, and the financial management to use the contractual date.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Status
Pending. Do not implement without explicit approval.
