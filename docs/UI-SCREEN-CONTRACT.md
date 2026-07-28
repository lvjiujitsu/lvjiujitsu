# UI Screen Contract — LV JIU JITSU

Fonte de verdade de interface do LV JIU JITSU. Governa propósito, princípios,
tokens, responsividade, tema, estados, implementação e critério de parada.

Seções 1 a 8 são o núcleo normativo e têm redação comum. Da seção 9 em diante o
documento descreve este produto: identidade, papéis, telas, componentes,
padrões de interação e histórico.

## 1. Propósito

O LV JIU JITSU é o portal operacional de uma academia de jiu jitsu. A interface
serve rotinas reais: cadastro público, tatame, presença, cronograma, materiais,
planos, pagamentos, repasses e graduação. Aluno, responsável, professor e
administrativo trabalham na mesma superfície, que muda por permissão.

Toda tela nova ou reimplementada deriva deste contrato e de uma PRD específica.
A interface serve rotina real: precisa ser clara, confiável e rápida de operar
em celular e em computador, sem esconder campo, ação ou estado crítico. Tela
interna não vira landing page.

## 2. Fontes de verdade

| Assunto | Fonte |
|---|---|
| Protocolo de agente | `AGENTS.md` |
| Contexto factual do produto | `CLAUDE.md` |
| Ciclo de execução de uma demanda | `docs/AGENT-WORKFLOW.md` |
| Formato e numeração de PRD | `docs/PRD-STANDARD.md` |
| Contrato visual | este arquivo |
| Requisito de cada tela | PRD em `docs/prd/` |
| Comportamento real | `system/urls.py`, `system/views/`, `system/forms/`, `system/services/`, `system/selectors/`, `templates/`, `static/system/` |
| Identidade, paleta e breakpoints reais | seção 9 |
| Papéis e permissões | seção 10 |
| Inventário de telas | seção 11 |
| Componentes | seção 12 |
| Padrões de interação | seção 13 |

Nenhuma rota citada neste documento pode faltar em `system/urls.py`. Quando o
contrato divergir do código, o código vence e o contrato é corrigido na mesma
PRD.

## 3. Princípios obrigatórios

- Funcionalidade antes de estética.
- Mobile-first sem esconder ação crítica; desktop denso, escaneável e
  operacional.
- Tema claro e escuro presentes em toda tela alterada.
- Informação crítica visível antes de elemento decorativo.
- Formulário com validação server-side e erro visível por campo.
- Ação destrutiva visualmente distinta, nomeando o alvo, nunca como ação
  primária.
- Estado vazio com próxima ação clara.
- Componente reutilizável por token, não por exceção local.
- Nenhuma regra de negócio em template ou JavaScript: o frontend apresenta
  estado calculado pelo servidor.
- Estado nunca é comunicado apenas por cor.
- Dado do usuário nunca entra em `innerHTML`.
- Permissão é validada na view; esconder botão não é autorização.
- Nenhum KPI, card de métrica, contador agregado, gráfico ou resumo executivo
  é criado, reinserido ou preservado por inferência visual.

A regra anti-KPI merece a íntegra porque é a mais violada. "Entrar na tela",
"corrigir o funcionamento", "validar UI/UX", "padronizar hub", "modernizar
layout" ou "homologar" **não** autorizam adicionar, restaurar ou manter
totalizador, bloco de visão geral, contador agregado fora do contexto direto de
uma lista, gráfico, percentual, valor resumido, ranking, tendência ou qualquer
métrica derivada sem fonte explícita.

Um KPI só existe quando todos os itens abaixo estiverem presentes:

- pedido nominal na solicitação atual ou em PRD específica;
- pergunta de produto que o indicador responde;
- fonte de dados real — selector, service, query ou endpoint;
- regra de permissão para quem pode ver o dado;
- estados vazio, carregado e erro;
- teste ou validação ORM provando o cálculo;
- validação visual desktop e mobile quando o indicador aparecer na UI.

Contador contextual continua permitido: badge de quantidade de uma lista já
exibida faz parte da compreensão da seção e não autoriza bloco agregado. Se uma
tela antiga tiver indicador não solicitado e a tarefa for corrigir
comportamento ou padronizar UX, o indicador é removido ou fica fora do escopo
até haver decisão de produto — nunca é preservado por inferência.

## 4. Tokens CSS obrigatórios

Todo componente usa token. Cor, sombra e borda literais só são aceitas na
definição do próprio token; fora dali, usa-se a variável. Valor local em
componente exige justificativa na PRD da tela.

