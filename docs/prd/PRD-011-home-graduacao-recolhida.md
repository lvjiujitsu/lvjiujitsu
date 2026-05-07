# PRD-011: Home com graduação recolhida

## Resumo do que será implementado
Nas homes do aluno e do professor, o card de graduação deve exibir inicialmente apenas a faixa atual. As informações de progresso hoje expostas na tela devem ficar dentro de um pequeno dropdown acionado pelo controle "Mais sobre a graduação".

## Tipo de demanda
Correção pontual de UI.

## Problema atual
O card de graduação ocupa espaço nas homes autenticadas porque mostra tempo na faixa, aulas aprovadas, conclusão e status diretamente na tela.

## Objetivo
Reduzir o volume inicial de informação nas homes do aluno e do professor, mantendo o acesso às informações completas da graduação sob demanda.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `manage.py`
- `requirements.txt`
- `templates/home/student/dashboard.html`
- `templates/home/instructor/dashboard.html`
- `templates/graduation/_progress_card.html`
- `templates/graduation/_belt_visual.html`
- `templates/graduation/_history_modal.html`
- `templates/base.html`
- `system/views/home_views.py`
- `system/views/portal_mixins.py`
- `system/urls.py`
- `system/services/graduation.py`
- `system/selectors/graduation.py`
- `system/models/graduation.py`
- `system/templatetags/graduation_tags.py`
- `system/tests/test_graduation.py`
- `system/tests/test_views.py`
- `static/system/css/portal/portal.css`
- `docs/prd/PRD-010-modulo-graduacao-faixas-graus.md`

### Arquivos adjacentes consultados
- `docs/prd/`
- `system/tests/test_calendar.py`
- `system/tests/test_plan_views.py`
- `system/tests/test_product_views.py`

### Internet / documentação oficial
- Não aplicável: a alteração usa comportamento HTML nativo de `<details>/<summary>` e CSS local, sem nova API de framework.

### MCPs / ferramentas verificadas
- PowerShell — ok — `Get-ChildItem`, `Get-Content`, `Select-String`.
- `.venv` — ok — `.\.venv\Scripts\python.exe --version` retornou Python 3.12.10.
- Django — ok — `.\.venv\Scripts\python.exe -m django --version` retornou 4.1.13.
- `rg` — indisponível — execução falhou por acesso negado ao binário empacotado; substituído por comandos nativos do PowerShell.
- Browser Use / node_repl — limitado nesta revisão — retornou `No active Codex browser pane available`.
- Playwright MCP — ok — validação desktop/mobile em `http://127.0.0.1:8000/`.

### Limitações encontradas
- Worktree já possui várias alterações não relacionadas; esta entrega não deve revertê-las.
- Há diretórios `cleanup-artifacts-*` com acesso negado ao listar via Git; não fazem parte do escopo.
- A primeira execução do Playwright Python no sandbox falhou por permissão; a validação foi repetida fora do sandbox com aprovação.
- O servidor Django que estava aberto na porta 8000 mantinha o template antigo em memória; foi reiniciado para validar o HTML servido pelo código atual.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django 4.1 seguindo SDD + TDD + MVT server-rendered.

### Ação
Implementar o card de graduação recolhido nas homes do aluno e do professor.

### Contexto
As duas homes incluem o componente compartilhado `templates/graduation/_progress_card.html`; portanto a mudança deve ser concentrada nesse include e no CSS do portal.

### Restrições
- sem hardcode de regra de graduação
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória
- preservar alterações pré-existentes do worktree

### Critérios de aceite
- [x] A home do aluno deve renderizar a faixa atual imediatamente.
- [x] A home do professor deve renderizar a faixa atual imediatamente.
- [x] As informações de tempo na faixa, aulas aprovadas, conclusão e status devem ficar dentro de um dropdown fechado por padrão.
- [x] O dropdown deve ser acionado pelo texto "Mais sobre a graduação".
- [x] O botão/modal de histórico, quando houver histórico, deve continuar acessível a partir do detalhe expandido.
- [x] A versão do `portal.css` deve ser atualizada no template que referencia o asset.

### Evidências esperadas
- teste automatizado cobrindo aluno e professor
- `manage.py test --verbosity 2`
- `manage.py check`
- `manage.py collectstatic --noinput`
- `manage.py showmigrations`
- validação visual em navegador desktop e mobile
- console do navegador sem erro JS crítico

### Formato de saída
Código implementado + testes + evidências de validação.

## Escopo
- `templates/graduation/_progress_card.html`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_graduation.py`
- `docs/prd/PRD-011-home-graduacao-recolhida.md`

## Fora do escopo
- Alterar regra de cálculo de graduação.
- Alterar models, migrations, seeds ou CRUD administrativo.
- Alterar layout dos demais cards das homes.

## Arquivos impactados
- `templates/graduation/_progress_card.html`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_graduation.py`
- `docs/prd/PRD-011-home-graduacao-recolhida.md`

