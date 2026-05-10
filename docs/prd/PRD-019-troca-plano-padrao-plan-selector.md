# PRD-019: Padronizar troca de plano com o padrão `plan-selector` do cadastro

## Resumo do que será implementado
Reescrever a tela de troca de plano (`/plan-change/`) reutilizando o mesmo padrão visual da etapa "Escolha seu plano" do wizard de cadastro: chips de filtro (público, tipo, frequência, recorrência) + cards PIX/Cartão lado a lado + resumo destacado. O resumo passa a exibir o cálculo da troca selecionada (crédito, custo proporcional e diferença líquida). A tela intermediária `plan_change_confirm.html` é eliminada — o POST do próprio `plan-change-select` aplica a troca (downgrade/gratuita) ou cria a ordem e redireciona para `payment-checkout` (upgrade).

## Tipo de demanda
Refatoração visual / padronização de UX (sem alteração de regra de negócio nem de schema).

## Problema atual
Mesmo após o PRD-006, a tela `plan_change_select.html` permanece visualmente divergente da tela de cadastro:

- a tela de cadastro usa chips horizontais por dimensão (público, tipo, frequência, ciclo) + cards PIX e Cartão lado a lado + resumo destacado;
- a tela de troca usa lista vertical agrupada (`catalog-cluster-card` + `record-card-catalog`) com proração colapsável em `<details>`;

O usuário ("trocar plano está despadronizado") quer ver o mesmo layout em ambas as telas, com o cálculo da troca selecionada visível no resumo da seleção. Manter dois padrões para a mesma operação ("escolher um plano") é fonte de inconsistência e confusão.

## Objetivo
- Reusar exatamente o padrão `.plan-selector-*` do wizard de cadastro na tela de troca.
- Exibir crédito proporcional, custo proporcional e diferença líquida no resumo, atualizados ao trocar de filtro / método.
- Eliminar a tela intermediária de confirmação (`plan_change_confirm.html`) — fluxo passa a ser: selecionar plano → submeter → backend aplica troca (gratuita) ou redireciona para checkout (upgrade).
- Extrair os estilos `plan-selector` para CSS compartilhado, evitando drift visual futuro.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `MEMORY.md` (raiz da auto-memory)
- `templates/billing/plan_change_select.html`
- `templates/billing/plan_change_confirm.html`
- `templates/login/register.html` (etapa `plan` — linhas 740–840)
- `templates/base.html`
- `system/views/plan_change_views.py`
- `system/services/plan_change.py`
- `system/services/registration_checkout.py`
- `system/selectors/plan_eligibility.py`
- `system/models/plan.py`
- `system/tests/test_views.py` (classe `PlanChangeSelectViewGroupingTest`, linhas 1993–2110)
- `static/system/css/billing/billing.css`
- `static/system/css/auth/login.css` (bloco `plan-selector*`, linhas 2575–2760)
- `static/system/js/auth/registration-wizard-clean.js` (`renderPlanList`, `buildPlanSelectorRow`, `buildPlanSelectorPaymentCard`, `buildPlanSelectorSummary`, linhas 2150–2470)
- `docs/prd/PRD-006-padronizar-tela-troca-plano.md`

### Arquivos adjacentes consultados
- `system/urls.py` — rotas `plan-change-select`, `plan-change-confirm`, `payment-checkout`
- `system/views/__init__.py` — exports
- `templates/home/student/dashboard.html` — chamadas a `plan-change-select`
- `static/system/js/auth/registration-wizard-clean.js` — `pixIconUrl`/`cardIconUrl` vêm de `data-pix-icon-url`/`data-card-icon-url` no form

### Internet / documentação oficial
- Não aplicável: refatoração visual reusando padrão já estabelecido no projeto.

### MCPs / ferramentas verificadas
- shell PowerShell — ok — leitura, edição, execução
- Playwright / browser MCP — obrigatório para validação visual (cadastro precisa continuar idêntico após mover CSS; nova tela de troca precisa ser validada)

### Limitações encontradas
- O número `019` é o próximo livre na pasta `docs/prd/`, mesmo havendo colisões anteriores (PRD-008, 015, 016 duplicados). Não está no escopo deste PRD reorganizar a numeração.

