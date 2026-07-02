# PRD-112: Solicitacao de acesso administrativo pendente

## Summary
Implementar fluxo completo para uma pessoa solicitar acesso administrativo sem ganhar permissao automaticamente. A solicitacao pode nascer no cadastro publico ou dentro do portal autenticado, fica pendente em fila administrativa e so vira `Person`, `PortalAccount`, `PersonOperationalRole` ou `administrative-assistant` apos aprovacao explicita de uma pessoa com capacidade administrativa.

## Demand type
Feature backend + UI + workflow de aprovacao + seguranca de permissao.

## Current problem
- O wizard publico so oferece `Aluno` e `Responsavel`.
- O cadastro interno de pessoa permite alterar `PersonType` e papeis, mas isso e uma acao administrativa direta, nao uma solicitacao auditavel.
- Nao existe entidade de solicitacao pendente para acesso administrativo.
- A PRD-111 consegue criar fixtures com administrativos e alunos com upgrade administrativo, mas essas possibilidades nao existem como fluxo de produto validavel ponta a ponta.

## Goal
- Adicionar solicitacao de acesso administrativo na tela de cadastro e no portal autenticado.
- Persistir a solicitacao com status pendente, dados pessoais, justificativa, papeis solicitados e origem.
- Criar fila administrativa para aprovar, reprovar, cancelar e auditar solicitacoes.
- Ao aprovar, promover a pessoa de forma transacional:
  - pessoa existente: manter vinculo principal e adicionar papeis operacionais aprovados;
  - pessoa nova: criar `Person`/`PortalAccount` apenas com acesso permitido;
  - administrativo pleno: usar `PersonTypeCode.ADMINISTRATIVE_ASSISTANT` somente quando o aprovador marcar esse nivel.
- Garantir que nenhuma permissao de gestao seja concedida antes da aprovacao.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md`
- `docs/prd/PRD-074-papeis-operacionais-acumulaveis-permissoes.md`
- `docs/prd/PRD-091-ui-papeis-operacionais-formulario-pessoa.md`
- `docs/prd/PRD-111-seeds-homologacao-cadastro-nn.md`
- `system/constants.py`
- `system/models/person.py`
- `system/models/pre_registration.py`
- `system/views/auth_views.py`
- `system/views/portal_mixins.py`
- `system/views/home_views.py`
- `system/forms/person_forms.py`
- `system/services/pre_registration.py`
- `system/services/portal_capabilities.py`
- `system/urls.py`
- `templates/login/register.html`

### Adjacent files consulted
- `static/system/js/auth/register.js`
- `templates/home/dashboard.html`
- `system/views/person_views.py`
- `system/services/operational_roles.py`
- `system/tests/test_person_operational_roles_form.py`
- `system/tests/test_home_dashboard.py`

### Internet / official documentation
- Django 5.2 auth and access control: `https://docs.djangoproject.com/en/5.2/topics/auth/default/`
- Django 5.2 transactions: `https://docs.djangoproject.com/en/5.2/topics/db/transactions/`
- Django 5.2 testing tools: `https://docs.djangoproject.com/en/5.2/topics/testing/tools/`

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: `LoginRequiredMixin`, `PermissionRequiredMixin`, custom permissions, `transaction.atomic` e `RequestFactory` para testes de views.

### Limitations found
- O wizard publico atual e um fluxo de pagamento antes de criar `Person`; a solicitacao administrativa nao deve reutilizar pagamento nem criar pessoa antes da aprovacao.
- `Person.person_type` continua singular; acesso administrativo parcial deve preferir `PersonOperationalRole` e capacidades.
- Se houver mudanca de schema, a baseline unica `system/migrations/0001_initial.py` deve ser regenerada localmente na implementacao, conforme protocolo do projeto.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitacao atual: gerar PRDs para implementar as funcionalidades conceituais ausentes antes da homologacao da PRD-111.

## Execution prompt
### Persona
Engenheiro Django senior focado em autorizacao, workflows pendentes e UI administrativa server-rendered.

