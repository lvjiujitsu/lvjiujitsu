# PRD-003: Simplificar listas e mover vínculos para páginas de visualização
## Resumo
Reduzir a poluição visual das telas de listagem e da página pública de informações, mantendo apenas resumos diretos no primeiro nível e concentrando o cruzamento completo entre pessoas, turmas, horários, tipos e categorias em páginas de visualização dedicadas.

## Problema atual
- As listas ficaram densas demais após a exposição de vínculos completos diretamente na home/listagem.
- A tela pública de informações saiu do objetivo de leitura rápida.
- O editor de turma mostra horários demais ao mesmo tempo, com sensação de repetição de dias.
- O usuário quer navegação progressiva: lista simples primeiro, detalhe completo só ao clicar em “Visualizar”.

## Objetivo
- Tornar listas e página pública mais limpas, diretas e resumidas.
- Adicionar páginas “Visualizar” para pessoa, turma, horário, tipo e categoria.
- Manter o cruzamento completo apenas nos detalhes.
- Reduzir o ruído visual do cadastro de turma, resumindo horários já existentes.

## Contexto consultado
- Context7: indisponível no ambiente atual.
- Web:
  - Django docs, generic views: https://docs.djangoproject.com/en/4.1/topics/http/generic-views/
  - Django docs, generic display views / `DetailView`: https://docs.djangoproject.com/en/4.0/ref/class-based-views/generic-display/

## Dependências adicionadas
- nenhuma

## Escopo / Fora do escopo
### Escopo
- Simplificar `info.html` para resumo por turma.
- Simplificar listas de pessoas, turmas, horários, tipos e categorias.
- Criar detail views, rotas e templates para esses mesmos objetos.
- Reduzir o número de linhas visíveis do cadastro de horários da turma.

### Fora do escopo
- Refazer a regra de validação estrutural implementada no PRD-002.
- Criar paginação, busca avançada ou filtros complexos.

## Arquivos impactados
- `docs/prd/PRD-003-simplify-lists-and-add-detail-views.md`
- `system/urls.py`
- `system/views/person_views.py`
- `system/views/class_views.py`
- `system/views/category_views.py`
- `templates/login/info.html`
- `templates/people/person_list.html`
- `templates/people/person_detail.html`
- `templates/classes/class_group_list.html`
- `templates/classes/class_group_detail.html`
- `templates/classes/class_group_form.html`
- `templates/class_schedules/class_schedule_list.html`
- `templates/class_schedules/class_schedule_detail.html`
- `templates/class_categories/class_category_list.html`
- `templates/class_categories/class_category_detail.html`
- `templates/person_types/person_type_list.html`
- `templates/person_types/person_type_detail.html`
- `static/system/css/portal/class-catalog.css`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_views.py`

## Riscos e edge cases
- Detail views precisam carregar vínculos sem N+1.
- A simplificação não pode remover ações essenciais de edição/exclusão.
- O cadastro de turma precisa continuar válido mesmo com menos linhas de horário visíveis.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- SDD guiado por este PRD.
- TDD com foco em detail views e simplificação da leitura.
- MTV: carregamento relacional preparado em view/service; templates só exibem.
- Detail pages com `DetailView` e contexto adicional apenas quando necessário.

## Critérios de aceite (escritos como assertions testáveis)
- [x] A página pública de informações deve mostrar resumo direto por turma, sem grade cruzada completa no primeiro nível.
- [x] A lista de pessoas deve exibir resumo simples e ação “Visualizar”.
- [x] A visualização de pessoa deve mostrar turmas como aluno e atuação como professor.
- [x] A lista de turmas deve exibir resumo simples e ação “Visualizar”.
- [x] A visualização de turma deve mostrar categoria, equipe docente e horários vinculados.
- [x] A lista de horários deve exibir resumo simples e ação “Visualizar”.
- [x] A visualização de horário deve mostrar turma, categoria e professores vinculados.
- [x] A lista de tipos deve exibir resumo simples e ação “Visualizar”.
- [x] A visualização de tipo deve mostrar as pessoas vinculadas àquele tipo.
- [x] A lista de categorias deve exibir resumo simples e ação “Visualizar”.
- [x] A visualização de categoria deve mostrar turmas e pessoas vinculadas.
- [x] O cadastro de turma deve reduzir a repetição visual dos horários.

## Plano (ordenado por dependência — fundações primeiro)
- [x] 1. Adicionar testes para detail views e novo comportamento resumido.
- [x] 2. Criar detail views, URLs e templates.
- [x] 3. Simplificar listas e página pública.
- [x] 4. Reduzir o ruído visual do editor de turma.
- [x] 5. Validar suíte e checagem visual.

## Comandos de validação
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_class_portal_views system.tests.test_views --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`

## Implementado (preencher ao final)
- Página pública `info.html` reduzida para cards resumidos por turma, exibindo apenas categoria, modalidade, contagem de horários e contagem de professores.
- Listagens de pessoas, turmas, horários, categorias e tipos simplificadas para leitura rápida, com vínculo completo removido do primeiro nível e ação explícita `Visualizar`.
- Detail views adicionadas para pessoa, turma, horário, categoria e tipo, cada uma exibindo os cruzamentos relacionais completos apenas dentro da página selecionada.
- Cadastro de turma mantido com edição inline de horários, mas agora com resumo agrupado por dia no topo da seção para reduzir a sensação de duplicidade de dias da semana.
- Testes novos cobrindo:
  - resumo do primeiro nível da página pública
  - detail views relacionais
  - resumo agrupado de horários no formulário de turma
- Validação executada:
  - `.\.venv\Scripts\python.exe manage.py test system.tests.test_class_portal_views system.tests.test_views --verbosity 2`
  - `.\.venv\Scripts\python.exe manage.py test --verbosity 2`
  - `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
  - `.\.venv\Scripts\python.exe manage.py findstatic system/css/portal/class-catalog.css system/js/shared/public-info.js`
  - `.\.venv\Scripts\python.exe manage.py showmigrations`
  - `.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8012 --noreload` em processo separado para validação visual
  - Navegação headless com Playwright nas rotas:
    - `/info/`
    - `/people/` e `/people/1/`
    - `/class-groups/`, `/class-groups/1/` e `/class-groups/3/edit/`
    - `/class-schedules/` e `/class-schedules/1/`
    - `/person-types/` e `/person-types/1/`
    - `/class-categories/` e `/class-categories/1/`
  - Capturas geradas em `test_artifacts/`:
    - `info-8012.png`
    - `people-list-8012.png`
    - `person-detail-8012.png`
    - `class-groups-list-8012.png`
    - `class-group-detail-8012.png`
    - `class-group-edit-8012.png`
    - `class-schedules-list-8012.png`
    - `class-schedule-detail-8012.png`
    - `person-types-list-8012.png`
    - `person-type-detail-8012.png`
    - `class-categories-list-8012.png`
    - `class-category-detail-8012.png`
  - Console do navegador: sem erros de JavaScript da aplicação; único erro restante é `404` para `/favicon.ico`

## Desvios do plano
- A primeira tentativa de automação visual falhou porque o `runserver` com autoreload não permaneceu acessível ao Playwright. A validação foi refeita com `runserver 127.0.0.1:8012 --noreload` em processo separado e concluída com sucesso.
