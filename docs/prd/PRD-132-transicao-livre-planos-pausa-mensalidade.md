# PRD-132: Transição livre entre planos + pausa de mensalidade (atestado e trancamento)

## Summary
Duas frentes relacionadas de flexibilização contratual, pedidas pelo usuário após identificar que o catálogo de troca de plano nunca oferece migração para Stripe recorrente:

**A) Transição livre entre planos** — permitir migrar de/para qualquer gateway (Asaas ↔ Stripe) via "Trocar plano", respeitando a trava de fidelidade Stripe já existente (`is_plan_change_locked`) — hoje o catálogo de destino exclui `gateway_code="stripe_card"` incondicionalmente, mesmo para quem não está preso a fidelidade nenhuma.

**B) Pausa de mensalidade** — dois mecanismos distintos, com regras de negócio próprias:
- **B1) Pausa por atestado médico**: sempre permitida, mesmo durante a carência de fidelidade Stripe. Suspende a cobrança pelo período informado no atestado e **posterga a data-fim da carência** pelo mesmo número de dias (a fidelidade não encolhe por causa de um problema de saúde, mas também não é "gasta" indevidamente). Exige aprovação administrativa.
- **B2) Trancamento self-service**: cota de até 30 dias por ano, sem exigir atestado, disponível **apenas fora do período de carência** (Asaas sempre; Stripe só depois que a fidelidade — original ou já prorrogada por B1 — terminar).
- Em ambos os casos: check-in bloqueado durante a pausa; vencimento/próxima cobrança postergado pelo período pausado.

**C) Transparência no cadastro** — as regras de trancamento/pausa devem estar visíveis para o cliente já na seleção de plano/resumo do wizard (público e de dependente), não só depois de contratado.

## Demand type
Nova funcionalidade (pedida explicitamente pelo usuário, com regras de negócio detalhadas por ele após pergunta de esclarecimento desta sessão).

## Current problem
- `build_plan_catalog` (`system/services/plan_change.py:302-311`) exclui `gateway_code="stripe_card"` do catálogo de troca **sempre**, para qualquer cliente, independente de estar ou não em carência — não existe hoje nenhum caminho self-service para migrar para um plano Stripe recorrente depois do cadastro inicial.
- Não existe conceito de "pausa"/"trancamento" no sistema: `MembershipStatus` (`system/models/membership.py:11-17`) tem `pending`, `active`, `past_due`, `canceled`, `expired`, `exempted` — nenhum estado de pausa temporária.
- `PRD-117` (fidelidade contratual) permanece pendente — hoje a "carência" é só um proxy via `Membership.current_period_end` (quando há `stripe_subscription_id` ou `plan.gateway_code == "stripe_card"`), sem campo dedicado. Esta PRD **não** cria esse campo dedicado; continua usando o mesmo proxy, mas precisa de um novo campo para "quanto a carência foi prorrogada por pausas médicas" (não pode simplesmente sobrescrever `current_period_end`, que também controla o ciclo de cobrança).
- Não existe fila de aprovação administrativa reaproveitável para este caso — o padrão mais próximo é o de `PRD-112` (solicitação de acesso administrativo pendente: `pending → approved/rejected/canceled`), que será usado como referência de arquitetura.
- Não existe upload/registro de atestado médico em nenhum lugar do sistema.
- Nenhuma cota anual (dias usados/ano) é rastreada em lugar nenhum do domínio hoje.

## Goal
1. Cliente sem trava de fidelidade (Asaas, ou Stripe fora da carência) pode trocar para **qualquer** plano ativo, incluindo Stripe recorrente, via "Trocar plano".
2. Cliente pode solicitar pausa por atestado médico a qualquer momento (mesmo em carência); fica "aguardando aprovação"; ao aprovar, cobrança suspensa no período informado e carência prorrogada pelo mesmo número de dias.
3. Cliente fora de carência pode trancar a matrícula sem atestado, até 30 dias por ano corrente, controlado automaticamente pelo sistema (não pode passar da cota).
4. Em ambos os casos de pausa aprovada: check-in bloqueado durante o período; vencimento/próxima cobrança postergado.
5. As regras de trancamento/pausa aparecem de forma clara para o cliente no momento da seleção de plano/resumo do cadastro (público e dependente).

