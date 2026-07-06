# PRD-126: Prevenir cobrança Stripe duplicada no mesmo cartão entre titular e dependente

## Summary
Quando um dependente contrata mensalidade própria (`DependentFinancialMode.DEPENDENT_OWN`) pagando com o mesmo cartão de crédito do titular, as duas assinaturas Stripe recorrentes tendem a cobrar no mesmo dia/horário, arriscando recusa da bandeira por operações duplicadas no mesmo cartão. Esta PRD define como o responsável escolhe, no momento do cadastro do dependente, entre fundir a cobrança em uma única assinatura Stripe ou manter duas assinaturas com horário de cobrança escalonado.

## Demand type
Prevenção de risco de pagamento (correção arquitetural preventiva, sem incidente registrado em produção ainda).

## Current problem
- `system/services/dependent_registration.py` cria `RegistrationOrder` e `Membership` **próprios** para o dependente quando `financial_mode = DEPENDENT_OWN`.
- `system/services/stripe_checkout.py::create_subscription_session_for_pre_registration` sempre cria uma **nova Stripe Checkout Session** `mode=subscription` para quem está pagando, sem parametrizar `billing_cycle_anchor`.
- `system/services/stripe_sync.py::ensure_stripe_customer` cria um **Stripe Customer novo por `Person`**, mesmo que titular e dependente informem o mesmo cartão físico no checkout.
- Nenhum model (`Membership`, `MembershipInvoice`, `Person`) guarda identificador de cartão/fingerprint, nem existe verificação de "mesmo cartão" entre pessoas.
- Titular e dependente costumam ser cadastrados na mesma sessão, então os `billing_cycle_anchor` das duas assinaturas Stripe ficam quase idênticos. Nos ciclos seguintes as duas cobranças caem no mesmo dia/horário; se usarem o mesmo cartão real, a bandeira pode recusar uma das duas por parecerem autorizações duplicadas.
- Estado real verificado no banco local: Bruno (pk=8) tem `Membership` ativo (plano família); Lucas (pk=9, dependente) não tem `Membership` próprio hoje — não há colisão nos dados de teste atuais porque o cenário é `family`, não `DEPENDENT_OWN`. O risco é real no caminho de código `DEPENDENT_OWN`, não no dado atual.

## Goal
No cadastro do dependente, quando `financial_mode = DEPENDENT_OWN` e a forma de pagamento for cartão, o responsável escolhe entre três estratégias de cartão:
1. **Novo cartão** (padrão atual, sem mudança de comportamento).
2. **Mesmo cartão — fundir em 1 assinatura**: o valor do plano do dependente é adicionado como item extra na assinatura Stripe já existente do titular (`POST /v1/subscription_items`). Uma única fatura por ciclo, mesmo `billing_cycle_anchor` do titular, sem nova Checkout Session.
3. **Mesmo cartão — manter separado, escalonar horário**: duas assinaturas Stripe continuam existindo, mas a Checkout Session do dependente recebe `subscription_data.billing_cycle_anchor` deslocado algumas horas em relação ao ciclo do titular, evitando a coincidência exata de horário.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-124-dependente-upgrade-plano-familiar.md`
- `docs/prd/PRD-125-sincronizacao-upgrade-familiar-stripe.md`
- `system/models/membership.py`
- `system/services/stripe_sync.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_webhooks.py`

### Adjacent files consulted
- `system/services/dependent_registration.py` (fluxo `DEPENDENT_OWN`, criação de `RegistrationOrder`/`Membership` próprios)
- `system/services/registration_checkout.py`
- `system/services/membership.py` (`activate_membership_from_session`, `activate_membership_from_paid_order`, `record_invoice_from_stripe`, `upsert_membership_from_stripe_subscription`, `mark_membership_canceled`)
- `system/constants.py` (`DependentFinancialMode`)
- `system/views/home_views.py` (`_build_payment_history_items`, `_build_billing_context` — consumidores de `MembershipInvoice`)

### Internet / official documentation
- Stripe: `subscription_data.billing_cycle_anchor` em Checkout Session `mode=subscription` — `https://docs.stripe.com/get-started/use-cases/saas-subscriptions` e `https://docs.stripe.com/billing/quickstart`. Confirma que é possível fixar a data do primeiro ciclo completo ao criar a Checkout Session.
- Stripe: `POST /v1/subscription_items` — `https://docs.stripe.com/api/subscription_items/create` e `https://docs.stripe.com/billing/subscriptions/quantities`. Confirma que é possível adicionar um item/preço a uma assinatura já existente, gerando uma única fatura por ciclo com múltiplos itens.

