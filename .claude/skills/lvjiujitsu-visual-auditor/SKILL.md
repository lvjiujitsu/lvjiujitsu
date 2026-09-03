---
name: lvjiujitsu-visual-auditor
description: Executa o ciclo do agente visual do LV Jiu Jitsu. Usar para auditar toda a superfície de interface — CSS, HTML e JavaScript — rota por rota em desktop e mobile, tema claro e escuro, exercitando cada elemento interativo, medindo responsividade, rolagem, contraste e alvo de toque pelo navegador interno, abrindo uma PRD por defeito visual, corrigindo o lote em uma única feature e entregando o Pull Request de developer para stage sem fazer merge.
---

# Ciclo canônico

A skill canônica é [`.agents/skills/lvjiujitsu-visual-auditor/SKILL.md`](../../../.agents/skills/lvjiujitsu-visual-auditor/SKILL.md).

Antes de agir, leia integralmente e siga à risca:

1. `CLAUDE.md`;
2. o arquivo canônico acima — ciclo, regras de PRD, matriz de evidência, pendências e falhas;
3. as referências que ele lista, em `.agents/skills/lvjiujitsu-visual-auditor/references/`: `checklist-visual.md` e `sonda.md`.

Não copie nem reescreva esse conteúdo aqui. Qualquer mudança de contrato acontece uma única vez, no arquivo canônico.

# O que é específico deste agente

- **Owner do lease é `visual`**, no checkpoint `visual.json`. Todo comando de `scripts/visual_state.py` usa `--owner visual`.
- **Ferramentas**: Bash para `scripts/visual_state.py`; ferramentas de navegador do Claude Code (`mcp__Claude_Browser__*`) para navegar, redimensionar para desktop e mobile, trocar tema, exercitar estados e capturar screenshot.
- **Lease ocupado**: se `visual_state.py acquire --owner visual` falhar, encerrar sem escrita e retomar na próxima execução — isso é esperado, não é falha.

# Ferramentas fechadas

- `.agents/skills/lvjiujitsu-visual-auditor/scripts/visual_state.py`
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/state.py` (somente reserva de PRD, com o owner da trilha)
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/git_flow.py`
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/quality_scan.py`

Não substituir operações desses scripts por comandos Git improvisados.
