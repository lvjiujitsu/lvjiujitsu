# PRD-014: Correções de UI do wizard de cadastro

## Resumo do que será implementado

Três correções pontuais de UI no wizard de cadastro (`register.html` + `register.js`):

1. **Botão Voltar oculto no pós-pagamento** — `showPostPaymentMode` oculta `#wizard-back` com `visibility:hidden` em `step-products` e `step-review`. O botão deve permanecer visível e funcional.
2. **"Resumo do cadastro" em lugar errado** — `renderConfirmationSummary('products-confirm-area')` renderiza o painel na tela de materiais. Esse painel deve aparecer **somente** na tela "Confirmar cadastro" (`step-review`).
3. **Botões de pagamento de materiais divergentes** — O botão PIX no carrinho de materiais tem `style="background:var(--text);color:var(--panel)"` (estilo inline diferente do checkout do plano). Ambos os botões de pagamento de materiais devem usar apenas `btn-checkout-pay`, sem override inline.

## Tipo de demanda

Correção pontual de UI — sem mudança de backend, schema ou fluxo funcional.

## Problema atual

| # | Onde | O que está errado |
|---|---|---|
| 1 | `showPostPaymentMode()` no JS | `back.style.visibility = 'hidden'` oculta o botão voltar em `step-products` e `step-review` |
| 2 | `showPostPaymentMode()` no JS | Chama `renderConfirmationSummary('products-confirm-area')` quando `stepId === 'step-products'` |
| 3 | Template `register.html`, sub-view carrinho | `<button id="products-btn-pay-pix" ... style="background:var(--text);color:var(--panel)">` |

## Objetivo

- Botão Voltar visível em todas as fases do wizard, com comportamento contextual por fase.
- "Resumo do cadastro" exclusivo da tela `step-review`.
- Botões de pagamento de materiais visualmente idênticos ao checkout do plano.

## Context Ledger

### Arquivos lidos integralmente
- `templates/login/register.html` — template completo
- `static/system/js/auth/register.js` — navegação, `showPostPaymentMode`, `renderConfirmationSummary`, `onEnterCheckout`
- `static/system/css/auth/register.css` — `btn-checkout-pay`, `btn-checkout-later`, `wizard-back`, `reg-confirm-panel`

### Arquivos adjacentes consultados
- `system/views/auth_views.py` — `PortalRegistrationView`, `MaterialsCheckoutView`, `FinalizeRegistrationView`

## Escopo

### Fix 1 — Botão Voltar no pós-pagamento

**Comportamento por fase:**

| Fase | Ação do botão Voltar |
|---|---|
| Etapas do wizard (step-profile … step-checkout) | Continua como está: `goTo(stepIndex - 1)`, na etapa 0 navega para login |
| `step-products` | Visível; navega para a tela anterior (`step-review` não existe ainda); o `href` padrão (`/login/`) é mantido — usuário pode sair do fluxo |
| `step-review` | Visível; clique chama `showPostPaymentMode('step-products')` (volta para materiais) |

**Mudanças em JS:**
- Em `showPostPaymentMode`: remover `back.style.visibility = 'hidden'`.
- Adicionar listener no `elWizardBack` dentro de `showPostPaymentMode('step-review')` para navegar para `step-products`.
- Em `step-products`: o botão voltar fica visível com comportamento padrão (link para login) — sem JS override adicional.
- Atualizar o label `#wizard-back-label` por fase:
  - `step-products` → `"Voltar"` (default, navega para login)
  - `step-review` → `"← Materiais"`

### Fix 2 — Remover Resumo do cadastro de step-products

**Mudanças em JS:**
- Em `showPostPaymentMode`: remover o bloco `if (stepId === 'step-products') { renderConfirmationSummary('products-confirm-area'); }`.
- `renderConfirmationSummary` continua sendo chamada em `renderReview()` (para `review-summary-area`).

**Mudanças em template:**
- Remover ou manter `<div id="products-confirm-area"></div>` vazio (pode ficar como âncora case necessário, mas nada renderiza).

### Fix 3 — Botões de pagamento de materiais idênticos ao checkout do plano

**Mudanças em template** (`register.html`, sub-view `products-subview-cart`):
- Remover `style="background:var(--text);color:var(--panel)"` do botão `#products-btn-pay-pix`.
- Ambos `#products-btn-pay-card` e `#products-btn-pay-pix` ficam com apenas `class="btn-checkout-pay"` — fundo vermelho, idêntico ao botão do checkout do plano.

## Fora do escopo

- Redesign estrutural do wizard
- Mudanças no backend
- Mudanças de schema ou migrations
- Novo comportamento de cancelamento de pré-cadastro

## Arquivos impactados

| Arquivo | Tipo de mudança |
|---|---|
| `static/system/js/auth/register.js` | Fix 1 (remover ocultação, adicionar back em step-review), Fix 2 (remover renderConfirmationSummary de products) |
| `templates/login/register.html` | Fix 3 (remover inline style do botão PIX) |
| `static/system/css/auth/register.css` | Sem mudança (estilos já corretos) |

## Critérios de aceite

- [ ] Em `step-products`, o botão Voltar do header é visível e clicável
- [ ] Em `step-review`, o botão Voltar do header é visível e leva de volta a `step-products`
- [ ] A tela `step-products` não exibe o painel "Resumo do cadastro"
- [ ] O painel "Resumo do cadastro" continua aparecendo normalmente em `step-review`
- [ ] Os botões "Pagar com Cartão" e "Pagar com PIX" no carrinho de materiais têm fundo vermelho idêntico ao botão de pagamento do checkout do plano
- [ ] Nenhum erro JS no console após as mudanças
- [ ] Versão `?v=` do JS e CSS atualizada nos templates

## Plano

- [x] 1. Leitura integral dos arquivos impactados
- [x] 2. Implementar Fix 1 no JS
- [x] 3. Implementar Fix 2 no JS
- [x] 4. Implementar Fix 3 no template
- [x] 5. Atualizar `?v=` nos assets alterados (JS: v15→v16)
- [x] 6. Validação em navegador (wizard flow + pós-pagamento)
- [x] 7. Inspeção do console

## Evidências

- `manage.py check` → 0 issues
- `manage.py collectstatic --noinput` → 169 static files copiados
- **step-products**: "← Voltar" visível no header; catálogo limpo sem painel "Resumo do cadastro"; botões "Pagar com Cartão" e "Pagar com PIX" com estilo vermelho idêntico (`btn-checkout-pay`); "Pular" com estilo secundário bordado
- **step-review**: "← Materiais" visível no header; clique navega de volta para `step-products` com barra de progresso em 80%; sem erros JS da aplicação
- Console do browser: apenas erros de extensão do MCP, nenhum erro da aplicação

## Implementado

- `static/system/js/auth/register.js` (v16): `showPostPaymentMode` reescrita para manter back button visível, contextualizar label por fase e adicionar listener de retorno em step-review; removida chamada `renderConfirmationSummary('products-confirm-area')`
- `templates/login/register.html`: removido `style="background:var(--text);color:var(--panel)"` do botão `#products-btn-pay-pix`; versão JS atualizada para `?v=16`
