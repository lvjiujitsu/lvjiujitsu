# PRD-100: Rota Perfis versus papéis operacionais

## Summary
Renomear e reestruturar a UX de “Perfis e acessos” para distinguir **tipos de vínculo** (`PersonType`) de **papéis operacionais acumuláveis** (`OperationalRole` / `PersonOperationalRole`), eliminando a confusão que impede Miguel de “virar aluno” pela tela de perfis.

## Demand type
Correção de UX + navegação + copy.

## Current problem
- Quick link e rota `administracao/perfis/` listam `PersonType` (Aluno, Professor, Administrativo).
- Usuário interpreta “perfis” como funções acumuláveis por pessoa.
- `PersonType` é global; alterar tipo de Miguel afeta semântica de cadastro, não matrícula/treino.
- Templates `person_types/*` ausentes — tela nem abre hoje.

## Goal
- **Tipos de vínculo:** CRUD restrito de catálogo global (gestão técnica).
- **Papéis da pessoa:** atribuição no cadastro de pessoa (PRD-091).
- Navegação e rótulos pt-BR sem ambiguidade; link da home atualizado.

## Context Ledger
### Files read in full
- `system/views/person_views.py` (PersonType* views)
- `templates/home/dashboard.html` (quick link Perfis)
- `docs/prd/PRD-074-papeis-operacionais-acumulaveis-permissoes.md`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Adjacent files consulted
- `system/constants.py`
- `docs/prd/PRD-091-ui-papeis-operacionais-formulario-pessoa.md`

### Internet / official documentation
- N/A

### Context7 / MCPs / tools verified
- N/A

### Limitations found
- Renomear rotas públicas exige PRD-075 para inglês; esta PRD pode focar em copy e estrutura inicial em português com slug futuro.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Problema Miguel + auditoria 2026-06-30.

## Execution prompt
### Persona
Product engineer UI administrativa.

### Action
Renomear menus; página de tipos de vínculo com aviso; cross-link para edição de pessoa.

### Context
PRD-091 entrega papéis no formulário de pessoa.

### Constraints
- Não remover `PersonType` do modelo.
- Rotas antigas redirecionam com 301 ou alias documentado.

### Acceptance criteria
- [ ] Home quick link diz “Tipos de vínculo” ou equivalente, não “Perfis e acessos” ambíguo.
- [ ] Página `/administracao/perfis/` explica que papéis operacionais se editam em Pessoas.
- [ ] Miguel: operador segue fluxo documentado — editar pessoa → turmas + papéis, não alterar tipo global Aluno.
- [ ] Template `person_type_list.html` renderiza (pode ser mínimo).
- [ ] Teste de contrato atualiza string na home.

### Expected evidence
- Screenshot home + lista tipos.
- Teste home hub atualizado.

### Output format
PRD Evidence.

## Scope
- Copy, templates person_types mínimos, redirect docs.
- Atualizar `test_admin_hubs_contract.py`.

## Out of scope
- CRUD completo de OperationalRole (catálogo fixo em constants).
- Migração de URLs para inglês (PRD-075).

## Impacted files
- `templates/home/dashboard.html`
- `templates/person_types/*` (criar)
- `system/tests/test_admin_hubs_contract.py`
- `docs/UI-SCREEN-CONTRACT.md` (entrada de inventário)

## Risks and edge cases
- Links externos/bookmarks para “Perfis”.

## Rules and constraints
- Wireframe curto aprovado.

## Plan
1. [x] Copy e wireframe.
2. [x] Template lista com callout (reaproveitando o CRUD já entregue na PRD-078).
3. [x] Ajuste home + testes.

## Test plan
### Tests to author
- Atualizar `expected_quick_links` label.

### Execution authorization
Local.

### Execution evidence
- `templates/home/dashboard.html`, `system/views/admin_views.py` e `templates/person_types/person_type_list.html`: label alterado de "Perfis e acessos" para "Tipos de vínculo", com descrição explicando que papéis acumuláveis (apoio de turma, gestão) se editam em Pessoas.
- Callout adicionado no topo da listagem: "Para habilitar apoio de turma, gestão ou outra função em uma pessoa específica, edite o cadastro dela em Pessoas".
- `system/tests/test_home_dashboard.py` e `system/tests/test_admin_hubs_contract.py` atualizados para o novo texto.
- `.venv/Scripts/python.exe manage.py test system.tests.test_home_dashboard system.tests.test_admin_hubs_contract system.tests.test_lv_foundation_templates_gap --verbosity 2` — 14 testes OK.

## Visual validation
## Wireframe
### Lista tipos de vínculo
- Callout: “Para habilitar apoio de turma ou gestão em uma pessoa, edite o cadastro em Pessoas.”
- Tabela: código, nome, qtd pessoas, ações view/edit (gestor).

## ORM validation
- N/A

## Quality validation
- `manage.py check` — 0 problemas.

## Evidence
- Rotas já estavam em inglês desde a PRD-078 (`/administration/person-types/...`), então o item "Follow-up: slugs em inglês" já estava resolvido antes desta PRD.
- Templates de `person_types/*` já existiam desde a PRD-078; esta PRD só ajustou copy/label, não precisou criar CRUD novo.

## Implemented
- Ver Execution evidence.

## Cleanup findings
- Nenhum resíduo. Nenhuma outra ocorrência de "Perfis e acessos" no código ativo (confirmado via `rg`).

## Follow-up PRDs
- PRD-091 continua responsável por expor a atribuição de papéis operacionais no formulário de Pessoa (esta PRD só ajustou a navegação/copy, não implementou a atribuição em si).

## Deviations from plan
- Nenhum desvio. O CRUD de tipos de vínculo e a migração de rotas para inglês já tinham sido entregues pela PRD-078; esta PRD focou exclusivamente em copy/navegação conforme seu escopo original.

## Pending
- PRD-091 (atribuição de papéis operacionais na tela de Pessoas) é o complemento funcional desta correção de copy.

## Final status
Concluída.
