# PRD-172: Limpeza estrutural e código sem comentário

## Summary

Remove a documentação legada arquivada, o arquivo de teste vazio e a exceção que
o gerador do índice carregava, apaga todo comentário e docstring do código,
corrige um BOM em arquivo Python, torna a regra absoluta em `AGENTS.md` §10 e
fecha a última menção a projeto irmão.

## Demand type

Limpeza e revisão de governança. Sem mudança de comportamento, de schema ou de
rota.

## Current problem

- `docs/archive/static-documentation-legacy/` guardava **12** documentos de
  arquitetura substituídos pelos contratos atuais. Documento substituído que
  continua no repositório é candidato a ser lido como se valesse.
- `system/tests/test_class_catalog.py` tinha **0 bytes**: arquivo de teste que
  não testa nada e sugere cobertura que não existe.
- `docs/prd/AUDIT-2026-06-30-master-findings.md` não é PRD numerada e obrigava
  `scripts/build_prd_index.py` a carregar uma exceção nomeada em
  `KNOWN_EXCEPTIONS`, divergindo do mesmo script nos projetos do eixo.
- `system/tests/test_services.py` começava com BOM UTF-8. O Python roda, porque
  o carregador remove o BOM, mas qualquer ferramenta que leia o arquivo como
  texto puro falha com `invalid non-printable character U+FEFF`.
- `AGENTS.md` §10 dizia "não adicionar comentário ou docstring **por padrão**",
  com a exceção "só manter contrato não inferível ou risco real". A exceção é o
  que mantinha 94 comentários e 88 docstrings vivos.
- `docs/prd/PRD-164` citava nome de projeto irmão em cinco pontos.

## Goal

`docs/` sem documento substituído, `docs/prd/` só com PRD numerada, gerador de
índice sem exceção própria, zero comentário e zero docstring fora de
`migrations/`, regra absoluta no contrato e zero menção a projeto irmão.

## Context Ledger

### Files read in full

- `AGENTS.md`, `docs/AGENT-WORKFLOW.md` §13
- `scripts/build_prd_index.py`
- `docs/prd/PRD-164-autocontencao-dos-contratos-e-padronizacao-do-ci.md`
- os 65 arquivos `.py` com comentário ou docstring

### Adjacent files consulted

- `system/tests/test_seed_docs_contract.py`, que valida
  `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/archive/static-documentation-legacy/`, os 12 documentos, para confirmar
  que o conteúdo já está nos contratos atuais

### Internet / official documentation

- Python, `ast.get_docstring` e `tokenize.COMMENT`:
  https://docs.python.org/3/library/ast.html
- Python, `utf-8-sig` e BOM em código-fonte:
  https://docs.python.org/3/library/codecs.html#module-encodings.utf_8_sig

### Context7 / MCPs / tools verified

- Context7 não foi consultado: a remoção usa a biblioteca padrão do Python.

### Limitations found

- Remover docstring que é o **único** corpo de uma função ou classe produz erro
  de sintaxe. O removedor detecta e substitui por `pass`.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

- Summary presented: Etapa 5 residual mais Etapa 6, com a opção "Tudo: py, html,
  css, js".
- User approval: escolhida na abertura da auditoria e reafirmada com "continue
  até finalizar".
- Date: 2026-07-26.

## Execution prompt

### Persona

Engenheiro responsável pela higiene do repositório.

### Action

Remover documentação substituída e resíduo, apagar comentário e docstring por
análise sintática, tornar a regra absoluta e fechar a autocontenção.

### Context

Documentação é no Obsidian, em `conhecimento-<projeto>.md`; o porquê vive na
PRD; a operação vive em `docs/`.

### Constraints

- remoção de comentário por `ast` e `tokenize`, nunca por expressão regular;
- `migrations/` fica de fora;
- todo nome de seed citado em `docs/OPERACAO-BANCO-SEEDS.md` precisa continuar
  existindo: `test_seed_docs_contract.py` reprova o contrário;
- a suíte precisa passar com a mesma contagem.

### Acceptance criteria

