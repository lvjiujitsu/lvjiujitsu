# PRD-170: Nivelamento dos contratos de produto

## Summary

`CLAUDE.md`, `README.md`, `docs/OPERACAO-BANCO-SEEDS.md` e
`docs/DEPLOY-RENDER-SUPABASE.md` tinham estruturas incompatíveis entre os
projetos do mesmo eixo. Esta PRD dá aos quatro um núcleo de seções com títulos
idênticos, deixando livre apenas o conteúdo que é regra de negócio, e promove a
ordem canônica das 21 seeds a tabela numerada — a fonte que o `/reset-local` e o
runbook passam a referenciar em vez de duplicar.

## Demand type

Revisão de governança e regeneração documental. Sem mudança de código Python,
de schema ou de UI.

## Current problem

- `CLAUDE.md` tinha 11 seções com numeração própria, incompatível com a dos
  projetos do mesmo eixo, e nenhuma seção declarando o que **não** existe — o
  que deixava um agente livre para propor terceiro gateway, `seed_test_data`
  único ou `requirements-dev.txt` que nunca houve.
- `README.md` tinha 6 seções e 89 linhas, o mais curto do eixo: sem tabela de
  URLs, sem ciclo local, sem seção de licença e sem os comandos de validação.
- `docs/OPERACAO-BANCO-SEEDS.md` tinha 19 seções sem numeração, organizadas por
  ambiente, com a ordem das 21 seeds descrita em prosa. Sem tabela numerada, o
  `/reset-local` e o runbook mantinham cópias da lista, que é exatamente como
  uma delas fica desatualizada.
- `docs/DEPLOY-RENDER-SUPABASE.md` não tinha "Logs esperados" nem "Smoke test
  depois do deploy" — as duas seções que dizem como saber que o deploy deu certo.
- Nenhum dos quatro descrevia o encerramento de processos do ciclo destrutivo,
  embora `clear_migrations.py` encerre processo Python antes de apagar e espere
  até 8 segundos pela saída.

## Goal

Os quatro contratos de produto têm núcleo de seções com títulos idênticos e na
mesma ordem nos três projetos do eixo; o que difere é conteúdo de produto. A
ordem das seeds tem dono único. Zero link quebrado.

## Context Ledger

### Files read in full

- `CLAUDE.md`, `README.md`
- `docs/OPERACAO-BANCO-SEEDS.md`, `docs/DEPLOY-RENDER-SUPABASE.md`
- `clear_migrations.py` — para descrever o encerramento de processos como ele é
- `system/tests/test_seed_docs_contract.py` — o teste que valida este documento

### Adjacent files consulted

- `lvjiujitsu/urls.py` e `system/urls.py` — rotas reais, para não inventar
  superfície
- `.claude/commands/reset-local.md`
- `system/management/commands/` — inventário real de comandos
- `docs/prd/PRD-169-nivelamento-dos-contratos-de-protocolo.md`

### Internet / official documentation

- Render, Build e Start Command de serviço Python:
  https://render.com/docs/deploy-django
- Supabase, segurança da Data API:
  https://supabase.com/docs/guides/api/securing-your-api

### Context7 / MCPs / tools verified

- Context7 não foi consultado: a mudança é documental e não envolve API de
  biblioteca.

### Limitations found

- O verificador de links trata menção negativa (`sem requirements-dev.txt`) e a
  frase genérica `` `SKILL.md` `` como caminho, e reporta falso positivo. Os dois
  casos foram conferidos à mão.
- O vocabulário de tokens CSS não pode ser unificado por documento: este projeto
  declara 49 tokens, os do mesmo eixo declaram 72 e 31, e **apenas três**
  (`--panel`, `--muted`, `--danger`) existem nos três. Unificar exige refatorar
  CSS e validar no browser, o que é PRD própria.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: plano de seis etapas e tabela "melhor de cada eixo".
- User approval: Etapa 3 autorizada com "pode seguir".
- Date: 2026-07-26.

## Execution prompt

### Persona

Responsável pela governança documental do repositório.

### Action

Nivelar os quatro contratos de produto por núcleo de seções e dar dono único à
ordem das seeds.

### Context

MVP descartável. Contrato descreve o que existe; ao divergir do código, o código
vence e o contrato é corrigido na mesma mudança.

### Constraints

- núcleo com títulos idênticos; conteúdo de produto livre;
- nenhuma rota, comando ou variável pode ser inventada — tudo conferido no
  código;
- todo nome de seed citado precisa existir: `test_seed_docs_contract.py`
  reprova o contrário;
- não alterar código nesta PRD.

### Acceptance criteria

- [x] `CLAUDE.md` com núcleo de 11 seções idêntico nos três e seções 12+ livres
      para regra de negócio;
