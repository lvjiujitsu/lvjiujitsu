# PRD-113: Solicitacao de turmas e horarios por professor

## Summary
Implementar fluxo para professores solicitarem criacao de nova turma, novo horario em turma existente ou onboarding de professor novo com proposta inicial de horario. A solicitacao fica pendente ate aprovacao por pessoa com gestao de turmas, e a aprovacao promove os dados para `ClassGroup`, `ClassSchedule`, `ClassInstructorAssignment` e, quando necessario, `Person`/`PortalAccount` de professor.

## Demand type
Feature backend + UI + workflow de aprovacao + calendario/turmas.

## Current problem
- O sistema possui CRUD administrativo de `ClassGroup` e `ClassSchedule`, mas apenas administrativo cria/edita diretamente.
- Professores nao possuem fluxo para solicitar novo horario ou nova turma.
- Professor novo, ainda sem cadastro, nao consegue propor horario inicial sem intervencao manual do admin.
- A PRD-111 possui fixtures com professores e turmas, mas nao consegue homologar a criacao real desses casos por solicitacao/aprovacao.

## Goal
- Permitir solicitacao de:
  - novo horario em turma existente;
  - nova turma com um ou mais horarios;
  - cadastro de professor novo com proposta de turma/horario inicial.
- Criar fila de aprovacao para gestores de turmas.
- Promover solicitacao aprovada para catalogo real de turmas/horarios de forma transacional.
- Reprovar ou cancelar mantendo historico e motivo.
- Expor status da solicitacao para professor/solicitante.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `docs/prd/PRD-074-papeis-operacionais-acumulaveis-permissoes.md`
- `docs/prd/PRD-091-ui-papeis-operacionais-formulario-pessoa.md`
- `docs/prd/PRD-111-seeds-homologacao-cadastro-nn.md`
- `system/constants.py`
- `system/models/person.py`
- `system/models/class_group.py`
- `system/models/class_schedule.py`
- `system/models/class_membership.py`
- `system/forms/class_forms.py`
- `system/views/class_views.py`
- `system/views/home_views.py`
- `system/views/portal_mixins.py`
- `system/services/class_management.py`
- `system/services/class_catalog.py`
- `system/services/class_calendar.py`
- `system/services/portal_capabilities.py`
- `system/urls.py`

### Adjacent files consulted
- `templates/classes/class_group_list.html`
- `templates/classes/class_group_form.html`
- `templates/class_schedules/class_schedule_list.html`
- `templates/class_schedules/class_schedule_form.html`
- `templates/home/dashboard.html`
- `system/tests/test_calendar.py`
- `system/tests/test_lv_foundation_classes.py`
- `static/initial_data/seed_system_initial_class_catalog.json`

### Internet / official documentation
- Django 5.2 auth and access control: `https://docs.djangoproject.com/en/5.2/topics/auth/default/`
- Django 5.2 transactions: `https://docs.djangoproject.com/en/5.2/topics/db/transactions/`
- Django 5.2 testing tools: `https://docs.djangoproject.com/en/5.2/topics/testing/tools/`

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: uso de mixins de autenticacao/permissao, `transaction.atomic`, permissoes customizadas e testes de views.

### Limitations found
- `ClassSchedule` ja tem constraint unica por turma/dia/estilo/hora; conflitos adicionais de sala/capacidade nao existem hoje no modelo.
- `ClassGroup.main_teacher` exige `PersonTypeCode.INSTRUCTOR`; professor novo precisa ser criado ou aprovado antes de virar professor principal.
- CRUD atual de classes e horarios e administrativo; novo fluxo nao deve liberar escrita direta para professor.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitacao atual: gerar PRDs para implementar o funcionamento completo antes da homologacao posterior.

## Execution prompt
### Persona
Engenheiro Django senior focado em catalogo de turmas, calendario, workflow de aprovacao e UI operacional.

### Action
Implementar solicitacoes pendentes de turma/horario por professor existente ou professor novo, com aprovacao administrativa e promocao transacional para o catalogo real.

### Context
`ClassGroup`, `ClassSchedule`, `ClassGroupForm`, `ClassScheduleForm` e `save_class_group_catalog` ja existem. A nova feature deve adicionar workflow de solicitacao sem permitir escrita direta no catalogo ate aprovacao.

