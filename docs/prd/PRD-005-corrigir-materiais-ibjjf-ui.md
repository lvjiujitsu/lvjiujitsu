# PRD-005: Corrigir materiais por regra IBJJF e UI de seleção

## Resumo do que será implementado
Corrigir catálogo de materiais do cadastro para respeitar combinações de faixas por graduação IBJJF, manter kimonos LV com cores tradicionais e ajustar a UI para seleção clara de opção/quantidade e adição ao carrinho.

## Tipo de demanda
Correção pontual

## Problema atual
As faixas estão com matriz inválida de cor+tamanho (incluindo combinações infantis não permitidas, como M preta/marrom), e a etapa de materiais no cadastro está com CSS incompleto, quebrando visual e usabilidade do dropdown/quantidade/botão de adicionar.

## Objetivo
Garantir matriz válida de variantes, manter seed com 2 unidades por variante, preservar seleção por categoria com dropdown e permitir adicionar múltiplas combinações ao carrinho com boa usabilidade em desktop e mobile.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `system/services/seeding.py`
- `system/services/registration_checkout.py`
- `system/tests/test_product_models.py`
- `templates/login/register.html`
- `static/system/css/auth/login.css`

### Arquivos adjacentes consultados
- `static/system/js/auth/registration-wizard-clean.js`
- `system/views/product_views.py`
- `system/models/product.py`
- `docs/prd/PRD-004-corrigir-catalogo-materiais-por-variante.md`

### Internet / documentação oficial
- IBJJF Uniform Requirements — `https://ibjjf.com/uniform`
- IBJJF Graduation System — `https://ibjjf.com/graduation-system`

### MCPs / ferramentas verificadas
- Context7 MCP — ok — `npx -y @upstash/context7-mcp --help`
- Playwright MCP — ok — `npx -y @playwright/mcp@latest --headless --help`

### Limitações encontradas
- Sem limitação crítica para a correção.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD.

### Ação
Implementar ajuste de regras de variantes e correção visual/funcional da etapa de materiais no cadastro.

### Contexto
Fluxo de materiais do cadastro impacta seleção de item, montagem do carrinho e baixa posterior de estoque por variante.

### Restrições
- sem hardcode frágil
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

### Critérios de aceite
- [ ] Faixas não devem permitir variantes infantis marrom/preta (M1-M3).
- [ ] Kimonos LV devem manter cores tradicionais branco, azul e preto.
- [ ] Seed deve manter 2 unidades por variante.
- [ ] Etapa Materiais deve exibir seleção por dropdown e botão de adicionar utilizável em desktop/mobile.

### Evidências esperadas
- testes de produto/seed passando
- tela de materiais funcional sem quebra visual crítica

### Formato de saída
Código implementado + testes + evidências de validação

## Escopo
- ajuste de seed de produtos/variantes
- ajuste de ordenação de cores no payload de catálogo
- ajuste CSS da etapa de materiais
- atualização de teste da seed

## Fora do escopo
- alteração de schema
- redesign completo da etapa de cadastro

## Arquivos impactados
- `system/services/seeding.py`
- `system/services/registration_checkout.py`
- `system/tests/test_product_models.py`
- `static/system/css/auth/login.css`
- `templates/login/register.html`

## Riscos e edge cases
- incompatibilidade de drafts antigos com variantes removidas
- diferença de renderização do select nativo entre navegadores

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

## Plano
- [ ] 1. Ajustar matriz de variantes em seed
- [ ] 2. Ajustar ordenação de cor para “Branca”
- [ ] 3. Corrigir estilos da etapa de materiais
- [ ] 4. Atualizar cache-busting do asset
- [ ] 5. Atualizar testes de seed
- [ ] 6. Validar testes/checks
- [ ] 7. Limpeza final
- [ ] 8. Atualização documental

## Validação visual
### Desktop
Dropdown de opção, controle de quantidade e botão de adicionar renderizam corretamente.

### Mobile
Layout permanece legível e botão ocupa largura adequada.

### Console do navegador
Sem erro JS crítico no fluxo.

### Terminal
Sem stack trace no fluxo testado.

## Validação ORM
### Banco
Sem migrações novas.

### Shell checks
Opcional para esta correção.

### Integridade do fluxo
Carrinho continua serializando `variant_id` e quantidade.

## Validação de qualidade
### Sem hardcode
Matriz de cor/tamanho centralizada em constantes.

### Sem estruturas condicionais quebradiças
Sem novas ramificações frágeis.

### Sem `except: pass`
Nenhum introduzido.

### Sem mascaramento de erro
Fluxo mantém falhas explícitas existentes.

### Sem comentários e docstrings desnecessários
Nenhum introduzido.

## Evidências
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` → 195 testes OK
- `.\.venv\Scripts\python.exe manage.py check` → sem issues
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` → concluído
- `.\.venv\Scripts\python.exe manage.py showmigrations` → sem migrações novas

## Implementado
- Seeds de faixas ajustadas para matriz IBJJF:
  - adulto (`A1-A4`): branca, azul, roxa, marrom, preta
  - infantil (`M1-M3`): branca, cinza, amarela, laranja, verde
- Kimonos LV mantidos com cores tradicionais (`Branco`, `Azul`, `Preto`) e 2 unidades por variante
- Ordenação de catálogo atualizada para reconhecer cor `Branca`
- CSS da etapa Materiais no cadastro atualizado com:
  - dropdown de opção visível e utilizável
  - controle de quantidade consistente
  - botão de adicionar ao carrinho com estilo/estado correto
  - preview do carrinho com ações e responsividade desktop/mobile
- Cache-busting do `registration-wizard-clean.js` atualizado em `register.html`
- Teste de seed ajustado para refletir regra nova e impedir `M1-M3` marrom/preta

## Desvios do plano
Nenhum até o momento.

## Pendências
- Executar validação técnica e visual final.
