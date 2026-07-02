# Padrões Visary → LV JIU JITSU

Referência arquitetural e de UX extraída do projeto irmão Visary (`c:\Users\whsf\Documents\GitHub\visary`). **Não portar domínio** (vistos, viagens consulares, assessores, parceiros de indicação). Apenas padrões reutilizáveis.

Fontes principais no Visary:
- `docs/UI-SCREEN-CONTRACT.md` (§6, §15.9–15.15)
- `system/urls.py`
- `system/views/` (ex.: `partners_views.py`, `etapa_views.py`, `admin_views.py`)
- `templates/layouts/modal_frame.html`, `templates/*/partials/*_modals.html`
- PRDs 080, 075 (destination-countries), 081–085

Relacionado no LV: `PRD-066`, `PRD-075`.

---

## 1. Nomenclatura de rotas (inglês)

### Princípio
- **Paths HTTP:** inglês, kebab-case, substantivos no plural quando for recurso.
- **Nomes de rota Django (`name=`):** inglês, snake_case, verbo + recurso.
- **UI visível:** pt-BR (labels, mensagens, títulos de modal).

### Estrutura canônica por módulo

| Papel | Path | Exemplo Visary | Mapeamento LV sugerido |
|---|---|---|---|
| Hub operacional | `/<resource>/` | `/clients/`, `/partners/` | `/people/`, `/classes/` |
| Listagem completa | `/<resource>/list/` | `/clients/list/` | `/people/list/` |
| Criar | `/<resource>/create/` | `/partners/create/` | `/people/create/` |
| Ver | `/<resource>/<pk>/view/` | `/partners/<pk>/view/` | `/people/<pk>/view/` |
| Editar | `/<resource>/<pk>/edit/` | `/partners/<pk>/edit/` | `/people/<pk>/edit/` |
| Excluir | `/<resource>/<pk>/delete/` | `/partners/<pk>/delete/` | `/people/<pk>/delete/` |
| Sub-recursos | aninhados sob o pai | `/clients/registration-steps/` | `/classes/schedules/` |
| Administração | `/administration/<sub>/` | `/administration/users/` | `/administration/users/` |
| APIs auxiliares | `/api/<resource>/` | `/api/search-zip/` | `/api/search-cep/` |
| Portal autenticado | `/<role>/...` | `/client/dashboard/` | manter prefixo se houver portal |

### Convenções de nome (`name=`)

```
home_<resource>          → hub do módulo
list_<resource>          → listagem completa
create_<resource>        → POST/GET de criação
view_<resource>          → leitura detalhada
edit_<resource>          → atualização
delete_<resource>        → exclusão
```

Exemplos reais: `home_partners`, `create_partner`, `list_users`, `edit_process_status`.

### Query strings para estado de modal (superfície principal)

| Query | Efeito |
|---|---|
| `?create=1` | abre modal de criação |
| `?edit=<pk>` | abre modal de edição |
| `?view=<pk>` | abre modal read-only |
| `?modal=1` | view renderiza conteúdo para iframe interno |
| `?expand_step=<id>` | mantém seção expandida após POST |

GET direto em rota de popup **sem** `?modal=1` → redirect para listagem/hub com query acima.

### O que evitar no LV
- Paths em português (`pessoas/`, `planos/`, `administracao/`).
- Verbos em português no path (`nova/`, `editar/`, `excluir/`).
- Misturar idiomas no mesmo módulo.

---

## 2. CRUD: modal vs redirect

### Regra padrão (§15.11 Visary)

Em **hubs e listagens operacionais**, CRUD curto fica na mesma tela:

| Operação | Comportamento |
|---|---|
| CREATE curto | modal de formulário |
| READ curto | modal read-only |
| UPDATE curto | modal pré-preenchido |
| DELETE | `<dialog>` de confirmação + POST server-side |

**Redirect/navegação** só quando muda de superfície: listagem completa, wizard longo, configuração avançada, auditoria, formulário multi-seção.

### Dois mecanismos de modal no Visary

#### A) Modal com iframe (formulários médios/grandes)

Fluxo:
1. Página pai inclui partial `_*_modals.html` com `<dialog>` + `<iframe>`.
2. Iframe carrega rota CRUD com `?modal=1`.
3. View detecta modal → `base_template = layouts/modal_frame.html` + `@xframe_options_sameorigin`.
4. POST válido → renderiza `modal_complete.html` (dispara fechamento/recarga no pai).
5. POST inválido → re-renderiza formulário **dentro do iframe** com erros por campo.