## Context Ledger
### Files read in full
- `system/services/plan_change.py` (`build_plan_catalog`, `is_plan_change_locked`, `get_plan_change_lock`, `_STRIPE_RECURRING_GATEWAY_CODE`)
- `system/models/membership.py` (`Membership`, `MembershipStatus`, `MembershipCredit`, `MembershipInvoice` — nenhum campo de pausa/carência prorrogada existe)
- `system/services/stripe_admin_actions.py` (`cancel_membership`, `change_membership_plan` — padrão de chamada `stripe.Subscription.modify`, já usa `metadata` e `transaction.atomic`)
- `system/services/stripe_checkout.py` (`create_subscription_session_for_pre_registration` — hoje só cria sessão para `PreRegistration` nova, não para migrar uma `Membership` existente)
- `docs/prd/PRD-117-fidelidade-contratual-planos-recorrentes.md` (confirma: nunca implementada, "não implementar sem aprovação explícita" — este PRD-132 não a substitui, apenas adiciona um campo de prorrogação sem mexer no restante do escopo dela)
- `docs/prd/PRD-112-solicitacao-acesso-administrativo-pendente.md` (padrão de referência: model com status `pending/approved/rejected/canceled`, fila administrativa com filtros, decisão transacional com `select_for_update`)
- `docs/prd/PRD-116-home-aluno-permissoes-cronograma-fidelidade.md` (origem da trava de fidelidade atual)

### Adjacent files consulted
- `system/services/class_calendar.py::perform_checkin` / `_student_instructor_present` (ponto de bloqueio de check-in a estender)
- `templates/login/register.html`, `templates/dependents/dependent_registration.html` (onde a transparência de regras precisa aparecer)

### Limitations found
- Não existe infraestrutura de upload de arquivo (atestado médico como PDF/imagem) usada em nenhum outro fluxo do sistema hoje. Registrar o atestado como **texto/observação + período informado** (sem anexo de arquivo) é o caminho mínimo compatível com o que já existe; anexar arquivo é uma extensão possível, mas fora do escopo inicial desta PRD (registrar como pendência/follow-up).
- Stripe `pause_collection` (`behavior="void"` ou `"mark_uncollectible"`) precisa ser validado contra a documentação oficial atual da API antes da implementação (Context7/documentação Stripe) — não presumir o payload exato sem confirmar.
- "Ano corrente" para a cota de 30 dias de trancamento self-service: confirmado pelo usuário como **aniversário da matrícula** (`Membership.activated_at`), não ano civil.

## Required skills
`lv-task-intake`, `lv-prd`, `lv-django-delivery`, `lv-ui-delivery`, `lv-cleanup-audit`

## Understanding approved
Usuário pediu explicitamente a PRD e detalhou as regras de negócio em resposta a perguntas de esclarecimento desta sessão (trancamento self-service e pausa médica são mecanismos **separados**; pausa médica sempre suspende cobrança real e posterga a carência; trancamento self-service só fora da carência, cota de 30 dias/ano; check-in bloqueado durante qualquer pausa).

## Scope

### Fase A — Catálogo de troca sem exclusão de gateway
- `build_plan_catalog`: remover `.exclude(gateway_code="stripe_card")` de ambas as queries (`get_eligible_plans`/`get_eligible_plan_prices`) — a trava de fidelidade (`is_plan_change_locked`) já impede a troca inteira quando aplicável; não há necessidade de excluir Stripe do catálogo à parte.
- Novo caminho de checkout para **migrar uma `Membership` existente para Stripe recorrente**: nova função em `stripe_checkout.py` (ex. `create_subscription_session_for_plan_change`), gerando uma `RegistrationOrder(is_plan_change=True, plan_price_ref=..., person=...)` e redirecionando para Stripe Checkout.
- **Bugs adicionais descobertos durante a investigação desta PRD (mesma família dos já corrigidos nas PRD-127/129/130), que bloqueiam a Fase A e precisam ser corrigidos como parte dela:**
  - `PaymentMethodChoiceView.get` (`system/views/payment_views.py:52-70`) decide o gateway só por `order.plan.payment_method` — para uma ordem `plan_price_ref` (PlanPrice), `order.plan` é `None`, então a condição `order.plan and ...` é `False` e a ordem **sempre** cai no `else` (Asaas PIX), mesmo quando deveria ser cartão Asaas ou Stripe. Roteamento silenciosamente errado, não é crash. Precisa resolver o `gateway_code` real (via `order.plan_price_ref.gateway_code` ou `order.plan.gateway_code`) e adicionar o branch Stripe.
  - `activate_membership_from_session` (`system/services/membership.py:81-136`, chamada pelo branch `mode == "subscription"` do webhook `checkout.session.completed` em `system/services/stripe_webhooks.py:145-176`) só lê `order.plan` (`if plan is None: return None`, linha 84) — para uma ordem de troca de plano baseada em `PlanPrice`, essa função aborta silenciosamente sem criar/atualizar nada, mesmo após um pagamento Stripe real confirmado. Além disso, esse branch **nunca verifica `order.is_plan_change`** (diferente do branch de pagamento único, que já verifica desde a PRD-130) — ou seja, mesmo corrigindo a leitura de `plan_price_ref`, hoje ele criaria/atualizaria uma `Membership` "nova" em vez de aplicar a troca sobre a `Membership` existente da pessoa (podendo duplicar assinatura ativa). Precisa: no branch `mode == "subscription"`, checar `order.is_plan_change` primeiro e, se verdadeiro, chamar `apply_plan_change` sobre a `Membership` ativa existente da pessoa (mesmo padrão já usado no branch de pagamento único), preenchendo depois os campos Stripe (`stripe_subscription_id`, `stripe_customer_id`, `current_period_start/end`) na `Membership` resultante.
