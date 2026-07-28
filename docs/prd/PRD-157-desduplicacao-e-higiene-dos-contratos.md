# PRD-157: Desduplicação dos contratos e higiene do CLAUDE.md

## Summary

Atribuir dono único a cada regra de governança do LV, mover para o `AGENTS.md` o procedimento que hoje vive no `CLAUDE.md`, e remover do `CLAUDE.md` os fatos que envelhecem sozinhos.

## Demand type

Revisão de governança.

## Current problem

**1. Procedimento dentro do arquivo de fatos.** `CLAUDE.md:5` declara que "Procedimentos pertencem ao `AGENTS.md`". Contradizem essa própria linha:

| Linha | Conteúdo | Natureza real |
|---|---|---|
| `CLAUDE.md:68` | "Registrar comando e resultado" | procedimento |
| `CLAUDE.md:132-135` | regra de proposta visual aprovada | procedimento e permissão |
| `CLAUDE.md:140-142` | política de produção | permissão |

**2. Duplicação factual entre `AGENTS.md` e `CLAUDE.md`.** `AGENTS.md:114-127` (§9 Django MVT) reproduz a árvore de camadas de `CLAUDE.md:24-37`. Dois pontos de manutenção para o mesmo fato — e as duas cópias respondem à mesma pergunta, diferente do caso legítimo em que cada arquivo responde a uma pergunta distinta.

**3. Fato com patch-level pinado.** `CLAUDE.md:15` fixa "Python 3.12.10, Django 5.2.14 LTS". O patch-level envelhece a cada `pip install -r requirements.txt`, e a fonte exata da versão é o `requirements.txt`, não o contrato.

## Goal

Depois desta PRD, alterar uma regra de governança do LV exige editar exatamente um arquivo, e o `CLAUDE.md` contém apenas fatos que não expiram.

## Context Ledger

### Files read in full

- `CLAUDE.md`, `AGENTS.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`
- `.claude/skills/*/SKILL.md` (seis arquivos)

### Adjacent files consulted

- `requirements.txt` — fonte exata das versões.
- `docs/UI-SCREEN-CONTRACT.md`, `docs/OPERACAO-BANCO-SEEDS.md` — donos candidatos.

### Internet / official documentation

- [Django 5.2 LTS — release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/) — confirma que a série LTS é a informação estável; o patch não é.

### Context7 / MCPs / tools verified

- Context7 indisponível na redação. Limitação registrada.

### Limitations found

- Nenhuma.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: auditoria de governança, 2026-07-22.
- User approval: instrução explícita de gerar PRDs de correção.
- Date: 2026-07-22

## Execution prompt

### Persona

Mantenedor da governança de agentes do LV Jiu Jitsu.

### Action

Aplicar a matriz de propriedade, mover procedimento do `CLAUDE.md` para o `AGENTS.md`, e desfixar o patch-level.

### Context

Matriz de propriedade a aplicar e a registrar em `AGENTS.md` §2:

| Assunto | Dono único | Quem referencia |
|---|---|---|
| Fatos do produto, stack, ambientes, portas | `CLAUDE.md` | todos |
| Precedência, idioma, gates de autorização, fechamento | `AGENTS.md` | skills |
| Procedimento detalhado do ciclo | `docs/AGENT-WORKFLOW.md` | `AGENTS.md`, skills |
| Formato e numeração de PRD | `docs/PRD-STANDARD.md` | `lv-prd` |
| Contrato visual e de fluxo | `docs/UI-SCREEN-CONTRACT.md` | `lv-ui-delivery` |
| Banco, ciclo destrutivo e seeds | `docs/OPERACAO-BANCO-SEEDS.md` | `CLAUDE.md`, `AGENTS.md` |
| Diferenças por ferramenta | `docs/PLATFORM-ADAPTERS.md` | `AGENTS.md` |

### Constraints

- Referência é uma linha com caminho, não um resumo. Resumo é duplicação com perda.
- `AGENTS.md` §9 pode manter a **tabela de responsabilidade** por camada (é protocolo) se `CLAUDE.md` §2 mantiver apenas a **árvore de diretórios** (é fato), e se houver uma referência cruzada explícita dizendo isso. Caso contrário, uma das duas sai.
- Não alterar a semântica de nenhuma regra nesta PRD — aqui só se decide onde ela vive.
- `CLAUDE.md` mantém a tabela de comandos; o que sai é a instrução de conduta ("Registrar comando e resultado").

### Acceptance criteria

