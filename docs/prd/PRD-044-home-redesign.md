# PRD-044: Home — Redesign Funcional e Visual

> Revisão completa da tela `/home/` com base no mapeamento do legado (maio/2026).
> O PRD-043 consolidou as 4 rotas em uma. Este PRD define o que deve ser exibido,
> como deve se comportar e como deve parecer — com qualidade visual consistente
> com o padrão `register.html` / `register.css`.

---

## Resumo do que será implementado

Redesign completo de `templates/home/dashboard.html` e `static/system/css/home/dashboard.css`, corrigindo bugs de campo, adicionando componentes faltantes (visual de faixa, card de plano com status real, botão "Trocar plano", histórico de presença, ícones SVG), e elevando a qualidade visual ao padrão do wizard de cadastro — limpo, minimalista, funcional, sem cara de template genérico.

---

## Tipo de demanda

Redesign de UI + correção de bugs + implementação de funcionalidades ausentes

---

## Problema atual

### Bugs críticos (campos errados no template)
| Campo usado | Campo correto no serviço | Impacto |
|---|---|---|
| `graduation_progress.percentage` | `graduation_progress.progress_pct` | Barra de graduação sempre em 0% |
| `graduation_progress.current_belt_display` | `graduation_progress.current_belt_rank.display_name` | Nome da faixa nunca exibe |
| `graduation_progress.classes_count` | `graduation_progress.approved_classes_in_window` | Contagem de aulas nunca exibe |

### Funcionalidades ausentes vs. legado
- Nenhum visual de cinturão (faixa SVG com cores e graus)
- Seção de mensalidade não mostra status real (`active_membership.status`)
- Nenhum botão "Trocar plano" para alunos com plano ativo
- Nenhum aviso de responsável financeiro diferente (`billing_owner`)
- Histórico de presença (`attendance_history`) nunca renderizado
- Botão de check-in para aluno ausente
- Ícones dos quick-links são emojis — informal e inconsistente com o padrão visual

### Problema de design
- Visual genérico de "template de dashboard IA" — sem identidade
- Tokens corretos, mas shadows, transições e composição abaixo do padrão `register.css`
- Emojis nos quick-links contradizem o padrão de ícones SVG do `register.html`
- Seção de graduação é mapeada mas nunca exibe nada (campo errado)

---

## Objetivo

1. Corrigir os 3 bugs de campo do serviço de graduação.
2. Implementar visual de cinturão SVG inline com cores e graus da faixa.
3. Implementar card de mensalidade com status real, valor e botão "Trocar plano".
4. Implementar histórico de presença compacto (últimas 5 entradas).
5. Implementar botão de check-in para aluno (POST com `schedule_id` ou `special_id`).
6. Substituir emojis dos quick-links por ícones SVG inline consistentes com `register.html`.
7. Adicionar rotas reais nos atalhos de acesso rápido (staff).
8. Elevar CSS ao padrão de qualidade `register.css`: shadows duplas, transições, hierarquia tipográfica rigorosa.

---

## Context Ledger

### Arquivos lidos integralmente
- `templates/home/dashboard.html` — template atual (versão pós-PRD-043)
- `static/system/css/home/dashboard.css` — CSS atual
- `templates/login/register.html` — referência de padrão visual e componentes
- `static/system/css/auth/register.css` — referência de CSS qualidade
- `system/views/home_views.py` — view e contexto completo
- `system/services/graduation.py` — campos reais de `compute_graduation_progress`
- `system/models/graduation.py` — `BeltRank`: `color_hex`, `tip_color_hex`, `stripe_color_hex`, `get_grade_slots()`
- `system/models/membership.py` — `MembershipStatus`, campos de `Membership`
- `docs/UI-SCREEN-CONTRACT.md` — tokens, breakpoints, papéis, princípios de UX
- `AGENTS.md` e `CLAUDE.md` — protocolos de trabalho