- Novo caminho para **migrar de Stripe para Asaas**: cancelar a assinatura Stripe atual (reaproveitar padrão de `stripe_admin_actions.cancel_membership`, adaptado para acionamento pelo próprio cliente, sem exigir `admin_user`) e seguir o fluxo Asaas normal de troca (já existente).
- `PlanChangeSelectView`/`serialize_plan_with_proration`: adaptar para sinalizar quando o destino exige checkout completo (Stripe) vs troca instantânea com proração (Asaas↔Asaas) — o frontend (`dashboard.js`) precisa diferenciar "aplicar na hora" de "redirecionar para pagamento".

### Fase B — Pausa por atestado médico
- Novo model `MembershipPauseRequest` (ou nome equivalente): `membership`, `kind` (`medical`/`self_service`), `requested_start_date`, `requested_end_date`, `reason_note` (texto livre — descrição do atestado, sem upload de arquivo nesta fase), `status` (`pending/approved/rejected/canceled`), `requested_at`, `decided_by`, `decided_at`, `decision_note`.
- Ação do cliente: botão "Pausar mensalidade" no dashboard → modal com seleção de tipo (atestado médico vs trancamento, ver Fase C) → para atestado: datas do período + observação → cria `MembershipPauseRequest(kind=medical, status=pending)`.
- Fila administrativa (reaproveitar padrão de `PRD-112`): listar pendentes, aprovar/reprovar, com motivo.
- Ao aprovar uma pausa médica:
  - Suspende cobrança no período: para Stripe, usar `pause_collection` na Subscription (validar payload exato via documentação oficial antes de implementar); para Asaas, adiar a próxima cobrança/vencimento pelo mesmo número de dias (não há "assinatura" Asaas para pausar, é um adiamento de data).
  - Novo campo em `Membership` para rastrear prorrogação de carência (ex. `fidelity_extended_days` ou `fidelity_end_override`) — a data efetiva de fim de carência usada por `is_plan_change_locked` passa a considerar essa prorrogação somada ao `current_period_end` original.
  - `Membership.status` ganha novo valor (`PAUSED`) ou o estado "pausado" é derivado de `MembershipPauseRequest` aprovado com janela vigente (decisão técnica a definir na implementação — preferir derivar do pedido aprovado + datas, evitando duplicar estado e a necessidade de um cron para reverter o status automaticamente no fim do período).

### Fase C — Trancamento self-service (30 dias/ano)
- Mesmo model `MembershipPauseRequest`, `kind=self_service`.
- Regra de elegibilidade: só permitido quando `is_plan_change_locked(membership)` é `False` no momento da solicitação.
- Cota: soma de dias já usados em pedidos `self_service` **aprovados** dentro do ano-matrícula corrente (ver regra de reset abaixo) não pode ultrapassar 30 dias; a solicitação informa o período e o sistema valida a cota antes de permitir o envio.
- **Reset da cota**: por **aniversário da matrícula** (data de `Membership.activated_at`, por pessoa/assinatura — não é um reset global em 1º de janeiro). O "ano corrente" de uma solicitação é o intervalo `[último aniversário ≤ hoje, próximo aniversário)`.
- **Aprovação**: exige fila administrativa, igual à pausa médica (mesmo model, `kind` diferencia o tipo, mesma tela/decisão) — confirmado pelo usuário. A cota de 30 dias é validada na criação da solicitação (bloqueia envio acima da cota), mas a aplicação efetiva (suspender cobrança, bloquear check-in, postergar vencimento) só ocorre após aprovação, exatamente como a pausa médica.

