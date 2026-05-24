# PRD-046: Portal Aluno e Professor — Graduação Enriquecida + Gestão de Cronograma no Dashboard

## Resumo do que será implementado

Enriquecimento da seção de graduação no dashboard para todos os perfis com dados de progressão detalhados (tempo na faixa, aulas aprovadas, % de conclusão, mensagem de bloqueio/habilitação, histórico recolhível). Adição de gestão de check-ins para professores na seção "Turmas de hoje": lista de alunos por aula com botão de aprovação, contagem de confirmados/pendentes, botão "Criar aulão" com modal inline, link "Gerir cronograma" para tela de calendário. Registro das rotas de ação do professor que já existem no código mas não estão mapeadas em `urls.py`. Criação das templates de calendário (`instructor_calendar.html` e `student_schedule.html`).

## Tipo de demanda

Nova feature + enriquecimento de tela existente

## Problema atual

1. Seção de graduação no dashboard mostra apenas faixa, grau e barra de progresso — sem data de graduação, sem detalhamento de meses na faixa vs. mínimo exigido, sem contagem de aulas aprovadas vs. exigidas, sem mensagem de habilitação/bloqueio, sem histórico.
2. A seção "Turmas de hoje" para professores exibe apenas o count de confirmados por aula — sem listagem de alunos, sem botão de aprovação de check-in, sem "Criar aulão", sem link para o cronograma.
3. As views de ação do professor (`InstructorApproveCheckinView`, `InstructorApproveSpecialCheckinView`, `InstructorSpecialClassCreateView`, `InstructorToggleSessionView`, etc.) existem mas suas rotas não estão registradas em `system/urls.py` — tornando-as inacessíveis.
4. Os templates `calendar/instructor_calendar.html` e `calendar/student_schedule.html` são referenciados pelas views mas não existem — causariam 500 em produção se as rotas fossem ativadas.

## Objetivo

- Alunos veem no dashboard: tempo na faixa atual, aulas aprovadas vs. mínimo, % conclusão, mensagem clara de habilitação ou bloqueio específico, histórico expansível.
- Professores/instrutores veem no dashboard: por aula, lista de alunos com status de check-in e botão "Aprovar"; botão "Criar aulão" com modal funcional; link "Gerir cronograma".
- Todas as rotas de ação do professor registradas e funcionais.
- Templates de calendário criados e funcionais (mensal, navegável, com ações de instructor).

## Context Ledger

### Arquivos lidos integralmente

- `system/views/home_views.py` — contexto do dashboard; graduation_progress, belt_rank, belt_stripes, billing_tabs
- `system/services/graduation.py` — compute_graduation_progress retorna SimpleNamespace completo com applicable_rule, current_graduation_date, months_in_current_grade, required_months, months_remaining, approved_classes_in_window, required_classes, missing_classes, is_eligible, progress_pct, blocker; get_graduation_history retorna lista de entries com belt_rank, grade_number, awarded_at, period_months, is_current
- `system/services/class_calendar.py` — get_today_classes_for_instructor retorna entries com checkins[], approved_count, pending_count; get_today_classes_for_person; approve_class_checkin; approve_special_checkin; create_special_class; toggle_session_cancel
- `system/views/calendar_views.py` — InstructorApproveCheckinView, InstructorApproveSpecialCheckinView, InstructorSpecialClassCreateView, InstructorSpecialClassDeleteView, InstructorToggleSessionView, InstructorCalendarView, StudentScheduleView — todas existem e não têm rota
- `system/urls.py` — apenas student-checkin e student-special-checkin estão registrados; rotas de instructor ausentes
- `templates/home/dashboard.html` — template atual; seção graduação com grad-card; seção classes com class-item
- `static/system/css/home/dashboard.css` — tokens, componentes; versão atual v5
- `static/system/js/dashboard.js` — bindCheckins (student), bindTabs, bindThemeToggle; v1

### Arquivos adjacentes consultados

- `system/models/calendar.py` — ClassCheckin, SpecialClassCheckin, CheckinStatus, ClassSession
- `system/forms/class_forms.py` — SpecialClassForm

### Internet / documentação oficial

- N/A — implementação pura em Django/JS/CSS sem novas dependências

### MCPs / ferramentas verificadas

- Chrome MCP — será usado na validação visual
- `.venv` Python — ambiente local Windows + PowerShell

### Limitações encontradas

