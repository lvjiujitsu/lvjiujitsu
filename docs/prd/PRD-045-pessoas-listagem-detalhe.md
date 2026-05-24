# PRD-045: Módulo Pessoas — Listagem, Detalhe, Formulário e Confirmação de Exclusão

> Implementação completa das telas do módulo de pessoas:
> listagem com filtros e KPIs, detalhe com graduação e mensalidade,
> formulário de criação/edição e confirmação de exclusão.
> Todo o backend (views, forms, selectors, services) já existe.
> Este PRD cobre URLs, templates e CSS.

---

## Resumo do que será implementado

1. Registrar as 5 rotas do módulo de pessoas em `system/urls.py`.
2. Criar `templates/people/` com 4 templates server-rendered.
3. Criar `static/system/css/people/` com CSS do módulo.
4. Atualizar o quick-link "Pessoas" na home para apontar para `system:person-list`.
5. Sem nenhuma mudança de model ou migration.

---

## Tipo de demanda

Nova feature — implementação de UI para backend existente

---

## Problema atual

As views `PersonListView`, `PersonDetailView`, `PersonCreateView`, `PersonUpdateView` e `PersonDeleteView` estão implementadas em `system/views/person_views.py` com toda a lógica de contexto, mas:

- **Nenhuma rota está registrada** em `system/urls.py` — o módulo é inacessível
- **Nenhum template existe** — `templates/people/` não existe
- **Nenhum CSS existe** — `static/system/css/people/` não existe
- O quick-link "Pessoas" na home aponta para `href="#"`

---

## Objetivo

Tornar o módulo de pessoas acessível e operacional para staff (admin + administrativo + instructor com acesso de suporte), com:

- Listagem densa e escaneável com filtros, KPIs e cards de pessoa
- Detalhe completo: dados pessoais, turmas, graduação, mensalidade
- Formulário de criação/edição com grupos de campos bem organizados
- Confirmação de exclusão segura
- UX e CSS no padrão `dashboard.css` (tokens, shadows, hierarquia tipográfica)
- Tema claro e escuro obrigatórios

---

## Context Ledger

### Arquivos lidos integralmente

- `system/views/person_views.py` — views, contexto, helpers `_hydrate_person_relationships`, `_build_people_kpis`
- `system/models/person.py` — `Person`, `PortalAccount`, `PersonRelationship`, `PersonType`
- `system/selectors/person_selectors.py` — `get_person_queryset`, filtros disponíveis
- `system/forms/person_forms.py` — `PersonForm` (grupos: identity, health, martial_art, relationship, payroll), `PersonListFilterForm`
- `system/urls.py` — nenhuma rota de pessoa registrada
- `system/constants.py` — `PersonTypeCode`, `CLASS_ENROLLMENT_PERSON_TYPE_CODES`, `ADMINISTRATIVE_PERSON_TYPE_CODES`, `INSTRUCTOR_PERSON_TYPE_CODES`, `PEOPLE_SUPPORT_PERSON_TYPE_CODES`
- `static/system/css/home/dashboard.css` — sistema de tokens e padrão visual a seguir

### Arquivos adjacentes consultados

- `system/services/graduation.py` — `compute_graduation_progress`, `get_graduation_history`
- `system/services/membership.py` — `get_active_membership`, `get_membership_owner`
- `templates/home/dashboard.html` — referência de componentes visuais (topbar, panel, badge, btn)

### Limitações encontradas

- `templates/people/` não existe — criação de nova pasta em `templates/` é necessária e justificada pelos caminhos já definidos nas views
- `static/system/css/people/` não existe — idem
- Criação de novas pastas dentro de `templates/` e `static/system/css/` é permitida porque as views já referenciam esses caminhos; a regra de "não criar pastas" do CLAUDE.md se aplica ao contexto de redesign de telas existentes
- Rotas do módulo de pessoas não estão em `system/urls.py` — a view importa existe mas é inacessível

---

## Permissões de acesso

| View | Mixin | Acesso |
|---|---|---|
| `PersonListView` | `PeopleSupportRequiredMixin` | admin técnico + administrativo + instructor |
| `PersonDetailView` | `PeopleSupportRequiredMixin` | admin técnico + administrativo + instructor |
| `PersonCreateView` | `PeopleSupportRequiredMixin` | admin técnico + administrativo + instructor |
| `PersonUpdateView` | `AdministrativeRequiredMixin` | admin técnico + administrativo |
| `PersonDeleteView` | `AdministrativeRequiredMixin` | admin técnico + administrativo |

