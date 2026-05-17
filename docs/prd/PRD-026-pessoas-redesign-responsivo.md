# PRD-026: Redesign responsivo de Pessoas

## Resumo do que será implementado
Reimplementar a apresentacao das telas de Pessoas para tornar listagem, detalhe, formulario e exclusao mais legiveis em celular e computador, preservando todas as funcionalidades existentes, permissoes por perfil e suporte a tema claro/escuro.

## Tipo de demanda
Refatoracao de UI com regeneracao documental e validacao funcional.

## Problema atual
As telas de Pessoas concentram muitos dados em blocos visuais pouco hierarquizados. Em formularios longos, campos de identidade, saude, arte marcial, vinculo e repasse aparecem como uma sequencia unica, dificultando uso em celular e computador. A listagem tambem nao deixa claro o escopo exibido para administrativo e professor.

## Objetivo
- Apresentar Pessoas com hierarquia visual moderna, responsiva e aderente ao padrao LV.
- Preservar tema claro/escuro via variaveis existentes.
- Separar formulario por blocos funcionais sem ocultar campos.
- Manter a listagem como porta de entrada rapida para visualizacao em modal, edicao e exclusao conforme permissao.
- Manter detalhe com resumo, financeiro, turmas, horarios e atuacao docente.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-025-redesign-ui-responsivo-lv.md`
- `system/views/person_views.py`
- `system/forms/person_forms.py`
- `system/models/person.py`
- `system/selectors/person_selectors.py`
- `templates/people/person_list.html`
- `templates/people/person_detail.html`
- `templates/people/person_form.html`
- `templates/people/person_confirm_delete.html`
- `templates/person_types/person_type_list.html`
- `templates/person_types/person_type_detail.html`
- `templates/person_types/person_type_form.html`
- `templates/person_types/person_type_confirm_delete.html`
- `templates/base.html`
- `static/system/css/portal/portal.css`
- `static/system/css/portal/class-catalog.css`
- `static/system/css/portal/person-detail.css`
- `system/tests/test_views.py`
- `system/tests/test_forms.py`

### Arquivos adjacentes consultados
- `system/tests/seed_helpers.py`
- Lista de arquivos em `static/`, `templates/` e `system/tests/`

### Internet / documentacao oficial
- Nao aplicavel nesta etapa; a mudanca usa Django templates e CSS existentes do projeto.

### MCPs / ferramentas verificadas
- PowerShell — disponivel — leitura com `Get-Content`
- ripgrep — disponivel — mapeamento de arquivos e testes com `rg`
- Django test runner — OK — `manage.py test`, `manage.py check`
- Browser/Playwright — OK — validacao visual desktop/mobile em `http://127.0.0.1:8000/people/`

### Limitacoes encontradas
- Nao criar novas pastas; o PRD usa `docs/prd/` existente e o CSS sera criado em `static/system/css/portal/` existente.
- Sem migracoes.
- Nao alterar regra de permissao, regra financeira ou regra de turma nesta etapa.

## Prompt de execucao
### Persona
Agente de desenvolvimento especialista em Django MVT seguindo SDD + TDD + mobile-first CSS.

### Acao
Implementar o redesign responsivo das telas de Pessoas seguindo a spec abaixo.

### Contexto
Pessoas e Tipos sao o nucleo de cadastro do portal LV Jiu Jitsu. Pessoas podem representar aluno, dependente, professor ou administrativo, e cada perfil deve preservar suas funcionalidades sem depender de campos escondidos no frontend.

### Restricoes
- sem hardcode de regra de negocio
- sem mascaramento de erro
- sem migracoes
- sem criar novas pastas
- sem mover funcionalidades para JavaScript
- CSS separado por tela/namespace em `static/`
- templates sem regra de negocio central
- validacao obrigatoria

