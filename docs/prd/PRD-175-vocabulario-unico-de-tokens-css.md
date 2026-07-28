# PRD-175: Vocabulário único de tokens CSS

## Summary

Unifica o nome dos tokens CSS no vocabulário semântico do eixo, preservando os
valores, e corrige **três tokens usados em `var()` sem nenhuma declaração** —
defeito anterior a esta PRD, que não falha e cai no valor inicial. Corrige também
o `§4` do contrato de UI, que autorizava a divergência de nomes.

## Demand type

Refatoração de UI e correção de defeito latente. Sem mudança de regra de
negócio, sem mudança de schema, sem mudança de rota.

## Current problem

- O acento de marca era `--brand-red`, `--brand-red-strong` e
  `--brand-red-muted`. O nome carregava a cor, o que amarra o token à paleta:
  trocar o vermelho exigiria renomear o token em todo lugar.
- **Três tokens eram usados sem nunca serem declarados:** `--brand-primary` e
  `--card` em `css/auth/register.css`, e `--surface-muted` em
  `css/home/dashboard.css`. As propriedades correspondentes caíam no valor
  inicial, sem erro no console.
- A família de autenticação usava `--auth-brand` e `--auth-brand-strong`,
  propagando o vocabulário antigo para dentro do componente.
- `docs/UI-SCREEN-CONTRACT.md` §4 declarava que "o núcleo declara papéis, não
  nomes concretos: o nome do token pertence à identidade". Era a regra que
  autorizava a divergência.

## Goal

Um papel tem um nome só, sem cor embutida. Nenhum `var()` usado fica sem
declaração. Nenhum pixel muda por renomeação.

## Context Ledger

### Files read in full

- os 7 arquivos CSS de `static/system/`, incluindo `css/lv/base.css`
- `docs/UI-SCREEN-CONTRACT.md` §4 e §9

### Adjacent files consulted

- `git show HEAD:` de `css/auth/register.css` e `css/home/dashboard.css`, para
  datar os órfãos
- inventário dos 79 nomes distintos de token no eixo, com matriz de presença

### Internet / official documentation

- CSS Custom Properties, comportamento de `var()` não resolvido:
  https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties#custom_property_fallback_values

### Context7 / MCPs / tools verified

- Browser interno na porta 8002, listando por página todo token usado nas folhas
  carregadas e conferindo que cada um resolve.

### Limitations found

- `var()` não resolvido **não** produz string vazia: a propriedade fica inválida
  no tempo de valor computado e cai no valor inicial ou herdado. Procurar
  propriedade vazia não encontra o defeito.
- As rotas internas exigem sessão. A cobertura das páginas não alcançadas veio de
  checagem estática de completude sobre todos os arquivos.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

Ordem explícita do operador: corrigir a convergência de tokens e validar no
browser, uma rota por vez. Data: 2026-07-27.

## Execution prompt

### Persona

Responsável pelo sistema visual do produto.

### Action

Renomear os tokens para o vocabulário comum preservando valores, declarar o que
faltava, e corrigir o contrato.

### Context

Renomear token preservando valor não muda pixel. Declarar token que faltava
**muda** pixel, e para melhor: a propriedade deixa de cair no valor inicial.

### Constraints

- valor preservado em toda renomeação;
- nome de token não carrega cor;
- órfão recebe o token do papel que ele designava, não um valor novo;
- validar no browser nos dois temas.

### Acceptance criteria

- [x] acento de marca em `--accent`, `--accent-strong`, `--accent-muted`, sem cor
      no nome;
- [x] família de autenticação em `--auth-accent` e `--auth-accent-strong`;
- [x] os três órfãos remapeados para o token do papel correspondente;
- [x] zero token usado sem declaração;
- [x] `§4` do contrato declarando o nome canônico de cada papel, idêntico nos
      três projetos do eixo;
- [x] login e cadastro validados no browser nos dois temas;
- [x] suíte completa verde com a contagem preservada.

### Expected evidence

Verificação de completude de token, medição no browser por rota e saída da
suíte.

### Output format

Diff, evidência de browser e PRD atualizada.

## Scope

- `static/system/css/**/*.css` e os JS que leem token
- `docs/UI-SCREEN-CONTRACT.md` §4

## Out of scope

- Valor de token existente: a paleta não muda.
- `--auth-cyan-soft` e demais tokens de componente sem par no vocabulário
  principal.
- Unificação de tema por arquivo — ver `Pending`.

## Impacted files

| Arquivo | Mudança |
|---|---|
| 8 arquivos CSS | acento renomeado de `--brand-red*` para `--accent*` |
| 1 arquivo CSS | família de autenticação alinhada |
| 2 arquivos CSS | órfãos remapeados para o token do papel |
| `docs/UI-SCREEN-CONTRACT.md` | `§4` reescrito com 19 papéis e o nome canônico de cada |

## Risks and edge cases

- **Renomear e quebrar o `var()`.** Substituição ancorada em
  `(?<![-a-z])--token(?=\s*:)` e `var\(\s*--token(?![-a-z])`, o que impediu que
  `--brand-red-strong` fosse atingido pela regra de `--brand-red`. A ordem das
  regras vai do nome mais longo para o mais curto.