### Context7 / MCPs / tools verified
- Context7 `/websites/stripe` consultado para `billing_cycle_anchor` em Checkout Session subscription mode e para `subscription_items` (criação e comportamento de fatura única com múltiplos itens). Ambos os mecanismos existem e são suportados pela API atual do Stripe.

### Limitations found
- Ambiente local não tem `STRIPE_SECRET_KEY` ativa para os registros de teste (Bruno/Lucas), então não é possível validar contra o Stripe real nesta PRD; a validação prevista é via mocks/fixtures e ORM local.
- O fluxo atual usa exclusivamente Stripe Checkout Session (hospedada) para criar assinaturas; nunca chama `Subscription`/`SubscriptionItem` diretamente. A estratégia "fundir" introduz o primeiro caminho de cobrança **sem redirecionamento externo** (chamada servidor-a-servidor), o que muda a experiência de confirmação de pagamento para esse caso específico (sem tela de sucesso do Stripe Checkout).
- `MembershipInvoice` é hoje 1-para-1 com `Membership`. Uma fatura Stripe fundida tem múltiplas `lines`, uma por item/preço — a solução adotada (ver Plan) dividide a fatura por linha em vez de mudar o schema de `MembershipInvoice`.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Usuário identificou o risco, pediu simulação para evitar o problema e confirmou explicitamente que **as duas estratégias de "mesmo cartão" devem ficar disponíveis simultaneamente**, cabendo ao responsável escolher qual usar no momento do cadastro do dependente.

## Execution prompt
### Persona
Agente Django sênior atuando em integração de pagamentos Stripe, com atenção a idempotência de webhook e a não regressão do fluxo de checkout existente.

### Action
Implementar a escolha de estratégia de cartão no cadastro de dependente com plano próprio, e os três caminhos de cobrança correspondentes (novo cartão / fundir / escalonar).

### Context
O dependente com `financial_mode = DEPENDENT_OWN` hoje sempre gera uma Stripe Checkout Session nova e independente. O titular precisa ter uma assinatura Stripe recorrente ativa (`stripe_subscription_id` preenchido) para que a opção "fundir" seja oferecida; sem isso, apenas "novo cartão" e "escalonar" fazem sentido (a opção fundir exige uma assinatura existente para receber o item extra).

### Constraints
- Sem alterar o comportamento do caminho "novo cartão" (regressão zero).
- Sem inventar novo preço comercial.
- Regra de negócio no backend; formulário/JS apenas coleta a escolha e exibe estado.
- `system/migrations/0001_initial.py` é a baseline única do projeto — qualquer campo novo em `Membership` é adicionado nela e regenerado localmente via ciclo destrutivo (`clear_migrations` + `makemigrations`), nunca como migration incremental (ver `[[feedback_migrations_policy]]`).
- Webhooks devem continuar idempotentes (`StripeWebhookEvent` já garante isso por `event_id`); a mudança para "múltiplos Memberships por `stripe_subscription_id`" não pode quebrar essa garantia.
- Sem tocar em pagamento real, painel Stripe ou ambiente HG/produção sem autorização explícita separada.