- `templates/calendar/` não existe; é necessário criar a pasta (justificativa: views já referem esses caminhos e sem o template produzem 500)
- CLAUDE.md seção 12 proíbe criar pastas ad-hoc em redesigns; esta criação é justificada por PRD e por ser nova funcionalidade (não redesign)

---

## Hierarquia Visual

- Padrão de leitura: F Pattern (seções empilhadas mobile, skim horizontal desktop)
- Título de seção (GRADUAÇÃO, TURMAS DE HOJE): peso 700, `--muted`, uppercase 0.69rem
- Nome da faixa: peso 700, `--text`, 1rem
- Stats (valor): peso 700, `--text`, 1rem
- Stats (label): peso 600, `--muted`, 0.625rem uppercase
- Stats (sub): peso 400, `--muted`, 0.6875rem
- Mensagem bloqueio: peso 500, `--warning`, background `--warning-muted`
- Mensagem elegível: peso 500, `--success`, background `--success-muted`
- Nome de aluno no check-in: peso 500, `--text`, 0.8125rem
- Botão Aprovar: `btn--primary btn--sm` (brand-red)

## Wireframe

### Seção Graduação (com applicable_rule)

```
[Belt SVG ─────────────────────────────────────────────]
[Faixa: Nome] [Xº grau]
Faixa atual desde DD/MM/AAAA

[NA FAIXA      ] [AULAS APROVADAS] [CONCLUSÃO   ]
[X meses       ] [X              ] [X%          ]
[mín. Y meses  ] [mín. Y aulas   ] [               ]
[faltam Z      ] [faltam Z       ] [               ]

PRÓXIMO GRAU                                      X%
[████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░]

[Faltam X meses e Y aulas para habilitar a próxima... ]   ← blocker
OU
[✓ Habilitado para a próxima graduação.               ]   ← eligible

[Ver histórico ▼]
  [mm/AAAA] [Faixa, Grau] [Atual?]
```

### Seção Turmas de Hoje (professor)

```
TURMAS DE HOJE            [Criar aulão] [Gerir cronograma]

[19:00 · Adulto — Prof. Preview · 3 confirmados · 1 pendente ]
  [Aluno A ─────────────────────── Confirmado               ]
  [Aluno B ─────────────────────── Aguardando  [Aprovar]    ]

[—— vazio ——]
```

### Modal Criar Aulão

```
╔════════════════════════════════╗
║  Criar aulão                   ║
║  Título    [_________________] ║
║  Data      [_________________] ║
║  Horário   [_________________] ║
║  Duração   [_________________] ║
║  [Erro]                        ║
║              [Cancelar] [Criar]║
╚════════════════════════════════╝
```

### Estados da tela

- Botão "Aprovar": idle → loading (disabled + "Aprovando…") → success (pill "Confirmado") | erro (volta idle)
- Modal: hidden → aberto (slide-up) → loading (submit disabled) → fechado (reload)
- Histórico: recolhido → expandido (chevron rotaciona)

## Máquinas de estado

### Botão Aprovar Check-in

- Estados: idle, loading, success, error
- Transições: idle → click → loading → resposta OK → success; resposta NOK → error → idle
- Representação visual: idle = btn--primary "Aprovar"; loading = disabled "Aprovando…"; success = status-pill--success "Confirmado"; error = volta idle com mensagem

### Modal Criar Aulão

- Estados: hidden, open, submitting, closed
- Transições: click "Criar aulão" → open; click overlay/esc → hidden; submit → submitting → closed (reload) | error → open
- Representação visual: hidden = [hidden]; open = overlay + slide-up; submitting = submit disabled

### Toggle Histórico de Graduação

- Estados: collapsed, expanded
- Transições: click → toggle; aria-expanded reflete estado
- Representação visual: collapsed = chevron normal; expanded = chevron rotacionado 180º

---

## Escopo

1. `system/urls.py` — registrar rotas instructor (approve, approve-special, toggle-session, special-create, special-delete) e calendar (instructor-calendar, instructor-calendar-month, student-schedule, student-schedule-month)
2. `templates/home/dashboard.html` — seção graduação enriquecida; seção turmas de hoje para professor com lista de alunos + botão Aprovar + botão Criar Aulão + link Gerir cronograma; modal criar aulão; home-config JSON atualizado
3. `static/system/css/home/dashboard.css` — v6: .grad-awarded, .grad-stats, .grad-stat, .grad-message, .grad-history-toggle, .grad-history-panel, .grad-history-item, .class-item__checkins, .checkin-row, .section__actions, .modal-overlay, .modal e filhos
4. `static/system/js/dashboard.js` — v2: bindApproveCheckins, bindSpecialClassModal, bindGradHistoryToggle
5. `templates/calendar/instructor_calendar.html` — nova (criação de pasta justificada por PRD)
6. `templates/calendar/student_schedule.html` — nova

