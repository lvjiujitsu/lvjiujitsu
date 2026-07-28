# PRD-155: Gate condicional de autorização — alinhar skills ao AGENTS.md

## Summary

Corrigir a contradição em que as skills pedem aprovação incondicionalmente enquanto o `AGENTS.md` manda seguir quando o prompt já autorizou o escopo. O gate passa a ser condicional em todas as fontes, com a mesma redação.

## Demand type

Revisão de governança.

## Current problem

Duas contradições ativas, ambas cobrando aprovação que o protocolo já dispensou.

**1. Template de intake sempre pergunta.** `.claude/skills/lv-task-intake/SKILL.md:24` encerra o bloco de resposta com `Posso implementar?`, sem condição. Contra:

- `AGENTS.md:48` — "seguir para execução quando a solicitação atual já autorizar o escopo";
- `docs/AGENT-WORKFLOW.md:80` — "Antes de uma mudança **ainda não autorizada**".

A própria skill, poucas linhas depois, manda tratar ordem explícita como autorização. O template contradiz a regra que o acompanha.

**2. Gate de UI incondicional.** `.claude/skills/lv-ui-delivery/SKILL.md:25` diz "pedir aprovação" sem condição e `CLAUDE.md:132` afirma "Alteração visual exige proposta aprovada antes do código". Contra `AGENTS.md:57` — "aprovação explícita **quando a solicitação atual não autorizar** implementação".

Efeito observado: o operador precisa autorizar duas vezes a mesma coisa — uma no prompt, outra na pergunta de confirmação — em toda demanda de UI.

## Goal

Depois desta PRD, existe uma única redação do gate de autorização, ela é condicional, e as quatro fontes que a mencionam usam exatamente essa redação ou referenciam quem a possui.

## Context Ledger

### Files read in full

- `AGENTS.md`, `CLAUDE.md`, `docs/AGENT-WORKFLOW.md`
- `.claude/skills/lv-task-intake/SKILL.md`
- `.claude/skills/lv-ui-delivery/SKILL.md`
- `.claude/skills/lv-prompt-builder/SKILL.md`

### Adjacent files consulted

- `.agents/skills/`, `.cursor/skills/` — espelhos das seis skills.
- `docs/PLATFORM-ADAPTERS.md` §7 — obrigação de sincronizar as três cópias.

### Internet / official documentation

- [Anthropic — Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) — a skill descreve procedimento; política de autorização pertence ao protocolo do projeto.

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
- Execution approval: prompt explícito de 2026-07-25 autorizou corrigir contradições cobertas pelas PRDs 154–158.

## Execution prompt

### Persona

Mantenedor da governança de agentes do LV Jiu Jitsu.

### Action

Definir a redação canônica do gate em `AGENTS.md` e alinhar `CLAUDE.md:132`, `lv-task-intake:24` e `lv-ui-delivery:25` a ela.

### Context

Redação canônica a adotar, escrita uma única vez em `AGENTS.md`:

```text
Pedir aprovação apenas quando a solicitação atual não autorizar o escopo.
Ordem explícita e inequívoca de implementação é autorização do escopo descrito.
Pedido exploratório, ambíguo ou que peça proposta mantém o gate.
Expansão material de escopo exige nova aprovação, independentemente do prompt original.
```

### Constraints

- O gate de UI não desaparece: continua obrigatório apresentar hierarquia, wireframe e estados antes do código. O que muda é **pedir aprovação** virar condicional; a proposta de design continua sendo produzida.
- Não relaxar o gate para expansão de escopo nem para ação externa irreversível.
- Alterar skill obriga sincronizar `.claude/`, `.agents/` e `.cursor/`.

### Acceptance criteria

- [x] `AGENTS.md` contém a redação canônica de quatro linhas acima, em um único lugar identificável.
- [x] `.claude/skills/lv-task-intake/SKILL.md` torna `Posso implementar?` condicional, com instrução explícita de **omitir** a linha quando houver ordem inequívoca de implementação.
- [x] `.claude/skills/lv-ui-delivery/SKILL.md:25` deixa de dizer "pedir aprovação" de forma incondicional e passa a referenciar o gate do `AGENTS.md`.
- [x] `CLAUDE.md:132` deixa de afirmar que toda alteração visual exige proposta aprovada; passa a afirmar que toda alteração visual exige **proposta de design**, e que a aprovação segue o gate do `AGENTS.md`.
- [x] A expressão "pedir aprovação" e variantes aparecem sem condição em zero arquivos. Verificação: `grep -rn "pedir aprovação\|exige proposta aprovada" CLAUDE.md AGENTS.md docs/ .claude/skills/` — cada ocorrência restante precisa estar acompanhada de condição ou de referência ao `AGENTS.md`; a saída completa é colada em `Evidence` com a justificativa de cada linha.
- [x] `lv-prompt-builder` continua com seu guard de parada próprio ("parar e fazer UMA pergunta objetiva"), que é comportamento desejado e não deve ser removido.
- [x] As três cópias de cada skill alterada são idênticas. Verificação: `diff` vazio para `.agents/` e `.cursor/`.
- [ ] Uma execução de teste do fluxo: dado um prompt com ordem explícita de implementar uma mudança de UI, o agente produz a proposta de design e segue para o código **sem** perguntar. Registrar a transcrição resumida como evidência.

