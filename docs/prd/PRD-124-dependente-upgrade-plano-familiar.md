# PRD-124: Dependente com upgrade para plano familiar

## Summary
Normalizar a etapa financeira do wizard de dependente para separar três decisões: usar plano familiar já ativo, migrar o titular para plano familiar, ou contratar mensalidade própria para o dependente.

Atualização de escopo em 2026-07-05: a decisão não deve aparecer como três cards iniciais. A etapa deve ser simples, baseada em filtros de frequência/período, e os cards de plano devem derivar a condição financeira.

## Demand type
Correção de regra de negócio com impacto em Django, pagamento e UI do modal.

## Current problem
A opção "Usar plano familiar ativo" aparece mesmo quando o titular tem apenas plano individual. O backend só aceita essa opção quando já existe `Membership` familiar ativa; o JavaScript ainda remove planos familiares do catálogo, impedindo o upgrade familiar no momento em que o dependente é adicionado.

Após a primeira implementação, a tela ficou com excesso de decisão explícita: título "Condição financeira", três cards antes dos filtros, e lista de planos exibida antes de o usuário escolher frequência e período de cobrança.

## Goal
Permitir que o titular com plano individual escolha explicitamente um plano familiar elegível durante a adição de dependente, mantendo também a alternativa de mensalidade própria do dependente.

Na interface, transformar essa escolha em seleção natural de plano: primeiro frequência e período, depois opções individuais e familiares elegíveis. A regra continua validada no backend via `financial_mode`/plano selecionado.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-006-padronizar-tela-troca-plano.md`
- `docs/prd/PRD-007-reformular-planos-precificacao-elegibilidade.md`
- `system/constants.py`
- `system/forms/dependent_forms.py`
- `system/views/dependent_views.py`
- `system/services/dependent_registration.py`
- `system/services/membership.py`
- `system/services/plan_change.py`
- `system/services/pre_registration.py`
- `system/services/registration_checkout.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_webhooks.py`
- `system/selectors/plan_eligibility.py`
- `system/models/plan.py`
- `system/models/membership.py`
- `system/urls.py`
- `system/tests/test_dependent_registration.py`
- `system/tests/test_commands.py`
- `templates/dependents/dependent_registration.html`
- `static/system/js/dependents/dependent_registration.js`
- `static/system/css/dependents/dependent_registration.css`

### Adjacent files consulted
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `static/initial_data/seed_system_initial_subscription_plans_stripe.json`
- `system/management/commands/seed_system_initial_subscription_plans_values.py`
- `system/management/commands/seed_system_initial_subscription_plans_stripe.py`
- `system/utils/plan_commercial.py`

### Internet / official documentation
- Django forms validation via Context7: `Form.is_valid()`, `Form.clean()` and `Form.add_error()` keep validation server-side and attach field errors.
- Stripe official docs: Checkout Sessions represent payment/subscription sessions and can be reconciled by internal references/metadata. URL: `https://docs.stripe.com/api/checkout/sessions`

### Context7 / MCPs / tools verified
- Context7 `/django/django` queried for form validation.
- Context7 `/websites/djangoproject_en_5_2` consultado em 2026-07-05 para confirmar validação via `Form.is_valid()`, `cleaned_data` e `add_error()`.
- Browser validation planned in the in-app browser after implementation.

### Limitations found
- Local seed has adult family plans, but no kids/juvenile family plans. This PRD does not invent new commercial prices.
- The existing pre-registration Stripe flow records local payment confirmation and does not update an existing remote Stripe subscription. This PRD preserves that integration boundary and fixes the local wizard/rule.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
O usuário pediu "implemente" após o diagnóstico que definiu os três caminhos financeiros e a necessidade de correção no form/service/JS.

## Execution prompt
### Persona
Agente Django sênior, trabalhando em SDD + TDD, com atenção especial a regra financeira e validação server-side.

### Action
Implementar o modo financeiro explícito no wizard de dependente, com testes e validação visual no navegador interno.

### Context
O titular pode estar em plano individual ativo e adicionar dependente depois do cadastro. Ao adicionar dependente, ele pode:
- usar plano familiar já ativo;
- migrar o próprio titular para plano familiar;
- contratar mensalidade própria para o dependente.

