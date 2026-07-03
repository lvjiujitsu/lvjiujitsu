# PRD-118: Adicionar dependente pós-matrícula

## Summary
Permitir que uma pessoa já autenticada no portal, seja aluno titular ou responsável, adicione um dependente depois da matrícula inicial. O fluxo deve partir da home, usar um wizard autenticado próprio, coletar os dados completos do dependente, resolver turma, plano, pagamento e materiais, e só criar `Person`, `PortalAccount`, `PersonRelationship`, matrícula e mensalidade após a finalização válida.

## Demand type
Nova funcionalidade de produto com impacto em UI autenticada, Django MVT, persistência, pagamento Asaas/Stripe e validação visual.

## Current problem
- O cadastro público (`/register/`) permite dependentes apenas durante a matrícula inicial.
- `HomeView` só popula `context["dependents"]` quando `has_dependents(person)` já é verdadeiro.
- `templates/home/dashboard.html` só renderiza a seção "Meus dependentes" dentro de `{% if dependents %}`.
- `system/tests/test_home_dependents_section.py` hoje codifica que uma pessoa sem dependentes não vê a seção.
- `system/urls.py` não possui rota autenticada para adicionar dependente depois da matrícula.
- Usar `/register/` como atalho seria incorreto: é um fluxo público, cria um cadastro completo e não vincula o novo aluno ao responsável autenticado.
- `RegistrationOrder` ainda exige `Person`, então o pagamento de um dependente ainda inexistente precisa seguir a lógica de pré-cadastro antes de pessoa, como PRD-040.

## Goal
Um aluno ou responsável autenticado consegue iniciar "Adicionar dependente" a partir da home, concluir um wizard padronizado e terminar com o dependente vinculado corretamente, sem criar dados parciais nem burlar pagamento, plano, turma ou vínculo familiar.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/README.md`
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`
- `docs/prd/PRD-105-secao-dependentes-home-responsavel.md`
- `docs/prd/PRD-106-responsavel-compra-materiais-para-dependente.md`
- `docs/GUIA-PREENCHIMENTO-TESTE-CLIENTE.md`
- `system/urls.py`
- `system/views/home_views.py`
- `templates/home/dashboard.html`
- `system/tests/test_home_dependents_section.py`
- `system/forms/registration_forms.py`
- `system/services/registration.py`
- `system/services/pre_registration.py`
- `system/services/registration_checkout.py`
- `system/views/auth_views.py`
- `system/views/payment_views.py`
- `system/models/pre_registration.py`
- `system/models/registration_order.py`
- `system/models/person.py`
- `system/models/membership.py`
- `system/services/membership.py`

### Adjacent files consulted
- `system/services/class_overview.py`
- `system/services/registration_validation.py`
- `system/selectors/plan_eligibility.py`
- `static/system/js/auth/register.js`
- `static/system/css/auth/register.css`
- `static/system/js/home/dashboard.js`
- `static/system/css/home/dashboard.css`

### Internet / official documentation
- Django 5.2 forms: https://docs.djangoproject.com/en/5.2/topics/forms/
  - Conclusão: entradas do usuário devem ser processadas por `POST`, validadas server-side por `Form.is_valid()` e persistidas somente a partir de `cleaned_data`.
- Django 5.2 transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
  - Conclusão: a criação final de dependente, vínculo, conta, matrícula, pedido e assinatura deve ocorrer dentro de `transaction.atomic`.
- Django 5.2 authentication: https://docs.djangoproject.com/en/5.2/topics/auth/default/
  - Conclusão: o fluxo deve exigir sessão autenticada por mixin/guard equivalente ao `PortalLoginRequiredMixin`.
- Stripe subscriptions integration: https://docs.stripe.com/billing/subscriptions/design-an-integration
  - Conclusão: assinatura recorrente deve continuar usando Billing/Checkout Sessions, não `PaymentIntent` manual.
- Stripe Checkout overview: https://docs.stripe.com/payments/checkout
  - Conclusão: Checkout Sessions seguem válidas para pagamento hospedado ou incorporado; esta PRD mantém o padrão atual de sessão/retorno/webhook do projeto.

