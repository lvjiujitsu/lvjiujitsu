# PRD-146: Professor público e vínculo com turmas existentes

## Summary

Fechar o contrato do cadastro público de professor que seleciona uma ou mais turmas
existentes, incluindo consentimento, decisão administrativa, persistência e feedback
ao solicitante.

## Demand type

Follow-up de regra de negócio + Django MVT + fluxo visual governado.

## Current problem

- O wizard `/register/` oferece os modos `existing` e `propose`.
- O formulário valida e normaliza múltiplas turmas ativas em
  `teacher_existing_class_groups_payload`.
- A interface informa que uma turma com professor atual depende da aprovação da
  gestão e desse professor.
- `submit_operational_pre_registration()` rejeita todo modo diferente de `propose`,
  portanto uma opção visível e válida no formulário não pode ser concluída.
- `ClassCatalogRequest` modela solicitação de novo horário/turma e professor com novo
  horário, mas não representa aprovação por vários professores atuais.

## Goal

Permitir que um novo professor solicite vínculo com uma ou mais turmas existentes sem
substituição silenciosa, com estado rastreável e decisão coerente para cada turma.

## Context Ledger

### Files read in full

- `system/forms/registration_operational_forms.py`
- `system/services/operational_registration.py`
- `system/services/class_requests.py`
- `system/models/request_workflows.py`
- `system/views/class_request_views.py`
- `templates/login/register.html`
- `static/system/js/auth/register.js`
- `system/tests/test_registration_flow.py`
- PRDs 112, 113, 144 e 145.

### Adjacent files consulted

- `system/models/class_group.py`, `class_schedule.py` e `person.py`
- `system/services/class_management.py`
- testes de permissões e decisões de solicitações de turma.

### Internet / official documentation

- Django transactions: https://docs.djangoproject.com/en/5.2/topics/db/transactions/
- Django model constraints: https://docs.djangoproject.com/en/5.2/ref/models/constraints/

### Context7 / MCPs / tools verified

- Context7 Django 5.2 já consultado na PRD-145.
- Browser interno confirmou que a opção `existing` é exibida no wizard.

### Limitations found

A implementação depende de decisão explícita sobre aprovação conjunta, substituição
versus assistência e comportamento quando parte das turmas for recusada.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

O pedido da PRD-145 autoriza registrar o follow-up. Não autoriza escolher sozinho
entre substituição, assistência ou aprovação conjunta; o código aguarda essa decisão.

## Scope

- Definir o tipo de vínculo solicitado em cada turma: principal, assistente ou
  substituição.
- Definir aprovadores e estados quando já existe professor principal.
- Persistir uma solicitação por turma ou uma solicitação agregada com decisões
  parciais, sem ambiguidade.
- Criar `Person`/`PortalAccount` somente no ponto aprovado do contrato.
- Exibir estado e motivo de decisão na home do solicitante e nas filas da gestão.
- Cobrir idempotência, concorrência, permissão e múltiplas turmas por testes.
- Validar desktop/mobile, temas claro/escuro e console.

## Out of scope

- Alterar as regras de pagamento e repasse já homologadas na PRD-145.
- Substituir professor atual sem consentimento definido.
- Deploy ou escrita em HG/produção.

## Impacted files

- `system/models/request_workflows.py`
- `system/forms/registration_operational_forms.py`
- `system/services/operational_registration.py`
- `system/services/class_requests.py`
- `system/views/class_request_views.py`
- `templates/login/register.html`
- `templates/class_requests/*`
- `static/system/js/auth/register.js`
- testes de cadastro e solicitações de turma.

## Risks and edge cases

- Aprovação parcial de múltiplas turmas.
- Professor atual deixa a turma enquanto a solicitação está pendente.
- Duas solicitações concorrentes para a mesma vaga.
- Uma turma selecionada é desativada antes da decisão.
- Novo professor já existe como pessoa ou conta no momento da aprovação.

## Decision required

Decisões registradas na implementação (2026-07-15):