### Acceptance criteria
- [ ] Wizard de dependente (`financial_mode = DEPENDENT_OWN`, forma de pagamento cartão) exibe a escolha "Novo cartão" / "Mesmo cartão — fundir" / "Mesmo cartão — escalonar horário".
- [ ] "Fundir" só é oferecida quando o titular tem `Membership` ativo com `stripe_subscription_id` preenchido.
- [ ] "Fundir": chamada a `POST /v1/subscription_items` na assinatura do titular; nenhuma nova Stripe Checkout Session é criada para o dependente; o dependente recebe `Membership` local ativo referenciando o `stripe_subscription_id` do titular e o `stripe_subscription_item_id` próprio.
- [ ] "Escalonar": Checkout Session do dependente recebe `subscription_data.billing_cycle_anchor` deslocado (parametrizável, ex.: +4h) em relação ao ciclo do titular; duas assinaturas Stripe distintas continuam existindo.
- [ ] Webhook `invoice.paid` sabe dividir uma fatura Stripe com múltiplas `lines` em um `MembershipInvoice` por `Membership` (via `stripe_subscription_item_id`), sem quebrar o caminho de fatura de item único existente.
- [ ] Webhook `customer.subscription.updated`/`customer.subscription.deleted` atualiza **todos** os `Membership` vinculados ao mesmo `stripe_subscription_id`, não apenas um.
- [ ] POST adulterado tentando forçar "fundir" sem o titular ter assinatura Stripe ativa é rejeitado no backend.
- [ ] Testes focados novos e existentes (`test_dependent_registration`, `test_home_dependents_section`) passam.
- [ ] `manage.py check` passa.
- [ ] Suíte completa sem regressão.

### Expected evidence
- Comandos e resultado real de teste (Red antes do código de produção, Green depois).
- ORM local confirmando `Membership`/`MembershipInvoice` divididos corretamente para o caso "fundir".
- Mock/fixture de payload de webhook Stripe (`invoice.paid` multi-linha, `customer.subscription.updated`) exercitando o novo split.
- Sem chamada real ao Stripe (ambiente local sem chave ativa nestes registros) — validação por mocks.

### Output format
Implementação + evidências reais + limitações não validadas.

## Scope
- Novo campo em `Membership`: `stripe_subscription_item_id` (para localizar a linha específica dentro de uma assinatura potencialmente compartilhada).
- Novo enum `DependentCardStrategy` (`new_card`, `same_card_merged`, `same_card_staggered`) em `system/constants.py`.
- `system/services/dependent_registration.py`: aceitar e validar a estratégia de cartão quando `financial_mode = DEPENDENT_OWN` + pagamento cartão.
- `system/services/stripe_checkout.py`: novo caminho "fundir" (chamada direta a `SubscriptionItem.create`, sem Checkout Session) e parametrização de `billing_cycle_anchor` no caminho "escalonar".
- `system/services/stripe_webhooks.py` + `system/services/membership.py`: dividir fatura multi-linha por `Membership`; atualizar todos os `Membership` de um `stripe_subscription_id` compartilhado.
- Formulário/wizard de dependente (`templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js`): nova etapa/seleção de estratégia de cartão.
- Testes focados cobrindo os três caminhos e a rejeição de adulteração.

## Out of scope
- Detecção automática de "mesmo cartão" via fingerprint Stripe (a escolha é sempre explícita do responsável, não inferida).
- Sincronizar retroativamente assinaturas já existentes que já colidem (esta PRD previne novos cadastros; migração de dado histórico é follow-up separado, se necessário).
- Alterar o fluxo Asaas (é exclusivo de cartão recorrente Stripe).
- Implementar sem aprovação explícita deste plano.

## Impacted files
- `system/constants.py`
- `system/models/membership.py`
- `system/migrations/0001_initial.py`
- `system/services/dependent_registration.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_webhooks.py`
- `system/services/membership.py`
- `system/forms/dependent_forms.py`
- `templates/dependents/dependent_registration.html`
- `static/system/js/dependents/dependent_registration.js`
- `system/tests/test_dependent_registration.py`
- `system/tests/test_commands.py` (se afetar seeds/migrations)

