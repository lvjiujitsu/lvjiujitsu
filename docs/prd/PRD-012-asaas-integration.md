# PRD-012: Integração Asaas (PIX in + folha de professores)

## Resumo
Adicionar integração com Asaas (sandbox) paralela ao Stripe. Objetivos:
1. Oferecer PIX como método de recebimento no checkout de alunos (complementa cartão via Stripe).
2. Pagar professores automaticamente via PIX de saída na data de pagamento configurada.
3. Permitir que professores solicitem saque parcial antecipado, sujeito a aprovação admin (escopo do PRD-013).

## Problema atual
- Recebimento só aceita cartão (Stripe checkout). Muito aluno prefere PIX.
- Pagamento de professores é manual (fora do sistema). Sem trilha de auditoria nem agendamento.

## Objetivo
- `POST /payments/pix/create/<order_id>/` gera cobrança PIX no Asaas e exibe QR Code + copia-e-cola.
- Webhook Asaas marca `RegistrationOrder.payment_status = PAID` quando o PIX é recebido.
- Folha mensal: comando `schedule_monthly_payouts` cria `TeacherPayout` pendente no dia de pagamento. Admin aprova → service dispara `Transfer` PIX via Asaas → webhook confirma `PAID`/`FAILED`.

## Contexto consultado
- Asaas API v3 (sandbox): `/customers`, `/payments`, `/payments/{id}/pixQrCode`, `/transfers`, `/finance/balance`.
- Autenticação por header `access_token`.
- Webhooks validados por token compartilhado (header `asaas-access-token`), não HMAC.

## Dependências adicionadas
- `requests>=2.31` (já presente via transitividade; confirmar em `requirements.txt`).

## Escopo
**Incluso (PRD-012):**
- Modelos: `TeacherBankAccount`, `TeacherPayrollConfig`, `TeacherPayout`, `AsaasWebhookEvent`.
- Campos novos em `Person`: `asaas_customer_id`.
- Campos novos em `RegistrationOrder`: `asaas_payment_id`, `asaas_pix_qrcode`, `asaas_pix_copy_paste`.
- Service `asaas_client` (HTTP wrapper), `asaas_checkout` (PIX in), `asaas_payroll` (PIX out), `asaas_webhooks`.
- View `CreatePixChargeView` para aluno; `AsaasWebhookView` para callback; views admin de folha.
- Command `schedule_monthly_payouts`.
- Templates: `pix_checkout.html`, `payroll_list.html`, `payout_approval.html`.
- Testes unitários com `requests` mockado.

**Fora do escopo (vai para PRD-013):**
- Saque parcial solicitado pelo professor.
- Cálculo de saldo disponível por professor a partir de presença.
- UI do portal do professor.

## Arquivos impactados
- `lvjiujitsu/settings.py` (novas vars)
- `.env.example`
- `system/models/asaas.py` (novo)
- `system/models/__init__.py`, `person.py`, `registration_order.py`
- `system/services/asaas_*.py` (4 arquivos novos)
- `system/views/asaas_views.py` (novo), `payment_views.py`
- `system/views/__init__.py`, `system/urls.py`
- `system/management/commands/schedule_monthly_payouts.py` (novo)
- `templates/billing/pix_checkout.html`, `payroll_list.html`, `payout_approval.html`
- `system/tests/test_asaas_*.py` (4 arquivos novos)

## Riscos
- **Saldo insuficiente** ao disparar transfer → tratar exceção, marcar `FAILED`, alertar admin.
- **Webhook não chega** → command de reconciliação periódica (fora do escopo; tratado manualmente via "Marcar como pago").
- **Dupla cobrança** se usuário retentar PIX → idempotência por `RegistrationOrder` (reuso do `asaas_payment_id` se ainda pendente).

## Regras e restrições
- SDD: PRD precede implementação ✅.
- TDD: testes unitários por camada, `requests` mockado.
- MTV: models → forms → services → views → urls → templates → static → tests.
- Services encapsulam lógica; views finas.
- Sem credenciais hardcoded; tudo via `.env`.

## Critérios de aceite
- [ ] `manage.py check` sem issues.
- [ ] Suite completa passa (testes existentes + novos).
- [ ] `collectstatic` sem erros.
- [ ] `POST /payments/pix/create/<order_id>/` retorna template com QR Code quando Asaas mockado.
- [ ] Webhook `PAYMENT_RECEIVED` marca order como `PAID`.
- [ ] `schedule_monthly_payouts` cria `TeacherPayout.PENDING` no dia correto.
- [ ] `dispatch_payout` chama `Transfer.create` e grava `asaas_transfer_id`.
- [ ] Webhook `TRANSFER_DONE` marca payout como `PAID`.
- [ ] Admin pode aprovar/recusar payout via fila.

## Plano
1. PRD (este arquivo).
2. Settings + `.env.example`.
3. Models + migração.
4. Services (client, checkout, payroll, webhooks).
5. Views + URLs + templates.
6. Management command.
7. Testes.
8. Check + testes + collectstatic.

## Comandos de validação
```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test system
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

## Implementado
(preencher ao final)

## Desvios do plano
(preencher se houver)
