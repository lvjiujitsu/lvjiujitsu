# PRD-004: Corrigir Catálogo de Materiais por Variante

## Resumo do que será implementado
Corrigir o fluxo de materiais para operar por variante real de produto, com tamanhos e cores tradicionais de Jiu Jitsu nas seeds, seleção por dropdown no cadastro e na loja, adição ao carrinho por variante e baixa de estoque coerente quando o pedido for marcado como pago.

## Tipo de demanda
Correção pontual com ajuste estrutural de fluxo

## Problema atual
O sistema já possui `ProductVariant`, mas o cadastro e a loja do aluno ainda montam carrinho por `Product` puro. Isso impede seleção correta de cor/tamanho, limita a composição do carrinho e inviabiliza a baixa correta de estoque por variante.

## Objetivo
- usar variantes reais no fluxo de materiais
- ajustar as seeds para faixas e kimonos com tamanhos e cores tradicionais
- permitir adicionar ao carrinho combinações distintas da mesma linha de produto
- baixar estoque por variante quando o pedido for efetivamente pago

## Context Ledger
### Arquivos lidos integralmente
- `CLAUDE.md`
- `system/models/product.py`
- `system/models/registration_order.py`
- `system/services/registration_checkout.py`
- `system/services/seeding.py`
- `system/services/product_management.py`
- `system/services/stripe_checkout.py`
- `system/services/stripe_webhooks.py`
- `system/services/asaas_checkout.py`
- `system/services/asaas_webhooks.py`
- `system/services/membership.py`
- `system/forms/product_forms.py`
- `system/views/product_views.py`
- `system/views/billing_admin_views.py`
- `system/tests/test_product_models.py`
- `system/tests/test_product_views.py`
- `system/tests/test_services.py`
- `templates/login/register.html`
- `templates/products/product_catalog.html`
- `templates/products/product_store.html`
- `templates/products/product_detail.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `static/system/css/portal/class-catalog.css`
- `static/system/css/billing/billing.css`

### Arquivos adjacentes consultados
- `system/urls.py`
- `system/tests/test_views.py`

### Internet / documentação oficial
- IBJJF Uniform — https://ibjjf.com/uniform
- IBJJF Graduation System — https://ibjjf.com/graduation-system
- Pretorian size guide — convenção de mercado para `A1-A4` e `M1-M3`
- Black Belt Store / Red Dragon — oferta real de faixas em `A1-A4` e linhas com `M1-M3`

### MCPs / ferramentas verificadas
- shell / PowerShell — ok — leitura integral e testes do projeto
- internet / busca web — ok — consulta de referências de tamanhos e cores
- Playwright MCP — ok — validação visual em `/register/` e `/store/`

### Limitações encontradas
- não há campo próprio de variante em `RegistrationOrderItem`, e a política local proíbe migração sem autorização explícita

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django monolítico com checkout server-rendered, seguindo SDD + TDD.

### Ação
Corrigir o catálogo de materiais para trabalhar por variante real em seeds, carrinho, pedido e baixa de estoque.

### Contexto
O projeto já modela variantes em `ProductVariant`, mas o fluxo de compra e matrícula ainda ignora esse contrato e fecha itens apenas por `Product`.

### Restrições
- sem migração
- sem hardcode frágil
- sem mascaramento de erro
- leitura integral obrigatória
- validação obrigatória
- manter views finas e regra em services

### Critérios de aceite
- [x] As seeds devem refletir tamanhos e cores tradicionais de faixas e kimonos (verificável por: teste)
- [x] O cadastro deve permitir escolher uma variante e adicionar ao carrinho mais de uma combinação do mesmo produto (verificável por: validação visual)
- [x] A loja do aluno deve permitir a mesma composição por variante (verificável por: validação visual)
- [x] A criação de pedido deve registrar snapshot do item com variante selecionada (verificável por: teste)
- [x] A confirmação de pagamento/manual paid deve baixar estoque da variante correta uma única vez (verificável por: teste)

### Evidências esperadas
- testes passando
- console do navegador limpo
- terminal sem stack trace
- carrinho funcionando em desktop e mobile

### Formato de saída
Código implementado + testes + evidências de validação

## Escopo
- atualizar seeds de produtos e variantes
- atualizar payload do catálogo de materiais
- atualizar parser/validação do carrinho para trabalhar por variante
- atualizar criação de pedidos de matrícula e loja
- implementar baixa de estoque por variante em transições de pagamento
- atualizar UI do cadastro e da loja do aluno
- cobrir com testes

## Fora do escopo
- migração para adicionar FK explícita de variante em item de pedido
- reembolso com reposição automática de estoque
- redesign completo das páginas públicas de materiais

## Arquivos impactados
- `docs/prd/PRD-004-corrigir-catalogo-materiais-por-variante.md`
- `system/services/seeding.py`
- `system/services/registration_checkout.py`
- `system/forms/product_forms.py`
- `system/forms/registration_forms.py`
- `system/services/membership.py`
- `system/services/stripe_webhooks.py`
- `system/services/asaas_webhooks.py`
- `system/views/product_views.py`
- `templates/login/register.html`
- `templates/products/product_store.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `static/system/js/products/product-store.js`
- `static/system/css/portal/class-catalog.css`
- `static/system/css/billing/billing.css`
- `system/tests/test_product_models.py`
- `system/tests/test_product_views.py`
- `system/tests/test_services.py`

