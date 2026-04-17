# PRD-013: Saque parcial antecipado solicitado por professor

## Resumo
Permitir que professores com `TeacherPayrollConfig` ativa solicitem um saque parcial antecipado do salário no portal. Admin revisa na fila já existente (PRD-012) e aprova/recusa/dispara.

## Problema atual
Hoje o professor só recebe no dia fixo da folha (dia configurado em `payment_day`). Antecipações são combinadas por fora do sistema, sem trilha de auditoria nem controle de limite.

## Objetivo
- Professor acessa `/me/financeiro/` e vê: salário base, saldo disponível do mês, histórico de pagamentos.
- Pode solicitar saque informando valor (≤ saldo disponível) e justificativa.
- A solicitação vira `TeacherPayout(kind=WITHDRAWAL, status=PENDING)` e entra na fila admin.
- Aprovação e disparo PIX reutilizam fluxo do PRD-012 (`approve_payout`, `dispatch_payout`).

## Saldo disponível
```
saldo_disponivel = monthly_salary - sum(
    TeacherPayout.amount
    WHERE person = self
      AND reference_month = primeiro_dia_do_mes_atual
      AND status in (PENDING, APPROVED, SENT, PAID)
)
```
Contam todos os `PayoutKind` (folha + saques anteriores já solicitados no mês).

## Escopo
**Incluso:**
- Service: `compute_available_balance(person, reference_month)`, `request_withdrawal(person, amount, notes)`
- Form: `WithdrawalRequestForm` (valor, notas)
- Views: `TeacherFinancialView` (GET), `TeacherWithdrawalRequestView` (POST)
- URLs: `me/financeiro/`, `me/financeiro/sacar/`
- Templates: `home/instructor/financial.html`
- Atalho no dashboard do professor
- Testes unitários do service + view

**Fora do escopo:**
- Notificação por e-mail/WhatsApp ao admin.
- Limite configurável (ex: "máximo 70% do salário") — fica `monthly_salary` total.
- Relatório mensal consolidado.

## Regras
- Apenas `person_type.code == "instructor"` pode solicitar.
- Professor precisa de `TeacherBankAccount` ativa e `TeacherPayrollConfig` ativa.
- `amount > 0` e `amount <= saldo_disponivel`.
- `reference_month` é sempre o primeiro dia do mês atual.
- Se já há folha PAGA do mês, saldo é zero.

## Arquivos impactados
- `system/services/asaas_payroll.py`
- `system/forms/__init__.py` ou novo arquivo de form
- `system/views/asaas_views.py` (ou novo `teacher_financial_views.py`)
- `system/urls.py`, `system/views/__init__.py`
- `templates/home/instructor/financial.html` (novo)
- `templates/home/instructor/dashboard.html` (atalho)
- `system/tests/test_asaas.py` (novos casos)

## Critérios de aceite
- [ ] `GET /me/financeiro/` retorna 200 para instructor, 403 para outros.
- [ ] Mostra saldo disponível correto.
- [ ] `POST` com valor inválido retorna erro de formulário.
- [ ] `POST` com valor válido cria `TeacherPayout` WITHDRAWAL PENDING.
- [ ] Aparece na `PayoutQueueView` do admin.
- [ ] Fluxo approve → dispatch idêntico ao folha mensal.
- [ ] Testes passando (existentes + novos).

## Plano
1. PRD.
2. Service (saldo + request).
3. Form + views + urls.
4. Templates.
5. Testes.
6. Validação final.

## Implementado
(preencher ao final)