**O nome do token é padronizado; o valor pertence à identidade do produto.** Um
papel tem um nome só, igual em qualquer projeto deste eixo: quem lê
`var(--surface)` sabe o que é sem abrir a paleta. A seção 9 declara o valor de
cada token neste projeto.

| Papel | Token | Presença | O que resolve |
|---|---|---|---|
| Fundo da página | `--bg` | obrigatório | plano de fundo fora dos painéis |
| Painel | `--panel` | obrigatório | superfície de card, painel e modal |
| Superfície embutida | `--surface` | obrigatório | área dentro de um painel |
| Superfície discreta | `--surface-soft` | condicional | segundo nível de embutimento |
| Borda e divisor | `--border` | obrigatório | contorno, separador e linha de tabela |
| Divisor discreto | `--border-soft` | condicional | separador de baixa ênfase |
| Texto principal | `--text` | obrigatório | título, rótulo e valor |
| Texto secundário | `--muted` | obrigatório | metadado, ajuda, placeholder e legenda |
| Acento de marca | `--accent` | obrigatório | ação primária, seleção e progresso |
| Acento em ênfase | `--accent-strong` | condicional | `hover` e estado ativo da ação primária |
| Acento em fundo | `--accent-muted` | condicional | preenchimento de chip e destaque suave |
| Acento secundário | `--accent-secondary` | condicional | informação e navegação contextual |
| Perigo | `--danger` | obrigatório | ação destrutiva e erro de campo |
| Foco visível | `--focus-ring` | obrigatório | anel de `:focus-visible` em todo controle |
| Sucesso | `--success` | condicional | confirmação de ação concluída |
| Alerta | `--warning` | condicional | pendência, prazo e atenção |
| Informação | `--info` | condicional | aviso neutro |
| Campo de entrada | `--input-bg` | condicional | fundo de `input`, `select` e `textarea` |
| Sombra e elevação | `--card-shadow` | condicional | destacar painel sobre o fundo |

Cada papel condicional aceita a variante `-muted` para o mesmo tom em fundo:
`--danger-muted`, `--success-muted`, `--warning-muted`, `--info-muted`.

Papel condicional existe quando o produto usa o estado correspondente; papel
obrigatório sem token declarado é lacuna registrada em PRD, não licença para
valor local. Componente novo reutiliza token existente antes de criar valor.

**Família de componente** usa prefixo próprio e segue o mesmo vocabulário:
`--<familia>-text`, `--<familia>-border`, `--<familia>-surface`. Nunca
`--<familia>-ink` nem `--<familia>-line`.

Token usado sem declaração é defeito: `var()` sem valor não falha, cai no valor
inicial e o desvio passa despercebido. A checagem é fazer o browser listar todo
token usado nas folhas carregadas e conferir que cada um resolve.

**Uma folha declara o núcleo: `static/system/css/theme.css`.** Ela é a primeira
folha do `<head>` de todo template que abre documento, declara `color-scheme` e
os tokens da tabela acima nos dois temas, e nenhuma outra folha os redeclara em
nível de tema. Folha de página declara apenas a família de prefixo próprio.

Redeclarar o núcleo em duas folhas produz duas paletas que divergem em silêncio:
a que vence depende da ordem de carga, e a página que carrega só uma delas fica
sem os papéis que a outra declarava. Override escopado a componente
(`.header .theme-toggle { --text: ... }`) continua válido — o que a regra proíbe
é a segunda declaração em `:root` ou em `html[data-theme=...]`.

**Propriedade customizada nunca referencia a si mesma.** `--accent: var(--accent)`
é ciclo: a propriedade fica inválida no tempo de valor computado e todo consumidor
cai no herdado. Renomear alias para o nome do alvo cria esse ciclo — ao colapsar
`--card-bg: var(--panel)` em `--panel`, a declaração inteira sai.
## 5. Responsividade

Faixas de referência, comuns aos três contextos de uso:

| Faixa | Contexto |
|---|---|
| até 639px | celular |
| 640px a 767px | celular grande ou tablet estreito |
| 768px a 1023px | tablet ou desktop compacto |
| 1024px ou mais | desktop |

Os breakpoints efetivamente escritos nas folhas deste projeto estão na seção 9.

### Celular

- Layout em uma coluna.
- `viewport-fit=cover` e safe areas respeitados.
- Alvo de toque de no mínimo 44 por 44 pixels (WCAG 2.5.8).
- Formulário longo agrupado por domínio, com título de seção.
- Tabela vira card ou lista; overflow horizontal só quando a comparação por
  coluna for essencial, e sempre dentro do wrapper da tabela, nunca no
  documento.
