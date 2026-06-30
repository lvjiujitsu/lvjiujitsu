---
name: lv-prd
description: Use esta skill para criar ou atualizar PRDs do LV JIU JITSU antes de mudanças relevantes. Construa uma spec comportamental com contexto integral, pesquisa oficial, skills requeridas, critérios verificáveis, execução de testes e evidência real.
---

# LV PRD

## Preparar

1. Ler `docs/PRD-STANDARD.md`.
2. Confirmar que `lv-task-intake` foi concluída.
3. Encontrar o próximo número livre.
4. Registrar arquivos, fontes, ferramentas e limitações.
5. Usar Context7 e documentação oficial quando aplicável.

## Especificar

Incluir problema, objetivo, escopo, fora de escopo, riscos, arquivos, skills, autorização registrada, critérios, evidência, plano test-first, execução de testes, browser, ORM e limpeza.

Para UI, incluir hierarquia, wireframe, máquina de estados e aprovação.

Para pagamentos, distinguir redirect, webhook, gateway, sessão, ORM e ambiente.

## Manter

- Não marcar checklist sem evidência.
- Diferenciar teste escrito de executado.
- Não declarar Red ou Green sem execução real.
- Atualizar `Evidence`, `Implemented`, `Cleanup findings`, `Deviations`, `Pending` e `Final status`.

## Restringir

- Não criar PRD vazia.
- Não inventar rota, gateway, comando ou resultado.
- Não implementar follow-up sem nova aprovação.
