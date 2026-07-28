---
name: lv-prd
description: Use esta skill para criar ou atualizar PRDs do LV JIU JITSU antes de mudanças relevantes. Construa uma spec comportamental com contexto integral, pesquisa oficial, skills requeridas, critérios verificáveis, execução de testes e evidência real.
---

# LV PRD

## Quando acionar

Antes de toda mudança relevante que exija especificação comportamental verificável.

## Passos

1. Confirmar `lv-task-intake` e ler `docs/PRD-STANDARD.md`.
2. Consultar `docs/prd/README.md` como índice canônico, escolher o próximo número sem duplicar e atualizar o índice.
3. Registrar arquivos lidos, fontes, ferramentas, limitações e autorização.
4. Especificar problema, objetivo, escopo, fora de escopo, riscos, critérios e evidências.
5. Definir plano test-first, comandos reais, browser, ORM e limpeza proporcionais.
6. Para UI, incluir hierarquia, wireframe, máquina de estados e gate do `AGENTS.md`.
7. Para pagamentos, distinguir redirect, webhook, gateway, sessão, ORM e ambiente.
8. Atualizar evidências, implementação, limpeza, desvios, pendências e status durante a execução.

## Saída

```text
PRD: <PRD-NNN e caminho>.
Autorização: <registrada | pendente>.
Critérios verificáveis: <resumo>.
Evidência esperada: <comandos, testes, browser e ORM>.
Status: <não iniciada | em execução | concluída | não concluída>.
```

## Parar quando

- A PRD e o índice estiverem atualizados com critérios verificáveis.
- Se o número estiver duplicado ou reservado, parar e corrigir o índice antes do código.
- Se faltar autorização necessária, parar com status pendente.
- Não marcar checklist nem declarar teste executado sem evidência real.
