# PRD-063: Integridade de exclusão em cascata de Person

## Summary

Validar de ponta a ponta, pela interface, a exclusão de `Person` no LV e tratar com segurança os modos de falha de integridade referencial. O mapa de `on_delete` mostra que `Person` é referenciada com mistura de `CASCADE`, `SET_NULL` e `PROTECT` em cerca de dez models; a `PersonDeleteView` é um `DeleteView` padrão que não trata `ProtectedError`, então apagar uma pessoa referenciada por relação `PROTECT` (ex.: professor em `ClassGroup.main_teacher`, instrutor em calendário, repasse `TeacherPayout`) falha sem mensagem clara ao administrador.

## Demand type

Auditoria de integridade + endurecimento de view + homologação por UI com mutação autorizada.

## Current problem

- `system/views/person_views.py::PersonDeleteView` é `DeleteView` puro (`AdministrativeRequiredMixin`), sem captura de `django.db.models.deletion.ProtectedError`.
- Mapa de `on_delete` referenciando `Person` (amostra confirmada por leitura):
  - `person.py`: `PortalAccount` (OneToOne, CASCADE), `PersonRelationship.source/target` (CASCADE), `person_type` (PROTECT).
  - `class_membership.py`: `ClassEnrollment` (CASCADE), `ClassInstructorAssignment` (CASCADE).
  - `class_group.py`: `main_teacher` (PROTECT), e segundo FK (PROTECT).
  - `asaas.py`: dois FKs CASCADE, um PROTECT, SET_NULL.
  - `registration_order.py`: CASCADE + SET_NULL + PROTECT.
  - `graduation.py`: CASCADE + PROTECT + SET_NULL.
  - `membership.py`: CASCADE + PROTECT.
  - `product_backorder.py`: CASCADE + PROTECT (variante).
  - `calendar.py`: múltiplos CASCADE/SET_NULL/PROTECT, instrutor PROTECT.
  - `trial_access.py`: CASCADE.
- Consequências não validadas:
  1. apagar **aluno** sem referências PROTECT deveria cascatear limpo (conta, matrículas, pré-pedidos, graduação, cobranças), mas isso não está comprovado por UI;
  2. apagar **professor/instrutor** referenciado por `PROTECT` deve ser **bloqueado** com mensagem clara — hoje provavelmente resulta em erro não tratado;
  3. não há comportamento definido nem teste para esses dois caminhos.

## Goal

1. Produzir o mapa completo e verificado de `on_delete` de toda referência a `Person`.
2. Definir o comportamento esperado: aluno sem PROTECT cascateia; pessoa com referência PROTECT é bloqueada com mensagem pt-BR explicando o que impede.
3. Endurecer `PersonDeleteView` para capturar `ProtectedError` e exibir mensagem amigável (sem 500), preservando permissão administrativa.
4. Cobrir com teste os dois caminhos (cascata bem-sucedida e bloqueio por PROTECT).
5. Homologar pela UI a exclusão de uma pessoa de teste em desktop e mobile, com evidência visual e console limpo.

## Context Ledger

### Files read in full

- `system/views/person_views.py` (parcial: assinaturas de `PersonDeleteView`)
- `system/models/person.py`
- `system/models/class_membership.py`
- `system/models/class_group.py`

### Adjacent files consulted

- `system/models/asaas.py`, `registration_order.py`, `graduation.py`, `membership.py`, `product_backorder.py`, `calendar.py`, `trial_access.py` (linhas de `on_delete`)
- `templates/people/person_confirm_delete.html`

### Internet / official documentation

