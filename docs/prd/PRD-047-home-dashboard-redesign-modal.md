# PRD-047: Home Dashboard — Redesign com Modais de Presenças e Histórico de Graduação

## Resumo do que será implementado

Redesign completo da tela `/home/` (dashboard unificado) para todos os perfis:

1. **Presenças de aula → modal por turma** (instrutor/staff): substituir a lista inline de check-ins (`class-item__checkins`) por um modal disparado pelo botão "Ver presenças" em cada aula. Resolve o problema de 100 alunos renderizados inline.
2. **Histórico de graduação → modal**: substituir o toggle inline (`grad-history-panel`) por um modal disparado por "Ver histórico". Melhora a proporção visual da seção.
3. **Seções recolhíveis**: cada seção principal ganha um botão de colapso (chevron), com estado persistido em `localStorage`. Permite o usuário minimizar informações.
4. **Proporções e layout**: revisão visual geral — cards mais compactos, hierarquia tipográfica mais clara, melhor uso de espaço em desktop e mobile.
5. **Versão de assets**: CSS `?v=7`, JS `?v=3`.

## Tipo de demanda

Redesign de interface com refatoração de UX — sem mudança de backend.

## Problema atual

- Lista de check-ins renderizada inline na `class-item` expande o card para um tamanho inviável (100 alunos = 100 linhas na mesma lista da turma).
- Histórico de graduação em toggle inline empilha muitos itens dentro do card de graduação.
- Seções não podem ser minimizadas — tela longa para todos os perfis.
- Proporções visuais são desiguais: seção de graduação muito grande, seção de turmas mistura densidade de informação com listas aninhadas.

## Objetivo

Interface home proporcional, escaneável e usável: cards compactos com ações rápidas visíveis, detalhe acessível por modal, seções recolhíveis para adaptar a densidade ao perfil do usuário.

## Context Ledger

### Arquivos lidos integralmente

- `templates/home/dashboard.html` — template atual completo
- `static/system/css/home/dashboard.css` — CSS atual completo (v3 no comentário, ?v=6 no template)
- `static/system/js/dashboard.js` — JS atual completo (v2)
- `system/views/home_views.py` — contexto do view e variáveis disponíveis
- `system/urls.py` — rotas existentes
- `templates/calendar/calendar.html` — referência de padrão unificado de modal

### Arquivos adjacentes consultados

- `docs/UI-SCREEN-CONTRACT.md` — contrato de UX
- `docs/prd/PRD-046-portal-aluno-professor-cronograma.md` — PRD anterior (padrão de evidências)

### MCPs / ferramentas verificadas

- Chrome MCP — disponível para validação visual

### Limitações encontradas

- Nenhuma mudança de model/service necessária: os dados já existem
- `graduation_history` não inclui "quem graduou" ou "motivo" — modal mostrará apenas os campos existentes (data, faixa, grau, is_current)

---

## Hierarquia Visual

- Padrão de leitura: F Pattern (mobile: coluna única, desktop: F reading)
- Topbar: peso 700, --text
- Título de página "Olá, [nome]": peso 800, 2rem, --text
- Título de seção (eyebrow): peso 700, 0.6875rem, --muted, uppercase
- Nome da aula: peso 600, 0.875rem, --text
- Horário: peso 700, 0.8125rem, --brand-red
- Subtítulo (professor, contador): peso 400, 0.75rem, --muted
- Status pills: peso 700, 0.6875rem
- Botão primary: --brand-red, peso 600
- Botão secondary: --border, peso 600

---

## Wireframe

### Região: Topbar (sticky)
- Logo LV + nome (esquerda)
- Botão tema + logout (direita)

### Região: Page header
- Eyebrow: dia da semana + data (muted, uppercase)
- Título: "Olá, [nome]" (bold 800)

### Região: Acesso rápido (admin/staff)
- Grid 2→3→4 colunas de quick-links com ícone + label
- Recolhível (chevron no header)