## Risks and edge cases
- Titular sem `stripe_subscription_id` (pagou via Asaas, ou não tem plano ativo, ou está com pagamento pendente) tentando "fundir" — deve ser bloqueado no backend, não só escondido na UI.
- Cancelamento do dependente quando "fundido": remover apenas o `subscription_item` do dependente, sem cancelar a assinatura inteira do titular.
- Cancelamento/expiração da assinatura do titular quando há dependente fundido: o dependente perde cobrança ativa junto — precisa de aviso/该tratamento explícito (registrar como pendência se não coberto nesta entrega).
- Reembolso parcial (`amount_refunded`) em fatura multi-linha: o split precisa refletir o reembolso na linha correta, não em toda a fatura.
- Falha ao criar `subscription_item` (ex.: rede, Stripe fora do ar) não deve deixar o dependente em estado "pago" localmente sem cobrança remota correspondente.

## Rules and constraints
- A estratégia de cartão só existe para `financial_mode = DEPENDENT_OWN` + pagamento cartão; `family_existing`/`family_upgrade` não usam este contrato (já compartilham o mesmo `Membership`, sem duplicidade).
- `DependentCardStrategy` é validado no backend; o JS apenas reflete a escolha.
- Nenhuma migration incremental — alteração de schema entra na baseline única conforme `CLAUDE.md` seção 6.

## Plan
1. Adicionar `DependentCardStrategy` em `system/constants.py` e `stripe_subscription_item_id` em `Membership` (regenerar baseline local).
2. Estender `system/forms/dependent_forms.py` e `dependent_registration.py` para aceitar/validar a estratégia, condicionada a `financial_mode`/forma de pagamento/existência de assinatura Stripe do titular.
3. Implementar em `stripe_checkout.py`:
   - `merge_dependent_into_existing_subscription(titular_membership, dependent_plan, dependent_person)` → `SubscriptionItem.create`, sem Checkout Session.
   - Parâmetro opcional `billing_cycle_anchor` em `create_subscription_session_for_pre_registration` para o caminho "escalonar".
4. Atualizar `system/services/membership.py`/`stripe_webhooks.py`:
   - `record_invoice_from_stripe` passa a iterar `invoice["lines"]["data"]`, resolvendo `Membership` por `stripe_subscription_item_id` quando houver mais de uma linha.
   - `upsert_membership_from_stripe_subscription`/`mark_membership_canceled` operam sobre `Membership.objects.filter(stripe_subscription_id=...)` (todas as linhas), não `.get()`.
5. Ajustar wizard (`dependent_registration.html`/`.js`) para exibir a escolha quando aplicável.
6. Escrever testes (Red) antes de cada trecho de produção; implementar o mínimo; rodar suíte focada e completa (Green).
7. Validar no navegador interno o novo passo do wizard (estado padrão, "fundir" habilitado/desabilitado conforme elegibilidade, "escalonar").

## Test plan
### Tests to author
- Wizard bloqueia "fundir" quando titular não tem `stripe_subscription_id`.
- POST adulterado forçando `same_card_merged` sem assinatura Stripe ativa do titular é rejeitado.
- Mock de `SubscriptionItem.create` chamado corretamente para "fundir"; nenhuma Checkout Session criada nesse caminho.
- Mock de Checkout Session recebendo `billing_cycle_anchor` correto para "escalonar".
- Webhook `invoice.paid` com fatura de 2 linhas cria 2 `MembershipInvoice`, um por `Membership`, com valores corretos.
- Webhook `customer.subscription.updated`/`deleted` atualiza ambos os `Membership` de um `stripe_subscription_id` compartilhado.
- Caminho "novo cartão" permanece sem regressão (testes existentes de `DEPENDENT_OWN`).

