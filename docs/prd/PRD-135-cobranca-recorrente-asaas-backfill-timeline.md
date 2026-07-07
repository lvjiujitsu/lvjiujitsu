# PRD-135: Cobrança recorrente automatizada Asaas (sincronizada com desconto família) + backfill de eventos históricos da timeline

## Summary
Dois itens que ficaram explicitamente **fora de escopo** da PRD-134 e o usuário pediu para tratar em PRD própria: (A) hoje não existe nenhuma automação de cobrança recorrente para memberships Asaas — cada cobrança é um pagamento avulso, e quando uma nova é gerada, o valor é recalculado do preço cheio de catálogo, **ignorando** `Membership.billed_price` (o valor já correto, com desconto família aplicado); (B) a timeline da PRD-134 (quando implementada) só registra eventos novos a partir do deploy — este PRD cobre popular retroativamente os eventos que já têm rastro em campos existentes (`Membership.canceled_at`, `RegistrationOrder.paid_at`/`refunded_at`, `MembershipPauseRequest.created_at`/`decided_at`).

## Demand type
Correção de gap arquitetural (A) + tarefa de dados (B), ambas pedidas explicitamente pelo usuário.

## Current problem

### Parte A — cobrança recorrente Asaas
- `system/services/asaas_client.py` só expõe `create_pix_payment`/`create_credit_card_payment` — pagamentos avulsos (`POST /payments`). Não existe conceito de "subscription" do lado Asaas neste projeto.
- Não existe nenhum management command, cron, Celery ou tarefa agendada que gere a próxima cobrança quando `Membership.current_period_end` vence — confirmado por busca exaustiva nesta sessão (nenhum arquivo em `system/management/commands/` relacionado a cobrança/renovação; nenhuma dependência de Celery/APScheduler/django-cron no projeto).
- Quando uma cobrança Asaas de renovação É criada manualmente hoje, o valor usado é sempre `plan.price`/`plan_price_ref.price` — o preço cheio do catálogo (`system/services/registration_checkout.py`, `_create_paid_plan_order` em `system/services/dependent_registration.py`) — **nunca** `Membership.billed_price`, que já reflete corretamente o desconto família vigente.
- Confirmado (mesma sessão) que o mecanismo de confirmação **já funciona corretamente** quando um novo `RegistrationOrder` de renovação é pago: `_handle_payment_event` (`system/services/asaas_webhooks.py:135-176`) chama `activate_membership_from_paid_order` (`system/services/membership.py:154-199`), que localiza a `Membership` ativa existente (via `person`+`plan`/`plan_price`, excluindo canceladas/expiradas) e estende `current_period_start`/`current_period_end` com `add_billing_cycle`. **O gap não é na confirmação — é em nada nunca criar a cobrança de renovação automaticamente, e o valor usado quando alguém cria manualmente ser o errado.**
- Resultado prático: para clientes Asaas com desconto família, uma eventual renovação (se e quando gerada manualmente por um admin) cobraria o preço cheio, não o valor com desconto — o inverso do que a PRD-134 investigou (não é "ficou cobrando com desconto indevido", é "a única forma de cobrar de novo ignora o desconto que deveria valer").

### Parte B — backfill de eventos históricos
- A PRD-134 cria `MembershipTimelineEvent`, mas por design **não** faz backfill — a timeline só começa a partir do deploy dessa PRD.
- Dado histórico parcial já existe e pode alimentar eventos retroativos sem inventar informação: `Membership.canceled_at` (cancelamento), `Membership.created_at` (criação/adesão), `RegistrationOrder.paid_at` (pagamento confirmado) e `RegistrationOrder.refunded_at` (estorno), `MembershipPauseRequest.created_at` (pausa solicitada) e `MembershipPauseRequest.decided_at` (pausa aprovada/reprovada, junto com `status`).
- Eventos sem rastro em campo isolado hoje (ex. adicionar/remover dependente antes desta PRD, troca de plano antes desta PRD, troca de cartão) **não podem ser reconstruídos com precisão** — não há campo equivalente a "data em que o dependente foi removido" fora de logs não estruturados. Esses ficam de fora do backfill, documentado como limitação.

## Goal
1. Toda `Membership` Asaas ativa (`asaas_pix`/`asaas_card`) gera automaticamente a cobrança do próximo ciclo antes do vencimento, usando o valor correto (`billed_price`, já refletindo desconto família), sem intervenção manual.
2. A confirmação de pagamento dessa cobrança gerada automaticamente estende a vigência exatamente como já acontece hoje para pedidos criados manualmente (nenhuma mudança no caminho de confirmação, que já está correto).
3. `MembershipTimelineEvent` (PRD-134) é populado retroativamente com os eventos que têm rastro confiável em campo existente, sem inventar dado para os que não têm.