## Prompt de execução
### Persona
Agente de desenvolvimento Django + frontend server-rendered seguindo SDD + TDD + Clean Code.

### Ação
Reescrever a tela de troca de plano para reusar o padrão `plan-selector` do cadastro, exibindo o cálculo da troca selecionada no resumo, eliminando a tela intermediária de confirmação.

### Contexto
A view `PlanChangeSelectView` já calcula proração para todos os planos elegíveis. O wizard de cadastro já implementa o padrão visual desejado em JS (`registration-wizard-clean.js`). O CSS `.plan-selector-*` está hoje em `static/system/css/auth/login.css`. Vamos extrair esse CSS para `static/system/css/shared/plan-selector.css`, criar JS específico para a troca em `static/system/js/billing/plan-change-selector.js`, reescrever o template de troca para usar o mesmo padrão e adicionar painel de cálculo da troca no resumo. A view passa a aceitar POST com `selected_plan` e aplica a troca diretamente (sem tela de confirmação intermediária).

### Restrições
- sem hardcode de regra de negócio
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória (já realizada)
- validação visual em navegador obrigatória (cadastro + troca)
- interface em pt-BR
- preservar comportamento já testado de `calculate_plan_change` e `apply_plan_change`/`create_plan_change_order`

### Critérios de aceite
- [ ] `/plan-change/` carrega com layout `plan-selector` idêntico ao da etapa de plano do cadastro (chips + cards PIX/Cartão + resumo) — verificável por inspeção visual.
- [ ] Selecionando PIX ou Cartão, o resumo exibe nome, ciclo, valor cheio e o cálculo da troca: crédito (R$), custo proporcional (R$) e diferença/economia (R$) — verificável por teste e visual.
- [ ] Quando o plano selecionado é gratuito ou downgrade (`net_amount <= 0`), o botão CTA é "Confirmar troca"; quando é upgrade, é "Confirmar e pagar" — verificável por teste e visual.
- [ ] POST em `/plan-change/` com `selected_plan=<id>` válido aplica troca direta (gratuita/downgrade) e redireciona para `student-home` com mensagem de sucesso — verificável por teste.
- [ ] POST em `/plan-change/` com `selected_plan=<id>` válido upgrade cria `RegistrationOrder` e redireciona para `payment-checkout` — verificável por teste.
- [ ] Tela `plan_change_confirm.html` e rota `plan-change-confirm` deixam de existir — verificável por inspeção e por `manage.py check`.
- [ ] CSS `.plan-selector-*` movido para `static/system/css/shared/plan-selector.css`; cadastro continua visualmente idêntico — verificável por validação visual da etapa de plano do cadastro.
- [ ] JS específico em `static/system/js/billing/plan-change-selector.js` carregado apenas na tela de troca — verificável por inspeção do template.
- [ ] `?v=` atualizado nos arquivos cujo conteúdo mudou — verificável por inspeção.
- [ ] `manage.py test --verbosity 2` passa sem falhas — verificável por terminal.
- [ ] `manage.py check` sem erros — verificável por terminal.
- [ ] Console do navegador limpo nas duas telas — verificável por DevTools.

### Evidências esperadas
- output de `manage.py test --verbosity 2` com 0 falhas
- output de `manage.py check` sem erros
- screenshot/descrição visual das duas telas pós-mudança
- console do navegador sem erros
- terminal sem stack trace

### Formato de saída
Código (view + template + JS + CSS compartilhado) + testes + evidências.