### Context7 / MCPs / tools verified
- Context7: `/websites/djangoproject_en_5_2` para Django 5.2.
- `stripe-best-practices`: lida; referência de billing/assinaturas exige Billing APIs + Checkout Sessions para recorrência.
- PowerShell: funcional.
- `rg`: funcional.

### Limitations found
- A implementação final evitou mudança de schema: `flow_kind` e `owner_person_id` ficam no `PreRegistration.form_snapshot`, encapsulados por `system/services/dependent_registration.py`.
- Pagamento externo real depende de ambiente, gateway e webhook ativos. A validação local cobriu criação de pré-cadastro, retorno de pagamento e caminho familiar; não foi executada uma nova cobrança real de dependente.
- Materiais opcionais não foram incorporados ao wizard desta entrega; permanecem no fluxo existente de loja/solicitação de materiais após a criação do dependente.
- Idempotência completa de duplo submit/refresh da finalização não foi implementada nesta entrega.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `stripe-best-practices`
- `browser:control-in-app-browser`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual: "implemente e valide". Esta entrega implementa e valida o núcleo funcional da PRD: home com ação, rota autenticada, formulário server-side, pré-cadastro pago sem criar pessoa, retorno de pagamento para o fluxo correto e finalização coberta por plano familiar.

## Execution prompt
### Persona
Agente sênior Django/MVT do LV JIU JITSU, seguindo SDD, TDD, validação visual no navegador interno e regras de pagamento do projeto.

### Action
Implementar o fluxo autenticado de adição de dependente pós-matrícula, desde a home até a finalização transacional, com plano/pagamento/material opcional e vínculo familiar correto.

### Context
O sistema já tem:
- wizard público com dependentes em `PortalRegistrationForm`, `register.js` e `register.html`;
- `PreRegistration` para pagamento antes de criar `Person`;
- `PersonRelationship` com `RESPONSIBLE_FOR`;
- home autenticada que só exibe dependentes já existentes;
- pagamentos Asaas e Stripe recorrente com retorno em `PaymentSuccessView`;
- regra de PRD-040: pagamento antes de pessoa.

### Constraints
- Não reaproveitar `/register/` como atalho visual ou HTTP para aluno autenticado.
- Não criar `Person`, `PortalAccount`, `ClassEnrollment`, `PersonRelationship`, `Membership` ou `RegistrationOrder` de dependente antes da finalização correta.
- Não guardar senhas em snapshot.
- Não aplicar regra de negócio em template ou JavaScript.
- Não expor rota de dependente para usuário não autenticado.
- Não permitir que um aluno vincule dependente a outra pessoa.
- Não permitir CPF já ativo em outro cadastro sem decisão administrativa explícita.
- Não editar `staticfiles/`.
- Atualizar `?v=` de CSS/JS alterados.

### Acceptance criteria
- [x] Aluno autenticado sem dependentes vê seção "Dependentes" com estado vazio e ação "Adicionar dependente".
- [x] Responsável/aluno com dependentes vê a lista existente e a ação "Adicionar dependente".
- [x] Usuário sem `portal_person` ativo não acessa o fluxo.
- [x] A rota autenticada canônica é criada em `GET/POST /dependents/add/`, sem depender de `/register/`.
- [x] Wizard coleta dados pessoais, saúde, experiência marcial, turma e plano.
- [ ] Wizard coleta materiais opcionais e revisão dedicada.
- [x] CPF do dependente é validado server-side contra `Person` ativo.
- [ ] CPF pendente em outro pré-cadastro do mesmo responsável é bloqueado.
- [x] Turmas selecionáveis respeitam elegibilidade por idade/sexo/categoria.
- [x] Plano individual exige pagamento antes de finalizar.
- [x] Plano familiar ativo do responsável pode cobrir o dependente sem cobrança duplicada.
- [x] Stripe recorrente usa Checkout/Billing existentes; Asaas usa o padrão existente.
- [x] Retorno de pagamento marca o fluxo pendente como pago sem criar pessoa automaticamente.
- [x] Finalização cria dependente, conta de portal, matrícula, relacionamento `RESPONSIBLE_FOR`, graduação inicial e assinatura/mensalidade de forma atômica.
- [ ] Reenvio ou refresh da finalização é idempotente.
- [x] Home passa a mostrar o dependente recém-criado e a mensalidade correta.
- [ ] Responsável consegue comprar materiais para o novo dependente dentro deste wizard.
- [x] Testes focados cobrem home, bloqueio anônimo, caminho familiar, pagamento pendente e retorno de pagamento.
- [x] Validação visual desktop/mobile no navegador interno cobre estado vazio, wizard e estado com dependente.

