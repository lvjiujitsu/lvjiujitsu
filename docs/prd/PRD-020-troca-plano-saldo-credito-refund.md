# PRD-020: Troca de plano com saldo→tempo, crédito futuro e refund automático

## Resumo do que será implementado
Reescrever o motor de troca de plano (`system/services/plan_change.py`) e a UI da troca para um modelo onde **o dinheiro pago se preserva ao máximo** dentro da assinatura:

- O sistema calcula o **saldo financeiro** (valor pago − consumo proporcional aos dias usados).
- Se o saldo cobrir um ou mais ciclos cheios do plano novo, a vigência do plano novo é estendida sem novo débito; eventual sobra (não fecha um ciclo inteiro) vira `MembershipCredit` aplicado como desconto na próxima renovação.
- Se o saldo não cobrir o plano novo (upgrade), cobra a diferença (`new_plan.price − available_credit`) e dá vigência cheia.
- Quando há sobra, o cliente pode optar por **receber a sobra de volta** automaticamente (refund disparado direto no Stripe ou Asaas, sem aprovação administrativa).

A UI da troca passa a exibir: plano atual, valor pago, dias usados/restantes, saldo disponível, nova vigência (data calculada), valor adicional (se upgrade) e — quando aplicável — sobra com toggle "manter como crédito" / "receber de volta".

## Tipo de demanda
Refatoração arquitetural + integração externa (Stripe Refund API + Asaas Refund API).

## Problema atual
O motor de troca atual (`calculate_plan_change`) calcula proração dia-a-dia para o **mesmo período restante** do ciclo do plano atual e, se há diferença a pagar, cobra; se não, devolve "Grátis". Isso não preserva o dinheiro já pago. Cenários problemáticos:

- Cliente no plano anual (R$ 3.204) com 4 meses usados (R$ 1.068 consumidos, R$ 2.136 de saldo). Ao trocar para mensal R$ 267, o sistema atual exibe "Grátis" para os 8 meses restantes, mas não dá direito ao cliente de continuar usando o saldo se cancelar o anual.
- Cliente perdia "valor implícito" do que pagou, contrariando expectativa de que o dinheiro debitado seja respeitado.

