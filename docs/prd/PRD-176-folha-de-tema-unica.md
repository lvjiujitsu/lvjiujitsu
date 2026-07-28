# PRD-176: Folha de tema única

## Summary

Concentra os tokens do núcleo em `static/system/css/theme.css` e corrige as
telas que carregavam `css/auth/register.css` sem `css/lv/base.css` e por isso
ficavam sem o núcleo inteiro — cadastro de dependente, conclusão de cadastro de
dependente e seleção de parcelas.

## Demand type

Refatoração de UI e correção de defeito latente. Sem mudança de regra de negócio,
de schema ou de rota.

## Current problem

- O núcleo era declarado em dois arquivos, `css/lv/base.css` e
  `css/auth/register.css`, com cinco papéis de valor divergente: `--bg` e
  `--border` no tema claro, `--border` e `--border-soft` nos dois temas.
- `css/auth/register.css` declarava só quatro papéis. Os templates que carregam
  essa folha **sem** `css/lv/base.css` ficavam sem os outros dezoito: as
  propriedades caíam no valor inicial, sem erro no console. São
  `dependents/dependent_registration.html`,
  `dependents/dependent_registration_done.html` e
  `login/installment_select.html`.
- `css/dependents/dependent_registration.css` usa `--input-bg` em cinco lugares,
  e `--input-bg` só existia em `css/auth/register.css`.
- `color-scheme` aparecia em três arquivos.

## Goal

Um papel, um valor, um arquivo. Toda tela que abre documento recebe o núcleo
completo nos dois temas, independentemente de quais folhas de página carrega.

## Context Ledger

### Files read in full

- `css/lv/base.css`, `css/auth/register.css`, `css/auth/login.css` e
  `css/dependents/dependent_registration.css`;
- os 9 templates que abrem documento;
- `docs/UI-SCREEN-CONTRACT.md` seções 4 e 9.

### Adjacent files consulted

- `git show HEAD:static/system/css/home/dashboard.css`, que provou que os dois
  blocos vazios são anteriores a esta mudança;
- mapa de qual template carrega qual folha, sobre os 10 arquivos CSS do projeto.

### Internet / official documentation

- `color-scheme` e sua interação com controles nativos:
  https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme

### Context7 / MCPs / tools verified

- Browser interno na porta 8002, medindo por rota todo token usado nas folhas
  carregadas e conferindo que cada um resolve nos dois temas.

### Limitations found

- `var()` não resolvido não produz string vazia: a propriedade fica inválida no
  tempo de valor computado e cai no valor inicial ou herdado. Procurar
  propriedade vazia não encontra o defeito.
- `/dependents/add/` exige sessão. A cascata dessa tela foi reproduzida
  injetando as folhas servidas na ordem do próprio template.
- O servidor foi iniciado com `--noreload` e o carregador de template é cacheado;
  mudança em template só aparece após reinício.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-ui-delivery`
- `lv-cleanup-audit`

## Understanding approved

Ordem explícita do operador: corrigir, validar no browser uma rota por vez, subir
o sistema e navegar. Data: 2026-07-27.

## Execution prompt

### Persona

Responsável pelo sistema visual do produto.

### Action

Criar a folha de tema, mover o núcleo para ela, ligá-la em todo template que abre
documento e conferir no browser.

### Context

Ligar a folha nas três telas que não tinham o núcleo **muda** pixel, e é a
correção: as propriedades deixam de cair no valor inicial.

### Constraints

- `lv/base.css` é canônica nos conflitos, por ser a folha do `lv/base.html`;
- `--input-bg` sobe ao núcleo, com o valor que `register.css` já usava;
- folha de página mantém apenas a família de prefixo próprio;
- validar nos dois temas.

### Acceptance criteria

- [x] `static/system/css/theme.css` declara os 23 tokens do núcleo nos dois temas;
- [x] nenhuma outra folha declara token do núcleo em nível de tema;
- [x] `theme.css` ligada nos 9 templates que abrem documento;
- [x] `color-scheme` declarado em um arquivo só;
- [x] rotas públicas com núcleo completo e zero token usado sem declaração;
- [x] `§4` do contrato de UI registrando a regra da folha única;
- [x] suíte completa verde com a contagem preservada.

### Expected evidence

Medição por rota no browser e saída da suíte.

### Output format

Diff, evidência de browser e PRD atualizada.

## Scope

- `static/system/css/**/*.css`
- os 9 templates que abrem documento
- `docs/UI-SCREEN-CONTRACT.md` seção 4

## Out of scope

- Família `--auth-*` de `css/auth/login.css`: é de componente e continua onde está.
- Valor de token que não estava em conflito: a paleta não muda fora dos cinco
  papéis divergentes.

## Impacted files

| Arquivo | Mudança |
|---|---|
| `static/system/css/theme.css` | núcleo de 23 tokens nos dois temas, mais `color-scheme` |
| `static/system/css/lv/base.css` | 45 declarações removidas |
| `static/system/css/auth/register.css` | 7 declarações removidas |
| `static/system/css/auth/login.css` | 2 declarações de `color-scheme` removidas |
| `static/system/css/home/dashboard.css` | 2 blocos vazios anteriores removidos |
| 9 templates | `theme.css` ligada como primeira folha do `<head>` |
| `docs/UI-SCREEN-CONTRACT.md` | seção 4 com a regra da folha de tema única |

## Risks and edge cases

- **Escolher o valor errado no conflito.** `lv/base.css` venceu por ser a folha
  que o `lv/base.html` carrega; `register.css` atende um subconjunto de telas.
- **`--input-bg` mudar de aparência ao subir ao núcleo.** O valor é o mesmo que
  `register.css` declarava, `#fafafa` no claro e `#18181b` no escuro. O que muda
  é que ele passa a existir também onde não existia.
