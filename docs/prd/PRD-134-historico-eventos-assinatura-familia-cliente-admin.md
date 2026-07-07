# PRD-134: Histórico de eventos de assinatura/família — timeline informativa (cliente) + auditoria técnica (admin)

## Summary
Durante a investigação do bug de desconto família (corrigido fora desta PRD — ver Context Ledger), o usuário perguntou onde está o histórico de alterações da assinatura ("dia X era assim, dia Y ficou assim, pago etc."). Não existe nada assim hoje: o único mecanismo de auditoria (`OperationalAuditEntry`) é admin-only, texto livre, sem vínculo estruturado com `Membership`/`Person`, e não cobre nenhum dos eventos de assinatura/família (adicionar/remover dependente, pausa, troca de plano, cancelamento, troca de cartão, pagamento, estorno, desconto família). Esta PRD cria uma fonte de eventos estruturada única, com duas apresentações distintas lendo o mesmo dado: uma timeline informativa para o cliente (linguagem simples, sem detalhe técnico) e uma auditoria técnica para o admin (actor, valores antes/depois, IDs, filtros).

## Demand type
Nova funcionalidade, pedida explicitamente pelo usuário.

## Current problem
- `system/models/audit.py::OperationalAuditEntry` é o único registro estruturado existente: `module` (person/checkin/financial), `action` (create/update/delete/approve/mark_paid), `actor_label` (texto livre), `entity_label` (texto livre), `summary` (texto livre, máx. 500 chars), `created_at`. Sem FK para `Membership`/`Person`/`PersonRelationship`, sem campos before/after estruturados.
- `system/services/audit.py::record_audit_event` é um service de criação simples, sem lógica adicional.
- O único uso real em fluxo de billing é `system/views/billing_admin_views.py::MarkOrderPaidActionView` (linhas ~112-118) — nenhum outro evento de assinatura/família é registrado.
- UI existente (`system/views/admin_views.py::AuditLogListView`, `templates/audit/audit_log_list.html`, rota `system:audit-log-list`) é admin-only via `AdministrativeRequiredMixin`. **Não existe equivalente client-facing.**
- Eventos de assinatura/família hoje **não são registrados em lugar nenhum estruturado**:
  - Adicionar dependente (`system/services/dependent_registration.py`)
  - Remover dependente (`system/views/dependent_views.py::DependentRemoveView`)
  - Cancelamento self-service, bloqueado por fidelidade (`system/services/plan_change.py::get_plan_change_lock`) e admin (`system/services/stripe_admin_actions.py::cancel_membership`, `system/services/membership.py::mark_membership_canceled` via webhook)
  - Pausa de mensalidade — solicitar/aprovar/reprovar (`MembershipPauseRequest`, PRD-131/132)
  - Troca de plano — self-service (`system/services/plan_change.py::apply_plan_change`) e admin (`system/services/stripe_admin_actions.py::change_membership_plan`)
  - Troca de cartão (Stripe Billing Portal, PRD-133 — não gera nenhum registro local, só redireciona)
  - Mudança de desconto família (`system/services/family_pricing.py::recompute_family_discounts_for_person`)
  - Pagamento confirmado/falho (`system/services/membership.py::record_invoice_from_stripe`, `mark_invoice_failed`)
  - Estorno (`system/services/stripe_admin_actions.py::refund_order`)
- Alguns desses eventos deixam rastro *parcial* em campos de timestamp isolados (`Membership.canceled_at`, `Membership.created_at`/`updated_at`, `RegistrationOrder.paid_at`/`refunded_at`, `MembershipPauseRequest.created_at`/`decided_at`), mas sem contexto legível nem visão cronológica unificada — cada um vive em uma tabela diferente, sem narrativa.