### Constraints
- Professor nao cria `ClassGroup`/`ClassSchedule` diretamente.
- Aprovacao e a unica transicao que grava no catalogo real.
- Gestor com `MANAGE_CLASSES` ou `MANAGE_ACADEMY` decide.
- Professor novo nao ganha area de professor antes de aprovacao.
- Dados de solicitacao devem ser auditaveis e preservados apos decisao.
- UI pt-BR, codigo em ingles.
- Validacao server-side obrigatoria.

### Acceptance criteria
- [x] Professor logado ve acao "Solicitar turma/horario" na home.
- [x] Professor logado pode solicitar novo horario para turma em que atua como principal/auxiliar, ou propor nova turma.
- [x] Solicitante sem cadastro pode enviar proposta de professor novo com dados pessoais e horario inicial.
- [x] Solicitacao pendente nao cria nem altera `ClassGroup` ou `ClassSchedule`.
- [x] Fila administrativa lista solicitacoes com status, professor, categoria, turma, dias/horarios e data.
- [x] Aprovador pode ajustar payload antes de aprovar sem editar diretamente a solicitacao original sem rastreio.
- [x] Aprovar novo horario cria `ClassSchedule` vinculado a turma correta.
- [x] Aprovar nova turma cria `ClassGroup`, horario e equipe docente conforme payload aprovado.
- [x] Aprovar professor novo cria `Person` como `instructor`, `PortalAccount` e vinculos de turma/horario aprovados.
- [x] Reprovar registra motivo e nao cria turma/horario/professor.
- [x] Solicitacoes duplicadas/conflitantes mostram erro claro.
- [ ] PRD-111 consegue validar professor, professor com dependente e solicitacao de novo horario usando fluxo real.

### Expected evidence
- Testes de services, forms e views.
- ORM local antes/depois da aprovacao.
- Screenshots desktop/mobile da solicitacao e fila.
- `manage.py check`.

### Output format
Codigo implementado, testes, validacao visual, PRD atualizada com evidencias reais.

## Scope
- Novo modelo de solicitacao, por exemplo `ClassCatalogRequest`.
- Tipos:
  - `new_schedule`
  - `new_class_group`
  - `new_teacher_with_schedule`
- Status:
  - `pending`
  - `approved`
  - `rejected`
  - `canceled`
- Payload versionado em JSON e campos normalizados para filtros.
- Forms para professor existente, professor novo e decisao administrativa.
- Services:
  - criar solicitacao;
  - validar conflitos;
  - aprovar novo horario;
  - aprovar nova turma;
  - aprovar professor novo;
  - reprovar/cancelar.
- Views/templates:
  - formulario de solicitacao do professor;
  - formulario publico/protegido de professor novo;
  - minhas solicitacoes;
  - fila administrativa;
  - detalhe/decisao.
- Testes e validacao visual.

## Out of scope
- Gestão de salas físicas.
- Notificacoes reais por e-mail/WhatsApp.
- Pagamento/repasse automatico do professor novo.
- Alterar regras de check-in.
- Fluxo de acesso administrativo; isso pertence a PRD-112.

## Impacted files
- `system/models/class_request.py` ou `system/models/class_group.py`
- `system/models/__init__.py`
- `system/forms/class_request_forms.py`
- `system/services/class_requests.py`
- `system/views/class_request_views.py`
- `system/views/home_views.py`
- `system/views/class_views.py`
- `system/urls.py`
- `templates/class_requests/*`
- `templates/home/dashboard.html`
- `templates/classes/class_group_detail.html`
- `static/system/css/classes/*` se necessario
- `static/system/js/lv/*` ou JS especifico se necessario
- `system/tests/test_class_catalog_requests.py`
- `system/migrations/0001_initial.py` se houver schema novo

## Risks and edge cases
- Professor auxiliar com `class-assistant` pode solicitar para turma escopada; nao deve solicitar para qualquer turma.
- Professor novo pode informar CPF ja existente como aluno/responsavel; aprovacao deve decidir promover pessoa existente para `instructor` ou negar.
- Horario ja existente deve ser bloqueado antes de aprovar.
- Aprovador pode alterar horario para conflito; service final deve revalidar.
- Criar turma ativa sem horario ativo deve ser proibido, preservando regra atual de `BaseClassGroupScheduleFormSet`.
- Aprovacao parcial de multiplos horarios deve ser definida: ou todos entram, ou nenhum entra.
- Cancelamento nao pode remover turma/horario ja aprovado.