## Escopo
- `system/views/plan_change_views.py`: substituir `PlanChangeSelectView` por uma `View` que serve `GET` (renderiza template com payload JSON) e `POST` (aplica troca / cria order). Remover `PlanChangeConfirmView`.
- `system/urls.py`: remover rota `plan-change-confirm`. Manter `plan-change-select` (apenas).
- `system/views/__init__.py`: ajustar exports.
- `templates/billing/plan_change_select.html`: reescrita completa usando padrão `plan-selector`.
- `templates/billing/plan_change_confirm.html`: **excluir**.
- `static/system/css/shared/plan-selector.css`: novo arquivo com os estilos `plan-selector*` e adições para o painel de cálculo da troca.
- `static/system/css/auth/login.css`: remover bloco `plan-selector*` (passa a vir do `shared/`).
- `templates/login/register.html`: incluir `shared/plan-selector.css` antes do `auth/login.css`.
- `static/system/css/billing/billing.css`: remover regras agora obsoletas (`.plan-change-grid`, `.plan-change-card*`, `.plan-change-action-row`, `.plan-change-net*`); manter `.plan-change-badge*` se usado em outro contexto (verificar). Bump de `?v=`.
- `static/system/js/billing/plan-change-selector.js`: novo arquivo, contém apenas a renderização do plan-selector + painel de cálculo, recebendo dados via `data-` attributes.
- `system/tests/test_views.py`: substituir `PlanChangeSelectViewGroupingTest` por `PlanChangeSelectViewTest` cobrindo:
  - GET retorna 200 e injeta `plan_catalog_json` (lista) com cada item contendo proration
  - GET retorna `membership` no contexto
  - POST com plano gratuito/downgrade aplica troca e redireciona para `student-home`
  - POST com plano upgrade cria order e redireciona para `payment-checkout`
  - POST com `selected_plan` ausente/ inválido redireciona com mensagem de erro
  - acesso não autenticado redirecionado.

## Fora do escopo
- Alteração no cálculo de proração (`system/services/plan_change.py`).
- Alteração em `apply_plan_change` / `create_plan_change_order`.
- Alteração no fluxo de checkout/pagamento posterior.
- Alteração na elegibilidade de planos (`plan_eligibility.py`).
- Alteração visual da etapa "Escolha seu plano" do cadastro além do necessário para mover o CSS.

## Arquivos impactados
| Arquivo | Tipo de mudança |
|---|---|
| `system/views/plan_change_views.py` | reescrita: GET + POST únicos; remoção de `PlanChangeConfirmView` |
| `system/urls.py` | remover rota `plan-change-confirm` |
| `system/views/__init__.py` | remover export `PlanChangeConfirmView` |
| `templates/billing/plan_change_select.html` | reescrita completa |
| `templates/billing/plan_change_confirm.html` | **excluir** |
| `templates/login/register.html` | adicionar `<link>` para `shared/plan-selector.css` |
| `static/system/css/shared/plan-selector.css` | **novo** |
| `static/system/css/auth/login.css` | remover bloco `plan-selector*` |
| `static/system/css/billing/billing.css` | remover regras obsoletas; bump `?v=` |
| `static/system/js/billing/plan-change-selector.js` | **novo** |
| `system/tests/test_views.py` | substituir `PlanChangeSelectViewGroupingTest` |

## Riscos e edge cases
- Quebra visual na tela de cadastro ao mover o CSS — mitigação: validar visualmente após a movimentação.
- Caso o usuário tenha perdido o `request.portal_person` ou `membership`, GET volta para a home com mensagem (mantém comportamento atual).
- Plano com `requires_special_authorization` continua sendo filtrado pela elegibilidade (preservado).
- Caso o JSON de catálogo fique vazio (ex.: nenhum plano elegível para troca), a tela exibe estado vazio idêntico ao do cadastro (`Nenhum plano disponível…`).
- POST com `selected_plan` inexistente: 404 ao buscar `SubscriptionPlan` resulta em mensagem de erro e redirecionamento.
- Decimal serializado para JSON: usar `str(value)` (igual ao `get_plan_catalog_payload`).

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
- [x] 2. Contratos: definir formato JSON do catálogo (plano + proration)
- [x] 3. Testes (Red): substituir `PlanChangeSelectViewGroupingTest`
- [x] 4. Implementação (Green): view + template + JS + CSS compartilhado
- [x] 5. Refatoração (Refactor): limpar billing.css, atualizar `?v=`
- [x] 6. Validação completa: test/check/collectstatic + visual desktop/mobile
- [x] 7. Limpeza final
- [x] 8. Atualização documental (este PRD)