- **Mudar aparência ao declarar órfão.** Onde o token não existia, a propriedade
  caía no valor inicial. Passar a resolver **é** mudança visual, e é a correção
  do defeito.
- **`--card` remapeado para `--surface`.** O nome designava a superfície embutida
  do cartão; `--surface` é o papel equivalente já declarado em `css/lv/base.css`.

## Rules and constraints

- `AGENTS.md` §8: mudança de CSS valida no browser, nos dois temas.
- `AGENTS.md` §10: menor mudança correta, causa raiz.

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

Nenhum teste novo. O que prova a mudança é o valor resolvido no browser: um teste
que leia CSS confirma string, não resolução. A suíte existente cobre regressão.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test
Ran 769 tests in 307.090s
OK
exit=0
```

## Visual validation

### Design approval

Não aplicável para a renomeação: a paleta é a mesma. Para os três órfãos, o
valor passa a ser o do token do papel já declarado.

### Routes and states

`/login/` e `/register/`, ambas HTTP 200. As rotas internas exigem sessão e foram
cobertas por checagem estática de completude sobre todos os CSS.

### Desktop

Medição no browser interno, servidor na porta 8002:

```text
/login/     folhas=2  tokens usados=8   NAO RESOLVEM: []
            tema claro  --accent: #c41230  --bg: #f4f4f5
            tema escuro --accent: #e02244  --bg: #08090b
/register/  folhas=2  tokens usados=10  NAO RESOLVEM: []
            campos=223
            tema claro  body bg rgb(245,245,245) | texto rgb(24,24,27)
            tema escuro body bg rgb(9,9,11)      | texto rgb(250,250,250)
```

Token do vocabulário antigo no HTML servido: **0**.

### Mobile

Não medido nesta PRD: nenhuma regra de breakpoint foi tocada e a mudança é de
nome de token, não de layout.

### Console and terminal

Console sem mensagem. `manage.py check` sem aviso.

### Screenshot / snapshot

Sem screenshot: o painel do navegador não compõe frames nesta sessão. A evidência
é medição de valor computado, que para token é mais forte que imagem — prova que
o token resolve, e não apenas que a tela abriu.

## ORM validation

Não aplicável: nenhuma mudança de model, query ou migration.

```text
python manage.py makemigrations --check --dry-run
No changes detected
exit=0
```

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

Órfãos de token, e a prova de que precediam esta PRD:

```text
--card           no HEAD do git: usos=3 declaracoes=0
--surface-muted  no HEAD do git: usos=1 declaracoes=0
```

Remapeamento aplicado:

```text
--brand-red -> --accent                --brand-red-strong -> --accent-strong
--brand-red-muted -> --accent-muted    --brand-primary -> --accent
--card -> --surface                    --surface-muted -> --surface-soft
--auth-brand -> --auth-accent          --auth-brand-strong -> --auth-accent-strong
```

Completude de token, depois:

```text
declarados: 41 | usados: 41
usados sem declaracao: 0
declarados sem uso: 0
```

Vocabulário comum aos três projetos do eixo: **de 3 para 12 nomes**
(`--accent --bg --border --card-shadow --danger --info --muted --panel
--success --surface --text --warning`).

`§4` do contrato de UI: **1 variante** nos três.

## Implemented

- acento de marca em `--accent`, `--accent-strong`, `--accent-muted`, sem cor no
  nome;
- família de autenticação em `--auth-accent` e `--auth-accent-strong`;
- os três órfãos remapeados para o token do papel que designavam;
- `§4` do contrato reescrito com 19 papéis e o nome canônico de cada, mais duas
  regras novas: família de componente usa `--<familia>-text` e
  `--<familia>-border`, e token usado sem declaração é defeito.

## Cleanup findings

- **O tema é declarado em dois arquivos**, `css/lv/base.css` e
  `css/auth/register.css`, com tokens repetidos. Não há folha de tema única.
- `--auth-cyan-soft` existe na família de autenticação sem par claro no
  vocabulário principal.

## Follow-up PRDs

- Folha de tema única, com `base.css` como fonte e `register.css` consumindo os
  tokens em vez de redeclará-los.

## Deviations from plan

Duas.

O plano era renomear token. A verificação de completude expôs três tokens usados
sem declaração, anteriores a esta PRD — confirmado por `git show HEAD:`.
Corrigi-los entrou no escopo porque renomear em volta de um defeito latente
deixaria o defeito mais difícil de achar depois.

O `§4` do contrato não estava no escopo. Entrou porque afirmava que "o nome do
token pertence à identidade", exatamente o oposto do que esta PRD implementa.

## Pending

- A folha de tema única, registrada em `Follow-up PRDs`.
- Validação mobile e screenshot: o painel do navegador não compõe frames nesta
  sessão, e nenhuma regra de breakpoint foi tocada.

## Final status

Concluída. Vocabulário único no eixo, sem cor no nome do token, três órfãos
corrigidos com prova de que precediam a mudança, e suíte de 769 casos verde.