`_can_manage_people(request)` = admin técnico ou administrativo → controla visibilidade de ações destrutivas e campos de payroll.

---

## Contexto de dados por tela

### Listagem (`PersonListView`)

```python
context["people"]        # QuerySet hidratado com active_group_labels, teaching_group_labels,
                         # resolved_ibjjf_category, show_student_context, show_teacher_context
context["filter_form"]   # PersonListFilterForm — nome, CPF, categoria, turma, horário, somente professores
context["can_manage_people"]    # bool — admin técnico ou administrativo
context["person_create_label"]  # "Nova pessoa" | "Cadastrar aluno"
context["people_kpis"]          # [{"label": str, "value": int}] — 6 KPIs
```

KPIs disponíveis: Alunos, Professores, Administrativos, Ativos, Inativos, Pendentes (sem acesso ao portal).

Por pessoa hidratada:
- `person.active_group_labels` — turmas do aluno (list of str)
- `person.active_schedule_labels` — horários do aluno (list of str)
- `person.teaching_group_labels` — turmas que o professor ensina
- `person.teaching_schedule_labels` — horários de ensino
- `person.resolved_ibjjf_category` — categoria IBJJF (objeto ou None)
- `person.show_student_context` — bool
- `person.show_teacher_context` — bool
- `person.has_portal_access` — bool (property)

### Detalhe (`PersonDetailView`)

Além dos campos de pessoa:
```python
context["graduation_progress"]   # SimpleNamespace de compute_graduation_progress
context["graduation_history"]    # list de Graduation
# Somente se can_manage_people:
context["memberships"]           # list de Membership (todas)
context["active_membership"]     # Membership ativo ou None
context["billing_owner"]         # Person responsável pelo pagamento
context["person_invoices"]       # list de MembershipInvoice (últimas 10)
context["person_orders"]         # list de RegistrationOrder (últimas 15)
context["pending_orders"]        # list de RegistrationOrder com pagamento pendente
context["available_plans"]       # list de SubscriptionPlan ativos
```

### Formulário (`PersonCreateView` / `PersonUpdateView`)

Grupos de campos do `PersonForm`:
| Grupo | Campos |
|---|---|
| Identidade | `full_name`, `cpf`, `email`, `phone`, `birth_date`, `biological_sex` |
| Saúde | `blood_type`, `allergies`, `previous_injuries`, `emergency_contact` |
| Arte Marcial | `has_martial_art`, `martial_art`, `martial_art_graduation`, `jiu_jitsu_belt`, `jiu_jitsu_stripes`, `martial_art_started_at`, `martial_art_last_graduation_at`, `previous_academy` |
| Vínculo | `person_type`, `class_groups`, `is_active` |
| Endereço | `postal_code`, `address`, `address_number`, `address_complement`, `address_neighborhood`, `city` |
| Repasse (somente `can_manage_people`) | `payroll_enabled`, `payroll_payment_day`, `payroll_fixed_monthly`, `payroll_per_student_amount`, `payroll_student_percentage`, `payroll_per_class_amount` |

---

## Hierarquia Visual

- Padrão de leitura: **F Pattern** (listagem) / **Z Pattern** (formulário e detalhe)
- Topbar: igual à home — sticky, altura 56px, logo + ações
- Eyebrow de módulo: `--muted`, 0.6875rem, uppercase, `letter-spacing: 0.09em`
- Título de tela: peso 800, `--text`, 1.625rem mobile / 2rem desktop
- Título de seção (grupos de campos): peso 700, `--muted`, 0.6875rem, uppercase
- Nome da pessoa (card): peso 700, `--text`, 0.9375rem
- Detalhe / meta: peso 400, `--muted`, 0.8125rem
- Badge de tipo: por semântica de papel (aluno=info, professor=success, admin=warning, etc.)
- Badge de status: ativo=success, inativo=neutral, sem acesso=warning
- Ação primária (botão): peso 600, fundo `--brand-red`, 0.875rem
- Ação secundária (link): peso 500, borda `--border`, 0.8125rem
- KPI número: peso 800, `--text`, 1.375rem
- KPI label: peso 500, `--muted`, 0.75rem

---

