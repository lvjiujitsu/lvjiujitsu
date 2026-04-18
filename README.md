# LV Jiu Jitsu

Sistema de gestão para academia de jiu-jitsu. Django 4.1.13, Python 3.12, SQLite.

## Governança do agente

Este projeto adota regime **control-first**:
- controle e auditoria sobre velocidade;
- contexto máximo obrigatório;
- uso de MCPs quando relevantes;
- coerência entre AGENTS/CLAUDE/Cursor Rules;
- redução de alucinação por evidência e validação.

Arquivos de governança:
- `AGENTS.md` — protocolo universal do agente
- `CLAUDE.md` — contexto persistente do projeto
- `.cursor/rules/` — regras operacionais sempre ativas