### Expected evidence
- `.\.venv\Scripts\python.exe manage.py check`
- Testes focados novos e ajustados.
- Teste proporcional de pagamento/pre-cadastro.
- `node --check` para JS alterado.
- Validação ORM local.
- Browser interno desktop/mobile, tema claro/escuro, console sem erro crítico.
- Registro de limitações de gateway real, se não executado.

### Output format
Código implementado, PRD atualizada com evidências reais, testes executados, screenshots/descrição do navegador interno, limpeza de diff e pendências explícitas.

## Scope
- Criar seção/estado vazio na home para dependentes.
- Criar fluxo autenticado próprio para adicionar dependente após matrícula.
- Reutilizar regras de dados do cadastro público onde fizer sentido, mas isolando o fluxo autenticado.
- Persistir rascunho/pagamento antes de criar pessoa real.
- Criar dependente e vínculo familiar apenas na finalização.
- Integrar mensalidade do dependente a uma das condições:
  - plano familiar ativo do responsável quando elegível;
  - contratação de plano próprio para o dependente;
  - solicitação de análise administrativa para isenção/permuta, se habilitada por regra de plano.
- Permitir materiais opcionais para o dependente antes da revisão final.
- Atualizar testes e documentação.

## Out of scope
- Reescrever o wizard público inteiro.
- Criar plano novo ou alterar preços.
- Resolver troca de plano/fidelidade do responsável além do necessário para adicionar dependente.
- Dar acesso administrativo ao dependente.
- Múltiplos responsáveis no mesmo fluxo. O novo dependente nasce vinculado ao usuário autenticado; vínculos adicionais ficam para fluxo administrativo existente/futuro.
- Validação real em produção/HG sem autorização explícita.

## Impacted files
| Arquivo | Mudança esperada |
|---|---|
| `system/forms/dependent_forms.py` | Novo form server-side para dependente pós-matrícula |
| `system/services/dependent_registration.py` | Regras transacionais de rascunho, pagamento e finalização |
| `system/services/registration.py` | Corrigir resolução de faixa inicial a partir do cadastro |
| `system/views/dependent_views.py` | Wizard autenticado e finalização |
| `system/views/payment_views.py` | Retorno de pagamento para fluxo de dependente |
| `system/views/home_views.py` | Expor estado vazio, lista e ação de dependentes |
| `system/urls.py` | Rotas canônicas do fluxo |
| `templates/home/dashboard.html` | Seção "Dependentes" com ação/estado vazio |
| `templates/dependents/dependent_registration.html` | Wizard autenticado |
| `static/system/css/dependents/dependent_registration.css` | Estilo do wizard |
| `static/system/css/home/dashboard.css` | Ajuste de estado vazio |
| `system/tests/test_dependent_registration.py` | Contrato backend do fluxo |
| `system/tests/test_home_dependents_section.py` | Atualizar estado vazio e ação |
| `docs/prd/PRD-118-adicionar-dependente-pos-matricula.md` | Evidências finais |

## Risks and edge cases
- Responsável com plano familiar ativo pode ou não cobrir mais um dependente; a regra precisa ser explícita e testada.
- Dependente menor sem e-mail próprio ainda precisa de acesso de portal; decidir se a senha é criada pelo responsável ou se a conta nasce sem login próprio.
- CPF já cadastrado como aluno ativo não pode ser duplicado; eventual vínculo com pessoa existente deve ser fluxo administrativo, não self-service.
- Pagamento Stripe pode confirmar por webhook antes do retorno visual.
- Usuário pode abandonar o fluxo após pagamento e antes da finalização.
- Usuário pode tentar finalizar duas vezes.
- Materiais pagos sem finalização precisam permanecer vinculados ao rascunho, sem baixa de estoque duplicada.
- Responsável que também é professor/administrativo deve manter a home split sem perder a ação de dependente.
- Dependente recém-criado deve aparecer em mensalidade, loja, materiais e home sem exigir logout/login.