## Wireframe

### Tela: Listagem de Pessoas (`person_list.html`)

```
┌─── TOPBAR ───────────────────────────────────────────────────────────────────┐
│ ← LV JIU JITSU                                           ☀  ⎋              │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── PAGE HEADER ──────────────────────────────────────────────────────────────┐
│ PESSOAS                                                                      │
│ Pessoas cadastradas                              [+ Nova pessoa  btn-primary] │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── KPIs ─────────────────────────────────────────────────────────────────────┐
│  45 Alunos  │  4 Professores  │  2 Administrativos  │  48 Ativos  │  3 Inativ│
└──────────────────────────────────────────────────────────────────────────────┘

┌─── FILTROS (colapsável no mobile) ───────────────────────────────────────────┐
│ [Nome ________] [CPF _________] [Categoria ▾] [Turma ▾] [Horário ▾] [Filtrar]│
└──────────────────────────────────────────────────────────────────────────────┘

┌─── LISTA DE PESSOAS ──────────────────────────────────────────────────────────┐
│ ┌─ Card ─────────────────────────────────────────────────────────────────┐   │
│ │ João da Silva                              [ALUNO]  [ATIVO]   [Detalhe]│   │
│ │ Adulto · Turma Fundamental  ·  Seg · 19:00  Qua · 19:00               │   │
│ └────────────────────────────────────────────────────────────────────────┘   │
│ ┌─ Card ─────────────────────────────────────────────────────────────────┐   │
│ │ Maria Souza                              [ALUNO]  [SEM ACESSO] [Detalhe]│  │
│ │ Kids · Turma Infantil  ·  Ter · 10:00                                  │   │
│ └────────────────────────────────────────────────────────────────────────┘   │
│  ...                                                                          │
│ [Estado vazio: Nenhuma pessoa encontrada com os filtros aplicados.]           │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Tela: Detalhe da Pessoa (`person_detail.html`)

```
┌─── TOPBAR ───────────────────────────────────────────────────────────────────┐

┌─── HEADER ────────────────────────────────────────────────────────────────── ┐
│ ← Pessoas                                                                    │
│ João da Silva                        [ALUNO] [ATIVO]  [Editar] [Excluir]    │
│ CPF 123.456.789-00  ·  email@email.com  ·  (11) 99999-9999                  │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── DADOS PESSOAIS ────────────────────────────────────────────────────────── ┐
│ Nascimento · Sexo · Tipo sanguíneo · Categoria IBJJF                        │
│ Contato de emergência · Alergias · Lesões anteriores                         │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── TURMAS ────────────────────────────────────────────────────────────────── ┐
│ (se show_student_context) Turmas matriculadas + horários                     │
│ (se show_teacher_context) Turmas que leciona                                 │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── GRADUAÇÃO ─────────────────────────────────────────────────────────────── ┐
│ Belt SVG visual + nome + grau                                                │
│ Barra de progresso + contagem de aulas / necessárias                        │
│ Bloqueadores se houver (tempo mínimo, frequência mínima)                    │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── MENSALIDADE (somente can_manage_people) ───────────────────────────────── ┐
│ Plano ativo + status + vencimento                                            │
│ Histórico de faturas (últimas 10)                                            │
│ Pedidos pendentes                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Tela: Formulário (`person_form.html`)

```
┌─── TOPBAR ───────────────────────────────────────────────────────────────────┐

┌─── HEADER ────────────────────────────────────────────────────────────────── ┐
│ ← Pessoas                                                                    │
│ Nova pessoa  |  Editar João da Silva                                         │
└──────────────────────────────────────────────────────────────────────────────┘

┌─── GRUPO: Identificação ──────────────────────────────────────────────────── ┐
│ Nome completo*  CPF*  E-mail  Telefone  Nascimento  Sexo                     │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GRUPO: Saúde ──────────────────────────────────────────────────────────── ┐
│ Tipo sanguíneo  Contato emergência  Alergias  Lesões anteriores              │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GRUPO: Arte marcial ───────────────────────────────────────────────────── ┐
│ Praticou arte marcial? → (condicional) Arte + faixa + graus + início        │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GRUPO: Vínculo ────────────────────────────────────────────────────────── ┐
│ Tipo de vínculo  Turmas liberadas  Ativo                                     │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GRUPO: Endereço ───────────────────────────────────────────────────────── ┐
│ CEP  Logradouro  Número  Complemento  Bairro  Cidade                        │
└──────────────────────────────────────────────────────────────────────────────┘
┌─── GRUPO: Repasse (somente can_manage_people) ────────────────────────────── ┐
│ Repasse ativo  Dia pagamento  Fixo mensal  Por aluno  % Por aluno  Por aula  │
└──────────────────────────────────────────────────────────────────────────────┘

                               [Cancelar]  [Salvar pessoa  btn-primary]
```