### Fase D — Transparência no cadastro
- `templates/login/register.html` (wizard público) e `templates/dependents/dependent_registration.html` (wizard de dependente): adicionar bloco de texto nas etapas de seleção de plano/resumo explicando as duas regras (trancamento de até 30 dias/ano sem atestado, fora de carência; atestado médico sempre pausa a cobrança e posterga a carência).

## Out of scope
- Upload de arquivo do atestado médico (fica registrado como período + observação em texto).
- Campo dedicado de fidelidade contratual da PRD-117 (esta PRD só adiciona o necessário para prorrogar a carência via pausa médica, sem assumir o escopo completo daquela PRD).
- Notificação automática por e-mail/WhatsApp ao aprovar/reprovar (fora de escopo — pode virar follow-up).
- Pausar/trancar dependentes de forma independente do titular nesta primeira fase (assumir que a pausa é por `Membership`, já cobrindo titular e dependente individualmente, já que cada um tem sua própria `Membership`).

## Rules and constraints
- Sem chamada real ao Stripe em teste automatizado — mockar `stripe.Subscription.modify`/`pause_collection`.
- `transaction.atomic` em toda decisão administrativa (aprovar/reprovar) e em qualquer escrita que mexa em `Membership` + `MembershipPauseRequest` juntos.
- Preservar 100% da suíte existente sem regressão (em especial `test_plan_change*.py`, `test_calendar.py` pelo novo bloqueio de check-in).
- Migration de schema necessária (novo model + novos campos em `Membership`) — segue a política do projeto: regenerar a baseline única via ciclo destrutivo (`clear_migrations` + `makemigrations`), não migration incremental.

## Risks and edge cases
- Cliente Stripe pausa por atestado, depois tenta trocar de plano durante a pausa — deve continuar bloqueado (pausa não é o mesmo que "fim de carência").
- Dois pedidos de pausa sobrepostos (ex. atestado sobre um trancamento já em andamento) — precisa de validação de sobreposição de datas.
- Aprovar uma pausa médica retroativa (atestado emitido depois do período já ter passado parcialmente) — decisão de produto a confirmar durante a implementação.
- Cota anual de 30 dias "vira o ano" no meio de uma pausa em andamento — definir se conta pelo ano da data de início ou proporcional.
- Migração Asaas → Stripe falha no meio do checkout (cliente abandona a página do Stripe) — precisa manter o plano atual intacto até confirmação real do pagamento (mesmo padrão já usado no cadastro público).

## Plan
_(a detalhar no início da execução de cada fase — esta PRD cobre o desenho completo; a implementação será feita fase a fase, cada uma com Red→Green própria)_

## Test plan
### Tests to author (por fase)
- Fase A: catálogo inclui Stripe quando não há trava; migração Asaas→Stripe cria `RegistrationOrder` correto e redireciona para Checkout; migração Stripe→Asaas cancela assinatura Stripe antes de criar o novo pagamento.
- Fase B: pausa médica cria pedido `pending`; aprovação suspende cobrança (mock Stripe) e prorroga carência; check-in bloqueado durante a janela aprovada; rejeição não altera `Membership`.
- Fase C: trancamento aceito dentro da cota; rejeitado (ou negado automaticamente) quando excede 30 dias/ano; bloqueado quando `is_plan_change_locked` é `True`.
- Fase D: template contém o texto de regras nas telas de cadastro (asserts de conteúdo, como já feito em outros contratos de wizard).

### Execution authorization
Local — mock de Stripe, sem chamada real a gateway.

## Decisões confirmadas pelo usuário
- Trancamento self-service **também exige aprovação administrativa** (mesma fila da pausa médica, mesmo model `MembershipPauseRequest`, campo `kind` diferencia).
- Cota de 30 dias/ano reseta no **aniversário da matrícula** (`Membership.activated_at`), não em ano civil.
- Implementação: **todas as 4 fases em uma entrega só**, sem pausar para revisão entre elas.