## Rules and constraints
- MVT: forms validam, services escrevem, views finas.
- `transaction.atomic` na aprovacao.
- `select_for_update` na solicitacao pendente durante decisao.
- Reusar validadores/formularios existentes (`ClassGroupForm`, `ClassScheduleForm`) sempre que possivel.
- Nao duplicar regra de constraint ja existente.
- Sem `innerHTML` com dado de usuario se houver JS.
- Sem editar `staticfiles/`.

## Visual hierarchy
- Home professor: acao pequena e operacional proxima da area "Turmas de hoje", nao card hero.
- Formulario de solicitacao: layout denso com radios/segmented control para tipo de solicitacao.
- Fila administrativa: lista operacional, filtros no topo, status em badges.
- Detalhe: dados originais da solicitacao e payload aprovado lado a lado quando houver ajuste.

## Wireframe
### Home professor
```text
Turmas de hoje
[Solicitar novo horario] [Solicitar nova turma]
Minhas solicitacoes: Pendente / Aprovada / Recusada
```

### Solicitacao de professor existente
```text
Tipo de solicitacao
( ) Novo horario em turma existente
( ) Nova turma

Turma/Categoria
Dia, horario, estilo, duracao, capacidade
Justificativa operacional
[Enviar solicitacao]
```

### Professor novo
```text
Dados do professor
Nome, CPF, e-mail, telefone, faixa/experiencia
Proposta inicial
Categoria, turma, dia, horario, estilo, duracao
Justificativa
[Enviar proposta]
```

### Fila administrativa
```text
Solicitacoes de turmas/horarios
Filtros: status, tipo, professor, categoria
Linha: tipo | professor | turma/categoria | horarios | status | data | [Ver]
Detalhe: [Aprovar] [Ajustar e aprovar] [Reprovar]
```

## State machine
```text
draft -> pending -> approved
draft -> pending -> rejected
pending -> canceled
approved/rejected/canceled -> terminal
```

### Promotion state
```text
pending request
  -> validate payload
  -> lock request
  -> create/update Person when needed
  -> create ClassGroup when needed
  -> create ClassSchedule(s)
  -> create ClassInstructorAssignment(s)
  -> mark approved
```

## Plan
1. [ ] Confirmar modelagem final do `ClassCatalogRequest`.
2. [ ] Escrever testes Red para professor existente solicitar novo horario sem alterar catalogo.
3. [ ] Escrever testes Red para aprovar novo horario.
4. [ ] Escrever testes Red para solicitar/aprovar nova turma com horarios.
5. [ ] Escrever testes Red para professor novo com proposta inicial.
6. [ ] Escrever testes Red de permissao e conflitos.
7. [ ] Implementar models/forms/services.
8. [ ] Implementar views/templates/urls.
9. [ ] Integrar chamada na home/calendario.
10. [ ] Validar visualmente desktop/mobile.
11. [ ] Atualizar PRD com evidencias reais.

## Test plan
### Tests to author
- `test_instructor_request_new_schedule_does_not_create_schedule`
- `test_approve_new_schedule_creates_class_schedule`
- `test_instructor_cannot_request_for_unscoped_class_group`
- `test_new_class_group_request_approval_creates_group_and_schedules`
- `test_new_teacher_request_does_not_create_person_before_approval`
- `test_new_teacher_request_approval_creates_instructor_and_schedule`
- `test_reject_request_creates_no_catalog_records`
- `test_duplicate_schedule_conflict_is_blocked`
- `test_only_manage_classes_or_manage_academy_can_approve`
- `test_cancel_pending_request_by_requester`
- `test_cannot_cancel_already_decided_request`
- `test_new_class_group_request_with_extra_schedules_creates_all_slots`
- `test_extra_schedule_duplicate_within_request_is_blocked`
- `test_extra_schedules_not_allowed_for_new_schedule_request`
- `test_manager_can_open_queue_and_detail` / `test_instructor_without_manage_capability_is_blocked_from_queue_and_detail` / `test_instructor_cannot_approve_via_post`
- `test_requester_can_self_cancel` / `test_unrelated_person_cannot_self_cancel`