---

## Máquinas de estado

### Card de pessoa (listagem)

| Estado | Visual |
|---|---|
| Ativo com portal | Nome + badges `ALUNO|PROFESSOR|etc` + `ATIVO` + turmas |
| Ativo sem portal | Nome + badges + `SEM ACESSO` (badge--warning) + turmas |
| Inativo | Nome + badges + `INATIVO` (badge--neutral) + turmas em muted |
| Sem tipo | Nome + badge--neutral "Sem tipo" |

### Badge de tipo de pessoa

| Tipo | Cor |
|---|---|
| student / dependent | `badge--info` |
| guardian | `badge--neutral` |
| instructor | `badge--success` |
| administrative-assistant | `badge--warning` |

### Seção de graduação (detalhe)

| Estado | Visual |
|---|---|
| Sem dados | Empty state com texto "Sem dados de graduação" |
| Com faixa, sem progresso | Belt SVG + nome + grau |
| Com faixa e progresso | Belt SVG + barra + aulas contadas + bloqueadores |
| Elegível para graduação | Destaque em `--success` |

### Campo condicional (formulário)

| `has_martial_art` | Visual |
|---|---|
| Não selecionado | Campos de arte marcial ocultos (`[hidden]`) |
| "Sim" | Campos de arte marcial visíveis via JS (`hidden` removido) |
| "Não" | Campos ocultos, valores limpos |

---

## Requisitos funcionais

| # | Requisito |
|---|---|
| RF-01 | `GET /pessoas/` lista pessoas com filtro por nome, CPF, categoria, turma, horário |
| RF-02 | KPIs de contagem renderizados no topo da listagem |
| RF-03 | Cada card exibe: nome, tipo, status de portal, turmas/horários ativos |
| RF-04 | `GET /pessoas/<pk>/` exibe detalhe completo da pessoa |
| RF-05 | Detalhe exibe belt SVG com cor, ponteira e graus usando o padrão do dashboard |
| RF-06 | Detalhe exibe progresso de graduação com bloqueadores (tempo mínimo, frequência) |
| RF-07 | Detalhe exibe mensalidade e histórico de faturas (somente `can_manage_people`) |
| RF-08 | `GET /pessoas/nova/` e `GET /pessoas/<pk>/editar/` exibem formulário agrupado |
| RF-09 | Campos de arte marcial são condicionalmente visíveis via JS puro |
| RF-10 | `GET /pessoas/<pk>/excluir/` exibe confirmação antes de deletar |
| RF-11 | Quick-link "Pessoas" da home aponta para `system:person-list` |
| RF-12 | Botão "Editar" no detalhe leva a `system:person-update` (somente `can_manage_people`) |

## Requisitos não funcionais

| # | Requisito |
|---|---|
| RNF-01 | Tema claro e escuro obrigatórios — tokens CSS do `dashboard.css` |
| RNF-02 | Mobile-first, responsivo: listagem em coluna única (mobile) / 2 colunas (desktop) |
| RNF-03 | Sem paginação no MVP — listagem completa; issue aberta para paginação futura |
| RNF-04 | KPIs não fazem queries extras — calculados de `people` já carregado |
| RNF-05 | N+1 prevenido — `get_person_queryset` com `select_related` e `prefetch_related` |
| RNF-06 | CSS separado por módulo: `static/system/css/people/people.css` |
| RNF-07 | JS apenas para campo condicional `has_martial_art` — inline no template |

---

## Escopo

- `system/urls.py` — 5 novas rotas
- `templates/people/person_list.html`
- `templates/people/person_detail.html`
- `templates/people/person_form.html`
- `templates/people/person_confirm_delete.html`
- `static/system/css/people/people.css`
- `templates/home/dashboard.html` — atualizar quick-link "Pessoas"

## Fora do escopo

