# PRD-008: Consolidar landing pública e remover páginas públicas obsoletas

## Resumo do que será implementado

Reduzir a área pública do portal para apenas três funções essenciais — login, cadastro e contato — eliminando o menu intermediário, as páginas de catálogo público de planos e materiais e a página informativa de turmas. A nova landing (raiz do site, `/`) passa a ser o próprio formulário de login com dois CTAs adicionais: "Criar conta" e "Falar com a LV" (WhatsApp).

## Tipo de demanda

Refatoração arquitetural com remoção de superfície pública. Mudança em URLs, views, templates, testes e referências cruzadas. Sem alteração de schema.

## Problema atual

A área pública hoje carrega cinco caminhos diferentes (Login, Cadastro, Turmas e Horários, Materiais, Planos) servidos por views distintas (`PortalHomeView`, `PortalInfoView`, `PlanCatalogView`, `ProductCatalogView`, `PortalLoginView`, `PortalRegisterView`) e nomes de URL legados (`templates/login/login.html`, `legacy-home`, `legacy-info`...). Isso:

1. **Dilui a captura de leads.** O usuário entra na home e tem 5 botões para escolher; o caminho de "comprar/contratar" fica perdido.
2. **Mantém código morto.** `PlanCatalogView` e `ProductCatalogView` exibem informação redundante: planos já aparecem dentro do wizard de cadastro e na troca de plano; materiais ficam na loja autenticada `/store/`. A página `/info/` foi superada pelo calendário.
3. **Polui URL legada.** Quatro rotas `templates/login/...` viraram aliases vivos por compatibilidade — agora obsoletas.

## Objetivo

- Tornar a tela inicial do site o próprio formulário de login com dois CTAs claros: cadastro e WhatsApp.
- Remover toda página pública que não tenha função direta de captação ou autenticação.
- Limpar nomes de URL `legacy-*` substituindo pelos canônicos.

## Context Ledger

### Arquivos lidos integralmente

- [system/urls.py](system/urls.py)
- [system/views/auth_views.py](system/views/auth_views.py)
- [system/views/plan_views.py](system/views/plan_views.py)
- [system/views/product_views.py](system/views/product_views.py)
- [system/views/__init__.py](system/views/__init__.py)
- [templates/login/login.html](templates/login/login.html)
- [templates/login/login_form.html](templates/login/login_form.html)
- [templates/login/info.html](templates/login/info.html)
- [templates/login/register.html](templates/login/register.html)
- [templates/login/password_reset_*.html] (4 arquivos)
- [templates/plans/plan_catalog.html](templates/plans/plan_catalog.html)
- [templates/products/product_catalog.html](templates/products/product_catalog.html)
- [templates/home/student/dashboard.html](templates/home/student/dashboard.html)
- [system/views/payment_views.py](system/views/payment_views.py)
- Testes: `test_views.py`, `test_plan_views.py`, `test_product_views.py`, `test_class_portal_views.py`

### Arquivos adjacentes consultados

- `static/system/js/auth/registration-wizard-clean.js` (referência indireta a `legacy-*` — não há nenhuma)

### Internet / documentação oficial

- N/A (pura refatoração interna).

### MCPs / ferramentas verificadas

- Todas as ferramentas locais (Read, Grep, Glob, Edit, Write) — funcionando.

### Limitações encontradas

- Nenhuma. Refatoração 100% interna.

## Prompt de execução

### Persona

Agente Django sênior em modo control-first com SDD + TDD.

### Ação

Remover quatro views públicas obsoletas (`PortalHomeView`, `PortalInfoView`, `PlanCatalogView`, `ProductCatalogView`), seus templates e URLs, e fazer a raiz do site servir `PortalLoginView` com dois CTAs novos (cadastro + WhatsApp).

### Contexto

O sistema é o portal da academia LV Jiu Jitsu. A área autenticada (dashboard, store, plan-change, calendário) já cobre todas as funções operacionais. A área pública precisa apenas captar lead e autenticar.

### Restrições

