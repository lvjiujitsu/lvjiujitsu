# PRD-062: Auditoria do padrão sinal → serviço idempotente

## Summary

Auditar no LV a superfície de sinais Django e a criação de registros derivados (backorders, repasses/`TeacherPayout`, financeiro de pedido) contra modos de falha conhecidos — dependência exclusiva de sinal, timing de M2M/`bulk_create` e exceção silenciada — e codificar o padrão "serviço idempotente + chamada explícita" (belt-and-suspenders) como regra de projeto. A constatação inicial é que o LV **já segue** o padrão correto nos serviços; este PRD confirma isso com evidência e endurece o único ponto frágil identificado.

## Demand type

Auditoria arquitetural preventiva + endurecimento pontual + codificação de regra. Pode gerar correção mínima de baixo risco no sinal de backorders.

## Current problem

- Em caso conhecido, lógica crítica dependia só de sinais e falhava por timing de M2M e `bulk_create`, que não disparam `post_save`. A correção foi extrair serviço idempotente e chamá-lo explicitamente na view.
- No LV, a auditoria preliminar indica situação saudável:
  - único `@receiver` do repositório está em `system/signals.py` (backorders) e já delega a `system/services/product_backorders.py`;
  - serviços de repasse (`asaas_payroll.py`) e financeiro (`financial_transactions.py`) criam registros dentro de `@transaction.atomic`, sem depender de sinal.
- Ponto frágil identificado: em `system/signals.py`, `promote_backorders_on_restock` envolve as chamadas de serviço em `try/except Exception` que apenas registra log e segue. Uma falha de promoção/cancelamento de pré-pedido fica invisível fora do log, sem nenhuma rede de reprocessamento ou chamada explícita equivalente no fluxo que altera estoque.
- Falta uma regra de projeto que proíba lógica derivada dependente apenas de sinal e exija serviço idempotente + chamada explícita, para evitar regressão futura ao padrão do PRD-105.

## Goal

1. Mapear toda a superfície de sinais e criação de registros derivados do LV e classificar cada uma quanto ao risco PRD-105 (timing, `bulk_create`, exceção silenciada, dependência exclusiva de sinal).
2. Confirmar com evidência que repasses e financeiro de pedido não dependem de sinal.
3. Endurecer o sinal de backorders: garantir idempotência do serviço e avaliar uma chamada explícita do serviço no fluxo de reposição de estoque, mantendo o sinal como rede secundária.
4. Cobrir a promoção/cancelamento de backorders com teste de idempotência (chamar duas vezes não duplica `RegistrationOrder`/`ProductBackorder`).
5. Codificar a regra "serviço idempotente + chamada explícita" na skill `lv-cleanup-audit` e/ou em `AGENTS.md §9`.

## Context Ledger

### Files read in full

- `system/signals.py`
- `system/apps.py`
- `system/services/product_backorders.py`
- `system/services/asaas_payroll.py`
- `system/services/financial_transactions.py`
- `system/services/payroll_rules.py`

### Adjacent files consulted

- `system/models/product.py` (ProductVariant, ProductBackorder, RegistrationOrder)
- `system/services/registration_checkout.py` (fluxo de pedido)
- inventário de `system/services/`

### Internet / official documentation

