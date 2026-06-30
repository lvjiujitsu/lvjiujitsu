# PRD-072: Correcoes da home do professor, presenca e mobile

## Summary
Corrigir observacoes visuais e funcionais feitas no navegador interno sobre a Home do professor: permitir desfazer presenca e indicar substituto da aula do dia, melhorar filtros do historico de presencas, trocar acoes longas por icones no mobile e corrigir o modal de historico de graduacoes em viewport estreita.

## Demand type
Correcao funcional Django + ajuste de UI responsiva.

## Current problem
- O professor consegue registrar presenca, mas nao consegue cancelar a propria presenca quando ocorre imprevisto.
- Nao existe representacao estruturada para professor substituto por sessao diaria.
- Os filtros do historico usam textos longos como "Todas as turmas", parecendo texto corrido dentro do modal.
- Acoes "Historico", "Criar aulao" e "Cronograma" quebram a largura no celular.
- O modal de historico de graduacoes fica grande e com scroll visual ruim no mobile.
- O JS da presenca usa `innerHTML` para atualizar UI, divergindo do contrato local.

## Goal
Implementar fluxo seguro para presenca do professor na aula do dia, com cancelamento e substituto, e corrigir os problemas responsivos/modais apontados sem alterar os demais papeis da Home.

## Context Ledger
### Files read in full
- `AGENTS.md`
- `CLAUDE.md`
- `docs/PRD-STANDARD.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `.agents/skills/lv-task-intake/SKILL.md`
- `.agents/skills/lv-prd/SKILL.md`
- `.agents/skills/lv-ui-delivery/SKILL.md`
- `.agents/skills/lv-django-delivery/SKILL.md`
- `.agents/skills/lv-cleanup-audit/SKILL.md`
- `docs/prd/PRD-018-botoes-mobile-home-professor.md`
- `system/views/calendar_views.py`
- `system/services/class_calendar.py`
- `system/models/calendar.py`
- `system/models/class_group.py`
- `system/models/class_schedule.py`
- `system/models/person.py`
- `system/forms/class_forms.py`
- `system/tests/test_calendar.py`

### Adjacent files consulted
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- `system/views/home_views.py`
- `system/urls.py`
- Projeto irmao `C:/Users/whsf/Documents/GitHub/visary` para padrao de acoes iconicas (`icon-action`, `btn-icon`, `aria-label`).

### Internet / official documentation
- Django 5.2 class-based views: https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/

### Context7 / MCPs / tools verified
- Context7 `/websites/djangoproject_en_5_2`: confirmado fluxo de `View.dispatch`, POST em CBV e Test Client.
- PowerShell local e `.venv` disponiveis.
- Browser interno disponivel em `http://127.0.0.1:8000/home/`.

### Limitations found
- A substituicao real por professor no dia nao cabe no schema atual sem novo campo de sessao diaria.
- A mudanca de schema sera local e pequena; HG/producao ficam fora do escopo.

## Required skills
- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved
A solicitacao "continue foque nas correcoes enviadas" autoriza implementar as correcoes apontadas nos comentarios do navegador. Mudanca de ambiente remoto, deploy, HG e producao nao estao autorizados.

## Execution prompt
### Persona
Agente Django MVT focado em fluxo operacional de aula e UI mobile.

### Action
Implementar as correcoes da Home do professor mantendo permissao server-side, CSRF e responsividade.

### Context
O sistema usa Django 5.2, templates server-rendered e Home unica em `/home/`. A presenca do professor ja usa `ClassSession.instructor_present` e `SpecialClass.instructor_present`.

### Constraints
- Sem regra de negocio em template/JS.
- Sem `innerHTML` para atualizar dados.
- Sem editar `staticfiles/`.
- Criar migration local somente para o campo de substituto necessario.
- Validar primeiro o papel professor, pois os comentarios vieram desse caso.

### Acceptance criteria
- [x] Professor presente ve acao para cancelar propria presenca.
- [x] Professor pode indicar professor substituto ativo para aula regular do dia.
- [x] Professor substituto passa a ver a aula do dia como instrutor e pode ser autorizado pelas checagens de ownership.
- [x] Filtros do historico usam valor default "Todos".
- [x] Acoes do header de Turmas no mobile viram botoes iconicos 44x44, sem overflow horizontal.
- [x] Modal de historico de graduacoes fica sobre a tela com altura controlada e scroll interno no mobile.
- [x] `dashboard.js` nao usa `innerHTML` no fluxo alterado.
- [x] Testes focados e `manage.py check` passam.
- [x] Browser interno valida desktop/mobile e console sem erro critico.

### Expected evidence
- Red focado antes da implementacao.
- Green focado depois.
- `manage.py check`.
- Validacao browser professor desktop/mobile com screenshots ou snapshots.
- Diff auditado.