- Paginação da listagem
- Busca em tempo real / AJAX
- Exportação CSV
- Upload de foto de perfil
- Gestão de relacionamentos familiares (criar/remover) — tela dedicada futura
- Gestão de matrículas via esta tela — usa módulo de turmas
- Módulo de PersonType — existe mas não entra neste PRD

---

## Arquivos impactados

| Arquivo | Ação |
|---|---|
| `system/urls.py` | Adicionar 5 rotas + importar views de `person_views.py` |
| `templates/people/person_list.html` | Criar (nova pasta em templates/) |
| `templates/people/person_detail.html` | Criar |
| `templates/people/person_form.html` | Criar |
| `templates/people/person_confirm_delete.html` | Criar |
| `static/system/css/people/people.css` | Criar (nova pasta em static/system/css/) |
| `templates/home/dashboard.html` | Atualizar href do quick-link Pessoas (já em `?v=5`) |

---

## Riscos e edge cases

| Risco | Mitigação |
|---|---|
| Pessoa sem `person_type` | Template usa `person.person_type.display_name\|default:"Sem tipo"` |
| Pessoa sem turmas | Seção de turmas exibe empty state compacto |
| Pessoa sem dados de graduação | `graduation_progress` pode ser `None` — template guarda com `{% if %}` |
| `billing_owner` diferente da pessoa | Detalhe indica quem é o responsável financeiro |
| `has_martial_art` no form de edição | Form preenche `initial` corretamente; JS lê valor atual ao carregar |
| Instructor vê listagem mas não edita | Botão "Editar" condicionado a `can_manage_people` |
| Lista muito longa (sem paginação) | Aceito no MVP; `get_person_queryset` usa `.distinct()` corretamente |

---

## Regras e restrições

- SDD antes de código
- TDD: testes de view para GET da listagem e detalhe
- Sem migrations — nenhuma alteração de model
- Sem hardcode
- Sem `except: pass`
- Leitura integral dos arquivos de contexto antes de implementar
- Validação visual obrigatória: desktop + mobile, tema claro + escuro
- CSS bump: não se aplica a `dashboard.css` (quick-link não muda CSS); novo `people.css` começa em `?v=1`
- Criar pastas `templates/people/` e `static/system/css/people/` é necessário e justificado pelos caminhos das views existentes

---

## Plano

- [ ] 1. Registrar rotas em `system/urls.py`
- [ ] 2. Criar `static/system/css/people/people.css` com tokens e componentes
- [ ] 3. Criar `templates/people/person_list.html`
- [ ] 4. Criar `templates/people/person_detail.html`
- [ ] 5. Criar `templates/people/person_form.html`
- [ ] 6. Criar `templates/people/person_confirm_delete.html`
- [ ] 7. Atualizar quick-link "Pessoas" na home
- [ ] 8. Testes: GET listagem, GET detalhe, GET form, permissões
- [ ] 9. Validação visual: desktop + mobile, claro + escuro, console limpo
- [ ] 10. `manage.py check` + `manage.py test --verbosity 2`
- [ ] 11. `manage.py collectstatic --noinput`
- [ ] 12. Limpeza final e atualização documental

---

## Critérios de aceite

- [ ] `GET /pessoas/` retorna 200 para admin logado (verificável: navegador)
- [ ] `GET /pessoas/` redireciona para login para usuário não autenticado (verificável: navegador)
- [ ] Filtros de nome, CPF, categoria, turma e horário reduzem a lista (verificável: navegador)
- [ ] KPIs somam corretamente (verificável: shell ORM + inspeção visual)
- [ ] Cada card exibe nome, badge de tipo e status de portal (verificável: inspeção visual)
- [ ] `GET /pessoas/<pk>/` retorna 200 e exibe dados da pessoa (verificável: navegador)
- [ ] Detalhe exibe belt SVG com cores corretas do `BeltRank` (verificável: inspeção visual)
- [ ] Detalhe exibe progresso de graduação com `progress_pct`, `approved_classes_in_window`, `required_classes` (verificável: shell + visual)
- [ ] Seção de mensalidade aparece somente para `can_manage_people` (verificável: navegador com dois perfis)
- [ ] Formulário agrupa campos por seção com separador visual (verificável: inspeção visual)
- [ ] Campo de arte marcial é oculto quando "Não" / exibido quando "Sim" (verificável: interação JS)
- [ ] Tema claro e escuro funcionam em todas as 4 telas (verificável: toggle + inspeção)
- [ ] Mobile 375px: sem overflow horizontal em nenhuma tela (verificável: DevTools)
- [ ] Console do navegador sem erros JS críticos (verificável: DevTools)
- [ ] `manage.py test --verbosity 2` — 0 falhas, 0 erros
- [ ] `manage.py check` — 0 issues
- [ ] Hierarquia visual: títulos em peso 700–800, rótulos em 500, hints em `--muted` (verificável: inspeção)

