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

## 15. Princípios de UX para interfaces geradas por IA

> Esta seção define os princípios cognitivos e de design que **toda interface gerada ou revisada por IA deve aplicar explicitamente**. Eles devem constar nos PRDs de tela como itens verificáveis.

---

### 15.1 Hierarquia Visual — Fontes, Pesos e Cores

A hierarquia visual comunica importância antes de o usuário ler.
Uma tela sem hierarquia obriga o usuário a "farejar" o conteúdo — custo cognitivo evitável.

**Regras obrigatórias:**

| Nível | Elemento | Peso sugerido | Token |
|---|---|---|---|
| 1 — Título de tela | `h1` | 700–800 | `--text` grande |
| 2 — Seção ou grupo | `h2`, label de grupo | 600 | `--text` |
| 3 — Campo ou item | `label`, texto de linha | 400–500 | `--text` |
| 4 — Ajuda, hint | `small`, help text | 400 | `--muted` |
| 5 — Placeholder | `placeholder` | 400 | `--muted` com opacidade |

- Vermelho (`--brand-red`) é acento — nunca base de texto corrido.
- `--muted` é reservado para metadados, não para informação principal.
- Peso 300 ou inferior é proibido em texto funcional.
- Tamanho mínimo de corpo em mobile: 14px. Em desktop: 13px operacional, 15px em formulário público.

**Padrões de leitura:**

- **F Pattern** — dashboards e listagens operacionais: informação crítica nas primeiras linhas, identificadores à esquerda, ações à direita.
- **Z Pattern** — telas de acesso e confirmação: atenção começa no canto superior esquerdo, cruza para o direito, desce em diagonal e termina na ação principal.

**Prompts para hierarquia (uso em PRDs):**

> "Organize o layout seguindo o padrão F: título e resumo no topo, listagem densa com identificador à esquerda, status ao centro, ações à direita."

> "Use hierarquia tipográfica de 3 níveis: título em 700, rótulos de campo em 500, valores e help text em 400 com `--muted`."

---

### 15.2 Lei da Proximidade — Gestalt

Elementos próximos são percebidos como grupo. Espaçamento comunica estrutura.

**Regras obrigatórias:**

- Campos do mesmo grupo visual têm espaçamento interno menor (`gap: 8–12px`) do que entre grupos (`gap: 20–28px`).
- Rótulo e campo: `margin-bottom: 4–6px` — nunca separados por mais de `8px`.
- Grupos de formulário separados por `border-top` + espaçamento, ou cabeçalho de seção.
- Botões de ação ficam adjacentes ao conteúdo que afetam — nunca soltos no rodapé sem relação visual clara.
- Em cards: dados descritivos do objeto ficam juntos; ações ficam num bloco separado (rodapé do card ou canto direito).

**Aplicação em prompts de PRD:**

> "Agrupe os campos de endereço (CEP, logradouro, número, complemento, cidade, estado) em um bloco com `gap: 10px` interno, separado do bloco de contato por um divisor ou título de seção."

---

### 15.3 Affordance e Feedback Visual

O usuário só clica onde percebe que pode clicar. Affordance é a pista visual de "isto é acionável".

**Regras obrigatórias:**

- Botões primários: fundo sólido, peso 600, padding generoso, `border-radius` consistente.
- Botões secundários: borda visível ou fundo distinto do painel — nunca igual ao fundo da tela.
- Links acionáveis: sublinhado ou cor distinta — nunca texto corrido com `cursor: pointer` invisível.
- Pills e chips de seleção: estado `--selected` com borda `--brand-red`, fundo `--brand-red-muted` e peso 600.
- Estados interativos obrigatórios: `default`, `hover`, `focus-visible`, `active`, `disabled`.
- `disabled`: opacidade 0.45 + `cursor: not-allowed` — nunca remover visualmente o elemento.
- Feedback imediato em ação: spinner ou mudança de label em submit, não aguardar resposta HTTP em silêncio.
- Erros de campo aparecem **abaixo do campo**, com cor `--danger`, ícone de aviso opcional.
- Sucesso de ação aparece em mensagem persistente (não toast efêmero para ação crítica).

**Affordance em componentes de seleção:**

