# PRD-089: CRUD de Planos com Precificação Dinâmica

## Resumo do que será implementado
Expandir o modelo `SubscriptionPlan` com campos de precificação dinâmica (valor líquido desejado, taxas do gateway e desconto por ciclo), implementar cálculo automático de preço final via `save()`, atualizar o formulário CRUD com preview em tempo real, e criar o JSON seed com os 72 planos iniciais da academia.

## Tipo de demanda
Nova feature + mudança de modelo + seed

## Problema atual
O modelo armazena apenas o `price` final manualmente. Se a taxa da operadora mudar, é necessário recalcular e reeditar cada plano individualmente. Não há rastreabilidade dos componentes do preço.

## Objetivo
- Taxa do gateway (fixa + %) é configurável por plano e reflete no preço automaticamente
- Desconto por ciclo (mensal → trimestral → semestral → anual) é configurável e reflete automaticamente
- Admin pode criar, editar e excluir planos via CRUD já existente
- Seed carrega os 72 planos iniciais (3 categorias × 2 frequências × 3 gateways × 4 ciclos)

---

## Fórmula de cálculo

```
gross_price = (base_net × n_meses × (1 − desconto_ciclo) + taxa_fixa) / (1 − taxa_pct)
```

Onde:
- `base_net` = valor líquido mensal desejado (o que a academia quer receber por mês)
- `n_meses` = 1 (mensal), 3 (trimestral), 6 (semestral), 12 (anual)
- `desconto_ciclo` = desconto concedido por compromisso de prazo maior (ex: 0.0257 = 2,57%)
- `taxa_fixa` = taxa fixa por cobrança do gateway (ex: R$ 1,99 no Asaas PIX)
- `taxa_pct` = taxa percentual do gateway (ex: 0.0599 = 5,99% Stripe)

---

## Campos novos no SubscriptionPlan

| Campo | Tipo | Descrição |
|---|---|---|
| `is_loyalty_plan` | BooleanField | Distingue planos Fidelidade dos Individuais |
| `base_monthly_net_price` | DecimalField null/blank | Valor líquido mensal desejado |
| `gateway_code` | CharField | Identificador do gateway: asaas_pix, asaas_card, stripe_card |
| `gateway_fixed_fee` | DecimalField | Taxa fixa do gateway (R$) |
| `gateway_percentage_fee` | DecimalField(4 decimais) | Taxa % como decimal (0.0429 = 4,29%) |
| `cycle_discount_percentage` | DecimalField(4 decimais) | Desconto do ciclo como decimal (0.0257 = 2,57%) |

Campo existente `price`: recebe `default=0`, calculado automaticamente em `save()` quando `base_monthly_net_price` estiver preenchido.

---

## Planos iniciais (72 registros)

| Categoria | Frequência | Base mensal líquida | Descontos (M/T/S/A) |
|---|---|---|---|
| Individual | 2x/sem | R$ 220,00 | 0% / 2,57% / 5,15% / 7,72% |
| Individual | 5x/sem | R$ 250,00 | 0% / 4,00% / 8,00% / 12,00% |
| Fidelidade | 2x/sem | R$ 203,01 | 0% / 0,50% / 1,00% / 1,48% |
| Fidelidade | 5x/sem | R$ 220,01 | 0% / 2,28% / 4,55% / 6,82% |
| Família | 2x/sem | R$ 203,01 | 0% / 0,50% / 1,00% / 1,48% |
| Família | 5x/sem | R$ 220,01 | 0% / 2,28% / 4,55% / 6,82% |

Gateways: Asaas PIX (ativo), Asaas Cartão (inativo por padrão), Stripe Cartão (ativo).

---

## Arquivos impactados

- `system/models/plan.py` — novos campos + save() + _compute_price()
- `system/forms/plan_forms.py` — novos campos no formulário
- `system/tests/test_plan_models.py` — novos testes de cálculo
- `templates/plans/plan_form.html` — seção de precificação + preview
- `templates/plans/plan_list.html` — mostrar componentes do preço
- `templates/plans/plan_detail.html` — detalhe de precificação
- `static/system/css/portal/plans.css` — estilos do CRUD de planos
- `static/system/js/shared/plan-form.js` — calculadora em tempo real
- `static/initial_data/subscription_plans.json` — 72 planos
- `system/management/commands/seed_system_initial_subscription_plans.py` — seed
- `CLAUDE.md` — documentar nova seed

## Critérios de aceite
- [ ] Ao alterar `gateway_percentage_fee` e salvar, `price` reflete o novo cálculo
- [ ] Ao alterar `cycle_discount_percentage` e salvar, `price` reflete o novo cálculo
- [ ] Planos sem `base_monthly_net_price` mantêm preço manual intacto
- [ ] Preview JS mostra preço calculado em tempo real ao editar o formulário
- [ ] Seed cria 72 planos idempotentemente; segunda execução não duplica

## Plano
- [x] 1. PRD
- [ ] 2. Model (requer ciclo destrutivo)
- [ ] 3. Form
- [ ] 4. CSS + JS
- [ ] 5. Templates
- [ ] 6. JSON seed
- [ ] 7. Seed command
- [ ] 8. Testes
- [ ] 9. CLAUDE.md