- Ação primária próxima ao título ou ao conteúdo que afeta, nunca fixa cobrindo
  conteúdo.
- Campo obrigatório, erro, status e link de continuidade nunca são escondidos:
  scroll vertical é aceitável, ocultar não é.

### Desktop

- Largura controlada para conteúdo operacional, sem full-width desnecessário.
- Grid responsivo e leitura em padrão F nas listagens.
- Listagem administrativa favorece comparação e escaneabilidade.
- Formulário pode usar duas colunas quando os campos tiverem relação clara.
- Progresso, status e ação permanecem visíveis sem poluir o painel.

### Acessibilidade mínima

- Label visível associada por `for`/`id` em todo campo.
- Erro não-campo acima dos campos, com `role="alert"`.
- Foco visível em todo controle, nos dois temas.
- Contraste WCAG AA nos dois temas.
- Imagem informativa com `alt` descritivo; imagem decorativa recebe `alt=""`.
- Estado sempre com uma segunda pista além da cor.
- Conteúdo interativo que não é navegável por leitor de tela tem alternativa
  textual equivalente, declarada na seção 13.

## 6. Tema claro e escuro

- `html[data-theme="light"]` e `html[data-theme="dark"]` selecionam o conjunto
  de tokens; nenhum componente escolhe cor fora deles.
- O tema inicial respeita a chave de preferência declarada na seção 9; na
  ausência de preferência salva, `prefers-color-scheme`.
- O alternador de tema fica visível e acessível em toda tela alterada.
- Toda cor nova precisa de valor nos dois temas. Contraste ou foco quebrado em
  um deles é defeito, não detalhe.
- Os dois temas preservam a mesma hierarquia e a mesma semântica de estado.
- Controles nativos respeitam `color-scheme`.
- `@media (prefers-reduced-motion: reduce)` suprime transição e animação
  decorativas.

## 7. Estados obrigatórios e hierarquia visual

### 7.1 Hierarquia

A hierarquia comunica importância antes da leitura. Tela sem hierarquia obriga
o usuário a farejar o conteúdo — custo cognitivo evitável.

| Nível | Elemento | Peso | Papel de token |
|---|---|---|---|
| 1 | título de tela | 700 a 800 | texto principal |
| 2 | seção ou grupo | 600 | texto principal |
| 3 | campo ou item | 400 a 500 | texto principal |
| 4 | ajuda ou hint | 400 | texto secundário |
| 5 | placeholder | 400 | texto secundário com opacidade |

- O acento de marca é acento, nunca base de texto corrido.
- O token de texto secundário é reservado a metadado, não a informação
  principal.
- Peso 300 ou inferior é proibido em texto funcional.
- Tamanho mínimo de corpo em celular: 14px.
- Padrão F em dashboard e listagem; padrão Z em acesso, confirmação e fluxo
  curto.

### 7.2 Proximidade

- Campos do mesmo grupo com `gap` de 8 a 12px; grupos separados por 20 a 28px
  ou por divisor.
- Rótulo e campo com 4 a 6px, nunca mais de 8px.
- Botão adjacente ao conteúdo que afeta.
- Em card, dado descritivo fica junto; ação fica em bloco separado.

### 7.3 Affordance e feedback

- Botão primário com fundo sólido, peso 600 e foco visível.
- Botão secundário com borda visível ou fundo distinto do painel.
- Link acionável com cor distinta ou sublinhado; nunca `cursor: pointer`
  invisível.
- Pill ou chip selecionado com borda e fundo de acento e peso 600.
- Estados interativos obrigatórios: `default`, `hover`, `focus-visible`,
  `active` e `disabled`.
- `disabled` usa opacidade 0.45 e `cursor: not-allowed`; o elemento não some.
- Submissão assíncrona exibe estado intermediário e bloqueia reenvio.
- Erro de campo aparece abaixo do campo, com o token de perigo.
- Sucesso e erro de ação crítica são persistentes, não toast efêmero.

### 7.4 Máquinas de estado

Todo componente interativo é uma máquina de estados; renderizar o estado errado
é defeito funcional, não detalhe visual.

| Componente | Estados obrigatórios |
|---|---|
| Formulário | `idle` → `dirty` → `submitting` → `success` ou `error` |
| Botão de ação | `default` → `loading` → `success`, `error` ou `disabled` |
| Lista ou tabela | `loading` → `empty`, `populated` ou `error` |
| Modal ou dialog | `closed` → `opening` → `open` → `closing` |
| Pill de seleção | `unselected` → `selected` → `disabled` |
| Step wizard | `pending` → `active` → `complete` → `error` |
| Upload | `idle` → `selecting` → `uploading` → `success` ou `error` |