### Execution authorization
Aprovada explicitamente pelo usuário em 2026-07-06 ("aprovo a mudança de regra de pagamento").

### Execution evidence
- `system/tests/test_membership_shared_subscription.py` (novo, 6 testes): `activate_membership_from_paid_order` grava/omite `stripe_subscription_id`/`stripe_subscription_item_id`; `record_invoice_from_stripe` divide fatura multi-linha por `Membership` via `stripe_subscription_item_id` e preserva o comportamento de fatura única; `upsert_membership_from_stripe_subscription` e `mark_membership_canceled` atualizam todos os `Membership` que compartilham `stripe_subscription_id`.
- `system/tests/test_stripe_checkout_merge.py` (novo, 3 testes): `merge_plan_into_existing_subscription` chama `stripe.SubscriptionItem.create` com os parâmetros corretos e levanta `StripeCheckoutError` sem assinatura do titular ou sem `stripe_price_id` do plano.
- `system/tests/test_dependent_registration.py` (`DependentCardStrategyTestCase`, novo, 6 testes): validação de formulário rejeita `same_card_merged` sem assinatura Stripe ativa do titular e aceita com assinatura ativa; `card_strategy` sempre volta a `new_card` fora do fluxo `dependent_own` + cartão; `create_pre_registration_plan_payment` funde corretamente (mock) e escreve `plan_payment` no snapshot; `create_pre_registration_plan_payment` escalona `billing_cycle_anchor` corretamente a partir do `current_period_end` do titular + 4h; `finalize_dependent_registration` sincroniza `stripe_subscription_id`/`stripe_subscription_item_id` do snapshot para o `Membership` do dependente.
- Comando: `.\.venv\Scripts\python.exe manage.py test system.tests.test_membership_shared_subscription system.tests.test_stripe_checkout_merge system.tests.test_dependent_registration.DependentCardStrategyTestCase --verbosity 2` → 15 testes novos, todos OK.
- Regressão: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` → 489 testes (474 pré-existentes + 15 novos), OK.
- `.\.venv\Scripts\python.exe manage.py check` → sem issues.
- Ciclo destrutivo executado para o campo novo `stripe_subscription_item_id`: `clear_migrations.py` + `makemigrations` + seeds de referência (1 a 18) recriados localmente.

## Visual validation
- Navegador interno: login como titular de teste com `Membership` ativo (`stripe_subscription_id` preenchido), wizard de dependente até a etapa "Plano do dependente", filtro "Cartão" selecionado, card "Individual RECORRENTE" (plano Stripe) selecionado.
- Bloco "Como cobrar o cartão do dependente?" aparece com as 3 opções (Novo cartão / Fundir / Escalonar), todas habilitadas porque o titular tem assinatura Stripe ativa.
- Seleção de "Mesmo cartão do responsável — fundir em 1 cobrança" atualiza corretamente o campo oculto `id_card_strategy` para `same_card_merged`.
- Console do navegador interno sem erros.
- Não validado neste ciclo: submissão real do pagamento (exige `STRIPE_SECRET_KEY` configurada e ambiente Stripe real — fora do escopo local); comportamento do bloco "fundir" desabilitado quando o titular NÃO tem assinatura Stripe ativa (coberto por teste automatizado de formulário, não replicado manualmente no navegador).

## ORM validation
Coberto pelos testes automatizados citados acima (criação/atualização de `Membership`/`MembershipInvoice` via ORM local, sem chamada real ao Stripe).

## Quality validation
`manage.py check` sem issues após todas as mudanças de modelo/serviço/formulário/view/template/JS.

## Evidence
Ver "Execution evidence" e "Visual validation" acima.

## Implemented
- `DependentCardStrategy` (`system/constants.py`): `new_card`, `same_card_merged`, `same_card_staggered`.
- `Membership.stripe_subscription_item_id` (`system/models/membership.py`), migration baseline regenerada.
- `activate_membership_from_paid_order` aceita `stripe_subscription_id`/`stripe_subscription_item_id` opcionais.
- **Correção de lacuna pré-existente** (ampliação de escopo aprovada pelo usuário): `finalize_pre_registration` (`system/services/pre_registration.py`) e `_create_paid_plan_order` (`system/services/dependent_registration.py`) agora sincronizam `stripe_subscription_id`/`stripe_subscription_item_id` do snapshot `plan_payment` para o `Membership` recém-ativado — antes, esse campo nunca era preenchido pelo fluxo de pré-cadastro (só pelo fluxo direto de `RegistrationOrder`, usado por troca de plano).
- `merge_plan_into_existing_subscription` e `billing_cycle_anchor` opcional em `create_subscription_session_for_pre_registration` (`system/services/stripe_checkout.py`).
- `record_invoice_from_stripe` divide fatura multi-linha por `Membership`; `upsert_membership_from_stripe_subscription`, `mark_membership_canceled` e `mark_invoice_failed` atualizam todos os `Membership` compartilhando `stripe_subscription_id` (`system/services/membership.py`).
- `create_pre_registration_plan_payment` (`system/services/registration_checkout.py`) ganha `card_strategy`/`owner`; branch "fundir" chama o merge e retorna URL local de sucesso (sem Checkout Session); branch "escalonar" calcula `billing_cycle_anchor` via `compute_staggered_billing_cycle_anchor` (offset de 4h sobre o próximo ciclo do titular).
- `DependentRegistrationForm.card_strategy` + `_clean_card_strategy` (`system/forms/dependent_forms.py`): valida que "fundir" só é aceito com assinatura Stripe ativa do titular.
- `_build_owner_plan_context` (`system/views/dependent_views.py`) expõe `owner_has_stripe_subscription` para o wizard.
- Wizard (`templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js`, `static/system/css/dependents/dependent_registration.css`): bloco "Como cobrar o cartão do dependente?" com as 3 opções, habilitado apenas quando `financial_mode=dependent_own` + `checkout_action=stripe_card`, desabilitando "fundir" quando o titular não tem assinatura Stripe ativa.

## Cleanup findings
Sem resíduo funcional introduzido no escopo. `stripe_invoice_id` de faturas fundidas usa a chave sintética `f"{invoice_id}::{item_id}"` (documentado no código) para preservar a unicidade do campo sem exigir mudança de schema adicional.

## Follow-up PRDs
- Migrar/corrigir assinaturas já existentes em produção que já colidem no mesmo cartão (fora do escopo — esta entrega previne apenas novos cadastros).
- Sincronizar `Person.stripe_customer_id`/`Membership.stripe_customer_id` a partir do fluxo de pré-cadastro (hoje o Checkout Session de assinatura não passa `customer=` explícito; gap relacionado, não bloqueante para esta entrega).

## Deviations from plan
Escopo ampliado durante a implementação, com aprovação explícita do usuário: foi necessário corrigir a lacuna pré-existente em que `Membership.stripe_subscription_id` nunca era sincronizado a partir do pagamento confirmado via pré-cadastro (`finalize_pre_registration`/`_create_paid_plan_order`) — sem essa correção, a opção "fundir" nunca teria um `stripe_subscription_id` real do titular para usar.

## Pending
- Validação end-to-end com Stripe real (checkout real, webhook real) — não executável neste ambiente local sem `STRIPE_SECRET_KEY` de teste configurada.
- Definição de negócio fechada sobre o offset de 4h usado no caminho "escalonar" (valor pragmático adotado, não confirmado como regra final).
- Sincronização de assinaturas já existentes que já colidem (fora do escopo, ver Follow-up).

## Final status
Concluída (implementação local + testes automatizados + validação visual do wizard). Validação end-to-end com Stripe real pendente de ambiente configurado.