### Arquivos adjacentes consultados
- `system/services/class_calendar.py` — estrutura de `get_today_classes_for_person`, `get_student_checkin_history`
- `system/urls.py` — rotas reais disponíveis (para preencher `href` dos quick-links)
- Legado `C:\Users\whsf\Downloads\lvjiujitsu-b37d45f1576e928d3f8a2be67ea05579ee696c48\` — mapeamento de funcionalidades existentes

### MCPs verificados
- Preview server Django em `http://127.0.0.1:8000` — ativo
- `manage.py check` — 0 issues (pré-implementação)
- `manage.py test --verbosity 2` — 165 testes OK (pré-implementação)

---

## Decisões de produto — o que fica na home

### Tudo inline (renderizado diretamente na home)
| Bloco | Perfis | Dados |
|---|---|---|
| Saudação + data | todos | `today_weekday`, `today_date`, nome do usuário |
| Visual da faixa + progresso | student, instructor, admin | `graduation_progress` |
| Turmas de hoje | todos | `today_classes` |
| Check-in (botão por aula) | student | `schedule_id` / `special_id` |
| Card de mensalidade + status | student | `active_membership`, `pending_order`, `active_trial_access` |
| Histórico de presença (últimas 5) | student, instructor | `attendance_history[:5]` |
| Acesso rápido — grid de links | admin, administrative | URLs reais via `{% url %}` |
| Resumo financeiro (stub) | admin, administrative | placeholder até módulo financeiro |

### Navega para outra tela (botão/link — não popup)
| Ação | Perfil | Rota |
|---|---|---|
| "Trocar plano" | student (plano ativo) | `system:plan-change-select` |
| "Ir para pagamento" | student (pendente) | `system:payment-checkout` |
| "Ver cronograma" | student | `system:student-schedule` |
| "Ver financeiro" | instructor | `system:teacher-financial` |
| "Ver loja" | student, instructor | `system:product-store` |
| "Ver módulo financeiro" | admin, administrative | `system:financial-control` |
| "Django Admin" | admin técnico | `/admin/` |

### Não existe na home (pertence a módulo dedicado)
- Criação de aulão — instrutor usa calendário (`system:instructor-calendar`)
- Aprovação de check-in de alunos — tela de calendário do instrutor
- Histórico completo de faturas — módulo financeiro
- Edição de plano / regras — módulo de planos
- Cadastro de pessoas — módulo de pessoas

### Sem popups
A home é um **painel de resumo e lançamento**. Toda ação destrutiva ou complexa acontece em página dedicada. Nenhum modal ou popup será implementado nesta tela.

---

## Hierarquia Visual

- Padrão de leitura: **F Pattern** — informação crítica no topo, ações à direita
- Fonte: `system-ui` (herança do body)
- `h1` (saudação): peso 800, `--text`, 1.625rem mobile / 2rem desktop
- Eyebrow (data): peso 500, `--muted`, 0.75rem, uppercase, `letter-spacing: 0.07em`
- Título de seção: peso 700, `--muted`, 0.6875rem, uppercase, `letter-spacing: 0.08em`
- Nome do plano / turma: peso 700, `--text`, 1rem
- Detalhe / subtítulo de card: peso 400, `--muted`, 0.8125rem
- Badge de status: peso 700, cor semântica, 0.6875rem, uppercase, `letter-spacing: 0.02em`
- Ação primária (botão): peso 600, fundo `--brand-red`, 0.875rem
- Ação secundária (link): peso 500, cor `--brand-red`, 0.8125rem

---

## Componentes novos ou redesenhados

### 1. Visual de cinturão (belt-visual)

SVG inline no template Django. Gerado server-side com dados do `BeltRank`.

```
Estrutura visual:
┌─────────────────────────────┬──────────────────┐
│  CORPO DA FAIXA (color_hex) │  PONTEIRA        │
│                             │ ████████         │
│                             │ (tip_color_hex)  │
│                             │ com listras de   │
│                             │ grau (grade_slots│
│                             │ em stripe_color) │
└─────────────────────────────┴──────────────────┘
```

Tamanho: 100% de largura, max-width: 280px, altura: 28px (mobile) / 36px (desktop).
Responsivo via CSS. Raio de borda: 4px.
Listras: retângulos verticais na ponteira, `get_grade_slots(grade_number)` retorna `[bool, bool, bool, bool]`.

