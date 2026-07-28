---
name: lv-parity-audit
description: "Use quando a demanda for auditar a coerência interna do LV JIU JITSU — estrutura, contratos, infraestrutura, skills e conhecimento — e produzir uma lista de divergências com evidência de comando. Audita este repositório contra o próprio contrato, nunca contra outro projeto."
disable-model-invocation: true
---

# LV JIU JITSU Parity Audit

## Quando acionar

Por pedido explícito do operador, quando ele quiser saber se o repositório
ainda cumpre o próprio contrato — antes de uma rodada de mudanças estruturais,
depois de uma série de PRDs, ou quando algo "parece fora do lugar".

Não acionar como parte de outra entrega: auditar no meio de uma implementação
mistura diagnóstico com mudança.

## Passos

1. Rodar os cinco gates e registrar a saída real de cada um:

`powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe scripts\build_prd_index.py --check
.\.venv\Scripts\python.exe scripts\validate_skill_frontmatter.py
.\.venv\Scripts\python.exe -m pip check
`

2. Conferir que todo link de `CLAUDE.md`, `AGENTS.md`, `README.md` e
   `docs/*.md` resolve em disco. Menção negativa e nome genérico de arquivo
   produzem falso positivo: conferir cada achado à mão.
3. Conferir que os quatro arquivos de ambiente declaram o mesmo conjunto de
   chaves, e que toda chave declarada tem leitor em `system/` ou em
   settings. Reportar **nome** de chave, nunca valor.
4. Conferir que `SUPABASE_RESET_CONFIRM` **não** está declarada em nenhum
   arquivo de ambiente: a ausência é a guarda do reset remoto.
5. Conferir que toda dependência de `requirements.txt` tem importador, e que
   todo importador tem dependência declarada.
6. Conferir que as sete skills existem e são idênticas em `.claude/skills/`,
   `.agents/skills/` e `.cursor/skills/`, por SHA-256.
7. Contar comentário e docstring em `.py`, `.html`, `.css` e `.js` fora
   de `migrations/`. O contrato exige zero (`AGENTS.md` §10).
8. Buscar arquivo órfão: diretório de dado sem leitor, script sem invocador,
   teste vazio, documento substituído. **Provar a orfandade** por busca antes
   de propor remoção — nome que parece legado não é prova.
9. Conferir que `docs/prd/` não tem número duplicado nem arquivo fora do
   padrão, e que o índice está em dia.
10. Rodar a suíte completa e comparar a contagem com a da última PRD fechada.

## Saída

`	ext
Gates: check=<> migrations=<> indice=<> skills=<> pip=<>
Links quebrados: <nenhum | lista, com falso positivo marcado>
Chaves de ambiente: <n>/<n>/<n>/<n> — conjunto idêntico: <sim | não>
SUPABASE_RESET_CONFIRM declarada: <0 | ONDE — defeito>
Dependência sem importador: <nenhuma | lista>
Importador sem dependência: <nenhum | lista>
Skills idênticas nas três plataformas: <sim | divergências>
Comentários/docstrings: py=<> html=<> css/js=<>
Órfãos com orfandade provada: <nenhum | lista>
PRDs: <n> arquivos, <n> números, duplicados=<>, gaps=<>
Suíte: <quantidade e resultado>
Divergências que exigem decisão do operador: <lista>
`

## Parar quando

- Um gate falhar: reportar a saída real e parar; auditoria sobre base vermelha
  não vale.
- Um achado depender de decisão de produto: registrar e perguntar, não decidir
  sozinho.
- Um órfão não tiver orfandade provada: reportar como suspeita, nunca como
  achado.
- Todos os gates verdes e a lista fechada: entregar o relatório e parar. Esta
  skill **não** corrige nada; correção exige PRD.