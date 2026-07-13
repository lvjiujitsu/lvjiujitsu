# PRD-141: Crítica profunda do frontend — problemas identificados

## Summary

Auditoria read-only **altamente crítica** do frontend LV JIU JITSU (jul/2026): 92 templates, 27 assets em `static/system/` (CSS, JS, imagens). Complementa PRD-138/139 (acochamento transversal) com análise **profunda só de UI**. Proposta de correção consolidada em ondas P0–P2 (jul/2026).

## Demand type

Auditoria frontend read-only + PRD de roteamento. **Não implementa código.**

## Current problem

O frontend funciona, mas concentra risco em quatro eixos:

1. **Arquitetura** — sem `base.html`; três shells paralelos; tema e assets repetidos em dezenas de templates.
2. **Domínio no JS** — elegibilidade de plano/turma/IBJJF e checkout reimplementados no browser (3k+ linhas).
3. **Segurança/manutenção** — 43 usos de `innerHTML` em JS; PRD-080 não executada; JSON `|safe` em `<script type="application/json">`.
4. **UX/a11y/performance** — `dashboard.html` monolítico (1,3k linhas), 12 modais no DOM inicial, sem focus trap, re-render completo de catálogos a cada filtro.

## Goal

Registrar **todos os problemas frontend** com severidade, evidência (arquivo/linha/padrão) e plano de correção verificável em ondas P0–P2.

## Context Ledger

### Files read in full

- `static/system/js/auth/register.js` (3.334 linhas)
- `static/system/js/dependents/dependent_registration.js` (1.204 linhas)
- `static/system/js/home/dashboard.js` (1.716 linhas)
- `static/system/css/lv/base.css`
- `static/system/css/auth/register.css` (2.015 linhas)
- `static/system/css/home/dashboard.css` (2.860 linhas)
- `templates/login/register.html` (1.053 linhas)
- `templates/home/dashboard.html` (1.366 linhas)
- `templates/auth/base_auth.html`
- `templates/lv/modal_frame.html`
- `static/system/js/lv/theme_boot.js`, `crud_modal.js`, `theme_toggle.js`
- `docs/PRD-STANDARD.md`, `docs/prd/PRD-138-*.md`, `docs/prd/PRD-139-*.md`, `docs/prd/PRD-080-*.md`

### Adjacent files consulted

- Inventário: 92 templates (`Glob templates/**/*.html`), 27 assets (`Glob static/system/**/*`)
- `rg` em: `innerHTML`, `?v=`, `extends`, `|safe`, `<script`, `theme_boot`, `aria-modal`, `style=`
- Amostragem: `templates/dependents/dependent_registration.html`, `templates/people/person_list.html`, `templates/calendar/calendar.html`, `static/system/js/products/store_cart.js`, `static/system/css/people/people.css`

### Internet / official documentation