### Action
Implementar workflow de solicitacao de acesso administrativo pendente, com entrada pelo cadastro publico e pelo portal, fila administrativa, aprovacao transacional e validacao visual.

### Context
O sistema ja possui `PersonType`, `OperationalRole`, `PersonOperationalRole`, `PortalCapability`, `PreRegistration` e `PortalSessionMiddleware`. A nova funcionalidade deve acrescentar workflow pendente sem conceder permissao ate a aprovacao.

### Constraints
- Sem permissao administrativa antes da aprovacao.
- Sem criar `Person` por solicitacao publica antes de aprovacao.
- Sem reaproveitar checkout/pagamento.
- UI em pt-BR; codigo e nomes tecnicos em ingles.
- Backend e fonte de verdade; JavaScript apenas controla experiencia.
- Todas as escritas de aprovacao/reprovacao em `transaction.atomic`.
- Reprovar nao apaga historico.
- Aprovar nao duplica pessoa por CPF.

### Acceptance criteria
- [x] Tela `/register/` exibe uma opcao clara de "Solicitar acesso administrativo" separada de Aluno/Responsavel.
- [x] Solicitacao publica grava apenas uma entidade pendente, sem criar `Person`, `PortalAccount` ou papel operacional.
- [x] Pessoa logada consegue solicitar acesso administrativo pelo portal sem alterar permissao corrente.
- [x] Solicitacao exige nome, CPF, e-mail, telefone, justificativa, origem e papeis solicitados.
- [x] CPF ja cadastrado vincula a solicitacao a pessoa existente, sem duplicar cadastro.
- [x] Fila administrativa lista pendentes com filtros por origem, CPF, status e data.
- [x] Apenas pessoa com `MANAGE_PEOPLE` ou `MANAGE_ACADEMY` aprova/reprova.
- [x] Aprovacao permite escolher entre papeis operacionais especificos e administrativo pleno.
- [x] Aprovacao de papeis operacionais cria/atualiza `PersonOperationalRole` sem trocar indevidamente o `person_type` de aluno/responsavel/professor.
- [x] Aprovacao de administrativo pleno cria ou atualiza `Person.person_type=administrative-assistant` somente quando explicitamente escolhido.
- [x] Reprovacao registra motivo e nao concede acesso.
- [x] Historico aparece no detalhe da pessoa e na fila de solicitacoes.
- [ ] PRD-111 consegue validar visualmente aluno com upgrade administrativo, administrativo seco e administrativo que treina usando fluxo real.

### Expected evidence
- Testes de model/service/view para solicitar, aprovar e reprovar.
- Testes de seguranca garantindo ausencia de permissao antes da aprovacao.
- `manage.py check`.
- Validacao visual desktop/mobile do cadastro publico, home do solicitante e fila administrativa.
- ORM local comprovando antes/depois da aprovacao.

### Output format
Codigo implementado, testes, screenshots/evidencia de navegador e PRD atualizada com resultados reais.

## Scope
- Novo modelo de solicitacao administrativa, por exemplo `AdministrativeAccessRequest`.
- Enums de status: `pending`, `approved`, `rejected`, `canceled`.
- Origem: `public_registration`, `portal`, `admin_created`.
- Campos minimos: pessoa existente opcional, dados pessoais, snapshot, papeis solicitados, justificativa, decisor, datas, motivo de decisao.
- Forms server-side para solicitacao publica, solicitacao autenticada e decisao administrativa.
- Services para criar, aprovar, reprovar e cancelar.
- Views/templates:
  - entrada no cadastro publico;
  - entrada no portal/home;
  - fila administrativa;
  - detalhe da solicitacao;
  - modal/acao de aprovar/reprovar.
- Auditoria operacional quando disponivel.
- Testes proporcionais e validacao visual.

## Out of scope
- Aprovar pagamento, plano ou matricula.
- Envio real de e-mail/WhatsApp.
- Escrita em HG/producao.
- Refatoracao geral do wizard publico.
- Criar fluxo de turma/horario por professor; isso pertence a PRD-113.