- [x] `CLAUDE.md` com a seção "O que não existe neste projeto";
- [x] `README.md` com as mesmas 10 seções nos três, com tabela de URLs;
- [x] `docs/DEPLOY-RENDER-SUPABASE.md` com as mesmas 10 seções nos três;
- [x] `docs/OPERACAO-BANCO-SEEDS.md` com as mesmas 6 seções numeradas nos três;
- [x] as 21 seeds em tabela numerada, com a variável exigida por passo;
- [x] `test_seed_docs_contract.py` verde depois da reescrita;
- [x] o documento descreve o encerramento de processos como o código faz;
- [x] `check` e `build_prd_index.py --check` verdes;
- [ ] `docs/UI-SCREEN-CONTRACT.md` nivelado — **não entregue**, ver `Pending`.

### Expected evidence

Lista de títulos de seção por arquivo nos três projetos; saída do teste de
contrato de seeds; saída do verificador de links e dos gates.

### Output format

Diff documental e PRD atualizada com evidência.

## Scope

- `CLAUDE.md`
- `README.md`
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/DEPLOY-RENDER-SUPABASE.md`

## Out of scope

- `docs/UI-SCREEN-CONTRACT.md` — ver `Pending` e `Follow-up PRDs`.
- Convergência do vocabulário de tokens CSS.
- `requirements.txt`, `.gitignore` e o conjunto de chaves de env.
- Remoção de comentários e docstrings.
- `docs/archive/static-documentation-legacy/`, os três guias de wizard e
  `docs/prd/AUDIT-2026-06-30-master-findings.md`.

## Impacted files

| Arquivo | Mudança |
|---|---|
| `CLAUDE.md` | 165 → 295 linhas; núcleo de 11 seções, seção "O que não existe", tabela caminho/responsabilidade, §12 Cadastro público, §13 Pagamentos, §14 Graduação, planos e repasses |
| `README.md` | 89 → 137 linhas; 10 seções, tabela de URLs por superfície, ciclo local, validação, licença |
| `docs/OPERACAO-BANCO-SEEDS.md` | 269 → 349 linhas; 6 seções numeradas, as 21 seeds em tabela com variável exigida, guardas e guarda de saída documentadas |
| `docs/DEPLOY-RENDER-SUPABASE.md` | 155 → 211 linhas; ganha "Logs esperados" e "Smoke test depois do deploy" |

## Risks and edge cases

- `test_seed_docs_contract.py` reprova se o documento citar comando de seed
  inexistente. A tabela das 21 seeds foi conferida contra
  `system/management/commands/` e o teste foi executado depois da reescrita.
- A referência `seed_system_initial_test_*` com asterisco não casa com a regex do
  teste, então os quatro nomes reais foram escritos por extenso na seção de
  seeds de demonstração.
- Descrever o encerramento de processos corretamente pode assustar: o comando
  mata processo Python. A proteção é real e está documentada — nunca o próprio
  PID, o pai direto nem os ancestrais, porque o `python.exe` do venv é um shim
  que aparece como ancestral.
- Numerar as seções cria referência estável (`§2.1`, `§3`) usada agora por
  `reset-local.md` e pelo `CLAUDE.md`. Renumerar no futuro quebra essas
  referências.

## Rules and constraints

- `AGENTS.md` §2: um dono por assunto; ao divergir do código, o código vence.
- `AGENTS.md` §10: segredo nunca impresso; ao ler env, reportar nome de chave.
- `AGENTS.md` §12: dívida material fora do escopo vira follow-up.

## Plan

- [x] Context and research
- [x] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

Nenhum teste novo. `system/tests/test_seed_docs_contract.py` já cobre o contrato
entre este documento e os comandos reais, e foi o guarda-corpo da reescrita.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test system.tests.test_seed_docs_contract --verbosity 2
Ran 2 tests in 0.001s
OK
exit=0
```

```text
python manage.py check
System check identified no issues (0 silenced).
exit=0
```

A suíte completa (769 casos) foi executada na PRD-169, antes desta mudança
documental; nenhum arquivo Python foi tocado aqui.

## Visual validation

### Design approval

Não aplicável: nenhuma mudança visual.

### Routes and states

Não aplicável. As rotas citadas no `CLAUDE.md` e no `README.md` foram extraídas
de `system/urls.py`, não inventadas.

### Desktop

Não aplicável.

### Mobile

Não aplicável.

### Console and terminal

`manage.py check` sem aviso.

### Screenshot / snapshot

Não aplicável: a mudança é documental.

## ORM validation

### Read-only checks

Nenhuma consulta necessária: nenhuma mudança de model, query ou migration.

### Mutating checks and authorization

Nenhuma escrita executada.

## Quality validation

```text
python manage.py check                        -> no issues, exit=0
python scripts/build_prd_index.py --check     -> Indice em dia, exit=0
```

Verificador de links, depois da mudança:

```text
CLAUDE.md: 24 referencias, 1 quebrada  -> falso positivo: "sem requirements-dev.txt"
AGENTS.md: 13 referencias, 1 quebrada  -> falso positivo: frase generica `SKILL.md`
README.md: 14 referencias, 0 quebradas
```

## Evidence

Títulos de seção por arquivo, nos três projetos do eixo:

