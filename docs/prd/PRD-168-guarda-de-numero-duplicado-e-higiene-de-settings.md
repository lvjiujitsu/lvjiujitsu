# PRD-168: Guarda de número duplicado no índice de PRD e higiene de settings

## Summary

O gerador do índice de PRD prometia revelar número duplicado e não revelava.
Esta PRD implementa a guarda, cria a suíte que fixa o comportamento do gerador
e torna explícitos dois cabeçalhos de segurança em `settings.py`.

## Demand type

Governança e infraestrutura. Sem mudança de regra de negócio, sem mudança de
schema, sem mudança visual.

## Current problem

- `scripts/build_prd_index.py` declara no próprio docstring que o índice "é a
  única fonte que revela gap reservado e numero duplicado". O código calcula
  apenas `max(numero) + 1` e nunca compara os números entre si, então dois
  arquivos com o mesmo `PRD-<NNN>` passam por `--check` sem alarme.
- Não existia teste do gerador neste projeto. O comportamento do `--check`, o
  formato de três dígitos e as recusas do gerador não estavam fixados.
- `settings.py` repetia o literal `{"hg", "prod"}` em três guardas de ambiente,
  sem constante nomeada, e não declarava `SECURE_CONTENT_TYPE_NOSNIFF` nem
  `X_FRAME_OPTIONS`. Os dois valores coincidem com o padrão do Django 5.2, mas
  ficam invisíveis para quem lê o arquivo e para `check --deploy`.

## Goal

`build_prd_index.py --check` falha quando dois arquivos disputam o mesmo
número, com a colisão nomeada na mensagem; o comportamento do gerador está
coberto por teste; as guardas de ambiente usam constante nomeada e a postura de
segurança está declarada em vez de herdada.

## Context Ledger

### Files read in full

- `scripts/build_prd_index.py`
- `lvjiujitsu/settings.py`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`
- `AGENTS.md`, `CLAUDE.md`

### Adjacent files consulted

- `system/tests/test_settings_hosts.py`
- `.github/workflows/ci.yml`
- `templates/` — 15 usos de `<iframe>`, todos com `src="about:blank"`
  preenchido por JavaScript, mais 4 usos de decorador `xframe_options`

### Internet / official documentation

- Django 5.2, `X_FRAME_OPTIONS` e clickjacking:
  https://docs.djangoproject.com/en/5.2/ref/clickjacking/
- Django 5.2, `SECURE_CONTENT_TYPE_NOSNIFF`:
  https://docs.djangoproject.com/en/5.2/ref/settings/#secure-content-type-nosniff

### Context7 / MCPs / tools verified

- Context7 não foi consultado: a mudança usa API de Django já em uso no
  projeto e a documentação oficial da versão fixada respondeu ao que faltava.

### Limitations found

- Nenhuma. Todos os comandos necessários rodaram localmente.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-django-delivery`
- `lv-cleanup-audit`

## Understanding approved

Autorizado pelo operador na sessão de 2026-07-26, com a instrução explícita de
nivelar os três MVPs irmãos por etapas e a decisão de tratar defeitos vermelhos
e guardas como primeira etapa.

## Execution prompt

### Persona

Engenheiro Django responsável pela governança do repositório.

### Action

Implementar a detecção de número duplicado no gerador do índice, criar a suíte
do gerador e tornar explícitas as guardas de ambiente e de cabeçalho.

### Context

MVP descartável, banco local recriável, sem dado real. O índice de PRD é a
fonte canônica do próximo número, conforme `AGENTS.md` §6.

### Constraints

- menor mudança correta;
- sem comentário e sem docstring novos;
- sem nova variável de ambiente;
- sem alteração de schema;
- `X_FRAME_OPTIONS` não pode quebrar os modais em `<iframe>`.

### Acceptance criteria

- [x] `collect_prd_files()` recusa `docs/prd/` com número repetido e nomeia os
      arquivos em conflito na mensagem;
- [x] `build_prd_index.py --check` retorna 1 nesse caso e não escreve nada;
- [x] existe `system/tests/test_prd_index_generator.py` cobrindo ordem,
      preservação de cabeçalho e notas, três dígitos, status, recusas e o modo
      `--check`;
- [x] `REMOTE_ENVIRONMENTS` substitui as três repetições do literal;
- [x] `SECURE_CONTENT_TYPE_NOSNIFF` e `X_FRAME_OPTIONS` declarados;
- [x] `manage.py check`, `makemigrations --check --dry-run` e a suíte completa
      passam.

### Expected evidence

Saída real de `build_prd_index.py --check`, da suíte focada e da suíte
completa.

### Output format

Diff mínimo e PRD atualizada com evidência.

## Scope

- `scripts/build_prd_index.py` — guarda de duplicata em `collect_prd_files()`.
- `system/tests/test_prd_index_generator.py` — novo.
- `lvjiujitsu/settings.py` — `REMOTE_ENVIRONMENTS`, `SECURE_CONTENT_TYPE_NOSNIFF`
  e `X_FRAME_OPTIONS`.

## Out of scope