Template Django:
```html
{% with belt=graduation_progress.current_belt_rank grade=graduation_progress.current_grade_number %}
{% if belt %}
<div class="belt-visual" aria-label="{{ belt.display_name }}{% if grade %}, {{ grade }} grau{{ grade|pluralize }}{% endif %}">
  <svg ...>
    <!-- corpo -->
    <rect x="0" y="0" width="72%" height="100%" fill="{{ belt.color_hex }}" rx="4"/>
    <!-- ponteira -->
    <rect x="72%" y="0" width="28%" height="100%" fill="{{ belt.tip_color_hex }}" rx="0 4 4 0"/>
    <!-- listras de grau -->
    {% for filled in belt.get_grade_slots(grade) %}
    {% if filled %}
    <rect x="..." ... fill="{{ belt.stripe_color_hex }}"/>
    {% endif %}
    {% endfor %}
  </svg>
  <span class="belt-visual__label">{{ belt.display_name }}{% if grade %} · {{ grade }}º grau{% endif %}</span>
</div>
{% endif %}
{% endwith %}
```

> **Nota de implementação:** `get_grade_slots()` é um método do model. Chamar no template via `{% with slots=graduation_progress.current_belt_rank.get_grade_slots graduation_progress.current_grade_number %}` — verificar se `with` suporta chamada com argumento; se não, enriquecer o contexto na view com `belt_grade_slots = belt_rank.get_grade_slots(grade_number)`.

### 2. Card de mensalidade (billing-card) — redesenhado

Layout (por aba/person):

```
┌─────────────────────────────────────────────────────────────────┐
│ [Badge STATUS]                                      [nome do plano] │
│ Vencimento: DD/MM/AAAA    R$ 00,00/mês                            │
│                                                                   │
│ [Botão: "Trocar plano" — secundário]  [Botão: "Pagar" — primário] │
└─────────────────────────────────────────────────────────────────┘
```

Estados e seus visuais:

| Estado | Badge | Cor badge | Botão primário | Botão secundário |
|---|---|---|---|---|
| `active` | Ativo | `--success` | — | "Trocar plano" |
| `past_due` | Em atraso | `--danger` | "Pagar agora" | "Trocar plano" |
| `pending` (sem membership, com pending_order) | Pendente | `--warning` | "Ir para pagamento" | — |
| `trial` | Experimental | `--info` | — | — |
| `sem_plano` | Sem plano | `--muted` | — | — |
| `exempted` | Isento | `--success` | — | — |
| `canceled` | Cancelado | `--muted` | — | — |

Aviso de responsável financeiro diferente:
```html
{% if tab.billing_owner and tab.billing_owner != tab.person %}
<p class="billing-card__owner-note">
  Mensalidade vinculada ao responsável {{ tab.billing_owner.full_name }}.
</p>
{% endif %}
```

### 3. Lista de turmas de hoje — com check-in (student)

Cada item da lista:

```
┌──────────────────────────────────────────────────────────────────┐
│ 18:30  •  Adulto · Gi           Prof. Wagner          [Check-in] │
│         Turma Fundamental                                        │
└──────────────────────────────────────────────────────────────────┘
```

- Horário em `--brand-red`, peso 700
- Ponto separador (·) em `--muted`
- Nome da turma em `--text`, peso 600
- Professor em `--muted`, peso 400
- Botão check-in: `btn--sm btn--secondary` → POST AJAX para `system:student-checkin`
- Após check-in bem-sucedido: substituir botão por pill "Aguardando aprovação" (`--warning`)
- Se check-in já aprovado: pill "Confirmado" (`--success`)
- Se aula cancelada: riscar horário + badge "Cancelada" (`--muted`)

### 4. Ícones SVG — quick-links

Substituir emojis por ícones SVG inline. Estilo: `stroke="currentColor"`, `stroke-width="1.75"`, `fill="none"`, `width="18" height="18"`. Mesma linguagem do `register.html`.

| Módulo | Ícone SVG |
|---|---|
| Pessoas | `<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>` |
| Turmas | `<path d="M17 21v-2a4 4 0 0 0-4-4H5..."/><circle cx="9" cy="7" r="4"/>...` |
| Financeiro | `<rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/>` |
| Graduação | `<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/>` |
| Materiais | `<path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/>` |
| Planos | `<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12..."/><polyline points="14 2 14 8 20 8"/>` |
| Django Admin | `<circle cx="12" cy="12" r="3"/><path d="M19.07 4.93..."/>` (settings) |
| Horários | `<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>` |