Cada estado tem representação visual distinta. Estado `error` nunca é
silencioso: diz o que falhou e o que o usuário pode fazer.

### 7.5 Exigência por estado

| Estado | Exigência |
|---|---|
| Vazio | texto que explica o que falta e qual é a próxima ação; nunca tabela em branco |
| Carregando | indicação visível acima de ~300ms; o controle que dispara fica `disabled` |
| Erro | mensagem em pt-BR dizendo o que aconteceu e o que fazer; erro de campo fica no campo |
| Sucesso | confirmação que sobrevive a recarregar — rota própria ou mensagem persistida |

## 8. Regras de implementação, validação e critério de parada

### 8.1 Implementação

- Toda tela nova ou reimplementada exige PRD ou item explícito em PRD.
- Ler integralmente view, form, model, service, selector, template, CSS, JS e
  testes antes de editar.
- Arquivo novo só dentro de pasta já existente em `templates/` e `static/`.
- CSS e JS editáveis vivem em `static/system/`; `staticfiles/` é saída de
  `collectstatic` e nunca é editado à mão.
- `innerHTML` com dado do usuário é proibido: usar `textContent` ou criação de
  elemento.
- JS inline em template é proibido, salvo dado JSON seguro em
  `<script type="application/json">` ou `json_script`.
- Estilo inline existente é removido quando a tela entra no escopo de uma PRD.
- Template apenas apresenta dado preparado pelo backend; view fina, negócio em
  `services/`, leitura em `selectors/`, sem query dentro de laço.
- POST usa CSRF e validação server-side.
- Nome de classe segue a convenção já existente na folha da superfície, sem
  introduzir segunda nomenclatura.

### 8.2 Design antes do código

Mudança visual relevante registra na PRD, antes da implementação:

1. objetivo e comportamento que deve ser preservado;
2. hierarquia visual ou wireframe, desktop e mobile;
3. máquina de estados: feliz, vazio, carregando, erro e limite aplicáveis;
4. papéis e permissões envolvidos;
5. temas, acessibilidade e evidência esperada.

O wireframe usa a estrutura abaixo e é pré-requisito de implementação, não
substituto da validação no navegador:

```md
## Wireframe

### Região: Topo
- Eyebrow: <módulo>
- Título: <objetivo da tela>
- Ação primária: <botão>

### Região: Conteúdo principal
- Grupo A: <nome> — campos: <lista>
- Grupo B: <nome> — campos: <lista>

### Região: Rodapé / ações
- Cancelar
- Salvar

### Estados da tela
- Carregando
- Vazio
- Com dados
- Erro
```

Correção pontual de espaçamento, cor ou texto não exige as cinco etapas;
redesenho de superfície exige.

### 8.3 Validação obrigatória

| Item | Como |
|---|---|
| Rota real | abrir a URL no navegador, imediatamente após implementar; não inferir do template |
| Desktop | viewport de desktop, caminho feliz e um edge case |
| Mobile | viewport estreito, mesmo roteiro |
| Temas | claro e escuro, verificando contraste e foco |
| Estados | vazio e com dados |
| Permissão | ao menos um perfil permitido e um bloqueado, quando aplicável |
| Console | sem erro crítico no console do navegador |
| Terminal | sem stack trace no servidor durante o roteiro |
| Django | `manage.py check` sem issue |
| Estáticos | `manage.py collectstatic --noinput` sem erro quando houver estático |
| Teste | escrito no ciclo TDD quando houver comportamento testável e executado quando proporcional ao escopo |
| Screenshot | desktop e mobile, com caminho registrado na PRD |

Não declarar Red, Green, ausência de regressão ou validação visual sem saída
real de comando ou evidência de navegador. Leitura de template e teste
automatizado não substituem a rota aberta.

**"Implementado" não significa "validado".** Sem execução observável, o item
vai para `Pending` na PRD, nunca para `Evidence`.

### 8.4 Critério de parada

Parar e pedir decisão do operador quando:

- a tela atual não tiver comportamento claro no código;
- houver divergência entre PRD, `CLAUDE.md`, `AGENTS.md` e código real;
- uma funcionalidade existente parecer quebrada e a correção exigir mudança de
  regra de negócio;
- o redesenho exigir nova migration;
- uma ação existente não puder ser preservada sem decisão de produto;
- a validação visual ou funcional estiver bloqueada;
- uma etapa exigir dado real de Render ou Supabase que não existe no
  repositório.

