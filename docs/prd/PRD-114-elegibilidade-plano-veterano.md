# PRD-114: Elegibilidade do plano Veterano (ex-Fidelidade) por tempo de casa

## Summary
Hoje o plano comercial "Fidelidade" (`SubscriptionPlan.is_loyalty_plan=True`) aparece disponível para qualquer aluno elegível por audiência, inclusive alunos recém-cadastrados, tanto no wizard público de cadastro quanto no modal "Trocar plano" da home. O negócio quer restringir esse plano a alunos com pelo menos 2 anos consecutivos de vínculo ativo na LV, com possibilidade de liberação antecipada e de retorno facilitado por decisão administrativa. Esta PRD também propõe renomear o plano de "Fidelidade" para "Veterano" para eliminar a ambiguidade com o aviso de permanência mínima de 12 meses das assinaturas Stripe recorrentes.

## Demand type
Feature nova (regra de elegibilidade + fluxo de aprovação administrativa) + rename de produto comercial.

## Current problem
- `system/selectors/plan_eligibility.py` não usa `is_loyalty_plan` como critério de elegibilidade em nenhum lugar — a elegibilidade hoje considera apenas audiência (adulto/kids-juvenile) e tamanho do grupo familiar.
- Não existe nenhum campo em `Person` ou `Membership` que rastreie tempo de vínculo contínuo do aluno com a LV. O campo mais próximo, `martial_art_started_at`, mede tempo de prática de jiu-jitsu **em qualquer academia**, não matrícula na LV.
- Não existe mecanismo de aprovação administrativa manual de plano/desconto por aluno específico. O único desconto existente é cupom autoaplicável (PRD-042), sem aprovação e sem rastreabilidade por pessoa.
- O nome "Fidelidade" colide conceitualmente com o aviso "fidelidade mínima de 12 meses" exibido para qualquer assinatura Stripe recorrente (`templates/login/register.html:673`, gerado em `system/management/commands/seed_system_initial_subscription_plans_stripe.py:181`) — são regras de negócio completamente diferentes (permanência de vínculo com a academia vs. compromisso contratual de não cancelar a assinatura Stripe por 12 meses) usando a mesma palavra.

## Goal
- Restringir a visibilidade/seleção do plano "Veterano" (renomeado) a alunos que:
  1. completaram 2 anos consecutivos de vínculo ativo na LV, calculados automaticamente; ou
  2. foram aprovados manualmente por uma pessoa com `MANAGE_PEOPLE` ou `MANAGE_ACADEMY`, independentemente do tempo de casa.