### 5. Histórico de presença (compacto)

Exibido para student e instructor. Máximo 5 entradas. Link "Ver mais" navega para módulo (futuro).

```
HISTÓRICO DE PRESENÇA
────────────────────────────────────────────────────
20 mai · 18:30   Turma Fundamental · Prof. Wagner    ✓ Confirmado
17 mai · 18:30   Turma Fundamental · Prof. Wagner    ✓ Confirmado
...
────────────────────────────────────────────────────
[Ver histórico completo →]
```

---

## CSS — padrão de qualidade a seguir

### Shadows (padrão `register.css`)
```css
--card-shadow: 0 1px 4px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.05);
--card-shadow-dark: 0 1px 6px rgba(0,0,0,.4), 0 4px 20px rgba(0,0,0,.3);
```

### Bordas
```css
border: 1.5px solid var(--border);
border-radius: 0.875rem; /* painéis */
border-radius: 0.75rem;  /* cards menores */
border-radius: 8px;       /* botões */
```

### Hover de card com ring (padrão `register.css` profile-card)
```css
.quick-link:hover {
  border-color: var(--brand-red);
  box-shadow: 0 0 0 3px var(--brand-red-muted), var(--card-shadow);
}
```

### Transições
```css
transition: border-color 0.15s, box-shadow 0.15s, background 0.15s, transform 0.12s;
```

### Animação de entrada por seção
```css
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.section { animation: fadeSlideIn 0.35s ease both; }
.section:nth-child(2) { animation-delay: 0.05s; }
/* etc. */
```

### Background sutil (padrão `register.css`)
```css
body {
  background-image:
    radial-gradient(ellipse 60% 50% at 110% 110%, rgba(196,18,48,.05) 0%, transparent 70%),
    radial-gradient(ellipse 40% 40% at -10% -10%, rgba(196,18,48,.02) 0%, transparent 60%);
}
html[data-theme="dark"] body {
  background-image:
    radial-gradient(ellipse 70% 55% at 100% 100%, rgba(196,18,48,.14) 0%, transparent 65%),
    radial-gradient(ellipse 50% 45% at 0% 0%, rgba(196,18,48,.06) 0%, transparent 60%);
}
```

### Logo com tema
```css
.topbar__logo { filter: none; transition: filter 0.2s; }
html[data-theme="dark"] .topbar__logo { filter: invert(1); }
```

---

## JS — comportamento inline

O JS da home deve ser **mínimo e declarativo**. Seguir o padrão `register.html`:

- Dados do servidor via `<script type="application/json" id="page-data">` — nunca em `data-*` com objetos JSON
- Tema: toggle simples (já implementado)
- Abas de billing: toggle simples (já implementado)
- **Check-in (novo)**: POST AJAX com `fetch()` e CSRF do input ou cookie; atualiza apenas o botão atingido (sem reload)
- Zero dependências externas — vanilla JS puro
- Proteger com IIFE `(function() { ... })()`
- Nunca usar `innerHTML` com dados do usuário — usar `textContent` e criação de elementos

### Fluxo check-in do aluno
```
click "Check-in"
→ btn.disabled = true, btn.textContent = "Aguardando…"
→ fetch POST /aulas/checkin/ { schedule_id }
→ sucesso: substituir botão por pill "Aguardando aprovação" (badge --warning)
→ erro: btn.disabled = false, btn.textContent = "Check-in", exibir mensagem de erro inline
```

---

## Wireframe por perfil