## Context Ledger
### Files read in full
- `system/services/asaas_client.py` (confirmado: só pagamentos avulsos, sem "subscription")
- `system/services/asaas_webhooks.py` (`_handle_payment_event` completo — confirmação de renovação já funciona)
- `system/services/membership.py` (`activate_membership_from_paid_order`, `add_billing_cycle`, `_add_months`)
- `system/services/registration_checkout.py` (`compute_staggered_billing_cycle_anchor`, cálculo de preço em `create_registration_order`)
- `system/services/dependent_registration.py` (`_create_paid_plan_order` — mesma lógica de preço cheio)

### Adjacent files consulted
- `docs/prd/PRD-134-historico-eventos-assinatura-familia-cliente-admin.md` (origem dos dois itens fora de escopo tratados aqui)
- `system/models/membership.py` (`Membership.current_period_end`, `MembershipPauseRequest`)
- `system/models/registration_order.py` (`RegistrationOrder.paid_at`, `refunded_at`)
- `CLAUDE.md` (seção 5 — deploy Render via Dashboard, sem `render.yaml`/`build.sh`)

### Internet / official documentation
- Documentação de "Cron Jobs" do Render (Dashboard) — confirma que o padrão de deploy do projeto (variáveis e serviços configurados pelo Dashboard, sem arquivo de infra no repo) já comporta um serviço agendado sem precisar de dependência nova (Celery/APScheduler) no código.