Encerrar quando o roteiro estiver completo e a evidência registrada na PRD.
Navegador indisponível, console com erro crítico ou screenshot ausente
significam validação incompleta: registrar a limitação e o status real, nunca
declarar a rota validada.

## 9. Identidade visual

### 9.1 Linguagem visual

A interface carrega a identidade de tatame, disciplina e cultura marcial com
uma camada administrativa sóbria.

**Usar:**
- Preto, grafite, branco, prata e cinzas neutros como base.
- Vermelho LV como acento de ação, risco, destaque ou progresso — nunca como
  fundo dominante de toda a tela.
- Tipografia forte em títulos, compacta em painéis operacionais.
- Iconografia simples para ações reconhecíveis.
- Logo LV visível e em destaque nas telas de acesso público.

**Evitar:**
- Gradientes roxos ou azuis genéricos.
- Painéis gigantes que empurram trabalho para fora da primeira tela.
- Cards aninhados dentro de cards.
- Decoração sem função.
- Texto explicando como usar a interface dentro da própria tela.

Assets de identidade: `static/system/img/`.

Tipografia operacional: além do mínimo de 14px em celular exigido pelo núcleo,
o desktop usa 13px em tela operacional densa e 15px em formulário público, onde
o usuário não tem treino no sistema.

### 9.2 Token por papel

| Papel | Token |
|---|---|
| Fundo da página | `--bg` |
| Painel | `--panel` |
| Superfície secundária | `--surface`, `--surface-soft`, `--input-bg` |
| Borda e divisor | `--border`, `--border-soft` |
| Texto principal | `--text` |
| Texto secundário | `--muted` |
| Acento de marca | `--brand-red`, `--brand-red-strong`, `--brand-red-muted` |
| Perigo | `--danger`, `--danger-muted` |
| Foco visível | `--focus-ring` |
| Sucesso | `--success`, `--success-muted` |
| Alerta | `--warning`, `--warning-muted` |
| Informação | `--info`, `--info-muted` |
| Sombra e elevação | `--shadow`, `--card-shadow`, `--card-shadow-hover` |
| Painel de marca | `--brand-panel-*` e o conjunto `--auth-*` nas telas de acesso |

### 9.3 Paleta concreta

```css
:root {
  --bg: #f4f4f5;
  --panel: #ffffff;
  --surface: #f9f9fb;
  --surface-soft: #f0f0f2;

  --border: #e4e4e7;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.08);

  --text: #18181b;
  --muted: #71717a;

  --brand-red: #c41230;
  --brand-red-strong: #9b0e25;
  --brand-red-muted: rgba(196, 18, 48, 0.12);

  --focus-ring: rgba(196, 18, 48, 0.35);

  --danger: #dc2626;
  --danger-muted: rgba(220, 38, 38, 0.1);
  --success: #16a34a;
  --warning: #d97706;
  --info: #2563eb;

  --brand-panel-bg: #0f0f0f;
  --brand-panel-text: #f4f4f5;
  --brand-panel-muted: #a1a1aa;
}

html[data-theme="dark"] {
  --bg: #09090b;
  --panel: #18181b;
  --surface: #1f1f23;
  --surface-soft: #27272a;

  --border: #3f3f46;
  --shadow: 0 1px 4px rgba(0, 0, 0, 0.4);

  --text: #fafafa;
  --muted: #a1a1aa;

  --brand-red: #e02244;
  --brand-red-strong: #c41230;
  --brand-red-muted: rgba(224, 34, 68, 0.15);

  --focus-ring: rgba(224, 34, 68, 0.4);

  --danger: #f87171;
  --danger-muted: rgba(248, 113, 113, 0.12);
  --success: #4ade80;
  --warning: #fbbf24;
  --info: #60a5fa;

  --brand-panel-bg: #000000;
  --brand-panel-text: #fafafa;
  --brand-panel-muted: #71717a;
}
```

`:root` define o tema claro; `html[data-theme="dark"]` sobrescreve.

### 9.4 Tema e breakpoints reais

A chave de preferência é `lv-theme` no `localStorage`, aplicada por
`static/system/js/lv/theme_boot.js` antes da pintura e alternada por
`theme_toggle.js`. Sem preferência salva, vale `prefers-color-scheme`.

As folhas são mobile-first: a maioria das regras cresce por `min-width`
(`480px`, `600px`, `640px`, `720px`, `768px`, `900px`), e o corte descendente
aparece em `max-width` de `479px`, `520px`, `639px` e `640px`. Um único corte
de tela larga usa `min-width: 1600px`.

