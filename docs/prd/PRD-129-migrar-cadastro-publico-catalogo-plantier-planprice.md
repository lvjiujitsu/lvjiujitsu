# PRD-129: Migrar cadastro público (`register.js`) para o catálogo PlanTier/PlanPrice

## Summary
Corrige uma regressão crítica descoberta durante a validação end-to-end da PRD-128: após o ciclo completo de `clear_migrations` + reseed, o cadastro público (`/register/`, `register.js`/`registration_forms.py`/`auth_views.py`) não exibe **nenhum plano** para um aluno novo (Adulto ou Kids/Juvenil não-veterano), porque a PRD-127 migrou os planos Individual/Família para `PlanTier`/`PlanPrice` e o seed novo não recria mais SKUs precificados em `SubscriptionPlan` para não-veteranos. O cadastro público continuava lendo exclusivamente `SubscriptionPlan` (decisão deliberada da PRD-127 para conter o raio de impacto), e essa decisão deixou de ser sustentável quando o catálogo legado de planos vendáveis ficou vazio.

## Demand type
Correção de regressão crítica (bloqueia o fluxo de maior tráfego do sistema — cadastro de aluno novo), payment-sensitive.

## Current problem
- `SubscriptionPlan` com `code in ("individual", "family")` estão `is_active=False` após o reseed (PRD-127); apenas variantes `loyalty-*` (Veterano) permanecem ativas.
- `system/views/auth_views.py::PortalRegisterView.get_context_data` chama `get_plan_catalog_payload()` sem `include_plan_prices=True`, então o JSON do catálogo enviado ao `register.js` só contém as variantes Veterano.
- Um aluno novo, não elegível a Veterano, vê a mensagem "Nenhum plano disponível para esta pessoa." na Etapa de plano e não consegue prosseguir com o pagamento — cadastro público efetivamente quebrado para o público majoritário (alunos novos).
- Confirmado via navegador interno (Chrome preview): fluxo completo do wizard público até a etapa 6/8 ("Escolha seu plano"), catálogo vazio de planos vendáveis.

## Goal
Migrar o cadastro público para o mesmo catálogo dual-source (`SubscriptionPlan` legado com id prefixado `sp:<pk>` + `PlanPrice` novo com id prefixado `pp:<pk>`) já usado com sucesso pelo wizard de adição de dependente (PRD-127 Fase 4), preservando 100% do comportamento hoje coberto por testes (elegibilidade por audiência, plano família, veterano, autorização especial, multiplicador de pessoas por pedido).

## Context Ledger
### Files read in full
- `system/forms/registration_forms.py` (campo `selected_plan`, `_clean_plan_selection`, `_build_plan_ineligible_message`)
- `system/services/registration_checkout.py` (`resolve_catalog_plan`, `build_catalog_plan_id`, `parse_selected_plan_payload`, `create_registration_order`, `_count_group_members`, `_count_training_persons`, `get_plan_catalog_payload`, `_build_legacy_plan_catalog_payload`, `_build_plan_price_catalog_payload`)
- `system/services/pre_registration.py` (`save_pre_registration_from_form`, `create_or_update_pre_registration` — sem chamadores, código morto —, `finalize_pre_registration`, `normalize_snapshot_for_form`, `build_wizard_form_snapshot`)
- `system/services/financial_transactions.py` (`resolve_checkout_action_for_plan`, `resolve_payment_provider_for_plan`)
- `system/selectors/plan_eligibility.py` (`is_plan_eligible`, `build_eligibility_context_for_registration`, `PlanEligibilityContext`)
- `system/views/auth_views.py` (`PortalRegisterView`, `FinalizeRegistrationView`)
- `static/system/js/auth/register.js` (`renderPlanCards`, `selectPlan`, `syncSelectedPlansPayload`)
- `system/models/plan.py` (`PlanPrice` — confirma que `payment_method`/`gateway_code` existem nativamente, compatíveis com `resolve_checkout_action_for_plan`/`resolve_payment_provider_for_plan` sem adaptação)

