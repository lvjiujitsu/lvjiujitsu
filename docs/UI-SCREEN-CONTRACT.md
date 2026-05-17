# UI Screen Contract — LV JIU JITSU

> Fonte de verdade de interface para o sistema LV JIU JITSU.
> Governa design, responsividade, tema, tokens CSS, papéis de acesso e critérios de validação visual.
> Toda tela implementada deve derivar deste contrato.

---

## 1. Propósito

O sistema LV JIU JITSU é um portal operacional de academia de jiu jitsu. A interface serve rotinas reais: cadastro, tatame, presença, calendário, materiais, planos, pagamentos, repasses e graduação.

A interface deve ser moderna, legível e confiável em celular e computador — sem transformar telas internas em landing pages e sem ocultar funcionalidades existentes.

---

## 2. Fontes de verdade

| Assunto | Fonte |
|---|---|
| Como o agente trabalha | `AGENTS.md` |
| Contexto factual do projeto | `CLAUDE.md` |
| Contrato visual e responsivo | Este arquivo |
| Requisito de cada tela | PRD em `docs/prd/` |
| Fluxos reais | `system/urls.py`, `system/views/`, `system/forms/`, `system/services/`, `templates/`, `static/system/` |
| Identidade visual | `static/system/img/` |

---

## 3. Princípios obrigatórios

- Funcionalidade antes de estética.
- Tema claro e escuro sempre presentes em toda tela.
- Mobile-first sem esconder ações.
- Desktop denso, escaneável e operacional.
- Informação crítica visível antes de informação decorativa.
- Formulários com validação e erros visíveis por campo.
- Ações destrutivas visualmente distintas e nunca como ação primária.
- Estados vazios com próxima ação clara.
- Componentes reutilizáveis — CSS por tokens, não por exceção.
- Nenhuma regra de negócio em template ou JavaScript.

---

## 4. Identidade LV

### Linguagem visual

A interface carrega a identidade de tatame, disciplina e cultura marcial com uma camada administrativa sóbria.

**Usar:**
- Preto, grafite, branco, prata e cinzas neutros como base.
- Vermelho LV como acento de ação, risco, destaque ou progresso — nunca como fundo dominante de toda a tela.
- Tipografia forte em títulos, compacta em painéis operacionais.
- Iconografia simples para ações reconhecíveis.
- Logo LV visível e em destaque nas telas de acesso público.

**Evitar:**
- Gradientes roxos/azuis genéricos.
- Painéis gigantes que empurram trabalho para fora da primeira tela.
- Cards aninhados dentro de cards.
- Decoração sem função.
- Texto explicando como usar a interface dentro da própria tela.

---

## 5. Tokens CSS obrigatórios

Todos os componentes usam tokens. Nenhuma cor, sombra ou borda é hardcoded fora dos tokens.

```css
:root {
  /* Fundos */
  --bg: #f4f4f5;
  --panel: #ffffff;
  --surface: #f9f9fb;
  --surface-soft: #f0f0f2;

  /* Bordas e sombras */
  --border: #e4e4e7;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.08);

  /* Tipografia */
  --text: #18181b;
  --muted: #71717a;

  /* Marca */
  --brand-red: #c41230;
  --brand-red-strong: #9b0e25;
  --brand-red-muted: rgba(196, 18, 48, 0.12);

  /* Interação */
  --focus-ring: rgba(196, 18, 48, 0.35);

  /* Semântica */
  --danger: #dc2626;
  --danger-muted: rgba(220, 38, 38, 0.1);
  --success: #16a34a;
  --warning: #d97706;
  --info: #2563eb;

  /* Painel de marca (telas de acesso) */
  --brand-panel-bg: #0f0f0f;
  --brand-panel-text: #f4f4f5;
  --brand-panel-muted: #a1a1aa;
}

html[data-theme="dark"] {
  /* Fundos */
  --bg: #09090b;
  --panel: #18181b;
  --surface: #1f1f23;
  --surface-soft: #27272a;

  /* Bordas e sombras */
  --border: #3f3f46;
  --shadow: 0 1px 4px rgba(0, 0, 0, 0.4);

  /* Tipografia */
  --text: #fafafa;
  --muted: #a1a1aa;

  /* Marca */
  --brand-red: #e02244;
  --brand-red-strong: #c41230;
  --brand-red-muted: rgba(224, 34, 68, 0.15);

  /* Interação */
  --focus-ring: rgba(224, 34, 68, 0.4);

  /* Semântica */
  --danger: #f87171;
  --danger-muted: rgba(248, 113, 113, 0.12);
  --success: #4ade80;
  --warning: #fbbf24;
  --info: #60a5fa;

  /* Painel de marca */
  --brand-panel-bg: #000000;
  --brand-panel-text: #fafafa;
  --brand-panel-muted: #71717a;
}
```