### Criterios de aceite
- [ ] A listagem de Pessoas deve exibir cabecalho contextual, filtros, cards responsivos, status, CPF, tipo, turmas e acoes permitidas.
- [ ] A acao Visualizar da listagem deve abrir modal na propria tela, sem navegar para tela extra.
- [ ] Administrativo deve ver todas as pessoas e acoes Visualizar, Editar e Excluir.
- [ ] Professor deve ver apenas pessoas permitidas pelo contrato atual e nao deve receber acoes administrativas.
- [ ] O formulario deve agrupar campos em Identidade, Saude, Arte marcial, Vinculo e Repasse sem remover campos existentes.
- [ ] Repasse deve aparecer somente quando a view permitir campos de repasse.
- [ ] O detalhe deve manter Resumo, Financeiro para administrativo, Turmas liberadas, Horarios liberados e Atuacao como professor.
- [ ] A tela de exclusao deve manter confirmacao POST com CSRF e acao destrutiva evidente.
- [ ] O layout deve funcionar em mobile e desktop sem sobreposicao ou texto cortado.
- [ ] Tema claro/escuro deve continuar usando variaveis globais.

### Evidencias esperadas
- testes automatizados passando
- `manage.py check` sem erro
- `collectstatic --noinput` sem erro
- navegador sem erro JS critico
- validacao visual desktop e mobile

### Formato de saida
Codigo implementado + testes + evidencias de validacao.

## Escopo
- `PersonForm` apenas para expor grupos de campos para template.
- Templates em `templates/people/`.
- CSS em `static/system/css/portal/`.
- Testes de contrato em `system/tests/`.
- Documentacao do PRD.

## Fora do escopo
- Alterar modelo de dados.
- Alterar permissoes existentes.
- Alterar financeiro, pagamentos, turmas ou repasses.
- Redesenhar todas as telas do sistema nesta etapa.
- Criar migracoes.

## Arquivos impactados
- `docs/prd/PRD-026-pessoas-redesign-responsivo.md`
- `system/forms/person_forms.py`
- `system/tests/test_forms.py`
- `system/tests/test_views.py`
- `templates/people/person_list.html`
- `templates/people/person_detail.html`
- `templates/people/person_form.html`
- `templates/people/person_confirm_delete.html`
- `static/system/css/portal/people.css`
- `static/system/js/shared/people-list.js`

## Riscos e edge cases
- Formularios longos em celular podem ocultar campos se houver agrupamento incorreto.
- A listagem pode perder contexto docente se remover labels hidratadas pela view.
- Acoes administrativas nao podem aparecer para professor.
- Checkboxes de turmas precisam continuar usaveis por toque.
- Tabelas financeiras precisam preservar rolagem horizontal quando necessario.

## Regras e restricoes
- SDD antes de codigo
- TDD para implementacao
- sem hardcode
- sem mascaramento de erro
- sem migracoes
- leitura integral obrigatoria
- validacao obrigatoria

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem de UI
- [x] 3. Testes (Red)
- [x] 4. Implementacao (Green)
- [x] 5. Refatoracao (Refactor)
- [x] 6. Validacao completa
- [x] 7. Limpeza final
- [x] 8. Atualizacao documental

## Validacao visual
### Desktop
OK. Playwright em 1622x1411 confirmou:
- largura util `.content-shell`: 1480px;
- filtro com 101px de altura;
- filtro com 6 colunas na linha principal;
- 4 cards na primeira linha;
- sem overflow horizontal.

### Mobile
OK. Playwright em 390x900 confirmou tela sem overflow horizontal e metadados dos cards em linhas compactas.

### Console do navegador
OK. Sem erros de console capturados na validacao Playwright.

### Terminal
OK. Comandos de validacao executados sem stack trace.

## Validacao ORM
### Banco
Nao ha alteracao de schema.

### Shell checks
`manage.py showmigrations system` confirmou `0001_initial` aplicada; nao houve criacao de migracao.

### Integridade do fluxo
OK. Listagem, detalhe e formulario de Pessoas abriram com usuario administrativo real do ambiente local.

## Validacao de qualidade
### Sem hardcode
OK. A mudanca adiciona apenas estrutura visual e grupos de campos derivados de nomes existentes do `PersonForm`.

### Sem estruturas condicionais quebradicas
OK. Nenhuma regra de negocio nova foi introduzida.