### Constraints
- Sem migração.
- Sem nova precificação inventada.
- Sem tocar `staticfiles/`.
- Sem abrir checkout externo como validação de sucesso.
- Regra de negócio no backend, não no JavaScript.
- Preservar a alteração preexistente em `system/migrations/0001_initial.py`.

### Acceptance criteria
- [x] O form aceita `financial_mode=family_existing` somente se o titular já tiver plano familiar ativo.
- [x] O form aceita `financial_mode=family_upgrade` somente com plano familiar elegível.
- [x] O form aceita `financial_mode=dependent_own` somente com plano individual compatível com o dependente.
- [x] O pagamento confirmado de upgrade familiar cria pedido/mensalidade para o titular, não para o dependente.
- [x] O pagamento confirmado de mensalidade própria continua criando pedido/mensalidade para o dependente.
- [x] O wizard mostra escolhas financeiras como cards claros e filtra planos conforme o modo selecionado.
- [x] O resumo final mostra "Plano familiar do titular" ou "Mensalidade própria" de forma inequívoca.
- [x] Teste focado de dependente passa.
- [x] `manage.py check` passa.
- [x] Browser interno mostra a etapa financeira funcional no modal.
- [x] A etapa 5 não exibe mais o título "Condição financeira" nem três cards iniciais de modo financeiro.
- [x] A lista de planos permanece vazia/instrutiva até o usuário escolher frequência e período de cobrança.
- [x] Após frequência/período, a seleção de card individual preenche `financial_mode=dependent_own`.
- [x] Após frequência/período, a seleção de card família preenche `financial_mode=family_upgrade`.
- [x] Planos "Veterano" não aparecem nem são aceitos para mensalidade própria de dependente sem elegibilidade.

### Expected evidence
- Comandos e resultados reais de teste.
- ORM local confirmando pedidos/mensalidades quando aplicável.
- Snapshot/screenshot ou inspeção do browser interno.

### Output format
Implementação + evidências + limitações.

## Scope
- Adicionar `financial_mode` como contrato server-side.
- Ajustar validação de plano familiar existente, upgrade familiar e mensalidade própria.
- Ajustar snapshot/persistência do pré-cadastro de dependente.
- Ajustar finalização para aplicar upgrade familiar no titular.
- Ajustar UI/JS da etapa "Escolha o plano do dependente".
- Atualizar testes focados.

## Out of scope
- Criar novos preços de planos kids/juvenil família.
- Atualizar assinatura remota já existente no Stripe.
- Refatorar todo o fluxo de troca de plano.
- Alterar schema ou migrations.

## Impacted files
- `system/constants.py`
- `system/forms/dependent_forms.py`
- `system/services/dependent_registration.py`
- `system/services/registration_checkout.py`
- `system/selectors/plan_eligibility.py`
- `system/views/dependent_views.py`
- `templates/dependents/dependent_registration.html`
- `static/system/js/dependents/dependent_registration.js`
- `static/system/css/dependents/dependent_registration.css`
- `system/tests/test_dependent_registration.py`
- `system/tests/test_plan_eligibility.py`

## Risks and edge cases
- Titular com Stripe recorrente pode precisar de rotina futura para sincronizar upgrade remoto de assinatura. Esta entrega corrige o estado local e o checkout de pré-cadastro usado pelo sistema.
- Responsável sem treino próprio não deve receber plano adulto familiar indevido; a validação deve usar elegibilidade familiar e plano selecionado.
- POST adulterado tentando usar plano familiar como mensalidade própria deve falhar.
- POST adulterado tentando usar opção familiar ativa sem `Membership` familiar deve falhar.

## Rules and constraints
- Validação de plano é obrigatória no form.
- `use_family_plan` permanece por compatibilidade, mas deixa de ser o único contrato.
- `financial_mode` é a fonte de decisão financeira.
- O JS apenas filtra a apresentação e preenche campos ocultos.