### Execution authorization
Local, banco de teste isolado do Django. Migrations locais autorizadas se a implementacao exigir schema.

### Execution evidence
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_administrative_access_requests system.tests.test_class_catalog_requests --verbosity 2` => 14 testes OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dashboard system.tests.test_register_wizard_contract system.tests.test_registration_flow system.tests.test_lv_foundation_classes system.tests.test_admin_hubs_contract --verbosity 2` => 21 testes OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py makemigrations system --check --dry-run` => sem mudancas detectadas.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py check` => sem issues.
- `2026-07-01` (correcao de limitacoes): `.\.venv\Scripts\python.exe clear_migrations.py` seguido de `.\.venv\Scripts\python.exe manage.py makemigrations` para adicionar `extra_schedules` (`JSONField`) em `ClassCatalogRequest`; baseline `0001_initial.py` regenerada.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test system.tests.test_class_catalog_requests system.tests.test_class_catalog_request_views --verbosity 2` => 19 testes OK.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py test --verbosity 1` => 391 testes OK (suite completa, apos regeneracao de migrations).
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py check` => sem issues.
- `2026-07-01`: `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run` => sem mudancas detectadas.

## Visual validation
### Desktop
- [x] Professor existente possui entrada pela home quando tem area docente/suporte.
- [x] Admin visualiza fila e formulario de decisao, incluindo botao "Cancelar".
- [x] Turma/horario aprovado e criado pelo service e coberto por ORM/teste.
- [x] Formulario de professor novo e de turma existente exibem ate 4 linhas de "Horarios adicionais" com rotulo por linha, sem quebrar o layout.
- [x] Botao "Solicitar novo horario" aparece no cronograma (`/calendar/`) ao lado de "Criar aulao" quando o usuario tem `SUPPORT_CLASSES`.

### Mobile
- [x] Formulario de solicitacao nao tem overflow horizontal.
- [x] Fila administrativa em lista mobile mostra status e acoes claras (validado em 375x812).

### Console
- [x] Sem erro JS critico.
- [x] Sem 404 de asset relevante nas telas navegadas.

## ORM validation
- [x] Antes da aprovacao de horario: `ClassSchedule` nao existe para payload.
- [x] Depois da aprovacao de horario: `ClassSchedule` existe e request esta `approved`.
- [x] Antes da aprovacao de professor novo: `Person` nao existe para CPF informado.
- [x] Depois da aprovacao de professor novo: `Person.person_type.code == instructor`, `PortalAccount` existe e turma/horario existem.
- [x] Reprovacao nao cria registros de catalogo.

## Quality validation
- [x] `manage.py test system.tests.test_class_catalog_requests --verbosity 2`
- [x] `manage.py check`
- [x] Browser interno desktop/mobile.
- [x] Busca por escrita direta de catalogo em view de solicitacao fora do service (revisado; `ClassGroup`/`ClassSchedule` continuam gravados apenas em `system/services/class_requests.py`).

## Evidence
- PRD criada em 2026-07-01 com leitura dos contratos locais, mapeamento do CRUD atual de turmas/horarios e consulta a documentacao oficial Django registrada no Context Ledger.
- `2026-07-01`: implementado model `ClassCatalogRequest`, forms, services transacionais, views, URLs, templates, proposta publica de professor e solicitacao autenticada de turma/horario.
- `2026-07-01`: `makemigrations --check --dry-run` sem mudancas; schema consolidado em `system/migrations/0001_initial.py`.
- `2026-07-01`: `manage.py check` OK.
- `2026-07-01`: 14 testes focados PRD-112/113 OK e 21 testes adjacentes OK.
- `2026-07-01`: navegador interno validou `/register/teacher-proposal/`, `/home/`, `/requests/classes/` e `/requests/classes/create/` em desktop e mobile sem erros de console.
- Evidencia visual salva em `docs/prd/evidence/PRD-112-113-home-mobile.png`.
- `2026-07-01` (correcao de limitacoes): implementado `cancel_class_catalog_request`, `can_cancel_class_catalog_request`, view `ClassCatalogRequestSelfCancelView`, rota `requests/classes/<pk>/cancel/`, botao "Cancelar" no detalhe (gestor) e na home (professor/requester).
- `2026-07-01`: implementado campo `extra_schedules` (JSON) em `ClassCatalogRequest`; `create_existing_teacher_class_request`/`create_new_teacher_class_request` aceitam ate 4 horarios adicionais, validados sem duplicidade e bloqueados para `NEW_SCHEDULE`; `_approve_new_class_group` cria um `ClassSchedule` por horario adicional revalidando conflito no momento da aprovacao.
- `2026-07-01`: formset `ClassCatalogExtraScheduleFormSet` integrado em `ExistingTeacherClassCatalogRequestCreateView` e `PublicNewTeacherClassCatalogRequestCreateView`; templates `class_requests/request_form.html` e `class_requests/new_teacher_form.html` renderizam as linhas extras rotuladas.
- `2026-07-01`: botao "Solicitar novo horario" adicionado em `templates/calendar/calendar.html`, condicionado a `show_instructor_area` (que ja exige `SUPPORT_CLASSES`, mesma capacidade exigida pela view de criacao).
- `2026-07-01`: novo arquivo `system/tests/test_class_catalog_request_views.py` com 5 testes de permissao/cancelamento; todos OK.
- `2026-07-01`: navegador interno validou fila/detalhe com cancelamento e aprovacao reais, formulario de professor novo com 4 linhas de horario adicional renderizadas e rotuladas, botao no cronograma, e fila mobile (375x812) legivel.
- `2026-07-01`: suite completa `manage.py test` (391 testes) OK apos regeneracao da baseline de migrations.

## Implemented
- Modelo persistente de solicitacao de catalogo com tipo, origem, status, professor/pessoa criada, turma alvo/criada, payload aprovado, decisor, datas e horarios adicionais (`extra_schedules`).
- Services de criacao, aprovacao, reprovacao e cancelamento com `transaction.atomic`, `select_for_update`, validacao de escopo docente e bloqueio de conflito de horario (inclusive entre horarios adicionais).
- Fluxo de professor existente para novo horario em turma existente ou nova turma, com ate 4 horarios adicionais na mesma solicitacao de nova turma.
- Fluxo publico `/register/teacher-proposal/` para professor novo com horario inicial e horarios adicionais opcionais.
- Fila administrativa e detalhe com ajuste de payload antes de aprovar/reprovar/cancelar.
- Integracao do card publico no `/register/`, da acao autenticada no `/home/` e de um atalho no cronograma (`/calendar/`).
- Cancelamento controlado: pelo professor/requerente da solicitacao ou por gestor com `MANAGE_CLASSES`/`MANAGE_ACADEMY`.

## Cleanup findings
- Revisao parcial executada em 2026-07-01. Nenhum `staticfiles/` foi editado.
- O clique automatizado em botoes de formulario continua sem disparar POST nativo neste navegador interno (mesma limitacao registrada na entrega anterior); a correcao foi validada com `form.submit()` via `preview_eval` e com `system.tests.test_class_catalog_request_views` usando o cliente de teste Django, que cobre o POST real de aprovacao/reprovacao/cancelamento.
- Aprovador ainda nao pode editar os horarios adicionais no momento da decisao (apenas o horario principal e editavel); documentado como escopo intencional para manter a decisao simples nesta correcao.

## Follow-up PRDs
- PRD-112 cobre solicitacao de acesso administrativo.
- PRD-111 deve validar os cenarios depois da implementacao.

## Deviations from plan
- Nenhum desvio material nesta correcao; os itens pendentes da entrega anterior foram implementados dentro do escopo original da PRD.
- Horarios adicionais sao limitados a 4 por solicitacao (5 no total incluindo o principal) e nao sao editaveis individualmente pelo aprovador nesta entrega; ajustar exige reprovar e reenviar.

## Pending
- Permitir que o aprovador edite/remova horarios adicionais individualmente antes de aprovar (hoje so o horario principal e ajustavel na decisao).
- PRD-111 ainda precisa rodar a homologacao visual completa de professor, professor com dependente e solicitacao de novo horario usando o fluxo real (fora do escopo desta correcao).

## Final status
Concluida.