### Sem `except: pass`
OK. Nenhum `except: pass` introduzido.

### Sem mascaramento de erro
OK. Nenhum tratamento silencioso novo.

### Sem comentarios e docstrings desnecessarios
OK.

## Evidencias
- Red inicial:
  - `manage.py test system.tests.test_forms.PersonFormLayoutContractTestCase --verbosity 2` falhou por ausencia de `identity_fields`.
  - `manage.py test system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections --verbosity 2` falhou por ausencia de `people.css`.
- Green:
  - `manage.py test system.tests.test_forms.PersonFormLayoutContractTestCase system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections --verbosity 2` — OK.
  - `manage.py test system.tests.test_forms system.tests.test_views --verbosity 2` — 76 testes OK.
  - `manage.py test --verbosity 2` — 263 testes OK antes do refinamento visual final.
  - `manage.py check` — OK.
  - `manage.py showmigrations system` — OK.
  - `manage.py collectstatic --noinput` — OK.
  - `git diff --check` — OK.
  - Playwright desktop/mobile — OK.

## Implementado
- Grupos de campos no `PersonForm` para Identidade, Saude, Arte marcial, Vinculo e Repasse.
- Template parcial reutilizavel para campos de Pessoa.
- Listagem com largura desktop maior, filtro compacto e cards responsivos.
- Visualizacao rapida de Pessoa em modal aberto pela propria listagem.
- Detalhe com hero proprio, acoes administrativas preservadas e resumo operacional.
- Exclusao com painel de confirmacao dedicado.
- CSS dedicado em `static/system/css/portal/people.css`.
- Edicao de Pessoa revisada como fluxo de edicao, nao consulta:
  - removidos resumos duplicados de pessoa, evolucao LV e historico tecnico da tela de edicao;
  - mantidos somente campos que o formulario de Pessoa edita diretamente;
  - fluxo Tatame restaurado com pergunta `Ja praticou arte marcial?` e, quando sim, modalidade, graduacao/nivel, faixa, graus, inicio no jiu jitsu, ultima graduacao anterior e academia anterior no mesmo bloco;
  - graduacao oficial, historico tecnico, financeiro e outros CRUDs relacionados permanecem em seus fluxos proprios.
  - secoes do formulario seguem padrao sequencial expansivel, sem layout lateralizado.

## Evidencias adicionais em 2026-05-16
- Red:
  - `manage.py test system.tests.test_forms.PersonFormLayoutContractTestCase system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections --verbosity 2` falhou porque a edicao nao expunha historico marcial nem evolucao cadastrada.
- Green:
  - `manage.py test system.tests.test_forms.PersonFormLayoutContractTestCase system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections --verbosity 2` — OK.
  - `manage.py test system.tests.test_forms system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections system.tests.test_views.PortalViewTestCase.test_person_update_saves_payroll_config_for_instructor --verbosity 2` — 5 testes OK.
  - `manage.py check` — OK.
  - `manage.py collectstatic --noinput` — OK.
- Browser em `http://localhost:8000/people/6/edit/` autenticado como admin tecnico:
    - desktop: 6 secoes expansíveis, formulario em 1 coluna, sem resumo duplicado, sem painel de evolucao duplicado, sem overflow horizontal, sem erros de console;
    - mobile 390x900: 6 secoes expansíveis, formulario em 1 coluna, icone de expandir/recolher visivel, sem overflow horizontal, sem erros de console.
- Browser em `http://localhost:8000/people/6/edit/`:
    - secao Tatame contem a pergunta de experiencia marcial e os 7 campos de detalhe no mesmo bloco;
    - ao selecionar `Nao`, os 7 campos de detalhe ficam ocultos e desabilitados;
    - sem erros de console.

## Desvios do plano
O refinamento visual final compactou filtros e metadados de cards apos anotacao do usuario no navegador.
Nova anotacao do usuario exigiu complementar a tela de edicao com topicos de historico marcial e evolucao cadastrada, sem alterar schema.

## Pendencias
Nenhuma pendencia tecnica conhecida nesta etapa.
