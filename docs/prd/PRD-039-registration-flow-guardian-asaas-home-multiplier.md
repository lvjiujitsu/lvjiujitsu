# PRD-039: Standardize the registration flow — guardian, Asaas, home, plan multiplier

## Summary of the implementation

Fixes across six independent but related fronts of the public registration flow:

1. **Guardian health/martial** — the guardian also goes through the health and sports history steps (like the holder)
2. **Asaas city** — the `city` field included in `create_customer()` to pre-fill the payment
3. **Plan multiplier** — for a guardian profile with N students, the plan is charged N times
4. **Post-payment UX** — on returning from Asaas, show a confirmation screen identical to the checkout one, with a `Continuar` (`Continue`) button; the same pattern for materials
5. **Final summary** — `step-review` shows the guardian → each student with their class and the amount paid
6. **Empty home** — minimal templates for the home routes that already exist

## Demand type

Bug fixes + feature gap

## Impacted files

- `system/forms/registration_forms.py`
- `system/services/registration.py`
- `system/services/registration_checkout.py`
- `system/services/asaas_client.py`
- `system/services/asaas_checkout.py`
- `system/views/auth_views.py`
- `static/system/js/auth/register.js`
- `templates/login/register.html`
- `templates/home/student/dashboard.html` (new)
- `templates/home/admin/dashboard.html` (new)
- `templates/home/instructor/dashboard.html` (new)

## Acceptance criteria

- [ ] The guardian wizard shows step-health and step-martial for the guardian themselves before the students
- [ ] The guardian's health/martial arts data is persisted on the guardian's Person
- [ ] The complete address (including city) is sent to Asaas when creating the customer
- [ ] A guardian with 2 students on a non-family plan generates an order with total = 2 × plan.price
- [ ] On returning from Asaas after paying for the plan, step-checkout shows a `Pagamento confirmado` (`Payment confirmed`) badge + a `Continuar para materiais` (`Continue to materials`) button
- [ ] On returning from Asaas after paying for materials, step-products shows a `Pagamento confirmado` (`Payment confirmed`) badge + a `Continuar para o resumo` (`Continue to the summary`) button
- [ ] step-review shows the guardian (when applicable) + each student with their class and the amount paid + a `Finalizar` (`Finish`) button
- [ ] After finishing, person.is_active=True, the login is performed, and it redirects to the home (not a 500 error)
- [ ] The home loads with no error for the student, admin, and instructor profiles

## Plan

- [x] 1. PRD created
- [ ] 2. Form: add the guardian health/martial fields
- [ ] 3. The registration service: pass the health/martial fields to the guardian
- [ ] 4. The registration_checkout service: the trainee multiplier
- [ ] 5. Asaas client + checkout: city
- [ ] 6. The auth view: enrich pending_person_summary + review_data to include the students
- [ ] 7. register.js: guardian health/martial in the sequence + correct saving
- [ ] 8. register.js: confirmed post-payment UX + an improved review
- [ ] 9. Home templates (minimal)
- [ ] 10. manage.py check + test
- [ ] 11. collectstatic

## Implemented

(filled in after execution)

## Deviations from plan

(filled in after execution)

## Pending

(filled in after execution)