- sem hardcode de segredo
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória (concluída acima)
- preservar `name` canônico das URLs (`root`, `login`, `register`)
- substituir todas as `legacy-*` referenciadas no projeto pelas canônicas antes de remover as rotas
- número de WhatsApp `+55 62 99987-6471` (link `https://wa.me/5562999876471`) mantido como na home antiga

### Critérios de aceite

- [ ] `/` renderiza `templates/login/login_form.html` (verificável: `manage.py test` + GET na raiz)
- [ ] `login_form.html` tem botão visível "Criar conta" linkando para `/register/`
- [ ] `login_form.html` tem botão visível "Falar com a LV" linkando para `https://wa.me/5562999876471`
- [ ] `/info/`, `/plans-catalog/`, `/materials/` e as 4 rotas `templates/login/...` retornam 404 (verificável: assertions em testes)
- [ ] Templates `login.html`, `info.html`, `plan_catalog.html`, `product_catalog.html` não existem mais no repositório (verificável: `Glob`)
- [ ] Views `PortalHomeView`, `PortalInfoView`, `PlanCatalogView`, `ProductCatalogView` não existem em `system/views/` (verificável: `Grep`)
- [ ] Nenhum template ou código Python referencia `legacy-home`, `legacy-login-form`, `legacy-register`, `legacy-info`, `info`, `plan-catalog`, `product-catalog` (verificável: `Grep`)
- [ ] `manage.py test --verbosity 2` passa com 0 falhas
- [ ] `manage.py check` passa sem warnings novos

### Evidências esperadas

- testes passando
- console limpo no navegador na raiz
- screenshot da nova landing com 3 elementos: form, CTA cadastro, CTA WhatsApp

### Formato de saída

Código + testes + relatório.

## Escopo

### Remoção
1. View `PortalHomeView` em `system/views/auth_views.py`.
2. View `PortalInfoView` em `system/views/auth_views.py`.
3. View `PlanCatalogView` em `system/views/plan_views.py` (e helper `_build_plan_groups`, constantes `PUBLIC_CATALOG_GROUP_ORDER` e `AUDIENCE_LABELS` se não usados em outro lugar).
4. View `ProductCatalogView` em `system/views/product_views.py` (preservar `_build_product_groups` se for usado pela `ProductStoreView`).
5. Template `templates/login/login.html`.
6. Template `templates/login/info.html`.
7. Template `templates/plans/plan_catalog.html`.
8. Template `templates/products/product_catalog.html`.
9. URL `/` apontando para `PortalHomeView` → trocar para `PortalLoginView`.
10. URL `/info/`.
11. URL `/plans-catalog/`.
12. URL `/materials/`.
13. URLs legadas `templates/login/login.html`, `templates/login/login-form.html`, `templates/login/cadastro.html`, `templates/login/informacoes.html`.
14. Exports correspondentes em `system/views/__init__.py`.

### Substituição de referências
15. Templates: `legacy-home` → `root`, `legacy-login-form` → `login`, `legacy-register` → `register`.
16. Código Python (auth_views, payment_views): `legacy-login-form` → `login`.
17. Testes: idem.
18. `templates/home/student/dashboard.html`: link "Ver planos" passa a apontar para `system:plan-change-select` (estudante autenticado já usa esse fluxo).

### Atualização de UX
19. `templates/login/login_form.html`:
    - Remover botão "Voltar" (raiz não tem para onde voltar).
    - Adicionar bloco abaixo do form com link "Ainda não possui cadastro? **Criar conta**" → `/register/`.
    - Adicionar botão "Falar com a LV" (mesmo estilo da landing antiga) → `https://wa.me/5562999876471`.
    - Bumpar cache-busting do CSS.

### Testes
20. Remover testes de páginas que sumiram.
21. Substituir referências `legacy-*` em testes pelos nomes canônicos.
22. Adicionar teste do CTA cadastro e WhatsApp na nova landing.

## Fora do escopo

- Loja na home autenticada com pré-pedido + notificação quando produto chega — vai para PRD-009.
- Nenhuma alteração em CSS/JS além do bump de cache no `login.css`.

## Arquivos impactados

