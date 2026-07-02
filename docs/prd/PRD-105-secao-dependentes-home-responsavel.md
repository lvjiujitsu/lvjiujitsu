# PRD-105: Seção "Meus dependentes" no home do responsável

## Summary
`HomeView.get_context_data()` já computa `context["dependents"]` (via `_build_dependents()`) com progresso de graduação, aulas de hoje e resumo de mensalidade de cada dependente — mas `templates/home/dashboard.html` nunca renderiza essa variável. Responsável não vê, na home, um resumo dos dependentes além da aba de mensalidade (`billing_tabs`, que só cobre cobrança).

## Demand type
Correção de UI (dado computado no backend sem entrada na interface — mesmo padrão da PRD-103).

## Current problem
- `system/views/home_views.py:167-168`: `if has_dependents(person): context["dependents"] = _build_dependents(person)`.
- `_build_dependents()` (linha 278) monta, por dependente: `person`, `belt_view` (dict pronto para SVG, nunca usado em nenhum template), `classes` (aulas de hoje), `billing` (via `_billing_summary`), `graduation_progress`.
- Busca em `templates/` confirma: nenhum template referencia `dependents`, `belt_view` ou o shape retornado por `_build_belt_view` (`body`/`tip`/`stripes`/`needs_border`/`grade`/`label`).
- `billing_tabs` (outro contexto, já renderizado) cobre cobrança por pessoa, mas não mostra graduação nem aulas de hoje de cada dependente na home.

## Goal
Responsável enxerga, na home, uma seção "Meus dependentes" com nome, faixa/grau atual e quantidade de aulas de hoje de cada dependente, com link para o detalhe completo da pessoa (`person-detail`).

## Context Ledger
### Files read in full
- `system/views/home_views.py` (`HomeView.get_context_data`, `_build_dependents`, `_billing_summary`, `_build_belt_view`)
- `templates/home/dashboard.html` (seção de mensalidade/`billing_tabs`, confirmando ausência de qualquer bloco de dependentes)
- `system/middleware.py` (confirma que `portal_is_student`/`is_student` reflete `ACCESS_STUDENT_AREA`, concedida a `GUARDIAN`, não "estar matriculado" — descartando uma hipótese inicial de bug em `_build_billing_context`)
- `system/constants.py` (`PERSON_TYPE_CAPABILITIES`, confirma a capability acima)

### Adjacent files consulted
- `system/services/graduation.py` (`compute_graduation_progress` — shape de `current_belt_rank`/`current_grade_number`)
- `system/services/class_calendar.py` (`get_today_classes_for_person`)

### Limitations found
- Nenhuma.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela solicitação atual ("finalize toda a implementação até não encontrar mais erros"). Achado veio de reauditoria dos painéis de professor/responsável; 5 dos 6 achados do agente de exploração foram descartados por serem falsos positivos (rotas de aulas em português já são um padrão histórico separado, fora de escopo desta PRD; a suposta "seção crítica ausente" foi refinada após verificação manual — `billing_tabs` já cobre cobrança, o que falta é graduação/aulas de hoje por dependente).

## Scope
- Simplificar `_build_dependents()` para não depender de `_build_belt_view()`/`_billing_summary()` (ambos sem consumidor real) — usar diretamente `graduation_progress.current_belt_rank`/`current_grade_number` e `get_active_membership()`.
- Renderizar seção "Meus dependentes" em `templates/home/dashboard.html`.

## Out of scope
- Migração de rotas de aulas para inglês (achado separado, não relacionado a este gap; não abrir PRD para isso agora pois é uma reestruturação de rotas maior e não um bug funcional).
- Redesenhar `billing_tabs`.

## Impacted files
- `system/views/home_views.py`
- `templates/home/dashboard.html`
- `system/tests/test_home_dashboard.py`