## Rules and constraints
- Fonte de verdade de UI: `docs/UI-SCREEN-CONTRACT.md`.
- Fonte de pagamento antes de pessoa: PRD-040.
- Fonte de dependentes na home: PRD-105.
- Fonte de compras para dependentes: PRD-106.
- Backend define permissões e regras; frontend só guia a experiência.
- `transaction.atomic` obrigatório na finalização.
- Toda ação de escrita usa `POST` e CSRF.
- Mensagens e interface em pt-BR.

## Plan
- [x] 1. Escrever testes Red para home com aluno sem dependentes vendo a ação.
- [x] 2. Escrever testes Red de permissão da rota autenticada.
- [ ] 3. Escrever testes Red de CPF duplicado e rascunho pendente.
- [x] 4. Escrever testes Red do caminho com plano familiar ativo.
- [x] 5. Escrever testes Red do caminho com plano pago próprio.
- [x] 6. Implementar modelagem de rascunho autenticado via snapshot do `PreRegistration`.
- [x] 7. Implementar form e service de dependente.
- [x] 8. Implementar views/urls do wizard.
- [x] 9. Integrar retorno de pagamento e finalização.
- [x] 10. Ajustar home/template/CSS.
- [x] 11. Validar desktop/mobile no navegador interno.
- [x] 12. Atualizar evidências, limpeza e pendências.

## Test plan
### Tests to author
- `HomeDependentsSectionTestCase.test_student_without_dependents_sees_add_dependent_action`
- `HomeDependentsSectionTestCase.test_guardian_with_dependents_still_sees_add_dependent_action`
- `DependentRegistrationPermissionTestCase.test_anonymous_user_redirects_to_login`
- `DependentRegistrationPermissionTestCase.test_technical_admin_without_portal_person_cannot_start_self_service_flow`
- `DependentRegistrationFormTestCase.test_rejects_active_existing_cpf`
- `DependentRegistrationFlowTestCase.test_draft_does_not_create_person`
- `DependentRegistrationFlowTestCase.test_family_plan_finalizes_without_new_charge_when_eligible`
- `DependentRegistrationFlowTestCase.test_paid_plan_requires_payment_before_finalize`
- `DependentRegistrationFlowTestCase.test_finalize_creates_dependent_relationship_enrollment_and_account_atomically`
- `DependentRegistrationFlowTestCase.test_finalize_is_idempotent`
- `DependentRegistrationPaymentReturnTestCase.test_stripe_return_marks_dependent_flow_paid_without_creating_person`
- `DependentRegistrationPaymentReturnTestCase.test_asaas_return_marks_dependent_flow_paid_without_creating_person`

### Execution authorization
Testes locais, ORM local, migrations locais e browser interno ficam autorizados quando a implementação for iniciada. Pagamento externo real continua exigindo ambiente/gateway conforme guia operacional.

### Execution evidence
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dependents_section system.tests.test_dependent_registration` — 7 testes, OK na execução final focada.
- `.\.venv\Scripts\python.exe manage.py check` — sem issues.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_home_dependents_section system.tests.test_pre_registration_service system.tests.test_registration_flow system.tests.test_graduation` — 31 testes, OK.
- `.\.venv\Scripts\python.exe manage.py test` — 440 testes, OK em 102.699s na execução final.

## Visual hierarchy
- A home deve usar F Pattern operacional.
- Seção "Dependentes" fica próxima de "Mensalidade" e "Graduação", não em acesso rápido administrativo.
- Ação "Adicionar dependente" é botão secundário com ícone de usuário/adicionar.
- Estado vazio é discreto, com texto curto e ação clara.
- Wizard usa o mesmo padrão de etapa do cadastro: logo/topo, barra de progresso, título da etapa, campos em coluna, ação primária no final.
- Campos obrigatórios exibem erro por campo, não só alerta global.
- Tema claro e escuro devem usar tokens existentes.

