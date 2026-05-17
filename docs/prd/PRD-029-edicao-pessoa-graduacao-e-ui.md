# PRD-029: Edicao de pessoa com UI proporcional e contexto de graduacao

## Resumo do que será implementado
Reimaginar a tela de edicao de pessoa para remover campos esticados, melhorar a secao de vinculo/turmas e exibir contexto compacto de graduacao oficial e atuacao docente sem transformar a tela em detalhe completo. Atualizar a seed de professores para carregar historico ficticio de graduacao tecnica.

## Tipo de demanda
Refatoracao de UI com ajuste de seed e regeneracao documental.

## Problema atual
A tela de edicao usa secoes largas demais, campos desproporcionais e lista de turmas em texto longo. Professores aparecem sem historico tecnico oficial na edicao, mesmo sendo pessoas com graduacao. A seed de professores nao registra historico completo de graduacao.

## Objetivo
- Tornar o formulario de edicao mais compacto, sequencial e proporcional.
- Manter a edicao focada nos dados da pessoa, sem operar CRUDs de graduacao/financeiro dentro da tela.
- Exibir contexto compacto de graduacao oficial com faixa visual e historico recente.
- Exibir contexto docente para professores sem misturar isso com turmas liberadas de aluno.
- Atualizar seed de professores com historico de graduacao idempotente.

## Context Ledger
### Arquivos lidos integralmente
- `CLAUDE.md`
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-028-home-e-pessoas-fullscreen.md`
- `system/forms/person_forms.py`
- `system/views/person_views.py`
- `system/models/graduation.py`
- `system/services/graduation.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `system/management/commands/seed_system_initial_administrative.py`
- `static/initial_data/initial_teachers.json`
- `static/initial_data/initial_administrative.json`
- `system/management/commands/seed_system_initial_administrative.py`
- `static/initial_data/belt_ranks.json`
- `templates/people/person_form.html`
- `templates/people/_person_field.html`
- `templates/graduation/_belt_visual.html`
- `static/system/css/portal/people.css`
- `system/tests/test_views.py`
- `system/tests/test_graduation.py`

### Arquivos adjacentes consultados
- `system/constants.py`
- `system/urls.py`
- `templates/graduation/_progress_card.html`
- `templates/graduation/_history_modal.html`

### Internet / documentação oficial
- Nao aplicavel; mudanca usa Django templates, CSS e modelos existentes.

### MCPs / ferramentas verificadas
- PowerShell — OK.
- Django test runner — OK.
- Browser/Playwright — OK.

### Limitações encontradas
- Sem migracoes.
- Sem novas pastas.
- Workspace ja possui muitas alteracoes locais; a implementacao deve preservar o que ja existe.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django MVT seguindo SDD + TDD + CSS responsivo operacional.

### Ação
Reimplementar a tela `people/person_form.html` para edicao proporcional e adicionar historico de graduacao de professores na seed.

### Contexto
Editar pessoa deve alterar cadastro, prontuario, arte marcial declarada, vinculo, turmas liberadas e repasse. Historico oficial de graduacao e atuacao docente aparecem como contexto compacto e links para seus fluxos proprios.

### Restrições
- sem hardcode de regra de negocio no template
- sem migracoes
- sem criar pastas
- sem remover campos existentes
- CSS em `static/`
- templates em `templates/`
- seed idempotente
- validacao visual obrigatoria

### Critérios de aceite
- [ ] A tela de edicao nao deve duplicar um card resumo com nome/CPF/tipo/status/acesso quando esses dados ja sao campos editaveis.
- [ ] Campos comuns devem ter largura proporcional no desktop e empilhar no celular.
- [ ] Textarea e listas longas devem ter largura controlada e altura apropriada.
- [ ] A secao de vinculo deve diferenciar edicao de tipo/status da selecao de turmas liberadas.
- [ ] Turmas liberadas devem aparecer como opcoes compactas, legiveis e nao como texto corrido desproporcional.
- [ ] Professores devem mostrar contexto de atuacao docente quando houver turma/horario.
- [ ] Pessoas com `Graduation` devem mostrar graduacao oficial atual e historico recente na edicao.
- [ ] Acoes de criar/editar/remover graduacao continuam no CRUD de Graduacao, acessadas por link.
- [ ] Seed de professores deve registrar historico idempotente ate a faixa/grau solicitados.
- [ ] Tema claro/escuro deve preservar contraste.
- [ ] Desktop e mobile nao podem ter overflow horizontal.

## Escopo
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-029-edicao-pessoa-graduacao-e-ui.md`
- `templates/people/person_form.html`
- `static/system/css/portal/people.css`
- `system/views/person_views.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `static/initial_data/initial_teachers.json`
- `system/tests/test_views.py`
- `system/tests/test_graduation.py`

## Fora do escopo
- Criar nova tela de graduacao.
- Alterar schema ou migracoes.
- Alterar regras de graduacao.
- Alterar permissoes.