- [Django 5.2 — on_delete / ProtectedError](https://docs.djangoproject.com/en/5.2/ref/models/fields/#django.db.models.ForeignKey.on_delete)
- [Django 5.2 — deletion / collector](https://docs.djangoproject.com/en/5.2/topics/db/queries/#deleting-objects)
- [Django 5.2 — DeleteView](https://docs.djangoproject.com/en/5.2/ref/class-based-views/generic-editing/#deleteview)
- [Django 5.2 — messages framework](https://docs.djangoproject.com/en/5.2/ref/contrib/messages/)

### Context7 / MCPs / tools verified

- Context7 a consultar para Django deletion/ProtectedError na execução.
- Browser interno disponível em `http://127.0.0.1:8000` para homologação.
- PowerShell, Git e `rg` disponíveis.

### Limitations found

- A exclusão é mutação real; exige autorização explícita e pessoa de teste dedicada.
- O conjunto exato de relações PROTECT que bloqueiam deve ser confirmado na execução, não presumido por amostra.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: validar e endurecer a exclusão de `Person`, tratando `ProtectedError` e homologando por UI.
- User approval: solicitação explícita de PRDs completos para implementação sequencial.
- Date: 2026-06-28.

## Execution prompt

### Persona

Engenheiro Django responsável por integridade referencial e fluxo administrativo de pessoas.

### Action

Mapear `on_delete`, definir comportamento esperado, endurecer a view, escrever testes e homologar a exclusão pela UI.

### Context

LV é monólito Django 5.2; `Person` é o agregado central referenciado por matrículas, repasses, graduação, calendário, pedidos e cobranças, com `on_delete` heterogêneo.

### Constraints

- Não criar migrations (não alterar `on_delete` sem decisão de schema do usuário).
- Não executar exclusão sem autorização e pessoa de teste.
- Não mascarar erro; mensagem deve ser específica e em pt-BR.
- Preservar `AdministrativeRequiredMixin`.

### Acceptance criteria

- [x] Mapa completo e verificado de toda referência a `Person` com seu `on_delete`.
- [x] Comportamento esperado documentado para os dois caminhos (cascata x bloqueio).
- [x] `PersonDeleteView` captura `ProtectedError` e renderiza mensagem pt-BR sem 500.
- [ ] Aluno sem referência PROTECT é excluído e cascata cobre conta, matrículas, relacionamentos e derivados esperados.
- [ ] Pessoa com referência PROTECT é bloqueada com mensagem que nomeia o impedimento.
- [x] Testes cobrem os dois caminhos.
- [ ] Homologação por UI em desktop e mobile com screenshot e console limpo.

### Expected evidence

- Mapa de `on_delete`.
- Saída dos testes (após autorização).
- Screenshot da exclusão bem-sucedida e da mensagem de bloqueio.
- Snapshot ORM read-only confirmando cascata e ausência de órfãos.

### Output format

Resumo curto, mapa, evidências, limitações e status.

## Scope

- `system/views/person_views.py` (`PersonDeleteView`)
- `templates/people/person_confirm_delete.html` (mensagem de bloqueio, se necessário)
- `system/tests/test_person_delete.py` (novo)
- este PRD.

## Out of scope

- Alteração de `on_delete` nos models (mudança de schema; decisão do usuário).
- Redesign da listagem/detalhe de pessoas.
- Exclusão de professores/instrutores em produção/HG.

## Impacted files

- `system/views/person_views.py`
- `templates/people/person_confirm_delete.html`
- `system/tests/test_person_delete.py` (novo)
- este PRD.

## Risks and edge cases

- Cascata excessiva: apagar aluno pode remover histórico financeiro/graduação que deveria ser preservado — avaliar se algum CASCADE deveria ser SET_NULL (registrar como follow-up de schema, não alterar aqui).
- `PROTECT` em `person_type` nunca bloqueia exclusão de pessoa (é o lado inverso), mas `main_teacher`/instrutor/repasse sim.
- Mensagem de bloqueio não pode vazar nomes técnicos de model ao usuário final.
- Exclusão em massa pela listagem, se existir, precisa do mesmo tratamento.

## Rules and constraints

- Menor mudança correta; causa raiz.
- Sem migration; sem mutação não autorizada.
- Mensagem específica, sem erro mascarado.
- Permissão no backend.

## Plan

- [x] Context and research (mapa completo de on_delete)
- [x] Definir comportamento esperado dos dois caminhos
- [x] Escrever testes (test-first)
- [x] Endurecer `PersonDeleteView`
- [ ] Solicitar autorização e executar testes
- [ ] Homologar por UI desktop/mobile
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

- `test_person_delete.py`: exclusão de aluno sem PROTECT (cascata esperada, sem órfãos); exclusão de pessoa com referência PROTECT (bloqueio + mensagem); resposta da view sem 500.

### Execution authorization

- Status: não autorizada nesta execução. Testes escritos antes do código, não executados por política.

### Execution evidence

Teste escrito, não executado por política. Não há declaração de Red/Green.

## Visual validation

- Servidor local em `127.0.0.1:8000`.
- Excluir pessoa de teste sem PROTECT → confirmar remoção e redirecionamento.
- Tentar excluir pessoa com PROTECT → confirmar mensagem de bloqueio.
- Desktop e mobile, tema claro e escuro, console sem erro, screenshots.

## ORM validation

- Introspecção read-only executada para mapear FKs de `Person`.
- Snapshot antes/depois de exclusão real não executado porque exigiria mutação de pessoa de teste.

## Quality validation

- `manage.py check` (após autorização).
- Revisão do diff e do mapa.
- `git diff --check`.

## Evidence

Mapa read-only por introspecção Django:

| Referência | Campo | `on_delete` |
|---|---|---|
| `ClassCheckin` | `approved_by` | `SET_NULL` |
| `ClassCheckin` | `person` | `CASCADE` |
| `ClassEnrollment` | `person` | `CASCADE` |
| `ClassGroup` | `main_teacher` | `PROTECT` |
| `ClassInstructorAssignment` | `person` | `CASCADE` |
| `Graduation` | `awarded_by` | `SET_NULL` |
| `Graduation` | `person` | `CASCADE` |
| `Membership` | `person` | `CASCADE` |
| `PersonRelationship` | `source_person` | `CASCADE` |
| `PersonRelationship` | `target_person` | `CASCADE` |
| `PortalAccount` | `person` | `CASCADE` |
| `PreRegistration` | `finalized_person` | `SET_NULL` |
| `ProductBackorder` | `person` | `CASCADE` |
| `RegistrationOrder` | `person` | `CASCADE` |
| `SpecialClass` | `teacher` | `PROTECT` |
| `SpecialClassCheckin` | `approved_by` | `SET_NULL` |
| `SpecialClassCheckin` | `person` | `CASCADE` |
| `TeacherBankAccount` | `person` | `CASCADE` |
| `TeacherPayout` | `person` | `PROTECT` |
| `TeacherPayrollConfig` | `person` | `CASCADE` |
| `TrialAccessGrant` | `person` | `CASCADE` |

Validações executadas:

- `python manage.py check` retornou `System check identified no issues (0 silenced).`
- `python -m py_compile system/tests/test_person_delete.py system/tests/test_register_wizard_contract.py` retornou exit code 0.
- `system/tests/test_person_delete.py` foi criado com os cenários de cascata de aluno e bloqueio por `ClassGroup.main_teacher`, mas não foi executado.

## Implemented

- `PersonDeleteView.form_valid()` agora captura `ProtectedError`, redireciona para o detalhe da pessoa preservada e exibe mensagem pt-BR com o tipo de vínculo protegido.
- Exclusão sem bloqueio mantém redirecionamento para a listagem e passa a exibir mensagem de sucesso.
- `_format_person_delete_blockers()` traduz os bloqueios conhecidos: turma principal, aula especial e repasse financeiro.
- `system/tests/test_person_delete.py` cobre contrato de cascata de aluno com conta/matrícula/relacionamento e bloqueio de professor vinculado a turma.

## Cleanup findings

- A listagem e o detalhe de pessoas já exibiam mensagens do Django; nenhuma alteração de template foi necessária para este ajuste.
- Nenhuma migration ou mudança de schema foi criada.
- Nenhuma pessoa de teste foi criada no banco local.

## Follow-up PRDs

- Possível PRD de schema para reavaliar CASCADE x SET_NULL onde a cascata apaga histórico que deveria ser preservado (decisão do usuário, ciclo destrutivo).

## Deviations from plan

- Homologação por UI e execução de testes não foram feitas porque exigem autorização explícita para mutação/testes.

## Pending

- Autorização para executar `system.tests.test_person_delete`.
- Autorização para criar/excluir pessoa de teste e validar o fluxo no browser desktop/mobile.

## Final status

**Concluída com limitações** — implementação e testes escritos; validação real de teste/UI/mutação permanece pendente por política de autorização.