```text
CLAUDE.md — nucleo, variantes=1:
  1. Natureza do projeto | 2. Produto | 3. Stack | 4. Arquitetura em camadas
  5. Contratos locais | 6. Comandos locais | 7. Banco e migrations | 8. Seeds
  9. Ambientes | 10. UI e validação | 11. Referências
  (12+ livre: aqui, Cadastro público, Pagamentos e Graduação/planos/repasses)

README.md — identicos nos tres:
  Stack | Estrutura | Setup local | Ciclo local completo | Servidor e URLs
  Validação | Ambientes | Governança | Licença

docs/DEPLOY-RENDER-SUPABASE.md — identicos nos tres:
  1. Serviços | 2. Comandos exatos | 3. Health check | 4. Environment Variables
  5. Supabase | 6. Auto-deploy | 7. Reset destrutivo remoto | 8. Logs esperados
  9. Smoke test depois do deploy | 10. Referências

docs/OPERACAO-BANCO-SEEDS.md — identicos nos tres:
  1. Ambientes | 2. Inventário de comandos | 3. Seeds — ordem e independência
  4. Local — SQLite | 5. Homologação — Supabase | 6. Produção — Supabase
```

Vocabulário de tokens CSS medido nos três projetos: 49 tokens aqui, 72 e 31 nos
outros, com **apenas 3 comuns** (`--panel`, `--muted`, `--danger`). É o dado que
justifica tratar a convergência como PRD própria.

## Implemented

- `CLAUDE.md` com núcleo de 11 seções, a seção "O que não existe neste projeto"
  e as regras de produto nas seções 12 a 14, incluindo a guarda de pagamento
  recebida da PRD-169;
- `README.md` com 10 seções, tabela de URLs por superfície e nota sobre o alias
  em inglês das rotas;
- `docs/DEPLOY-RENDER-SUPABASE.md` com "Logs esperados", "Smoke test depois do
  deploy" e o aviso de que reset remoto não recria o estado dos gateways;
- `docs/OPERACAO-BANCO-SEEDS.md` com 6 seções numeradas e as 21 seeds em tabela,
  com a variável exigida por passo — agora fonte única, referenciada pelo
  `/reset-local` em vez de duplicada;
- descrição correta do encerramento de processos, incluindo a espera de 8
  segundos e o uso de `taskkill` sem `/T`.

## Cleanup findings

- `system/tests/test_class_catalog.py` tem 0 linhas: arquivo de teste vazio.
- `docs/archive/static-documentation-legacy/` guarda 12 documentos substituídos
  pelos contratos atuais.
- `docs/prd/AUDIT-2026-06-30-master-findings.md` não é PRD numerada e obriga o
  gerador do índice a manter uma exceção nomeada.
- `docs/wizard-step-plan-*.md`: três guias soltos na raiz de `docs/`, agora
  referenciados pelo `CLAUDE.md` §12 mas fora da taxonomia dos demais contratos.
- `.env` declara `DJANGO_DEBUG=1` em vez de `True`.
- `.claude/settings.local.json` duplica exatamente `settings.json`.
- Não existe `seed_test_data`: o par com `clear_test_data` é feito por quatro
  seeds `seed_system_initial_test_*`, o que difere dos projetos do mesmo eixo.

## Follow-up PRDs

- Nivelamento de `docs/UI-SCREEN-CONTRACT.md` por núcleo normativo e inventário
  de produto.
- Convergência do vocabulário de tokens CSS entre os projetos do eixo, com
  validação visual das rotas afetadas nos dois temas.
- Etapas seguintes já acordadas: infraestrutura e ambiente, estrutura e limpeza
  de comentários e docstrings.

## Deviations from plan

Uma. `docs/UI-SCREEN-CONTRACT.md` estava no escopo da etapa e **não foi
entregue**. O motivo está em `Pending`; não é bloqueio de informação, é decisão
de não reestruturar pela metade um contrato de 591 linhas cujo material
normativo e de produto estão intercalados.

## Pending

- **`docs/UI-SCREEN-CONTRACT.md` não foi nivelado.** O material normativo que o
  núcleo deve absorver está em `§1, 2, 3, 5, 6, 7, 11, 12, 13` e `§14.1–14.4`, e
  o material de produto — identidade, papéis, inventário de telas, componentes e
  os padrões `§15.5` a `§15.7` — está intercalado com ele. Reestruturar sem ler a
  cauda por inteiro apagaria padrões existentes. Vira PRD própria, com o plano:
  núcleo em oito seções (propósito, fontes, princípios, tokens por papel,
  responsividade, temas, estados e hierarquia, validação e critério de parada) e
  cauda livre a partir da nona (identidade visual, papéis, inventário de telas,
  componentes, padrões de interação, changelog).
- Os sete achados de limpeza acima.

## Final status

Concluída com limitações. Quatro dos cinco contratos de produto nivelados, com
núcleo de seções idêntico nos três projetos do eixo, e a ordem das 21 seeds com
dono único e coberta por teste. O contrato de UI ficou de fora, com motivo e
plano registrados.