### Aluno / Responsável / Dependente
```
TOPBAR: [Logo LV JIU JITSU]                    [☀] [⎋]
────────────────────────────────────────────────────────
Sexta-feira, 23/05/2026
Olá, Lucas 👋

GRADUAÇÃO
┌──────────────────────────────────────────────────────┐
│ [████████████████████░░░░░░░░░]  Faixa Branca · 2º  │
│ [cinturão SVG com cores reais]                       │
│ 24 aulas de 40 necessárias · 60%                     │
└──────────────────────────────────────────────────────┘

MENSALIDADE
┌──────────────────────────────────────────────────────┐
│ [ATIVO]        Plano Individual Mensal               │
│ Vencimento: 15/06/2026   R$ 150,00/mês              │
│                                           [Trocar plano →] │
└──────────────────────────────────────────────────────┘

TURMAS DE HOJE
┌──────────────────────────────────────────────────────┐
│ 18:30  ·  Fundamental · Gi   Prof. Wagner  [Check-in] │
│ 20:00  ·  Avançado · Gi      Prof. Wagner  [Confirmado] │
└──────────────────────────────────────────────────────┘

PRESENÇA RECENTE
┌──────────────────────────────────────────────────────┐
│ 20 mai · 18:30   Fundamental · Gi   ✓ Confirmado     │
│ 17 mai · 18:30   Fundamental · Gi   ✓ Confirmado     │
│                                    [Ver histórico →] │
└──────────────────────────────────────────────────────┘
```

### Admin / Administrativo
```
TOPBAR: [Logo LV JIU JITSU]                    [☀] [⎋]
────────────────────────────────────────────────────────
Sexta-feira, 23/05/2026
Olá, Wagner 👋

ACESSO RÁPIDO
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│[svg]    │ │[svg]    │ │[svg]    │ │[svg]    │
│Pessoas  │ │Turmas   │ │Financeiro│ │Graduação│
└─────────┘ └─────────┘ └─────────┘ └─────────┘
┌─────────┐ ┌─────────┐ ┌─────────┐
│[svg]    │ │[svg]    │ │[svg]    │
│Materiais│ │Planos   │ │Admin    │ ← só admin técnico
└─────────┘ └─────────┘ └─────────┘

TURMAS DE HOJE
(mesmo componente — lista compacta)

FINANCEIRO
┌──────────────────────────────────────────────────────┐
│ 💰  Módulo financeiro em breve.       [Ver módulo →] │
└──────────────────────────────────────────────────────┘
```

### Instrutor
```
TOPBAR: [Logo LV JIU JITSU]                    [☀] [⎋]
────────────────────────────────────────────────────────
Sexta-feira, 23/05/2026
Olá, Professor Wagner 👋

GRADUAÇÃO
(mesmo componente — faixa + barra de progresso)

TURMAS DE HOJE
┌──────────────────────────────────────────────────────┐
│ 18:30  ·  Fundamental · Gi                           │
│ 3 check-ins confirmados · 1 aguardando              │
│                              [Ver cronograma →]      │
│ 20:00  ·  Avançado · Gi                             │
│ 5 check-ins confirmados                              │
└──────────────────────────────────────────────────────┘

PRESENÇA RECENTE
(últimas 5 aulas com total de presenças)
```

---

## Requisitos Funcionais

### RF-01 — Correção de campos de graduação
- `graduation_progress.progress_pct` (não `percentage`)
- `graduation_progress.current_belt_rank.display_name` (não `current_belt_display`)
- `graduation_progress.approved_classes_in_window` (não `classes_count`)
- Seção só renderiza se `graduation_progress is not None` e `graduation_progress.current_belt_rank is not None`

### RF-02 — Cinturão SVG
- Renderizado server-side via template Django com dados do `BeltRank`
- Proporção: 3:1 (corpo: 72%, ponteira: 28%)
- Cores: `belt.color_hex` (corpo), `belt.tip_color_hex` (ponteira), `belt.stripe_color_hex` (listras)
- Listras: `belt.get_grade_slots(current_grade_number)` → lista de bool
- Sem biblioteca externa — SVG puro inline
- Fallback se `belt` é None: não renderiza o componente (sem erro)

### RF-03 — Card de mensalidade
- Exibe: nome do plano, status (badge), valor mensal (`plan.price`), data de vencimento (`next_billing_date`)
- Botão "Trocar plano": visível se `active_membership.status in ('active', 'exempted')`
- Botão "Pagar agora": visível se `active_membership.status == 'past_due'` ou `pending_order is not None`
- Aviso de responsável: visível se `billing_owner and billing_owner != person`
- Abas por dependente: se `billing_tabs|length > 1`