### Adjacent files consulted
- `system/services/dependent_registration.py`/`dependent_forms.py` — padrão de referência já validado em produção local (Fase 4 da PRD-127) para a mesma migração de IDs.
- `system/tests/test_pre_registration_service.py`, `system/tests/test_register_wizard_contract.py` — cobertura existente do fluxo público.

### Internet / official documentation
Nenhuma consulta nova — reaproveita padrão Django (`forms.CharField`, `ModelForm` cleaning) já usado nas PRDs 126/127/128.

### Context7 / MCPs / tools verified
N/A — sem biblioteca nova.

### Limitations found
- `create_or_update_pre_registration` (`pre_registration.py`) é código morto (sem nenhum chamador no repositório) — não será migrado nesta PRD; fica registrado como possível limpeza futura (`lv-cleanup-audit`).
- Fluxo de "plano família" via `SubscriptionPlan.is_family_plan` fica, na prática, inatingível para clientes novos porque não há mais nenhuma linha `is_family_plan=True` ativa — o multiplicador por grupo (`_count_group_members`) permanece no código por compatibilidade histórica (não quebra nada), mas nenhum teste depende dele ficar alcançável.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
Usuário confirmou explicitamente (pergunta objetiva com 3 alternativas) a opção "Migrar o wizard público para o catálogo novo", em vez de reverter o seed ou apenas registrar a pendência.

## Execution prompt
### Persona
Agente Django sênior em regra de negócio financeira, atento a não regressão do fluxo de cadastro público (maior volume de tráfego do sistema).

### Action
Migrar `selected_plan` do cadastro público de `IntegerField`/`SubscriptionPlan.pk` para `CharField` aceitando ids prefixados (`sp:<pk>`/`pp:<pk>`), resolvidos via `resolve_catalog_plan` já existente.

### Context
O wizard de dependente já resolve exatamente este problema (`dependent_forms.py::_clean_financial_choice`, `dependent_registration.py::_legacy_selected_plan`) — esta PRD replica o mesmo padrão para `registration_forms.py`/`pre_registration.py`/`registration_checkout.py`/`register.js`.

### Constraints
- Sem migration de schema (nenhum campo novo necessário — `RegistrationOrder.plan_price_ref` já existe da PRD-127).
- Preservar 100% do comportamento hoje coberto por `test_pre_registration_service.py`/`test_register_wizard_contract.py`.
- `PlanPrice` nunca tem `is_family_plan`/`is_loyalty_plan`/`requires_special_authorization` — a elegibilidade para uma seleção `pp:<pk>` usa checagem simplificada (só audiência), sem reusar `is_plan_eligible` (que pressupõe atributos exclusivos de `SubscriptionPlan`).
- Sem chamada real a Asaas/Stripe em teste automatizado.
- Não alterar `create_or_update_pre_registration` (código morto, fora de escopo).

### Acceptance criteria
- [x] `selected_plan` (form público) aceita e resolve ids prefixados `sp:`/`pp:` via `resolve_catalog_plan`.
- [x] `get_plan_catalog_payload(include_plan_prices=True)` usado em `auth_views.py`, catálogo público passa a incluir tiers `PlanTier`/`PlanPrice` ativos.
- [x] `create_registration_order` cria `RegistrationOrder` corretamente para ambos os casos (`plan=`/`plan_price_ref=`), preservando o multiplicador por pessoas do pedido.
- [x] `save_pre_registration_from_form` não tenta atribuir uma string prefixada a `selected_plan_id` (FK inteira) — grava `None` quando a seleção é `PlanPrice`, preservando o snapshot bruto para reconstrução posterior.
- [x] `register.js`: `data-plan-id` deixa de ser convertido via `parseInt`; qualquer teste estático de contrato (`test_register_wizard_contract.py`) que hoje verifique ausência de `parseInt` continua válido, e nenhum novo `parseInt` sobre plano é introduzido.
- [x] Teste manual no navegador interno confirma que um aluno Adulto novo e um Kids/Juvenil novo veem planos vendáveis reais na Etapa "Escolha seu plano" após o reseed completo.
- [x] Suíte completa sem regressão; `manage.py check` sem issues.

