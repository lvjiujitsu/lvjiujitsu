---
name: lv-prompt-builder
description: "Use esta skill quando o usuário trouxer um problema cru e pedir o melhor prompt de execução para o Claude no LV JIU JITSU. Classifica a demanda, lê os contratos pertinentes e gera um execution prompt auto-suficiente no padrão LV, com skills na ordem, arquivos a ler e gates de PRD/UI/teste/pagamento consolidados. Não implementa: entrega o prompt e para."
argument-hint: <problema a resolver>
disable-model-invocation: true
---

# LV Prompt Builder

## Quando acionar

Quando o usuário pedir para transformar um problema cru em um prompt de execução autossuficiente. O produto é o prompt; esta skill não implementa.

## Passos

1. Tratar a entrada como problema a diagnosticar, não como ordem de implementação.
2. Se estiver vazia ou ambígua a ponto de não nomear o fluxo, fazer uma pergunta objetiva e parar.
3. Ler `AGENTS.md`, `CLAUDE.md` e contratos pertinentes sem editar arquivos.
4. Classificar pela categoria de `docs/AGENT-WORKFLOW.md` e decidir PRD, UI, comportamento testável e pagamento.
5. Ordenar skills: `lv-task-intake`, `lv-prd`, `lv-ui-delivery`, `lv-django-delivery`, `lv-cleanup-audit`, conforme aplicável.
6. Listar arquivos e contratos a ler integralmente por camada.
7. Consolidar autorização do escopo e gates restantes conforme `AGENTS.md`.
8. Gerar bloco único no formato Execution prompt de `docs/PRD-STANDARD.md`.
9. Não inventar arquivo, rota, skill, comando, fonte ou validação.

## Saída

```text
Execution prompt
Persona: ...
Action: ...
Context: ...
Constraints: ...
Acceptance criteria: ...
Test policy: ...
Required skills: ...
Authorizations and gates: ...
Expected evidence: ...
Output format: ...
```

## Parar quando

- O prompt autossuficiente estiver entregue com os gates externos restantes.
- Se o problema estiver vazio ou materialmente ambíguo, parar após uma pergunta objetiva.
- Não criar PRD, alterar código ou continuar para implementação.