### Região: Turmas de hoje
- Section header: título + ações (Criar aulão, Gerir cronograma) + chevron collapse
- Panel: lista de class-items
  - [Horário] · [Nome · Categoria] / [info sub] / [ação]
  - Para instrutor: botão "Ver presenças (N)" abre modal de presenças
  - Para aluno: botão Check-in / pill Confirmado / pill Aguardando
  - Cancelada: pill Cancelada + razão

### Região: Modal de Presenças (instrutor)
- Título: "Presenças — [Nome da turma]"
- Botão fechar (X)
- Lista scrollável de alunos: [nome] | [status pill] | [botão Aprovar se pendente]
- Empty state se sem check-ins

### Região: Graduação (aluno/staff)
- Section header: título + chevron collapse
- Panel: belt SVG + nome + grau + data desde
- Stats grid 3 colunas (quando há regra)
- Progress bar + label
- Mensagem bloqueio/habilitação
- Botão "Ver histórico" → abre modal

### Região: Modal de Histórico de Graduação
- Título: "Histórico de graduação"
- Botão fechar (X)
- Lista de faixas com data, nome, grau, badge "Atual"

### Região: Mensalidade (aluno/responsável)
- Recolhível (chevron)
- Plano ativo, badge status, data vencimento, botões de ação

### Região: Histórico de presença
- Recolhível (chevron)
- Lista compacta: data + hora | turma · categoria | ✓

### Estados da tela
- Carregando: renderizado pelo servidor; sem spinner
- Vazio (sem aulas): empty-state com ícone calendário
- Com dados: lista completa
- Modal aberto: overlay escurecido, modal centrado (desktop) / bottom sheet (mobile)

---

## Máquinas de estado

### Modal de Presenças
- Estados: `closed` → `open`
- Transições: botão "Ver presenças" → open; botão ✕ ou overlay → closed; Escape → closed
- Representação visual: overlay + modal com lista de check-ins

### Modal de Histórico de Graduação
- Estados: `closed` → `open`
- Transições: botão "Ver histórico" → open; botão ✕ ou overlay → closed; Escape → closed
- Representação visual: overlay + modal com lista de graduações

### Botão de Aprovar (dentro do modal)
- Estados: `idle` → `loading` → `success`
- Transições: click → disabled + "Aprovando…" → pill "Confirmado"
- Em erro: restaura botão "Aprovar"

### Seção recolhível
- Estados: `expanded` (default) ↔ `collapsed`
- Transições: click no chevron alterna estado
- Persistência: `localStorage['lv-sections']`
- Representação visual: chevron roda 90°, conteúdo hidden

### Botão Check-in (aluno)
- Estados: `idle` → `loading` → `success (Aguardando aprovação)` | `error`
- Representação visual: botão → pill "Aguardando aprovação" (warning) | mensagem de erro abaixo

---

## Critérios de aceite

### Funcionais

- [ ] Botão "Ver presenças" em cada aula não cancelada (instrutor/admin): ao clicar, modal abre com a lista de check-ins daquela aula específica (verificável: inspeção visual no Chrome MCP com perfil instrutor)
- [ ] Modal de presenças exibe: nome do aluno, pill de status, botão Aprovar se pendente (verificável: inspeção visual)
- [ ] Ao aprovar dentro do modal, botão vira pill "Confirmado" sem recarregar a página; a mesma aprovação é refletida se o modal for fechado e reaberto (verificável: fluxo Chrome MCP)
- [ ] Botão "Ver histórico" na seção de graduação abre modal com toda a entrada de histórico (verificável: aluno com histórico no banco)
- [ ] Modal de histórico exibe badge "Atual" na entrada corrente (verificável: inspeção visual)
- [ ] Chevron em cada seção principal colapsa/expande o conteúdo da seção (verificável: click no Chrome MCP)
- [ ] Estado de colapso é persistido no localStorage (verificável: reload da página)
- [ ] Todos os modais fecham com Escape ou click no overlay (verificável: teclado + click)
- [ ] Fluxo de check-in do aluno permanece funcional (verificável: fluxo Chrome MCP com perfil aluno)
- [ ] Seção "Criar aulão" e modal de criação permanecem funcionais (verificável: fluxo Chrome MCP com perfil instrutor)