## Fora do escopo

- Cancelar aula do cronograma via dashboard (botão no calendar, não no dashboard)
- Aprovar cancelamento de sessão via dashboard
- Funcionalidade CRUD completa de horários no calendário
- Histórico de presença do aluno no dashboard (já existe)
- Módulo financeiro do professor (stub existente)
- Criação de novas rotas administrativas de calendário

## Arquivos impactados

| Arquivo | Tipo de mudança |
|---|---|
| `system/urls.py` | Adição de rotas |
| `templates/home/dashboard.html` | Edição de seções existentes + modal |
| `static/system/css/home/dashboard.css` | Adição de estilos (v5→v6) |
| `static/system/js/dashboard.js` | Adição de funções (v1→v2) |
| `templates/calendar/instructor_calendar.html` | Criação |
| `templates/calendar/student_schedule.html` | Criação |

## Riscos e edge cases

- `graduation_progress.applicable_rule` pode ser None → não mostrar stats grid nesses casos
- `graduation_progress.current_graduation_date` pode ser None (legacy sem data) → omitir a linha de data
- Instructor sem turmas hoje → empty state existente funciona
- Aulão criado mesmo dia → schedule_id não existe (is_special=True) → checkin_kind="special"
- Check-in já aprovado antes do clique → servidor retorna sucesso mas is_approved já é true → idempotente
- Pessoa sem belt_rank → seção de graduação mostra empty state

## Regras e restrições

- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória via Chrome MCP
- `?v=` atualizado no template ao alterar CSS e JS

## Plano

- [x] 1. Contexto e leitura integral (concluído acima)
- [ ] 2. Registrar rotas em system/urls.py
- [ ] 3. Atualizar dashboard.css (v6)
- [ ] 4. Atualizar dashboard.js (v2)
- [ ] 5. Atualizar dashboard.html (graduação + professor + modal + config)
- [ ] 6. Criar templates/calendar/instructor_calendar.html
- [ ] 7. Criar templates/calendar/student_schedule.html
- [ ] 8. manage.py check + manage.py test
- [ ] 9. Validação visual Chrome MCP
- [ ] 10. Limpeza e atualização documental

## Critérios de aceite

- [ ] Dashboard aluno: exibe "Faixa atual desde DD/MM/AAAA" quando current_graduation_date não é None (verificável: visual)
- [ ] Dashboard aluno: exibe grid 3 colunas com "NA FAIXA / X meses / mín. Y", "AULAS APROVADAS / X / mín. Y", "CONCLUSÃO / X%" quando applicable_rule não é None (verificável: visual)
- [ ] Dashboard aluno: exibe mensagem de bloqueio com texto dos campos bloqueantes quando not is_eligible (verificável: visual)
- [ ] Dashboard aluno: exibe mensagem verde "Habilitado para a próxima graduação" quando is_eligible (verificável: visual)
- [ ] Dashboard aluno: botão "Ver histórico" expandem/recolhem lista de graduações com chevron rotacionando (verificável: visual + clique)
- [ ] Dashboard professor: seção "Turmas de hoje" tem botões "Criar aulão" e "Gerir cronograma" no header (verificável: visual)
- [ ] Dashboard professor: cada aula mostra lista de alunos com status-pill e botão "Aprovar" para pendentes (verificável: visual)
- [ ] Dashboard professor: clique em "Aprovar" faz POST para instructor-approve-checkin ou instructor-approve-special-checkin com checkin_id; em sucesso substitui waiting pill + botão por "Confirmado" (verificável: visual + network)
- [ ] Dashboard professor: clique em "Criar aulão" abre modal; submit com dados válidos cria special class e recarrega; submit inválido exibe erro no modal (verificável: visual + network)
- [ ] Link "Gerir cronograma" navega para /cronograma/ (instructor-calendar) sem 404 (verificável: navegação)
- [ ] GET /cronograma/ retorna 200 para instructor (verificável: navegação)
- [ ] GET /cronograma/alunos/ retorna 200 para student (verificável: navegação)
- [ ] manage.py check: 0 issues (verificável: terminal)
- [ ] manage.py test: 0 falhas, 0 erros (verificável: terminal)
- [ ] Console do navegador: sem erros JS (verificável: DevTools)