---

## 6. Responsividade

### Breakpoints de referência

| Faixa | Contexto |
|---|---|
| até 639px | celular |
| 640px–767px | celular grande / tablet estreito |
| 768px–1023px | tablet / desktop compacto |
| 1024px ou mais | desktop |

### Celular

- Layout em uma coluna.
- Respeitar `viewport-fit=cover` e safe areas.
- Botões e links de ação: alvo mínimo 44×44px (WCAG 2.5.8).
- Formulários longos agrupados por seção com títulos claros.
- Tabelas viram cards ou listas; overflow horizontal só quando comparação por coluna for essencial.
- Ações primárias próximas ao título ou ao conteúdo — nunca fixas cobrindo conteúdo.
- Scroll vertical aceitável; esconder campo crítico não é.

### Desktop

- Largura controlada para conteúdo operacional — não full-width desnecessário.
- Dashboards com grid responsivo.
- Listagens administrativas favorecendo comparação e escaneabilidade.
- Formulários podem usar duas colunas quando os campos tiverem relação clara.
- Tabelas financeiras permanecem como tabela quando comparação por coluna for essencial.

---

## 7. Tema claro e escuro

- `html[data-theme="light"]` aplica os tokens de `:root`.
- `html[data-theme="dark"]` sobrescreve com os tokens de modo escuro.
- O tema inicial deve respeitar `localStorage["lv-theme"]`.
- Na ausência de preferência salva, usar `prefers-color-scheme`.
- O botão de alternância de tema deve estar visível e acessível em toda tela.
- Todo componente usa tokens — sem cores soltas.
- Controles nativos respeitam `color-scheme`.

---

## 8. Papéis e permissões

| Tipo | Código | Papel de UI |
|---|---|---|
| Aluno | `student` | aulas, check-in, planos, materiais, graduação |
| Responsável | `guardian` | mensalidades, dependentes, materiais |
| Dependente | `dependent` | aulas, check-in, graduação (acesso de aluno dependente) |
| Professor | `instructor` | painel docente, aprovação de check-in, cronograma, alunos, financeiro próprio |
| Administrativo | `administrative-assistant` | gestão completa, financeiro, cadastros, estoque, planos |
| Admin técnico | sessão Django | acesso ao painel master e Django Admin |

Flags reais no request (via middleware):
- `request.portal_is_technical_admin`
- `request.portal_is_administrative`
- `request.portal_is_instructor`
- `request.portal_is_student`
- `request.portal_type_codes`
- `PortalRoleRequiredMixin.allowed_codes`

---

## 9. Inventário de telas

### 9.1 Autenticação (escopo inicial)

| Template | Rota | View | Status |
|---|---|---|---|
| `login/login_form.html` | `GET/POST /login/` | `PortalLoginView` | **implementado** (PRD-030) |
| `login/password_reset_form.html` | `GET/POST /password-reset/` | `PortalPasswordResetView` | pendente |
| `login/password_reset_done.html` | `GET /password-reset/done/` | `PortalPasswordResetDoneView` | pendente |
| `login/password_reset_confirm.html` | `GET/POST /reset/<token>/` | `PortalPasswordResetConfirmView` | pendente |
| `login/password_reset_complete.html` | `GET /reset/done/` | `PortalPasswordResetCompleteView` | pendente |

### 9.2 Dashboards