## Impacted files
- `system/models/person.py` ou novo model em `system/models/access_request.py`
- `system/models/__init__.py`
- `system/constants.py`
- `system/forms/access_request_forms.py`
- `system/services/access_requests.py`
- `system/views/access_request_views.py`
- `system/views/auth_views.py`
- `system/views/home_views.py`
- `system/urls.py`
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `templates/home/dashboard.html`
- `templates/access_requests/*`
- `system/tests/test_administrative_access_requests.py`
- `system/migrations/0001_initial.py` se houver schema novo

## Risks and edge cases
- Autoaprovacao: quem solicita nao pode aprovar a propria solicitacao se nao tiver capacidade vigente.
- CPF duplicado: solicitacao publica deve localizar pessoa existente por CPF normalizado.
- Pessoa existente com pagamento pendente nao deve ganhar gestao por contornar bloqueio financeiro.
- Solicitacao repetida pendente para mesmo CPF e tipo deve ser bloqueada ou consolidada.
- Reprovacao precisa preservar historico para auditoria.
- Administrativo parcial deve usar papel operacional; trocar `person_type` pode quebrar area pessoal do aluno.
- Aprovar pessoa nova sem senha definida exige fluxo claro de criacao/ativacao de `PortalAccount`.

## Rules and constraints
- MVT: models persistem, forms validam entrada, services escrevem, views finas.
- `transaction.atomic` em aprovacao/reprovacao.
- `select_for_update` quando aprovar solicitacao pendente.
- Permissao sempre no backend por `PortalCapability`.
- Sem regra de negocio em template/JS.
- Sem `except: pass`.
- Sem editar `staticfiles/`.

## Visual hierarchy
- Cadastro publico: a nova opcao deve aparecer como terceiro card funcional, mas visualmente indicar "pendente de aprovacao", nao "acesso imediato".
- Portal/home: bloco compacto "Solicitacoes" abaixo das areas pessoais/gestao, com status atual.
- Fila administrativa: tabela/lista densa, operacional, com status, solicitante, origem, papeis solicitados, data e acoes.
- Detalhe: resumo da pessoa, justificativa, papeis solicitados, historico e decisao.

## Wireframe
### Cadastro publico
```text
Como voce vai se cadastrar?
[Aluno] [Responsavel] [Solicitar acesso administrativo]

Solicitar acesso administrativo
- Nome completo
- CPF
- E-mail
- Telefone
- Area desejada: Pessoas / Turmas / Financeiro / Estoque / Graduacao / Gestao completa
- Justificativa
[Enviar solicitacao]
```

### Portal autenticado
```text
Solicitacoes
Status atual: nenhuma / pendente / aprovada / recusada
[Solicitar acesso administrativo]
```

### Fila administrativa
```text
Solicitacoes administrativas
Filtros: status, origem, CPF, periodo
Linha: solicitante | CPF | origem | papeis | status | data | [Ver]
Detalhe: [Aprovar] [Reprovar] [Cancelar]
```

## State machine
```text
draft -> pending -> approved
draft -> pending -> rejected
pending -> canceled
approved/rejected/canceled -> terminal
```

### Regras de estado
- `pending` nao concede capacidade.
- `approved` exige decisor, data e payload aprovado.
- `rejected` exige motivo.
- `canceled` so permitido pelo solicitante antes da decisao ou por gestor.

## Plan
1. [ ] Confirmar modelagem final do request.
2. [ ] Escrever testes Red de criacao publica sem `Person`.
3. [ ] Escrever testes Red de solicitacao autenticada sem mudar capacidades.
4. [ ] Escrever testes Red de aprovacao com `PersonOperationalRole`.
5. [ ] Escrever testes Red de aprovacao como administrativo pleno.
6. [ ] Implementar model/forms/services.
7. [ ] Implementar views/templates/urls.
8. [ ] Ajustar wizard JS sem deslocar fluxo de pagamento de aluno/responsavel.
9. [ ] Validar visualmente cadastro, portal e fila.
10. [ ] Atualizar PRD com evidencias reais.