- Pill de cor: exibe a cor como fundo ou círculo colorido — nunca só texto.
- Pill de tamanho: exibe estoque disponível abaixo do rótulo quando relevante.
- Pill desabilitado (sem estoque): `opacity: 0.4`, linha diagonal CSS opcional, `cursor: not-allowed`.

---

### 15.4 Máquinas de Estado em Componentes

Todo componente interativo é uma máquina de estados. Renderizar estado errado é um bug funcional.

**Estados mínimos a mapear por tipo:**

| Componente | Estados obrigatórios |
|---|---|
| Formulário | `idle` → `dirty` → `submitting` → `success` \| `error` |
| Botão de ação | `default` → `loading` → `success` \| `error` \| `disabled` |
| Lista/tabela | `loading` → `empty` \| `populated` \| `error` |
| Modal/drawer | `closed` → `opening` → `open` → `closing` |
| Pill de seleção | `unselected` → `selected` → `disabled` |
| Step wizard | `pending` → `active` → `complete` → `error` |
| Upload | `idle` → `selecting` → `uploading` → `success` \| `error` |

**Regras obrigatórias:**

- Cada estado deve ter representação visual distinta.
- Transições de estado não devem ser instantâneas em ações assíncronas — feedback intermediário obrigatório.
- Estado `error` nunca silencioso — sempre comunica o que falhou e o que o usuário pode fazer.
- Componentes de wizard: cada etapa tem estado explícito; etapas anteriores permanecem navegáveis salvo regra de negócio que impeça.

**Mapeamento em PRDs:**

Todo PRD de tela com componentes interativos deve incluir a seção:

```md
## Máquinas de estado
### <Nome do componente>
- Estados: <lista>
- Transições: <diagrama ou tabela>
- Representação visual: <descrição ou mockup>
```

---

### 15.5 Wireframes e UX Pilot

Wireframes são o alicerce de qualquer tela nova ou reimplementada. Sem wireframe aprovado, a implementação parte de premissas não validadas.

**Processo mínimo:**

1. **Wireframe de baixa fidelidade** — estrutura, hierarquia, agrupamentos, fluxo de estados. Sem cor, sem ícone.
2. **Revisão** com o usuário ou representante de produto.
3. **Mockup de referência** — tokens CSS aplicados, estados principais, responsivo.
4. **Implementação** — derivada do mockup, não do achismo.

**UX Pilot (ferramenta recomendada para PRDs com IA):**

Quando o PRD descrever uma tela nova ou redesign relevante, o agente deve:

- Incluir no PRD uma seção `## Wireframe` com descrição estruturada da tela em formato de lista hierárquica, cobrindo: regiões da tela, grupos de campo, ações e estados.
- A seção `## Wireframe` pode ser usada como prompt para ferramentas de geração de wireframe (UX Pilot, Figma AI, etc.).
- O wireframe não substitui a validação visual no navegador — é pré-requisito de implementação, não substituto.

**Template de wireframe para PRDs:**

```md
## Wireframe

### Região: Topo
- Eyebrow: <módulo>
- Título: <objetivo da tela>
- Ação primária: <botão> (alinhado à direita)

### Região: Conteúdo principal
- Grupo A: <nome> — campos: <lista>
- Grupo B: <nome> — campos: <lista>

### Região: Rodapé / ações
- Cancelar (secundário, esquerda)
- Salvar (primário, direita)

### Estados da tela
- Carregando: <descrição>
- Vazio: <descrição>
- Com dados: <descrição>
- Erro: <descrição>
```

---

## 14. Changelog

```
[2026-05-17] UI-SCREEN-CONTRACT reescrito do zero após deleção completa de templates e assets.
             Novo contrato parte do inventário real de telas a partir do zero.
             Login implementado como primeira tela (PRD-030).
             Tokens CSS redefinidos. Inventário de módulos mapeado com status explícito.
[2026-05-20] Adicionada Seção 15 — Princípios de UX para interfaces geradas por IA:
             15.1 Hierarquia Visual (Fontes, Pesos, Cores, F/Z Pattern, prompts para PRD).
             15.2 Lei da Proximidade — Gestalt (agrupamento, espaçamento, aplicação em prompts).
             15.3 Affordance e Feedback Visual (estados interativos, pills, erros, sucesso).
             15.4 Máquinas de Estado em Componentes (tabela por tipo, regras, template de PRD).
             15.5 Wireframes e UX Pilot (processo mínimo, template de wireframe para PRDs).
```