| Template | Rota | View | Status |
|---|---|---|---|
| `home/admin/dashboard.html` | `GET /home/admin/` | `AdminHomeView` | pendente |
| `home/administrative/dashboard.html` | `GET /home/administrative/` | `AdministrativeHomeView` | pendente |
| `home/instructor/dashboard.html` | `GET /home/instructor/` | `InstructorHomeView` | pendente |
| `home/student/dashboard.html` | `GET /home/student/` | `StudentHomeView` | pendente |

### 9.3 Demais módulos (rotas removidas da fase 1 — readicionadas conforme PRDs)

- Pessoas, Tipos de pessoa
- Categorias de turma, Turmas, Horários
- Planos, Troca de plano
- Financeiro, Repasses, Filas de pagamento
- Materiais, Loja, Histórico de pedidos
- Graduação, Faixas, Regras
- Calendário (aluno, professor, admin)
- Cadastro público (wizard)
- Webhooks (Stripe, Asaas)

---

## 10. Componentes mínimos obrigatórios

### Shell global (a implementar)

- `base.html` — shell padrão das telas autenticadas.
- Topbar com: logo LV, nome do portal, menu do usuário, alternância de tema.
- Drawer/sidebar refletindo permissões reais — nunca mostra link inacessível.
- Telas de autenticação são standalone (não herdam `base.html`), mas compartilham tokens e tema.

### Cabeçalho de tela operacional

Toda tela operacional deve ter:
- Eyebrow curto (contexto/módulo).
- Título objetivo.
- Subtítulo apenas quando informar estado ou contexto real.
- Ação primária quando houver.
- Navegação de volta consistente.

### Formulários

- Label visível associada por `for`/`id`.
- Erro por campo abaixo do campo.
- Erros não-campo acima dos campos com `role="alert"`.
- Help text quando necessário.
- `{% csrf_token %}` em todo POST.
- Botão Cancelar e Salvar quando aplicável.
- Agrupamento por domínio quando houver muitos campos.
- Foco visível em todos os controles (`:focus-visible`).

### Listas CRUD

- Filtros antes dos resultados.
- Estado vazio com próxima ação.
- Badge de status.
- Ações: visualizar, editar, excluir (quando permitidas).
- Ação destrutiva nunca como destaque primário.

---

## 11. Regras de implementação

- Toda tela nova ou reimplementada exige PRD ou item explícito em PRD.
- Ler integralmente view, form, model, service, template, CSS, JS e testes antes de editar.
- Novos arquivos criados apenas dentro de pastas já existentes em `templates/` e `static/`.
- `staticfiles/` é saída gerada — nunca editar.
- Atualizar `?v=N` de assets alterados.
- CSS entra em `static/system/css/<modulo>/`.
- JS entra em `static/system/js/<modulo>/`.
- `innerHTML` com dados do usuário é proibido — usar `textContent` ou criação de elementos.
- JS inline no template é proibido, salvo dados JSON seguros em `<script type="application/json">`.

---

## 12. Validação obrigatória por tela

Antes de concluir qualquer tela:

- `manage.py check` — 0 issues.
- `manage.py test --verbosity 2` — 0 falhas.
- `manage.py collectstatic --noinput` — sem erro.
- Rota GET renderiza sem erro 500.
- Fluxo POST preservado quando aplicável.
- Validação visual desktop.
- Validação visual mobile.
- Console do navegador sem erro crítico.
- Terminal sem stack trace.
- Tema claro e escuro verificados.
- Estado vazio e estado com dados verificados.
- Permissão: ao menos um perfil permitido e um bloqueado testados quando aplicável.

---

## 13. Critério de parada

Parar e solicitar decisão do usuário quando:

- A tela atual não tiver comportamento claro no código.
- Houver divergência entre PRD, `CLAUDE.md`, `AGENTS.md` e código real.
- Uma funcionalidade existente parecer quebrada e a solução exigir mudança de regra de negócio.
- O redesign exigir nova migração.
- Uma ação existente não puder ser preservada sem decisão de produto.
- A validação visual ou funcional estiver bloqueada.

---

## 14. Changelog

```
[2026-05-17] UI-SCREEN-CONTRACT reescrito do zero após deleção completa de templates e assets.
             Novo contrato parte do inventário real de telas a partir do zero.
             Login implementado como primeira tela (PRD-030).
             Tokens CSS redefinidos. Inventário de módulos mapeado com status explícito.
```