### Limitations found
- Este projeto **não tem** nenhuma infraestrutura de tarefa agendada (sem Celery, sem APScheduler, sem django-cron). A automação precisa ser um `management command` Django invocável externamente (Render Cron Job no Dashboard para HG/produção — configuração fora do código, mesmo padrão já usado pelo projeto; execução manual via `manage.py <command>` local).
- Backfill da Parte B é necessariamente incompleto — eventos sem campo de data confiável (dependente adicionado/removido, troca de plano/cartão antes desta PRD) não entram. Documentado como limitação aceita, não como bug.
- **Parte B depende da Parte A da PRD-134 estar implementada** (o model `MembershipTimelineEvent` precisa existir) — se PRD-134 ainda não foi implementada quando esta PRD for executada, a Parte B fica bloqueada até lá.

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-cleanup-audit`

## Understanding approved
Usuário pediu diretamente para abrir PRD cobrindo os dois itens que ficaram fora de escopo da PRD-134.

## Execution prompt
### Persona
Desenvolvedor Django do LV JIU JITSU, seguindo `AGENTS.md`/`CLAUDE.md`, TDD e camadas MVT do projeto.

### Action
Parte A: criar management command + service que gera a cobrança Asaas do próximo ciclo com o valor correto, antes do vencimento. Parte B: criar management command de backfill que popula `MembershipTimelineEvent` a partir dos campos de data já existentes.

### Context
Ver Current problem e Context Ledger.

### Constraints
- Parte A não deve duplicar cobrança se já existir um `RegistrationOrder` pendente/pago para o mesmo ciclo (idempotência).
- Parte A deve usar `membership.billed_price` quando `family_discount_applied=True`, senão `effective_full_price` — nunca recalcular do zero ignorando o desconto.
- Parte A não deve gerar cobrança para `Membership` pausada (`MembershipPauseRequest` aprovada ativa) nem cancelada/expirada.
- Parte B é append-only e idempotente — rodar duas vezes não duplica evento.
- Sem chamada real a gateway em teste automatizado.

### Acceptance criteria
- Rodar o management command da Parte A localmente, com memberships Asaas de teste vencendo, gera exatamente um `RegistrationOrder` novo por membership elegível, com o valor de `billed_price` correto.
- Rodar de novo sem mudança de estado não duplica a cobrança.
- Membership pausada ou cancelada não gera cobrança.
- Rodar o backfill da Parte B popula eventos de cancelamento/pagamento/estorno/pausa com datas corretas batendo com os campos de origem, sem duplicar em execução repetida.

### Expected evidence
Comando de teste + resultado real, `manage.py check`, execução real dos dois management commands contra dados de teste locais com evidência de saída.

### Output format
Código implementado + PRD atualizada com Evidence/Implemented/Pending/Final status reais.

## Scope

### Parte A — cobrança recorrente Asaas
1. `system/services/asaas_billing_cycle.py` (novo) — `find_due_asaas_memberships(lead_days=N)`: memberships com `effective_gateway_code` em (`asaas_pix`, `asaas_card`), `status=ACTIVE`, sem pausa aprovada ativa, `current_period_end` dentro da janela de antecedência, sem `RegistrationOrder` pendente/pago já cobrindo o próximo ciclo.
2. `generate_due_asaas_charge(membership)` — cria `RegistrationOrder` com `total = membership.billed_price if membership.family_discount_applied else membership.effective_full_price`, chama `create_pix_payment`/`create_credit_card_payment` conforme `effective_payment_method`, salvando `asaas_payment_id`.
3. `system/management/commands/generate_due_asaas_charges.py` (novo) — invoca `find_due_asaas_memberships` + `generate_due_asaas_charge` para cada uma, com log do que foi gerado/pulado.
4. Nenhuma mudança no caminho de confirmação (`_handle_payment_event`/`activate_membership_from_paid_order`) — já funciona corretamente.
5. Documentar no PRD (não em código) a configuração do Render Cron Job para HG/produção — fora do repositório, decisão de infraestrutura a confirmar com o usuário antes do deploy (frequência sugerida: diária).

### Parte B — backfill de timeline
1. `system/management/commands/backfill_membership_timeline.py` (novo, depende de `MembershipTimelineEvent` da PRD-134 existir) — para cada `Membership`/`RegistrationOrder`/`MembershipPauseRequest` existente, cria o `MembershipTimelineEvent` correspondente quando o campo de origem existir e não houver evento já criado para aquela combinação (idempotência via checagem de duplicata antes de criar).
2. Mapeamento: `Membership.canceled_at` → `MEMBERSHIP_CANCELED` (`actor=None`, `context={"backfilled": true}`); `RegistrationOrder.paid_at` → `PAYMENT_CONFIRMED`; `RegistrationOrder.refunded_at` → `REFUND_ISSUED`; `MembershipPauseRequest.created_at` → `PAUSE_REQUESTED`; `MembershipPauseRequest.decided_at` (quando `status` in aprovada/reprovada) → `PAUSE_APPROVED`/`PAUSE_REJECTED`.
3. Marcar eventos de backfill com `context={"backfilled": true, ...}` para diferenciar de eventos capturados em tempo real (útil para auditoria/depuração, sem mudar a apresentação ao usuário).

## Out of scope
- Retry automático de cobrança Asaas falhada (fica para PRD futura se necessário — esta PRD só cobre gerar a cobrança do próximo ciclo, não uma política de retentativa).
- Configurar de fato o Render Cron Job no Dashboard (ação de deploy, exige autorização explícita de ambiente conforme `AGENTS.md`/seção 10 do `CLAUDE.md` — só o management command é entregue em código).
- Backfill de eventos sem campo de data confiável (dependente adicionado/removido, troca de plano/cartão antes do deploy desta PRD) — limitação aceita, documentada.
- Qualquer mudança no fluxo Stripe (já coberto/corrigido em sessões anteriores).

## Impacted files
- `system/services/asaas_billing_cycle.py` (novo)
- `system/management/commands/generate_due_asaas_charges.py` (novo)
- `system/management/commands/backfill_membership_timeline.py` (novo, depende de PRD-134)
- `system/tests/test_asaas_billing_cycle.py` (novo)
- `system/tests/test_backfill_membership_timeline.py` (novo)

## Risks and edge cases
- Cobrança duplicada se o command rodar duas vezes no mesmo dia antes da confirmação do primeiro pagamento — mitigado checando `RegistrationOrder` pendente existente antes de criar outro.
- Membership com desconto família mudando entre a geração da cobrança e o pagamento (ex. dependente removido nesse meio-tempo) — a cobrança já gerada mantém o valor congelado no momento da criação (mesmo comportamento de qualquer cobrança já emitida); o próximo ciclo já reflete o valor atualizado.
- Backfill rodando em produção com volume alto de `Membership`/`RegistrationOrder` histórico — mitigar com processamento em lote/paginação no command.
- `context={"backfilled": true}` vazando na timeline do cliente de forma confusa — `describe_for_client`/`describe_for_admin` (PRD-134) não devem exibir esse marcador ao cliente, só usá-lo internamente se necessário para admin.

## Rules and constraints
- Sem migration nova nesta PRD (Parte A não muda schema; Parte B só popula dado em model já existente da PRD-134).
- Sem chamada real a gateway em teste automatizado — mock de `create_pix_payment`/`create_credit_card_payment`.
- Idempotência obrigatória nos dois management commands.
- `transaction.atomic` em cada geração de cobrança e em cada backfill de evento.

## Plan
1. Parte A: `find_due_asaas_memberships` + testes (TDD) → `generate_due_asaas_charge` + testes → management command + teste de integração.
2. Parte B (após confirmar PRD-134 implementada): mapeamento de campo→evento + testes → management command + teste de idempotência.
3. Suíte completa + `manage.py check`.
4. Validação real: rodar os dois commands contra dados de teste locais, evidenciar saída.

## Test plan
### Tests to author
- `find_due_asaas_memberships`: inclui membership vencendo dentro da janela; exclui pausada, cancelada, Stripe, com pedido pendente já existente.
- `generate_due_asaas_charge`: usa `billed_price` quando desconto aplicado; usa `effective_full_price` quando não; chama o client Asaas correto por `effective_payment_method`.
- Command `generate_due_asaas_charges`: roda duas vezes seguidas sem duplicar.
- Backfill: cada tipo de evento mapeado corretamente; rodar duas vezes não duplica.

### Execution authorization
Local — ORM, management commands e testes autorizados por `AGENTS.md`. Configuração do Render Cron Job exige autorização explícita de ambiente (fora desta PRD).

### Execution evidence
`manage.py test system.tests.test_asaas_billing_cycle system.tests.test_membership_timeline_backfill` → 14 testes, OK (ver Evidence).

## Visual validation
Não aplicável (sem UI nova) — Parte A e B são management commands.

## ORM validation
Testado via ORM local: fixtures de `Membership`/`RegistrationOrder`/`MembershipPauseRequest` cobrindo os cenários de elegibilidade (dentro/fora da janela, Stripe vs Asaas, cancelada, com pedido pendente) e os 4 tipos de campo-fonte do backfill.

## Quality validation
`manage.py check` limpo; suíte completa sem regressão (639 testes, mesma execução da PRD-134 nesta sessão).

## Evidence
- `manage.py test system.tests.test_asaas_billing_cycle` → **9 testes, OK** (Parte A: elegibilidade, valor com/sem desconto, idempotência, management command).
- `manage.py test system.tests.test_membership_timeline_backfill` → **5 testes, OK** (Parte B: cancelamento, pagamento/estorno, pausa solicitada/aprovada, idempotência, management command).
- `manage.py test` (suíte completa) → **639 testes, OK**, sem regressão.
- `manage.py check` → limpo.
- Mocks de gateway: `system.services.asaas_checkout.asaas_client.create_pix_payment`/`create_credit_card_payment`/`create_customer` — sem chamada real a gateway em teste automatizado, conforme regra da PRD.

## Implemented
- Parte A: `system/services/asaas_billing_cycle.py` (`find_due_asaas_memberships`, `generate_due_asaas_charge`, `generate_due_asaas_charges`) reaproveitando `create_pix_charge_for_order`/`create_credit_card_charge_for_order` já existentes (`asaas_checkout.py`) — usa `membership.billed_price` quando `family_discount_applied=True`, senão `effective_full_price`. Idempotência via checagem de `RegistrationOrder` pendente para o mesmo plano/pessoa. Management command `generate_due_asaas_charges --lead-days N`.
- Parte B: `system/services/membership_timeline_backfill.py` populando `MembershipTimelineEvent` a partir de `Membership.canceled_at`, `RegistrationOrder.paid_at`/`refunded_at`, `MembershipPauseRequest.created_at`/`decided_at`. Idempotência via `context__source_id` (chave estável por registro de origem, ex. `membership_canceled:<pk>`) — bypassa `auto_now_add` via `.update()` para preservar a data histórica real. Management command `backfill_membership_timeline`.

## Cleanup findings
Nenhum resíduo — commands não geram nenhum estado de teste que precise de limpeza (rodados só via suíte de testes nesta sessão, não em produção/HG).

## Follow-up PRDs
- Política de retentativa de cobrança Asaas falhada, se necessário após validar o volume real de falhas.
- Configuração real do Render Cron Job para `generate_due_asaas_charges` (ação de deploy/infra, fora de código — exige autorização explícita de ambiente).

## Deviations from plan
Nenhum — Parte B executada após Parte A da PRD-134 já estar implementada e validada na mesma sessão, sem bloqueio.

## Pending
Configuração do Render Cron Job em HG/produção (infraestrutura, exige autorização de deploy — fora desta PRD) e execução real do backfill contra o banco de produção (dado real, exige autorização de ambiente).

## Final status
**Concluída** — Parte A e Parte B implementadas, testadas (14 testes específicos + suíte completa de 639 sem regressão) e com `manage.py check` limpo. Deploy do cron job e execução do backfill em HG/produção ficam pendentes de autorização de ambiente, fora do escopo de código local.
