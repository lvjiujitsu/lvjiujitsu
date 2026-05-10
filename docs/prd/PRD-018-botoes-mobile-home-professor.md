# PRD-018: Botões Mobile Na Home Do Professor

## Resumo do que será implementado
Ajustar a responsividade dos controles da home do professor para que, no celular, os botões de ação ocupem a largura inteira da linha.

## Tipo de demanda
Correção pontual de UI responsiva.

## Problema atual
Na viewport mobile de 375px, os botões `Meu financeiro`, `Criar aulão`, `Gerir cronograma` e o summary `Mais sobre a graduação` ficam com largura apenas do conteúdo, gerando áreas vazias e alinhamento inconsistente dentro dos cards.

## Objetivo
Em telas pequenas, cada ação principal dos cards da home do professor deve ocupar a linha inteira, preservando o comportamento desktop atual.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `templates/home/instructor/dashboard.html`
- `templates/graduation/_progress_card.html`
- `templates/base.html`

### Arquivos adjacentes consultados
- `static/system/css/portal/portal.css`
- `system/tests/test_views.py`
- `system/tests/test_graduation.py`
- comentários visuais do navegador em `http://localhost:8000/home/instructor/`

### Internet / documentação oficial
- Não aplicável. Correção local de CSS.

### MCPs / ferramentas verificadas
- PowerShell — OK — leitura de arquivos e execução de comandos.
- Browser Use — OK para DOM da página; screenshot via CDP indisponível por timeout.
- Playwright local — OK com execução fora do sandbox para validação visual e métricas de layout.

### Limitações encontradas
- Nenhuma.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django MVT e CSS responsivo seguindo SDD + validação visual.

### Ação
Corrigir a responsividade dos botões selecionados na home do professor.

### Contexto
A home do professor usa templates Django e o CSS compartilhado `portal.css`.

### Restrições
- sem migrações
- sem alterar regras de negócio
- sem CSS inline
- atualizar versão do asset CSS referenciado no template
- validar em viewport mobile real

### Critérios de aceite
- [x] Em 375px de largura, `Meu financeiro` deve ocupar a linha inteira do card.
- [x] Em 375px de largura, `Criar aulão` e `Gerir cronograma` devem ocupar linhas inteiras.
- [x] Em 375px de largura, `Mais sobre a graduação` deve ocupar a linha inteira do card.
- [x] Em desktop, os botões devem manter layout inline quando houver espaço.
- [x] `manage.py check` deve passar.
- [x] `collectstatic --noinput` deve passar.

### Evidências esperadas
- Screenshot ou inspeção visual mobile.
- Console do navegador sem erro crítico.
- `manage.py check`.
- `collectstatic --noinput`.

### Formato de saída
Código implementado + evidências de validação + status final.

## Escopo
- CSS responsivo em `static/system/css/portal/portal.css`.
- Cache busting do CSS em `templates/base.html`.

## Fora do escopo
- Alterar fluxo da home do professor.
- Alterar texto, rotas ou permissões.
- Criar migrações.

## Arquivos impactados
- `docs/prd/PRD-018-botoes-mobile-home-professor.md`
- `static/system/css/portal/portal.css`
- `templates/base.html`

## Riscos e edge cases
- Regra global de ações pode afetar outros dashboards no mobile; isso é aceitável quando o contexto também for botão de ação de card.
- Desktop não deve ser afetado porque a regra será limitada a breakpoint mobile.

## Regras e restrições
- SDD antes de código
- sem hardcode de segredo
- sem migrações
- validação visual obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Testes / validação Red visual
- [x] 4. Implementação
- [x] 5. Validação completa
- [x] 6. Limpeza final
- [x] 7. Atualização documental

## Validação visual
### Desktop
Validado em Playwright com viewport 1024x768. O container de ações manteve `display:flex`, `flex-direction: row`; `Criar aulão` e `Gerir cronograma` ficaram na mesma linha.

### Mobile
Validado em Playwright com viewport 375x667. Larguras finais:
- `Meu financeiro`: 321px de 321px do container.
- `Mais sobre a graduação`: 321px de 321px do container.
- `Criar aulão`: 321px de 321px do container.
- `Gerir cronograma`: 321px de 321px do container.

### Console do navegador
Sem erros de console durante a validação Playwright.

### Terminal
`manage.py check`, `collectstatic --noinput`, testes direcionados e suíte completa executados.

## Validação ORM
### Banco
Não aplicável.

### Shell checks
Não aplicável.

### Integridade do fluxo
Não alterar rotas nem persistência.

## Validação de qualidade
### Sem hardcode
Sem segredos ou dados variáveis.

### Sem estruturas condicionais quebradiças
CSS por breakpoint.

### Sem `except: pass`
Não aplicável.

### Sem mascaramento de erro
Não aplicável.

### Sem comentários e docstrings desnecessários
Não adicionar comentário de código desnecessário.

## Evidências
- `manage.py check`: sem issues.
- `manage.py collectstatic --noinput`: 165 arquivos copiados.
- Testes direcionados: 4 testes OK para home do professor e card de graduação.
- Suíte completa: `manage.py test --verbosity 2` passou com 329 testes.
- Validação mobile Playwright: viewport 375x667, quatro controles com largura igual ao container e console sem erros.
- Validação desktop Playwright: viewport 1024x768 manteve ações inline.

## Implementado
- Ajustado `static/system/css/portal/portal.css` para que `.dashboard-section-heading > div` não capture containers `.dashboard-section-actions`.
- No breakpoint `max-width: 520px`, ações do dashboard empilham em coluna, com largura total e altura normal.
- `summary.graduation-progress-summary` passa a ocupar largura total no mobile.
- Atualizado cache-busting do `portal.css` em `templates/base.html`.

## Desvios do plano
- Browser Use carregou o DOM da página, mas screenshot via CDP expirou. A validação visual foi concluída com Playwright local.

## Pendências
- Nenhuma.
