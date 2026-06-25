---
name: lv-cleanup-audit
description: Use esta skill no final de toda mudança do LV JIU JITSU para revisar o diff e o fluxo tocado, remover resíduos, detectar código morto, legado, duplicação, hardcode, risco e documentação obsoleta, e gerar PRD de follow-up sem expandir o escopo automaticamente.
---

# LV Cleanup Audit

## Auditar

1. Ler o diff completo da tarefa.
2. Reler integralmente os arquivos alterados.
3. Verificar contratos adjacentes e PRD.
4. Procurar código morto, órfãos, duplicação, hardcode, erro mascarado, N+1, comentário redundante, temporários, documentação divergente e teste sem contrato.
5. Confirmar referências antes de remover.

## Corrigir

- Remover resíduos introduzidos.
- Corrigir achados dentro do escopo.
- Preservar mudanças preexistentes.
- Não iniciar refatoração ampla como limpeza.

## Criar follow-up

Para dívida material fora do escopo:

1. criar nova PRD com `lv-prd`;
2. registrar evidência, risco e arquivos;
3. vincular à PRD atual;
4. parar;
5. pedir aprovação.

## Fechar

Atualizar limpeza, achados residuais, evidências, limitações e status. Não declarar o sistema inteiro limpo quando apenas o escopo foi auditado.
