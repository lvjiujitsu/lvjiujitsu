# PRD-174: Taxonomia do runbook operacional

## Summary

Reescrever o runbook de operação do LV no Obsidian
(`obsidian/projetos/comandos-powershell-lvjiujitsu.md`) em uma taxonomia de nove
seções numeradas. O runbook ganha as seções que não existiam — ambientes, telas,
produção, seeds em tabela, publicação e erros comuns — e passa a declarar as
guardas reais do reset remoto.

## Demand type

Documentação operacional fora do repositório. Sem mudança de código.

## Current problem

O runbook tinha 183 linhas e era o mais incompleto dos três. Seis problemas
concretos:

1. **Não existia seção de produção.** O documento cobria homologação e local. O
   ambiente `prod` — que tem `.env.prod`, `clear_migration_supabase_prod` e
   `SUPABASE_RESET_CONFIRM=RESET_PROD` — não aparecia em lugar nenhum, embora
   `docs/OPERACAO-BANCO-SEEDS.md` §6 o descreva por inteiro.
2. **A ordem estava invertida.** O documento abria por HOMOLOGAÇÃO e só depois
   tratava do local, que é onde a rotina diária acontece.
3. **As guardas do reset remoto estavam incompletas e o comportamento padrão
   estava errado por omissão.** O runbook mostrava
   `python manage.py clear_migration_supabase_hg` logo abaixo de duas variáveis
   de ambiente, sem dizer que sem `--execute` o comando **apenas simula** e sem
   citar `DJANGO_DEBUG=False`, o host Supabase nem `SUPABASE_PROJECT_REF`. Quem
   seguisse o runbook esperaria destruição imediata onde há simulação, e
   confiaria em duas guardas onde há sete.
4. **As 21 seeds não estavam em tabela.** Apareciam só como bloco corrido
   dentro do ciclo destrutivo, sem dizer qual variável cada uma exige.
   `seed_system_initial_teacher` falha sem `SEED_INITIAL_TEACHER_PASSWORD`, e
   isso não estava escrito.
5. **Não havia tabela de erros comuns, tabela de telas nem seção de
   publicação.**
6. **O interpretador divergia.** O runbook usava `Activate.ps1` seguido de
   `python`, enquanto o repositório trata `.\.venv\Scripts\python.exe` como
   caminho canônico, que não depende de política de execução nem de ativação
   prévia.

## Goal

Um runbook que cubra os três ambientes, cuja afirmação sobre operação
destrutiva corresponda ao que o comando faz, e em que cada seção possa ser
citada por número.

## Context Ledger

### Files read in full