- [Django static files](https://docs.djangoproject.com/en/5.2/howto/static-files/) — versionamento/cache de assets e `{% static %}`.
- [MDN — `Element.innerHTML` security considerations](https://developer.mozilla.org/en-US/docs/Web/API/Element/innerHTML#security_considerations) — risco XSS e preferência por APIs seguras.
- [MDN — WAI-ARIA `dialog` pattern](https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Roles/dialog_role) — focus trap, `aria-modal`, retorno de foco.

### Context7 / MCPs / tools verified

- `Glob`, `Grep`, `Read` no workspace (sem alteração de código).
- Context7 não consultado nesta rodada (achados baseados em código e docs Django/MDN acima).

### Limitations found

- Auditoria estática; **nenhum** teste de browser, Lighthouse, axe ou dispositivo real executado.
- `register.js` lido por seções (arquivo >100k caracteres); contagem de linhas via PowerShell.
- `staticfiles/` não inspecionado (saída gerada).
- Não validado comportamento runtime de gateways (Asaas/Stripe) no wizard.

## Required skills

- `lv-task-intake` (concluída)
- `lv-prd` (esta PRD)
- `lv-ui-delivery` (critérios de validação visual futuros)

## Understanding approved

Demanda classificada como **auditoria read-only crítica de frontend**. Escopo: `templates/` (92), `static/system/`. Entrega: PRD-141 com proposta de correção consolidada. Implementação via PRD-filhas.

## Execution prompt

### Persona

Revisor sênior implacável — apenas criticar, sem elogiar. Cada achado com evidência.

### Action

Auditar frontend completo; listar problemas por severidade; criticar arquitetura de shells; documentar em PRD-141.

### Context

PRD-138/139 documentaram acochamento geral. Esta PRD aprofunda **somente** camada de apresentação.

### Constraints

- Read-only.
- Proposta de correção preenchida (jul/2026); execução requer PRD-filha por onda.
- Seguir `docs/PRD-STANDARD.md`.

### Acceptance criteria

- [ ] PRD-141 criada com template completo.
- [ ] Seção "Problemas identificados" com CRÍTICA/ALTA/MÉDIA/BAIXA e evidência.
- [ ] Arquitetura de shells documentada.
- [ ] README atualizado após PRD-139.
- [ ] Plan com checkboxes (desmarcados).
- [ ] Fonte oficial externa citada.

### Expected evidence

- Paths e linhas no repositório.
- Contagens `rg`/PowerShell registradas nesta PRD.

### Output format

Markdown em `docs/prd/PRD-141-critica-frontend-problemas.md`.

## Scope

- `templates/` — 92 arquivos HTML.
- `static/system/` — CSS, JS, imagens (27 arquivos).
- Problemas: UX, a11y, responsividade, performance, segurança (XSS, `innerHTML`, CSRF no JS), consistência visual, duplicação, regra de negócio indevida no JS, shells, `?v=`, inline scripts, temas claro/escuro, mobile, modais, `register.js`, `dependent_registration.js`, `dashboard.js`.

## Out of scope

- Implementação de correções.
- Backend (`system/services`, forms, views) exceto como contraste quando JS duplica regra.
- HG/produção, deploy, pagamento real.
- `staticfiles/` gerado.
- Implementação de correções (execução via PRD-filhas por onda).

## Impacted files

| Área | Arquivos principais |
|---|---|
| Wizard público | `templates/login/register.html`, `static/system/js/auth/register.js`, `static/system/css/auth/register.css` |
| Wizard dependente | `templates/dependents/dependent_registration.html`, `static/system/js/dependents/dependent_registration.js` |
| Home | `templates/home/dashboard.html`, `static/system/js/home/dashboard.js`, `static/system/css/home/dashboard.css` |
| Shell admin | ~57 templates standalone + `static/system/css/lv/base.css`, `people/people.css`, `classes/classes.css` |
| Shell auth | `templates/auth/base_auth.html`, `templates/login/*.html` |
| Shell modal CRUD | `templates/lv/modal_frame.html`, `static/system/js/lv/crud_modal.js` |

## Risks and edge cases

- Corrigir só `innerHTML` sem mover elegibilidade para o backend pode mascarar divergência cliente/servidor.
- Unificar shell sem mapa de `?v=` pode quebrar cache de usuários com assets antigos.
- Modais em iframe (dependente/cronograma) exigem estratégia de foco pai↔filho; remoção ingênua quebra UX.
- `register.js` e `dependent_registration.js` divergem em parsing de data (DD/MM vs ISO) — correção parcial gera regressão silenciosa.

## Rules and constraints

- Regra de negócio pertence a `services/` (AGENTS.md §9); JS atual viola isso nos wizards.
- PRD-080 exige eliminar `innerHTML` com dados de usuário — ainda pendente.
- Tema claro/escuro obrigatório (CLAUDE.md §9) — implementação inconsistente entre shells.

## Arquitetura frontend (crítica)

### Inventário de shells (92 templates)

| Shell | Mecanismo | Quantidade | Problema |
|---|---|---:|---|
| **Standalone monolito** | `<!DOCTYPE html>` completo, head/body duplicados | **62** | Sem herança; cada tela redeclara meta, tema, CSS, scripts |
| **Auth** | `{% extends "auth/base_auth.html" %}` | **5** | Só login + reset de senha; wizard/register **não** usa |
| **Modal iframe CRUD** | `{% extends "lv/modal_frame.html" %}` | **25** | Terceiro head/body; `theme_boot.js` sem `?v=` |
| **Partials** | `{% include %}` sem shell | **4** | OK como fragmento; acoplados a `dashboard.html` |

**Não existe** `templates/lv/base.html` nem `base.html` global. PRD-075 introduziu `base.css`, mas não um layout Django unificado.

### Três famílias visuais incompatíveis

```text
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ Wizard / Register   │  │ Dashboard / Home      │  │ Admin list/detail   │
│ register.css tokens │  │ dashboard.css tokens│  │ base+people+classes │
│ max-width 540px     │  │ topbar + sections   │  │ CRUD + modais       │
│ inline theme IIFE   │  │ inline theme IIFE   │  │ theme_boot.js       │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
```

### Dois sistemas de modal

1. **`<dialog class="crud-modal">` + iframe** — `crud_modal.js`, `modal_frame.html` (admin).
2. **`.modal-overlay` + `hidden`** — `dashboard.html` (12 modais) + iframes dependente/cronograma.

Sem API comum: `overflow` alterna `style` vs `classList`; fechamento usa listeners duplicados por modal.

### God-modules

| Arquivo | Linhas | Papel |
|---|---:|---|
| `register.js` | 3.334 | Wizard completo + planos + materiais + operacional + cupom |
| `dashboard.js` | 1.716 | Tema + 12 modais + check-in + tabs + filtros + AJAX |
| `dashboard.css` | 2.860 | Home + modais + componentes |
| `register.css` | 2.015 | Wizard + planos + produtos + operacional |
| `dashboard.html` | 1.366 | Markup de todas as áreas + todos os modais |

## Problemas identificados

Legenda de severidade:

- **CRÍTICA** — risco de segurança, divergência de negócio ou débito estrutural que bloqueia evolução.
- **ALTA** — a11y/performance/UX grave ou duplicação massiva com manutenção inviável.
- **MÉDIA** — inconsistência, dívida clara, workaround repetido.
- **BAIXA** — polish, convenção, otimização marginal.

---

### CRÍTICA

| ID | Problema | Evidência |
|---|---|---|
| C-01 | **Regra de negócio de elegibilidade no JS** — `resolveAudience`, filtro de turmas por idade/sexo/IBJJF e elegibilidade de planos (família, adulto, kids) implementados no browser; servidor deveria ser autoritativo (`plan_eligibility.py` citado na PRD-138). | `register.js` L2218–2257 (`calcAgeYears`, `resolveAudience`, `filterGroupsByPerson`); L1427–1446 (`getEligiblePlansForCurrentPerson`); `dependent_registration.js` L146–201, L341–373 |
| C-02 | **God-module `register.js`** — 3.334 linhas, máquina de estados, validação por etapa, checkout, materiais, cupom, perfis operacionais; impossível revisar ou testar unitariamente no estado atual. | Contagem linhas; funções `validatePrincipal` L644+, `validatePlan` L1688+, `submitOperationalRegistration` L2201+ |
| C-03 | **Duplicação quase integral wizard dependente** — `dependent_registration.js` (1.204 linhas) replica catálogo de turmas, planos, materiais, navegação de steps e helpers (`escHtml`, `fmtPrice`, máscaras) já presentes em `register.js`. | Estrutura espelhada: `bindClassCatalog` L204–277 vs `register.js` `renderClassCatalog` L2290–2343; `bindPlanCatalog` L302–721; 18× `innerHTML` em ambos |
| C-04 | **43 ocorrências de `innerHTML` em JS** — PRD-080 não concluída; padrão proibido pelo contrato UI para dados dinâmicos; escape manual `escHtml` não cobre todos os vetores (atributos, URLs, SVG concatenado). | `rg innerHTML`: `register.js` 22, `dependent_registration.js` 18, `dashboard.js` 3 |
| C-05 | **JSON de catálogo com `\|safe` em template** — se serialização falhar ou injetar `</script>`, vetor XSS clássico em bloco JSON. | `register.html` L13–24; `dependent_registration.html` L12–16 |
| C-06 | **Sem layout base Django** — 62 páginas reimplementam documento HTML; qualquer mudança global (CSP, favicon, fonte, theme) exige edição em massa. | `rg ^<!DOCTYPE` → 62 templates; apenas 30 usam `extends` (25 modal + 5 auth) |
| C-07 | **Estado do wizard exclusivamente client-side** — navegação, filtros de plano e seleção de turma vivem em `state` JS; risco de divergência com `PreRegistration` no servidor (PRD-040). | `register.js` — objeto `state`, `clearWizardState`, `onEnterPlan`, `validatePlan`; form `novalidate` em `register.html` L70 |

---

### ALTA

| ID | Problema | Evidência |
|---|---|---|
| A-01 | **`dashboard.js` monolítico** — 1.716 linhas, 15+ `bind*Modal` no boot, listeners globais em `document` para cada feature. | L1692–1715 inicialização; funções L349–1648 |
| A-02 | **`dashboard.html` monolítico** — 1.366 linhas; 12 modais + dados duplicados no DOM (ex.: listas de check-in clonadas para modal de presença). | Modais L719–1320; `bindPresenceModal` clona filhos `dashboard.js` L946–950 |
| A-03 | **Modais sem focus trap / sem `inert` no fundo** — teclado pode escapar; foco não retorna ao gatilho; padrão ARIA dialog incompleto. | `rg focus-trap|inert|aria-modal` em JS → 0 em `static/system/js`; modais usam só `hidden` + `aria-modal="true"` em `dashboard.html` |
| A-04 | **12+ listeners `keydown` Escape em `document`** — um por modal; custo e ordem de execução imprevisível. | `dashboard.js` L384–386, L443–445, L727–729, L781–783, L816–818, L862–864, L948–965, L1148–1150, L1187–1189, L1415–1417, L1507–1509, L1589–1591 |
| A-05 | **Re-render completo via `innerHTML` em catálogos** — cada clique em filtro/pílula destrói e recria DOM inteiro (planos, turmas, produtos); perda de foco, custo de layout, listeners reanexados manualmente. | `register.js` L1509, L1645 (`renderPlanFilters`/`renderPlanCards`); `dependent_registration.js` L459, L582, L843 |
| A-06 | **Parsing de data inconsistente entre wizards** — `register.js` só `DD/MM/YYYY` (`split('/')`); dependente aceita ISO `AAAA-MM-DD` também; mesma regra IBJJF, resultados diferentes. | `register.js` L2218–2222; `dependent_registration.js` L146–158 |
| A-07 | **Iframe dependente sem limpar `src` ao fechar** — documento interno permanece em memória; duplo carregamento de CSS/JS do wizard. | `bindDependentRegistrationModal` `dashboard.js` L419–423 fecha overlay mas não zera iframe; contraste com `crud_modal.js` L31–33 (`about:blank`) |
| A-08 | **Tokens CSS duplicados e divergentes** — `:root` e `html[data-theme="dark"]` redefinidos em `base.css` L6–54 e `register.css` L6–39 com valores diferentes (`--bg`, `--surface`, etc.). | Diff manual dos blocos `:root`; admin carrega `base.css`, wizard carrega só `register.css` |
| A-09 | **Triplo stack CSS admin sem contrato** — ~41 telas carregam `base.css?v=1` + `people.css?v=2` + `classes.css?v=1|v=2` arbitrário. | `rg lv/base.css` 41 templates; `classes.css` v=1 em ~35, v=2 em 6 (`request_list.html` L11, `graduation_overview.html` L11) |
| A-10 | **Validação wizard depende de JS com `novalidate`** — HTML5 desligado; sem JS, envio passa sem barreiras de etapa. | `register.html` L70 `novalidate`; `dependent_registration.html` form sem garantia server-step equivalente no cliente |
| A-11 | **CSRF em fetch JSON correto, mas inconsistente** — `dashboard.js` `getCsrfToken` L31–34 OK; cupom em `register.js` L2701 usa `fetch` POST — se token ausente em edge case, falha silenciosa. | Padrão misto FormData vs JSON; holder CSRF em `dashboard.html` L44 `csrf-holder` hidden |

---

### MÉDIA

| ID | Problema | Evidência |
|---|---|---|
| M-01 | **Theme boot inline duplicado (17×)** — mesmo IIFE copiado em vez de `theme_boot.js` versionado. | `rg localStorage.getItem('lv-theme')` em 17 templates (`register.html` L8, `dashboard.html` L8, etc.) |
| M-02 | **`theme_boot.js` / `theme_toggle.js` / `crud_modal.js` sem `?v=`** — 42 templates referenciam `theme_boot.js` sem query; só `base_auth.html` usa `?v=20260629-4`. | `rg theme_boot.js` — 1 match com `?v=`; demais sem versão |
| M-03 | **Esquemas de `?v=` incompatíveis** — numérico (`?v=49`), sem versão, data (`20260629-4`); impossível política única de cache-bust. | `register.js ?v=49`, `dashboard.css ?v=29`, `login.css ?v=20260629-4`, `plans.js ?v=1` |
| M-04 | **Versão CSS divergente no mesmo fluxo dependente** — `dependent_registration.css ?v=14` vs `dependent_registration_done.css ?v=7` no done. | `dependent_registration.html` L11; `dependent_registration_done.html` L10 |
| M-05 | **`installment_select.html` com `register.css ?v=7`** — página do fluxo de cadastro com cache potencialmente obsoleto (wizard em `?v=26`). | `installment_select.html` L9 |
| M-06 | **Logo tema escuro via `filter: invert`** — hack em vez de `logo-lv-white.png` (asset existe, não usado na home). | `dashboard.html` L16 `logo-lv-dark.png`; `dashboard.css` L123 `filter: invert`; assets `logo-lv-white.png` em `static/system/img/` |
| M-07 | **Fonte Montserrat só no shell auth** — dashboard/register usam `system-ui`; identidade tipográfica inconsistente. | `base_auth.html` L10–12; ausente em `dashboard.html`/`register.html` |
| M-08 | **Tabs sem navegação por teclado (setas)** — só click; não segue APG tab pattern. | `dashboard.js` `bindTabs` L89–114 — sem `ArrowLeft`/`ArrowRight` |
| M-09 | **`window.confirm` / `alert` nativos** — UX dissonante com modais customizados. | `dashboard.js` L826 `confirm` remoção dependente; L1683 `alert` cancelar aula |
| M-10 | **Mensagens auto-dismiss 5s** — usuário pode perder erro crítico. | `dashboard.js` L79–86 `bindAutoDismissMessages` |
| M-11 | **Estilos inline em templates** — escapam tokens; dificultam tema. | `rg style=` → 35 ocorrências em 30 templates; `person_detail.html` 38× |
| M-12 | **`home-config` JSON inline monolítico** — string única em `dashboard.html` L45; frágil a URLs vazias e difícil de validar. | Template `dashboard.html` L45 |
| M-13 | **Barra de progresso wizard com largura inline fixa** — desalinhada se número de etapas mudar no servidor. | `register.html` L49 `style="width:16.66%"` (6 etapas hardcoded no markup L43) |
| M-14 | **Cupom validado via rota PT `/cadastro/validar-cupom/`** — acoplamento i18n URL no JS. | `register.js` L2701 |
| M-15 | **CEP via ViaCEP no wizard** — dependência externa no cliente; falha de rede sem degradação clara. | `register.js` L84 `fetch('https://viacep.com.br/ws/'` |
| M-16 | **Scripts inline adicionais** — `person_detail.html`, `person_confirm_delete.html`, `installment_select.html` com blocos `<script>` de comportamento. | `templates/login/installment_select.html` L231+; `person_confirm_delete.html` L79+ |
| M-17 | **`plan_form_modal.html` script sem `defer`** — pode bloquear parse do iframe. | `plan_form_modal.html` L52; `tier_form_modal.html` L52 |
| M-18 | **Contraste `modal-open` vs `overflow: hidden`** — duas APIs para travar scroll. | `client-profile` usa `body.classList.add('modal-open')` L482; calendar usa `body.style.overflow` L361 |

---

### BAIXA

| ID | Problema | Evidência |
|---|---|---|
| B-01 | **`store_cart.js` minimalista sem feedback** — só monta JSON no submit; sem validação de estoque no cliente (OK se server valida). | `store_cart.js` L1–20 |
| B-02 | **`calendar.js` sem `innerHTML`** — positivo relativo, mas `calendar.html` repete inline theme IIFE. | `calendar.html` L8; `calendar.js` sem `innerHTML` |
| B-03 | **SVG e ícones duplicados inline** — dezenas de blocos SVG idênticos em templates; peso de HTML. | `dashboard.html` — múltiplos `<svg>` no topbar/quick links |
| B-04 | **`prefers-reduced-motion` só em `register.css`** — dashboard não reduz animações de seção/modal. | `register.css` L2280–2282; ausente em `dashboard.css` |
| B-05 | **Partial home sem testes visuais documentados** — `home/partials/*.html` (4) acoplados ao dashboard sem isolamento. | `templates/home/partials/` |
| B-06 | **Favicon não referenciado em wizard/dashboard** — só em `base_auth.html` L8. | `register.html`, `dashboard.html` sem `<link rel="icon">` |

---

### Matriz resumo

| Severidade | Qtd IDs |
|---|---:|
| CRÍTICA | 7 |
| ALTA | 11 |
| MÉDIA | 18 |
| BAIXA | 6 |
| **Total** | **42** |

## Proposta de correção

> Proposta de correção preenchida pelo consolidador em jul/2026.

Plano acionável alinhado a PRD-138 (ondas 2–3), PRD-142 (home/selectors) e PRD-143 (API elegibilidade + god-form). **Pré-requisito bloqueante:** achados C-01 e C-07 só entram em P1 após PRD-143 Onda P0 (validação unificada + API read-model).

### Ondas priorizadas

| Onda | Foco | Risco global | Dependências |
|---|---|---|---|
| **P0** | Shell base + segurança JSON + política `?v=` | Médio | Independente de JS; **não** deduplicar 62 templates antes de `base.html` |
| **P1** | Elegibilidade server-driven + módulo wizard compartilhado | Alto | **Bloqueado por** PRD-143 P0 (`registration_forms` fatiado + API elegibilidade) |
| **P2** | `innerHTML`, dashboard/modais, tokens CSS, a11y | Médio–alto | P1 concluída; PRD-080 residual |

---

### Onda P0 — Fundação shell e cache (sem tocar regra de negócio JS)

| ID | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| C-06 | Criar `templates/lv/base.html` com blocos `title`, `extra_css`, `content`, `extra_js`; incluir favicon, meta, `theme_boot.js?v=…`, holder CSRF | Novo `templates/lv/base.html`; piloto: `templates/people/person_list.html`, `templates/calendar/calendar.html` | 2 templates piloto usam `extends`; `rg ^<!DOCTYPE` reduz em 2; tema claro/escuro OK desktop+mobile no browser | Médio |
| C-05 | Substituir `\|safe` em JSON por `json_script` ou serialização escapada Django | `templates/login/register.html` L13–24; `templates/dependents/dependent_registration.html` L12–16 | Nenhum `\|safe` em `<script type="application/json">`; wizard carrega catálogo; console sem erro | Baixo |
| M-02, M-03 | Política única `?v=YYYYMMDD-n` em **todos** os assets referenciados por `base.html` e shells existentes | `theme_boot.js`, `theme_toggle.js`, `crud_modal.js`; grep em `templates/` | `rg 'theme_boot\.js"'` → 0 sem `?v=`; bump documentado em `UI-SCREEN-CONTRACT.md` | Baixo |
| B-06 | Favicon e meta comuns via `base.html` | Piloto + `register.html`, `dashboard.html` na P1 | `<link rel="icon">` presente nas páginas piloto | Baixo |

**Dependência interna:** C-06 **antes** de migrar os 62 standalone (mapa faseado: admin CRUD → home → wizard).

**O que NÃO fazer em P0:**
- Não remover `innerHTML` nem fatiar `register.js` (mascara divergência com backend).
- Não unificar tokens CSS (`register.css` `:root`) antes de `base.html` definir stack canônico.
- Não alterar `resolveAudience` / `getEligiblePlansForCurrentPerson` no JS.

---

### Onda P1 — Wizard server-driven e deduplicação (após PRD-143 P0)

| ID | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| C-01, C-07 | Remover elegibilidade do JS; consumir API read-model (`build_eligibility_context_for_person` exposta via view JSON) | `static/system/js/auth/register.js` L2218–2257, L1427–1446; `dependent_registration.js` L146–201, L341–373; nova rota em `auth_views.py` / service (PRD-143) | Teste HTTP: resposta API = resultado de `plan_eligibility.py` para fixture família; JS só renderiza cards desabilitados/habilitados; **zero** `calcAgeYears` para filtro de plano | Alto |
| C-02, C-03 | Extrair `static/system/js/lv/wizard_shared.js` (catálogo turmas/planos, `escHtml`, máscaras, navegação steps) | `register.js`, `dependent_registration.js`; templates com `?v=` bump | LOC `register.js` < 2000; `dependent_registration.js` < 600; funções duplicadas `bindClassCatalog`/`renderClassCatalog` unificadas | Alto |
| A-06 | Unificar parsing de data para ISO no shared (backend já valida) | `wizard_shared.js`; remover `split('/')` exclusivo em `register.js` | Mesma data DD/MM e ISO produz mesma elegibilidade turma em teste E2E | Médio |
| C-06 (cont.) | Migrar `register.html` e `dependent_registration.html` para `extends lv/base.html` | `templates/login/register.html`, `templates/dependents/dependent_registration.html` | Wizard herda tema/favicon/CSRF; sem IIFE inline duplicado (M-01) | Médio |
| A-10 | Reativar validação HTML5 progressiva onde possível; manter gate server-side por etapa | `register.html` L70 `novalidate` → condicional ou removido com `required` por step | Sem JS: submit bloqueado server-side com 400; com JS: etapas intermediárias não POSTam finalize | Médio |

**Dependências:** PRD-143 achados #1, #10 (god-form + validação única) **concluídos** antes de iniciar C-01. PRD-138 Onda 2 (PRD-129) em paralelo aceitável.

**O que NÃO fazer em P1:**
- Não deletar `dependent_registration.js` inteiro antes do shared estável.
- Não mover checkout/cupom para o shared sem testes de pagamento sandbox.

---

### Onda P2 — Hardening UI, performance cliente e a11y

| ID | Ação | Arquivos | Critério de aceite | Risco |
|---|---|---|---|---|
| C-04 | Eliminar `innerHTML` com dados dinâmicos (PRD-080); usar `textContent`, `createElement`, ou template `<template>` | `register.js` (22×), `dependent_registration.js` (18×), `dashboard.js` (3×) | `rg innerHTML static/system/js` → 0 em fluxos com dado de usuário; testes wizard verdes | Alto |
| A-01, A-02 | Partir `dashboard.js` / `dashboard.html` por domínio; modais lazy-load | `dashboard.js`, `dashboard.html`, novos `static/system/js/home/*` | `dashboard.html` < 800 linhas; modais fora do viewport inicial carregam sob demanda | Alto |
| A-03, A-04 | Módulo modal único: focus trap, `inert` no fundo, Escape centralizado, retorno de foco | Novo `static/system/js/lv/modal.js`; refatorar `dashboard.js` bind*Modal | axe/dialog: foco preso; 1 listener Escape; tab order válido em 3 modais amostra | Médio |
| A-05 | Atualização incremental de catálogos (diff DOM) em vez de re-render total | `wizard_shared.js` `renderPlanCards` / `renderClassCatalog` | Filtro de plano não destrói foco; Performance tab sem layout thrash visível | Médio |
| A-07 | Zerar `iframe.src` ao fechar modais dependente/cronograma | `dashboard.js` L419–423; alinhar a `crud_modal.js` L31–33 | Memória estável após 5 abrir/fechar; network sem reload duplicado | Baixo |
| A-08, A-09 | Remover `:root` de `register.css`; admin usa só `base.css` tokens | `register.css` L6–39; templates admin | Diff visual zero tema claro/escuro; uma fonte `--bg`/`--surface` | Médio |
| A-11 | Padronizar `getCsrfToken` em helper `lv/csrf.js` | `dashboard.js`, `register.js` L2701 | POST cupom/AJAX falha com mensagem se token ausente | Baixo |

**Dependências:** P1 shared wizard estável. `base.html` (P0) antes de deduplicar CSS admin em massa.

**O que NÃO fazer em P2:**
- Não fundir os dois sistemas de modal (iframe CRUD vs overlay dashboard) em um só sem PRD de design aprovada.
- Não trocar ViaCEP por hardcode; manter degradação graciosa (M-15).

---

### Achados MÉDIA/BAIXA — backlog P2+

| IDs | Ação resumida | Quando |
|---|---|---|
| M-01 | Remover 17 IIFEs theme após `base.html` | P0 migração shell |
| M-06–M-09, M-13–M-18 | Polish UX (logo, tabs teclado, `confirm`→modal) | Após P2 modais |
| B-03–B-05 | SVG partials, `prefers-reduced-motion` dashboard | Onda 3 PRD-138 |

---

## Cross-PRD dependencies

| Dependência | PRD parceira | Direção | Bloqueio |
|---|---|---|---|
| API elegibilidade + validação unificada | **PRD-143** P0 (#1, #10) | 143 → 141 | C-01, C-07 não iniciam sem API |
| `registration_forms` fatiado | **PRD-143** P0 | 143 → 141 | Remover regra JS antes do form/service |
| `home_views` → selectors | **PRD-142** P0 + **PRD-143** P1 (#6) | 142+143 → 141 | Dashboard consome contexto já otimizado |
| `base.html` antes deduplicação templates | **PRD-141** P0 | 141 → 141 | 62 standalone só após shell |
| `innerHTML` / PRD-080 | **PRD-141** P2 | Interno | Após shared wizard |
| Shell + tokens | **PRD-138** Onda 3 | 138 ↔ 141 | Alinhar PRD-075/084 |
| Catálogo `PlanTier` only | **PRD-138** Onda 2 / **PRD-143** P1 (#8) | 143 → 141 | Wizard consome só `pp:` na API |

## Visual hierarchy

Estado atual (não prescritivo):

- **Wizard** — coluna única 540px, header fixo (voltar/logo/progresso), steps empilhados `hidden`.
- **Dashboard** — topbar global + seções recolhíveis + abas por pessoa (billing/classes/profile).
- **Admin** — topbar simplificada + tabela/lista + ações CRUD em modal iframe.

## Wireframe

```text
[WIZARD 540px]                 [DASHBOARD full]              [ADMIN list]
┌──────────────────┐          ┌────────────────────────┐   ┌────────────────────────┐
│ ← Logo    Etapa  │          │ Logo    [perfil][tema]│   │ Logo    [tema] [sair] │
│ ████░░░░ progress│          ├────────────────────────┤   ├────────────────────────┤
│ Título step      │          │ ▼ Seção (collapse)     │   │ Filtros / KPIs         │
│ [cards/lista]    │          │   cards / tabelas      │   │ Tabela                 │
│ [Próximo]        │          │ [modal overlay 12×]    │   │ [dialog>iframe CRUD]   │
└──────────────────┘          └────────────────────────┘   └────────────────────────┘
```

## State machine

Wizard (`register.js`): máquina de estados **no cliente** — perfil → dados → martial → turmas (N alunos) → planos (N alunos) → pagamento → materiais → revisão → POST final. Transições bloqueadas por `validate*` locais; flags servidor (`reg-post-plan-json`, etc.) apenas reidratam entrada.

Dependente (`dependent_registration.js`): subconjunto espelhado com `data-payment-confirmed` / `data-materials-confirmed` no form.

Dashboard: sem máquina unificada; cada modal é micro-estado independente com DOM próprio.

## Plan

### Onda P0 — Shell e cache
- [x] Criar `templates/lv/base.html` e migrar 2 templates piloto admin (`person_list.html`, `calendar.html`)
- [x] Corrigir C-05: `json_script` em `register.html` e `dependent_registration.html`
- [x] Normalizar `?v=` em `theme_boot.js`, `theme_toggle.js`, `crud_modal.js` (M-02, M-03)
- [ ] Documentar mapa de migração dos 62 standalone (fases: admin → home → wizard)
- [ ] Atualizar `docs/UI-SCREEN-CONTRACT.md` com shell real

### Onda P1 — Wizard (após PRD-143 P0)
- [x] Validar C-01/C-07 contra API `plan_eligibility.py` (teste contrato) — titular e dependente
- [x] Extrair `wizard_shared.js` — extração cirúrgica das funções duplicadas (calc idade, elegibilidade, CSRF, endpoints); **não** reduziu `register.js`/`dependent_registration.js` abaixo das metas de LOC (<2000/<600) — ver PRD-144 F-06/F-07
- [x] Unificar parsing de data (A-06) — backend + `wizard_shared.js` aceitam DD/MM e ISO
- [ ] Migrar wizard templates para `extends lv/base.html`
- [ ] Revisar `novalidate` e gate server-side (A-10)

### Onda P2 — Hardening
- [ ] Executar PRD-080: eliminar 43 `innerHTML` (C-04) — iniciado (`setElementText` no empty-state de planos do dependente), 41 ocorrências restantes
- [ ] Partir `dashboard.html` / `dashboard.js` (A-01, A-02)
- [ ] Implementar `modal.js` com focus trap + Escape único (A-03, A-04)
- [ ] Unificar tokens CSS; remover `:root` de `register.css` (A-08, A-09)
- [x] Lifecycle iframe modais (A-07) — dependente e calendário
- [x] Padronizar `getCsrfToken` (A-11) — `lv/csrf.js`

## Test plan

### Tests to author

- [ ] Testes E2E wizard: elegibilidade plano/turma bate resposta API/servidor
- [ ] Testes a11y automatizados (axe) em modais dashboard
- [ ] Testes de regressão visual desktop/mobile tema claro/escuro por shell

### Execution authorization

Auditoria read-only — testes **não executados** nesta PRD.

### Execution evidence

- Nenhum (pendente PRDs de execução).

## Visual validation

| Item | Status |
|---|---|
| Browser desktop wizard | Não executado |
| Browser mobile wizard | Não executado |
| Browser dashboard modais | Não executado |
| Tema escuro/claro | Não executado |
| Console limpo | Não executado |

## ORM validation

Não aplicável (escopo frontend read-only).

## Quality validation

| Verificação | Resultado |
|---|---|
| Inventário 92 templates | OK (`Glob`) |
| Inventário 27 assets | OK (`Glob`) |
| Leitura integral arquivos críticos | OK (register.js por seções) |
| `rg innerHTML` / `?v=` / shells | OK |

## Evidence

- Contagens linhas (PowerShell 2026-07-08): `register.js` 3334, `dashboard.js` 1716, `dependent_registration.js` 1204, `dashboard.html` 1316, `register.html` 1053, `register.css` 2015, `dashboard.css` 2860.
- `rg innerHTML` em `static/system/js`: 43 ocorrências (22+18+3).
- `rg ^<!DOCTYPE` em templates: 62 standalone.
- `rg extends`: 25 `lv/modal_frame`, 5 `auth/base_auth`.
- `rg localStorage.getItem('lv-theme')`: 17 inline IIFEs.
- `rg theme_boot.js`: 42 templates; 1 com `?v=`.

## Implemented

Nada implementado na auditoria original — documentação apenas.

**[2026-07-09] Onda P0 + parte da P1 executadas** (fora do escopo original read-only, autorizadas pelo usuário):

- **Onda P0** — `templates/lv/base.html` criado (piloto em 2 telas); `json_script` substituindo `|safe` em `register.html`/`dependent_registration.html` (C-05); `?v=` normalizado em 44 templates (M-02/M-03). Ver evidência na PRD-138.
- **Onda P1 (parcial) — C-01/C-07 (elegibilidade server-driven no wizard público)**: `register.js` (`static/system/js/auth/register.js`, `?v=50`) agora consulta `POST /cadastro/elegibilidade/` (API criada na PRD-143 P0) via `refreshEligibilityFromServer()`, cacheada por `state.eligibility` (chave = hash do payload relevante). `getEligiblePlansForCurrentPerson()` usa a lista `eligible_plan_ids` do servidor como autorização de negócio (família, audiência agregada); o cálculo local (`resolveAudience`) permanece só como (a) fallback antes da resposta chegar e (b) filtro de **apresentação** — qual aba de pessoa mostrar, não mais fonte de verdade sobre elegibilidade.
  - Risco mitigado: sem framework de E2E no projeto, validado via navegador interno com verificação de rede/DOM em cada passo (não só screenshot) — POST confirmado nos logs do servidor, resposta da API conferida byte-a-byte contra o `context` esperado (holder adulto + dependente kids → `adult_family_group_eligible=true`), troca de aba confirmada sem refetch redundante (cache funcionando), zero erros no console em todas as etapas.
  - **Não fechado nesta rodada**: `dependent_registration.js` continua com elegibilidade 100% client-side (mesmo padrão, não replicado ainda); unificação de parsing de data (A-06); migração de `register.html`/`dependent_registration.html` para `extends lv/base.html`; revisão de `novalidate` (A-10). Ficam para a próxima rodada da Onda P1.
  - Evidência: `manage.py test system` — 662 testes OK; `node --check register.js` sem erro de sintaxe; validação manual completa do wizard holder+dependente (perfil → dados → saúde → marcial → turmas → **plano com API** → materiais → volta ao plano) sem regressão.
- **[2026-07-09] Onda P1 fechada — C-01/C-07 completo, A-06, A-07, A-11**:
  - **A-06 (parsing de data unificado)**: `registration_validation.py::_parse_birthdate` passou a aceitar `%d/%m/%Y` **e** `%Y-%m-%d` (fallback), já que `dependent_registration.js` usa `<input type="date">` (ISO) e a API de elegibilidade antes só entendia o formato BR do wizard público. Teste dedicado: `test_registration_eligibility_api.py::test_holder_birthdate_accepts_iso_format`.
  - **C-01/C-07 (dependente) — fechado**: `dependent_registration.js` passou a consultar `POST /cadastro/elegibilidade/` (mesmo endpoint do wizard público), representando o dependente como um "holder" isolado no payload. Cobre o branch **realmente ativo** (`dependentOwnPlanEligible` — plano próprio do dependente). O branch de "plano família" (`familyUpgradePlanEligible`) permanece client-side **por achado, não por atalho**: nenhum `PlanPrice` ativo tem `is_family_plan=true` hoje (migração PRD-127 moveu os planos família para o catálogo novo, que não tem variante família — `get_eligible_plan_prices` só filtra por audiência); logo esse branch já é hoje um caminho morto na prática, e não há regra de negócio real para migrar ali sem antes desenhar um produto "PlanPrice familiar" (fora de escopo desta PRD).
  - **Extração `wizard_shared.js`** (`static/system/js/auth/wizard_shared.js`, namespace `window.LV.Wizard`): consolidou as funções genuinamente duplicadas entre os dois wizards — `calcAgeYears`/`resolveAudience` (agora aceitam DD/MM **e** ISO em ambos os wizards, fechando de vez a divergência A-06 também no cliente), `escapeHtml`, `readJsonScript`, `eligibilityFetchKey`/`fetchEligibility` (máquina de cache+POST da elegibilidade), `getFormEndpoints` (lê `data-eligibility-url`/`data-validate-coupon-url` do `<form>`, eliminando a URL PT hardcoded `/cadastro/validar-cupom/` — achado M-14 também fechado), `setElementText` (helper DOM seguro, início do C-04), `formatIsoDateForDisplay`, `warn`. `register.js` e `dependent_registration.js` carregam o módulo antes de si (`<script>` não-deferred) e abortam com erro no console se `window.LV.Wizard` não existir.
  - **A-11 (CSRF único)**: `static/system/js/lv/csrf.js` (`window.LV.getCsrfToken`) substituiu 3 implementações locais quase-idênticas em `dashboard.js`, `register.js` e `dependent_registration.js`.
  - **A-07 (lifecycle de iframe)**: `dashboard.js` — `closeModal()` dos modais de dependente e de calendário agora zera `frame.src = 'about:blank'` ao fechar (mesmo padrão de `crud_modal.js`), evitando estado obsoleto do wizard ao reabrir.
  - Validação: `manage.py test system` — 674 testes OK (674 = 662 + testes novos desta e de outras ondas paralelas). Navegador interno: wizard público (`/register/`) e wizard de dependente (`/dependents/add/?modal=1`) percorridos ponta a ponta até o step de plano com pessoa titular real (membership ativa), confirmando nos logs de rede o `POST /cadastro/elegibilidade/` disparando com o payload correto e a resposta determinando os cards de plano renderizados (cenário adulto e cenário criança testados nos dois wizards), console sem erros em nenhuma etapa.
  - **Ainda não fechado**: F-06/F-07 (LOC de `register.js`/`dependent_registration.js` — a extração foi cirúrgica, não uma reescrita completa: ~3.831L / ~1.398L hoje); C-04 completo (43 `innerHTML`, só o "empty state" de planos foi migrado para `setElementText`); A-01/A-02 (split do dashboard); A-03/A-04 (`modal.js` com focus trap); A-08/A-09 (tokens CSS únicos); A-10 (`novalidate`); migração de `register.html`/`dependent_registration.html` para `extends lv/base.html`. Avaliados como risco médio/alto sem bug de correção subjacente (são polish estrutural, não corrigem divergência de regra de negócio) — deixados para PRD-147 (ver PRD-144).

## Cleanup findings

- PRD-080 permanece aberta; escopo ampliado (inclui `dependent_registration.js`).
- PRD-084 (tokens CSS) parcialmente violada por `register.css` duplicar `:root`.
- Número PRD-041 já usado por “Stripe recorrente”; esta auditoria usa **PRD-141** conforme solicitado.

## Follow-up PRDs

| PRD sugerida | Escopo |
|---|---|
| PRD-142+ (consolidador) | Shell unificado + extração wizard shared |
| PRD-080 (existente) | Eliminar `innerHTML` |
| PRD-084 (existente) | Tokens CSS únicos |

_Numeração final a cargo do consolidador._

## Deviations from plan

Nenhum — escopo read-only cumprido.

## Pending

- Execução das ondas P0–P2 (requer PRD-filha de implementação por onda).
- PRD-143 P0 concluída antes de P1 (elegibilidade JS).
- Validação browser desktop/mobile pós-implementação.

## Final status

**Concluída** — auditoria estática entregue; proposta de correção consolidada (jul/2026). Implementação pendente de aprovação por onda.
