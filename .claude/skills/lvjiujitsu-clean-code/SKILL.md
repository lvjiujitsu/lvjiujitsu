---
name: lvjiujitsu-clean-code
description: Executa o ciclo do agente de limpeza do LV JIU JITSU. Usar para varrer o repositório inteiro em busca de comentário e docstring, hardcode, mistura de idioma entre código em inglês e interface em português, e desvio de governança em nome de arquivo; abrir uma PRD por defeito, corrigir o lote em uma única feature e entregar o Pull Request de developer para stage sem fazer merge.
---

# Ciclo canônico

A skill canônica é [`.agents/skills/lvjiujitsu-clean-code/SKILL.md`](../../../.agents/skills/lvjiujitsu-clean-code/SKILL.md).

Antes de agir, leia integralmente e siga à risca:

1. `CLAUDE.md`;
2. o arquivo canônico acima — ciclo, regras de PRD, critério de cobertura, pendências e falhas;
3. a referência que ele lista, em `.agents/skills/lvjiujitsu-clean-code/references/checklist-limpeza.md`.

Não copie nem reescreva esse conteúdo aqui. Qualquer mudança de contrato acontece uma única vez, no arquivo canônico.

# O que é específico deste agente

- **Owner do lease é `clean`**, no checkpoint `clean.json`. Todo comando de `scripts/clean_state.py` usa `--owner clean`.
- **Ferramentas**: Bash para `scripts/clean_state.py` e para `quality_scan.py` da skill de ciclo autônomo, com caminho relativo à raiz do repositório.
- **Lease ocupado**: se `clean_state.py acquire --owner clean` falhar, encerrar sem escrita e retomar na próxima execução — isso é esperado, não é falha.

# Ferramentas fechadas

- `.agents/skills/lvjiujitsu-clean-code/scripts/clean_state.py`
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/state.py` (somente reserva de PRD, com o owner da trilha)
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/git_flow.py`
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/quality_scan.py`

Não substituir operações desses scripts por comandos Git improvisados.