- [system/urls.py](system/urls.py)
- [system/views/auth_views.py](system/views/auth_views.py)
- [system/views/plan_views.py](system/views/plan_views.py)
- [system/views/product_views.py](system/views/product_views.py)
- [system/views/payment_views.py](system/views/payment_views.py)
- [system/views/__init__.py](system/views/__init__.py)
- [templates/login/login_form.html](templates/login/login_form.html)
- [templates/login/register.html](templates/login/register.html)
- [templates/login/password_reset_form.html](templates/login/password_reset_form.html)
- [templates/login/password_reset_done.html](templates/login/password_reset_done.html)
- [templates/login/password_reset_complete.html](templates/login/password_reset_complete.html)
- [templates/login/password_reset_confirm.html](templates/login/password_reset_confirm.html)
- [templates/home/student/dashboard.html](templates/home/student/dashboard.html)
- [system/tests/test_views.py](system/tests/test_views.py)
- [system/tests/test_plan_views.py](system/tests/test_plan_views.py)
- [system/tests/test_product_views.py](system/tests/test_product_views.py)
- [system/tests/test_class_portal_views.py](system/tests/test_class_portal_views.py)
- **Apagar:** `templates/login/login.html`, `templates/login/info.html`, `templates/plans/plan_catalog.html`, `templates/products/product_catalog.html`

## Riscos e edge cases

- **Bookmarks externos** apontando para `/info/`, `/plans-catalog/`, `/materials/` ou `templates/login/...` ficarão 404. Aceitável: páginas eram informacionais e serão substituídas pelo wizard de cadastro/troca de plano.
- **SEO**: nenhum índice externo conhecido para essas páginas. Não há plano de redirect 301.
- **Templates de reset de senha** continuam linkando para login após reset — só muda o nome do `name` (de `legacy-login-form` para `login`).

## Regras e restrições

- SDD antes de código (PRD aqui)
- TDD ajustando os testes em paralelo às remoções
- sem hardcode
- sem mascaramento
- sem migração

## Plano

- [x] 1. Contexto e leitura integral
- [ ] 2. Substituir `legacy-*` por nomes canônicos em todo lugar (templates + Python + testes)
- [ ] 3. Atualizar `login_form.html` com CTAs novos e remover botão Voltar
- [ ] 4. Trocar rota `/` para `PortalLoginView`
- [ ] 5. Remover views `PortalHomeView`, `PortalInfoView`, `PlanCatalogView`, `ProductCatalogView` + exports
- [ ] 6. Remover URLs `/info/`, `/plans-catalog/`, `/materials/` e as 4 legadas
- [ ] 7. Apagar templates obsoletos (4)
- [ ] 8. Atualizar `dashboard.html` (link plan-catalog → plan-change-select)
- [ ] 9. Limpar testes
- [ ] 10. Bumpar cache CSS/JS
- [ ] 11. Validação `manage.py check`
- [ ] 12. Limpeza final
- [ ] 13. Relatório

## Validação visual

### Desktop
- `/` mostra form login + CTA cadastro + CTA WhatsApp
- `/login/` continua respondendo (mesma view, agora também na raiz)
- `/register/` continua intacta
- `/info/`, `/plans-catalog/`, `/materials/` retornam 404

### Mobile
- mesma tela em viewport ≤ 480px

### Console
- sem 404 de assets
- sem erro JS

## Validação ORM

### Banco
- Nenhuma alteração de schema.

### Shell checks
- Nenhum dado tocado.

### Integridade do fluxo
- Login + cadastro + recuperação de senha funcionam intactos.

## Validação de qualidade

### Sem hardcode
- Número de WhatsApp aparece apenas em `login_form.html` como link, alinhado à landing antiga.

### Sem estruturas condicionais quebradiças
- Refatoração subtractiva.

### Sem `except: pass`
- Nada introduzido.

### Sem mascaramento de erro
- Nada.

### Sem comentários e docstrings desnecessários
- Nada.

## Evidências

(a preencher após implementação)

## Implementado

(a preencher após implementação)

## Desvios do plano

(a preencher após implementação)

## Pendências

- PRD-009: loja na home autenticada com pré-pedido + notificação de chegada de produto.