## 10. Papéis e permissões

| Tipo | Código | Papel de UI |
|---|---|---|
| Aluno | `student` | aulas, check-in, planos, materiais, graduação |
| Responsável | `guardian` | mensalidades, dependentes, materiais |
| Dependente | `dependent` | aulas, check-in, graduação (acesso de aluno dependente) |
| Professor | `instructor` | painel docente, aprovação de check-in, cronograma, alunos, financeiro próprio |
| Administrativo | `administrative-assistant` | gestão completa, financeiro, cadastros, estoque, planos |
| Admin técnico | sessão Django | painel master e Django Admin |

Flags reais no request, via middleware:

- `request.portal_is_technical_admin`
- `request.portal_is_administrative`
- `request.portal_is_instructor`
- `request.portal_is_student`
- `request.portal_type_codes`
- `PortalRoleRequiredMixin.allowed_codes`

Papel acumulável é a regra, não a exceção: a mesma pessoa pode ser aluno e
professor. A UI reflete a união dos papéis; a view valida cada um.

## 11. Inventário de telas

### 11.1 Autenticação

| Template | Rota | View | Status |
|---|---|---|---|
| `login/login_form.html` | `GET/POST /login/` | `PortalLoginView` | implementado (PRD-030) |
| `login/password_reset_form.html` | `GET/POST /password-reset/` | `PortalPasswordResetView` | implementado |
| `login/password_reset_done.html` | `GET /password-reset/done/` | `PortalPasswordResetDoneView` | implementado |
| `login/password_reset_confirm.html` | `GET/POST /reset/<token>/` | `PortalPasswordResetConfirmView` | implementado |
| `login/password_reset_complete.html` | `GET /reset/done/` | `PortalPasswordResetCompleteView` | implementado |

### 11.2 Home unificada

A home é uma única superfície por permissão (PRD-043), não um dashboard por
papel.

| Template | Rota | View | Status |
|---|---|---|---|
| `home/dashboard.html` | `GET /home/` | `HomeView` | implementado — o contexto varia por papel (`portal_is_technical_admin`, `portal_is_administrative`, `portal_is_instructor`, `portal_is_student`) dentro da mesma tela |
| — | `GET /dashboard/` | `DashboardRedirectView` | redireciona para `/home/` pós-login |

### 11.3 Módulos operacionais

As rotas canônicas são em inglês e cada uma tem alias pt-BR que redireciona:

| Módulo | Rota canônica | Alias |
|---|---|---|
| Pessoas e tipos de pessoa | `/people/` | `/pessoas/` |
| Turmas, categorias e horários | `/classes/` | `/turmas/`, `/aulas/` |
| Planos, tiers e preços | `/plans/`, `/plan-tiers/`, `/plan-prices/` | `/planos/` |
| Financeiro e repasses | `/financial/` | `/financeiro/` |
| Materiais, loja e pedidos | `/materials/`, `/store/`, `/my-materials/` | `/materiais/`, `/loja/`, `/meus-materiais/` |
| Graduação | `/graduation/` | `/graduacao/` |
| Calendário e cronograma | `/calendar/` | `/cronograma/` |
| Administração e auditoria | `/administration/` | `/administracao/` |
| Solicitações (acesso, turmas, pausas) | `/requests/` | — |
| Cadastro público | `/register/` | `/cadastro/` |
| Mensalidade do cliente | `/minha-mensalidade/` | — |
| Pagamentos e webhooks | `/pagamentos/` | — |
| Health check | `/health/` | — |

### 11.4 Contrato do wizard público — `/register/`

- Aluno e responsável seguem para plano e pagamento; `Person` e contas só são
  ativados depois da confirmação e da finalização.
- Administrativo e professor encerram com solicitação pendente, sem criar
  `Person`.
- A aprovação administrativa cria o perfil e os papéis autorizados.
- A aprovação da proposta de professor cria professor, turma/horários e dados
  de recebimento informados na solicitação.
- Snapshots em estado terminal não conservam senhas em texto puro.

## 12. Componentes

### 12.1 Shell global

`templates/lv/base.html` com blocos `title`, `extra_css`, `body_class`,
`topbar`, `page_class`, `content`, `modals` e `extra_js`. Inclui favicon, meta
viewport, `theme_boot.js`, `modal.js`, `theme_toggle.js` e mensagens do
sistema.

