---
name: lvjiujitsu-autonomous-developer
description: Executa, no Claude Code, o mesmo ciclo rigoroso compartilhado com o agente Codex do LV Jiu Jitsu — sincronizar stage em developer, retomar uma auditoria global comprovável arquivo por arquivo e linha por linha, revisar o avanço recente do Codex como auditor sênior, auditar diffs somente após concluir a cobertura global, criar uma PRD por defeito, corrigir todas as PRDs do lote em uma única feature e worktree, validar Django, segurança e UI, publicar exclusivamente em developer e abrir ou atualizar o Pull Request para stage sem fazer merge.
---

# Ciclo compartilhado

Este agente e o agente Codex (`.codex/agents/lvjiujitsu-agent-developer.toml`) executam **o mesmo ciclo mecânico**, para nunca divergirem em critério. A skill canônica é [`.agents/skills/lvjiujitsu-autonomous-developer/SKILL.md`](../../../.agents/skills/lvjiujitsu-autonomous-developer/SKILL.md).

Antes de agir, leia integralmente e siga à risca:

1. `CLAUDE.md`;
2. o arquivo canônico acima — resultado, ciclo em 16 passos, regras de PRD, critério de cobertura, pendências, ambientes e falhas;
3. as referências que ele lista, todas em `.agents/skills/lvjiujitsu-autonomous-developer/references/`: `auditoria-global.md`, `django-mvt.md`, `seguranca.md`, `ui-browser.md`, `git-worktree.md`, `quality-gates.md`, `checklist-auditoria.md`.

O `checklist-auditoria.md` é obrigatório antes de cada `state.py audit`, não uma leitura de apoio: verificação não executada é arquivo não auditado. E cada rodada reaudita o inventário inteiro — arquivo sem achado numa rodada volta a `pending` na seguinte.

Não copie nem reescreva esse conteúdo aqui. Qualquer mudança de contrato acontece uma única vez, no arquivo canônico, e vale para os dois agentes ao mesmo tempo.

# O que é específico deste agente

- **Owner do lease é `claude`.** Todo comando de `scripts/state.py` usa `--owner claude`. Nunca usar `--owner codex` nem reaproveitar um lease de outro owner.
- **Ferramentas**: use a ferramenta Bash para `scripts/state.py`, `scripts/git_flow.py` e `scripts/quality_scan.py`, com caminho relativo à raiz do repositório (ex.: `.agents/skills/lvjiujitsu-autonomous-developer/scripts/state.py`). Use as ferramentas de navegador do Claude Code (`mcp__Claude_Browser__*`) para a matriz de evidência de `ui-browser.md`.
- **Papel de auditor sênior**: além do ciclo completo, revise com lente crítica os commits e PRDs mais recentes produzidos pelo agente Codex desde a última execução deste agente. Um problema real encontrado nessa revisão vira PRD própria, com o mesmo rigor de qualquer outro achado.
- **Lease ocupado pelo Codex**: se `state.py acquire --owner claude` falhar, encerrar imediatamente sem nenhuma escrita e relatar que o ciclo será retomado na próxima execução — isso é esperado, não é falha do agente.

# Ferramentas fechadas

- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/state.py` para lease, inventário, checkpoint, cobertura e retomada;
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/git_flow.py` para sincronização, worktree, publicação, PR e limpeza;
- `.agents/skills/lvjiujitsu-autonomous-developer/scripts/quality_scan.py` para comentários, docstrings, resíduos e integridade do diff.

Não substituir operações desses scripts por comandos Git improvisados.
