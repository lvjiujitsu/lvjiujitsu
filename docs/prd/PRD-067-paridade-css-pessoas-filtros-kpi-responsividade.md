# PRD-067: Paridade de CSS de Pessoas — filtros, KPIs, linhas e responsividade

## Summary
Corrigir a homologação visual do módulo Pessoas para atingir paridade com o hub de referência. A primeira passada (PRD-066) entregou o padrão de modal/ações icônicas, mas o CSS de linhas (cards), filtros e responsividade divergiu do contrato, e a faixa de KPIs foi mantida — em conflito com a governança anti-KPI do contrato de tela.

## Demand type
Correção de UI/CSS com paridade de referência + governança.

## Required skills
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Current problem
Comparando `static/system/css/people/people.css` (LV) com `static/system/css/client/clients.css` + `portal/modules.css`:
1. `.person-card` usa `align-items: center`; o padrão pede `flex-start` (linhas desalinham quando há badges + meta).
2. `.person-card__name` e `.person-card__meta` truncam com `nowrap/ellipsis`; o padrão deixa quebrar (`line-height` 1.3/1.45, `overflow-wrap: anywhere`).
3. `.person-card__avatar` é cinza (`surface-soft`/`muted`); o padrão usa avatar com marca (`brand-muted`/`brand-strong`).
4. `.icon-actions` diverge: o padrão é `justify-content: flex-end; gap: 0.375rem; flex-wrap: nowrap`.
5. `.filter-input/.filter-select` têm `height: 36px`; o padrão usa `44px`. `.filter-field` recebe `max-width: 200px` que o contrato não prevê.
6. Não há regra mobile para as linhas: em ≤768px o card deve fazer `flex-wrap: wrap` e as ações viram grade alinhada após o avatar (`margin-left: calc(40px + 1rem)`). No LV as ações ficam comprimidas/cortadas.
7. Faixa de KPIs (6 cards) presente sem pedido — o contrato proíbe KPI não solicitado em hub operacional.

## Goal
- Reescrever os blocos de `card/linha`, `filtros` e `responsividade` de `people.css` reproduzindo o contrato de referência com tokens do LV.
- Alinhar `.icon-actions` da fundação (`crud_modal.css`) ao contrato.
- Remover a faixa de KPIs de Pessoas (template + contexto/helper na view).
- Registrar a regra anti-KPI no `UI-SCREEN-CONTRACT.md`.

## Mapeamento de tokens
`--brand`→`--brand-red`, `--brand-strong`→`--brand-red-strong`, `--brand-muted`→`--brand-red-muted`.

## Out of scope
- Remover KPIs de outros módulos (Home, etc.) — tarefa própria.
- Alterar o domínio ou a lógica de Pessoas além do contexto de KPI.
- Migrations, seeds, reset.

## Acceptance criteria
- [x] `.person-card` alinha ao topo (`flex-start`); nome e meta quebram sem truncar.
- [x] Avatar usa marca (`backgroundColor rgba(224,34,68,.12)` / `color rgb(196,18,48)` confirmados por computed style).
- [x] `.icon-actions` = `flex-end`, `gap: 0.375rem`, `nowrap` (desktop).
- [x] Filtros com inputs de 44px (computed) e sem `max-width` artificial.
- [x] Mobile (≤768px): card `flex-wrap: wrap`, ações em grade de 44px com `margin-left: 56px`; sem overflow horizontal (computed confirmado).
- [x] Faixa de KPIs removida de Pessoas (template + view + CSS órfão); `UI-SCREEN-CONTRACT.md §15.7` declara a regra anti-KPI.
- [x] Validação no navegador: desktop e mobile, claro e escuro, console sem erro.

## Expected evidence
- `manage.py check` sem issues ✓.
- `collectstatic` aplicado ✓.
- Testes: `test_person_delete`, `test_admin_hubs_contract`, `test_home_dashboard` → 10 testes OK (nenhuma regressão pela remoção de KPI/ajuste de view).
- Screenshots desktop/mobile/claro/escuro com paridade.

## Status
- [x] Concluída e validada no navegador (desktop/mobile/claro/escuro) + testes verdes.