## Verificação técnica (Stripe pause_collection)
Confirmado via `docs.stripe.com` (fetch direto): `pause_collection.behavior` aceita `keep_as_draft`, `mark_uncollectible` ou `void`; usado `void` (fatura anulada, sem cobrança) + `resumes_at` (timestamp Unix, retomada automática). O status da subscription permanece `active` durante a pausa — só a cobrança é afetada.

## Implemented
### Fase A — Transição livre entre planos
- `system/services/plan_change.py::build_plan_catalog`: removida a exclusão de `gateway_code="stripe_card"` de ambas as queries (`get_eligible_plans`/`get_eligible_plan_prices`).
- Novo `plan_requires_stripe_checkout(plan)` e campos `gateway_code`/`requires_checkout` em `serialize_plan_with_proration`.
- Novo `create_plan_change_stripe_order(person, membership, new_plan)`: cria `RegistrationOrder(kind=SUBSCRIPTION, is_plan_change=True, plan_price_ref/plan=new_plan, total=new_plan.price)`.
- `system/services/stripe_checkout.py::create_subscription_session_for_plan_change(order, request)`: nova função pública; `_create_subscription_session` migrada de `price` pré-sincronizado (`stripe_price_id`, que não é populado pelos seeds) para `price_data` inline — mesmo padrão já comprovado em `create_subscription_session_for_pre_registration`.
- `system/views/plan_change_views.py::PlanChangeSelectView`: novo branch — plano destino Stripe → cria ordem + Checkout Session, retorna `redirect_url` (Stripe hospedado); migrar **para fora** do Stripe → cancela a assinatura Stripe atual (`cancel_membership(at_period_end=False)`, sem `admin_user`) e reresseta `status=ACTIVE`/`stripe_subscription_id=""` antes de seguir o fluxo normal.
- **2 bugs pré-existentes corrigidos** (mesma família das PRD-127/129/130 — código que só lia `SubscriptionPlan`):
  - `system/views/payment_views.py::PaymentMethodChoiceView`: roteava por `order.plan.payment_method`, sempre caindo em Asaas PIX para ordens `plan_price_ref`. Agora resolve `gateway_code` real (`asaas_pix`/`asaas_card`/`stripe_card`) via novo `_resolve_order_gateway_code`.
  - `system/services/stripe_webhooks.py`: branch `mode == "subscription"` de `checkout.session.completed` nunca verificava `order.is_plan_change` e só lia `order.plan` (`activate_membership_from_session` aborta silenciosamente para `PlanPrice`). Novo `_apply_stripe_plan_change_migration` aplica a troca sobre a `Membership` ativa existente (via `apply_plan_change`) e preenche os campos Stripe (`stripe_subscription_id`, `stripe_customer_id`, `current_period_start/end`) — em vez de criar uma assinatura duplicada.
- `templates/home/dashboard.html`: card do catálogo mostra "Assinatura recorrente — você será redirecionado para o pagamento" quando `requires_checkout`.

### Fase B/C — Pausa de mensalidade
- `system/models/membership.py`: novo `Membership.fidelity_extension_days`; novo model `MembershipPauseRequest` (`kind` medical/self_service, `status` pending/approved/rejected/canceled, período, decisão); `Membership.current_pause`/`is_currently_paused`.
- `system/services/membership_pause.py` (novo): `create_pause_request` (bloqueia sobreposição, `self_service` exige fora de carência + cota de 30 dias/ano por aniversário de matrícula via `_membership_year_window`); `approve_pause_request` (`@transaction.atomic`, `select_for_update`; pausa Stripe via `pause_collection` behavior=`void`+`resumes_at` quando há `stripe_subscription_id`; posterga `current_period_end`; soma `fidelity_extension_days` só para `medical`); `reject_pause_request`/`cancel_pause_request`; `get_self_service_quota_summary`.
- `system/services/class_calendar.py::perform_checkin`/`get_today_classes_for_person`: bloqueiam check-in durante pausa aprovada vigente; template `today_classes_list.html` mostra "Matrícula pausada até DD/MM/AAAA".
- `system/views/membership_pause_views.py` (novo): `MembershipPauseRequestCreateView` (cliente, JSON), `MembershipPauseQuotaView`, `MembershipPauseRequestQueueView`/`DetailView` (fila administrativa, mesmo padrão da PRD-112 — `PortalRoleRequiredMixin` + capacidades `MANAGE_PEOPLE`/`MANAGE_ACADEMY`).
- `templates/membership_pauses/pause_request_list.html`/`pause_request_detail.html` (novos, espelham `access_requests/*`).
- `templates/home/dashboard.html` + `static/system/js/home/dashboard.js`: botão "Pausar mensalidade" + modal (`bindPauseModal`), mesmo padrão fetch/JSON do modal de troca de plano.
- `system/forms/membership_pause_forms.py` (novo): `MembershipPauseRequestForm`, `MembershipPauseDecisionForm`.

