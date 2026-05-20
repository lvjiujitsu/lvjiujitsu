# PRD-038: Redesign da etapa "Materiais e equipamentos" no wizard de cadastro

## Resumo do que será implementado

Reescrever completamente a etapa `step-products` do wizard de cadastro para seguir o mesmo padrão visual e de interação das etapas de plano e turma: cards clicáveis com transição interna (produto → variante → carrinho), tema claro/escuro, e botões de pagamento funcionais.

## Tipo de demanda

Redesign de tela com correção de bugs de comportamento

## Problema atual

1. **Layout incompatível com o design system** — `step-products` usa uma lista plana com selects e steppers que não seguem os tokens visuais do wizard (`plan-card`, `plan-filter-pill`, `wizard-step__actions`, etc.)
2. **"Pagar com Cartão" não funciona** — `setPayloads()` é chamada como listener de `submit`, mas o payload hidden input não é atualizado antes do submit disparar; o form envia `[]`
3. **"Pular" não funciona** — `products-skip-form` envia o form corretamente, mas o botão é rendering dentro do footer sem garantia de que o CSRF token esteja no form; investigar se há conflito de `<form>` aninhado
4. **Sem tema consistente** — elementos como `.product-item`, `.qty-stepper`, `.product-variant-select` não usam as variáveis CSS do design system (`--panel`, `--border`, `--accent`, `--text`, `--muted`, `--radius-card`)
5. **UX não modular** — exibe todos os produtos ao mesmo tempo em lista vertical, sem fluxo guiado passo-a-passo

## Objetivo

Substituir a implementação atual por:

- **Sub-step 1 — Catálogo**: grid de cards de produto (1 card por produto), semelhante a `plan-cards`, com botão "Adicionar" por card
- **Sub-step 2 — Configurar item**: ao clicar "Adicionar" em um produto com variantes, transicionar para uma tela de seleção de variante (tamanho/cor) e quantidade dentro da mesma `section`, sem modal separado
- **Sub-step 3 — Carrinho**: lista dos itens selecionados com total, botões de pagamento (Cartão / PIX) e link "Pular"
- Corrigir payload dos forms de pagamento para que seja setado antes do submit
- Garantir que "Pular" funciona
- Manter tema claro e escuro sem elementos com cores hardcoded

---

## Context Ledger

### Arquivos lidos integralmente

- `templates/login/register.html` (seção `step-products`, linhas 649–691)
- `static/system/js/auth/register.js` (funções `renderProductGrid`, `bindProductForms`, `buildProductsPayload`, linhas 1772–1872)
- `static/system/css/auth/register.css` (classes de produto existentes)

### Arquivos adjacentes consultados

- `system/views/auth_views.py` — `MaterialsCheckoutView` e `RegisterMaterialsCheckoutView`
- `system/services/registration.py` — `create_product_only_order`
- `templates/login/register.html` (seções `step-plan`, `step-checkout` para referência de padrão visual)

### Internet / documentação oficial

- Não necessário — implementação puramente frontend (HTML/CSS/JS) com padrão já definido no projeto

### MCPs / ferramentas verificadas

- Playwright MCP — validação visual obrigatória ao final

### Limitações encontradas

- Nenhuma

---

## Prompt de execução

### Persona

Agente de desenvolvimento Django + JS vanilla seguindo SDD + o padrão visual já estabelecido no wizard de cadastro LV Jiu-Jitsu.

### Ação

Reimplementar a etapa `step-products` substituindo lista plana por fluxo de sub-steps em 3 fases: catálogo de cards → configurar variante/qtd → carrinho com pagamento.

### Contexto

O wizard de cadastro (`templates/login/register.html` + `static/system/js/auth/register.js` + `static/system/css/auth/register.css`) já tem um design system completo com tokens CSS, cards de plano clicáveis (`plan-card`, `plan-card--selected`), filtros em pills (`plan-filter-pill`), e ações em `wizard-step__actions`. A etapa de materiais deve seguir esse mesmo sistema.

O backend (`RegisterMaterialsCheckoutView`) já aceita `selected_products_payload` como JSON com `[{"variant_id": N, "quantity": N}, ...]` e `checkout_action` como `asaas_card`, `pix` ou `pay_later`. Nenhuma mudança backend é necessária.

### Restrições

- sem hardcode de cores — usar variáveis CSS do design system
- sem lógica de negócio no frontend
- sem migrações
- sem criar novas pastas — apenas editar arquivos existentes em `static/system/css/auth/`, `static/system/js/auth/` e `templates/login/`
- payload dos forms de pagamento deve ser serializado _antes_ do submit
- leitura integral obrigatória dos arquivos impactados antes de editar
- ao alterar CSS ou JS versionados por `?v=`, atualizar o número no template

---

## Escopo

### Sub-step 1: Catálogo de cards

- Substituir `<div id="products-grid">` por grid de cards com o mesmo visual do `plan-card`
- Cada card mostra: nome do produto, categoria, faixa de preço ("a partir de R$ X,XX" quando há variantes com preços distintos, ou o preço único), badge "Sem estoque" quando `total_stock === 0`
- Card com estoque zero é desabilitado (sem hover, cursor default, opacidade reduzida) — igual ao padrão de turma indisponível
- Botão "Adicionar" dentro do card ativa sub-step 2 para aquele produto
- Counter de itens no carrinho exibido no heading da seção quando `cart.length > 0`: "X item(ns) no carrinho"

### Sub-step 2: Configurar item