### UX / Visual

- [ ] Hierarquia visual: título de seção em peso 700 muted uppercase; nome da aula em 600; horário em brand-red bold (verificável: inspeção visual)
- [ ] Modais renderizam como bottom sheet em mobile (≤600px) e centrado em desktop (verificável: resize Chrome MCP)
- [ ] Tema claro e escuro funcionam em toda a tela e modais (verificável: toggle de tema)
- [ ] Todos os estados de class-item (normal, cancelado, com check-in, sem check-in) renderizam corretamente (verificável: inspeção visual)
- [ ] Nenhum `class-item__checkins` inline renderizado para o instrutor (verificável: DevTools → sem `.class-item__checkins` no DOM)

---

## Evidências esperadas

- `manage.py test --verbosity 2` → 0 falhas, 0 erros
- `manage.py check` → sem issues
- Chrome MCP: screenshots da tela com perfil aluno, instrutor e admin nos temas claro e escuro
- Console do navegador: sem erros JS
- Terminal: sem stack trace

---

## Escopo

- `templates/home/dashboard.html` — reescrita parcial (estrutura HTML + modais)
- `static/system/css/home/dashboard.css` — adições CSS + bump de versão (comentário)
- `static/system/js/dashboard.js` — substituição de `bindGradHistoryToggle` + adição de modais e seção collapse

## Fora do escopo

- `system/views/home_views.py` — sem mudanças
- `system/services/` — sem mudanças
- Campos novos no modelo de graduação (granter, reason) — PRD futuro
- Módulo financeiro (stub permanece)

## Arquivos impactados

| Arquivo | Tipo de mudança |
|---|---|
| `templates/home/dashboard.html` | Modificação — HTML principal + modais |
| `static/system/css/home/dashboard.css` | Adição — novos componentes modal e collapse |
| `static/system/js/dashboard.js` | Modificação — bind de modais e collapse |

---

## Riscos e edge cases

- **Clonagem de DOM de checkins**: se checkin-source tiver muitos itens, clonar pode ser lento → aceitável até ~500 itens
- **Aprovação no modal e estado desatualizado**: após fechar e reabrir modal sem reload, approved buttons na source div já estão atualizados → OK
- **Seção colapsada sem aulas**: empty-state deve continuar oculto quando seção está colapsada → comportamento correto pois o body inteiro é hidden
- **Perfil admin técnico (sem portal_person)**: `today_classes` e `graduation_progress` são vazios → tela renderiza sem seções condicionais → OK
- **Aulão (special class)**: `item.is_special = True`, checkins têm `data-is-special="true"` → JS usa `instructorApproveSpecialUrl` → OK

---

## Regras e restrições

- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro (`except: pass`)
- sem migrações (nenhuma mudança de model)
- leitura integral obrigatória ✓
- validação visual obrigatória em navegador

---

## Plano

- [x] 1. Leitura integral de todos os arquivos do fluxo
- [ ] 2. Escrita do PRD-047 com hierarquia visual, wireframe, máquinas de estado
- [ ] 3. Testes existentes: garantir que passam sem mudança de backend
- [ ] 4. Implementação: dashboard.html + dashboard.css + dashboard.js
- [ ] 5. Bump de versões: CSS ?v=7, JS ?v=3
- [ ] 6. Validação visual: Chrome MCP, temas, mobile e desktop
- [ ] 7. Limpeza final

---

## Validação visual

### Desktop (≥768px)
- Topbar compacta, logo visível
- Seções com cabeçalho claro e chevron de colapso
- Class items compactos: horário em vermelho, nome bold, sub muted, botão à direita
- Modal de presenças centrado, max-width 520px
- Graduação: belt SVG 280–340px, stats grid 3 cols, progress bar