- [x] `docs/archive/` removido;
- [x] `docs/prd/` só com PRD numerada e `README.md`;
- [x] `KNOWN_EXCEPTIONS` de volta ao padrão do eixo;
- [x] `system/tests/test_class_catalog.py` removido;
- [x] `system/tests/test_services.py` sem BOM;
- [x] zero comentário e zero docstring em `.py` fora de `migrations/`;
- [x] zero comentário em `.html`, `.css` e `.js`;
- [x] `AGENTS.md` §10 com proibição absoluta;
- [x] zero menção a projeto irmão em arquivo versionado;
- [x] `conhecimento-lvjiujitsu.md` criado;
- [x] `check`, `makemigrations --check --dry-run`, índice, skills, `pip check` e
      suíte completa verdes, com a contagem preservada.

### Expected evidence

Contagem antes e depois, saída da suíte, verificação do gerador de índice e
varredura de autocontenção.

### Output format

Diff, saída dos comandos e PRD atualizada.

## Scope

- `docs/archive/static-documentation-legacy/`.
- `docs/prd/AUDIT-2026-06-30-master-findings.md`, movido para `docs/`.
- `scripts/build_prd_index.py`, só `KNOWN_EXCEPTIONS`.
- `system/tests/test_class_catalog.py`.
- Todo `.py` fora de `migrations/`, mais `.html`, `.css` e `.js`.
- `AGENTS.md` §10 e `docs/AGENT-WORKFLOW.md` §13.
- `docs/prd/PRD-164`, apenas as menções a projeto irmão.

## Out of scope

- Os três guias `docs/wizard-step-plan-*.md`, referenciados por `CLAUDE.md` §12.
- `migrations/0001_initial.py`, gerado.
- PRDs históricas, cujo texto é registro.
- `docs/UI-SCREEN-CONTRACT.md` e os tokens CSS.
- Criação de um `seed_test_data` único.
- Troca das aspas simples de `settings.py`.
- Os cinco itens de convergência de código registrados na PRD-171.

## Impacted files

| Arquivo | Mudança |
|---|---|
| `docs/archive/` | removido; 12 documentos |
| `docs/prd/AUDIT-2026-06-30-master-findings.md` | movido para `docs/` |
| `scripts/build_prd_index.py` | `KNOWN_EXCEPTIONS` volta a `{"README.md"}`; passa a ter variante única no eixo |
| `system/tests/test_class_catalog.py` | removido; 0 bytes |
| `system/tests/test_services.py` | BOM UTF-8 removido |
| 65 arquivos `.py` | 94 comentários e 88 docstrings removidos |
| 7 arquivos `.css`/`.js` | 158 comentários removidos |
| 3 arquivos `.html` | 38 comentários removidos |
| `AGENTS.md` | §10 com proibição absoluta; 226 → 233 linhas |
| `docs/AGENT-WORKFLOW.md` | §13 remete ao §10 |
| `docs/prd/PRD-164` | sem nomear projeto irmão |

## Risks and edge cases

- **Mover o arquivo de auditoria** poderia quebrar o gerador de índice, que o
  listava como exceção. A ordem foi mover primeiro e só então remover a exceção,
  com `--check` verde depois.
- **Remover o teste vazio** não muda a contagem da suíte: 0 bytes produz 0 casos.
  A contagem antes e depois é a mesma, 769, o que confirma.
- **Docstring como corpo único** produziria erro de sintaxe; tratado com `pass`.
- **O BOM** fez o removedor falhar no parse antes de qualquer escrita. Corrigido
  lendo com `utf-8-sig` e gravando sem BOM, o que resolveu os dois problemas de
  uma vez.
- **Remoção por regex** teria corrompido string contendo `#` ou `/*`. Por isso
  `ast` para docstring e `tokenize` para comentário.

## Rules and constraints

- `AGENTS.md` §10, na redação nova.
- `AGENTS.md` §12: dívida material fora do escopo vira follow-up.

## Plan

- [x] Context and research
- [x] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

## Test plan

### Tests to author