- Exibido dentro da `section#step-products`, ocultando o catálogo (`products-subview--catalog`) e mostrando `products-subview--configure`
- Heading: nome do produto
- Se o produto tiver apenas 1 variante com estoque: pular seleção de variante, mostrar diretamente stepper de quantidade
- Se houver múltiplas variantes: renderizar pills clicáveis por variante (`variant-pill`, `variant-pill--selected`) em vez de select — mesmo padrão de `plan-filter-pill`; variante sem estoque: pill desabilitada
- Stepper de quantidade: min 1, max = `stock_quantity` da variante selecionada
- Botão "Adicionar ao carrinho" — adiciona item ao estado JS `cart[]` e volta para sub-step 1
- Botão "Cancelar" — volta ao catálogo sem adicionar

### Sub-step 3: Carrinho

- `products-subview--cart` aparece quando `cart.length > 0` via botão "Ver carrinho (X)" no footer do catálogo
- Lista de itens com nome, variante, qtd, subtotal; botão "×" para remover item
- Total geral
- Dois botões de pagamento: "Pagar com Cartão" e "Pagar com PIX" — cada um submete form POST com payload JSON serializado do carrinho
- Link "Pular — adicionar materiais depois" que submete form com `checkout_action=pay_later` e payload `[]`
- Botão "Continuar comprando" para voltar ao catálogo

### Correção crítica de payload

O payload deve ser serializado em `click` do botão (ou em `mousedown`/`pointerdown`), não em `submit`, para garantir que o hidden input esteja preenchido antes do POST.

Alternativa mais segura: usar um único form com `action` e `checkout_action` definidos dinamicamente, e serializar em `click` do botão de submit relevante.

---

## Fora do escopo

- Alterações no backend / views / forms / models
- Alterações em outras etapas do wizard
- Criação de novas rotas
- Implementação de modal flutuante (a transição ocorre dentro da seção, não em overlay)

---

## Arquivos impactados

| Arquivo | Tipo de mudança |
|---|---|
| `templates/login/register.html` | Substituir HTML de `step-products`; atualizar `?v=` de CSS e JS |
| `static/system/js/auth/register.js` | Substituir `renderProductGrid`, `bindProductForms`; adicionar `renderProductsCatalog`, `renderProductsConfigure`, `renderProductsCart`, `bindProductsSection` |
| `static/system/css/auth/register.css` | Adicionar classes de produto que seguem o design system; remover classes órfãs antigas de produtos |

---

## Riscos e edge cases

- Produto com apenas 1 variante no estoque → pular tela de seleção de variante
- Produto sem nenhuma variante com estoque → card desabilitado, sem botão "Adicionar"
- Variante esgotada enquanto usuário configura → stepper max = 0; bloquear "Adicionar ao carrinho"
- Usuário volta ao catálogo e tenta adicionar produto já no carrinho → incrementar qtd ou substituir (comportamento: substituir para simplificar)
- `productCatalog` vazio (nenhum produto cadastrado) → exibir mensagem de catálogo vazio + botão "Pular"
- Payload JSON inválido no POST → backend já trata `IntegrityError` e erros de validação; frontend deve garantir JSON válido

---

## Regras e restrições

- SDD antes de código
- TDD para lógica de serialização de payload
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação visual obrigatória em desktop e mobile

---

## Plano

- [ ] 1. Leitura integral dos arquivos impactados
- [ ] 2. Escrever testes para `buildProductsPayload` (serialização correta do carrinho)
- [ ] 3. Atualizar HTML de `step-products` com nova estrutura de sub-views
- [ ] 4. Implementar CSS das novas classes no design system
- [ ] 5. Implementar JS: estado do carrinho, funções de render, correção de payload
- [ ] 6. Atualizar versões `?v=` em register.html
- [ ] 7. Validação visual: desktop e mobile, tema claro e escuro
- [ ] 8. Validação funcional: Cartão, PIX, Pular — verificar payload no POST
- [ ] 9. Limpeza de classes CSS órfãs
- [ ] 10. Atualização documental

---

## Validação visual

### Desktop

- Sub-step 1: grid de cards de produto alinhado, sem overflow horizontal
- Sub-step 2: pills de variante alinhadas, stepper legível, botões com espaçamento correto
- Sub-step 3: lista de carrinho com itens, total, botões de pagamento

### Mobile

- Cards empilhados em coluna única abaixo de 480px
- Pills de variante com wrap adequado
- Footer com botões empilhados em coluna

### Console do navegador

- Sem erros JS durante navegação entre sub-steps
- Sem warnings de formulário

### Terminal

- Sem stack trace no POST para `register-materials-checkout`

---

## Validação ORM

### Banco

- `RegistrationOrder` criado com `selected_products_payload` correto após POST de cartão ou PIX
- `RegistrationOrder` criado com payload `[]` após "Pular"

### Shell checks

```python
from system.models import RegistrationOrder
order = RegistrationOrder.objects.order_by('-created_at').first()
print(order.selected_products_payload)
```

### Integridade do fluxo

- Após pagamento por cartão: redireciona para Asaas, depois volta a `/register/` na etapa de revisão
- Após PIX: exibe QR code ou redireciona
- Após Pular: avança para `step-review`

---

## Evidências esperadas

- Screenshots de sub-step 1, 2 e 3 em desktop e mobile
- Console do navegador limpo
- Terminal sem stack trace
- Shell check confirmando payload correto no `RegistrationOrder`

---

## Implementado

_Pendente_

## Desvios do plano

_Nenhum_

## Pendências

_Nenhuma_