- `obsidian/projetos/comandos-powershell-lvjiujitsu.md` (183 linhas, versão
  anterior)
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/DEPLOY-RENDER-SUPABASE.md`
- `CLAUDE.md`, `AGENTS.md`

### Adjacent files consulted

- `.env.example` — conjunto canônico de 71 chaves, usado na seção 5.3; base da
  correção de `STRIPE_PUBLIC_KEY`
- `system/urls.py` — rotas canônicas e aliases, base da seção 2
- `system/management/commands/` — inventário real, incluindo
  `explain_perf_indexes`, `backfill_membership_timeline` e
  `generate_due_asaas_charges`

### Internet / official documentation

- [Stripe CLI — listen](https://docs.stripe.com/cli/listen) — confirmação do
  encaminhamento de webhook para o endpoint local, mantido na seção 3.5.

### Context7 / MCPs / tools verified

Não aplicável: nenhuma biblioteca nova.

### Limitations found

O runbook vive no Obsidian, fora do repositório e fora do Git. Não existe gate
automatizado que verifique se ele continua verdadeiro. No repositório existe
`system/tests/test_seed_docs_contract.py`, que cobre os nomes de seed citados na
documentação **versionada** — o runbook do Obsidian está fora desse alcance.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: nivelar o runbook por seções de títulos idênticos,
  mantendo os comandos reais e sem apagar conteúdo.
- User approval: ordem explícita do operador, com a instrução de que as seções
  de erros comuns, seeds com pré-requisito de env e publicação passem a
  existir, preenchidas com o que é verdade neste projeto.
- Date: 2026-07-26

## Execution prompt

### Persona

Operador do LV escrevendo o próprio runbook.

### Action

Reescrever o runbook na taxonomia de nove seções, com os comandos reais deste
projeto e a seção de produção que faltava.

### Context

O runbook é atalho operacional; a norma vive em `docs/OPERACAO-BANCO-SEEDS.md`
e em `docs/DEPLOY-RENDER-SUPABASE.md`.

### Constraints

- Nenhum comando inventado.
- Nenhum segredo: apenas nomes de chave.
- Nenhuma menção a outro projeto.
- Nenhum conteúdo perdido: Stripe CLI, ngrok e o disparo de checkout em sandbox
  permanecem.

### Acceptance criteria

- [x] Nove seções numeradas, na ordem: Ambientes, Arquitetura das telas, Local,
      Seeds, Homologação, Produção, Publicar alterações, Erros comuns,
      Referências.
- [x] Existe seção de produção, com checagem somente leitura, reset e recarga.
- [x] As guardas do reset remoto listam as sete condições, incluindo
      `SUPABASE_PROJECT_REF` e `--execute`, e o texto diz que sem `--execute` o
      comando simula.
- [x] As 21 seeds estão em tabela, com o pré-requisito de ambiente de cada uma.
- [x] Existe tabela de erros comuns com sintoma, causa e correção.
- [x] Existe seção de publicação declarando que o push dispara Auto-Deploy.
- [x] Existe tabela de telas com rota canônica, alias pt-BR, função e acesso.
- [x] A seção de gateways de pagamento permanece, com Stripe CLI, ngrok e o
      `trigger` de checkout.
- [x] Todo comando citado existe no repositório.
- [x] Zero menção a outro projeto.

### Expected evidence

Verificação estrutural do documento e conferência de cada comando e chave
contra o repositório.

### Output format

Markdown, pt-BR, com blocos PowerShell.

## Scope

- `obsidian/projetos/comandos-powershell-lvjiujitsu.md`.

## Out of scope

- Commit e push.
- Conferência dos painéis Stripe e Asaas.

## Impacted files

| Arquivo | Mudança |
|---|---|
| `obsidian/projetos/comandos-powershell-lvjiujitsu.md` | reescrito: 183 → 544 linhas, taxonomia de 9 seções |
| `docs/prd/README.md` | índice regenerado |

## Risks and edge cases

- **Documentar chave de ambiente que não existe.** Risco real: o rascunho
  trazia `STRIPE_PUBLISHABLE_KEY`, e a chave do projeto é `STRIPE_PUBLIC_KEY`.
  Detectado na conferência contra `.env.example` e corrigido antes de fechar.
- **Documentar comando inexistente.** Mitigado conferindo cada nome contra
  `system/management/commands/`.
- **Descrever o reset como destrutivo por padrão.** Corrigido: o texto agora
  diz que sem `--execute` o comando lista e não remove.

## Rules and constraints

`AGENTS.md` §2, §10 (segredo nunca impresso) e `CLAUDE.md` §1.

## Plan

- [x] Context and research
- [ ] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

Teste primeiro não se aplica: o arquivo está fora do repositório e não há
comportamento executável a cobrir.

## Test plan

### Tests to author

Nenhum.

### Execution authorization

- Status: authorized

### Execution evidence

A suíte foi executada como gate de regressão do repositório; ver `Evidence`.

## Visual validation

Não aplicável: nenhuma superfície muda.

### Design approval

Não aplicável.

### Routes and states

Não aplicável.

### Desktop

Não aplicável.

### Mobile

Não aplicável.

### Console and terminal

Não aplicável.

### Screenshot / snapshot

Não aplicável.

## ORM validation

### Read-only checks

Não aplicável.

### Mutating checks and authorization

Não aplicável.

## Quality validation

Conferência das chaves de ambiente contra `.env.example`, dos nomes de comando
contra o diretório real, verificação dos títulos de seção e busca por menção
cruzada.

## Evidence

Chaves de gateway conferidas em `.env.example`, base da correção:

```text
STRIPE_SECRET_KEY  STRIPE_PUBLIC_KEY  STRIPE_WEBHOOK_SECRET
STRIPE_PLAN_SYNC_ENABLED  ASAAS_API_KEY  ASAAS_API_URL  ASAAS_WEBHOOK_TOKEN
```

`STRIPE_PUBLISHABLE_KEY` não existe no projeto; o runbook declara
`STRIPE_PUBLIC_KEY`.

Estrutura resultante:

```text
1. Ambientes | 2. Arquitetura das telas | 3. LOCAL — SQLITE (3.1 a 3.5) |
4. Seeds — ordem e independência (4.1 demonstração e importação histórica) |
5. HOMOLOGAÇÃO — RENDER + SUPABASE (5.1 a 5.7) |
6. PRODUÇÃO — RENDER + SUPABASE (6.1 a 6.3) | 7. Publicar alterações |
8. Erros comuns | 9. Referências
544 linhas · menções cruzadas = []
```

A seção 3.5, exclusiva deste projeto, é a única subseção que os outros níveis
da taxonomia não preveem — e existe porque só este produto tem gateway de
pagamento.

Gates do repositório, todos executados nesta sessão:

```text
$ .\.venv\Scripts\python.exe manage.py check
System check identified no issues (0 silenced).