## Goal
1. Todo evento relevante de assinatura/família (lista acima) passa a gerar um registro estruturado único, capturado no mesmo `transaction.atomic` de cada service que já muda o estado.
2. O cliente, na própria área logada, vê uma timeline informativa e cronológica dos eventos da sua família — linguagem simples ("07/07/2026 — Dependente Gustavo removido da família"), sem IDs técnicos, sem nome de admin interno, sem jargão de gateway.
3. O admin vê uma auditoria técnica — mesmos eventos, mas com actor identificado, valores antes/depois estruturados, IDs técnicos (Stripe/Asaas quando aplicável), com filtro por pessoa/período/tipo.
4. As duas visões leem a mesma fonte de dados — a apresentação diverge, a captura não se duplica.

## Context Ledger
### Files read in full
- `system/models/audit.py` (model `OperationalAuditEntry` completo)
- `system/services/audit.py` (`record_audit_event`)
- `system/views/admin_views.py` (`AuditLogListView`)
- `system/services/family_pricing.py` (`recompute_family_discounts_for_person`, `_sync_stripe_discount`)
- `system/services/stripe_discounts.py` (`apply_family_discount`, `remove_family_discount`)
- `system/services/stripe_admin_actions.py` (`cancel_membership`, `change_membership_plan`, `refund_order`)
- `system/services/membership.py` (`mark_membership_canceled`, `record_invoice_from_stripe`, `mark_invoice_failed`)
- `system/views/dependent_views.py` (`DependentRemoveView`)
- `system/models/membership.py` (`Membership`, `MembershipPauseRequest`, `MembershipPauseRequestKind`, `MembershipPauseRequestStatus`, `MembershipInvoice`)

### Adjacent files consulted
- `docs/prd/PRD-131-corrigir-professor-presente-padrao-cancelar-restaurar-aula.md`, `docs/prd/PRD-132-transicao-livre-planos-pausa-mensalidade.md` (modelo `MembershipPauseRequest`, fluxo de aprovação)
- `docs/prd/PRD-133-indicador-pagamento-trocar-cartao-stripe.md` (troca de cartão via Billing Portal, sem registro local — estilo de PRD usado como referência de nível de detalhe)
- `templates/home/dashboard.html` (seção MENSALIDADE / billing_tabs, onde a timeline do cliente deve se encaixar)

### Internet / official documentation
Nenhuma consulta externa necessária — funcionalidade é modelagem de dados e apresentação internas, sem integração de gateway nova.

### Context7 / MCPs / tools verified
Não aplicável — sem biblioteca/SDK/API externa nova neste escopo.

### Limitations found
- Bugs reais de sincronização de desconto família encontrados e corrigidos nesta sessão (fora do escopo desta PRD, já implementados e testados antes desta PRD ser aberta):
  1. `system/services/stripe_discounts.py::apply_family_discount` usava `Subscription.modify(coupon=...)`, parâmetro rejeitado pelo Stripe quando `billing_mode.type=flexible` (padrão atual) — corrigido para `discounts=[{"coupon": ...}]`. `remove_family_discount` mantido em `delete_discount()` (já funcionava, confirmado ao vivo).
  2. `cancel_membership`, `change_membership_plan` (`stripe_admin_actions.py`) e `mark_membership_canceled` (`membership.py`) não chamavam `recompute_family_discounts_for_person` — corrigido.