### Fase D — Transparência no cadastro
- `templates/login/register.html`: aviso Stripe existente ajustado (trancamento sem atestado só fora da carência) + novo bloco `plan-policy-notice` sempre visível na etapa de plano.
- `templates/dependents/dependent_registration.html`: mesmo bloco de regras na etapa de plano do dependente.
- `static/system/css/auth/register.css`: nova classe `.plan-policy-notice`.

## Evidence
- **Testes automatizados novos**: `system/tests/test_membership_pause.py` (21 testes: cota/sobreposição/carência, aprovação Stripe mock `pause_collection`, bloqueio de check-in, views cliente e fila admin) + `system/tests/test_plan_change_stripe_migration.py` (10 testes: catálogo com Stripe, migração Asaas→Stripe, migração Stripe→Asaas com cancelamento, webhook não duplica `Membership`, roteamento de gateway) — **31 testes novos, todos verdes**.
- `manage.py test` (suíte completa) → **585 testes, OK** (554 pré-existentes + 31 novos), sem regressão.
- `manage.py check` → limpo, antes e depois do reset destrutivo de migração.
- Migração regenerada via ciclo destrutivo (`clear_migrations` + `makemigrations`) — baseline única `0001_initial.py` inclui `MembershipPauseRequest` e `Membership.fidelity_extension_days`.
- **Validação ao vivo no navegador interno**, com os 3 alunos reais recriados (Beatriz/Stripe, Carlos/Asaas cartão, Diana/Asaas PIX — mesmas faixas de antes) após o reset:
  - Catálogo "Trocar plano" do Carlos (Asaas) agora mostra a opção Stripe recorrente com "Assinatura recorrente — você será redirecionado para o pagamento" (print).
  - Confirmado contra a API real do Stripe (test mode): selecionar o plano Stripe cria `RegistrationOrder(kind=subscription, is_plan_change=True, plan_price_ref=9)` e retorna uma URL real de Checkout Stripe (`checkout.stripe.com/c/pay/cs_test_...`) — prova end-to-end de que a correção do `price_data` inline (em vez de `stripe_price_id` pré-sincronizado, que os seeds não populam) funciona.
  - Modal "Pausar mensalidade" testado end-to-end pelo Carlos: solicitação de trancamento (10 dias) criada como `pending`.
  - Fila `/requests/pausas/` (login técnico `admin`): lista a solicitação, aprovação via UI real — "Pausa de mensalidade aprovada."
  - Confirmado no banco: `Membership.current_period_end` postergado de `07/08/2026` para `17/08/2026` (10 dias) e refletido na home ("Vigência 07/07/2026 → 17/08/2026"); `fidelity_extension_days=0` (correto — só `medical` prorroga carência).
  - Ordens de teste da validação Stripe (criadas contra a API real, nunca pagas) removidas do banco local após a validação.

## Cleanup findings
- Nenhum resíduo de código. Artefatos de validação (ordens Stripe de teste não pagas) removidos do banco local.
- Débito conhecido, fora de escopo: os `PlanPrice` com `gateway_code=stripe_card` seedados não têm `stripe_price_id` sincronizado — não é mais um bloqueio (a Fase A passou a usar `price_data` inline, dispensando o Price pré-criado), mas o campo `stripe_price_id` em si permanece sem uso real neste fluxo; avaliar se ainda faz sentido mantê-lo ou se deve virar um follow-up de limpeza.

## Final status
Concluída e validada — Fases A, B, C e D implementadas, testadas (31 testes novos, suíte completa 585 OK) e validadas ao vivo contra Stripe test-mode real e o fluxo completo de aprovação administrativa.
