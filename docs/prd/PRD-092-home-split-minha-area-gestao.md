# PRD-092: Home split Minha área e Gestão

## Summary
Corrigir e completar a experiência dual na home quando a pessoa treina e também exerce gestão ou apoio (caso Aline, administrativo titular, responsável com dependentes). O template atual abre “Minha área” e “Gestão” com IDs duplicados e seção de gestão incompleta no modo split.

## Demand type
Correção de UI + ajuste de contexto na view.

## Current problem
- `dashboard.html` repete `id="staff-area-title"` e estrutura `<section>` inconsistente entre `needs_split` e `show_staff_area` (`dashboard.html:64-75`).
- `home_views.py` mistura `today_classes` administrativo com `my_classes` de aluno sem separação clara no split.
- Usuário reporta home administrativo split Minha área / Gestão disfuncional.

## Goal
Usuário com treino + gestão vê:
- **Minha área:** turmas de aluno, graduação, check-in, dependentes.
- **Gestão:** acesso rápido, financeiro resumo, turmas do dia como staff, aprovações.

Sem IDs duplicados, sem conteúdo de gestão dentro do bloco pessoal.

## Context Ledger
### Files read in full
- `templates/home/dashboard.html`
- `templates/home/partials/today_classes_section.html`
- `system/views/home_views.py`
- `system/tests/test_home_dashboard.py`
- `docs/prd/PRD-014-painel-administrativo-como-pessoa.md`

### Adjacent files consulted
- `static/system/js/home/dashboard.js`
- `docs/prd/AUDIT-2026-06-30-master-findings.md`

### Internet / official documentation
- WCAG 2.2 unique id: https://www.w3.org/WAI/WCAG22/Understanding/parsing

### Context7 / MCPs / tools verified
- Não aplicável.

### Limitations found
- Redesign amplo pode exigir aprovação visual prévia (`lv-ui-delivery`).

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved
Autorizado pela auditoria e problema explícito do usuário.

## Execution prompt
### Persona
Implementador UI Django com foco em papéis acumuláveis.

### Action
Refatorar template e contexto para split estável com landmarks ARIA únicos.

### Context
`needs_split`, `has_personal_area`, `show_staff_area` em `HomeView`.

### Constraints
- Preservar funcionalidades existentes da home unificada.
- Tokens CSS existentes; sem KPI novo não solicitado.

### Acceptance criteria
- [ ] HTML válido: um único `id` por elemento; seções fechadas corretamente.
- [ ] Aline (aluno + class-assistant): “Minha área” com check-in de aluno; “Gestão” sem misturar lista de aulas pessoais.
- [ ] Administrativo que não treina mantém hint “sem área pessoal de treino”.
- [ ] Teste de regressão atualiza asserts de IDs removidos (`staff-area-title` duplicado).
- [ ] Desktop e mobile validados no navegador.

### Expected evidence
- Screenshots split desktop/mobile.
- Testes home verdes.

### Output format
Evidência na PRD.

## Scope
- `home_views.py` contexto de split.
- `dashboard.html` e partials se necessário.
- Testes `test_home_dashboard.py`.

## Out of scope
- Regra de check-in professor (PRD-094).
- Redesign financeiro completo.

## Impacted files
- `templates/home/dashboard.html`
- `system/views/home_views.py`
- `system/tests/test_home_dashboard.py`
- `static/system/css/home/dashboard.css` (ajustes mínimos)

## Risks and edge cases
- Responsável com dependentes: dependentes ficam em qual bloco?
- Admin técnico sem `portal_person`.

## Rules and constraints
- Wireframe aprovado antes do código visual.

## Plan
1. [x] Wireframe com regiões Minha área / Gestão (já existente no template; validado como correto).
2. [x] Teste falhando para conteúdo Aline (reproduzido ao vivo antes de codar).
3. [x] Ajuste de contexto (não foi necessário ajustar o template de split em si — ver Evidence).
4. [x] Validação browser.

## Test plan
### Tests to author
- `test_dual_role_student_sees_own_checkin_merged_with_support_classes` (implementado na PRD-094, cobre o mesmo cenário)

### Execution authorization
Local autorizado.

### Execution evidence
- Esta PRD e a PRD-094 descrevem o mesmo sintoma observado pelo usuário (Aline não vê check-in) a partir de duas hipóteses diferentes. Investigação real mostrou:
  1. **IDs duplicados (`staff-area-title`)**: não é um bug em tempo de execução. O template usa um único bloco `{% if needs_split %}...{% elif show_staff_area and not has_personal_area %}...{% endif %}` — as duas ocorrências de `id="staff-area-title"` estão em ramos mutuamente exclusivos; nunca renderizam juntas na mesma resposta. Confirmado lendo `templates/home/dashboard.html` linhas 64-75 e o fechamento correspondente na linha 516 (`{% if needs_split or show_staff_area and not has_personal_area %}`).
  2. **Conteúdo de gestão misturado na área pessoal**: também não reproduziu — `personal_today_classes` já é estritamente `my_classes` (sempre `entry_role="student"`).
  3. **O bug real**: para Aline (aluna + apoio de turma, sem ser administrativa), `needs_split` nunca ativa (só ativa para administrativos ou responsável com dependentes) — então ela cai no branch "não dividido", que sobrescrevia `today_classes` com a visão de instrutor/apoio, **descartando** sua própria lista de check-in. Corrigido na PRD-094 (mesmo arquivo `home_views.py`).
- `.venv/Scripts/python.exe manage.py test system.tests.test_home_dashboard --verbosity 2` — 5 testes OK.
- `.venv/Scripts/python.exe manage.py test system --verbosity 1` — 326 testes OK.

## Visual validation
## Wireframe
### Região: Cabeçalho
- Saudação, badges de papel (Aluno, Apoio de turma, Administrativo).

### Região: Minha área (condicional `needs_split`)
- Turmas de hoje como aluno com ação check-in.
- Graduação recolhida.

### Região: Gestão
- Acesso rápido, resumo financeiro, turmas staff/aprovações.

### Estados
- Só gestão; só aluno; split completo.

## ORM validation
Validado com a seed real da Aline (`920.000.011-81`) no banco de desenvolvimento local.

## Quality validation
- `manage.py check` — 0 problemas.

## Evidence
- Ver Execution evidence acima. A implementação real ficou em `system/views/home_views.py` (PRD-094); esta PRD documenta a investigação e descarta as duas primeiras hipóteses (IDs duplicados, mistura de conteúdo) como falsos positivos, confirmando a terceira (roteamento de lista) como a causa raiz real.

## Implemented
- Ver PRD-094 (`_merge_class_entries` em `system/views/home_views.py`). Nenhuma mudança de template foi necessária nesta PRD — a estrutura HTML do split já estava correta.

## Cleanup findings
- Nenhum resíduo.

## Follow-up PRDs
- Nenhum.

## Deviations from plan
- O plano original presumia um bug de template (IDs duplicados/estrutura HTML); a investigação real mostrou que o template já estava correto e o bug estava no Python (`home_views.py`). Documentado aqui para não repetir a investigação de template no futuro.

## Pending
- Nenhum.

## Final status
Concluída.