### RF-04 — Check-in (aluno)
- Botão "Check-in" por aula sem check-in
- POST AJAX para `system:student-checkin` com `schedule_id` ou `system:student-special-checkin` com `special_id`
- CSRF token via `document.cookie` ou input hidden `{% csrf_token %}` embutido inline
- Estados do botão: `default` → `loading` (disabled + "Aguardando…") → `pill-pending` | `error`
- Sem reload de página
- Se check-in já aprovado: pill verde "Confirmado"
- Se check-in pendente (já feito): pill amarela "Aguardando aprovação"

### RF-05 — Histórico de presença
- Máximo 5 entradas de `attendance_history`
- Exibido para student e instructor
- Cada entrada: data, horário, nome da turma, categoria, status
- Link "Ver histórico completo" → futura rota (pode estar desabilitado enquanto módulo não existe: `href="#"`)
- Se `attendance_history` vazio: não renderizar seção

### RF-06 — Atalhos do acesso rápido com rotas reais
| Link | Rota Django |
|---|---|
| Pessoas | `system:person-list` |
| Turmas | `system:class-group-list` |
| Horários | `system:class-schedule-list` |
| Financeiro | `system:financial-control` |
| Graduação | *(rota pendente — href="#" por ora)* |
| Materiais | `system:product-list` |
| Planos | `system:plan-list` |
| Django Admin | `/admin/` |

### RF-07 — Mensagens Django
- Renderizar `{% if messages %}` com componente visual por tag: error, success, warning, info
- Ícone SVG de info/alerta antes do texto
- Bloco posicionado após topbar, antes do cabeçalho

### RF-08 — Versão de cache dos assets
- Ao alterar `dashboard.css`, atualizar `?v=N` no template (`?v=3` na próxima entrega)
- Ao extrair JS para arquivo separado: atualizar `?v=` correspondente

---

## Requisitos Não Funcionais

### RNF-01 — Performance
- Zero bibliotecas JS externas
- Zero imagens além da logo (SVG inline para tudo)
- CSS compilado em arquivo único, sem importações encadeadas
- Nenhuma query N+1: `select_related()` / `prefetch_related()` onde necessário na view

### RNF-02 — Acessibilidade
- Todos os botões interativos com `aria-label` descritivo
- `role="status"` nos estados vazios
- `role="alert"` nos erros e mensagens do sistema
- `role="progressbar"` com `aria-valuenow`, `aria-valuemin`, `aria-valuemax` na barra de graduação
- `role="tablist"` / `role="tab"` / `role="tabpanel"` nas abas de dependente
- `:focus-visible` em todos os elementos interativos com `outline` visível
- Alvo mínimo de toque: 44×44px (WCAG 2.5.8)
- Cinturão SVG com `aria-label` descritivo (nome da faixa + grau)

### RNF-03 — Responsividade
- Mobile-first, coluna única abaixo de 640px
- Quick-access: 2 colunas mobile, 3 colunas tablet, 4 colunas desktop
- Turmas: sempre lista vertical
- Mensalidade: card full-width, badge alinhado à direita
- Cinturão SVG: `max-width: 280px`, centralizado em mobile

### RNF-04 — Tema claro e escuro
- Toda cor via token CSS — zero hardcode
- Logo: `filter: invert(1)` no dark mode (padrão `register.css`)
- `color-scheme: light` / `dark` definido no `html`
- Cinturão SVG usa `fill="{{ belt.color_hex }}"` — cores reais da faixa, sem token (correto: são cores da faixa, não da UI)

### RNF-05 — Segurança
- `innerHTML` proibido — usar `textContent` ou criação de elementos DOM
- CSRF em todos os POST (header `X-CSRFToken` via fetch)
- Dados do usuário nunca em `eval()` ou string interpolada em JS

### RNF-06 — Manutenibilidade
- CSS com tokens, sem cor solta
- Seções do template claramente comentadas com `{# ─── ... ─── #}`
- JS mínimo — preferir renderização server-side a lógica client-side
- Sem classes CSS criadas por exceção — apenas extensões dos padrões definidos

---

## Escopo

