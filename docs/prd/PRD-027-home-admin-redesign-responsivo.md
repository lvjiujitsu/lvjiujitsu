# PRD-027: Redesign responsivo da home master

## Resumo do que será implementado
Reimplementar a home do administrador técnico para seguir o padrão visual aplicado em Pessoas: página larga, seções claras por domínio, atalhos sempre visíveis, tema claro/escuro preservado e sem controles decorativos ou disfuncionais.

## Tipo de demanda
Refatoração de UI.

## Problema atual
A home master ainda usa a estrutura antiga de `panel-card` com listas de atalhos pouco agrupadas. Em desktop o conteúdo não aproveita bem a largura disponível e em mobile os grupos não deixam claro onde cada rotina administrativa se encaixa.

## Objetivo
- Padronizar a home master com o novo visual do portal.
- Agrupar atalhos por domínio: Cadastros, Tatame, Materiais, Graduação, Financeiro e Técnico.
- Remover dependência de toggle ou ação escondida.
- Manter todos os links atuais acessíveis.

## Context Ledger
### Arquivos lidos integralmente
- `templates/home/admin/dashboard.html`
- `templates/base.html`
- `static/system/css/portal/portal.css`
- `system/views/home_views.py`
- `system/tests/test_views.py`

### Arquivos adjacentes consultados
- `templates/home/administrative/dashboard.html`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_product_views.py`
- `system/tests/test_plan_views.py`
- `system/tests/test_calendar.py`

### Internet / documentação oficial
- Não aplicável.

### MCPs / ferramentas verificadas
- Django test runner — OK.
- Playwright — OK.

### Limitações encontradas
- Sem criação de pastas.
- Sem migrações.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django MVT seguindo SDD + TDD + CSS responsivo.

### Ação
Reimplementar a home master administrativa preservando links e permissões.

### Contexto
A home master é a superfície técnica de entrada do administrador e deve ser clara, direta e consistente com a tela de Pessoas.

### Restrições
- sem hardcode de regra de negócio
- sem JavaScript desnecessário
- CSS em `static/`
- templates em `templates/`
- validação obrigatória

### Critérios de aceite
- [ ] A home master deve carregar sem botão `Mostrar mais`.
- [ ] A home master deve conter grupos: Cadastros, Tatame, Materiais, Graduação, Financeiro e Técnico.
- [ ] Todos os links antigos devem permanecer acessíveis.
- [ ] O layout deve usar a largura desktop de maneira semelhante à tela de Pessoas.
- [ ] A home deve funcionar sem overflow horizontal em desktop e mobile.

### Evidências esperadas
- testes passando
- `manage.py check`
- `collectstatic --noinput`
- Playwright desktop/mobile sem erro de console

## Escopo
- `templates/home/admin/dashboard.html`
- `static/system/css/portal/admin-dashboard.css`
- `system/tests/test_views.py`
- documentação deste PRD

## Fora do escopo
- Alterar permissões.
- Alterar rotas.
- Alterar dashboards de professor, aluno ou administrativo convencional.

## Arquivos impactados
- `docs/prd/PRD-027-home-admin-redesign-responsivo.md`
- `templates/home/admin/dashboard.html`
- `static/system/css/portal/admin-dashboard.css`
- `system/tests/test_views.py`

## Riscos e edge cases
- Remover link acidentalmente.
- Deixar cards largos demais em mobile.
- Reintroduzir texto decorativo sem função.

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode
- sem migrações
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Teste de contrato
- [x] 3. Implementação
- [x] 4. Validação técnica
- [x] 5. Validação visual

## Validação visual
### Desktop
OK. Playwright em 1622x1411 confirmou largura útil de 1480px, 3 colunas e 6 seções.

### Mobile
OK. Playwright em 390x900 confirmou 1 coluna e ausência de overflow horizontal.

### Console do navegador
OK. Sem erros críticos capturados.

### Terminal
OK. Testes focados, `manage.py check`, `collectstatic` e `git diff --check` executados.

## Evidências
- Red: `test_master_dashboard_uses_grouped_responsive_layout` falhou por ausência de `admin-dashboard.css`.
- Green: testes focados da home master e atalhos adjacentes passaram.
- Playwright desktop/mobile passou.

## Implementado
- `templates/home/admin/dashboard.html` reestruturado em seções por domínio.
- `static/system/css/portal/admin-dashboard.css` criado.
- Testes de contrato atualizados.

## Desvios do plano
Nenhum.

## Pendências
Nenhuma pendência conhecida nesta etapa.