## Visual hierarchy
- Título: "Plano do dependente".
- Subtítulo: orientação curta para escolher frequência e período.
- Filtros: frequência semanal, período de cobrança e forma de pagamento.
- Estado vazio: mensagem curta enquanto frequência/período não estão definidos.
- Catálogo: cards "Individual" e "Família" elegíveis depois dos filtros mínimos.
- Erros por campo abaixo do grupo correspondente.

## Wireframe
### Região: Etapa financeira
- Título: "Plano do dependente"
- Subtítulo: "Escolha frequência e período para ver as opções disponíveis."
- Filtros de plano:
  - Frequência semanal
  - Período de cobrança
  - Forma de pagamento
- Lista de planos:
  - Estado inicial: "Escolha frequência e período para ver os planos."
  - Card "Individual": mensalidade própria do dependente.
  - Card "Família": upgrade do titular para plano familiar.
  - Card "Plano familiar ativo": apenas quando o titular já tem familiar ativo.

### Região: Rodapé
- Botão primário existente: "Próximo" / "Ir para pagamento"

### Estados da tela
- Sem plano familiar ativo: card "Usar plano familiar ativo" desabilitado.
- Upgrade sem plano elegível: mensagem de vazio no catálogo.
- Plano selecionado: card com borda de seleção e hidden fields sincronizados.
- Erro server-side: mensagem abaixo do campo financeiro.

## State machine
### Financial mode
- `idle`: frequência/período incompletos; nenhum plano exibido.
- `dependent_own`: usuário selecionou card de plano individual; exige plano individual do dependente.
- `family_existing`: usuário selecionou opção de plano familiar ativo; exige familiar ativo e não exige plano novo.
- `family_upgrade`: usuário selecionou card de plano familiar; exige plano familiar elegível e pagamento.

### Submit
- `idle` -> `validating` -> `redirect_checkout` ou `finalize` ou `error`.

## Test plan
### Tests to author
- `family_upgrade` cria pré-cadastro e redireciona para checkout.
- Pós-pagamento de `family_upgrade` cria dependente e ativa plano familiar no titular.
- `dependent_own` rejeita plano familiar.
- `family_existing` rejeita titular sem plano familiar.
- GET do modal não renderiza cards iniciais de modo financeiro e mantém campos ocultos de contrato.
- Mensalidade própria de dependente rejeita plano veterano sem elegibilidade.

### Execution authorization
Testes locais estão autorizados pela solicitação de implementação.

### Execution evidence
- Red proporcional: teste focado de dependente falhou antes do código de produção para `family_upgrade`/adulteração de plano.
- Red da revisão visual: `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration.DependentRegistrationFlowTestCase.test_dependent_plan_step_is_filter_first_without_financial_mode_cards --verbosity 1` falhou porque o template ainda renderizava "Condição financeira".
- Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration.DependentRegistrationFlowTestCase --verbosity 1` -> 19 testes, OK.
- Green: `.\.venv\Scripts\python.exe manage.py test system.tests.test_plan_eligibility --verbosity 1` -> 12 testes, OK.
- Green: `.\.venv\Scripts\python.exe manage.py check` -> sem issues.
- Regressão: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` -> 472 testes, OK.
- Green da revisão visual: `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration.DependentRegistrationFlowTestCase --verbosity 1` -> 21 testes, OK.
- Green da revisão visual: `node --check static\system\js\dependents\dependent_registration.js` -> sem erros.
- Green da revisão visual: `.\.venv\Scripts\python.exe manage.py check` -> sem issues.
- Revalidação após ajuste do estado de erro da etapa 5: `node --check static\system\js\dependents\dependent_registration.js` -> sem erros; `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration.DependentRegistrationFlowTestCase --verbosity 1` -> 21 testes, OK; `.\.venv\Scripts\python.exe manage.py check` -> sem issues.

