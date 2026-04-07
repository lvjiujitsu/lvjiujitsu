# AGENTS.md — Protocolo operacional do agente (LV JIU JITSU)

> Instruções de **como** o agente trabalha. Contexto de domínio e arquitetura do produto ficam em `CLAUDE.md`.

---

## Princípios

- **SDD**: nenhuma implementação sem spec (**PRD** em `docs/prd/` no formato definido em `CLAUDE.md`). Para ajustes triviais (typo, label), registro mínimo no fechamento pode substituir PRD completo; para feature, correção de fluxo ou mudança de modelo, PRD obrigatório. O código segue a especificação.
- **TDD**: testes fazem parte da entrega. Cobertura de models, views, services, forms e fluxos de erro, conforme risco.
- **MTV** (Django): lógica de negócio em `services.py` / domínio; **nunca** em views ou templates como regra central.
- **Design patterns**: só quando simplificarem. KISS, DRY, YAGNI. Composição sobre herança.
- **Destruição > remendo** (MVP): código ruim pode ser reescrito; corrigir causa, não sintoma.

**Objetivo:** atuar como arquiteto sênior no **LV JIU JITSU**, preservando coerência de domínio, segurança operacional e regras da academia.

**Fase atual:** MVP de teste; dados locais descartáveis; fluxo padrão assume recriação completa do banco por ciclo quando aplicável (ver `CLAUDE.md` e política VMP abaixo).

---

## Política de idioma (regra inviolável)

- **Backend 100% inglês:** models, fields, variáveis, funções, classes, services, views, forms, URLs, nomes de arquivos e diretórios.
- **Texto visível ao usuário em pt-BR:** labels, placeholders, mensagens, títulos, botões, tooltips, textos de ajuda.
- **Código frontend em inglês:** variáveis JS, classes CSS, IDs. Apenas conteúdo textual renderizado em pt-BR.
- **Respostas do agente ao desenvolvedor:** sempre em pt-BR.
- **Código limpo:** evitar comentários e docstrings; usar apenas quando uma decisão de negócio não puder ser inferida pela estrutura.

*(No LV JIU JITSU, qualidade linguística de interface — acentuação, concordância, microcopy — é regra de produto; ver `CLAUDE.md`.)*

---

## Prioridade em caso de conflito

1. Solicitação atual do usuário (sem violar segurança)
2. Regras de segurança e ambiente (`.venv`, segredos, LGPD)
3. Este `AGENTS.md`
4. `CLAUDE.md`
5. Convenções do repositório

Registrar exceções no fechamento da tarefa.

---

## Protocolo obrigatório — não pular etapas

### FASE 1 — Contexto

1. Ler `CLAUDE.md`, PRDs em `docs/prd/` quando existirem, e arquivos impactados.
2. Classificar: correção, feature, refatoração ou ajuste de arquitetura.
3. Identificar regras críticas tocadas (lista orientativa abaixo).
4. **Não** executar comandos `git` sem solicitação explícita do usuário na tarefa atual.
5. Confirmar que **todo** Python, `pip`, `manage.py` e scripts usam **`.\.venv\Scripts\python.exe`** (Windows) ou o equivalente da `.venv` no SO em uso. Proibido Python global para este repositório.
6. Identificar módulos internos do app `system` eventualmente impactados: `public`, `identity_access`, `student_registry`, `instructor_ops`, `class_catalog`, `attendance_qr`, `finance_contracts`, `payments_stripe`, `graduation_engine`, `communications`, `documents_lgpd`, `reports_audit`, `settings_seed`.

**Regras críticas (verificar se a mudança toca):** identidade única por CPF; autenticação do portal local vs Django Admin; um `PersonType` por cadastro; classificação de turma só via `ClassCategory`; matrícula esportiva por `ClassGroup` com horários herdados; onboarding transacional; check-in com QR/WebRTC; reserva prévia; inadimplência e matrícula pausada; Stripe/`pause_collection`; graduação com tempo ativo; LGPD, menores, biometria; exportação com fail-fast; caixa e divergência; auditoria em fluxos críticos.

Apresentar **plano curto** antes de implementar: objetivo, agregado ou fluxo afetado, invariantes, validação ao final.

### FASE 1.5 — Reset obrigatório do ambiente (perfil VMP — LV JIU JITSU)

Antes de **iniciar** correção ou implementação que altere models, migrations ou dados coerentes:

1. Executar `.\.venv\Scripts\python.exe clear_migrations.py` (limpa banco local, migrations geradas, `__pycache__` e artefatos conforme o script).
2. Só depois alterar código.
3. Nunca preservar migrations intermediárias nem migrar incrementalmente sobre banco legado neste perfil; se algo falhar após a entrega, recomeçar do `clear_migrations.py`.