### Expected evidence
- Comando e resultado real de teste (Red antes do código de produção quando aplicável, Green depois).
- Validação visual no navegador interno mostrando o catálogo populado para Adulto e Kids/Juvenil.
- Validação Asaas/Stripe real: fora de escopo desta PRD (mesma limitação já registrada na PRD-128 — depende de navegador externo e intervenção humana).

### Output format
Implementação + evidências reais + limitações não validadas.

## Scope
- `system/forms/registration_forms.py`: `selected_plan` vira `CharField`; `_clean_plan_selection` resolve via `resolve_catalog_plan`, com branch simplificado para `PlanPrice` (sem família/veterano/autorização especial).
- `system/services/registration_checkout.py`: `create_registration_order` resolve `plan_id` via `resolve_catalog_plan`, populando `RegistrationOrder.plan` OU `RegistrationOrder.plan_price_ref` conforme o tipo resolvido.
- `system/services/pre_registration.py`: `save_pre_registration_from_form` só atribui `selected_plan_id` quando a seleção resolve para um `SubscriptionPlan` legado (via helper local), evitando `ValueError` ao salvar uma string prefixada num `IntegerField`/FK.
- `system/views/auth_views.py`: `get_plan_catalog_payload(include_plan_prices=True)`.
- `static/system/js/auth/register.js`: remove `parseInt` da seleção de plano (`selectPlan`/click handler de `.plan-card`); bump de versão do asset.
- `templates/login/register.html`: bump do `?v=` do script.
- Testes: estender `system/tests/test_pre_registration_service.py` (fluxo PlanPrice ponta a ponta) e `system/tests/test_register_wizard_contract.py` (se necessário); novo teste dedicado para `create_registration_order`/`_clean_plan_selection` com `PlanPrice`.

## Out of scope
- Reabrir o modelo de "plano família" como SKU (`SubscriptionPlan.is_family_plan`) — permanece como estava, apenas inatingível na prática por falta de dados ativos.
- `create_or_update_pre_registration` (código morto).
- Validação real do Asaas/Stripe sandbox — mesma limitação da PRD-128.
- Qualquer alteração ao wizard de dependente (já migrado na PRD-127).

## Impacted files
`system/forms/registration_forms.py`, `system/services/registration_checkout.py`, `system/services/pre_registration.py`, `system/views/auth_views.py`, `static/system/js/auth/register.js`, `templates/login/register.html`, `templates/login/installment_select.html` (se referenciar a mesma versão de asset), `system/tests/test_pre_registration_service.py`, `system/tests/test_register_wizard_contract.py`.

## Risks and edge cases
- Um `PreRegistration` em rascunho criado ANTES desta mudança, com `selected_plan_id` legado (inteiro), deve continuar sendo lido corretamente — `resolve_catalog_plan` recebe strings prefixadas; snapshots antigos com "15" puro (sem prefixo) não existem em produção local (ambiente de desenvolvimento único, sem dados legados reais a preservar), mas o código de resolução deve degradar sem exceção não tratada.
- `RegistrationOrder.plan` é `on_delete=PROTECT`; ao criar pedido a partir de `PlanPrice`, `plan` deve ficar `None` (não usar um `SubscriptionPlan` arbitrário) e `plan_price_ref` deve apontar para o `PlanPrice` correto.
- Multiplicador de pessoas (`_count_training_persons`/`_count_group_members`) deve continuar sendo aplicado sobre o preço unitário correto (`plan.price` ou `plan_price.price`), sem duplicar ou zerar o total.
- Mensagens de erro de elegibilidade para `PlanPrice` precisam ser claras mesmo sem os atributos de `SubscriptionPlan` (não podem chamar `_build_plan_ineligible_message` cegamente).

## Rules and constraints
- Sem migration de schema.
- Sem chamada real a gateway em teste automatizado.
- Seguir exatamente o padrão já estabelecido em `dependent_forms.py`/`dependent_registration.py` (reaproveitar `resolve_catalog_plan`/`build_catalog_plan_id`, não reinventar).