## Evidências esperadas

- manage.py check 0 issues
- manage.py test 0 falhas
- Screenshot do dashboard do aluno com stats de graduação
- Screenshot do dashboard do professor com lista de alunos e botão Aprovar
- Screenshot do modal "Criar aulão"
- Screenshot das páginas de calendário (/cronograma/, /cronograma/alunos/)
- Console do navegador limpo

---

## Validação visual

### Desktop
- Seção graduação: grid 3 colunas visíveis, mensagem de bloqueio abaixo da barra
- Seção turmas professor: checkin rows com pill + botão alinhados à direita
- Modal: centralizado na tela, max-width 480px

### Mobile
- Seção graduação: grid 3 colunas em 375px (fontes menores mas legível)
- Checkin rows: nome truncado mas botão Aprovar visível
- Modal: ocupa largura total, bordas arredondadas no topo

### Console do navegador
- 0 erros JS

### Terminal
- 0 stack traces no servidor

## Validação ORM

### Shell checks

```python
# Verify graduation_progress data
from system.services.graduation import compute_graduation_progress
from system.models import Person
p = Person.objects.first()
gp = compute_graduation_progress(p)
print(gp.current_graduation_date, gp.months_in_current_grade, gp.required_months, gp.is_eligible)
```

## Validação de qualidade

### Sem hardcode
- URLs de API lidas do JSON config, nunca hardcoded no JS

### Sem estruturas condicionais quebradiças
- JS usa guard clauses; template usa `{% if %}` direto sem lógica de negócio

### Sem `except: pass`
- JS usa `.catch` com log/estado de erro; Python views já têm tratamento adequado

### Sem mascaramento de erro
- Erros de approve-checkin voltam para idle com botão reativado

### Sem comentários desnecessários
- Código auto-explicativo

---

## Evidências

### Iteração 2 — Responsividade do cronograma
- Decisão de UX: `/cronograma/` deve ter largura própria em desktop, sem ficar limitado ao `max-width` da home; em mobile, a grade mensal deve virar uma lista de dias legível.
- Decisão de interação: clicar/tocar em qualquer dia abre um modal com as informações completas daquele dia.
- Teste Red/Green: `CalendarServiceTestCase.test_calendar_page_renders_responsive_day_detail_contract` falhou antes da implementação porque o template ainda usava a estrutura antiga e passou após a inclusão de `page--calendar`, `calendar-board`, `cal-grid--days`, botões de dia e modal `calendar-day-modal`.
- `system/services/class_calendar.py`: `weekday` passou a usar `date_format(..., "D")` para manter rótulos de dia localizados em pt-BR.
- Validação mobile no navegador (375px): `pageWidth=360`, `gridWidth=332`, `bodyOverflow=false`, 31 botões de dia, modal de detalhe abriu com título `1 de Maio de 2026` e lista completa de aulas/cancelamentos.
- Validação desktop no navegador (2560px): `pageWidth=1720`, `gridWidth=1680`, colunas de ~235px, dias com ~174px de altura, `bodyOverflow=false`.

### Testes automatizados
- `manage.py test --verbosity 2` → **168 testes, 0 falhas, 0 erros** (5.07s)
- `manage.py check` → **System check identified no issues (0 silenced)**
- `manage.py collectstatic --noinput` → **174 static files collected**

### Validação visual — Desktop (Chrome MCP, 127.0.0.1:8000)

**Admin / Usuário com `show_instructor_area`:**
- Dashboard mostra "Criar aulão" + "Gerir cronograma" na header de TURMAS DE HOJE ✅
- Modal "Criar aulão": abre ao clicar no botão, fecha com Escape e botão Cancelar, contém campos Título / Data (pré-preenchida com hoje) / Horário / Duração ✅
- Navegação `/cronograma/` renderiza calendário mensal completo (Maio 2026) com pills de classes ✅
- Pills de turmas do professor (owned) em azul; pills de aulão em vermelho; pills canceladas em strikethrough ✅
- Legenda: "Minhas turmas" (azul) / "★ Aulão" (vermelho) / "Cancelada" ✅
- Botão "Criar aulão" presente no header do calendário ✅