- [Django 5.2 — signals](https://docs.djangoproject.com/en/5.2/topics/signals/)
- [Django 5.2 — m2m_changed](https://docs.djangoproject.com/en/5.2/ref/signals/#m2m-changed)
- [Django 5.2 — bulk_create caveats](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#bulk-create)
- [Django 5.2 — database transactions](https://docs.djangoproject.com/en/5.2/topics/db/transactions/)

### Context7 / MCPs / tools verified

- Context7 a consultar para Django signals/transactions na execução.
- PowerShell, Git e `rg` disponíveis.
- Browser interno disponível para evidência visual do fluxo de backorders, se a correção tocar UI.

### Limitations found

- A criação de `TeacherPayout` ocorre em comando/serviço agendado; validar exige autorização de execução de comando.
- Dados legados de backorders, se existirem, exigem inspeção ORM read-only antes de qualquer mutação.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: auditar sinais/serviços do LV contra a lição PRD-105 e endurecer o único ponto frágil, sem inventar bug inexistente.
- User approval: solicitação explícita de PRDs completos para implementação sequencial.
- Date: 2026-06-28.

## Execution prompt

### Persona

Engenheiro Django responsável por sinais, serviços transacionais e integridade de registros derivados.

### Action

Auditar a superfície de sinais/serviços, escrever teste de idempotência do fluxo de backorders, endurecer o sinal e codificar a regra de projeto.

### Context

LV é monólito Django 5.2 com domínio em `system/`. Único `@receiver` em `system/signals.py`. Repasses e financeiro já em serviços transacionais.

### Constraints

- Não criar migrations.
- Não executar testes sem autorização.
- Não mutar dados de produção/HG.
- Toda escrita derivada deve permanecer idempotente.
- Manter o sinal como rede secundária; nunca remover proteção sem substituí-la.

### Acceptance criteria

- [ ] Existe um mapa classificando cada sinal e cada criação de registro derivado quanto ao risco PRD-105.
- [ ] Há evidência de que `TeacherPayout` e financeiro de pedido não dependem de sinal.
- [ ] `restock_variant`/`cancel_all_active_for_variant` comprovadamente idempotentes por teste.
- [ ] Chamar o serviço de promoção de backorders duas vezes não duplica `RegistrationOrder` nem reativa pré-pedidos cancelados.
- [ ] O `except Exception` silencioso do sinal é reavaliado: ou passa a ter rede de reprocessamento/visibilidade, ou é substituído por chamada explícita no fluxo de estoque com o sinal como fallback.
- [ ] Regra "serviço idempotente + chamada explícita" registrada em `lv-cleanup-audit` e/ou `AGENTS.md §9`.

### Expected evidence

- Mapa de sinais/serviços com classificação de risco.
- Saída do teste de idempotência (após autorização).
- Diff do endurecimento do sinal e da regra codificada.

### Output format

Resumo curto, mapa de risco, evidências, limitações e status.

## Scope

- `system/signals.py`
- `system/services/product_backorders.py`
- `system/tests/` (novo teste de idempotência de backorders)
- `system/views/` ou serviço que aciona reposição de estoque (chamada explícita, se aplicável)
- `AGENTS.md` (§9) e/ou skill `lv-cleanup-audit`
- este PRD.

## Out of scope

- Redesign do módulo financeiro ou de repasses.
- Alteração de models ou migrations.
- Fluxo de pagamento externo Asaas/Stripe.
- Correção de dados legados sem autorização separada.

## Impacted files

- `system/signals.py`
- `system/services/product_backorders.py`
- `system/tests/test_product_backorders_signal.py` (novo)
- regra de governança em `AGENTS.md` e/ou `lv-cleanup-audit`
- este PRD.

## Risks and edge cases

- `ProductVariant.save()` não envolve M2M; o risco de timing do PRD-105 não se aplica diretamente, mas deve ser confirmado e documentado, não presumido.
- Adicionar chamada explícita pode duplicar promoção se o serviço não for idempotente — por isso o teste de idempotência é pré-requisito da chamada explícita.
- Repasses agendados podem criar `TeacherPayout` em janela concorrente; confirmar uso de `unique`/`get_or_create` como rede.
- Silenciar exceção mascara falha (regra de clean code do projeto): a reavaliação não pode introduzir `except: pass`.

## Rules and constraints

- Menor mudança correta e causa raiz.
- Serviço é a fonte de verdade; sinal é rede secundária.
- Sem exceção mascarada.
- `transaction.atomic` em múltiplas escritas.

## Plan

- [ ] Context and research (mapa de sinais/serviços)
- [ ] Escrever teste de idempotência (test-first)
- [ ] Confirmar independência de sinal em repasses/financeiro
- [ ] Endurecer sinal de backorders / chamada explícita
- [ ] Codificar regra de projeto
- [ ] Solicitar autorização e executar testes
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

- `test_product_backorders_signal.py`: idempotência de `restock_variant` e `cancel_all_active_for_variant`; não duplicação de `RegistrationOrder`; não reativação de pré-pedido cancelado.

### Execution authorization

- Status: não solicitada. Testes escritos antes do código, executados somente após autorização.

### Execution evidence

A coletar após autorização. Não declarar Red/Green sem execução.

## Visual validation

A definir: se a chamada explícita tocar a tela de estoque/loja, validar no browser interno (desktop/mobile, console, screenshot). Caso contrário, não aplicável.

## ORM validation

- Inspeção read-only de backorders e payouts antes de qualquer mutação.
- Mutação de dados legados exige autorização separada.

## Quality validation

- `manage.py check` (após autorização).
- Mapa de risco revisado.
- `git diff --check`.

## Evidence

Planejada — não executada. A coletar na implementação.

## Implemented

Pendente.

## Cleanup findings

Pendente.

## Follow-up PRDs

- Possível PRD de correção de dados legados de backorders/payouts, se a inspeção ORM revelar inconsistência.

## Deviations from plan

Nenhum até o momento.

## Pending

- Autorização para executar testes e comandos de repasse.

## Final status

**Não concluída** — PRD especificada; implementação pendente de execução sequencial.
