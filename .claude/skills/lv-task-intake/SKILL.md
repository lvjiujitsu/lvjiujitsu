---
name: lv-task-intake
description: Use esta skill no início de qualquer demanda do LV JIU JITSU que possa gerar diagnóstico, plano, PRD ou alteração. Classifique a demanda, faça preflight, leia o fluxo integralmente, pesquise fontes atuais, confirme entendimento e registre a autorização do prompt antes de editar.
---

# LV Task Intake

## Quando acionar

No início de toda demanda que possa gerar diagnóstico, plano, PRD ou alteração.

## Passos

1. Ler `AGENTS.md` e `CLAUDE.md` integralmente.
2. Classificar a demanda e verificar worktree, `.venv`, shell e ferramentas.
3. Identificar e ler integralmente arquivos diretos e contratos adjacentes.
4. Usar Context7 para bibliotecas, frameworks, SDKs, APIs e CLIs e consultar documentação oficial atual.
5. Registrar premissas, limitações, validação e risco de expansão.
6. Tratar ordem explícita e inequívoca como autorização do escopo descrito.
7. Pedir aprovação somente quando o pedido for exploratório, ambíguo, pedir proposta ou ampliar materialmente o escopo.
8. Preservar mudanças preexistentes e não inventar evidência.

## Saída

```text
Entendido: <resultado>.
Escopo: <fluxos/arquivos>.
Validação: <browser, checks, testes e ORM local proporcionais>.
Autorização: <registrada pelo prompt | pendente>.
Posso implementar? <incluir somente quando a autorização estiver pendente>
```

## Parar quando

- O contexto, o escopo, a validação e a autorização estiverem registrados.
- Se faltar informação que altere materialmente o resultado, parar com uma pergunta objetiva.
- Se uma fonte ou ferramenta obrigatória estiver indisponível, parar a conclusão e registrar a limitação.