## Wireframe
### Região: Home / Dependentes
- Título: `Dependentes`
- Ação: `Adicionar dependente`
- Estado vazio:
  - Texto principal: `Nenhum dependente vinculado.`
  - Texto de apoio: `Cadastre um dependente para vincular turma, plano e materiais.`
  - Botão: `Adicionar dependente`
- Estado com dados:
  - Lista de dependentes já existente.
  - Botão `Adicionar dependente` no cabeçalho.

### Região: Wizard / Topo
- Voltar para home.
- Logo LV.
- Progresso `Etapa X de Y`.

### Região: Wizard / Etapas
- Etapa 1: Dados do dependente.
- Etapa 2: Saúde e emergência.
- Etapa 3: Experiência marcial e faixa.
- Etapa 4: Turma.
- Etapa 5: Plano e condição de pagamento.
- Etapa 6: Materiais opcionais.
- Etapa 7: Revisão e finalização.

### Região: Pagamento
- Se pagamento externo for necessário, o retorno local deve reabrir o wizard no estado correto.
- Se plano familiar cobre o dependente, mostrar badge `Coberto pelo plano familiar` e pular pagamento de mensalidade.

### Estados da tela
- Carregando: catálogo de turmas/planos ainda indisponível.
- Vazio: sem turmas/planos elegíveis, com mensagem objetiva.
- Editando: campos preenchíveis.
- Erro: erro por campo e resumo no topo.
- Pago: badge persistente e próxima ação clara.
- Finalizado: mensagem de sucesso e retorno para home.

## State machine
### Fluxo de dependente
- `idle` -> `draft`
- `draft` -> `plan_selected`
- `plan_selected` -> `covered_by_family_plan`
- `plan_selected` -> `payment_pending`
- `payment_pending` -> `payment_confirmed`
- `covered_by_family_plan` -> `ready_to_finalize`
- `payment_confirmed` -> `materials`
- `materials` -> `materials_payment_pending`
- `materials_payment_pending` -> `materials_payment_confirmed`
- `materials` -> `review`
- `materials_payment_confirmed` -> `review`
- `review` -> `finalizing`
- `finalizing` -> `finalized`
- qualquer estado -> `canceled`
- qualquer estado editável -> `error`

### Home / Dependentes
- `no_dependents` -> mostra estado vazio e CTA.
- `has_dependents` -> mostra lista e CTA.
- `dependent_flow_pending` -> mostra CTA de continuar rascunho quando houver fluxo inacabado do usuário.

## Visual validation
### Desktop
- [x] Home sem dependentes mostra ação.
- [x] Home com dependentes preserva cards existentes e ação.
- [x] Wizard sem overflow observado.
- [x] Retorno pós-pagamento redireciona para `/dependents/add/` pelo teste automatizado.

### Mobile
- [x] Botões e formulário renderizam em 390x844.
- [x] Campos não extrapolam largura (`overflowX=false`).
- [x] Progresso e ações não cobrem conteúdo observado.

### Tema
- [ ] Claro sem perda de contraste.
- [x] Escuro validado no estado atual do navegador interno.

### Console
- [x] Sem erro JS crítico.
- [ ] Sem 404 relevante de estático.

## ORM validation
- [x] Antes da finalização paga: `Person.objects.filter(cpf=<cpf_dependente>).exists()` é falso no teste `test_paid_plan_creates_pre_registration_without_person`.
- [x] Após finalização familiar: existe `Person` ativa para o dependente.
- [x] Existe `PortalAccount` ativa para o dependente.
- [x] Existe `PersonRelationship(source_person=responsavel, target_person=dependente, RESPONSIBLE_FOR)`.
- [x] Existe `ClassEnrollment` ativo para a turma escolhida.
- [x] `get_active_membership(dependente)` resolve pelo plano familiar do responsável no navegador interno.
- [ ] Nenhum pedido/material/estoque é duplicado após refresh.

## Quality validation
- [x] `manage.py check`.
- [x] Testes focados.
- [x] Teste proporcional de pagamentos/retorno.
- [x] `node --check` não aplicável: nenhum JS foi alterado/criado.
- [x] Diff revisado com `lv-cleanup-audit`.
- [x] Sem `except: pass` introduzido.
- [x] Sem `innerHTML` com dados do usuário introduzido.
- [x] Lista de dependentes mantém `select_related("target_person", "target_person__person_type")`.

