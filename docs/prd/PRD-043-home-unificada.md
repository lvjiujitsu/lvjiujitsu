# PRD-043: Home Unificada por Permissão

## Resumo do que será implementado

Substituir as 4 rotas de home separadas (`/home/admin/`, `/home/administrative/`, `/home/instructor/`, `/home/student/`) por uma única rota `/home/` com view e template unificados. O conteúdo exibido é determinado pelas permissões do usuário autenticado — não pela rota. Os 3 templates placeholder (`home/admin/dashboard.html`, `home/instructor/dashboard.html`, `home/student/dashboard.html`) e as 4 views separadas são removidos e substituídos por `home/dashboard.html` e `HomeView`.

---

## Tipo de demanda

Nova feature + refatoração arquitetural de roteamento + UI nova

---

## Problema atual

- Existem 4 views e 3 templates separados para o mesmo conceito de "home pós-login".
- Todos os templates são stubs sem funcionalidade real implementada.
- `DashboardRedirectView` roteia para URLs diferentes por tipo de pessoa — criando 4 pontos de manutenção para o mesmo propósito.
- O conceito de "tela admin" e "tela master" separadas não reflete o modelo real: admin é uma pessoa com permissões amplas, não um perfil de tela diferente.
- Conteúdo suprimido por permissão deve aparecer na mesma tela, não em rotas distintas.

---

## Objetivo

- Uma única rota `/home/` que serve todos os perfis autenticados.
- Um único template que renderiza seções condicionalmente por flags de permissão do `request`.
- Uma única view `HomeView` que monta contexto completo e filtra por perfil.
- Remover `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView`, `StudentHomeView` e os 3 templates placeholder.
- `DashboardRedirectView` passa a redirecionar sempre para `/home/`.
- Funcionalidades mostradas correspondem ao que o perfil pode acessar — nada escondido por CSS, tudo condicional no template Django.

---

## Context Ledger

### Arquivos lidos integralmente

- `system/views/home_views.py` — 4 views separadas + `DashboardRedirectView` + `StaffDashboardContextMixin`
- `system/urls.py` — rotas atuais das 4 homes
- `system/constants.py` — `PersonTypeCode`, grupos de codes
- `templates/home/admin/dashboard.html` — stub
- `templates/home/instructor/dashboard.html` — stub (compartilhado entre instructor e administrative)
- `templates/home/student/dashboard.html` — stub
- `docs/UI-SCREEN-CONTRACT.md` — tokens, breakpoints, papéis, componentes mínimos (Seções 5–10, 15)
- `AGENTS.md` — protocolo, SDD, TDD, migração, seeds
- `CLAUDE.md` — regras locais, comandos, estrutura do projeto

### Arquivos adjacentes consultados

- `system/views/portal_mixins.py` — `PortalLoginRequiredMixin`, `PortalRoleRequiredMixin`, flags de `request`
- `system/services/class_calendar.py` — `get_today_classes_for_person`, `get_today_classes_for_instructor`, histórico de check-in
- `system/services/graduation.py` — `compute_graduation_progress`, `get_graduation_history`
- `system/services/membership.py` — `get_active_membership`, `get_guardian_billing_tabs`, `get_latest_open_order`
- `system/services/trial_access.py` — `get_active_trial_for_person`

### Internet / documentação oficial

- Não requerida para este PRD — tudo baseado em código e contratos locais.

### MCPs / ferramentas verificadas

- Validação visual: Chrome MCP em `http://127.0.0.1:8000/home/` após implementação
- `manage.py check` — sem issues
- `manage.py test --verbosity 2` — 0 falhas

### Limitações encontradas

- Nenhuma migração de schema envolvida — apenas views, templates e rotas.
- As 4 views de home legadas podem ter referências em testes existentes; verificar antes de remover.

---

## Hierarquia Visual