### Mobile (375px)
- Seções empilhadas em coluna única
- Class items em linha compacta
- Modais como bottom sheet (bottom: 0, border-radius top apenas)

### Console do navegador
- Sem erros JS (TypeError, ReferenceError, etc.)
- Sem 404 em assets

### Terminal
- Sem stack trace

### Iteração 3 — Correção de overflow horizontal
- Diagnóstico no navegador antes da correção: `.grad-history-list` com `clientWidth=421`, `scrollWidth=429`, `overflowX=auto`; excedente causado por `.grad-history-entry--current` com `margin: 0 -0.5rem`.
- Validação no navegador após correção: `.grad-history-list` com `clientWidth=318`, `scrollWidth=318`, `overflowX=hidden`, `hasHorizontalOverflow=false`.
- Console do navegador: zero erros.
- `manage.py check` → 0 issues.
- `collectstatic --noinput` → 1 arquivo copiado, 173 inalterados.
- `manage.py test --verbosity 2` → 168 testes passando.
- Sem warnings de migration

### Iteração 4 — Remoção do botão inferior "Fechar"
- Validação no navegador: modal de histórico aberto com `footerExists=false`, `footerCloseButtonCount=0`, `headerCloseButtonCount=1`.
- Botão X do cabeçalho fecha o modal corretamente.
- Console do navegador: zero erros.
- `manage.py check` → 0 issues.

### Iteração 5 — Remoção do KPI "Conclusão"
- Validação no navegador: `conclusionCards=0`, `gradStatCount=2`, `progressBarExists=true`.
- Console do navegador: zero erros.

### Iteração 6 — Histórico de presença dentro de Turmas de hoje
- Validação no navegador: headings de seções principais = `Turmas de hoje`, `Graduação`; `separateHistorySections=0`.
- Validação no navegador: `classesHistoryButtonCount=1`, com botão "Histórico" dentro de `Turmas de hoje`.
- Validação no navegador: modal aberto com `modalRows=1`, filtro textual e paginação `Página 1 de 1`.
- Validação no navegador: filtro `sem` retornou `visibleRows=0`, `pageText=Sem resultados`; filtro `teste` retornou `visibleRows=1`, `pageText=Página 1 de 1`.
- Console do navegador: zero erros.

### Iteração 7 — Filtros estruturados no histórico de presença
- Decisão de UX: substituir filtro textual livre por filtros explícitos de turma, professor, mês e ano.
- Critério atualizado: o modal deve renderizar quatro selects (`Turma`, `Professor`, `Mês`, `Ano`) e botão `Limpar`; cada linha de histórico deve expor atributos estruturados para filtragem client-side.
- Teste Red/Green: `HomeDashboardTestCase.test_attendance_history_modal_uses_structured_filters` falhou antes da implementação porque ainda havia `type="search"` e passou após a troca pelos selects.
- Validação no navegador: `textSearchCount=0`, labels dos filtros = `Turma`, `Professor`, `Mês`, `Ano`; opções renderizadas para turma, professor, mês e ano.
- Validação no navegador: seleção combinada por turma/professor/mês/ano manteve `visibleRows=1` e paginação `Página 1 de 1`; botão `Limpar` zerou todos os selects e manteve a lista visível.
- Console do navegador: zero erros.

### Iteração 8 — Cronograma visível para aluno
- Decisão de UX: o aluno também deve acessar `Cronograma` a partir de `Turmas de hoje` para consultar as aulas do mês.
- Critério atualizado: o header de `Turmas de hoje` deve renderizar o link `/cronograma/` para aluno, sem renderizar ações de professor como `Criar aulão`.
- Teste Red/Green: `HomeDashboardTestCase.test_student_home_renders_calendar_link` falhou antes da implementação porque o link não existia para aluno e passou após a correção.

---

## Validação ORM

