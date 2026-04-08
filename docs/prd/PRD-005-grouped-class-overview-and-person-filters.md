# PRD-005: Agrupar turmas e horários no primeiro nível e adicionar filtros em pessoas
## Resumo
Eliminar a repetição visual de turmas e horários nas listas de primeiro nível, agregando por conceito lógico, além de adicionar filtros operacionais no painel de pessoas e padronizar a ação `Excluir` com destaque visual leve em vermelho.

## Problema atual
- A lista pública e a gestão de turmas ainda repetem `Adulto · Jiu Jitsu` várias vezes porque cada professor está sendo tratado como um card separado no primeiro nível.
- A lista de horários ainda repete linhas por ocorrência, quando o primeiro nível deveria resumir por dia da semana.
- O painel de pessoas não possui filtros suficientes para gestão operacional rápida.
- Os links de exclusão nas listas ainda não têm o destaque visual destrutivo solicitado.

## Objetivo
- Agrupar turmas por categoria + modalidade no primeiro nível.
- Agrupar horários por dia da semana no primeiro nível.
- Mover a gestão detalhada das ocorrências físicas para dentro das páginas `Visualizar`.
- Adicionar filtros em pessoas por nome, CPF, professor, categoria, turma e horário.
- Aplicar coloração leve em vermelho às ações `Excluir`.

## Contexto consultado
- Context7:
  - Django `ListView`: sobrescrever `get_queryset()` para filtrar via `request.GET` e adicionar contexto extra em `get_context_data()`.
- Web:
  - MDN, favicon e metadata já consultados no PRD-004, sem impacto direto aqui.

## Dependências adicionadas
- nenhuma

## Escopo / Fora do escopo
### Escopo
- Ajustar agrupamento na página pública de informações.
- Ajustar agrupamento nas listas administrativas de turmas e horários.
- Ajustar detail views de turmas e horários para mostrar os registros físicos agregados.
- Adicionar formulário de filtros no painel de pessoas.
- Aplicar estilo destrutivo leve em vermelho aos controles `Excluir`.

### Fora do escopo
- Refatorar o modelo de dados para unificar fisicamente turmas por categoria.
- Implementar paginação, ordenação avançada ou busca full text.