- `templates/home/dashboard.html` — reescrever
- `static/system/css/home/dashboard.css` — reescrever
- `system/views/home_views.py` — enriquecer contexto: `belt_grade_slots` se necessário
- `static/system/js/home/dashboard.js` — criar (extrair JS do template)

---

## Fora do escopo

- Criação de aulão pelo instrutor (tela de calendário)
- Aprovação de check-in de alunos pelo instrutor (tela de calendário)
- Módulo financeiro completo (PRD separado)
- Módulo de graduação completo (PRD separado)
- Sidebar/drawer global (`base.html`) — PRD separado
- Notificações em tempo real
- Gráficos ou relatórios

---

## Arquivos impactados

| Arquivo | Ação |
|---|---|
| `templates/home/dashboard.html` | reescrever |
| `static/system/css/home/dashboard.css` | reescrever (bump `?v=3`) |
| `static/system/js/home/dashboard.js` | criar (extrair JS do template) |
| `system/views/home_views.py` | enriquecer contexto se necessário |

---

## Riscos e edge cases

- **`get_grade_slots()` no template:** método com argumento — verificar se Django template engine suporta `object.method arg`; se não, enriquecer o contexto na view com `belt_grade_slots = [...]`.
- **Admin técnico sem `portal_person`:** `graduation_progress` será `None`; seção de graduação não deve renderizar.
- **`billing_tabs` vazio para admin/instructor:** não deve renderizar seção de mensalidade.
- **`today_classes` com estrutura diferente por perfil:** student recebe `get_today_classes_for_person`, instructor recebe `get_today_classes_for_instructor` — verificar campos retornados pelos dois serviços antes de usar no template.
- **Check-in duplicado:** o backend rejeita; o frontend deve lidar com 400 mostrando mensagem inline sem reload.
- **`attendance_history` com estrutura diferente por perfil:** student vs. instructor — verificar campos antes de renderizar.
- **Rota `system:class-group-list` pode não existir:** verificar em `system/urls.py` antes de referenciar no template.

---

## Regras e restrições

- SDD antes de código — implementação só começa após leitura completa dos serviços de graduação, mensalidade e calendário
- TDD — testes de rota e contexto da view antes de implementar template
- Sem hardcode de cor, perfil ou string de tipo de pessoa
- Sem migração de schema
- Sem `innerHTML` com dados do usuário
- `?v=` atualizado em todo asset alterado
- Leitura integral de `class_calendar.py` antes de implementar check-in e turmas
- Leitura integral de `membership.py` antes de implementar card de mensalidade

---

## Plano de implementação

- [ ] 1. Leitura integral
  - [ ] `system/services/class_calendar.py` — estrutura de retorno de `get_today_classes_for_person`, `get_student_checkin_history`
  - [ ] `system/services/membership.py` — campos de `Membership`, `get_active_membership`, `get_guardian_billing_tabs`
  - [ ] `system/urls.py` — confirmar rotas disponíveis para quick-links
  - [ ] Testar chamada `get_grade_slots()` no Django shell para verificar compatibilidade com template
- [ ] 2. Enriquecer contexto da view (se necessário)
  - [ ] Adicionar `belt_grade_slots` ao contexto se `get_grade_slots()` não funcionar no template
  - [ ] Verificar que `get_today_classes_for_person` retorna `schedule_id` ou `special_id` para check-in
- [ ] 3. Testes (Red)
  - [ ] Teste: `GET /home/` com aluno com membership ativa → contexto tem `billing_tabs[0].active_membership`
  - [ ] Teste: `GET /home/` com aluno sem graduation → seção de graduação ausente
  - [ ] Teste: `GET /home/` com admin → `show_staff_area=True`, `billing_tabs=[]`
- [ ] 4. Implementação (Green)
  - [ ] Reescrever `dashboard.css` com padrão `register.css`
  - [ ] Reescrever `dashboard.html` com componentes completos
  - [ ] Criar `dashboard.js` com check-in AJAX
  - [ ] Corrigir campos de graduação no template
  - [ ] Implementar cinturão SVG
  - [ ] Implementar card de mensalidade com estados
  - [ ] Implementar ícones SVG nos quick-links
  - [ ] Implementar histórico de presença
  - [ ] Preencher rotas reais nos quick-links