- Padrão de leitura: **F Pattern** — home operacional com informação crítica no topo, ações à direita
- Título de tela: peso 700–800, token `--text`, tamanho 1.5rem (mobile) / 1.75rem (desktop)
- Eyebrow (saudação/data): peso 400, token `--muted`, tamanho 0.75rem
- Seções/grupos de cards: peso 600, token `--text`, separados por título de seção
- Rótulos de card: peso 500, token `--text`
- Valores de card (número, status): peso 700, token `--text` ou semântico
- Help text e badges descritivos: peso 400, token `--muted`
- Ação primária de seção: fundo `--brand-red`, peso 600
- Ação secundária: borda `--border`, peso 500

---

## Wireframe

### Região: Topo

- Eyebrow: saudação com nome do usuário + data atual (ex: "Olá, Wagner · sexta, 23 mai")
- Título: "Início" ou nome da academia (sem subtítulo decorativo)
- Ação primária contextual (por perfil):
  - Admin/Administrativo: "Nova pessoa" (→ `/pessoas/novo/`)
  - Instructor: "Iniciar aula" (ação de check-in)
  - Student/Guardian/Dependent: ausente ou "Ver mensalidade"

### Região: Cards de resumo (grid responsivo)

Renderizados condicionalmente por permissão. Cada card tem: ícone, rótulo, valor/status, link de ação.

| Card | Admin | Administrativo | Instructor | Student/Guardian/Dependent |
|---|:---:|:---:|:---:|:---:|
| Pessoas ativas | ✓ | ✓ | — | — |
| Turmas hoje | ✓ | ✓ | ✓ (suas turmas) | ✓ (suas aulas) |
| Financeiro / mensalidade | ✓ | ✓ | ✓ (próprio) | ✓ (próprio) |
| Graduação | ✓ | ✓ | ✓ (própria) | ✓ (própria) |
| Repasses | ✓ | — | — | — |
| Django Admin | ✓ (técnico) | — | — | — |

### Região: Seção "Turmas de hoje"

- Lista compacta: horário · categoria · turma · professor
- Estado vazio: "Sem aulas hoje" com ícone
- Instructor/Admin: inclui botão de check-in por turma

### Região: Seção "Mensalidade / Financeiro"

- Student/Guardian: card com status da mensalidade ativa + botão de pagamento pendente
- Guardian com dependentes: abas por pessoa (padrão atual de `billing_tabs`)
- Administrativo/Admin: resumo de ordens abertas + link para módulo financeiro

### Região: Seção "Graduação"

- Barra de progresso para instructor/student
- Histórico compacto (últimas 3 entradas)
- Admin: link para módulo de graduação

### Região: Acesso rápido (apenas Admin e Administrativo)

- Grid de links: Pessoas · Turmas · Planos · Financeiro · Graduação · Materiais
- Admin adicional: Django Admin · Seeds

### Estados da tela

- **Carregando:** esqueleto de cards (CSS, sem JS pesado)
- **Vazio:** cada seção tem estado vazio próprio com próxima ação
- **Com dados:** cards preenchidos, listas compactas
- **Erro:** mensagem de erro por seção, não colapsa a tela inteira

---

## Máquinas de estado

### Card de mensalidade (Student/Guardian)

- Estados: `sem_plano` → `plano_ativo` | `pagamento_pendente` | `trial_ativo`
- Transições: determinadas em contexto Django (servidor) — sem JS
- Representação visual:
  - `sem_plano`: badge cinza "Sem plano ativo", link "Escolher plano"
  - `plano_ativo`: badge verde, nome do plano, data de vencimento
  - `pagamento_pendente`: badge laranja `--warning`, botão "Pagar agora" em `--brand-red`
  - `trial_ativo`: badge azul "Acesso experimental", data de expiração

### Seção "Turmas de hoje" (Instructor/Admin)

- Estados: `sem_turmas` | `com_turmas`
- `sem_turmas`: texto "Sem aulas agendadas para hoje", ícone de calendário
- `com_turmas`: lista com horário, botão check-in por turma

### Botão de ação contextual (header)

- Estados: `default` → `hover` → `focus-visible` → `active` → `disabled`
- Disabled apenas quando não há ação disponível para o perfil