## Arquivos impactados
- `docs/prd/PRD-005-grouped-class-overview-and-person-filters.md`
- `system/services/class_overview.py`
- `system/selectors/__init__.py`
- `system/selectors/person_selectors.py`
- `system/views/class_views.py`
- `system/views/person_views.py`
- `system/views/auth_views.py`
- `system/forms/person_forms.py`
- `system/forms/__init__.py`
- `templates/login/info.html`
- `templates/classes/class_group_list.html`
- `templates/classes/class_group_detail.html`
- `templates/class_schedules/class_schedule_list.html`
- `templates/class_schedules/class_schedule_detail.html`
- `templates/people/person_list.html`
- `templates/person_types/person_type_list.html`
- `templates/class_categories/class_category_list.html`
- `static/system/css/portal/portal.css`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_views.py`

## Riscos e edge cases
- A agregação não pode esconder a manutenção dos registros físicos.
- Os filtros de pessoas precisam funcionar tanto para alunos quanto para professores.
- O agrupamento por dia da semana precisa preservar acesso à edição/exclusão das ocorrências reais.
- A nova lógica não pode causar N+1 nas páginas de detalhe.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- SDD guiado por este PRD.
- TDD obrigatório para agrupamento e filtros.
- MTV: consultas e agregações fora do template.
- Views finas; preparação relacional em serviço/query layer.

## Critérios de aceite (escritos como assertions testáveis)
- [x] A página pública de informações deve exibir `Adulto · Jiu Jitsu` apenas uma vez no primeiro nível.
- [x] A lista administrativa de turmas deve agrupar turmas lógicas e não repetir `Adulto · Jiu Jitsu`.
- [x] A visualização de turma deve exibir os professores e horários combinados dessa turma lógica e listar as ocorrências físicas para gestão.
- [x] A lista administrativa de horários deve agrupar por dia da semana, sem repetir o mesmo dia várias vezes no primeiro nível.
- [x] A visualização de horário deve exibir todas as ocorrências daquele dia e permitir gestão das ocorrências físicas.
- [x] O painel de pessoas deve aceitar filtros por nome, CPF, professor, categoria, turma e horário.
- [x] Os controles `Excluir` nas listas e confirmações devem ter destaque visual leve em vermelho.

## Plano (ordenado por dependência — fundações primeiro)
- [x] 1. Adicionar testes para agrupamento de turmas, agrupamento de horários e filtros de pessoas.
- [x] 2. Implementar agregações lógicas em `class_overview.py`.
- [x] 3. Atualizar views e templates de turmas/horários para usar agregações.
- [x] 4. Adicionar formulário e lógica de filtros em pessoas.
- [x] 5. Padronizar estilo visual da ação `Excluir`.
- [x] 6. Validar suíte, estáticos e Playwright headless.

## Comandos de validação
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_class_portal_views system.tests.test_views --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
- `.\.venv\Scripts\python.exe manage.py findstatic system/css/portal/portal.css`
- `.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8014 --noreload`
- Playwright headless nas listas de turmas, horários e pessoas

## Implementado (preencher ao final)
- Agrupei o primeiro nível da página pública e da gestão de turmas por chave lógica `categoria + modalidade`, evitando repetição de `Adulto · Jiu Jitsu` quando existem vários professores/ocorrências físicas.
- Agrupei o primeiro nível da gestão de horários por `weekday`, deixando os detalhes das ocorrências reais apenas dentro de `Visualizar`.
- Mantive a gestão operacional dos registros físicos nas detail views, com professores, horários, turmas do dia, ocorrências reais e ações de edição/exclusão por item físico.
- Extraí a leitura de pessoas para selector dedicado e acrescentei filtro por nome, CPF, somente professores, categoria, turma lógica e horário.
- Padronizei os controles destrutivos com vermelho leve em links de lista/detalhe e no botão de confirmação de exclusão.
- Cobri o comportamento com testes de view e validação visual headless.

### Evidências de validação
- Testes direcionados:
  - `.\.venv\Scripts\python.exe manage.py test system.tests.test_class_portal_views system.tests.test_views --verbosity 2`
- Suíte completa:
  - `.\.venv\Scripts\python.exe manage.py test --verbosity 2`
- Estáticos:
  - `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
  - `.\.venv\Scripts\python.exe manage.py findstatic system/css/portal/portal.css`
- ORM/Banco:
  - `.\.venv\Scripts\python.exe manage.py showmigrations`
  - `.\.venv\Scripts\python.exe manage.py shell -c "<checagens de contagem e agregação>"`
- Playwright headless:
  - `/info/`
  - `/class-groups/`
  - `/class-groups/3/`
  - `/class-groups/3/delete/`
  - `/class-schedules/`
  - `/class-schedules/1/`
  - `/people/`
  - `/people/?full_name=&cpf=&is_teacher=on&class_category=&class_group_key=1%3A%3AJiu+Jitsu&weekday=`
  - `/people/3/`
- Screenshots:
  - `test_artifacts/info-8014-grouped.png`
  - `test_artifacts/class-groups-8014-grouped.png`
  - `test_artifacts/class-group-detail-8014.png`
  - `test_artifacts/class-group-delete-8014.png`
  - `test_artifacts/class-schedules-8014-grouped.png`
  - `test_artifacts/class-schedule-detail-8014.png`
  - `test_artifacts/people-list-8014.png`
  - `test_artifacts/people-list-filtered-8014.png`
  - `test_artifacts/person-detail-8014.png`
  - `test_artifacts/info-8014-mobile.png`
  - `test_artifacts/people-list-filtered-8014-mobile.png`
- Console/rede:
  - Playwright registrou `0` erros de console.
  - Requisições da página filtrada de pessoas retornaram `200` para HTML, CSS, JS e logos, sem `404`.

## Desvios do plano
- Nenhum até o momento.