- [ ] 5. Refatoração
  - [ ] Verificar animação de entrada por seção
  - [ ] Verificar que nenhuma cor está fora de token
  - [ ] Verificar `aria-*` completos
- [ ] 6. Validação completa
  - [ ] `manage.py check` — 0 issues
  - [ ] `manage.py test --verbosity 2` — 0 falhas
  - [ ] Screenshot desktop tema claro
  - [ ] Screenshot desktop tema escuro
  - [ ] Screenshot mobile (375px) tema claro
  - [ ] Screenshot mobile tema escuro
  - [ ] Console do navegador sem erro
  - [ ] Terminal sem stack trace
  - [ ] Validar estado vazio de todas as seções (admin sem dados)
  - [ ] Validar estado com dados (aluno com plano ativo, faixa e turmas)
- [ ] 7. Limpeza
  - [ ] Remover JS inline do template
  - [ ] Sem artefatos temporários
- [ ] 8. Atualização documental
  - [ ] PRD-044 com evidências
  - [ ] `CLAUDE.md` Seção 13 se houver mudança relevante

---

## Critérios de aceite

### Funcionais
- [ ] Barra de graduação exibe percentual real (`progress_pct`) — verificável: screenshot com aluno com graduação
- [ ] Cinturão SVG renderiza com cores corretas do `BeltRank` — verificável: inspeção visual
- [ ] Listras de grau preenchidas corretamente segundo `grade_number` — verificável: inspeção visual
- [ ] Card de mensalidade exibe nome do plano, status badge, data de vencimento — verificável: screenshot
- [ ] Botão "Trocar plano" visível para aluno com plano ativo — verificável: screenshot + ORM check
- [ ] Botão "Pagar" visível para aluno com `pending_order` — verificável: screenshot
- [ ] Botão de check-in executa POST sem reload e atualiza status — verificável: interação no browser
- [ ] Histórico de presença exibe últimas 5 entradas para student — verificável: screenshot
- [ ] Quick-links com ícones SVG e rotas reais (não `href="#"`) — verificável: clique e inspeção
- [ ] Mensagens Django renderizadas com estilo correto — verificável: provocar mensagem de teste

### Visuais
- [ ] Hierarquia tipográfica: saudação 800, seções 700 muted uppercase, cards 700, detalhes 400 muted
- [ ] Shadows duplas nos painéis (não `box-shadow: none` ou sombra plana)
- [ ] Hover nos quick-links com ring `--brand-red-muted`
- [ ] Logo invertida em dark mode via `filter: invert(1)`
- [ ] Nenhuma cor hardcoded fora de token CSS — verificável: grep no CSS
- [ ] Animação `fadeSlideIn` nas seções — verificável: observação na recarga

### Acessibilidade
- [ ] Barra de graduação com `role="progressbar"` e `aria-valuenow` correto
- [ ] Abas de dependente com `role="tablist"`, `role="tab"`, `aria-selected`
- [ ] Botões com `aria-label` onde `textContent` não é suficiente
- [ ] Cinturão SVG com `aria-label` descritivo
- [ ] `:focus-visible` visível em todos os controles interativos

### Técnicos
- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 falhas
- [ ] `manage.py collectstatic` — sem erro
- [ ] Console do navegador — sem erro JS crítico
- [ ] Terminal do servidor — sem stack trace

---

## Evidências esperadas

- Screenshot desktop tema claro: home admin com acesso rápido + turmas vazias + financeiro stub
- Screenshot desktop tema escuro: mesma estrutura, logo invertida, cores de token corretas
- Screenshot mobile 375px: coluna única, quick-access 2 cols, cinturão compacto
- Screenshot aluno com plano ativo: card mensalidade com badge verde + botão "Trocar plano"
- Screenshot aluno com faixa: cinturão SVG com cores + barra de graduação com % real
- Output `manage.py check` — System check identified no issues
- Output `manage.py test --verbosity 2` — OK

---

## Implementado

*(a preencher após implementação)*

## Desvios do plano

*(a preencher após implementação)*

## Pendências

*(a preencher após implementação)*