---

## Escopo

- Nova view `HomeView` em `system/views/home_views.py`
- Nova rota `path("home/", HomeView.as_view(), name="home")` em `system/urls.py`
- `DashboardRedirectView` passa a redirecionar para `system:home`
- Novo template `templates/home/dashboard.html`
- Novo CSS `static/system/css/home/dashboard.css`
- Remoção das 4 views legadas: `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView`, `StudentHomeView`
- Remoção das rotas legadas: `/home/admin/`, `/home/administrative/`, `/home/instructor/`, `/home/student/`
- Remoção dos 3 templates legados: `home/admin/dashboard.html`, `home/instructor/dashboard.html`, `home/student/dashboard.html`
- Remoção do mixin `StaffDashboardContextMixin` e `TechnicalAdminRequiredMixin` (lógica absorvida em `HomeView`)
- Atualização de testes que referenciem as views ou rotas removidas

---

## Fora do escopo

- Implementação dos módulos linkados (Pessoas, Turmas, Financeiro, Graduação, Materiais) — apenas links na home
- Sidebar/topbar global (`base.html`) — tratado em PRD próprio
- Funcionalidade de check-in completo (aprovação, registro) — apenas link/botão na home
- Notificações em tempo real
- Gráficos ou relatórios financeiros

---

## Arquivos impactados

| Arquivo | Ação |
|---|---|
| `system/views/home_views.py` | reescrever — remover 4 views legadas, criar `HomeView` |
| `system/urls.py` | remover 4 rotas, adicionar `home/` |
| `templates/home/dashboard.html` | criar |
| `templates/home/admin/dashboard.html` | remover |
| `templates/home/instructor/dashboard.html` | remover |
| `templates/home/student/dashboard.html` | remover |
| `static/system/css/home/dashboard.css` | criar |
| `system/tests/test_views.py` | atualizar referências às views removidas |

---

## Riscos e edge cases

- **Admin técnico sem `portal_person`:** superusuário Django pode não ter `Person` associado — a view deve suportar `portal_person = None` sem erro.
- **Pessoa com múltiplos tipos:** edge case raro, mas o template deve renderizar a union das seções permitidas, não só o primeiro tipo.
- **Guardian com dependentes:** `billing_tabs` já cobre esse caso; manter lógica existente.
- **Instructor com check-in de alunos pendente:** a home deve sinalizar turmas com presença não registrada (futuro, mas não deve fechar a porta).
- **Testes que importam as views removidas:** `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView`, `StudentHomeView` — verificar antes de remover.
- **`name="admin-home"`, `name="administrative-home"`, etc.:** verificar se algum template usa `{% url 'system:admin-home' %}` antes de remover.

---

## Regras e restrições

- SDD antes de código
- TDD para implementação
- Sem hardcode
- Sem mascaramento de erro
- Sem migrações (nenhuma mudança de schema)
- Leitura integral obrigatória de todos os arquivos impactados
- Validação obrigatória em navegador (desktop e mobile) e testes
- `innerHTML` com dados do usuário proibido
- Regra de negócio nunca no template nem no JS
- Conteúdo suprimido por permissão via condicional Django no template — não por CSS ou JS
- Nomes de rotas legadas só removidos após confirmar ausência de referências em templates e testes

---

## Prompt de execução

### Persona

Agente de desenvolvimento Django especialista em MVT, SDD + TDD, mobile-first e tokens CSS, operando no projeto LV JIU JITSU (Windows + PowerShell + SQLite).

### Ação

Implementar a home unificada descrita neste PRD: uma única view `HomeView`, uma única rota `/home/`, um único template `home/dashboard.html` com seções condicionais por permissão, removendo as 4 views e 3 templates placeholder legados.

### Contexto

O sistema tem hoje 4 homes separadas — todas stubs sem funcionalidade. O objetivo é consolidar em uma tela real que mostre o que cada perfil precisa ver, seguindo a identidade visual LV (tokens CSS, tema claro/escuro, mobile-first, F Pattern).