## Plan
1. `registration_checkout.py::create_registration_order` — reescrever para usar `resolve_catalog_plan` (teste primeiro).
2. `registration_forms.py::_clean_plan_selection` — trocar `IntegerField`→`CharField`, branch `PlanPrice` simplificado (teste primeiro).
3. `pre_registration.py::save_pre_registration_from_form` — corrigir atribuição de `selected_plan_id` (teste primeiro).
4. `auth_views.py` — `include_plan_prices=True`.
5. `register.js` — remover `parseInt` da seleção de plano; bump de versão.
6. Suíte completa + `manage.py check` + validação visual no navegador interno (Adulto novo e Kids/Juvenil novo vendo planos reais).

## Test plan
### Tests to author
- `create_registration_order` com seleção `pp:<pk>` cria `RegistrationOrder` com `plan=None`, `plan_price_ref=<PlanPrice>`, total correto multiplicado por pessoas do pedido.
- `create_registration_order` com seleção `sp:<pk>` (Veterano) continua funcionando sem regressão (não-regressão explícita).
- `_clean_plan_selection`/form: seleção `pp:<pk>` de audiência incompatível (ex. Kids/Juvenil para pessoa adulta) é rejeitada com mensagem clara.
- `save_pre_registration_from_form` com seleção `pp:<pk>` não levanta exceção e persiste `selected_plan_id=None`.
- Fluxo completo (`finalize_pre_registration`) com `PlanPrice`: snapshot → form revalidado → `Person`/`Membership`(`plan_price_ref`) criados corretamente.

### Execution authorization
Autorizada pelo usuário (resposta objetiva escolhendo a migração completa).

### Execution evidence
- `./.venv/Scripts/python.exe manage.py test system.tests.test_registration_public_plan_price --verbosity 2` → 7 testes novos, todos `ok` (form aceita `pp:<pk>` para audiência compatível, rejeita audiência incompatível, rejeita id de catálogo inexistente; `create_registration_order` cria `RegistrationOrder` com `plan_price_ref` e multiplica corretamente por pessoas do pedido; `finalize_pre_registration` com `PlanPrice` cria `Membership.plan_price_id` correto e `RegistrationOrder` com `plan_price_ref`/`plan=None`/`payment_status=PAID`).
- `./.venv/Scripts/python.exe manage.py test system.tests.test_pre_registration_service system.tests.test_register_wizard_contract system.tests.test_plan_commercial --verbosity 2` → 17 testes existentes, todos `ok` (não-regressão confirmada, incluindo o contrato estático de `register.html`/`register.js` com a versão de asset atualizada).
- `./.venv/Scripts/python.exe manage.py test --verbosity 1` → suíte completa, 544 testes, `OK`.
- `./.venv/Scripts/python.exe manage.py check` → `System check identified no issues (0 silenced)`.

## Visual validation
Executado no navegador interno (Chrome preview), após `clear_migrations` + reseed completo:
- Aluno Adulto novo (CPF `529.982.247-25`, nascimento 15/03/1998): fluxo completo do wizard público até a Etapa 6/8 ("Escolha seu plano") mostra o card "Individual — R$ 221,99/Mensal — 2x por semana", seleção funcional (`id_selected_plan` = `pp:1`, `aria-pressed="true"` após clique). Antes da correção: "Nenhum plano disponível para esta pessoa."
- Aluno Kids/Juvenil novo (CPF `153.509.460-56`, nascimento 10/05/2015, turma Kids): card "Individual — R$ 208,31/mês — 2x por semana — Recorrente" (Stripe), seleção funcional (`id_selected_plan` = `pp:19`).
- Regressão adicional encontrada e corrigida durante esta validação: `register.js::onEnterPlan()` tinha o mesmo bug de "filtro de forma de pagamento nunca revalidado" já corrigido nesta sessão em `dependent_registration.js` — corrigido com a mesma lógica defensiva (reset do filtro quando o valor atual não pertence mais ao conjunto de opções válidas do público corrente).
- Confirmado reload físico do servidor de preview necessário (bug conhecido de conteúdo obsoleto do `runserver --noreload`, documentado em memória) para que a versão nova do asset (`?v=49`) fosse servida.

