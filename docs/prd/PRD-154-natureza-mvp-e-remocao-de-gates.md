# PRD-154: Natureza MVP descartável e remoção dos gates de ambiente

## Summary

Declarar no contrato que o LV Jiu Jitsu é um MVP descartável — local, HG e produção são simulação sem dado real — e remover as regras que tratam produção como sagrada e que travam a conclusão por divergência documental.

## Demand type

Revisão de governança.

## Current problem

Três regras escritas para um produto com dado real de cliente, aplicadas a um MVP onde nada é real:

| Local | Trecho | Efeito |
|---|---|---|
| `CLAUDE.md:141` | "Produção não é ambiente de experimentação" | Bloqueia o ciclo destrutivo num banco que é recriado por migrate + seeds |
| `CLAUDE.md:97`, `AGENTS.md:145`, `AGENT-WORKFLOW.md:103` | "confirmação explícita de ambiente" para toda escrita em HG | HG é descartável; o gate não protege nada e é cobrado três vezes |
| `AGENTS.md:14` | "Divergência entre fontes bloqueia a conclusão até ser resolvida" | Parada dura por inconsistência documental, num repositório com sete documentos de governança que inevitavelmente divergem |

O terceiro é o mais caro: qualquer divergência entre `CLAUDE.md`, `AGENTS.md`, `AGENT-WORKFLOW.md` e as seis skills vira motivo de bloqueio, e esta auditoria encontrou seis divergências ativas.

O LV também não declara em lugar nenhum a natureza descartável do ambiente.

## Goal

Depois desta PRD, um agente que leia `CLAUDE.md` e `AGENTS.md` conclui que reset, migrate, seeds e deploy são operação normal em qualquer ambiente, e que divergência documental é registrada no fechamento em vez de travar a entrega.

## Context Ledger

### Files read in full

- `CLAUDE.md`, `AGENTS.md`
- `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md`
- `.claude/skills/lv-task-intake/SKILL.md`, `lv-prd`, `lv-django-delivery`, `lv-ui-delivery`, `lv-cleanup-audit`, `lv-prompt-builder`

### Adjacent files consulted

- `.claude/settings.json`, `.claude/settings.local.json` — `deny` e `ask` já vazios.
- `.claude/launch.json` — porta 8000.

### Internet / official documentation