## Evidence
- `rg -n "PRD-118|Adicionar dependente pós-matrícula" docs\prd\PRD-118-adicionar-dependente-pos-matricula.md docs\prd\README.md` — encontrou a PRD e a linha do índice.
- `git diff --check -- docs\prd\README.md docs\prd\PRD-118-adicionar-dependente-pos-matricula.md` — sem erro de whitespace; PowerShell avisou apenas normalização futura LF→CRLF no README.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_home_dependents_section` — 7 testes, OK.
- `.\.venv\Scripts\python.exe manage.py check` — sem issues.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_dependent_registration system.tests.test_home_dependents_section system.tests.test_pre_registration_service system.tests.test_registration_flow system.tests.test_graduation` — 31 testes, OK.
- `.\.venv\Scripts\python.exe manage.py test` — 440 testes, OK.
- Browser interno desktop: home exibiu `DEPENDENTES`, `Adicionar dependente`, estado vazio; depois exibiu `Dependente Browser PRD 118`, `BRANCA`, `MENSALIDADE EM DIA`, `2 aulas hoje`; console sem erros.
- Browser interno mobile 390x844: home e wizard sem overflow horizontal; console sem erros.
- Banco local de validação: criado `Dependente Browser PRD 118` e plano/assinatura fictícia `Familiar Validação Browser` para validar o caminho familiar sem checkout externo.

## Implemented
- `system/forms/dependent_forms.py`: form server-side do dependente pós-matrícula com validação de CPF ativo, senha, turma, histórico marcial e condição financeira.
- `system/services/dependent_registration.py`: snapshot do fluxo autenticado, pré-cadastro pago e finalização transacional.
- `system/views/dependent_views.py`: `GET/POST /dependents/add/` autenticado.
- `system/views/payment_views.py`: retorno de pagamento de dependente volta para o fluxo correto e marca `plan_paid`.
- `system/views/home_views.py` e `templates/home/dashboard.html`: seção `Dependentes` com estado vazio e CTA.
- `templates/dependents/dependent_registration.html` e `static/system/css/dependents/dependent_registration.css`: tela sequencial de cadastro do dependente.
- `system/services/registration.py`: correção da resolução de faixa inicial para não resolver `white` como `red_white`.
- Testes novos/ajustados em `system/tests/test_dependent_registration.py` e `system/tests/test_home_dependents_section.py`.

## Cleanup findings
- Diff do fluxo tocado revisado.
- `git diff --check` nos arquivos da entrega não reportou erro de whitespace; PowerShell/Git avisou apenas normalização futura LF→CRLF em arquivos já rastreados.
- Não foram introduzidos `except: pass`, `innerHTML`, `console.log`, `TODO` ou `FIXME` nos novos arquivos do fluxo.
- Dados fictícios de validação ficaram no banco local para evidenciar o fluxo no navegador interno.
- Worktree já tinha muitas mudanças preexistentes e não relacionadas, incluindo PRDs 115–117 e ajustes de cadastro/professor/administrativo; não foram revertidas.

## Follow-up PRDs
_Nenhuma criada._

## Deviations from plan
- Sem migration/schema: o vínculo do rascunho autenticado usa `form_snapshot["flow_kind"]` e `form_snapshot["owner_person_id"]`.
- Sem JS próprio para wizard: a tela é sequencial server-rendered para reduzir superfície de regra em frontend.
- Materiais opcionais e revisão dedicada ficaram fora desta implementação.
- Validação real de cobrança externa não foi repetida; a integração foi coberta por teste de pré-cadastro/retorno e pelo service de checkout existente.

## Pending
- Integrar materiais opcionais no wizard ou criar CTA explícito para loja com dependente recém-criado.
- Implementar idempotência completa de finalização.
- Bloquear CPF de dependente em pré-cadastro pendente do mesmo responsável.
- Criar teste específico de técnico autenticado sem `portal_person` recebendo 403.
- Validar tema claro explicitamente no navegador interno em uma passagem dedicada.

## Final status
Funcionalidade implementada e validada com limitações registradas.