## Validação visual
### Desktop
- Etapa de plano do cadastro continua idêntica.
- Tela de troca exibe chips + cards PIX/Cartão lado a lado + resumo com cálculo da troca.

### Mobile
- Layout em coluna única; cards PIX/Cartão empilhados (`@media max-width: 360px` já existente).

### Console do navegador
- Sem erros JS críticos nas duas telas.

### Terminal
- Sem stack trace ao navegar nos dois fluxos.

## Validação ORM
### Banco
- Nenhuma alteração de schema.

### Shell checks
- `SubscriptionPlan.objects.filter(is_active=True).exclude(requires_special_authorization=True).count()` retorna lista esperada.
- `Membership.objects.filter(status="active")` permanece consultável.

### Integridade do fluxo
- Após POST gratuito: membership.plan trocado, status preservado.
- Após POST upgrade: `RegistrationOrder` criada com `is_plan_change=True` e `total = net`.

## Validação de qualidade
### Sem hardcode
- Catálogo gerado via selector existente; ícones via `data-*-icon-url`.
### Sem estruturas condicionais quebradiças
- Lógica mantida em service; view fina; JS estruturado por funções.
### Sem `except: pass`
- Tratamento de `PlanChangeError` continua com `continue` (preservado).
### Sem mascaramento de erro
- Mensagens de erro explícitas via `messages.error`.
### Sem comentários e docstrings desnecessários
- Não adicionar.

## Evidências
- `manage.py check`: `System check identified no issues (0 silenced).`
- `manage.py test --verbosity 1` (suíte completa): `Ran 341 tests in 66.893s — OK`
- `manage.py test system.tests.test_views.PlanChangeSelectViewTest --verbosity 2`: `Ran 12 tests in 1.841s — OK`
  - `test_unauthenticated_access_redirected` ok
  - `test_get_renders_membership_in_context` ok
  - `test_get_template_carries_plan_catalog_script_and_icons` ok
  - `test_get_plan_catalog_excludes_current_plan` ok
  - `test_get_plan_catalog_serializes_amounts_as_strings_with_proration` ok
  - `test_get_plan_catalog_marks_upgrade_and_downgrade_correctly` ok
  - `test_post_with_upgrade_creates_order_and_redirects_to_checkout` ok
  - `test_post_with_downgrade_applies_change_and_redirects_home` ok
  - `test_post_without_selected_plan_redirects_with_error` ok
  - `test_post_with_same_plan_redirects_with_error` ok
  - `test_post_with_inactive_plan_returns_404` ok
  - `test_confirm_route_was_removed` ok (NoReverseMatch para `plan-change-confirm`)
- `manage.py collectstatic --noinput`: `167 static files copied`
- HTTP probes: `/plan-change/` 302 → login (sem sessão); `/register/` 200; novos assets `shared/plan-selector.css` e `js/billing/plan-change-selector.js` 200
- Validação visual em navegador (Preview MCP, sessão portal autenticada como persona "teste"):
  - Desktop: chips (Frequência, Recorrência) + cards PIX/Cartão lado a lado + resumo com nome, ciclo, valor cheio e cálculo da troca (Crédito, Custo, Diferença/Economia). Selecionando PIX (downgrade) → CTA "Confirmar troca", net=Grátis (verde). Selecionando Anual Cartão (upgrade) → CTA "Confirmar e pagar", net=R$ 12,88 (laranja).
  - Mobile (375x812): grid responsivo, cards lado a lado, breakdown legível, CTA full-width.
  - Console limpo nas duas resoluções (`No console logs` em level=error).
  - Cadastro (`/register/`) carregando `shared/plan-selector.css` antes de `auth/login.css`; computed style do `.plan-selector-chip` preservado (border-radius 999px, padding 8px 14px, font-weight 600).