### Output format
Codigo implementado, evidencias reais, limitacoes e status.

## Scope
- `system/models/calendar.py`
- `system/migrations/0002_classsession_substitute_teacher.py`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/urls.py`
- `system/tests/test_calendar.py`
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- Esta PRD.

## Out of scope
- Deploy, HG ou producao.
- Regras de repasse por substituicao.
- Notificacao para aluno/professor.
- Reescrever o calendario completo.
- Validar todos os papeis da Home nesta rodada.

## Impacted files
- `system/models/calendar.py`
- `system/migrations/0002_classsession_substitute_teacher.py`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/views/home_views.py`
- `system/urls.py`
- `system/tests/test_calendar.py`
- `templates/home/dashboard.html`
- `static/system/css/home/dashboard.css`
- `static/system/js/home/dashboard.js`
- `docs/prd/PRD-072-correcoes-home-professor-presenca-mobile.md`

## Risks and edge cases
- Professor substituto precisa estar ativo e ter tipo `instructor`.
- Professor original nao deve indicar a si mesmo como substituto.
- Aula cancelada nao deve aceitar presenca/substituicao como se estivesse ativa.
- Aulon ja possui professor proprio; substituicao de aulon fica fora do schema e continua pelo campo `teacher`.
- Mobile 375px nao pode ter overflow horizontal por botoes de header.

## Rules and constraints
- SDD antes de codigo.
- TDD proporcional.
- Menor mudanca correta.
- Permissao no backend.
- Validacao visual obrigatoria.

## Visual hierarchy
- Header de secao mantem titulo a esquerda.
- Desktop preserva botoes texto.
- Mobile converte acoes de secao em botoes quadrados com icone e `aria-label`/`title`.
- Presenca do professor fica junto ao card da aula, como estado operacional.
- Modal de graduacao usa header fixo visual, corpo com scroll e largura contida.

## Wireframe
### Turmas de hoje - mobile
- Linha 1: chevron + "Turmas de hoje" + acoes iconicas: historico, aulao, cronograma.
- Card da aula: horario, nome, contadores.
- Presenca: pill "Presente 12:08" + botoes "Cancelar" e "Trocar professor".

### Modal de substituicao
- Titulo: "Indicar substituto".
- Campo: Professor substituto.
- Acoes: Cancelar, Salvar.

### Modal historico de graduacoes - mobile
- Overlay escuro.
- Sheet com `max-height`.
- Header e botao fechar.
- Lista rolavel, cada item em linha compacta.

## State machine
### Presenca do professor
- `not_present`: botao "Registrar presenca".
- `present`: pill "Presente HH:mm" + "Cancelar" + "Trocar professor".
- `cancelled`: sem acao de presenca.
- `substituted`: professor original ve substituto indicado; substituto ve aula como instrutor.
- `loading`: botoes desabilitados durante POST.
- `error`: erro textual proximo aos botoes.

### Modal
- `closed` -> `open` -> `submitting` -> `success` ou `error`.

## Plan
- [x] 1. Intake, contratos e contexto.
- [x] 2. PRD antes do codigo.
- [x] 3. Testes Red.
- [x] 4. Implementacao.
- [x] 5. Testes Green e checks.
- [x] 6. Browser desktop/mobile.
- [x] 7. Cleanup audit.

## Test plan
### Tests to author
- Service: cancelar presenca limpa `instructor_present` e horario.
- Service: indicar substituto valida ownership, professor ativo e nao si mesmo.
- Service/query: substituto ve aula regular do dia em `get_today_classes_for_instructor`.
- View: endpoint de cancelar presenca retorna JSON e respeita permissao.
- View: endpoint de substituicao retorna JSON e bloqueia professor invalido.
- Template: Home renderiza acoes de cancelamento/substituicao quando instrutor esta presente.

### Execution authorization
Testes locais, migration local e ORM local estao autorizados pelo escopo operacional solicitado. Ambientes remotos nao estao autorizados.

### Execution evidence
- Red focado: `.\.venv\Scripts\python.exe manage.py test system.tests.test_calendar.InstructorSelfCheckinServiceTestCase --verbosity 2`
  - Resultado esperado antes da implementacao: falha de importacao para `assign_session_substitute`.
- Green focado: `.\.venv\Scripts\python.exe manage.py test system.tests.test_calendar.InstructorSelfCheckinServiceTestCase --verbosity 2`
  - Resultado: OK.
- Regressao proporcional: `.\.venv\Scripts\python.exe manage.py test system.tests.test_home_dashboard system.tests.test_calendar.InstructorSelfCheckinServiceTestCase --verbosity 2`
  - Resultado: 24 testes OK.
- Check Django: `.\.venv\Scripts\python.exe manage.py check`
  - Resultado: System check identified no issues.