- [ ] `AGENTS.md` §2 contém a matriz de propriedade acima, com as sete linhas.
- [ ] `CLAUDE.md:68` não contém mais instrução de conduta; a regra "Registrar comando e resultado" existe em `AGENTS.md` ou `docs/AGENT-WORKFLOW.md`, em um único lugar. Verificação: `grep -rn "Registrar comando e resultado" --include=*.md .` retorna 1 arquivo.
- [ ] `CLAUDE.md:132-135` e `:140-142` não contêm mais regra de permissão; o conteúdo correspondente vive em `AGENTS.md`. Após `PRD-154` e `PRD-155`, o que restar dessas linhas é fato ou referência.
- [ ] A árvore de camadas Django existe como fato em exatamente um arquivo, e a referência cruzada entre `AGENTS.md` §9 e `CLAUDE.md` §2 está escrita explicitamente.
- [ ] `CLAUDE.md:15` deixa de fixar patch-level. Texto exigido: "Python 3.12 / Django 5.2 LTS", com `requirements.txt` apontado como fonte exata. Verificação: `grep -n "3.12.10\|5.2.14" CLAUDE.md` retorna vazio.
- [ ] Nenhuma outra linha do `CLAUDE.md` fixa versão de patch, contagem de arquivos ou quantidade que muda com o uso. Verificação: varredura manual registrada, listando cada número encontrado e por que ele é estável.
- [ ] Nenhuma referência aponta para arquivo inexistente. Verificação: para cada caminho citado em `CLAUDE.md`, `AGENTS.md` e `docs/*.md`, `test -f` retorna verdadeiro.
- [ ] `wc -l CLAUDE.md` e `wc -l AGENTS.md` registrados antes e depois.
- [ ] `.\.venv\Scripts\python.exe manage.py check` sem erro.

### Expected evidence

- Diff de `CLAUDE.md`, `AGENTS.md` e dos docs tocados.
- Saída dos `grep` de contagem.
- Saída do verificador de links.
- `wc -l` antes e depois.

### Output format

Diff + saídas de comando na seção `Evidence`.

## Scope

- `CLAUDE.md`: linhas 15, 68, 132-135, 140-142 e §2.
- `AGENTS.md`: §2 (matriz) e §9.
- `docs/AGENT-WORKFLOW.md`: recebe o procedimento movido, se for o dono escolhido.

## Out of scope

- Alterar a semântica de regra (`PRD-154`, `PRD-155`).
- Skills (`PRD-156`).
- Slash commands (`PRD-158`).
- `docs/archive/static-documentation-legacy/` — legado arquivado, não é contrato ativo.

## Impacted files

| Arquivo | Natureza |
|---|---|
| `CLAUDE.md` | remoção de procedimento e de versão pinada |
| `AGENTS.md` | matriz nova; §9 ajustada |
| `docs/AGENT-WORKFLOW.md` | recebe procedimento movido |

## Risks and edge cases

| Risco | Mitigação |
|---|---|
| Mover regra e perdê-la no caminho | Cada `grep` de contagem exige exatamente 1 arquivo restante, provando que a regra sobreviveu em algum lugar. |
| Referência quebrar em renomeação futura | Critério inclui verificação de existência de todo caminho citado. |
| Ambiguidade entre árvore de diretórios e tabela de responsabilidade | Critério exige a referência cruzada explícita, ou a remoção de uma das duas. |
| Conflito de edição com `PRD-154` e `PRD-155`, que tocam as mesmas linhas | Esta PRD é executada **depois** das duas; a dependência está declarada em `Final status`. |

## Rules and constraints

- pt-BR no conteúdo; identificadores em inglês.
- Menor diff correto.
- Não criar arquivo novo.

## Plan

- [ ] Context and research
- [ ] Implementation
- [ ] Validation
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

Nenhum teste Django.

### Execution authorization

- Status: authorized

### Execution evidence

Pendente.

## Visual validation

Não aplicável.

## ORM validation

Não aplicável.

## Quality validation

`grep` de contagem, verificador de links, `wc -l`, `manage.py check`.

## Evidence

Pendente.

## Implemented

Pendente.

## Cleanup findings

Pendente.

## Follow-up PRDs

- `PRD-158` — slash commands.

## Deviations from plan

Pendente.

## Pending

Pendente.

## Final status

Não iniciada. Depende de `PRD-154` e `PRD-155`, que reescrevem as mesmas linhas do `CLAUDE.md`.