## Test plan
### Tests to author
- `test_public_administrative_request_does_not_create_person`
- `test_existing_person_request_links_by_cpf_without_duplicate`
- `test_pending_request_does_not_add_capabilities`
- `test_approve_operational_roles_grants_expected_capabilities`
- `test_approve_full_administrative_sets_person_type_when_selected`
- `test_reject_request_keeps_person_unchanged`
- `test_only_manage_people_or_manage_academy_can_decide`
- `test_duplicate_pending_request_for_same_cpf_is_rejected`
- `test_cancel_pending_request_by_requester`
- `test_cannot_cancel_already_decided_request`
- `test_manager_can_open_queue_and_detail` / `test_non_manager_is_blocked_from_queue_and_detail` / `test_non_manager_cannot_approve_via_post`
- `test_requester_can_self_cancel` / `test_unrelated_person_cannot_self_cancel`
- `test_date_filter_narrows_queue`

### Execution authorization
Local, banco de teste isolado do Django. Migrations locais autorizadas se a implementacao exigir schema.

### Execution evidence
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_administrative_access_requests system.tests.test_class_catalog_requests --verbosity 2` => 14 testes OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dashboard system.tests.test_register_wizard_contract system.tests.test_registration_flow system.tests.test_lv_foundation_classes system.tests.test_admin_hubs_contract --verbosity 2` => 21 testes OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py makemigrations system --check --dry-run` => sem mudancas detectadas.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py check` => sem issues.
- `2026-07-01` (correcoes de limitacoes): `.\.venv\Scripts\python.exe clear_migrations.py` + `.\.venv\Scripts\python.exe manage.py makemigrations` (regerou `0001_initial.py` com `extra_schedules` em `ClassCatalogRequest`; `AdministrativeAccessRequest` sem mudanca de schema).
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_administrative_access_requests system.tests.test_class_catalog_requests system.tests.test_administrative_access_request_views system.tests.test_class_catalog_request_views --verbosity 2` => 30 testes OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` => 391 testes OK (suite completa).
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py check` => sem issues.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` => sem mudancas detectadas.

## Visual validation
### Desktop
- [x] Cadastro publico mostra terceira opcao sem quebrar layout.
- [x] Envio exibe confirmacao de solicitacao pendente (mensagem de sucesso e mudanca de status validadas via aprovar/cancelar reais no navegador interno).
- [x] Portal mostra bloco de solicitacoes e links de filas para pessoa com gestao.
- [x] Fila administrativa renderiza filtros (status, origem, CPF, data) e detalhe de aprovacao/reprovacao/cancelamento.

### Mobile
- [x] Cards do cadastro nao sobrepoem texto.
- [x] Fila administrativa vira lista escaneavel (validado no card gerado nesta entrega, layout de linha unica por solicitacao).
- [x] Formulario e home validados sem overflow horizontal; botao "Cancelar" no bloco de solicitacoes da home valida em 375x812.

### Console
- [x] Sem erro JS critico.
- [x] Sem 404 de asset relevante nas telas navegadas.

## ORM validation
- [x] Antes da aprovacao: solicitacao existe, pessoa/roles nao foram criados ou alterados.
- [x] Depois da aprovacao operacional: `PersonOperationalRole` ativo existe.
- [x] Depois da aprovacao plena: `Person.person_type.code == administrative-assistant` apenas quando escolhido.
- [x] Depois da reprovacao: nenhuma capacidade nova aparece.

## Quality validation
- [x] `manage.py test system.tests.test_administrative_access_requests --verbosity 2`
- [x] `manage.py check`
- [x] Teste visual com navegador interno.
- [x] Busca por comparacoes indevidas de `person_type` em novas views (revisado; aprovacao operacional preserva `person_type` e so altera quando `grant_full_administrative` e explicito).