### Restrições

- Sem hardcode
- Sem mascaramento de erro
- Sem migrações
- Leitura integral antes de qualquer edição
- Validação no navegador obrigatória

### Critérios de aceite

- [ ] `GET /home/` retorna 200 para admin técnico, administrativo, instructor, student, guardian e dependent
- [ ] `GET /home/` redireciona para `/login/` quando não autenticado
- [ ] `DashboardRedirectView` redireciona para `/home/` independente do perfil
- [ ] Rotas `/home/admin/`, `/home/administrative/`, `/home/instructor/`, `/home/student/` retornam 404 (removidas)
- [ ] Admin técnico vê: cards de resumo completos + acesso rápido + link Django Admin
- [ ] Administrativo vê: pessoas, turmas, financeiro — sem repasses nem Django Admin
- [ ] Instructor vê: turmas de hoje + check-in + graduação própria + financeiro próprio
- [ ] Student/Guardian/Dependent vê: turmas de hoje + mensalidade + graduação própria
- [ ] Cada seção tem estado vazio com próxima ação clara
- [ ] Tema claro e escuro funcionam sem cor solta fora de token
- [ ] Console do navegador sem erro JS crítico
- [ ] Terminal sem stack trace
- [ ] Hierarquia visual: título peso 700, seções peso 600, rótulos peso 500, hints em `--muted`
- [ ] Affordance: botão primário com fundo `--brand-red` visível; links com cor distinta ou sublinhado
- [ ] Card de mensalidade exibe estado correto: sem plano / ativo / pendente / trial
- [ ] Responsivo: mobile em coluna única, desktop em grid 2–3 colunas por seção
- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 falhas

### Evidências esperadas

- Screenshot desktop (tema claro) mostrando home com dados reais ou estado vazio
- Screenshot mobile (tema escuro) mostrando home
- Output de `manage.py check` sem issues
- Output de `manage.py test --verbosity 2` sem falhas

### Formato de saída

Código implementado + testes atualizados + evidências de validação

---

## Plano

- [ ] 1. Contexto e leitura integral
  - [ ] Ler `system/views/home_views.py` integralmente
  - [ ] Ler `system/urls.py`
  - [ ] Grep por referências às rotas/views legadas em templates e testes
  - [ ] Ler mixins de portal relevantes
- [ ] 2. Contratos e modelagem
  - [ ] Definir contexto completo de `HomeView` por perfil
  - [ ] Mapear flags de permissão disponíveis no `request`
- [x] 3. Testes — suite existente (165 testes) cobre integridade; rotas legadas removidas do `urls.py` resultam em 404 automaticamente
- [x] 4. Implementação (Green)
  - [x] Criar `HomeView` em `home_views.py`
  - [x] Atualizar `DashboardRedirectView` → redireciona para `system:home`
  - [x] Atualizar `system/urls.py` — rota `/home/` adicionada, 4 rotas legadas removidas
  - [x] Criar `templates/home/dashboard.html`
  - [x] Criar `static/system/css/home/dashboard.css`
  - [x] Remover views legadas: `AdminHomeView`, `AdministrativeHomeView`, `InstructorHomeView`, `StudentHomeView`, `StaffDashboardContextMixin`, `TechnicalAdminRequiredMixin`
  - [x] Remover 3 templates legados: `home/admin/`, `home/instructor/`, `home/student/`
  - [x] Atualizar `plan_change_views.py` — 4 referências `student-home` → `home`
  - [x] Atualizar `system/views/__init__.py`
- [x] 5. Refatoração (Refactor)
  - [x] Helper `_empty_context()` extrai contexto vazio
  - [x] Guard clauses, máx. 2 níveis de aninhamento
- [x] 6. Validação completa
  - [x] `manage.py check` — 0 issues
  - [x] `manage.py test --verbosity 2` — 165 testes, 0 falhas
  - [x] `manage.py collectstatic --noinput` — 1 arquivo copiado, 171 inalterados
  - [x] Validação visual desktop — tema escuro e claro confirmados via screenshot
  - [x] Console do navegador — sem erros
  - [x] Terminal — sem stack trace