- Check JS: `node --check static\system\js\home\dashboard.js`
  - Resultado: sem erro de sintaxe.
- Check migrations: `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`
  - Resultado: No changes detected.

## Visual validation
- Browser interno em `http://127.0.0.1:8000/home/`, usuario professor Lauro.
- Mobile 375x667:
  - Acoes da secao `Turmas de hoje` renderizadas como botoes iconicos 44x44.
  - Sem overflow horizontal.
  - Presenca exibida com `Cancelar` e `Trocar professor`.
  - Filtros do historico com defaults `Todos`.
  - Modal de substituto abriu sobre a tela, com select de professores ativos e sem erro de console.
  - Modal de historico de graduacoes abriu sobre a tela, altura controlada e scroll interno na lista.
- Desktop 1280x900:
  - Acoes preservam texto e largura adequada.
  - Filtros default `Todos`.
  - Controles de cancelar/substituir presentes.
  - Sem erro de console.
- Screenshots locais:
  - `test_screenshots/prd-072-home-professor/mobile-home.jpg`
  - `test_screenshots/prd-072-home-professor/mobile-attendance-modal.jpg`
  - `test_screenshots/prd-072-home-professor/mobile-substitute-modal.jpg`
  - `test_screenshots/prd-072-home-professor/mobile-grad-modal.jpg`
  - `test_screenshots/prd-072-home-professor/desktop-home.jpg`

## ORM validation
- `.\.venv\Scripts\python.exe manage.py migrate`
  - Resultado: `Applying system.0002_classsession_substitute_teacher... OK`.
- `.\.venv\Scripts\python.exe manage.py showmigrations system | Select-String "0002"`
  - Resultado: `[X] 0002_classsession_substitute_teacher`.

## Quality validation
- `git diff --check`
  - Resultado: sem erro de whitespace; apenas avisos locais de conversao LF -> CRLF.
- Busca de residuos:
  - `rg -n 'innerHTML|insertAdjacentHTML|outerHTML|debugger|console\.log|TODO|FIXME|href="#"|Django Admin' ...`
  - Resultado: ocorrencias apenas nesta PRD e em asserts negativos existentes de teste.
- `dashboard.js` nao contem `innerHTML`, `insertAdjacentHTML` ou `outerHTML` no codigo alterado.

## Evidence
- Fonte oficial usada: Django 5.2 class-based views, `dispatch` e fluxo HTTP: https://docs.djangoproject.com/en/5.2/ref/class-based-views/base/
- Context7 confirmou contratos de CBV, POST/CSRF e Test Client para Django 5.2.
- Validacao visual feita no navegador interno com professor Lauro em desktop e mobile.

## Implemented
- Adicionado `ClassSession.substitute_teacher` para substituicao por sessao diaria regular.
- Adicionados services de cancelar presenca do professor, indicar substituto e cancelar presenca em aulao.
- Ajustadas queries para o substituto enxergar a aula regular do dia e ser autorizado nas checagens de ownership.
- Adicionados endpoints JSON com CSRF para cancelamento de presenca e substituicao.
- Home do professor passou a renderizar `Cancelar`, `Trocar professor` e modal de substituicao.
- Filtros do historico de presencas agora mostram default curto `Todos`.
- Header mobile de `Turmas de hoje` usa acoes iconicas 44x44 com `aria-label` e `title`.
- Modal de historico de graduacoes passou a usar altura controlada e scroll interno.
- JS removeu atualizacao via `innerHTML` no fluxo alterado e usa reload apos POSTs operacionais.

## Cleanup findings
- Diff limitado aos arquivos do escopo e a esta PRD.
- Nao foram encontrados `debugger`, `console.log`, `TODO`, `FIXME`, `href="#"` novo ou `innerHTML` no codigo da Home alterado.
- Screenshots de validacao ficaram em pasta de evidencia local ignorada pelo Git.
- Sem PRD de follow-up obrigatoria identificada no escopo desta correcao.

## Follow-up PRDs
- Nenhuma criada.

## Deviations from plan
- Foi necessario criar migration local para representar substituto por sessao diaria regular, pois o schema anterior nao tinha onde persistir essa decisao sem regra temporaria em JS/template.
- Durante a validacao visual, o navegador ainda carregava `dashboard.js?v=1`; o template foi atualizado para `dashboard.js?v=2` e o CSS para `dashboard.css?v=3`.

## Pending
- Deploy, HG/producao e aplicacao remota da migration estao fora do escopo desta rodada.
- Validacao completa de aluno, responsavel, administrativo e admin nao foi repetida nesta rodada; a correcao validada foi o caso professor solicitado pelos comentarios.

## Final status
Concluida com limitacoes: fluxo do professor corrigido e validado localmente; ambientes remotos e demais papeis ficam pendentes de autorizacao/rodada propria.