## Evidence
- PRD criada em 2026-07-01 com leitura dos contratos locais, mapeamento do fluxo atual de cadastro/papeis e consulta a documentacao oficial Django registrada no Context Ledger.
- `2026-07-01`: implementado model `AdministrativeAccessRequest`, forms, services transacionais, views, URLs, templates, integracao no cadastro publico e home autenticada.
- `2026-07-01`: `makemigrations --check --dry-run` sem mudancas; schema consolidado em `system/migrations/0001_initial.py`.
- `2026-07-01`: `manage.py check` OK.
- `2026-07-01`: 14 testes focados PRD-112/113 OK e 21 testes adjacentes OK.
- `2026-07-01`: navegador interno validou `/register/admin-access/`, `/register/`, `/home/`, `/requests/admin-access/` e `/requests/admin-access/create/` sem erros de console.
- Evidencia visual salva em `docs/prd/evidence/PRD-112-113-home-mobile.png`.
- `2026-07-01` (correcao de limitacoes): implementado `cancel_administrative_access_request`, `can_cancel_administrative_access_request`, view `AdministrativeAccessRequestSelfCancelView`, rota `requests/admin-access/<pk>/cancel/`, botao "Cancelar" no detalhe (gestor) e na home (solicitante).
- `2026-07-01`: filtro `date_from`/`date_to` adicionado a `AdministrativeAccessRequestQueueView` e ao template `access_requests/request_list.html`.
- `2026-07-01`: `PersonDetailView` passa `access_request_history`/`class_request_history`; nova secao "Solicitacoes" em `templates/people/person_detail.html`, visivel apenas para `can_manage_people`.
- `2026-07-01`: novo arquivo `system/tests/test_administrative_access_request_views.py` com 6 testes de permissao/cancelamento/filtro de data; todos OK.
- `2026-07-01`: navegador interno validou fila com filtro de data, cancelamento real de solicitacao (status pendente -> cancelada), historico no detalhe de pessoa (`/people/1/view/`) e bloco "Solicitacoes" mobile (375x812) com botao "Cancelar" funcional.
- `2026-07-01`: suite completa `manage.py test` (391 testes) OK apos regeneracao da baseline de migrations.

## Implemented
- Modelo persistente de solicitacao administrativa com status, origem, pessoa vinculada, decisor, papeis solicitados/aprovados e constraint de CPF pendente.
- Service de criacao, aprovacao e reprovacao com `transaction.atomic`, `select_for_update`, normalizacao de CPF e preservacao de `person_type` para upgrade operacional.
- Fluxo publico `/register/admin-access/` sem criacao de `Person` antes de aprovacao.
- Fluxo autenticado `/requests/admin-access/create/`.
- Fila e detalhe administrativo com filtros por status/origem/CPF/data e decisao aprovar/reprovar/cancelar.
- Integracao do card no `/register/` e do bloco de solicitacoes no `/home/`.
- Cancelamento controlado: pelo proprio solicitante (CPF correspondente) ou por gestor com `MANAGE_PEOPLE`/`MANAGE_ACADEMY`, preservando historico via `decided_by`/`decided_at`/`decision_notes`.
- Historico de solicitacoes administrativas e de turma no detalhe da pessoa, restrito a `can_manage_people`.

## Cleanup findings
- Revisao parcial executada em 2026-07-01. Nenhum `staticfiles/` foi editado.
- O clique automatizado em botoes de formulario continua sem disparar POST nativo neste navegador interno (mesma limitacao registrada na entrega anterior); a correcao foi validada com `form.submit()` via `preview_eval` e com `system.tests.test_administrative_access_request_views`/`test_class_catalog_request_views` usando o cliente de teste Django, que cobrem o POST real.

## Follow-up PRDs
- PRD-113 cobre solicitacoes de turmas/horarios.
- PRD-111 deve ser usada depois para homologar os cenarios de upgrade administrativo.

## Deviations from plan
- Nenhum desvio material nesta correcao; os itens pendentes da entrega anterior foram implementados dentro do escopo original da PRD.

## Pending
- PRD-111 ainda precisa rodar a homologacao visual completa de aluno com upgrade administrativo, administrativo seco e administrativo que treina usando o fluxo real (fora do escopo desta correcao).

## Final status
Concluida.