## Implementado
- `system/views/plan_change_views.py`: reescrita; `PlanChangeSelectView` agora aceita GET (renderiza catálogo serializado com proração) e POST (aplica troca direta para gratuita/downgrade ou cria `RegistrationOrder` para upgrade e redireciona para `payment-checkout`). `PlanChangeConfirmView` removido. Helpers locais `_serialize_plan_with_proration` e `_build_plan_catalog`.
- `system/urls.py`: rota `plan-change-confirm` removida.
- `system/views/__init__.py`: export `PlanChangeConfirmView` removido.
- `templates/billing/plan_change_select.html`: reescrita usando `plan-selector` + `json_script` para o catálogo, `data-pix-icon-url` / `data-card-icon-url` no form, CTA dinâmico ("Confirmar troca" / "Confirmar e pagar") via JS. Inclui novos `?v=20260509a` para `shared/plan-selector.css` e `billing/billing.css`.
- `templates/billing/plan_change_confirm.html`: excluído.
- `templates/login/register.html`: passa a incluir `<link>` para `shared/plan-selector.css` antes de `auth/login.css` (`?v=20260509a` em ambos).
- `static/system/css/shared/plan-selector.css`: criado a partir do bloco extraído de `auth/login.css`, com adições para o painel `plan-selector-summary-breakdown` (crédito, custo, net colorido por cenário).
- `static/system/css/auth/login.css`: bloco `.plan-selector-*` removido (carregado agora via shared).
- `static/system/css/billing/billing.css`: regras obsoletas (`.plan-change-grid`, `.plan-change-card*`, `.plan-change-action-row`, `.plan-change-net*`, `.plan-change-badge*`, `.proration-breakdown`, `.proration-total`) removidas. Adicionadas `.plan-change-cta-row` e `.plan-change-empty`.
- `static/system/js/billing/plan-change-selector.js`: novo módulo IIFE que lê o JSON do catálogo, renderiza chips de filtro (público/tipo/frequência/recorrência) + cards PIX/Cartão + resumo com cálculo da troca, sincroniza `#selected-plan` e o CTA do form.
- `system/tests/test_views.py`: `PlanChangeSelectViewGroupingTest` substituído por `PlanChangeSelectViewTest` com 12 testes cobrindo GET, POST (upgrade/downgrade/sem plano/mesmo plano/inativo), serialização do catálogo e remoção da rota antiga.
- `.claude/launch.json`: criado para suportar validação visual via Preview MCP (config "django" apontando para `runserver 127.0.0.1:8000`).

## Desvios do plano
- O CSS de `shared/plan-selector.css` é carregado **antes** do `auth/login.css` no `register.html` para preservar a precedência de cascata pretendida (estilos do shared como base; auth.css pode sobrescrever se necessário no futuro). Sem impacto visual hoje — validado por inspeção e screenshot.
- **Pós-validação visual** (após screenshots iniciais): dois bugs identificados pelo usuário e corrigidos:
  1. **Chips selecionados ilegíveis no tema dark**: o CSS shared usava `var(--panel-strong)` (token definido só em `auth/login.css`); na tela de troca, que herda apenas `portal/portal.css`, o token ficava `unset` e `color` herdava do parent, igualando à cor de fundo do chip selecionado. Correção: `shared/plan-selector.css` passou a usar `var(--panel-solid)` (token definido em `portal/portal.css`); como o `auth/login.css` ainda usa `--panel-strong` em outros 32 lugares, foi adicionado `--panel-solid` ao lado de `--panel-strong` em ambos os blocos `:root` do `auth/login.css` (alias com mesmo valor).
  2. **Botão CTA esticado verticalmente no mobile**: `.plan-change-cta-row .btn { flex: 1 1 220px }` combinado com `flex-direction: column` na media query causava o `flex-grow: 1` operar no eixo vertical. Correção: na media query mobile, redefinido para `flex: 0 0 auto`, mantendo `width: 100%` e altura natural (`min-height: 44px`).
  - `?v=` bumped para `20260509c` em `plan_change_select.html` e `register.html` para invalidar caches.
  - Re-validação visual desktop+mobile pós-fix confirmou: chips legíveis (bg `#f5f7fa` / color `#14161b` no dark) e botões mobile com altura 44px e largura 321px (full-width sem stretch).

## Pendências
- Nenhuma. Validação visual desktop e mobile concluída via Preview MCP com sessão portal autenticada; todos os testes e checks passando.