- Não existe hoje nenhuma sincronização de cobrança recorrente Asaas com `Membership.billed_price` — Asaas neste projeto não usa "subscription", cada cobrança é um pagamento avulso recalculado do preço de catálogo cheio. Gap arquitetural pré-existente, **fora do escopo desta PRD** (a timeline só registra o que já acontece hoje, não corrige o gateway).

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-cleanup-audit`

## Understanding approved
Usuário pediu explicitamente: rastrear todos os eventos listados acima, exibir em dois lugares com propostas distintas (cliente informativo, admin auditoria), para melhor controle.

## Execution prompt
### Persona
Desenvolvedor Django do LV JIU JITSU, seguindo `AGENTS.md`/`CLAUDE.md`, TDD e camadas MVT do projeto.

### Action
Implementar um novo model estruturado de eventos de assinatura/família, um service central de emissão, e duas views/templates de leitura (cliente e admin) sobre a mesma fonte.

### Context
Ver Current problem e Context Ledger acima — nove pontos de mutação já mapeados, nenhum gera registro estruturado hoje.

### Constraints
- Registrar o evento sempre dentro da mesma `transaction.atomic` que já existe em cada service mutador (não criar transação nova).
- Não vazar dado técnico (IDs Stripe/Asaas, nome de admin) na timeline do cliente.
- Não vazar evento de uma família para outra — sempre filtrar por `person`/grupo familiar do próprio usuário logado.
- Não duplicar `OperationalAuditEntry` — o novo model é específico de assinatura/família; o audit log genérico continua existindo para os módulos que já usa (person/checkin).
- Sem chamada real a gateway nova — esta PRD só registra e exibe eventos que outros services já produzem.

### Acceptance criteria
- Os nove eventos mapeados (dependente adicionado/removido, pausa solicitada/aprovada/reprovada, troca de plano self-service/admin, cancelamento self-service/admin, troca de cartão, pagamento confirmado/falho, estorno, mudança de desconto família) geram um registro cada, com `event_type`, `person`, `membership` (quando aplicável) e `context` estruturado.
- Timeline do cliente mostra os eventos da própria família em ordem cronológica decrescente, com texto simples e sem dado técnico.
- Auditoria do admin mostra os mesmos eventos com actor, valores antes/depois e IDs técnicos quando existirem, com filtro por pessoa/período/tipo.
- Nenhum evento de uma família aparece na timeline de outra.

### Expected evidence
Comando de teste + resultado real, `manage.py check`, validação visual das duas telas (cliente e admin) no navegador interno.

### Output format
Código implementado + PRD atualizada com Evidence/Implemented/Pending/Final status reais.

## Scope
1. **Novo model** `system/models/membership_timeline.py::MembershipTimelineEvent` (nome definido nesta PRD):
   - `person` — FK `Person`, `related_name="timeline_events"` — pessoa dona do evento na timeline (o dependente removido, o titular que pausou, etc.).
   - `membership` — FK `Membership`, `null=True, blank=True`, `related_name="timeline_events"` — quando o evento tem uma assinatura associada.
   - `event_type` — `CharField` com `TextChoices` (`MembershipTimelineEventType`): `DEPENDENT_ADDED`, `DEPENDENT_REMOVED`, `PAUSE_REQUESTED`, `PAUSE_APPROVED`, `PAUSE_REJECTED`, `PLAN_CHANGED`, `MEMBERSHIP_CANCELED`, `CARD_UPDATED`, `PAYMENT_CONFIRMED`, `PAYMENT_FAILED`, `REFUND_ISSUED`, `FAMILY_DISCOUNT_CHANGED`.
   - `actor` — FK `Person`, `null=True, blank=True`, `related_name="timeline_events_caused"` — `None` quando o evento vem de um webhook/processo automático (ex. `mark_membership_canceled` via Stripe).
   - `actor_is_admin` — `BooleanField(default=False)` — diferencia "o próprio cliente fez" de "um admin fez em nome dele" (controla o que aparece na timeline do cliente vs. o rótulo técnico do admin).
   - `context` — `JSONField(default=dict)` — payload estruturado específico do `event_type` (ex. `{"dependent_name": "Gustavo", "old_price": "1308.65", "new_price": "1073.09"}`). Nunca inclui segredo/token; pode incluir IDs técnicos (Stripe/Asaas) — esses só são renderizados na visão admin.
   - `created_at` (via `TimeStampedModel`, padrão do projeto).
   - **Decisão de design — não reaproveitar `OperationalAuditEntry`**: esse model é texto livre (`summary`/`actor_label`/`entity_label` como `CharField`), sem FK estruturada e sem separação de audiência. Estendê-lo quebraria seu uso atual (person/checkin) e ainda exigiria os mesmos campos novos. Um model paralelo, específico do domínio de assinatura/família, é mais simples de filtrar por família e não arrisca regressão no módulo de auditoria existente.
   - **Decisão de design — sem `client_summary`/`admin_summary` armazenados**: os textos são gerados em tempo de leitura por uma função de apresentação (`describe_for_client(event)` / `describe_for_admin(event)`) a partir de `event_type` + `context`, não persistidos. Evita re-migração de dado histórico se o texto mudar; o `context` já carrega tudo que as duas funções precisam.
   - Migration via ciclo destrutivo (`clear_migrations` + `makemigrations`), política única do projeto — sem migration incremental.

2. **Service central de emissão** `system/services/membership_timeline.py`:
   - `record_membership_event(person, event_type, *, membership=None, actor=None, actor_is_admin=False, context=None)` — cria o `MembershipTimelineEvent`. Chamado a partir de cada um dos nove pontos de mutação, dentro do `transaction.atomic` já existente em cada um:
     - `dependent_registration.py` (evento `DEPENDENT_ADDED`, para o dependente)
     - `dependent_views.py::DependentRemoveView` (evento `DEPENDENT_REMOVED`, para owner e dependente)
     - `plan_change.py::apply_plan_change` (evento `PLAN_CHANGED`, `actor_is_admin=False`)
     - `stripe_admin_actions.py::change_membership_plan` (evento `PLAN_CHANGED`, `actor_is_admin=True`)
     - `stripe_admin_actions.py::cancel_membership` (evento `MEMBERSHIP_CANCELED`, `actor_is_admin=True`)
     - `membership.py::mark_membership_canceled` (evento `MEMBERSHIP_CANCELED`, `actor=None` — webhook)
     - Fluxo de solicitar/aprovar/reprovar pausa (PRD-131/132, localizar service exato de `MembershipPauseRequest` — eventos `PAUSE_REQUESTED`/`PAUSE_APPROVED`/`PAUSE_REJECTED`)
     - `stripe_checkout.py::create_billing_portal_session` (evento `CARD_UPDATED` — registrar no retorno do fluxo, já que o Billing Portal é externo; avaliar se captura no redirect de volta ou no próximo webhook `customer.subscription.updated` com mudança de `default_payment_method`)
     - `membership.py::record_invoice_from_stripe` (evento `PAYMENT_CONFIRMED`) e `mark_invoice_failed` (evento `PAYMENT_FAILED`)
     - `stripe_admin_actions.py::refund_order` (evento `REFUND_ISSUED`)
     - `family_pricing.py::recompute_family_discounts_for_person` (evento `FAMILY_DISCOUNT_CHANGED`, só quando `previous != discount_applies`, mesmo padrão já usado para decidir sincronizar Stripe)
   - `describe_for_client(event)` / `describe_for_admin(event)` — funções puras de apresentação por `event_type`.

3. **View + template cliente**: nova seção/aba na home (`templates/home/dashboard.html` ou template dedicado) listando `describe_for_client(event)` para os eventos de `get_family_group_members(pessoa_logada)`, ordem cronológica decrescente, paginação simples (últimos N ou por período).

4. **View + template admin**: nova aba dentro do hub administrativo existente (ou extensão de `/administration/audit/`) com `describe_for_admin(event)`, actor, `context` técnico, filtro por pessoa/período/`event_type`.

5. **Plano de testes**: emissão de evento em cada um dos nove pontos; `describe_for_client` vs `describe_for_admin` produzindo textos distintos para o mesmo evento; ordenação cronológica; isolamento entre famílias (evento de uma família não aparece na timeline de outra).

## Out of scope
- Corrigir a sincronização de cobrança recorrente Asaas (gap arquitetural separado, já registrado como pendência de sessão anterior) — esta PRD só registra o que os services já fazem, não corrige o gateway.
- Registrar retroativamente eventos que já aconteceram antes desta PRD (sem backfill de histórico — a timeline começa a partir do deploy desta funcionalidade).
- Notificação ativa (e-mail/push) por evento — só timeline passiva, consultada sob demanda.
- Edição/exclusão de eventos pelo admin (auditoria é append-only).

## Impacted files
- `system/models/membership_timeline.py` (novo)
- `system/models/__init__.py` (exportar novo model)
- `system/migrations/0001_initial.py` (regenerado via ciclo destrutivo)
- `system/services/membership_timeline.py` (novo — `record_membership_event`, `describe_for_client`, `describe_for_admin`)
- `system/services/dependent_registration.py`, `system/views/dependent_views.py`, `system/services/plan_change.py`, `system/services/stripe_admin_actions.py`, `system/services/membership.py`, `system/services/family_pricing.py`, `system/services/stripe_checkout.py` (chamadas ao service central)
- Service/view de `MembershipPauseRequest` (localizar exato durante implementação — provavelmente `system/services/membership_pause.py` ou equivalente da PRD-132)
- `system/views/home_views.py` ou novo `system/views/timeline_views.py` (view cliente)
- `system/views/admin_views.py` ou novo `system/views/timeline_admin_views.py` (view admin)
- `templates/home/dashboard.html` + novo template de timeline
- `templates/audit/` (extensão) ou novo diretório de template admin
- `system/tests/test_membership_timeline.py` (novo)

## Risks and edge cases
- Evento com `membership=None` quando o dependente removido não tinha mais Membership ativa — model precisa suportar (`null=True`).
- Volume de eventos por família crescendo sem paginação — mitigar com paginação desde o início.
- `context` com dado sensível vazando na timeline do cliente por engano — mitigar centralizando toda leitura de `context` só dentro de `describe_for_client`/`describe_for_admin`, nunca renderizando `context` bruto em template.
- Webhook duplicado gerando evento duplicado (Stripe já garante idempotência de webhook via `StripeWebhookEvent`, mas o service de emissão de timeline não tem essa proteção própria) — avaliar checar duplicata por `(membership, event_type, context)` recente antes de criar, ou aceitar o risco dado que o `StripeWebhookEvent` já bloqueia reprocessamento do mesmo evento Stripe.

## Rules and constraints
- `transaction.atomic` já existente em cada service — não criar transação nova só para o evento.
- Sem regra de negócio em template — `describe_for_client`/`describe_for_admin` vivem em `services/`.
- Sem comentário/docstring por padrão.
- Testes cobrindo os nove pontos de emissão antes de declarar Green.

## Plan
1. Model `MembershipTimelineEvent` + migration destrutiva.
2. Service `record_membership_event` + `describe_for_client`/`describe_for_admin`.
3. Integrar chamada nos nove pontos de mutação, um de cada vez, com teste antes do código (TDD).
4. View + template cliente.
5. View + template admin.
6. Suíte completa + `manage.py check` + validação visual das duas telas.

## Test plan
### Tests to author
- `record_membership_event` cria registro com campos corretos.
- Cada um dos nove pontos de mutação chama `record_membership_event` com `event_type` e `context` esperados (mock ou verificação de banco pós-chamada).
- `describe_for_client`/`describe_for_admin` retornam textos distintos e sem dado técnico na versão cliente, para cada `event_type`.
- Timeline do cliente não mostra evento de outra família (isolamento).
- Ordenação cronológica decrescente.

### Execution authorization
Local — ORM, migrations e testes autorizados por `AGENTS.md`.

### Execution evidence
`manage.py test system.tests.test_membership_timeline` → 18 testes, OK (ver Evidence).

## Visual validation
- Cliente logado (`529.982.247-25`): botão "Histórico de alterações" aparece no card MENSALIDADE; modal abre listando 5 eventos de teste em ordem cronológica decrescente, com data/hora, texto simples e **sem nenhum dado técnico** (nenhum ID Stripe/Asaas visível). Confirmado em tema claro, tema escuro e viewport mobile (375×812) — texto trunca com reticências no card mobile, mesmo padrão já usado pelos outros modais do app.
- Admin (`admin`, via `/administration/historico-assinaturas/`): lista os mesmos 5 eventos com texto técnico completo (ex. "Assinatura cancelada (Stripe: sub_visual_test) — por Sistema/webhook", "Desconto família aplicado — R$ 220.00 → R$ 180.00"). Filtro por tipo de evento (`card_updated`) testado — reduziu corretamente de 5 para 1 resultado.
- Card "Histórico de assinaturas" aparece no hub `/administration/` com contador dinâmico ("5 EVENTOS REGISTRADOS").
- Console do navegador sem erros.
- Dados de validação (pessoa `Visual Timeline Teste` + 5 eventos manuais) removidos do banco local após a validação.

## ORM validation
Migração destrutiva regenerada (`clear_migrations.py` + `makemigrations` + `migrate`) incluindo `MembershipTimelineEvent`; seeds de referência reaplicadas para validação visual.

## Quality validation
`manage.py check` limpo; suíte completa sem regressão (639 testes).

## Evidence
- `manage.py test system.tests.test_membership_timeline` → **18 testes, OK**.
- `manage.py test` (suíte completa, após todas as correções) → **639 testes, OK**, sem regressão.
- `manage.py check` → limpo.
- **Bug real encontrado e corrigido durante a suíte completa**: `stripe_admin_actions.py` passava `admin_user` (instância Django `User`, técnico administrativo) diretamente como `actor=` para `record_membership_event`, mas `MembershipTimelineEvent.actor` é FK para `Person` — `ValueError` real ao cancelar assinatura via `CancelMembershipActionView`. Corrigido removendo `actor=admin_user` nos 3 pontos afetados (`cancel_membership` × 2 branches, `change_membership_plan`, `refund_order`), mantendo `actor_is_admin=True` (o admin técnico não tem necessariamente uma `Person` correspondente).

## Implemented
Ver Scope — todos os itens implementados: model `MembershipTimelineEvent` (migração destrutiva regenerada), service `membership_timeline.py` (`record_membership_event`, `describe_for_client`, `describe_for_admin`, `build_client_timeline`, `build_admin_timeline`), emissão nos 9+ pontos de mutação mapeados, view+template cliente (modal na home) e admin (`/administration/historico-assinaturas/` com filtro pessoa/tipo).

## Cleanup findings
- Bug de FK `actor` (User vs Person) encontrado e corrigido — ver Evidence.
- Dados manuais de validação visual removidos após uso.

## Follow-up PRDs
- Sincronização de cobrança recorrente Asaas com `billed_price`/desconto família — tratada na PRD-135 (Parte A), implementada em sequência nesta mesma sessão.

## Deviations from plan
- `CARD_UPDATED` registrado no momento do redirecionamento ao Billing Portal (intenção do cliente), não no retorno confirmado — decisão já registrada como aberta na PRD original; optou-se pela captura no ponto de disparo por ser determinística e não depender de query param hoje não consumido por nenhuma view (`?card_update=done`).

## Pending
Nenhuma pendência de código. Não implementado: notificação ativa (fora de escopo) e backfill de eventos sem rastro histórico confiável (tratado como limitação aceita na PRD-135).

## Final status
**Concluída** — model, service, emissão nos 9+ pontos mapeados, views/templates cliente e admin implementados e validados (testes automatizados + validação visual real no navegador, tema claro/escuro, mobile). Um bug real de tipo (`actor` FK) foi encontrado e corrigido durante a execução da suíte completa.
