---
name: lv-task-intake
description: Use esta skill no início de qualquer demanda do LV JIU JITSU que possa gerar diagnóstico, plano, PRD ou alteração. Classifique a demanda, faça preflight, leia o fluxo integralmente, pesquise fontes atuais, confirme entendimento e obtenha a autorização necessária antes de editar.
---

# LV Task Intake

## Executar

1. Ler `AGENTS.md` e `CLAUDE.md` integralmente.
2. Classificar a demanda.
3. Verificar worktree, `.venv`, shell, comandos e ferramentas relevantes.
4. Identificar arquivos diretos e contratos adjacentes.
5. Ler cada arquivo relevante por inteiro.
6. Usar Context7 para bibliotecas, frameworks, SDKs, APIs e CLIs.
7. Consultar documentação oficial atual e guardar os links.
8. Identificar premissas, limitações e risco de expansão.
9. Responder de forma mínima:

```text
Entendi: <resultado>.
Escopo: <fluxos/arquivos>.
Validação: <browser, checks e ORM; testes somente se autorizados>.
Posso implementar?
```

## Autorizar

- Tratar ordem explícita de implementação como autorização do escopo descrito.
- Pedir nova aprovação para expansão, UI sem proposta aprovada, testes, ORM mutável, migrations, reset, seeds, pagamento real, deploy ou push.
- Preservar mudanças preexistentes do usuário.

## Restringir

- Não expor raciocínio interno.
- Não repetir o prompt.
- Não inventar rota, gateway, comando, migration, seed ou evidência.
- Não assumir que documentação histórica supera o código atual.