- Nivelar `AGENTS.md`, `CLAUDE.md` e os documentos de `docs/`.
- Remover comentários e docstrings do repositório.
- Unificar `requirements.txt` e o conjunto de chaves de env.
- Remover `docs/archive/static-documentation-legacy/`.

## Impacted files

| Arquivo | Mudança |
|---|---|
| `scripts/build_prd_index.py` | detecção de número duplicado |
| `system/tests/test_prd_index_generator.py` | arquivo novo, 24 casos |
| `lvjiujitsu/settings.py` | constante de ambientes remotos e dois cabeçalhos declarados |
| `docs/prd/README.md` | índice regenerado |

## Risks and edge cases

- `X_FRAME_OPTIONS = "DENY"` bloquearia `<iframe>` de mesma origem se as views
  dependessem do valor global. Verificado antes de aplicar: os 15 `<iframe>`
  do projeto carregam `about:blank` e recebem conteúdo por JavaScript, e as
  views que precisam de exceção já usam o decorador `xframe_options`. O valor
  aplicado é o mesmo que o Django já usava por padrão, então não há mudança de
  comportamento — apenas de visibilidade.
- A guarda de duplicata é retroativa: um repositório que já tenha colisão passa
  a falhar no CI até renumerar. Neste projeto não havia colisão.

## Rules and constraints

- `AGENTS.md` §6: o número vem de `docs/prd/README.md`, não de `ls`.
- `AGENTS.md` §7: sem declarar Red ou Green sem saída real.
- `AGENTS.md` §10: sem comentário ou docstring por padrão.

## Plan

1. implementar a guarda em `collect_prd_files()`;
2. criar a suíte do gerador, incluindo o caso de duplicata;
3. observar a suíte verde;
4. conferir o uso real de `<iframe>` antes de declarar `X_FRAME_OPTIONS`;
5. aplicar `REMOTE_ENVIRONMENTS` e os dois cabeçalhos;
6. rodar `check`, `makemigrations --check --dry-run` e a suíte completa;
7. regenerar `docs/prd/README.md`.

## Test plan

### Tests to author

- `test_duplicate_number_makes_generator_fail`
- `test_check_fails_when_a_number_is_duplicated`
- `test_next_free_number_keeps_three_digits`
- demais casos do gerador e do modo `--check` (24 no total, contando a
  subclasse que reexecuta a bateria).

### Execution authorization

Testes locais autorizados por `AGENTS.md` §7. Banco de teste isolado.

### Execution evidence

```text
python manage.py test system.tests.test_prd_index_generator --verbosity 2
Ran 24 tests in 0.072s
OK
exit=0
```

```text
python manage.py test
Ran 769 tests in 292.150s
OK
exit=0
```

## Visual validation

Não aplicável: nenhuma rota, template, CSS ou JavaScript foi alterado.
`X_FRAME_OPTIONS` recebeu o valor que o Django já aplicava por padrão, e o uso
de `<iframe>` foi auditado antes da mudança.

## ORM validation

Não aplicável: nenhuma mudança de model, query ou migration.

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

## Quality validation

```text
python manage.py check
System check identified no issues (0 silenced).
exit=0
```

```text
python scripts/build_prd_index.py --check
Indice em dia.
exit=0
```

```text
python scripts/validate_skill_frontmatter.py
[OK] 6 skill(s) nas 3 plataformas
18 arquivo(s) de skill validado(s).
exit=0
```

## Evidence

- guarda de duplicata exercitada contra um diretório com colisão: a mensagem
  nomeia número e arquivos em conflito;
- suíte do gerador: 24 casos, verde;
- suíte completa: 769 casos, verde (eram 745 antes desta PRD).

## Implemented

- detecção de número duplicado em `collect_prd_files()`, com mensagem que
  nomeia cada colisão;
- `system/tests/test_prd_index_generator.py` com 24 casos;
- `REMOTE_ENVIRONMENTS` no lugar das três repetições do literal;
- `SECURE_CONTENT_TYPE_NOSNIFF` e `X_FRAME_OPTIONS` declarados.

## Cleanup findings

- `system/tests/test_class_catalog.py` tem 0 linhas: arquivo de teste vazio.
- `docs/archive/static-documentation-legacy/` guarda 12 documentos de
  arquitetura substituídos pelos contratos atuais.
- `docs/prd/AUDIT-2026-06-30-master-findings.md` não é PRD numerada e obriga o
  gerador a manter uma exceção nomeada em `KNOWN_EXCEPTIONS`.
- `docs/wizard-step-plan-*.md`: três guias soltos na raiz de `docs/`, fora da
  taxonomia dos demais contratos.
- `settings.py` usa aspas simples enquanto os demais arquivos do eixo usam
  aspas duplas.
- `.env` declara `DJANGO_DEBUG=1` em vez de `True`.

## Follow-up PRDs

Reservado em `docs/prd/README.md` conforme as etapas acordadas com o operador:
nivelamento de contratos de protocolo, nivelamento de contratos de produto,
infraestrutura e ambiente, estrutura e limpeza de comentários e docstrings.

## Deviations from plan

Nenhum.

## Pending

- Os seis achados de limpeza listados acima pertencem às etapas de estrutura e
  de limpeza, não a esta PRD.

## Final status

Concluída.