Contrato técnico:
- GET sem `?modal=1` → `redirect` para listagem com `?create=1` / `?edit=<pk>` / `?view=<pk>`.
- POST válido em modal → `messages.success` + resposta de conclusão modal.
- POST válido fora de modal → `redirect` para listagem.
- Comunicação iframe→pai: `postMessage` com `window.location.origin` (nunca `"*"`).
- Após sucesso a partir de hub: fechar modal + `window.location.reload()` no pai (preservar contexto).
- `modal_complete_url = None` quando a ação veio de iframe (evita navegar a janela pai).

Componentes reutilizáveis:
- `templates/layouts/modal_frame.html` — shell mínimo do iframe
- `static/system/js/client/modal_frame.js` — tema, altura compacta, cancelamento, conclusão
- `templates/client/modal_complete.html` — página de sucesso pós-POST

#### B) Modal inline server-rendered (CRUD simples)

Usado quando o formulário cabe na listagem (ex.: etapas de cadastro).

Fluxo:
1. Formulário embutido em `<dialog class="registration-modal">` no template da listagem.
2. POST inválido → view re-renderiza **a listagem inteira** com flags `open_create_modal=True` + form com erros.
3. POST válido → redirect para listagem com mensagem (+ query de expansão se houver filhos).

Vantagem: sem iframe; ideal para entidades pequenas e aninhadas.

### Quando usar redirect (exceções documentadas em PRD)

- Wizard público ou operacional longo (`/register/`, cadastro multi-etapa).
- Edição com stepper, muitas seções ou sub-registros complexos.
- Páginas de detalhe que concentram múltiplas áreas (financeiro expandido, formulário consular).
- Primeira implementação pode manter rota dedicada para editar; modal cobre create/view/delete curto.

### Templates standalone

- Remover template dedicado de CRUD curto **somente** quando nenhuma view GET o renderiza mais.
- Cobrir ausência do arquivo em teste.
- Durante transição: redirect da rota antiga para hub com query de modal.

### Ações icônicas na listagem (§15.9–15.10)

- Tabelas densas: `.table-actions` + `.table-action--view|edit|delete`.
- Cards/linhas repetidas: `.icon-actions` + `.icon-action--view|edit|delete`.
- Texto da ação só em `aria-label` e `title`; ícone visível.
- Desktop: ações em linha única; mobile: alvo mínimo 44×44px.
- Botões textuais permanecem para ação primária de página ("Cadastrar pessoa") e formulários.

### Modais read-only (§15.2)

- Fechamento: apenas botão `×` no header.
- Sem rodapé com "Fechar".
- Sem duplicar ações que já existem no card de origem.
- Backdrop clicável fecha.

### Exclusão (§15.1)

- Ícone lixeira → `<dialog class="confirm-delete-dialog">` → POST confirmado.
- Nunca checkbox exposto nem botão primário destrutivo.

---

## 3. Views finas vs services

### Camadas (Visary)

```
views/     → HTTP, permissão, escolha de template, redirect/render
forms/     → validação de entrada, widgets
services/  → regra de negócio, escritas transacionais, efeitos colaterais
selectors/ → leituras reutilizáveis, agregações, formatação para exibição
models/    → persistência e invariantes simples
```

### Responsabilidade da view

A view **faz**:
- `@login_required` / checagem de módulo/perfil.
- Detectar contexto modal (`?modal=1`, POST flag equivalente).
- Montar contexto de abertura de modal (`_partner_modal_context`, `_build_registration_steps_context`).
- Instanciar form, chamar `form.is_valid()`, `form.save()` ou delegar a service.
- Escolher template/base (`portal_module.html` vs `modal_frame.html`).
- Redirect, messages e resposta de conclusão modal.

A view **não faz**:
- Reordenamento complexo de registros.
- Lógica de domínio multi-modelo.
- Formatação reutilizável de dashboards.
- Validação duplicada fora do form.

### Padrão modal na view (helpers privados por módulo)

Cada módulo CRUD modal tende a ter helpers locais na view:

```
_is_modal_request(request)
_<resource>_create_modal_url()
_<resource>_modal_context(request)
_<resource>_modal_complete_response(request, message)
```

Isso mantém a view fina sem criar abstração prematura; a lógica repetida entre módulos vai para mixin ou util compartilhado no LV (`ModalCrudMixin` já previsto em PRD-066).

### Services — quando extrair

Usar `services/` quando houver:
- múltiplas escritas em `transaction.atomic`;
- regras de ordem/posição (ex.: reordenar etapas);
- integrações externas (CEP, gateways);
- efeitos que forms não devem conhecer.

Exemplo de granularidade: `registration_steps.py` expõe funções puras (`resolve_step_order_for_create`, `get_next_step_order`) — view chama, não reimplementa.