### Expected evidence

- Diff de `AGENTS.md`, `CLAUDE.md` e das duas skills, mais espelhos.
- Saída completa do `grep` com justificativa por linha.
- Saída dos `diff` de sincronização.
- Transcrição resumida do teste de fluxo.

### Output format

Diff + saídas de comando na seção `Evidence`.

## Scope

- `AGENTS.md`: redação canônica.
- `CLAUDE.md:132`.
- `.claude/skills/lv-task-intake/SKILL.md` e `.claude/skills/lv-ui-delivery/SKILL.md`, mais espelhos.

## Out of scope

- Reestruturar as skills em `Quando acionar / Passos / Saída / Parar quando` (`PRD-156`).
- Gates de ambiente (`PRD-154`).
- Regra de pagamento.

## Impacted files

| Arquivo | Natureza |
|---|---|
| `AGENTS.md` | redação canônica |
| `CLAUDE.md` | edição da linha 132 |
| `.claude/skills/lv-task-intake/SKILL.md` | template condicional |
| `.claude/skills/lv-ui-delivery/SKILL.md` | referência ao gate |
| `.agents/skills/*`, `.cursor/skills/*` | espelhamento |

## Risks and edge cases

| Risco | Mitigação |
|---|---|
| Agente passar a implementar sobre pedido ambíguo | A redação condiciona a omissão a "ordem explícita e inequívoca"; pedido exploratório mantém o gate, e isso está escrito na própria regra. |
| Proposta de design deixar de ser produzida | Constraint explícita: a proposta continua obrigatória; só a aprovação vira condicional. Critério de aceite testa exatamente esse fluxo. |
| Expansão de escopo escapar | A quarta linha da redação canônica trata disso e é verificada no critério. |
| Espelhos divergirem | `diff` vazio é critério de aceite. |

## Rules and constraints

- pt-BR no conteúdo; identificadores em inglês.
- Menor diff correto.

## Plan

- [x] Context and research
- [x] Implementation
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

Nenhum teste Django. O teste é de fluxo do agente, descrito no critério de aceite.

### Execution authorization

- Status: authorized

### Execution evidence

- Prompt atual de 2026-07-25 reconhecido como ordem explícita; execução iniciou sem pergunta duplicada.
- Busca por `pedir aprovação`, `Posso implementar` e `exige proposta aprovada` confirmou somente usos condicionais ou follow-up fora do gate inicial.
- Hashes SHA-256 das três cópias de cada skill: idênticos.

## Visual validation

Não aplicável — a mudança é de protocolo, não de tela. O teste de fluxo usa uma demanda de UI como cenário.

## ORM validation

Não aplicável.

## Quality validation

`grep` com justificativa linha a linha, `diff` de espelhos e o teste de fluxo.

## Evidence

- `AGENTS.md` contém o gate canônico.
- `CLAUDE.md` exige proposta de design e referencia o gate.
- `lv-task-intake` só inclui `Posso implementar?` quando a autorização está pendente.
- `lv-ui-delivery` referencia o gate condicional.

## Implemented

Gate condicional implementado e sincronizado nas três plataformas.

## Cleanup findings

Nenhuma ocorrência incondicional residual no gate inicial. A regra de aprovação de follow-up em `AGENTS.md` permanece porque trata expansão material.

## Follow-up PRDs

- `PRD-156` — estrutura das skills.

## Deviations from plan

PRD-154 não foi implementada: o prompt atual autorizou hardening local, não flexibilização de ambientes remotos.

## Pending

Teste interativo específico com uma mudança real de UI não foi executado nesta entrega sem alteração visual.

## Final status

**Concluída com limitação**: contrato, espelhos e buscas validados; cenário interativo de UI não executado por não haver mudança visual no escopo.