- **`lv/base.html`** — 52 telas administrativas, mais calendário e pessoas.
- **Standalone operacionais** — `home/dashboard.html`, `login/register.html` e
  o wizard de dependente; tokens via `lv/base.css` mais overrides.
- **Auth** — `{% extends "auth/base_auth.html" %}`.
- **Modal CRUD** — `lv/modal_frame.html` + `crud_modal.js`; a home usa
  `dashboard_modals.html` + `dashboard_modals.js`.
- **DOM seguro** — wizards e dashboard sem `.innerHTML`;
  `static/system/js/lv/dom_utils.js` (`LV.DOM`).
- Topbar com logo LV, nome do portal, menu do usuário e alternância de tema.
- Drawer ou sidebar refletindo permissões reais — nunca mostra link
  inacessível.
- Telas de autenticação são standalone e não herdam `base.html`, mas
  compartilham tokens e tema.
- Atualizar `?v=N` de asset alterado.
- CSS em `static/system/css/<modulo>/`; JS em `static/system/js/<modulo>/`.

### 12.2 Cabeçalho de tela operacional

Toda tela operacional tem eyebrow curto de contexto ou módulo, título objetivo,
subtítulo apenas quando informar estado ou contexto real, ação primária quando
houver e navegação de volta consistente.

### 12.3 Formulários

- Label visível associada por `for`/`id`.
- Erro por campo abaixo do campo; erros não-campo acima, com `role="alert"`.
- Help text quando necessário.
- `{% csrf_token %}` em todo POST.
- Botão Cancelar e Salvar quando aplicável.
- Agrupamento por domínio quando houver muitos campos.
- Foco visível em todos os controles (`:focus-visible`).

### 12.4 Listas CRUD

- Filtros antes dos resultados.
- Estado vazio com próxima ação.
- Badge de status.
- Ações visualizar, editar e excluir quando permitidas, em ícone
  (`.icon-action`) conforme a seção 13.1.
- Ação destrutiva nunca como destaque primário.

## 13. Padrões de interação

### 13.1 CRUD operacional em modal/dialog

Aplica-se a todos os hubs e listagens operacionais do LV.

**Regra geral**
- Ações curtas de criar, editar, visualizar e excluir em hub ou listagem
  acontecem por modal/dialog na própria tela, sem trocar de superfície.
- Navegação para outra tela só ocorre em mudança real de superfície: listagem
  completa, configuração, detalhe rico ou wizard justificado por PRD.
- O card de listagem expõe **ações icônicas** (`.icon-action`) — no mínimo
  visualizar (`--view`), editar (`--edit`) e excluir (`--delete`) —
  respeitando permissões no backend.

**Implementação**
- Modal é um `<dialog class="crud-modal">` com `.crud-modal__header` (eyebrow,
  título e botão `.crud-modal__close` 44×44) e corpo iframe
  (`.crud-modal__frame`) ou `.crud-modal__body` para formulário curto.
- Conteúdo server-rendered: criar, editar e visualizar carregam a rota com
  `?modal=1`; o controlador `static/system/js/lv/crud_modal.js` abre o iframe e
  `static/system/js/lv/modal_child.js` sincroniza o tema (via `theme_boot.js`)
  e sinaliza conclusão por `postMessage`.
- GET de rota antiga de popup redireciona para a superfície principal com o
  modal aberto por estado previsível (query).
- POST inválido re-renderiza a superfície principal com o modal aberto e erros
  por campo.
- Excluir usa diálogo de confirmação
  (`static/system/js/lv/confirm_delete.js`, `data-confirm-submit`) e trata
  `ProtectedError` com mensagem por vínculo.

**Estados**
- CRUD modal: `closed` → `open` → `submitting` → `success` ou `error`.
- Diálogo destrutivo: `closed` → `confirmable` → `submitting` → `success` ou
  `error`.

**Fundação compartilhada real** (não é um `base.html` único; ver seção 12.1)
- `templates/lv/modal_frame.html`, `templates/lv/modal_done.html`.
- `static/system/css/lv/base.css` — tokens, shell, componentes, ações icônicas
  e modal CRUD.
- `static/system/js/lv/theme_boot.js`, `theme_toggle.js`, `crud_modal.js`,
  `modal_child.js`, `confirm_delete.js`.
- Sem CSS ou JS inline de comportamento nas telas que já usam
  `lv/modal_frame.html`; standalones ainda têm IIFE de tema inline (débito
  PRD-141 M-01).

**Validação**
- Desktop e mobile sem overflow horizontal; tema claro e escuro corretos;
  console sem erro crítico; modal abre e fecha por botão, backdrop e Esc.