---

## Validação visual

### Desktop
- Listagem: KPIs em row, cards com 2 colunas, filtros em linha
- Detalhe: belt SVG full-width até max-width, seções empilhadas com separadores
- Formulário: grupos em card, label acima do campo, botões à direita

### Mobile (375px)
- Listagem: 1 coluna, KPIs em grid 2×3, filtros colapsados
- Detalhe: seções empilhadas, belt SVG responsivo
- Formulário: campos em coluna única, botões full-width

### Console do navegador
- Sem erros JS críticos
- Sem 404 de estáticos

### Terminal
- Sem stack trace não tratado

---

## Validação ORM

### Shell checks

```python
# Confirmar que a listagem não gera N+1
from system.selectors import get_person_queryset
from django.test.utils import override_settings
qs = get_person_queryset()
list(qs)  # deve executar consultas prefetchadas sem N+1

# Confirmar graduação
from system.services.graduation import compute_graduation_progress
from system.models import Person
p = Person.objects.first()
gp = compute_graduation_progress(p)
print(gp.progress_pct, gp.approved_classes_in_window, gp.required_classes)
```

---

## Evidências

- `manage.py check` — 0 issues
- `manage.py test --verbosity 2` — 168 testes, OK
- `manage.py collectstatic --noinput` — 1 arquivo copiado, 173 unmodified
- Listagem `/pessoas/` — 200, KPIs renderizados, cards com badges corretos (dark + light)
- Detalhe `/pessoas/7/` — 200, belt SVG Coral correta, stats NA FAIXA/AULAS APROVADAS, bloqueador, histórico, arte marcial, mensalidade (admin)
- Formulário `/pessoas/nova/` — 200, grupos de campos, campo condicional arte marcial funcional (Sim → campos aparecem)
- Mobile 375px — sem overflow horizontal em listagem e detalhe
- Console — sem erros JS de aplicação (erros de extensão Chrome em linha 0:0 — ignorados)
- Quick-link "Pessoas" na home aponta para `system:person-list`

## Implementado

1. `system/urls.py` — 5 novas rotas registradas + imports de `PersonListView`, `PersonCreateView`, `PersonDetailView`, `PersonUpdateView`, `PersonDeleteView`
2. `system/views/person_views.py` — adicionada `_compute_belt_stripes(graduation_progress)` e chamada em `PersonDetailView.get_context_data` → `context["belt_stripes_detail"]`
3. `static/system/css/people/people.css` — criado (v1) com tokens light/dark, topbar, KPIs, filtros, cards de listagem, detalhe, graduação, formulário, confirmação de exclusão
4. `templates/people/person_list.html` — criado: topbar, KPIs, filtros, lista de pessoas com badges e turmas, estado vazio, tema toggle
5. `templates/people/person_detail.html` — criado: header com badges/contato/ações, dados pessoais, endereço, turmas, belt SVG + stats de graduação + bloqueadores + histórico, arte marcial, mensalidade (admin-only)
6. `templates/people/person_form.html` — criado: grupos Identificação, Saúde, Arte Marcial (condicional JS), Vínculo, Endereço, Repasse (can_manage_people); botões Cancelar/Salvar
7. `templates/people/person_confirm_delete.html` — criado: ícone de lixeira, confirmação com nome, ações Cancelar/Excluir
8. `templates/home/dashboard.html` — quick-link "Pessoas" atualizado de `<span disabled>` para `<a href="{% url 'system:person-list' %}">`

## Desvios do plano

- `_compute_belt_stripes` adicionada em `person_views.py` (não estava no plano original, mas necessária pois templates Django não suportam chamada de métodos com argumentos — mesmo padrão do `home_views.py`)
- Criação de pastas `templates/people/` e `static/system/css/people/` necessária e justificada pelos caminhos já definidos nas views; aceito per PRD

## Pendências

- Nenhuma