Nenhum teste novo. A suíte de 769 casos é o teste, e
`system/tests/test_seed_docs_contract.py` já cobre o contrato entre o runbook de
banco e os comandos reais.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test
Ran 769 tests in 265.968s
OK
exit=0
```

Mesma contagem de antes da limpeza — o arquivo de teste removido tinha 0 casos.

## Visual validation

### Design approval

Não aplicável: nenhuma mudança visual.

### Routes and states

Não aplicável.

### Desktop

Não aplicável.

### Mobile

Não aplicável.

### Console and terminal

`manage.py check` sem aviso.

### Screenshot / snapshot

Não aplicável. Comentário em CSS e em template Django não produz efeito visual:
o de CSS é descartado pelo parser e o de HTML sai no HTML servido, mas não
renderiza.

## ORM validation

### Read-only checks

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

### Mutating checks and authorization

Nenhuma escrita executada.

## Quality validation

```text
manage.py check                     -> ok
makemigrations --check --dry-run    -> exit=0
build_prd_index.py --check          -> exit=0
validate_skill_frontmatter.py       -> exit=0
pip check                           -> exit=0
manage.py test                      -> 769 OK
```

## Evidence

Contagem de comentário antes e depois, pelo mesmo contador:

```text
antes:   py 94 comentarios + 88 docstrings | css/js 158 | html 38
depois:  py  0 comentarios +  0 docstrings | css/js   0 | html  0
```

Gerador de índice, depois de remover a exceção:

```text
KNOWN_EXCEPTIONS = {"README.md"}
build_prd_index.py normalizado: 1 variante no eixo, 205 linhas
build_prd_index.py --check      -> Indice em dia, exit=0
```

Varredura de autocontenção:

```text
arquivos versionados: 0 mencao a projeto irmao
```

## Implemented

- `docs/archive/static-documentation-legacy/` removido, 12 documentos;
- arquivo de auditoria movido para `docs/`, e `KNOWN_EXCEPTIONS` de volta ao
  padrão do eixo — o gerador de índice passou a ter variante única;
- `system/tests/test_class_catalog.py` removido;
- BOM UTF-8 removido de `system/tests/test_services.py`;
- 94 comentários e 88 docstrings removidos de 65 arquivos `.py`, por `ast` e
  `tokenize`;
- 158 comentários removidos de 7 arquivos `.css` e `.js`, e 38 de 3 `.html`;
- `AGENTS.md` §10 com a regra absoluta e a exceção única de arquivo gerado;
- `docs/AGENT-WORKFLOW.md` §13 remetendo ao §10;
- `docs/prd/PRD-164` sem nomear projeto irmão;
- `conhecimento-lvjiujitsu.md` criado, com o fluxo de cadastro público, a
  separação redirect/webhook/banco e o que morde.

## Cleanup findings

- `scripts/build_prd_index.py` usa `description=__doc__` no `argparse`; sem
  docstring, o `--help` mostra `None`.
- Os três `docs/wizard-step-plan-*.md` continuam soltos na raiz de `docs/`,
  agora referenciados por `CLAUDE.md` §12 mas fora da taxonomia dos demais
  contratos.

## Follow-up PRDs

Nenhuma nova. As pendências abertas continuam sendo as registradas nas PRDs 170
e 171.

## Deviations from plan

Uma. O BOM em `system/tests/test_services.py` não estava previsto: ele apareceu
como falha de parse do removedor, no dry-run. Corrigi-lo entrou no escopo porque
é o mesmo defeito de higiene e porque, sem isso, aquele arquivo ficaria de fora
da remoção.

## Pending

- O `--help` de `scripts/build_prd_index.py` mostra `None`.
- Os três guias de wizard fora da taxonomia de `docs/`.
- As pendências herdadas das PRDs 170 e 171, incluindo o remoto da branch.

## Final status

Concluída. Documentação substituída removida, `docs/prd/` só com PRD numerada,
gerador de índice com variante única no eixo, zero comentário e zero docstring
fora de `migrations/`, regra absoluta no contrato, zero menção a projeto irmão, e
suíte de 769 casos verde com a contagem preservada.