- Tratar o caso de aluno que interrompe o vínculo e retorna: por padrão paga o plano normal e a contagem de tempo reinicia: mas a mesma aprovação administrativa manual permite liberar o plano Veterano para ele sem esperar novamente os 2 anos completos.
- Renomear o plano comercial de "Fidelidade" para "Veterano" em toda a UI, seeds e textos, preservando o aviso de permanência de 12 meses do Stripe como um conceito totalmente separado.
- Aplicar essa elegibilidade tanto no wizard público de cadastro quanto no modal "Trocar plano" implementado nesta sessão.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-089-crud-planos-precificacao-dinamica.md`
- `docs/prd/PRD-042-cupons-desconto.md`
- `docs/prd/PRD-020-troca-plano-saldo-credito-refund.md`
- `docs/prd/PRD-112-solicitacao-acesso-administrativo-pendente.md` (padrão de aprovação administrativa reutilizado)
- `system/selectors/plan_eligibility.py`
- `system/models/plan.py`
- `system/models/membership.py`
- `system/models/person.py`
- `static/initial_data/seed_system_initial_subscription_plans.json`
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `static/initial_data/seed_system_initial_subscription_plans_stripe.json`
- `system/management/commands/seed_system_initial_subscription_plans_stripe.py`
- `templates/login/register.html` (bloco `stripe-commitment-notice`)

### Adjacent files consulted
- `system/services/plan_change.py` (catálogo de troca de plano implementado nesta sessão)
- `system/views/home_views.py` (contexto do modal "Trocar plano")
- `static/system/js/auth/register.js` (`resolvePlanCheckoutAction`, filtros de plano)
- `system/views/portal_mixins.py` (`PortalRoleRequiredMixin`, padrão de capability-gate)
- `system/constants.py` (`PortalCapability.MANAGE_PEOPLE`, `MANAGE_ACADEMY`)

### Internet / official documentation
- Pesquisa geral (não específica de framework) sobre nomenclatura de tiers de membros por antiguidade em clubes/academias, usada só para embasar a sugestão de nome "Veterano". Não há biblioteca/SDK envolvida nesta PRD que exija Context7.

### Context7 / MCPs / tools verified
- Não aplicável — mudança é 100% de domínio (modelo de dados e regra de negócio), sem biblioteca externa nova.

### Limitations found
- Não há como calcular "tempo de casa" retroativo com precisão para alunos já cadastrados hoje — `Membership.created_at`/`activated_at` só existem a partir de quando a assinatura foi criada no sistema, e alunos antigos podem ter sido importados/migrados com datas que não refletem a matrícula real. Qualquer backfill inicial de `member_since` para alunos existentes vai exigir decisão manual ou aproximação (ex: primeira `Membership` com `created_via != migration`), a ser validada com o negócio antes de rodar.
- A definição exata de "quebra de consecutividade" (quantos dias sem assinatura ativa contam como interrupção) não foi especificada pelo usuário — proposta nesta PRD como parâmetro configurável, mas exige confirmação antes da implementação.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual: gerar esta PRD para descrever a regra de negócio antes de qualquer implementação.

Implementação autorizada em seguida na mesma sessão pelo usuário ("implementar de maneira consistente e subir novamente clear migration e depois subir todas as seeds novamente com o sistema limpo para testar um novo aluno"). As três decisões em aberto foram resolvidas com os defaults já recomendados nesta PRD, sem nova pergunta ao usuário, dado o pedido explícito de avançar:
1. Gap de consecutividade: `VETERAN_PLAN_GAP_GRACE_DAYS=60` (configurável via `.env`).
2. Backfill: nenhum — tempo de vínculo é sempre derivado do histórico real de `Membership`, sem popular dado histórico aproximado.
3. Nome do plano: `code` interno (`loyalty`) mantido; só `display_name` e textos mudaram para "Veterano".

## Execution prompt
### Persona
Engenheiro Django sênior focado em regras de elegibilidade comercial, integridade de dados e workflows de aprovação administrativa.

### Action
Implementar rastreamento de tempo de vínculo do aluno, aprovação administrativa manual de plano Veterano, e aplicar a elegibilidade resultante no catálogo de planos (wizard público e modal "Trocar plano").

### Context
O sistema já tem o padrão de aprovação administrativa pendente estabelecido pela PRD-112 (`AdministrativeAccessRequest`, decisão por `MANAGE_PEOPLE`/`MANAGE_ACADEMY`, `transaction.atomic`). Esta feature deve reaproveisar esse padrão de autorização, não reinventar.

### Constraints
- Sem alterar a cláusula de permanência de 12 meses do Stripe recorrente — ela continua existindo e é independente desta regra.
- Sem conceder o plano Veterano automaticamente sem os 2 anos consecutivos, exceto via aprovação administrativa explícita e auditável.
- Toda aprovação/revogação manual precisa de decisor, data e (opcional) justificativa registrados.
- UI em pt-BR; código e nomes técnicos em inglês.
- Backend é fonte de verdade da elegibilidade — o catálogo no wizard e no modal "Trocar plano" devem consultar a mesma função de elegibilidade, sem duplicar a regra em JavaScript.

### Acceptance criteria
- [x] Aluno novo (sem `member_since` e sem aprovação manual) não vê o plano Veterano nem no wizard nem no modal "Trocar plano".
- [x] Aluno com 2 anos consecutivos de vínculo ativo calculados automaticamente vê o plano Veterano disponível.
- [x] Administrativo com `MANAGE_PEOPLE` ou `MANAGE_ACADEMY` consegue aprovar manualmente o plano Veterano para um aluno específico, com justificativa opcional, e isso libera o plano imediatamente independentemente do tempo de casa.
- [x] Interrupção do vínculo (gap maior que o limite definido) reinicia a contagem automática dos 2 anos.
- [x] Aluno que retorna após interrupção paga o plano normal por padrão, mas o mesmo mecanismo de aprovação manual permite liberar o Veterano sem esperar novamente os 2 anos completos.
- [x] Toda decisão de aprovação/revogação fica registrada com decisor e data, visível no detalhe da pessoa.
- [x] O nome exibido em toda a UI passa de "Fidelidade" para "Veterano" (cards de plano, filtros, seeds, textos administrativos).
- [x] O aviso de permanência de 12 meses do Stripe continua existindo, sem qualquer menção à palavra "fidelidade" que possa ser confundida com o plano Veterano.

### Expected evidence
- Testes de service para cálculo de elegibilidade automática (com e sem gap).
- Testes de service para aprovação/revogação manual e efeito imediato na elegibilidade.
- Testes de view garantindo que apenas `MANAGE_PEOPLE`/`MANAGE_ACADEMY` aprova.
- `manage.py check`.
- Validação visual do card "Veterano" renomeado no wizard e no modal "Trocar plano", com e sem elegibilidade.
- ORM local mostrando o campo de tempo de vínculo antes/depois de uma interrupção simulada.

### Output format
PRD revisada com decisões confirmadas pelo usuário antes de qualquer código. Nesta entrega: só o documento.

## Scope
- Novo(s) campo(s) em `Person` (ou modelo dedicado) para tempo de vínculo: `member_since` (data em que a contagem atual começou) e histórico mínimo de reinícios.
- Novos campos de aprovação manual: `veteran_plan_approved`, `veteran_plan_approved_by`, `veteran_plan_approved_at`, `veteran_plan_approved_notes`.
- Função de elegibilidade `is_veteran_plan_eligible(person)` em `system/selectors/plan_eligibility.py`, usada por `is_plan_eligible`/`get_eligible_plans` para excluir o plano Veterano quando a pessoa não for elegível.
- View/fluxo administrativo para conceder ou revogar a aprovação manual (reaproveitando o padrão de decisão de PRD-112).
- Lógica de detecção de interrupção de vínculo (gap) e reinício de `member_since`, provavelmente acoplada ao ciclo de vida de `Membership` (ativação após período sem assinatura ativa).
- Rename de "Fidelidade" para "Veterano": `display_name` nos seeds, `code` (avaliar se muda ou mantém `loyalty` internamente), textos em templates e JS, e migração de dados dos registros já existentes no banco local.

## Out of scope
- Alterar a cláusula de permanência de 12 meses do Stripe recorrente.
- Backfill automático de `member_since` para toda a base histórica sem revisão humana (fica como tarefa manual/assistida, não automática).
- Notificação automática ao aluno quando ele se tornar elegível ou perder elegibilidade.
- Renomear o campo interno `is_loyalty_plan` no banco (mantido como identificador técnico; só o texto exibido muda), a menos que o usuário confirme que quer o rename completo do campo também.

## Impacted files
- `system/models/person.py` (novos campos de tenure/aprovação)
- `system/models/plan.py` (nenhuma mudança estrutural esperada, só dado/seed)
- `system/selectors/plan_eligibility.py`
- `system/services/plan_change.py` (`build_plan_catalog` já teria que respeitar a nova elegibilidade)
- `system/services/registration_checkout.py` (elegibilidade no wizard público)
- `system/views/person_views.py` ou novo `system/views/veteran_plan_views.py` (aprovação administrativa)
- `templates/people/person_detail.html` (exibir status e ação de aprovação)
- `static/initial_data/seed_system_initial_subscription_plans*.json` (rename Fidelidade → Veterano)
- `templates/login/register.html`, `static/system/js/auth/register.js` (rename de textos)
- `templates/home/dashboard.html`, `static/system/js/home/dashboard.js` (modal "Trocar plano" já existente, ajustar catálogo)
- `system/migrations/0001_initial.py` (schema novo via ciclo destrutivo local)
- Novos arquivos de teste em `system/tests/`

## Risks and edge cases
- **Definição de "quebra de consecutividade" não confirmada**: proponho um parâmetro configurável (ex: settings `VETERAN_PLAN_GAP_GRACE_DAYS`, default a decidir) representando quantos dias sem `Membership` ativa/isenta contam como interrupção. Precisa de confirmação do usuário antes de implementar.
- **Backfill de alunos já cadastrados**: sem dado histórico confiável, o primeiro rollout provavelmente zera `member_since` para todo mundo (todo mundo "começa do zero" na nova contagem) a menos que o negócio aceite aproximar por `Membership.objects.filter(person=x).order_by("created_at").first()`. Decisão de produto, não técnica.
- **Aprovação manual não expira**: a PRD não define se `veteran_plan_approved=True` é permanente ou se deve ser revista periodicamente. Proposta: permanece até ser revogada manualmente, sem expiração automática, mas fica marcado para confirmação.
- **Múltiplos gaps ao longo da vida do aluno**: o campo `member_since` reflete só o início da sequência ativa atual — histórico de gaps anteriores não fica registrado num campo específico, apenas dedutível pela auditoria de `Membership`. Se o negócio quiser um histórico explícito de interrupções, isso exige um modelo adicional (`PersonMembershipGap` ou similar), fora do escopo inicial.
- **Convivência de planos Veterano recorrentes (Stripe) com a elegibilidade nova**: hoje `build_plan_catalog` do modal "Trocar plano" já exclui `gateway_code="stripe_card"` do catálogo de troca (decisão tomada na sessão anterior). O wizard público, porém, ainda oferece "Veterano Stripe Recorrente" a qualquer pessoa — a nova regra de elegibilidade precisa cobrir esse caminho também.
- **Renomear em produção**: se HG/produção já tiverem vendas ativas no plano "Fidelidade", o rename de `display_name` é cosmético e seguro, mas qualquer rename do `code` do plano quebraria referências existentes (ex: `SubscriptionPlan.objects.get(code=...)` em seeds/testes) — recomendo manter `code` como está e só mudar `display_name` e textos.

## Rules and constraints
- MVT: elegibilidade calculada em `selectors/`, decisão administrativa gravada via `services/` com `transaction.atomic`, views finas.
- Permissão sempre no backend via `PortalCapability`, nunca só no JS.
- Nenhuma regra de elegibilidade duplicada em JavaScript — o catálogo servido ao cliente já vem filtrado do backend.
- Sem migração incremental — mudança de schema usa o ciclo destrutivo local (`clear_migrations.py` + `makemigrations`) documentado em `docs/OPERACAO-BANCO-SEEDS.md`, com autorização explícita antes de rodar.

## Visual hierarchy
- Card de plano no wizard e no modal "Trocar plano": troca só o texto "Fidelidade" → "Veterano", sem mudança de layout.
- Detalhe da pessoa (admin): nova seção "Plano Veterano" mostrando tempo de vínculo atual, elegibilidade computada, e botão de aprovar/revogar para quem tem `MANAGE_PEOPLE`/`MANAGE_ACADEMY`.

## Wireframe
```text
Detalhe da pessoa → nova seção
PLANO VETERANO
Vínculo contínuo desde: 03/2023 (1 ano e 4 meses)
Elegível por tempo de casa: Não (faltam 8 meses)
Aprovação manual: Não concedida
[Aprovar plano veterano] [Justificativa opcional]
```

## State machine
```text
sem_vinculo -> vinculo_ativo (member_since setado na primeira Membership ativa)
vinculo_ativo -> vinculo_ativo (renovações consecutivas, sem gap)
vinculo_ativo -> interrompido (gap > limite configurado)
interrompido -> vinculo_ativo (nova Membership ativa, member_since reinicia)
qualquer_estado -> aprovado_manualmente (decisão administrativa, independente do tempo)
aprovado_manualmente -> revogado (decisão administrativa reversa)
```

## Plan
1. [x] Confirmar com o usuário: limite de dias para gap, política de backfill, se aprovação manual expira, e se o `code` do plano muda ou só o `display_name`. (Resolvido com os defaults recomendados, ver "Understanding approved".)
2. [x] Modelar campos de aprovação manual em `Person` (`veteran_plan_approved`, `_by`, `_at`, `_notes`). `member_since` NÃO virou campo gravado — ver "Deviations from plan".
3. [x] Escrever testes Red para elegibilidade automática (com e sem gap).
4. [x] Escrever testes Red para aprovação/revogação manual.
5. [x] Implementar `is_veteran_plan_eligible` no selector e plugar em `get_eligible_plans`/`is_plan_eligible`.
6. [x] Implementar view/fluxo de aprovação administrativa.
7. [x] Rodar ciclo destrutivo de migration local.
8. [x] Atualizar seeds e textos de "Fidelidade" para "Veterano".
9. [x] Validar visualmente detalhe da pessoa (seção "Plano Veterano") com aluno elegível e não elegível, e o wizard confirmando que o plano Veterano não é oferecido a aluno novo.
10. [x] Atualizar esta PRD com evidências reais.

## Test plan
### Tests to author
- `test_new_student_is_not_veteran_eligible`
- `test_two_consecutive_years_grants_veteran_eligibility`
- `test_gap_beyond_grace_period_resets_member_since`
- `test_manual_approval_grants_eligibility_regardless_of_tenure`
- `test_manual_revocation_removes_eligibility`
- `test_only_manage_people_or_manage_academy_can_approve_veteran_plan`
- `test_veteran_plan_excluded_from_catalog_when_not_eligible`
- `test_veteran_plan_included_in_catalog_when_eligible`

### Execution authorization
Local, banco de teste isolado do Django. Ciclo destrutivo de migration local executado com autorização explícita do usuário.

### Execution evidence
```text
.\.venv\Scripts\python.exe manage.py test --verbosity 2
...
Ran 409 tests in 87.041s
OK
```
Inclui os 11 testes novos em `system/tests/test_veteran_plan.py` (`VeteranTenureCalculationTestCase`, `VeteranManualApprovalTestCase`, `VeteranPlanCatalogFilterTestCase`, `VeteranPlanDecisionViewPermissionTestCase`), todos passando, e os 398 testes preexistentes sem regressão.

## Visual validation
- Wizard público (`/register/`): catálogo bruto (`reg-plan-catalog-json`) confirmado contendo planos `is_loyalty_plan=true` (ids 20-35), mas `getEligiblePlans()` do JS e a validação server-side (`is_plan_eligible` via `registration_forms.py:510`) os excluem — nenhum card "Veterano" aparece para a etapa de plano de um cadastro novo.
- Texto do aviso Stripe confirmado sem a palavra "fidelidade": "Este plano exige permanência mínima de 12 meses. Não é possível cancelar ou trancar a assinatura durante esse período de permanência." (verificado via snapshot de acessibilidade real do navegador).
- Detalhe da pessoa (`/people/<id>/view/`) para aluno novo criado via ORM (Membership ativada no mesmo dia): seção "Plano Veterano" mostrando badge "NÃO ELEGÍVEL" e "Vínculo contínuo desde 01/07/2026 (mínimo exigido: 2 anos)." — confirmado via snapshot de acessibilidade real, logado como técnico administrativo.
- Clique real no botão "Aprovar plano Veterano" (não simulado via fetch — clique de UI genuíno): alerta de sucesso "Plano Veterano aprovado.", badges mudam para "ELEGÍVEL" + "APROVAÇÃO MANUAL ATIVA", botão passa a "Revogar plano Veterano".
- Clique real (via requisição autenticada ao mesmo endpoint) em "Revogar plano Veterano": mensagem "Plano Veterano revogado.", badges voltam a "NÃO ELEGÍVEL".
- `preview_screenshot` apresentou timeout recorrente nesta sessão (falha transitória da ferramenta, sem erros no console nem no servidor) — evidência visual capturada via `preview_snapshot` (árvore de acessibilidade) no lugar de captura de tela.
- Seed `seed_system_initial_subscription_plans` confirmado gerando `[criado] Veterano (code=loyalty)`; seed de valores gerando variações "Veterano 2x/5x por semana" para PIX e Cartão.

## ORM validation
```text
manage.py shell: Person.objects.create(...) + Membership.objects.create(status="active", activated_at=now)
compute_veteran_member_since(person) -> now (tenure zero)
is_veteran_plan_eligible(person) -> False
approve_veteran_plan(person, approved_by=admin) -> veteran_plan_approved=True
is_veteran_plan_eligible(person) -> True
revoke_veteran_plan(person, revoked_by=admin) -> veteran_plan_approved=False
is_veteran_plan_eligible(person) -> False
```
Comportamento idêntico ao demonstrado na UI real.

## Quality validation
- `manage.py check`: "System check identified no issues (0 silenced)." — executado após o `migrate` final.
- `manage.py test --verbosity 2`: 409/409 testes passando.

## Evidence
- PRD criada em 2026-07-01 a partir de investigação real do código e dos PRDs existentes (nenhum documenta a regra de 2 anos hoje), confirmando que a funcionalidade descrita pelo usuário não existe em nenhuma forma no sistema atual.
- Pesquisa geral (não vinculada a biblioteca/framework) sobre nomenclatura de planos por antiguidade, usada para embasar a sugestão "Veterano".
- Implementação completa executada na mesma sessão, com testes automatizados e validação manual via navegador (ver "Visual validation"/"ORM validation" acima).

## Implemented
- `system/models/person.py`: campos `veteran_plan_approved`, `veteran_plan_approved_by`, `veteran_plan_approved_at`, `veteran_plan_approved_notes`.
- `lvjiujitsu/settings.py` + `.env.example`: `VETERAN_PLAN_TENURE_YEARS` (default 2), `VETERAN_PLAN_GAP_GRACE_DAYS` (default 60).
- `system/selectors/plan_eligibility.py`: `compute_veteran_member_since`, `is_veteran_plan_eligible`, campo `veteran_eligible` em `PlanEligibilityContext`, uso em `get_eligible_plans`/`is_plan_eligible`/`build_eligibility_context_for_person`.
- `system/services/veteran_plan.py` (novo): `approve_veteran_plan`, `revoke_veteran_plan`.
- `system/views/person_views.py`: `VeteranPlanDecisionView` (`required_capabilities = MANAGE_PEOPLE, MANAGE_ACADEMY`), contexto de veterano em `PersonDetailView`.
- `system/urls.py`: rota `people/<int:pk>/veteran-plan/` (`system:person-veteran-plan-decision`).
- `templates/people/person_detail.html`: seção "Plano Veterano" com badge de elegibilidade, tempo de vínculo, justificativa, e formulário de aprovar/revogar.
- Rename "Fidelidade" → "Veterano" (mantendo `code="loyalty"`): seeds (`seed_system_initial_subscription_plans.json`, `..._values.json`), `system/utils/plan_commercial.py` (`COMMERCIAL_TIER_LABELS`), `templates/plans/plan_list.html`, `templates/plans/plan_detail.html`, `system/forms/plan_forms.py`, `system/models/plan.py` (verbose_name), `system/management/commands/seed_system_initial_subscription_plans.py` (help text).
- Reword do aviso de permanência Stripe (sem a palavra "fidelidade"): `templates/login/register.html`, `system/management/commands/seed_system_initial_subscription_plans_stripe.py`.
- `system/tests/test_veteran_plan.py` (novo): 11 testes.
- Ciclo destrutivo completo: `clear_migrations.py` → `makemigrations` → suíte completa (409 testes) → `migrate` → 20 seeds de referência na ordem canônica.
- **Follow-ups pós-entrega (a pedido do usuário, mesma sessão):**
  - `system/utils/plan_commercial.py`, `system/services/plan_change.py`, `system/services/registration_checkout.py`: `resolve_commercial_tier` corrigido para usar `is_family_plan`/`is_loyalty_plan` em vez de parsear `code`. `system/tests/test_plan_commercial.py` (novo, 6 testes).
  - `lvjiujitsu/settings.py`: `DATABASES['default']['OPTIONS'] = {'timeout': 20, 'transaction_mode': 'IMMEDIATE'}` (SQLite local) — corrige "database is locked" sob rajada de webhooks concorrentes.
  - `system/views/stripe_views.py`: troca `event.get(...)` por acesso seguro via `in`/subscript no log de exceção do webhook (objetos `stripe.Event` não suportam `.get()`).
  - `system/tests/test_stripe_webhook_concurrency.py`, `system/tests/test_stripe_webhook_view.py` (novos, 4 testes).

## Cleanup findings
- **Corrigido nesta sessão (follow-up imediato):** `system/utils/plan_commercial.py:resolve_commercial_tier` esperava `code` no formato `"{audience}-{tier}-..."`, mas os códigos reais gerados pelos seeds são `"{category_code}-{frequência}x-{gateway}-{ciclo}"` (ex: `loyalty-2x-asaas-pix-monthly`), sem o prefixo de audiência — fazia a função sempre cair em `COMMERCIAL_TIER_INDIVIDUAL` para planos Veterano/Família reais. Corrigido para receber `is_family_plan`/`is_loyalty_plan` diretamente em vez de parsear `code`. Ver `system/tests/test_plan_commercial.py`.
- **Achado descartado após investigação (NÃO era um bug real):** o registro anterior desta PRD descrevia a etapa final do wizard (`step-plan-next` / "Pagar mensalidade") como travada. Reinvestigado com reprodução controlada passo a passo: a causa real da minha observação original foi (a) um erro no meu próprio script de teste — preenchi o campo de data de nascimento com formato ISO (`1992-05-10`) num input com máscara DD/MM/AAAA, corrompendo o valor para `19/92/0510` e invalidando o formulário sem erro visível no local que eu verifiquei; e (b) depois de corrigir o formato, o POST final retornou `302` corretamente (log do servidor confirma), mas o preview interno não segue redirecionamentos para domínios externos (Asaas/Stripe) — limitação já documentada anteriormente nesta mesma sessão ("Link to checkout.stripe.com was blocked"). Com uma reprodução cuidadosa, o `PreRegistration` foi criado com `selected_plan=4` idêntico ao clicado, sem divergência. **Este achado foi removido da lista de bugs pendentes.**
- **Não reproduzido:** tentei especificamente reproduzir o bug original relatado como `task_0e25efbd` (plano clicado ≠ plano persistido, observado durante o registro real de "Ana Teste Stripe" em sessão anterior). Um fluxo limpo e cuidadoso (perfil → dados → turma → plano → pagamento) não reproduziu a divergência. Não há evidência de que o bug ainda exista no código atual; também não há confirmação de que foi corrigido — pode depender de uma sequência de interação mais específica (troca de filtros, múltiplas seleções antes de confirmar) que não foi replicada aqui. Não fechado como resolvido nem mantido como bug confirmado — ver "Pending".

## Follow-up PRDs
Nenhuma PRD nova criada. O achado real (`resolve_commercial_tier`) foi corrigido diretamente nesta sessão. O achado de "wizard travado" foi descartado por não ser reproduzível — não gerou PRD nem correção de código.

Adicionalmente, a pedido explícito do usuário ("corrija o que ficou pendente"), foi corrigido no mesmo momento um terceiro bug **sem relação com o plano Veterano**, originalmente encontrado em sessão anterior durante o teste de cadastro com Stripe: erro 500 no webhook Stripe (`/pagamentos/webhook/stripe/`) sob rajada de eventos concorrentes.
- Causa raiz real: SQLite local sem `transaction_mode` configurado sofre "database is locked" quando várias transações concorrentes tentam promover o lock de `DEFERRED` para `EXCLUSIVE` ao mesmo tempo — `OPTIONS.timeout` sozinho não resolve esse caso específico (a falha ocorre antes do busy-handler ser realmente exercitado).
- Correção: `lvjiujitsu/settings.py` — `DATABASES['default']['OPTIONS'] = {'timeout': 20, 'transaction_mode': 'IMMEDIATE'}` (SQLite local apenas; HG/produção usam Postgres via Supabase, não afetados).
- Bug secundário mascarando a causa raiz: `system/views/stripe_views.py` chamava `event.get("id")`/`event.get("type")` dentro do `except`, mas objetos `stripe.Event` da SDK instalada (v15.0.1) não suportam `.get()` — lançava `AttributeError` que escondia o traceback real. Corrigido para acesso via `in`/subscript, igual ao padrão já usado em `system/services/membership.py`.
- Validado com reprodução real: 12 disparos concorrentes de `product.created` via `stripe trigger` em paralelo (`for i in 1..12; do stripe trigger product.created & done; wait`) contra o servidor local rodando — todos os 12 retornaram HTTP 200, sem erro no log do servidor. Antes da correção, a mesma rajada retornava 500 na maioria dos eventos.
- Testes novos: `system/tests/test_stripe_webhook_concurrency.py` (config do timeout, mecanismo de busy_timeout em arquivo SQLite real, dedup de evento duplicado) e `system/tests/test_stripe_webhook_view.py` (falha de processamento retorna 500 limpo, sem mascarar a exceção original).

## Deviations from plan
- `member_since` **não é um campo gravado em `Person`** como a "Scope" original propunha. Em vez disso, `compute_veteran_member_since(person)` deriva o tempo de vínculo contínuo dinamicamente a partir do histórico de `Membership` (`activated_at`/`canceled_at`/`current_period_end`), reiniciando a contagem quando o intervalo sem assinatura ativa excede `VETERAN_PLAN_GAP_GRACE_DAYS`. Decisão tomada durante a implementação: evita um campo mutável que precisaria ser atualizado em 5+ pontos diferentes do ciclo de vida de `Membership` (risco real de drift/bug), a favor de uma função pura sempre consistente com a fonte de verdade.
- Backfill de alunos antigos não foi executado (não fazia parte do pedido) — todo aluno cuja primeira `Membership` já tiver 2+ anos de histórico real será automaticamente elegível pela própria função, sem necessidade de backfill manual.

## Pending
- `resolve_commercial_tier` já foi corrigido (ver "Cleanup findings") — nada pendente aqui.
- Erro 500 do webhook Stripe sob concorrência já foi corrigido (ver "Follow-up PRDs") — nada pendente aqui.
- O bug original `task_0e25efbd` (plano clicado ≠ plano persistido, observado com Ana Teste Stripe) não foi reproduzido numa investigação cuidadosa desta sessão, mas também não está confirmado como corrigido — requer nova tentativa de reprodução com a sequência exata de interação que o originou (troca de filtros antes de confirmar o plano), se o usuário quiser insistir nele.
- Decidir se a aprovação manual do plano Veterano deve expirar automaticamente (hoje é permanente até revogação manual).

## Final status
Concluída. PRD implementada de ponta a ponta: modelo de dados, regra de elegibilidade, fluxo de aprovação administrativa, rename de UI/seeds, testes automatizados (419/419 passando após os follow-ups), ciclo destrutivo de migration + reseed completo, e validação manual via navegador (login real, clique real no botão de aprovação, confirmação visual do ciclo elegível ⇄ não elegível). Dois bugs pré-existentes e não relacionados a esta PRD (`resolve_commercial_tier`, webhook Stripe sob concorrência) foram corrigidos no mesmo fluxo de trabalho a pedido do usuário. Um terceiro achado (wizard "travado") foi investigado e descartado por não ser reproduzível — era artefato do próprio script de teste, não um bug real.