## Objetivo
1. Calcular saldo do plano atual (`amount_paid − amount_consumed`) e converter em tempo de vigência no plano novo (ciclos inteiros).
2. Sobra (saldo restante após arredondar para baixo no nº de ciclos) → `MembershipCredit` consumível na próxima renovação.
3. Upgrade (saldo < preço cheio do novo plano) → cobra diferença, vigência cheia.
4. Botão opcional: "Receber sobra de volta" → dispara refund automático no provider correto (Stripe ou Asaas), sem aprovação administrativa.
5. UI mostra o cálculo completo no resumo.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`, `CLAUDE.md`
- `system/models/membership.py` — `Membership`, `MembershipInvoice`, `MembershipStatus`
- `system/models/registration_order.py` — `RegistrationOrder`, `PaymentStatus`, `PaymentProvider`, `OrderKind`
- `system/services/membership.py` — `add_billing_cycle`, `get_billing_cycle_day_count`, `record_refund_from_charge`, `_ensure_active_membership_for_person`
- `system/services/plan_change.py` (a ser reescrito)
- `system/services/stripe_admin_actions.py` — `refund_order` reutilizável
- `system/services/asaas_client.py` — falta endpoint `refund_payment` (será adicionado)
- `system/services/asaas_webhooks.py` — fluxo `apply_plan_change` em PIX
- `system/services/stripe_webhooks.py` (linhas 162-173) — fluxo `apply_plan_change` em Stripe
- `system/views/plan_change_views.py` (refatorado no PRD-019)
- `templates/billing/plan_change_select.html`, `static/system/js/billing/plan-change-selector.js`, `static/system/css/shared/plan-selector.css`

### Arquivos adjacentes consultados
- `system/services/financial_transactions.py` (resolve_payment_provider_for_plan)
- `system/services/payroll_rules.py` (`append_order_refund_record`)
- `system/tests/test_views.py` (PlanChangeSelectViewTest)
- `docs/prd/PRD-019-troca-plano-padrao-plan-selector.md`

### Internet / documentação oficial
- Stripe Refund API: `stripe.Refund.create(payment_intent=..., amount=...)` — já em uso em `stripe_admin_actions`.
- Asaas API Refund: `POST /payments/{id}/refund` (body `{value}`); webhook envia `PAYMENT_REFUNDED`/`PAYMENT_PARTIALLY_REFUNDED` (já tratados em `asaas_webhooks`).

### MCPs / ferramentas verificadas
- shell PowerShell — ok
- Preview MCP — ok (usado no PRD-019)
- Reset destrutivo autorizado pelo usuário (clear_migrations.py + makemigrations + migrate)

### Limitações encontradas
- Webhook Stripe `charge.refunded` já é tratado e atualiza `Order.payment_status=REFUNDED` + `MembershipInvoice.amount_refunded`. O refund disparado por nós deve ser **idempotente com webhook**: salvar imediatamente no `Order.notes` via `append_order_refund_record(cumulative=False)` e deixar webhook eventualmente reforçar.
- Asaas refund pode ser parcial; é seguro chamar várias vezes? Sim, mas vamos guardar `MembershipMovement`-like log no `notes` via mesmo helper `append_order_refund_record`.

## Prompt de execução
### Persona
Agente de desenvolvimento Django + integrações Stripe/Asaas seguindo SDD + TDD.

### Ação
Reescrever `system/services/plan_change.py` com novo motor (saldo→tempo, sobra→credit, upgrade→cobrança), implementar `request_plan_change_refund` disparando providers, atualizar UI e testes.

### Contexto
Ver acima. O usuário autorizou explicitamente reset destrutivo + criação automática de migration consolidada (`0001_initial`).

### Restrições
- Sem hardcode de regras (todos os valores monetários vêm do plano e da `RegistrationOrder` paga).
- Sem `except: pass` ou mascaramento de erro.
- Manter compatibilidade da assinatura `apply_plan_change(order, membership, new_plan)` usada em webhooks.
- Idempotência: refund disparado por nós + eventual webhook subsequente não devem creditar duas vezes.
- Sem `MembershipCredit` duplicado para a mesma troca.

### Critérios de aceite
- [ ] Cliente no anual com 4 meses usados, troca para mensal: vigência estende em N ciclos cheios (`floor(saldo / preço_mensal)`), sobra entra como `MembershipCredit`, sem cobrança.
- [ ] Cliente no mensal troca para anual: cobra `anual.price − saldo`, vigência cheia (1 ano).
- [ ] Quando há sobra, UI exibe valor da sobra + botão "receber esse valor de volta"; ao clicar, refund é disparado **automaticamente** no provider da última ordem paga (Stripe ou Asaas) e o histórico do pedido é atualizado.
- [ ] Se a última ordem foi `MANUAL`, o "receber de volta" registra a pendência (fallback) e exibe aviso.
- [ ] Nenhum endpoint novo precisa de aprovação administrativa.
- [ ] `manage.py test --verbosity 2` passa sem falhas (suíte completa).
- [ ] Reset destrutivo executado sem erro; migrations consolidadas em `0001_initial`.
- [ ] Validação visual em desktop e mobile com console limpo.

### Evidências esperadas
- Output de testes
- Output de `clear_migrations.py`, `makemigrations`, `migrate`
- Screenshots desktop+mobile
- Console do browser limpo

### Formato de saída
Modelo + serviço + integração + view + template + JS + testes + reset destrutivo.

## Escopo
- `system/models/membership.py`: novo `MembershipCredit`.
- `system/services/plan_change.py`: reescrito.
- `system/services/asaas_client.py`: novo `refund_payment(payment_id, value=None)`.
- `system/services/asaas_refunds.py` **(novo)** ou inline em `plan_change.py`: orquestração do refund Asaas (idempotente, registra no `Order.notes`).
- `system/views/plan_change_views.py`: GET com novo payload (campos novos), POST com `action`/`leftover_action` (`keep_credit` default | `refund`).
- `templates/billing/plan_change_select.html`: novo painel "seu plano atual" + ajustes no resumo.
- `static/system/js/billing/plan-change-selector.js`: renderiza campos novos + botão de refund + toggle de leftover.
- `static/system/css/shared/plan-selector.css` ou `billing.css`: estilos para novos blocos.
- `system/tests/test_services.py` ou `test_plan_change.py` (novo arquivo): testes do motor (cálculo, ciclos, sobra, upgrade, refund mockado).
- `system/tests/test_views.py`: cobrir POST com novos modos.

## Fora do escopo
- Cancelamento integral com janela legal de 7 dias por arrependimento → PRD-021 separado.
- Notificações ao cliente por e-mail/SMS após troca/refund.
- Tela administrativa para ver/forçar refunds (admin atual segue usando `stripe_admin_actions`).
- Refund parcial em outras situações fora de troca de plano.

## Arquivos impactados
| Arquivo | Tipo |
|---|---|
| `system/models/membership.py` | + `MembershipCredit` |
| `system/services/plan_change.py` | reescrita completa |
| `system/services/asaas_client.py` | + função `refund_payment` |
| `system/views/plan_change_views.py` | GET/POST novos campos |
| `templates/billing/plan_change_select.html` | painel + toggle |
| `static/system/js/billing/plan-change-selector.js` | renderização nova |
| `static/system/css/shared/plan-selector.css` | classes novas |
| `system/tests/test_services.py` | novos testes do motor |
| `system/tests/test_views.py` | novos testes de view |
| `system/migrations/0001_initial.py` | regenerada via reset destrutivo |
| `system/views/__init__.py` | (provavelmente sem mudança) |

## Riscos e edge cases
- **Não há ordem paga vinculável**: cliente exempted ou seed sem `RegistrationOrder`. Fallback: usar `membership.plan.price` como `amount_paid`.
- **Múltiplas ordens pagas** para mesmo plano (renovações): pegar a mais recente paga não estornada.
- **Saldo igual ao preço de N ciclos exatos** (sem sobra): `leftover_credit = 0`, sem botão de refund.
- **Refund Stripe falha** (charge muito antiga, etc.): mostrar erro e manter o leftover como `MembershipCredit` automaticamente.
- **Refund Asaas falha**: idem.
- **Cliente clica refund durante upgrade** (não há sobra): UI não deve oferecer o botão.
- **Reset destrutivo**: com banco local SQLite descartável (`db.sqlite3`), aplicar como definido em `CLAUDE.md`.

## Regras e restrições
- SDD + TDD
- Reset destrutivo autorizado
- Sem hardcode de valores monetários
- Idempotência em integrações externas

## Plano
- [ ] 1. Modelo `MembershipCredit`
- [ ] 2. Adicionar `refund_payment` em `asaas_client.py`
- [ ] 3. Reescrever `plan_change.py` (motor + apply + refund)
- [ ] 4. Atualizar view (GET/POST com `leftover_action`)
- [ ] 5. Atualizar template + JS + CSS
- [ ] 6. Testes (motor + view + refund mockado)
- [ ] 7. Reset destrutivo + migrate
- [ ] 8. Validação visual desktop + mobile
- [ ] 9. Atualização documental

## Validação visual
### Desktop
- Painel "seu plano atual" com valor pago, dias usados/restantes, saldo
- Resumo do plano-alvo com nova vigência, sobra (se houver), botão de refund
- Botão "Confirmar troca" / "Confirmar e pagar" depende do cenário

### Mobile
- Layout adaptado mantendo legibilidade

### Console
- Limpo nas duas telas

### Terminal
- Sem stack trace

## Validação ORM
### Banco
- `MembershipCredit` criado, migrations 0001_initial regenerada

### Shell checks
- `MembershipCredit.objects.filter(applied_at__isnull=True).count()` em cenários de troca com sobra
- `RegistrationOrder.objects.filter(refunded_at__isnull=False)` após disparo do refund

### Integridade do fluxo
- Webhook subsequente não duplica créditos nem refunds

## Validação de qualidade
- Sem hardcode
- Sem `except: pass`
- Funções pequenas, comentários só onde necessário
- Idempotência protegida

## Evidências
*(a preencher após execução)*

## Implementado
*(a preencher após execução)*

## Desvios do plano
*(a preencher após execução)*

## Pendências
*(a preencher após execução)*