- [Django — settings por ambiente](https://docs.djangoproject.com/en/5.2/topics/settings/) — separação de ambiente é configuração, não política de aprovação.

### Context7 / MCPs / tools verified

- Context7 indisponível na redação. Limitação registrada; nenhuma referência inventada.

### Limitations found

- `.env`, `.env.hg` e `.env.prod` não foram lidos.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: auditoria de governança do projeto, 2026-07-22.
- User approval: instrução explícita de gerar PRDs de correção por repositório.
- Date: 2026-07-22

## Execution prompt

### Persona

Mantenedor da governança de agentes do LV Jiu Jitsu.

### Action

Editar `CLAUDE.md`, `AGENTS.md` e `docs/AGENT-WORKFLOW.md` para declarar a natureza MVP, substituir o gate de ambiente por gate de irreversibilidade e rebaixar a regra de bloqueio por divergência.

### Context

Ler os três arquivos por inteiro. As três ocorrências do gate de HG precisam ser tratadas na mesma entrega.

### Constraints

- Guardas técnicas em código permanecem: `SUPABASE_RESET_CONFIRM`, `DJANGO_ENVIRONMENT`, `DJANGO_DEBUG=False`. Sai o gate **documental** de pedir permissão, não a guarda de execução.
- Não tocar em skills nesta PRD — isso é `PRD-155` e `PRD-156`.
- Menor diff correto: substituir a frase, não reescrever a seção.
- O domínio de pagamento (Asaas, Stripe) **não** é coberto pela liberação. Cobrança em sandbox continua sendo ação externa e mantém autorização explícita.

### Acceptance criteria

- [ ] `CLAUDE.md` ganha uma seção numerada `Natureza do projeto` declarando: MVP descartável; local, HG e prod sem dado real; prod é simulação; qualquer ambiente reconstruível por `migrate` + seeds.
- [ ] Essa seção inclui a cláusula de revogação: no dia em que existir dado real de aluno ou cobrança real em produção, os gates voltam. Sem essa cláusula o critério não é atendido.
- [ ] `CLAUDE.md:141` não contém mais "Produção não é ambiente de experimentação". Verificação: `grep -n "não é ambiente de experimentação" CLAUDE.md` retorna vazio.
- [ ] Nenhum do projeto arquivos contém "confirmação explícita de ambiente". Verificação: `grep -rn "confirmação explícita de ambiente" CLAUDE.md AGENTS.md docs/` retorna vazio.
- [ ] A tabela de gates em `docs/AGENT-WORKFLOW.md` passa a classificar por irreversibilidade: ação irreversível **fora** do repositório (push, deploy externo, chamada a gateway de pagamento, envio de e-mail real) exige autorização; tudo que o repositório reconstrói é operação normal.
- [ ] `migrate`, reset e seeds em HG e prod aparecem na tabela como autorizados sem confirmação adicional.
- [ ] `AGENTS.md:14` deixa de bloquear. Texto exigido: divergência entre fontes é resolvida pela precedência do §1 e registrada no fechamento; ela não interrompe a entrega. Verificação: `grep -n "bloqueia a conclusão" AGENTS.md` retorna vazio.
- [ ] `CLAUDE.md` declara a porta canônica local do projeto.
- [ ] `CLAUDE.md` declara o que **não** existe no LV, no padrão de negação explícita de ambiente.
- [ ] `.\.venv\Scripts\python.exe manage.py check` sem erro após as edições.

### Expected evidence

- Diff do projeto arquivos.
- Saída literal do projeto `grep` de verificação.
- Saída de `manage.py check`.

### Output format

Diff + saídas de comando na seção `Evidence`.

## Scope

- `CLAUDE.md`: seção nova; `:97` e `:141` corrigidas; §11 reescrita; bloco de negação explícita.
- `AGENTS.md`: `:14` rebaixada; `:145` reduzida a referência.
- `docs/AGENT-WORKFLOW.md`: `:103` e a tabela de gates.

## Out of scope

- Skills (`PRD-155`, `PRD-156`).
- Desduplicação geral (`PRD-157`).
- Slash commands (`PRD-158`).
- Qualquer flexibilização de regra de pagamento.

## Impacted files

| Arquivo | Natureza |
|---|---|
| `CLAUDE.md` | edição + seção nova |
| `AGENTS.md` | edição |
| `docs/AGENT-WORKFLOW.md` | edição |

## Risks and edge cases

| Risco | Mitigação |
|---|---|
| Liberação ser lida como permissão para operar cobrança real | Restrição explícita: pagamento permanece como ação externa com autorização. Critério de aceite não altera nenhuma regra de Asaas/Stripe. |
| Remover o bloqueio por divergência esconder inconsistência real | A regra substituta obriga **registrar** a divergência no fechamento; ela deixa de travar, não de aparecer. |
| Correção parcial deixar 1 das 3 cópias do gate de HG | O critério é um `grep` sobre os três arquivos, não inspeção por arquivo. |
| Cláusula de revogação ser esquecida | Critério de aceite dedicado. |

## Rules and constraints

- pt-BR no conteúdo; identificadores em inglês.
- Não criar arquivo novo.

## Plan

- [ ] Context and research
- [ ] Implementation
- [ ] Validation
- [ ] Cleanup audit
- [ ] Documentation

## Test plan

### Tests to author

Nenhum teste automatizado. Verificação por `grep` e `manage.py check`.

### Execution authorization

- Status: authorized

### Execution evidence

Pendente.

## Visual validation

Não aplicável.

## ORM validation

Não aplicável.

## Quality validation

Os três `grep` do critério de aceite mais `manage.py check`.

## Evidence

Pendente.

## Implemented

Pendente.

## Cleanup findings

Pendente.

## Follow-up PRDs

- `PRD-155` — gate condicional de autorização nas skills.
- `PRD-156` — estrutura das skills e índice de PRD.
- `PRD-157` — desduplicação e higiene do CLAUDE.md.
- `PRD-158` — slash commands.

## Deviations from plan

Pendente.

## Pending

Pendente.

## Final status

Não iniciada.