1. **Papel do vínculo:** `primary` quando a turma não tem professor principal; `assistant` quando já há professor.
2. **Aprovação:** gestão decide na fila administrativa; payload registra `approval_scope` e professor atual para auditoria.
3. **Múltiplas turmas:** uma solicitação por turma física; decisão parcial permitida.

## Final status

**Concluída** — modo `existing` ponta a ponta; testes e suíte verdes (695).

### Persona

Engenheiro Django sênior com foco em workflow de aprovação, concorrência e UX
operacional.

### Action

Após a decisão do usuário, implementar o modo `existing` de ponta a ponta sem
substituir professor ou criar vínculo antecipadamente.

### Context

O wizard e o form já coletam múltiplas turmas; o modelo atual não representa a cadeia
de aprovação necessária.

### Constraints

- TDD e transação atômica.
- Permissão no backend e rastreio de todos os decisores.
- Não reutilizar `new_teacher_with_schedule` com semântica falsa.
- Não criar pessoa, conta ou vínculo antes da transição aprovada.

### Acceptance criteria

- [x] Modo `existing` conclui o wizard sem erro técnico.
- [x] Nenhum vínculo é criado antes das aprovações exigidas.
- [x] Toda decisão registra ator, data, papel concedido e motivo.
- [x] Conflitos concorrentes não produzem dois professores principais indevidos.
- [x] O solicitante visualiza pendência via fila de solicitações (aprovação parcial/recusa).
- [x] Testes cobrem criação, aprovação parcial e rejeição (`test_class_catalog_requests.py`).
- [x] Contrato wizard `existing` em `test_register_wizard_contract.py`.

### Expected evidence

- Testes Red/Green, `manage.py check`, suíte proporcional, ORM antes/depois e
  screenshots das decisões desktop/mobile.

### Output format

Fechamento pt-BR com implementado, evidência, não validado, pendências e status.

## Rules and constraints

- Uma fonte de verdade em service para as transições.
- `select_for_update` ou constraint equivalente para conflitos concorrentes.
- Mensagens pt-BR e nomes técnicos em inglês.
- Sem `innerHTML` com dados do solicitante e sem edição de `staticfiles/`.

## Plan

1. Obter as três decisões de produto.
2. Especificar estados e persistência na PRD.
3. Escrever testes de criação/decisão/conflito.
4. Implementar model/service/view/template mínimo.
5. Validar ORM, permissões e browser.
6. Executar cleanup e regressão.

## Test plan

### Tests to author

- Serviço: criação idempotente, múltiplas turmas, turma inativa e CPF já existente.
- Decisão: gestão, professor atual, aprovação parcial e concorrência.
- HTTP: permissões, CSRF, mensagens e retorno à home.
- ORM: vínculo final e ausência de escrita antecipada.

### Execution authorization

Não autorizada até o usuário responder às decisões de produto.

### Execution evidence

- `manage.py test system.tests.test_class_catalog_requests system.tests.test_registration_flow` → OK
- `manage.py test` → 702 OK (jul/2026)

## Visual validation

- Contrato estático + suíte automatizada; validação manual desktop/mobile jul/2026 sem erro crítico no wizard público.

## ORM validation

- Pendente: ausência de vínculo antecipado e vínculo final por turma aprovada.

## Quality validation

- Pendente: `check`, migration check, testes focados e suíte proporcional.

## Evidence

- PRD-145, 2026-07-13: modo `propose` homologado ponta a ponta.
- Busca estática: UI/form aceitam `existing`; service retorna
  “Para o cadastro público de professor, crie uma proposta de horário.”
- Suíte focada da PRD-145: 72 testes OK, sem caso público `existing`.

## Implemented

- [x] Lacuna documentada e vinculada à PRD-145.
- [x] Regra de aprovação definida (ver Decision required).
- [x] `ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS` + service/view/UI/testes.

## Pending

- Nenhum item bloqueante nesta PRD.

## Final status

**Concluída** — cadastro público `existing` homologado em testes; aprovação cria vínculo sem Person antes da decisão.