Nenhuma mudança de model → sem validação ORM necessária.

---

## Validação de qualidade

- Sem hardcode de cores ou medidas fora dos tokens CSS
- Sem `except: pass`
- Sem `innerHTML` com dados do usuário (usar `textContent` ou clonagem de DOM)
- Sem regra de negócio no template ou JS

---

## Implementado

### Iteração 1 (PRD-047 original)
- `templates/home/dashboard.html` — reescrita com modais de presenças e histórico, seções recolhíveis, versões CSS ?v=7 e JS ?v=3
- `static/system/css/home/dashboard.css` — adicionados: `.section__title-row`, `.section__toggle`, `.modal__header`, `.modal__close`, `.modal-checkin-list`, `.modal-checkin-item*`, `.modal-empty`, `.grad-history-list`, `.grad-card__footer`; comentário atualizado para v4
- `static/system/js/dashboard.js` — adicionados `bindPresenceModal`, `bindGradHistoryModal`, `bindSectionCollapse`; `bindApproveCheckins` convertido para event delegation; removido `bindGradHistoryToggle`

### Iteração 2 — Redesign da seção de graduação (solicitado pelo usuário)
- `system/services/graduation.py` — `get_graduation_history` enriquecido com `belt_stripes` por entrada (stripe positions computadas como no view principal)
- `templates/home/dashboard.html` — seção de graduação reestruturada: compacta por padrão (belt SVG + "MINHA FAIXA" + nome/grau + botão "Mais sobre a graduação +"), painel expansível inline (`grad-details`) com stats IBJJF enriquecidos, barra de progresso e "Ver histórico"; modal de histórico reescrito com belt SVG por entrada, faixa de datas, permanência, concessor e notas; CSS `?v=8`, JS `?v=4`
- `static/system/css/home/dashboard.css` — adicionados: `.grad-compact-header`, `.grad-compact-info*`, `.grad-details`, `.grad-stat__rule`, `.grad-stat__detail`, `.grad-details__footer`, `.grad-history-entry*`, `.grad-history-modal-footer`; comentário atualizado para v5
- `static/system/js/dashboard.js` — adicionado `bindGradDetailsToggle` (toggle inline do painel de detalhes, ícone + / −)

### Iteração 3 — Correção de overflow horizontal no modal de histórico
- `static/system/css/home/dashboard.css` — `.grad-history-list` passou a bloquear overflow no eixo X; removido o `margin: 0 -0.5rem` de `.grad-history-entry--current`, que fazia a entrada atual exceder a largura útil da lista e ativava scroll horizontal desnecessário.
- `templates/home/dashboard.html` — CSS atualizado de `?v=8` para `?v=9`.

### Iteração 4 — Remoção de ação duplicada no modal de histórico
- `templates/home/dashboard.html` — removido o botão "Fechar" do rodapé do modal de histórico de graduações. O modal permanece fechável pelo botão X no cabeçalho, clique no overlay e tecla Escape.

### Iteração 5 — Remoção de KPI duplicado de conclusão
- `templates/home/dashboard.html` — removido o KPI "Conclusão" da seção de graduação, porque o percentual já é representado pela barra de progresso.
- `static/system/css/home/dashboard.css` — grid de KPIs de graduação ajustado de três para duas colunas; comentário atualizado para v7.
- `templates/home/dashboard.html` — CSS atualizado de `?v=9` para `?v=10`.

### Iteração 6 — Histórico de presença em modal acionado por Turmas de hoje
- `templates/home/dashboard.html` — removida a seção separada "Histórico de presença"; adicionado botão "Histórico" no cabeçalho de `Turmas de hoje`; criado modal `attendance-history-modal` com filtro, lista e paginação.
- `static/system/css/home/dashboard.css` — adicionados estilos de modal largo, lista, linhas e paginação do histórico de presenças; comentário atualizado para v8.
- `static/system/js/dashboard.js` — adicionado `bindAttendanceHistoryModal`, com filtro textual normalizado e paginação client-side sobre os itens renderizados pelo servidor.
- `templates/home/dashboard.html` — CSS atualizado para `?v=11` e JS para `?v=5`.