## Riscos e edge cases
- draft antigo do cadastro com payload legado de produtos
- pedido pago duas vezes por retry de webhook ou ação manual repetida
- falta de schema próprio de variante em item de pedido
- risco residual de concorrência se o estoque mudar entre criação do pedido e confirmação do pagamento

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem migrações
- sem hardcode
- sem mascaramento de erro
- leitura integral obrigatória
- validação obrigatória

## Plano
- [x] 1. Contexto e modelagem do fluxo por variante
- [x] 2. Testes de seeds, pedido e baixa de estoque
- [x] 3. Implementação backend
- [x] 4. Implementação UI do cadastro e loja
- [x] 5. Validação técnica completa
- [x] 6. Validação visual desktop e mobile
- [x] 7. Limpeza final
- [x] 8. Atualização documental

## Validação visual
### Desktop
- `/register/` etapa Materiais com seleção por variante e carrinho
- loja do aluno com seleção por variante e carrinho

### Mobile
- mesmos fluxos com viewport móvel

### Console do navegador
- sem erros JS críticos

### Terminal
- sem stack trace

## Validação ORM
### Banco
- sem migração

### Shell checks
- não obrigatório se testes cobrirem pedido e baixa de estoque

### Integridade do fluxo
- itens do pedido devem carregar snapshot legível da variante

## Validação de qualidade
### Sem hardcode
- listas de tamanhos e cores concentradas nas seeds

### Sem estruturas condicionais quebradiças
- payload e resolução de variante centralizados em service

### Sem `except: pass`
- não introduzir

### Sem mascaramento de erro
- carrinho inválido deve falhar explicitamente

### Sem comentários e docstrings desnecessários
- não introduzir

## Evidências
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` → 195 testes OK
- `.\.venv\Scripts\python.exe manage.py check` → sem erros
- `.\.venv\Scripts\python.exe manage.py check --deploy` → apenas warnings esperados de ambiente local (`DEBUG`, cookies/SSL/HSTS)
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` → OK
- `.\.venv\Scripts\python.exe manage.py showmigrations` → sem migrações novas
- Playwright mobile em `/register/` → categorias `Faixas`, `Kimonos`, `Rash Guard`, `Patches`; payload `variant_id`; carrinho renderizado
- Playwright desktop e mobile em `/store/` → dropdown por categoria, seleção de variante, quantidade 2 da mesma variante + item de outra variante no mesmo carrinho
- Console do navegador → 0 errors / 0 warnings
- Terminal do servidor (`runserver-8000.out.log` / `runserver-8000.err.log`) → sem stack trace

## Implementado
- Seeds de produtos remodeladas para variantes tradicionais:
  - faixas com cores de graduação e tamanhos `A1-A4` / `M1-M3`
  - kimonos LV adulto e infantil nas cores `Branco`, `Azul`, `Preto`
  - 2 unidades por variante seeded
- Catálogo de materiais do cadastro e da loja agora opera por variante real, com payload contendo `variant_id`, `color`, `size`, `label` e `snapshot_name`
- Carrinho do cadastro e da loja permite:
  - adicionar 2 unidades da mesma cor/tamanho
  - combinar cores e tamanhos diferentes no mesmo pedido
  - manter snapshot legível do item selecionado
- Criação de pedido e confirmação de pagamento baixam estoque da variante correta com proteção idempotente

## Desvios do plano
- Como migração não foi autorizada, o vínculo da variante no item do pedido permaneceu como snapshot textual em `RegistrationOrderItem.product_name`, com resolução de variante no service de baixa de estoque

## Pendências
- Nenhuma dentro do escopo definido