## Visual validation
- Navegador interno em `http://127.0.0.1:8000/home/`.
- Modal de dependente abriu por iframe `/dependents/add/?modal=1`.
- Fluxo preenchido com dados fictícios até etapa 5.
- Estado `dependent_own`: card selecionado, dica "Selecione a mensalidade própria do dependente.", amostra de planos com título "Individual".
- Estado `family_upgrade`: card selecionado, dica "Selecione o plano familiar que substituirá a mensalidade atual do titular.", 18 cards exibidos com título "Família".
- Estado `family_existing`: card desabilitado para titular sem plano familiar ativo.
- Validação visual desktop e mobile emitida via screenshot no navegador interno; sem sobreposição aparente.
- Console do navegador interno: `[]` para erros/warnings.
- Revisão 2026-07-05 no navegador interno:
  - Modal abriu em `http://127.0.0.1:8000/home/` via iframe `/dependents/add/?modal=1`.
  - Etapa 5 exibiu "Plano do dependente", zero `.plan-card` e zero `[data-financial-mode]` antes dos filtros.
  - Após `2x por semana` + `Mensal`, `afterFreqCards=0` e `cardsAfterFilters=6`.
  - Cards exibidos: `Individual`, `Individual`, `Individual`, `Família`, `Família`, `Família`; `Veterano=false`.
  - Seleção de card Família sincronizou `#id_financial_mode option:checked = family_upgrade`.
  - Seleção de card Individual sincronizou `#id_financial_mode option:checked = dependent_own`.
  - Próximo avançou para "Materiais opcionais" sem navegar para checkout.
  - Console do navegador interno: `[]`.

## ORM validation
Coberta pelos testes Django:
- `test_paid_family_upgrade_finalizes_with_owner_family_membership` confirma pedido pago no titular, plano familiar ativo no titular e nenhum pedido/mensalidade no dependente.
- `test_paid_resume_finalizes_with_paid_plan_even_if_post_is_tampered` confirma que pós-pagamento restaura o plano pago e ignora adulteração de POST.
- `test_family_upgrade_creates_pre_registration_without_person` confirma pré-cadastro sem criar pessoa antes do pagamento e payload de checkout do titular.

## Quality validation
`git diff --check` executado sem erros de whitespace; apenas avisos esperados de conversão LF/CRLF no Windows.

## Evidence
- Testes focados, suíte completa e `manage.py check` passaram.
- Browser interno validou modal, alternância entre modos financeiros, filtro de planos e console limpo.
- `system/migrations/0001_initial.py` aparece no worktree apenas com timestamp alterado previamente; não faz parte desta implementação.

## Implemented
- Novo contrato `DependentFinancialMode` com `dependent_own`, `family_existing` e `family_upgrade`.
- Validação server-side para bloquear plano familiar como mensalidade própria e bloquear plano familiar ativo inexistente.
- Upgrade familiar cria pedido/mensalidade no titular e cancela mensalidades anteriores do titular.
- Pré-cadastro salva `financial_mode` e payload de planos do titular quando o fluxo é upgrade familiar.
- Checkout passou a aceitar `selected_plans_payload` como lista JSON nativa ou string JSON.
- Elegibilidade familiar agora conta quantidade de adultos, corrigindo adulto + adulto.
- Wizard do dependente exibe cards financeiros e filtra catálogo entre "Individual" e "Família".
- Revisão 2026-07-05:
  - Removidos os três cards iniciais de modo financeiro da etapa 5.
  - Etapa renomeada para "Plano do dependente".
  - Lista de planos fica bloqueada por mensagem instrutiva até frequência e período serem selecionados.
  - O card de plano selecionado define `financial_mode` automaticamente.
  - Planos veteranos foram removidos da UI de mensalidade própria e bloqueados no form.
  - O botão Próximo mantém mensagem de erro quando frequência/período ainda não foram escolhidos.

## Cleanup findings
Sem resíduo funcional introduzido no escopo. Dívidas preservadas: atualização remota de assinatura Stripe existente e criação de preços família kids/juvenil, ambas fora do escopo desta PRD.

## Follow-up PRDs
- `PRD-125-sincronizacao-upgrade-familiar-stripe.md`: sincronizar upgrade familiar com assinatura remota Stripe já existente.

## Deviations from plan
Foi necessário corrigir `PlanEligibilityContext` para contar adultos, pois o modelo anterior só tinha booleano `adult_active` e não liberava família adulto + adulto.

## Pending
- Sem pendência bloqueante no escopo implementado.
- Fora do escopo: preço família kids/juvenil inexistente no seed local e sincronização remota de assinatura Stripe existente.

## Final status
Concluída.
