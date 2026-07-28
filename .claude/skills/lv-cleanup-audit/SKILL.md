---
name: lv-cleanup-audit
description: Use esta skill no final de toda mudança do LV JIU JITSU para revisar o diff e o fluxo tocado, remover resíduos, detectar código morto, legado, duplicação, hardcode, risco e documentação obsoleta, e gerar PRD de follow-up sem expandir o escopo automaticamente.
---

# LV Cleanup Audit

## Quando acionar

No fechamento de toda mudança do LV JIU JITSU.

## Passos

1. Executar `git diff -- .` e `git status --short`.
2. Reler integralmente arquivos alterados, PRD e contratos adjacentes.
3. Procurar código morto, órfãos, duplicação, hardcode, erro mascarado, N+1, temporários, documentação divergente e teste sem contrato.
4. Confirmar referências, remover resíduos introduzidos e corrigir achados dentro do escopo.
5. Preservar mudanças preexistentes e não iniciar refatoração ampla.
6. Se o diff tocar `*/skills/*/SKILL.md`, comparar `.agents`, `.claude` e `.cursor` por hash ou conteúdo byte a byte e falhar a auditoria se divergirem.
7. Para dívida material fora do escopo, criar PRD com `lv-prd`, vincular à atual e parar sem implementar.
8. Atualizar limpeza, evidências, limitações, pendências e status.

## Saída

```text
Diff auditado: <comando executado>
Achados corrigidos no escopo: <lista ou "nenhum">
Follow-up criado: <PRD-NNN ou "nenhum">
Cópias de skill sincronizadas: <sim | não se aplica>
Status: limpo | com follow-up
```

## Parar quando

- O diff do escopo estiver relido, validado e sem resíduo introduzido.
- Se as cópias de skill divergirem, parar com status não limpo.
- Se houver dívida material fora do escopo, parar após criar o follow-up.
- Não declarar o sistema inteiro limpo quando apenas o escopo foi auditado.