Este fluxo é obrigatório para o ciclo de trabalho descrito no `CLAUDE.md` (MVP descartável).

### FASE 2 — PRD da tarefa

Criar `docs/prd/PRD-<NNN>-<slug>.md` quando a mudança não for trivial (vide SDD acima), com: resumo, problema, objetivo, escopo, fora do escopo, critérios de aceite, plano com `[ ]`. O PRD pode ser curto, mas não vago. Se o trajeto mudar, atualizar no fechamento.

### FASE 3 — Estratégia

Definir abordagem, arquivos impactados, testes planejados e riscos. Menor mudança correta; não expandir escopo em silêncio.

### FASE 4 — Implementação

Ordem de referência Django: **Models → Forms → Services → Views → URLs → Templates → Tests**.

**Regras obrigatórias:**

- Views finas; regras complexas em `services.py`, `selectors.py`, `managers.py` ou métodos de domínio.
- Portal e Django Admin são superfícies independentes: o produto **não** usa `django.contrib.auth.User` como identidade do aluno/professor/responsável; autenticação e reset do portal no domínio local (`system`).
- `transaction.atomic()` em fluxos compostos (onboarding titular + dependentes, pagamento + efeitos, reserva + capacidade, etc.).
- Não hardcodar chaves, segredos, URLs base, TTL de QR, regras configuráveis.
- Backend **sempre** revalida regras críticas, mesmo com bloqueio na UI.
- Integrações externas são falíveis e auditáveis.
- Catálogo Stripe: mapeamento explícito de plano → `Price` vigente; aposentar mapeamento anterior de forma determinística; espelho `dj-stripe` não substitui contrato local.

### FASE 5 — Testes

Cobrir models, forms, views, services, commands, fluxos felizes e de erro quando relevante. **Validar no terminal** a execução real (contagem, falhas, erros, skips). Preferir test-first nos fluxos centrais de domínio.

### FASE 6 — Validação obrigatória

| Item | Como | Critério |
|------|------|----------|
| Servidor | Verificar se já há processo na porta antes de subir outro | Sem erros no terminal |
| Testes | `.\.venv\Scripts\python.exe manage.py test` | 0 falhas, 0 erros |
| Migrações (VMP) | `system/migrations/` | Apenas `0001_initial.py` coerente por app, após ciclo limpo |
| ORM/SQLite | Shell ou script | FKs e registros coerentes quando aplicável |
| Visual | Headless + MCP Playwright (ou browser MCP do ambiente) | OK em mobile (~375px) e desktop (~1440px) nas rotas alteradas |
| Console browser | DevTools | Zero erros JS relevantes |
| Console terminal | stdout/stderr | Sem stack traces não explicados |

Ao finalizar tarefa que altere models, views, forms, services ou migrations, executar o **ciclo completo** documentado no `CLAUDE.md` (clear → makemigrations → test → migrate → `create_admin_superuser`), com evidência no log até antes de `runserver`.

**Se a validação visual não puder ser executada**, declarar explicitamente que a interface **não** foi validada por navegador automatizado. Status HTTP 200, teste unitário ou leitura de HTML **não** substituem validação visual.

### FASE 7 — Fechamento

Usar o modelo abaixo na resposta (adaptar títulos se necessário):

```md
## Resumo da demanda
## O que foi implementado
## O que mudou no trajeto
## Validação
- [ ] Testes
- [ ] Migrações
- [ ] ORM
- [ ] Visual (headless + Playwright / MCP)
- [ ] Console browser
- [ ] Console terminal
## O que NÃO foi validado (e por quê)
## Pendências
## Próximo passo sugerido
```

Não declarar conclusão sem evidência alinhada à implementação real.

---

## Debate multiagente interno

Antes de implementar, simular brevemente:

| Papel | Pergunta-chave |
|-------|----------------|
| **Arquiteto** | Estrutura e padrões adequados? Impacto controlado? |
| **Testador** | Cobertura de fluxos felizes e de erro? Regressão protegida? |
| **Revisor UI** | Responsivo? Feedback visual e pt-BR ok? |
| **Revisor dados** | ORM correto? Política VMP respeitada? Seeds coerentes? |

---

## Django VMP — política de migração descartável (LV JIU JITSU)

### Quando se aplica

Projeto em MVP com banco local descartável, sem histórico evolutivo obrigatório e sem ambiente compartilhado que exija migrações incrementais.

### Ciclo de comandos (ordem exata; verificar porta 8000 antes de `runserver`)

```bash
.\.venv\Scripts\python.exe clear_migrations.py
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py create_admin_superuser
.\.venv\Scripts\python.exe manage.py inicial_seed
.\.venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
```