### Selectors — quando extrair

Usar `selectors/` para:
- queries reutilizadas entre views;
- montagem de contexto de dashboard;
- formatação de exibição (CPF, status agregados por registro).

Selectors **não** escrevem no banco.

### Forms

- Toda validação de campo no Django Form/ModelForm.
- POST inválido em modal: mesmo form com `.errors` — nunca duplicar validação em JS.
- CSRF em todo POST.

---

## 4. Padrão mobile / desktop

### Breakpoints (§6 Visary)

| Faixa | Uso |
|---|---|
| ≤639px | celular |
| 640–767px | celular grande / tablet estreito |
| 768–1023px | tablet / desktop compacto |
| ≥1024px | desktop operacional |

### Mobile-first

- Layout uma coluna; `viewport-fit=cover` e safe areas.
- Alvos tácteis ≥44×44px (botões, `.icon-action`, close do modal).
- Tabelas → cards ou scroll horizontal **no wrapper da tabela**, não no documento.
- Modais: quase full-screen, ancorados na base, sem overflow horizontal.
  - Ex.: `width: calc(100vw - 1rem)`, `max-height: 92vh`, cantos inferiores retos.
- Formulários longos agrupados por domínio; ações primárias perto do conteúdo afetado.
- Cards com ações no header: em ≤639px, header empilha (`flex-direction: column`); botões `flex: 1`.

### Desktop

- Conteúdo operacional com largura controlada.
- Listagens densas, leitura em padrão F.
- Formulários em duas colunas quando campos relacionados (`.grid-inline`).
- Modal CRUD: `max-width ~860px`, header com eyebrow + título + subtítulo.
- Ações de linha icônicas em linha única.

### Tema claro/escuro

- `html[data-theme="light|dark"]` com tokens CSS (`--bg`, `--panel`, `--text`, `--brand-*`, `--danger`).
- Preferência em `localStorage` (Visary: `visary-theme`; LV: `lv-theme`).
- Iframe sincroniza tema com pai via `postMessage` / leitura do `data-theme` parent.
- Validar **ambos** os temas em toda entrega UI.

### Shell compartilhado

- Hub/listagem estende `layouts/portal_module.html` (topbar, sidebar por permissão, mensagens).
- CSS modular: `static/system/css/portal/operational.css`, CSS por módulo.
- JS compartilhado: `operational.js`, controlador de modal por módulo.
- Proibido: JS inline (exceto JSON seguro), `innerHTML` com dado de usuário, regra de negócio em template/JS.

---

## 5. Checklist para PRDs do LV

Ao especificar um módulo CRUD inspirado no Visary, a PRD deve declarar:

1. **Rotas canônicas em inglês** (path + `name`) e redirects temporários de rotas legadas em português, se houver.
2. **Superfície principal** (hub vs list) e quais ações abrem modal vs navegam.
3. **Mecanismo de modal:** iframe (form médio) ou inline (form simples).
4. **Query strings** de estado (`create`, `edit`, `view`, `modal`).
5. **Comportamento POST:** inválido (re-render com modal aberto) vs válido (message + reload/redirect).
6. **Permissões** validadas na view, não só ocultando botão.
7. **Partial de modais** (`templates/<module>/partials/_<resource>_modals.html`).
8. **Assets** CSS/JS por módulo + bump de `?v=` em static alterado.
9. **Wireframe** desktop e mobile + estados (vazio, populado, modal aberto, erro).
10. **Exceções** justificadas se alguma ação não couber em modal.

---

## 6. Anti-padrões (não replicar)

- CRUD curto que redireciona para página dedicada quando cabe em modal.
- Duplicar "Fechar" no rodapé de modal read-only.
- KPIs, totalizadores ou dashboards executivos sem pedido nominal na PRD.
- Copiar domínio, labels ou fluxos consulares do Visary.
- Navegar a janela pai após POST bem-sucedido em iframe.
- Permissão apenas ocultando ícone na UI.

---

## 7. Relação com PRDs existentes do LV

| LV PRD | Escopo |
|---|---|
| PRD-066 | Portabilidade visual + `ModalCrudMixin` + fundação JS/CSS |
| PRD-075 | Rotas inglesas + shell + CRUD modal (Pessoas como referência) |
| PRD-078 | Templates modais ausentes — depende desta fundação |

Este documento complementa `docs/UI-SCREEN-CONTRACT.md` do LV; não substitui contratos locais de pagamento, cadastro público (PRD-040) ou seeds.

---

*Gerado em 2026-06-30 a partir de exploração readonly do repositório Visary.*