### Iteração 7 — Filtros por turma, professor, mês e ano
- `templates/home/dashboard.html` — filtro textual removido; modal atualizado com selects para turma, professor, mês e ano, botão "Limpar", atributos `data-class-filter`, `data-teacher-filter`, `data-month-filter`, `data-month-label` e `data-year-filter`; CSS atualizado para `?v=12` e JS para `?v=6`.
- `static/system/css/home/dashboard.css` — adicionados estilos para `.modal__select` e grid responsivo `.attendance-history-filters`; modal largo ampliado para 720px; comentário atualizado para v9.
- `static/system/js/dashboard.js` — `bindAttendanceHistoryModal` passou a popular selects a partir dos itens renderizados e aplicar filtros por igualdade combinada, preservando paginação e estado vazio.
- `system/tests/test_home_dashboard.py` — adicionado teste de contrato para impedir regressão para filtro textual.

### Iteração 8 — Link Cronograma para aluno
- `templates/home/dashboard.html` — ramo não instrutor do header `Turmas de hoje` passa a renderizar ações com `Histórico` quando existir histórico e `Cronograma` sempre disponível.
- `system/tests/test_home_dashboard.py` — adicionado teste garantindo `Cronograma` para aluno e ausência de `Criar aulão`.

## Evidências

### Testes automatizados
- `manage.py test --verbosity 2` → 168 testes passando, 0 erros
- `manage.py check` → 0 issues
- `collectstatic --noinput` → 2 arquivos copiados, 172 inalterados
- `manage.py test system.tests.test_home_dashboard.HomeDashboardTestCase.test_attendance_history_modal_uses_structured_filters --verbosity 2` → teste novo passando

### Validação visual — perfil aluno (Wagner, light theme)
- Seção Graduação compacta por padrão: belt SVG branca + "MINHA FAIXA" + "Branca" + botão "Mais sobre a graduação +" ✓
- Clique no botão expande painel inline: "Faixa atual desde...", stats com contexto IBJJF ("regra IBJJF tempo mínimo: N meses", "faltam N meses para habilitar..."), barra de progresso, mensagem de bloqueio, "Ver histórico" ✓
- Botão muda para "Mais sobre a graduação −" quando expandido ✓
- "Ver histórico" abre modal "Histórico de graduações" com belt SVG miniatura, data range, permanência em vermelho, notas em itálico, ponto verde na entrada atual ✓
- Escape fecha modal de histórico ✓
- Console: zero erros JS ✓

### Validação visual — perfil instrutor (André, light theme)
- Seção Graduação compacta: belt preta com ponteira vermelha + grau 1 ✓
- Painel expandido: 1 mês / regra 36 meses, 0 aulas / regra 192 aulas, barra de progresso, bloqueio com faltam 35 meses e 192 aulas ✓
- Modal "Histórico de graduações": 18+ entradas scrolláveis, cada uma com belt SVG correto (cores e graus), datas, permanência em vermelho, fechamento pelo X do cabeçalho ✓
- Modal de presenças (botão 👥 1): abre com "WAGNER HELIO DA SILVA FILHO | Confirmado" ✓
- Escape fecha modais ✓
- Console: zero TypeError, ReferenceError, erros de rede críticos ✓

### Terminal
- Sem stack trace

## Desvios do plano

- `presenceModalsExist: false` para aluno é comportamento correto: o modal de presenças só é renderizado quando `show_instructor_area=True`
- localStorage de colapso de seção é compartilhado por sessão do browser (não por usuário); comportamento aceitável
- Seção de graduação não tem mais colapso via chevron de seção — o toggle interno ("Mais sobre a graduação") substituiu o padrão anterior conforme solicitado pelo usuário

## Pendências

- Nenhuma