## Risks and edge cases
- Responsável sem dependentes: seção não deve aparecer (`dependents` vazio já tratado por `has_dependents`).
- Dependente sem faixa registrada: mostrar sem badge de faixa, sem quebrar o card.

## Rules and constraints
- UI em pt-BR, sem lógica de negócio no template (contagem/joins já vêm prontos da view).

## Plan
- [x] Simplificar `_build_dependents`.
- [x] Renderizar seção no dashboard.
- [x] Teste focado.
- [x] Validação visual.

## Test plan
### Tests to author
- Responsável com dependente vê seção "Meus dependentes" com nome e faixa do dependente.
- Pessoa sem dependentes não vê a seção.

### Execution authorization
Autorizada localmente.

### Execution evidence
- `system/tests/test_home_dependents_section.py` (2 testes): responsável vê a seção "Meus dependentes" com nome e faixa do dependente; pessoa sem dependentes não vê a seção.
- `.venv/Scripts/python.exe manage.py test system.tests.test_home_dependents_section --verbosity 2` — 2 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 348 testes OK (suíte completa).
- `.venv/Scripts/python.exe manage.py check` — 0 problemas.
- Validação ao vivo no navegador (relação demo André→Aline criada via ORM e removida após o teste, com restauração da conta de portal real do André via `seed_system_initial_teacher`): seção "Meus dependentes" mostra nome, faixa ("Roxa · 1º grau"), status de mensalidade ("Sem plano ativo") e "2 aulas hoje"; botão "Ver perfil" navega corretamente para `people/6/view/`; validado em desktop e mobile (375x812) sem overflow.

**Nota operacional**: durante a validação, descobri que o servidor de preview local roda com `--noreload` (`.claude/launch.json`), então mudanças em arquivos `.py` (diferente de templates) exigem reinício manual do servidor para surtir efeito — isso causou uma investigação de ~40 minutos de um "bug fantasma" (a seção não aparecia porque o processo do servidor ainda rodava o código antigo de `home_views.py`). Após reiniciar o servidor, a seção renderizou corretamente na primeira tentativa.

## Visual validation
Desktop, mobile, tema escuro, com dado real (responsável com dependente).

## ORM validation
`PersonRelationship` (RESPONSIBLE_FOR) usado para o teste.

## Quality validation
- `manage.py test system.tests.test_home_dashboard` e suíte completa.
- `manage.py check`.

## Evidence
- O link "Ver perfil" só aparece quando `can_access_people` é verdadeiro (capability `SUPPORT_PEOPLE`), já que `PersonDetailView` exige essa capability — um responsável puro (sem esse papel) veria a seção sem o link, evitando um 403.

## Implemented
- `system/views/home_views.py`: `_build_dependents()` simplificado para retornar `person`, `graduation_progress`, `today_classes`, `active_membership` diretamente; removidas as funções órfãs `_billing_summary()` e `_build_belt_view()` (nunca consumidas por nenhum template).
- `templates/home/dashboard.html`: nova seção "Meus dependentes", renderizada quando `dependents` é não vazio, com badge de faixa/grau, badge de status de mensalidade, contagem de aulas de hoje e link condicional para o perfil completo.
- `system/tests/test_home_dependents_section.py` (novo).

## Cleanup findings
- Removido código morto que só existia para alimentar `_build_dependents()` (a função `_build_belt_view` teria exigido uma nova partial SVG nunca criada); a simplificação evitou reintroduzir esse débito.
- Nenhum resíduo de dados de teste; conta de portal do André restaurada ao estado de seed original via `seed_system_initial_teacher` (idempotente).

## Follow-up PRDs
- Migração das rotas de aulas (`aulas/...`) para inglês com compat — achado real da reauditoria, mas fora de escopo aqui por ser uma reestruturação ampla de rotas; registrar para avaliação futura se a varredura continuar.

## Deviations from plan
_Nenhum até o momento._

## Pending
_Nenhuma até o momento._

## Final status
Concluída.