- **Página perder token ao remover a declaração local.** `theme.css` está ligada
  nos 9 templates que abrem documento, antes de qualquer folha de página.
- **Template não recarregado.** O carregador é cacheado; o servidor foi
  reiniciado antes de medir, e a medição confirma `theme.css` na lista de folhas
  servidas.

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

Nenhum teste novo. O que prova a mudança é o valor resolvido no browser: teste
que lê CSS confirma string, não resolução. A suíte existente cobre regressão.

### Execution authorization

- Status: authorized

### Execution evidence

```text
python manage.py test
Ran 769 tests in 369.102s
OK
```

## Visual validation

### Design approval

Nas três telas que carregavam `register.css` sem `base.css`, dezoito papéis
deixam de cair no valor inicial. Nenhum valor foi inventado: cada um é o que
`lv/base.css` já declarava.

### Routes and states

`/login/` e `/register/`, ambas HTTP 200. `/dependents/add/` exige sessão; a
cascata dela foi reproduzida com as folhas servidas.

### Desktop

Medição no browser interno, servidor na porta 8002, com `cache: 'reload'`:

```text
rota          folhas                              nucleo faltando   token sem declaracao
/login/       [theme.css, login.css]              []                []
/register/    [theme.css, base.css, register.css] []                []

/dependents/add/ (cascata reproduzida: theme.css + register.css + dependent_registration.css)
  tema claro   nucleo invalido: []
  tema escuro  nucleo invalido: []
```

Antes da mudança, `/dependents/add/` carregava apenas `register.css` e
`dependent_registration.css`, e das dezoito medições do núcleo só quatro tinham
declaração.

Dono de `color-scheme` nas rotas medidas: `:root, html[data-theme="light"]` e
`html[data-theme="dark"]`, ambos em `theme.css`.

### Mobile

Não medido nesta PRD: nenhuma regra de breakpoint foi tocada e a mudança é de
onde o token é declarado, não de layout.

### Console and terminal

Console sem mensagem de erro. `manage.py check` sem aviso.

### Screenshot / snapshot

Sem screenshot: o painel do navegador não compõe frames nesta sessão. A evidência
é valor computado por rota, que para token é mais forte que imagem — prova que o
token resolve, e não apenas que a tela abriu.

## ORM validation

Não aplicável: nenhuma mudança de model, query ou migration.

```text
python manage.py makemigrations --check --dry-run
No changes detected
```

## Quality validation

```text
manage.py check                     -> ok
makemigrations --check --dry-run    -> exit=0
build_prd_index.py --check          -> exit=0
validate_skill_frontmatter.py       -> exit=0
manage.py test                      -> 769 OK
```

## Evidence

Papéis do núcleo com valor divergente entre arquivos, antes:

```text
--bg          [claro]  #f4f4f6 (base.css)  vs  #f5f5f5 (register.css)
--border      [claro]  #e2e2e8             vs  #e4e4e7
--border      [escuro] #2d2d32             vs  #2d2d30
--border-soft [claro]  #ebebef             vs  #f0f0f2
--border-soft [escuro] #222226             vs  #1f1f23
```

Declarações do núcleo removidas das folhas de página:

```text
lv/base.css         45
auth/register.css    7
auth/login.css       2
total               52
```

Declaração de token em nível de tema, depois:

```text
theme.css        [:root, html[data-theme="light"]] 23   [html[data-theme="dark"]] 23
auth/login.css   [:root, html[data-theme="light"]] 18   [html[data-theme="dark"]] 18   -- familia --auth-*
```

Papéis do núcleo com valor divergente entre arquivos: **de 5 para 0**.
Tokens declarados em mais de um arquivo: **de 3 para 0**.
Templates que abrem documento sem o núcleo completo: **de 3 para 0**.

## Implemented

- `theme.css` como dona única dos 23 tokens do núcleo e do `color-scheme`;
- 52 declarações duplicadas removidas de três folhas;
- `--input-bg` promovido ao núcleo, o que faz `dependent_registration.css`
  resolver seus cinco usos;
- `theme.css` ligada como primeira folha nos 9 templates que abrem documento,
  cobrindo as três telas que antes não recebiam o núcleo;
- dois blocos vazios anteriores a esta mudança removidos de `dashboard.css`;
- seção 4 do contrato de UI com a regra da folha de tema única, a proibição de
  redeclarar o núcleo e a proibição de propriedade customizada autorreferente.

## Cleanup findings

- `.class-list { }` e `.attendance-list { }` eram blocos vazios presentes no
  `HEAD`. Removidos.
- A junção de duas regras numa linha só, produzida ao retirar um bloco de
  `lv/base.css`, foi desfeita.

## Follow-up PRDs

Nenhuma.

## Deviations from plan

Uma. O plano era unificar a folha de tema. O mapa de carga expôs três templates
que abrem documento e carregam `register.css` sem `base.css`, ficando sem
dezoito papéis do núcleo. Ligar `theme.css` neles entrou no escopo porque é
exatamente o que a folha única existe para resolver.

## Pending

- Validação mobile e screenshot: o painel do navegador não compõe frames nesta
  sessão, e nenhuma regra de breakpoint foi tocada.
- `/dependents/add/` medida por reprodução da cascata, não por navegação
  autenticada: entrar com senha não é ação que o agente executa.

## Final status

Concluída. Folha de tema única, cinco divergências de valor resolvidas, três
telas que estavam sem o núcleo corrigidas e suíte de 769 casos verde.