**Professor (Layon Quirino Vidal — Preta 1º grau, CPF 920.000.000-01):**
- Dashboard: greeting "Olá, Layon ..." ✅
- TURMAS DE HOJE: "Criar aulão" + "Gerir cronograma" visíveis ✅
- Seção GRADUAÇÃO: faixa Preta 1º grau com visual correto (faixa preta + divisor branco + stripe vermelho) ✅
- "Faixa atual desde 10/10/2023" ✅
- Stats: NA FAIXA 31 meses (mín. 36 · faltam 5) / AULAS APROVADAS 0 (mín. 192 · faltam 192) / CONCLUSÃO 43% ✅
- Barra de progresso "Próximo grau" em 43% ✅
- Mensagem de bloqueio amber: "Faltam 5 meses na faixa e 192 aulas aprovadas para habilitar a próxima graduação." ✅
- "Ver histórico" toggle presente ✅
- Link "Gerir cronograma" navega para `/cronograma/` com pills owned em azul ✅

**Aluno (WAGNER HELIO — Branca, CPF 014.337.401-09):**
- Dashboard: greeting "Olá, WAGNER ..." ✅
- TURMAS DE HOJE: sem botões de instrutor (apenas link para cronograma não aparece) ✅
- Seção GRADUAÇÃO: faixa Branca com visual correto ✅
- "Faixa atual desde 24/05/2026" ✅
- Stats: NA FAIXA 0 meses (mín. 4 · faltam 4) / AULAS APROVADAS 0 (mín. 32 · faltam 32) / CONCLUSÃO 0% ✅
- Barra de progresso em 0% ✅
- Mensagem de bloqueio amber: "Faltam 4 meses na faixa e 32 aulas aprovadas para habilitar a próxima graduação." ✅
- "Ver histórico" toggle: expande e mostra "05/2026 | Branca | Atual" com chevron rotacionando ✅
- MENSALIDADE: badge "ATIVO" + nome do plano + data de vencimento ✅

**Cronograma do aluno (`/cronograma/alunos/`):**
- Renderiza calendário mensal read-only ✅
- Sem botão "Criar aulão" ✅
- Legenda: "Aula regular" / "★ Aulão" / "Cancelada" ✅

### Console do navegador
- Zero erros de aplicação ✅
- Apenas 5 exceptions de extensão do Chrome ("message channel closed before response") — não relacionados ao app ✅

### Terminal
- Zero stack traces durante toda a validação ✅

## Implementado

- `system/urls.py`: 9 novas rotas registradas para views de calendário/checkin que já existiam mas estavam sem URL
- `static/system/css/home/dashboard.css` (v5→v6): CSS para `grad-awarded`, `grad-stats`, `grad-message`, `grad-history-*`, modal, `checkin-row`, `cal-*`, `section__actions`
- `static/system/js/dashboard.js` (v1→v2): `bindApproveCheckins()`, `bindSpecialClassModal()`, `bindGradHistoryToggle()`
- `templates/home/dashboard.html`: seção de graduação enriquecida, checkins de instrutor, modal "Criar aulão", atualização do `home-config` JSON
- `templates/calendar/instructor_calendar.html`: criado (nova pasta `templates/calendar/`)
- `templates/calendar/student_schedule.html`: criado
- `templates/calendar/calendar.html`: atualizado para layout responsivo próprio do cronograma, com detalhe de dia em modal
- `static/system/css/home/dashboard.css`: adicionados estilos responsivos para `.page--calendar`, `.calendar-board`, `.cal-grid--days`, `.cal-day__button`, lista mobile e modal de detalhes do dia
- `system/tests/test_calendar.py`: adicionado teste de contrato do layout responsivo do cronograma

## Desvios do plano

- Pasta `templates/calendar/` foi criada apesar da regra geral de "não criar novas pastas" — necessária e justificada no PRD pois as views já referenciavam esses templates
- Modal "Criar aulão" no `instructor_calendar.html` foi implementado com JS inline (não no `dashboard.js`) pois a página de calendário é standalone e não carrega `dashboard.js`
- Admin técnico (`is_superuser`) recebe `show_instructor_area=True` por herança de permissão na view — comportamento existente, não alterado

## Pendências

- Gestão de check-ins ao vivo não foi testada com classes no dia (hoje é domingo — sem aulas agendadas); a lógica de `checkin-row` e `js-approve-checkin` está implementada e os endpoints estão registrados, mas requerem teste em dia de semana com classes no schedule
- Tela de calendário: funcionalidade de toggle/cancelar sessão (`InstructorToggleSessionView`) implementada em url mas sem botão na UI atual (fora do escopo desta PRD)
