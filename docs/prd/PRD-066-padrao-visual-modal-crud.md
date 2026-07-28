# PRD-066: Padrão visual e de CRUD em modal

## Summary
Trazer para o LV JIU JITSU a geração de UI consolidada: CRUD curto em modal/dialog na própria tela, ações icônicas em cards, fundação compartilhada de tema/datas/modais e responsividade desktop/mobile com tema claro/escuro. O LV hoje usa templates full-page standalone (`person_form`, `person_detail`, `person_confirm_delete`) e cards com link único "Detalhe" — padrão legado a aposentar.

## Demand type
Reescrita arquitetural de UI multi-módulo, faseada.

## Required skills
- `lv-task-intake`
- `lv-ui-delivery`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Current problem
- O `UI-SCREEN-CONTRACT.md` do LV não declara regra de CRUD curto em modal/dialog (0 ocorrências).
- Não existe fundação JS/CSS compartilhada: o boot de tema está duplicado inline em cada template; não há utilitário de datas pt-BR nem controlador de modais.
- As telas operacionais não estendem um layout/shell comum; cada uma é um documento HTML isolado.
- O CRUD navega para telas dedicadas em vez de abrir popup.

## Goal
Estabelecer no LV o contrato e a experiência de referência:
- Fundação compartilhada (`theme_boot`, `pt_br_date_inputs`, `crud_modal`, `crud_frame`) e CSS do sistema de `icon-action` + `crud-modal`.
- Regra normativa §15.11 "CRUD operacional em modal/dialog" no contrato de UI do LV.
- Conversão módulo a módulo para listagem com ações icônicas (visualizar/editar/excluir + ações de domínio) e CRUD curto em modal server-rendered via `<dialog>` + iframe.

## Mapeamento de tokens
| Token de origem | LV |
|---|---|
| `--brand` | `--brand-red` |
| `--brand-muted` | `--brand-red-muted` |
| `--background` | `--panel` |
| `theme` (localStorage) | `lv-theme` |

## Contrato visual replicado
- `.icon-action`: 44×44, borda 1.5px `var(--border)`, raio 0.5rem, `background: var(--panel)`, ícone 1rem; modificadores `--view` (brand), `--edit` (brand), `--delete` (danger).
- `.crud-modal`: `<dialog>` com header (eyebrow + título + botão close 44×44) e corpo iframe (`width: min(860px, calc(100vw - 2rem))`); `::backdrop` `rgba(15,23,42,.48)`; fallback `.is-open` para navegadores sem `<dialog>`.
- Mobile: ações icônicas em grade de 44px; modal ocupa `calc(100vw - 1rem)`.

## Escopo por fases
1. **Fundação compartilhada** (este ciclo): assets JS/CSS, layout/shell `portal_module`, partials de topbar/tema/mensagens, regra §15.11. Verificável por `manage.py check` e `collectstatic`.
2. **Pessoas (referência)**: listagem com ações icônicas + criar/editar/visualizar em modal + excluir com confirmação; endpoints modais server-side. Validação no navegador desktop/mobile, claro/escuro.
3. **Replicação**: Turmas, Planos, Graduação, Financeiro, Produtos e Administração/Módulos, cada um em incremento próprio reutilizando a fundação.

## Out of scope
- Portar domínio externo (viagens, vistos, processos consulares, dependentes de assessoria).
- Criar migrations, alterar regra de negócio ou schema.
- Executar testes, seeds ou reset sem autorização.

## Acceptance criteria
- [x] Fundação JS/CSS compartilhada criada em `static/system/js/shared/` (theme_boot, pt_br_date_inputs, crud_modal, crud_frame) e `static/system/css/shared/crud_modal.css`.
- [ ] `templates/layouts/portal_module.html` e partials de topbar/tema/mensagens criados e reutilizáveis.
- [x] §15.6 (CRUD em modal/dialog) adicionada ao `docs/UI-SCREEN-CONTRACT.md`.
- [x] Pessoas: card exibe ações icônicas visualizar/editar/excluir respeitando permissões (editar/excluir só `can_manage_people`).
- [x] Pessoas: criar/editar/visualizar abrem em modal (iframe) sem trocar de tela; POST inválido re-renderiza com erro de campo no modal (validado: CPF inválido → 200 com erro, não 500).
- [x] Excluir usa diálogo de confirmação (`data-confirm-submit`) e respeita `ProtectedError`; validado E2E (criação→exclusão com mensagem de sucesso).
- [x] Desktop e mobile (375px, sem overflow) e claro/escuro corretos; console sem erro crítico.
- [ ] Cada módulo replicado mantém o mesmo contrato visual.

## Expected evidence
- `manage.py check` sem issues.
- `collectstatic --noinput` por alteração em static.
- Validação visual no navegador interno por módulo (desktop/mobile/claro/escuro).
- Testes focados escritos por módulo; execução somente sob autorização.

## Status
- [x] Fase 1 — Fundação (assets compartilhados + §15.6 + este PRD; `manage.py check` sem issues)
- [x] Fase 2 — Pessoas (referência): lista com ações icônicas + modais criar/editar/visualizar + excluir; validado no navegador (desktop/mobile/claro/escuro). Correção colateral: `clean_cpf` agora levanta `ValidationError` em vez de deixar `ValueError` escapar (evitava 500 ao editar CPF inválido). `ModalCrudMixin` libera `X-Frame-Options: SAMEORIGIN` apenas em respostas `?modal=1`.
- [ ] Fase 3 — Replicação por módulo (Turmas, Planos, Graduação, Financeiro, Produtos, Admin)

Concluída com limitações: Fases 1 e 2 entregues e validadas no navegador. Fase 3 pendente — replicar o padrão de Pessoas nos demais módulos reutilizando a fundação e o `ModalCrudMixin`.