## ORM validation
`Membership.objects.get(person=person).plan_price_id` e `RegistrationOrder.objects.get(person=person).plan_price_ref_id` verificados via teste automatizado (ver Execution evidence) e via `manage.py shell` durante a investigação da regressão original (contagem de `PlanTier`/`PlanPrice`/`SubscriptionPlan` ativos pós-reseed).

## Quality validation
`manage.py check` limpo; suíte completa (544 testes) sem regressão; nenhuma chamada real a Asaas/Stripe em teste automatizado (mocks já existentes em `family_pricing`/`stripe_discounts` não foram tocados por esta PRD).

## Evidence
Ver Execution evidence e Visual validation acima.

## Implemented
- `system/services/registration_checkout.py::create_registration_order` reescrito para resolver `selected_plan` via `resolve_catalog_plan`, populando `RegistrationOrder.plan` (legado) OU `RegistrationOrder.plan_price_ref` (novo), preservando o multiplicador por pessoas do pedido (`_count_group_members`/`_count_training_persons`).
- `system/forms/registration_forms.py`: campo `selected_plan` migrado de `IntegerField` para `CharField`; `_clean_plan_selection` resolve via `resolve_catalog_plan`, com branch simplificado de elegibilidade por audiência para seleções `PlanPrice` (sem família/veterano/autorização especial, que não existem nesse modelo); import de `SubscriptionPlan` removido (não mais usado diretamente no arquivo).
- `system/services/pre_registration.py`: novo helper `_legacy_plan_pk_from_catalog_id` usado em `save_pre_registration_from_form` para só atribuir `selected_plan_id` (FK legada) quando a seleção resolve para um `SubscriptionPlan`; seleções `PlanPrice` gravam `selected_plan_id=None`, preservando a string de catálogo no snapshot bruto para reconstrução em `finalize_pre_registration`.
- `system/views/auth_views.py`: `get_plan_catalog_payload(include_plan_prices=True)` — catálogo público agora inclui `PlanTier`/`PlanPrice` ativos (com IDs prefixados `sp:`/`pp:`), junto com as variantes Veterano legadas (também prefixadas nesse modo, sem colisão de ID).
- `static/system/js/auth/register.js`: removido o único `parseInt` aplicado a `data-plan-id` (agora string opaca, igual ao wizard de dependente); `onEnterPlan()` corrigido para revalidar `planFilter.cycle`/`frequency`/`method` contra o conjunto de opções válidas do público corrente antes de aplicar o valor padrão, corrigindo uma regressão real que travava a forma de pagamento com um valor de uma audiência anterior/inexistente; versão do asset `?v=49`.
- `templates/login/register.html`: bump de versão do script.
- Testes novos: `system/tests/test_registration_public_plan_price.py` (7 testes: form, `create_registration_order`, finalização completa).
- Teste de contrato atualizado: `system/tests/test_register_wizard_contract.py` (versão do asset `register.js`).

## Cleanup findings
- `create_or_update_pre_registration` (pre_registration.py) é código morto — candidato a remoção em auditoria futura, fora desta PRD.
- O modelo de "plano família" via `SubscriptionPlan.is_family_plan` permanece no código (`_count_group_members`, branch em `create_registration_order`) mas é inatingível na prática — nenhuma linha `is_family_plan=True` está ativa no catálogo pós-PRD-127. Não removido nesta PRD (fora de escopo; comportamento preservado por segurança).

## Follow-up PRDs
- Remoção de código morto (`create_or_update_pre_registration`) se confirmado sem uso após esta PRD.
- Avaliar se o branch de "plano família" legado (`is_family_plan`) deve ser removido ou se algum dia terá SKUs ativos novamente.