## Arquivos impactados
- `docs/UI-SCREEN-CONTRACT.md`
- `docs/prd/PRD-029-edicao-pessoa-graduacao-e-ui.md`
- `templates/people/person_form.html`
- `templates/plans/plan_form.html`
- `static/system/css/portal/people.css`
- `system/views/person_views.py`
- `system/management/commands/seed_system_initial_teacher.py`
- `static/initial_data/initial_teachers.json`
- `system/tests/test_views.py`
- `system/tests/test_graduation.py`

## Riscos e edge cases
- Confundir `class_groups` de aluno com atuacao docente de professor.
- Duplicar historico ao rodar seed novamente.
- Estourar layout com nomes longos de turmas e horarios.
- Esconder campos obrigatorios em mobile.

## Regras e restrições
- SDD antes de codigo.
- TDD para implementacao.
- Sem hardcode de segredo.
- Sem migracoes.
- Leitura integral obrigatoria.
- Validacao obrigatoria.

## Plano
- [x] 1. Contexto e leitura integral.
- [x] 2. Atualizar testes de contrato da tela.
- [x] 3. Implementar contexto de graduacao na view.
- [x] 4. Reimplementar template da edicao.
- [x] 5. Ajustar CSS responsivo.
- [x] 6. Atualizar seed de professores.
- [x] 7. Validar testes/check/collectstatic.
- [x] 8. Validar browser desktop/mobile.

## Validação visual
### Desktop
OK. `http://localhost:8000/people/6/edit/` em 1440x1000:
- sem overflow horizontal;
- layout com formulario e contexto lateral (`1004px 380px`);
- campos principais com largura controlada de 420px;
- graduacao oficial exibida com 6 itens recentes de historico;
- console sem erros.

### Mobile
OK. `http://localhost:8000/people/6/edit/` em 390x900:
- sem overflow horizontal;
- contexto de graduacao sobe antes do formulario;
- campos principais com largura controlada de 336px;
- console sem erros.

### Console do navegador
OK. 0 erros nos cenarios mobile e desktop validados.

### Terminal
OK. Sem stack trace durante seeds, testes e validacao.

## Validação ORM
### Banco
OK. Seed `seed_system_initial_teacher` executada localmente apos `seed_system_initial_belt_ranks`, criando historico de graduacao para os 5 professores.

### Shell checks
OK. Teste automatizado confirma idempotencia da seed e faixa/grau atual de cada professor.

### Integridade do fluxo
OK. Formulario preserva POST existente e contexto de graduacao e somente leitura.

## Validação de qualidade
### Sem hardcode
OK. Historicos ficticios vivem no JSON da seed; template consome dados do modelo.

### Sem estruturas condicionais quebradiças
OK. View usa services existentes de graduacao e hidratacao de relacionamentos.

### Sem `except: pass`
OK.

### Sem mascaramento de erro
OK. Seed falha explicitamente se faixa exigida nao existir.

## Evidências
- Red inicial:
  - `test_people_screens_render_responsive_contract_sections` falhou por ausencia de `Acesso e turmas`.
  - `test_teacher_seed_creates_requested_graduation_histories_idempotently` falhou porque professores nao possuíam graduacao oficial.
- Green focado:
  - `manage.py test system.tests.test_views.PortalViewTestCase.test_people_screens_render_responsive_contract_sections system.tests.test_graduation.InitialTeacherSeedGraduationTestCase.test_teacher_seed_creates_requested_graduation_histories_idempotently --verbosity 2` — OK.
- Validacao completa:
  - `manage.py test --verbosity 2` — 276 testes OK.
  - `manage.py check` — OK.
  - `manage.py collectstatic --noinput` — OK.
  - `git diff --check` — OK, apenas avisos CRLF.

## Implementado
- Tela de edicao de Pessoa com layout proporcional, sem card resumo duplicado.
- Contexto compacto de graduacao oficial atual e historico recente.
- Contexto compacto de atuacao docente para professores.
- `Turmas liberadas` renderizado como painel de opcoes compactas.
- Seed de professores com historico idempotente:
  - Lauro: faixa preta grau 2.
  - Andre: faixa preta grau 1.
  - Layon: faixa preta grau 1.
  - Vanessa: faixa marrom grau 4.
  - Vinicius: faixa preta grau 0.
- Seeds de professores e administrativo passam a preencher dados cadastrais coerentes com a edicao manual: tipo sanguineo, alergias, lesoes previas, contato de emergencia, arte marcial, inicio no jiu jitsu, ultima graduacao anterior e academia anterior.
- Ajuste de contrato regressivo em `templates/plans/plan_form.html` para manter `Cadastrar plano`.

## Desvios do plano
Durante a suite completa, um contrato ja existente de `plan_form.html` falhou porque o template renderizava `Novo plano` onde o teste exige `Cadastrar plano`. A correcao foi aplicada sem mudar regra de negocio.

## Pendências
Nenhuma pendencia conhecida para esta etapa.