## Riscos e edge cases
- Pessoa sem graduação registrada deve continuar vendo a mensagem atual sem dropdown vazio.
- Pessoa com faixa mas sem regra configurada deve ver a mensagem de regra apenas no detalhe expandido.
- Pessoa com histórico deve continuar abrindo e fechando o modal de histórico.
- A solução deve funcionar sem JavaScript adicional para abrir o dropdown.

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Testes (Red)
- [x] 4. Implementação (Green)
- [x] 5. Refatoração (Refactor)
- [x] 6. Validação completa
- [x] 7. Limpeza final
- [x] 8. Atualização documental

## Validação visual
### Desktop
Playwright MCP validou `desktop-student` e `desktop-instructor` em viewport 1280x900:
- faixa visível imediatamente
- "Tempo na faixa atual" oculto antes da abertura
- "Tempo na faixa atual", "Aulas aprovadas" e "Ver histórico" visíveis após clicar em "Mais sobre a graduação"
- histórico abre via `static/system/js/graduation/progress-card.js?v=20260507a`
- `inlineHistoryScriptCount=0`
- `console_errors=0`

### Mobile
Playwright MCP validou `mobile-student` e `mobile-instructor` em viewport 390x844 com os mesmos critérios de desktop, `console_errors=0` e sem overflow horizontal.

### Console do navegador
Playwright MCP: `errors=[]` para aluno/professor em desktop/mobile.

### Terminal
Comandos executados sem stack trace após a correção. O servidor local foi reiniciado e `/login/` respondeu `200`.

## Validação ORM
### Banco
Sem alteração de schema prevista.

### Shell checks
Foram criadas personas temporárias `930.000.700-01` e `930.000.700-02` para validar aluno e professor com graduação real no banco local. Ao final, a limpeza retornou `False False` para existência residual das pessoas e da faixa `codex-visual-white`.

### Integridade do fluxo
Aluno e professor autenticados acessaram suas respectivas homes e o componente compartilhado preservou o modal de histórico dentro do detalhe expandido.

## Validação de qualidade
### Sem hardcode
Sem hardcode de regra de graduação; o template continua consumindo `graduation_progress` e `graduation_history`.

### Sem estruturas condicionais quebradiças
Mudança concentrada no include compartilhado, mantendo as condicionais existentes por `current_belt_rank`, `applicable_rule` e `graduation_history`.

### Sem `except: pass`
Nenhum `except: pass` introduzido.

### Sem mascaramento de erro
Nenhum erro mascarado; comportamento do dropdown é nativo via `<details>/<summary>`.

### Sem comentários e docstrings desnecessários
Nenhum comentário/docstring novo em código de produção.

## Evidências
- Red: `.\.venv\Scripts\python.exe manage.py test system.tests.test_graduation.GraduationDashboardCardTestCase --verbosity 2` falhou antes da implementação por ausência de "Mais sobre a graduação".
- Green focado: `.\.venv\Scripts\python.exe manage.py test system.tests.test_graduation.GraduationDashboardCardTestCase --verbosity 2` — 2 testes, OK.
- Módulo de graduação: `.\.venv\Scripts\python.exe manage.py test system.tests.test_graduation --verbosity 2` — 18 testes, OK.
- Suite completa: `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 305 testes, OK.
- Check: `.\.venv\Scripts\python.exe manage.py check` — 0 issues.
- JS check: `node --check .\static\system\js\graduation\progress-card.js` — OK.
- Static: `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — 1 arquivo copiado, 164 inalterados.
- Migrations: `.\.venv\Scripts\python.exe manage.py showmigrations` — somente `system.0001_initial` aplicada no app local.
- Diff check: `git diff --check` — sem erros; apenas avisos de normalização LF/CRLF em arquivos já modificados.
- Playwright MCP: aluno e professor com dropdown fechado por padrão; informações aparecem após clique; histórico abre; `scriptCount=1`; `inlineHistoryScriptCount=0`; `errors=[]`.

## Implementado
- `templates/graduation/_progress_card.html`: removeu informações detalhadas da exposição inicial e colocou tempo, aulas, conclusão, status e histórico dentro de `<details class="graduation-progress-details">`.
- `templates/graduation/_progress_card.html`: substituiu o script inline do histórico por asset estático versionado.
- `static/system/js/graduation/progress-card.js`: centraliza abertura/fechamento do modal de histórico.
- `static/system/css/portal/portal.css`: adicionou estilos do controle "Mais sobre a graduação" e do corpo do detalhe.
- `templates/base.html`: atualizou o cache-busting do `portal.css` para `20260507a`.
- `system/tests/test_graduation.py`: adicionou cobertura para home de aluno e professor com dropdown fechado por padrão.

## Desvios do plano
- Não houve consulta externa; não havia API nova de biblioteca a confirmar.
- Browser Use não conectou ao painel ativo nesta revisão; a validação visual foi feita por Playwright MCP.
- O servidor local foi reiniciado porque a instância anterior servia o template antigo em memória.

## Pendências
Nenhuma pendência desta alteração.