$ .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
No changes detected

$ .\.venv\Scripts\python.exe scriptsuild_prd_index.py --check
182 PRD(s) indexada(s).
Indice em dia.

$ .\.venv\Scripts\python.exe scriptsalidate_skill_frontmatter.py
[OK] 7 skill(s) nas 3 plataformas
[OK] 7 metadado(s) Codex integro(s) em UTF-8 com LF.
21 arquivo(s) de skill validado(s).

$ .\.venv\Scripts\python.exe -m pip check
No broken requirements found.

$ .\.venv\Scripts\python.exe manage.py test
Ran 769 tests in 352.074s
OK
```

Contagem da suíte preservada: 769 testes, mesma da execução anterior.

## Implemented

- Runbook reescrito em nove seções numeradas, abrindo pelo local.
- Seção 6 criada: produção com checagem somente leitura, reset destrutivo e
  recarga.
- Guardas do reset remoto completadas nas seções 5.4 e 6.2: sete condições, com
  `SUPABASE_PROJECT_REF` correspondente ao host e a flag `--execute`, mais a
  nota de que sem ela o comando simula.
- Aviso, na seção 5.4, de que o reset não recria o estado dos gateways:
  cobrança e assinatura já criadas no Asaas e no Stripe continuam existindo lá.
- As 21 seeds em tabela, com o pré-requisito de ambiente de cada uma
  (`ADMIN_SUPERUSER_PASSWORD`, `SEED_INITIAL_TEACHER_PASSWORD`,
  `SEED_INITIAL_ADMINISTRATIVE_PASSWORD`) e a nota de que os passos 12 e 13 são
  legados idempotentes.
- Seção 4.1 com as quatro seeds de demonstração, o requisito
  `SEED_TEST_PORTAL_PASSWORD`, `clear_test_data` e a importação histórica
  Kanri.
- Seção 2 com a tabela de telas: rota canônica em inglês, alias pt-BR, função e
  acesso.
- Seção 1 com a tabela dos três ambientes e o aviso de não misturar os ciclos.
- Seção 3.5 preservando ngrok, Stripe CLI, `stripe listen`, o `trigger` de
  checkout com `client_reference_id`, os sinais de sucesso e
  `generate_due_asaas_charges`, com a nota de que ele escreve no gateway.
- Seção 7 de publicação, com os gates locais, `git diff` e o aviso de que o
  push dispara o Auto-Deploy.
- Tabela de dez erros comuns, incluindo as mensagens reais de recusa do
  `clear_migrations.py`, a armadilha do `python-decouple` com chave de valor
  vazio, o webhook Stripe apontado para rota errada e o `SITE_BASE_URL`
  divergente.
- Interpretador padronizado em `.\.venv\Scripts\python.exe`, sem depender de
  `Activate.ps1`.
- Bloco de variáveis do Render com `SUPABASE_PROJECT_REF`, `SITE_NAME`,
  `SITE_NAME_UPPER`, as chaves de seed e as de gateway, e a explicação de por
  que `SUPABASE_RESET_CONFIRM` não é cadastrada.
- Seção 3.2 com `explain_perf_indexes`, `check_database_connection`,
  `makemigrations --check --dry-run`, `pip check` e os dois gates de contrato.

## Cleanup findings

- A versão anterior descrevia o ciclo destrutivo local dizendo apenas que ele
  "encerra apenas processos Python pertencentes ao LV". A descrição foi
  completada com o que `docs/OPERACAO-BANCO-SEEDS.md` §4.3 registra: o
  `taskkill` é por PID, sem `/T`, com espera de até 8 segundos, e nunca atinge o
  próprio processo, o pai direto nem os ancestrais.
- A versão anterior citava "seeds canônicas 1→21 na ordem de
  `docs/OPERACAO-BANCO-SEEDS.md`" sem listá-las, e ao mesmo tempo mostrava as
  duas últimas soltas em um bloco. A tabela substitui as duas formas.
- O domínio e o serviço HG estavam em uma lista solta no topo; passaram para a
  tabela do serviço, na seção 5.2.

## Follow-up PRDs

Nenhuma.

## Deviations from plan

O interpretador foi padronizado em `.\.venv\Scripts\python.exe`, o que não
estava no pedido explicitamente. A troca não altera o que os comandos fazem e
elimina a dependência de `Activate.ps1` e de política de execução, que é a
única razão pela qual o runbook anterior precisava de um passo a mais.

## Pending

Nenhuma pendência conhecida neste runbook.

## Final status

concluída