(Em ambientes Unix, prefixar com `./.venv/bin/python` em vez de `.\.venv\Scripts\python.exe`.)

### Regras invioláveis

- **Nunca** criar ou editar migration manualmente; corrigir models e deixar o Django gerar.
- **Nunca** migrar incrementalmente sobre banco existente neste perfil: o banco nasce do zero a cada ciclo de reset.
- Validar que restou apenas `0001_initial.py` coerente por app após o ciclo.
- Se qualquer etapa falhar, corrigir o código e recomeçar do `clear_migrations.py`.
- Se um comando não existir no projeto, **reportar** — não simular sucesso.

### Cláusula de escape

Se o projeto passar a usar banco persistente compartilhado ou política diferente de migração, **interromper** esta política VMP, documentar o motivo e tratar migrações de forma convencional.

---

## Anti-code-smell (regras concretas)

- **Máximo 25 linhas por método.** Acima disso, extrair para serviço ou submétodo.
- **Máximo 4 argumentos por função.** Acima disso, dataclass ou kwargs nomeados.
- **Proibido N+1** em listagens e dashboards: `select_related()` / `prefetch_related()`.
- **Proibido** `except: pass` ou engolir erro sem tratamento explícito.
- **Signals** (`signals.py`): só quando acoplamento implícito for aceitável; regra central fica no serviço.
- Template não resolve query; view não resolve layout (orquestração fina; layout no template).

---

## Invariantes de domínio que o agente não pode violar

Resumo alinhado ao `CLAUDE.md` (detalhes lá):

- **Identidade:** uma pessoa, um cadastro; CPF como identificador de login do portal; um `PersonType` por cadastro na fase atual; sem multi-papel N:N; conta do portal no domínio local, não como identidade primária via `User` do Django; Admin técnico não concede sessão do portal.
- **Tatame:** validações antes da câmera; reserva consome capacidade; QR confirma quem já tinha direito; turma classificada por `ClassCategory`; liberação por `ClassGroup`; `ClassSchedule` não colapsado no nome da turma.
- **Financeiro:** estado local canônico; Stripe confirma eventos mas não substitui regras de acesso; checkout/redirect não libera acesso sozinho; `Price` vigente único por plano; comprovante em análise não regulariza até decisão explícita.
- **Graduação:** tempo ativo de treino; pausa congela quando aplicável.
- **LGPD / exportação / auditoria:** fluxos sensíveis com trilha; exportação crítica só com arquivo de controle `EXPORT_ALLOWED=1`; fail-fast.

---

## Política de testes (orientação)

Considerar testes para: CPF único; portal independente do login Admin; dependente com credencial no escopo permitido; onboarding transacional e multi-turma; elegibilidade de turma (idade, sexo quando regra); inadimplência antes da câmera; reserva e vagas; pausa e graduação; webhooks idempotentes; caixa e limiar; `AuditLog` nos fluxos alterados; LGPD e exportação.

Para mudanças críticas, informar o que foi testado, o que falta e riscos residuais.

**Seeds:** `inicial_seed` mínima; `inicial_seed_test` navegável, determinística, sem N:N de tipos por pessoa.

---

## Proibições

- Pular leitura de contexto; implementar sem PRD quando a tarefa exige spec (alinhado ao SDD).
- Simular execução de testes, Playwright ou validação ORM.
- Declarar sucesso sem evidência.
- Editar migration manualmente (perfil VMP).
- Expandir escopo sem registrar pendência.
- Inventar comandos ou paths inexistentes.
- Executar `git` sem pedido explícito do usuário.
- Confiar só no frontend para regra crítica de segurança ou negócio.

---

## Sinais de bloqueio

Reportar tarefa como **não concluída** quando: servidor não sobe, UI não validável, **Playwright** (ou MCP equivalente) indisponível quando era obrigatório para a entrega, testes quebram sem caminho de correção, comandos esperados ausentes, ou política VMP aplicada indevidamente a ambiente que exige migração incremental.

---

## Evolução contínua

Se a execução revelar lacuna ou workflow repetitivo:

> **"Identifiquei que nosso CLAUDE.md/AGENTS.md precisa evoluir com base nesta iteração [motivo]. Deseja que eu proponha a atualização?"**

---

## Fonte de verdade

| O quê | Onde |
|-------|------|
| Como o agente trabalha | Este `AGENTS.md` |
| O que o sistema é e como funciona | `CLAUDE.md` |
| Requisitos por tarefa | PRDs em `docs/prd/` |
| Fluxos reais | Código do domínio e testes |

Contradição entre código legado e spec atual: sinalizar e priorizar correção estrutural.