### 13.2 Componentes de seleção da loja

A loja de materiais tem affordance própria, porque o usuário escolhe variação
com estoque real:

- Pill de cor exibe a cor como fundo ou círculo colorido — nunca só texto.
- Pill de tamanho exibe o estoque disponível abaixo do rótulo quando relevante.
- Pill sem estoque usa `opacity: 0.4`, linha diagonal CSS opcional e
  `cursor: not-allowed`.
- Pill selecionado usa borda `--brand-red`, fundo `--brand-red-muted` e peso
  600.

### 13.3 Wireframe antes da tela

Tela nova ou redesenho relevante segue o processo mínimo:

1. **Wireframe de baixa fidelidade** — estrutura, hierarquia, agrupamentos e
   fluxo de estados. Sem cor, sem ícone.
2. **Revisão** com o operador ou representante de produto.
3. **Mockup de referência** — tokens aplicados, estados principais, responsivo.
4. **Implementação** — derivada do mockup, não do achismo.

A seção `## Wireframe` da PRD, no formato da seção 8.2, pode ser usada como
prompt para ferramenta de geração de wireframe. O wireframe é pré-requisito de
implementação, nunca substituto da validação no navegador.

Prompts de referência para descrever hierarquia e agrupamento na PRD:

> "Organize o layout seguindo o padrão F: título e resumo no topo, listagem
> densa com identificador à esquerda, status ao centro, ações à direita."

> "Use hierarquia tipográfica de 3 níveis: título em 700, rótulos de campo em
> 500, valores e help text em 400 com `--muted`."

> "Agrupe os campos de endereço (CEP, logradouro, número, complemento, cidade,
> estado) em um bloco com `gap: 10px` interno, separado do bloco de contato por
> um divisor ou título de seção."

### 13.4 Máquinas de estado na PRD

PRD de tela com componente interativo inclui:

```md
## Máquinas de estado
### <Nome do componente>
- Estados: <lista>
- Transições: <diagrama ou tabela>
- Representação visual: <descrição ou mockup>
```

Componente de wizard tem estado explícito por etapa; etapas anteriores
permanecem navegáveis, salvo regra de negócio que impeça.

## 14. Changelog

```md
- [2026-07-26] PRD-173: documento reestruturado em núcleo normativo (seções 1 a
  8) e cauda de produto (seções 9 a 14). Tokens passam a ser declarados por
  papel, com a paleta concreta na seção 9; a antiga §15.7 (anti-KPI) foi
  absorvida pelo núcleo, §15.6 virou §13.1, e a numeração duplicada de §14/§15
  foi desfeita.
- [2026-07-13] PRD-145: contrato terminal do wizard público documentado para aluno, responsável, administrativo e professor; snapshots terminais não podem conservar senhas em texto puro.
- [2026-07-09] PRD-141 Onda P0 implementada: `templates/lv/base.html` criado (shell único com blocos title/extra_css/topbar/content/modals/extra_js); piloto em `templates/people/person_list.html` e `templates/calendar/calendar.html` (zero diff visual, validado desktop/mobile/tema claro-escuro). `|safe` em JSON substituído por `json_script` em `register.html`/`dependent_registration.html` (C-05). `?v=` de `theme_boot.js`/`theme_toggle.js`/`crud_modal.js` normalizado para `20260709-1` em todos os 44 templates que os referenciam (M-02/M-03).
- [2026-07-09] Correção pós-auditoria PRD-138/139/141 (Onda 0, sem mudança de código): password reset marcado implementado; inventário reescrito para a home unificada `/home/` (PRD-043), já que dashboards por papel nunca existiram como rotas separadas; nomes reais dos arquivos de shell corrigidos para `templates/lv/modal_frame.html` e `static/system/js/lv/{theme_boot,theme_toggle,crud_modal,modal_child,confirm_delete}.js`.
- [2026-06-29] PRD-067: anti-KPI não solicitado; paridade de CSS de Pessoas (linhas, filtros 44px, responsividade mobile) e remoção da faixa de KPIs não solicitada do hub operacional.
- [2026-06-28] PRD-066: CRUD operacional em modal/dialog — ações icônicas, modal server-rendered e fundação compartilhada.
- [2026-05-20] Princípios de UX para interfaces geradas por IA: hierarquia visual, lei da proximidade, affordance e feedback, máquinas de estado e wireframes.
- [2026-05-17] Contrato reescrito do zero após deleção completa de templates e assets; inventário real de telas a partir do zero, login como primeira tela (PRD-030) e tokens redefinidos.
```