## Deviations from plan
- Encontrada e corrigida uma regressão adicional não prevista no plano original: `register.js::onEnterPlan()` tinha o mesmo bug de filtro de forma de pagamento "nunca revalidado" que havia sido corrigido em `dependent_registration.js` nesta mesma sessão (PRD-128). Corrigida com a mesma técnica, dentro do escopo desta PRD por ser bloqueante para a mesma validação de "aluno novo vê planos".

## Pending
- Nenhuma. Validação Asaas real executada com sucesso em 2026-07-06 (ver seção abaixo).

## Validação Asaas real (executada em 2026-07-06)
Executada com assistência do usuário via navegador externo (`claude-in-chrome`), conforme registrado como pendência nesta PRD e na PRD-128:

1. Cadastro público preenchido no navegador interno até a Etapa 6 (Aluno "Carlos Teste PIX", CPF 529.982.247-25, plano `pp:1` — Adulto 2x por semana, PIX).
2. Primeira tentativa real bloqueada pelo Asaas: `400 invalid_object` — `SITE_BASE_URL` local (`http://127.0.0.1:8000`) não é HTTPS nem domínio cadastrado em "Minha Conta → Informações" do sandbox Asaas.
3. Usuário subiu um túnel `ngrok` (`https://dealmaker-deserve-afford.ngrok-free.dev` → `localhost:8000`), cadastrou esse domínio como "Site" na conta sandbox Asaas (temporariamente, substituindo `lvjiujitsu-hg.onrender.com` — a ser revertido pelo usuário após o teste) e configurou um webhook apontando para o túnel.
4. Após ajustar `.env` local (`SITE_BASE_URL`, `DJANGO_ALLOWED_HOSTS`, `ASAAS_WEBHOOK_TOKEN`) com confirmação do usuário e reiniciar o servidor, o pagamento PIX real foi criado com sucesso via `create_pre_registration_plan_payment` (`asaas_payment_id=pay_jfokildk7gfohu6a`, `asaas_customer=cus_000008338873`).
5. Pagamento confirmado via endpoint oficial de simulação do sandbox Asaas (`POST /v3/sandbox/payment/{id}/confirm`, documentado em `docs.asaas.com/reference/confirm-payment`) — status mudou para `RECEIVED` com `paymentDate`/`transactionReceiptUrl` reais, sem necessidade de aprovação manual no painel.
6. **O redirect real da Asaas para a `successUrl` funcionou sozinho** (via túnel), sem precisar da simulação manual `/pagamentos/sucesso/?id=<pay_id>` documentada no guia como fallback — confirmando que a limitação documentada (falta de túnel HTTPS + domínio registrado) era exatamente a única barreira.
7. Wizard avançou corretamente para o modo pós-pagamento ("Pagamento confirmado", "Adulto 2x por semana", "Total: R$ 221,99"), materiais pulados, cadastro finalizado.
8. Verificação final no banco: `Person` "Carlos Teste PIX" criado e ativo; `PreRegistration` `finalized`; `Membership` `active` referenciando `plan_price_id=1` (catálogo novo da PRD-127/129) — confirma que o pipeline PIX real → Membership com `PlanPrice` funciona ponta a ponta.
9. Ambiente revertido após o teste: túnel `ngrok` encerrado; `.env` local (`SITE_BASE_URL`, `DJANGO_ALLOWED_HOSTS`) revertido para os valores originais; servidor reiniciado. Usuário reverterá o campo "Site" da conta sandbox Asaas de volta para `lvjiujitsu-hg.onrender.com`.
10. **Achado incidental (não bloqueante)**: `Membership.billed_price` fica `None` para uma assinatura nova sem grupo familiar (só é populado via `recompute_family_discounts_for_person`, nunca chamado no fluxo público solo). Não é um bug visível — o template já usa `billed_price|default:effective_full_price` — mas fica registrado como possível follow-up para popular `billed_price` na ativação de qualquer `Membership` novo, não só quando há desconto família.

## Final status
Concluída e validada integralmente — testes automatizados, navegador interno E validação real do sandbox Asaas (PIX) com o usuário via navegador externo. Nenhuma pendência restante nesta PRD.