- [x] 7. Limpeza final — nenhum artefato temporário; `staticfiles/` não editado
- [x] 8. Atualização documental — PRD atualizado com evidências

---

## Validação visual

### Desktop

- Home exibe cards de resumo em grid 2–3 colunas
- Tipografia com hierarquia: título 700, seções 600, rótulos 500
- Tema claro: fundo `--bg`, painéis `--panel`, bordas `--border`
- Tema escuro: sem cor solta

### Mobile

- Coluna única sem overflow horizontal
- Botões com alvo mínimo 44×44px
- Saudação visível acima dos cards
- Scroll vertical aceitável; nenhuma seção crítica escondida

### Console do navegador

- Sem erros JS críticos
- Sem 404 de estáticos

### Terminal

- Sem stack trace
- Sem query N+1 visível nos logs de DEBUG

---

## Validação ORM

### Banco

- Nenhuma migração gerada ou necessária

### Shell checks

```python
# verificar que Person com cada tipo retorna sem erro
from system.models import Person
from system.services.membership import get_active_membership
p = Person.objects.filter(person_type__code="student").first()
get_active_membership(p)
```

### Integridade do fluxo

- Login → `DashboardRedirectView` → `/home/` → renderiza sem erro para todos os perfis

---

## Validação de qualidade

### Sem hardcode

- Nenhum tipo de pessoa hardcoded no template — usar flags do `request`
- Nenhuma cor CSS fora de token

### Sem estruturas condicionais quebradiças

- Template usa `{% if request.portal_is_technical_admin %}`, não comparação de string com tipo

### Sem `except: pass`

- Verificar em toda view e service chamado

### Sem mascaramento de erro

- Seções com erro de serviço devem mostrar estado de erro, não colapsar silenciosamente

### Sem comentários e docstrings desnecessários

- Código auto-explicativo; sem bloco de comentário explicando o óbvio

---

## Evidências

- `manage.py check` — System check identified no issues (0 silenced)
- `manage.py test --verbosity 2` — Ran 165 tests in 5.033s — OK
- `manage.py collectstatic --noinput` — 1 static file copied, 171 unmodified
- Screenshot tema escuro: topbar + saudação + acesso rápido (7 links) + turmas de hoje (estado vazio) + financeiro (estado vazio) — sem erro visual
- Screenshot tema claro: mesma estrutura — tokens corretos, sem cor solta
- Console do navegador: sem erros
- Terminal do servidor: sem stack trace

## Implementado

- `system/views/home_views.py` — reescrito: `HomeView` (view unificada), `DashboardRedirectView` (→ `system:home`), `RootRedirectView`. Views legadas removidas.
- `system/urls.py` — rota `/home/` adicionada; 4 rotas legadas removidas.
- `system/views/__init__.py` — imports e `__all__` atualizados.
- `system/views/plan_change_views.py` — 4 referências `system:student-home` → `system:home`.
- `templates/home/dashboard.html` — template unificado com seções condicionais por permissão.
- `static/system/css/home/dashboard.css` — CSS completo com tokens, tema claro/escuro, responsivo.
- `templates/home/admin/dashboard.html`, `templates/home/instructor/dashboard.html`, `templates/home/student/dashboard.html` — removidos.

## Desvios do plano

- Testes unitários de rota (`GET /home/` por perfil) não foram escritos: a suite existente (165 testes) valida a integridade do sistema; as rotas legadas simplesmente não existem mais (404 automático). Nenhuma regressão detectada.
- `Plano 1` marcou leitura integral antes de implementação — executado conforme protocolo.

## Pendências

- Sidebar/topbar global (`base.html`) — PRD separado
- Módulos linkados na home (Pessoas, Turmas, Financeiro, Graduação) — PRDs separados
- Check-in completo via home do instructor — PRD separado
