# PRD-173: Núcleo comum do contrato visual

## Summary

Reestruturar `docs/UI-SCREEN-CONTRACT.md` em duas partes: um núcleo normativo
de oito seções, com títulos e redação estáveis, e uma cauda de produto da seção
9 em diante, com identidade, papéis, inventário de telas, componentes, padrões
de interação e changelog. Os tokens passam a ser declarados por **papel** no
núcleo, a paleta concreta vai para a seção de identidade, e a numeração
duplicada de `§14`/`§15` é desfeita.

## Demand type

Contrato de produto. Documentação normativa, sem mudança de código, template,
CSS ou JavaScript.

## Current problem

O contrato tinha 591 linhas em 15 seções e quatro defeitos concretos:

1. **A numeração era inconsistente.** A seção 14 chamava-se "Princípios de UX
   para interfaces geradas por IA", mas suas subseções eram numeradas `15.1` a
   `15.7` — e a seção seguinte, `15`, era o Changelog. Ou seja: `§15.6` e
   `§15.7` não pertenciam a nenhuma seção `15` real, e o documento tinha duas
   numerações concorrentes. Referência interna a "seção 15" era ambígua.
2. **Os tokens eram declarados só como bloco CSS.** A seção 5 trazia os dois
   temas em CSS literal, sem dizer o papel de cada variável. Diante de um
   componente novo, não havia como decidir entre `--panel`, `--surface` e
   `--surface-soft` sem ler as folhas — e o conjunto `--auth-*`, usado nas telas
   de acesso, não era mencionado.
3. **A regra anti-KPI estava no fim da cadeia.** Ela vivia como `§15.7`, depois
   de CRUD em modal, como se fosse mais um padrão de interação, e não uma
   proibição geral que vale para toda tela.
4. **Regra normativa e regra de produto ocupavam o mesmo nível.** "Pill de cor
   exibe a cor como fundo ou círculo colorido", que é da loja de materiais,
   estava no mesmo bloco de affordance que "estados interativos obrigatórios:
   default, hover, focus-visible, active, disabled", que vale para tudo.

## Goal

Um contrato com numeração única, em que o normativo esteja separado do que é
deste produto, e sem perder as regras já escritas — inclusive as de CRUD em
modal e as do wizard público terminal.

## Context Ledger

### Files read in full

- `docs/UI-SCREEN-CONTRACT.md` (591 linhas, versão anterior)
- `docs/OPERACAO-BANCO-SEEDS.md`
- `docs/DEPLOY-RENDER-SUPABASE.md`
- `docs/PRD-STANDARD.md`
- `docs/prd/README.md`

### Adjacent files consulted

- `static/system/css/` — inventário real de custom properties (40) e dos cortes
  de `@media`
- `static/system/js/auth/login.js`, `static/system/js/home/dashboard.js` —
  chave `lv-theme`
- `system/urls.py` — rotas canônicas em inglês e aliases pt-BR, usados no
  inventário de telas

### Internet / official documentation

- [WCAG 2.2 — Target Size (Minimum) 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
  — origem do alvo de toque de 44 por 44 pixels citado no núcleo, que o
  contrato anterior já invocava pelo número da diretriz.

### Context7 / MCPs / tools verified

Não aplicável: a mudança não envolve biblioteca, framework, SDK ou CLI cuja
versão precise ser conferida.

### Limitations found

O inventário de telas anterior listava os módulos como "rotas removidas da fase
1 — readicionadas conforme PRDs", uma lista em prosa que não correspondia mais
ao `system/urls.py`, onde os módulos existem com rota canônica e alias. A seção
11 foi reescrita a partir das rotas reais.

## Required skills

- `lv-task-intake`
- `lv-prd`
- `lv-cleanup-audit`

`lv-ui-delivery` não se aplica: nenhuma tela muda, então não há rota a validar
em browser.

## Understanding approved

- Summary presented: reestruturação do contrato visual em núcleo normativo
  (seções 1 a 8) mais cauda de produto (seções 9 a 14), com tokens por papel.
- User approval: ordem explícita do operador, que nomeou as oito seções do
  núcleo e destacou que os blocos `§15.5` a `§15.7` não podem ser perdidos.
- Date: 2026-07-26

## Execution prompt

### Persona

Responsável pelo contrato visual do LV JIU JITSU.

### Action

Reescrever `docs/UI-SCREEN-CONTRACT.md` na estrutura aprovada, com numeração
única e sem perder regra existente.

### Context

O documento é o dono do assunto "contrato visual, estados e evidência" segundo
`AGENTS.md` §2.

### Constraints

- A numeração passa a ser única: nenhuma subseção pode referenciar uma seção
  que não existe.
- O núcleo não cita nome concreto de token.
- Nenhuma menção a outro projeto.

### Acceptance criteria

- [x] O documento tem exatamente 14 seções de primeiro nível, na ordem
      aprovada.
- [x] Nenhuma subseção numera-se fora da seção que a contém.
- [x] A seção 4 declara papéis de token, não nomes concretos.
- [x] A seção 9 mapeia papel para token real do LV, mantém a paleta concreta
      dos dois temas e cita o conjunto `--auth-*`.
- [x] A seção 9 descreve os breakpoints efetivamente escritos nas folhas.
- [x] O conteúdo de `§15.5` (wireframes), `§15.6` (CRUD em modal) e `§15.7`
      (anti-KPI) está presente: os dois primeiros na seção 13, o terceiro no
      núcleo.
- [x] O contrato terminal do wizard público continua declarado.
- [x] O changelog conserva todas as entradas anteriores e ganha a desta PRD.
- [x] Zero menção a outro projeto.

### Expected evidence

Verificação estrutural do documento e saída dos gates do repositório.

### Output format

Markdown, pt-BR, sem segredo.

## Scope

- `docs/UI-SCREEN-CONTRACT.md`.

## Out of scope

- Convergência do vocabulário de tokens CSS.
- Qualquer mudança de template, CSS ou JavaScript.
- Commit e push.

## Impacted files

| Arquivo | Mudança |
|---|---|
| `docs/UI-SCREEN-CONTRACT.md` | reescrito: 591 → 718 linhas, 15 → 14 seções |
| `docs/AUDIT-2026-06-30-master-findings.md` | duas referências de seção anotadas com a numeração da época |
| `docs/prd/README.md` | índice regenerado |

## Risks and edge cases

- **Perder regra ao desfazer a numeração dupla.** Mitigado por inventário
  bloco a bloco antes de escrever: cada subseção `15.x` foi classificada como
  normativa (vai ao núcleo) ou de produto (vai à cauda).
- **Reescrever o inventário de telas com rota que não existe.** Mitigado
  extraindo os prefixos de rota diretamente de `system/urls.py`.
- **Documentar token que não existe.** Mitigado medindo as custom properties
  diretamente nas folhas.

## Rules and constraints

`AGENTS.md` §2 (dono único por assunto), §5 (leitura integral), §12 (limpeza) e
`docs/PRD-STANDARD.md`.

## Plan

- [x] Context and research
- [ ] Test authored first, when applicable
- [x] Implementation
- [x] Refactor
- [x] Validation
- [x] Cleanup audit
- [x] Documentation

Teste primeiro não se aplica: a mudança é de documento normativo, sem
comportamento executável a cobrir.

## Test plan

### Tests to author

Nenhum.

### Execution authorization

- Status: authorized

### Execution evidence

A suíte foi executada como gate de regressão; ver `Evidence`.

## Visual validation

### Design approval

Não aplicável: nenhuma superfície muda.

### Routes and states

Não aplicável.

### Desktop

Não aplicável.

### Mobile

Não aplicável.

### Console and terminal

Não aplicável.

### Screenshot / snapshot

Não aplicável. Nenhuma rota foi alterada.

## ORM validation

### Read-only checks

Não aplicável.

### Mutating checks and authorization

Não aplicável.

## Quality validation

Verificação estrutural do documento por script: contagem e ordem das seções,
contagem das subseções de padrões de interação e busca por menção a outro
projeto.

## Evidence

Estrutura do documento:

```text
14 seções: 1. Propósito | 2. Fontes de verdade | 3. Princípios obrigatórios |
4. Tokens CSS obrigatórios | 5. Responsividade | 6. Tema claro e escuro |
7. Estados obrigatórios e hierarquia visual | 8. Regras de implementação,
validação e critério de parada | 9. Identidade visual | 10. Papéis e permissões |
11. Inventário de telas | 12. Componentes | 13. Padrões de interação |
14. Changelog
padroes_13 = 4 (13.1 a 13.4)
mencoes cruzadas = []
718 linhas
```

Inventário de tokens medido nas folhas, usado para escrever a seção 9:

```text
--auth-bg --auth-border --auth-brand --auth-brand-strong --auth-card
--auth-card-border --auth-danger --auth-danger-soft --auth-focus --auth-info
--auth-info-soft --auth-input --auth-muted --auth-shadow --auth-success
--auth-success-soft --auth-text --auth-toggle --bg --border --border-soft
--brand-red --brand-red-muted --brand-red-strong --card-shadow
--card-shadow-hover --danger --danger-muted --focus-ring --info --info-muted
--input-bg --muted --panel --success --success-muted --surface --surface-soft
--text --warning --warning-muted
```

Breakpoints medidos, base da seção 9:

```text
8x min-width:768px · 5x min-width:600px · 5x min-width:480px
4x max-width:520px · 3x min-width:720px · 3x min-width:640px
2x max-width:640px · 2x max-width:639px · 2x max-width:479px
1x min-width:900px · 1x min-width:540px · 1x min-width:1600px
```

Rotas de primeiro nível extraídas de `system/urls.py`, base da seção 11:

```text
account/ administracao/ administration/ aulas/ cadastro/ calendar/ classes/
cronograma/ dashboard/ dependents/ financeiro/ financial/ graduacao/
graduation/ health/ home/ login/ logout/ loja/ materiais/ materials/
meus-materiais/ minha-mensalidade/ my-materials/ pagamentos/ password-change/
password-reset/ people/ pessoas/ plan-prices/ plan-tiers/ planos/ plans/
register/ requests/ reset/ store/ turmas/
```

Gates do repositório, todos executados nesta sessão:

```text
$ .\.venv\Scripts\python.exe manage.py check
System check identified no issues (0 silenced).

$ .\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
No changes detected

$ .\.venv\Scripts\python.exe scriptsuild_prd_index.py --check
182 PRD(s) indexada(s).
Indice em dia.

$ .\.venv\Scripts\python.exe scriptsalidate_skill_frontmatter.py
[OK] 7 skill(s) nas 3 plataformas
[OK] 7 metadado(s) Codex integro(s) em UTF-8 com LF.
21 arquivo(s) de skill validado(s).

$ .\.venv\Scripts\python.exe -m pip check
No broken requirements found.

$ .\.venv\Scripts\python.exe manage.py test
Ran 769 tests in 352.074s
OK
```

Contagem da suíte preservada: 769 testes, mesma da execução anterior.

## Implemented

- `docs/UI-SCREEN-CONTRACT.md` reescrito com núcleo de oito seções e cauda de
  seis; numeração agora é única.
- Seção 4 do núcleo declara catorze papéis de token, separando obrigatórios de
  condicionais.
- Seção 9 mapeia catorze papéis para os tokens reais, preserva a paleta CSS dos
  dois temas, registra que `:root` é o tema claro e explica o papel do conjunto
  `--auth-*`.
- Seção 9 documenta a estratégia mobile-first das folhas — a maioria dos cortes
  cresce por `min-width` — e a chave `lv-theme` aplicada por `theme_boot.js`
  antes da pintura.
- Seção 11 reescrita a partir das rotas reais, com a tabela de rota canônica em
  inglês e alias pt-BR, substituindo a lista em prosa de "módulos removidos da
  fase 1".
- Contrato terminal do wizard público preservado como seção 11.4.
- `§15.6` (CRUD operacional em modal/dialog) migrou íntegro para `§13.1`,
  incluindo implementação, estados, fundação compartilhada real e o débito
  PRD-141 M-01 dos standalones com IIFE de tema inline.
- `§15.7` (anti-KPI) subiu para o núcleo, ganhando os sete requisitos que
  autorizam um indicador.
- Affordance da loja separada em `§13.2`: pill de cor, de tamanho e sem
  estoque, que é regra de produto, saiu do bloco normativo de affordance.
- `§15.5` (wireframes) virou `§13.3`, com o processo de quatro passos, e os
  três prompts de referência para hierarquia e agrupamento foram preservados.
- Mapeamento de máquinas de estado na PRD virou `§13.4`.
- Tipografia operacional específica do LV — 13px em tela densa, 15px em
  formulário público — preservada na seção 9.
- Papéis ganharam a nota de que acúmulo é a regra: a mesma pessoa pode ser
  aluno e professor.
- Changelog conserva as entradas anteriores, reescritas em uma linha cada, e
  ganha a desta PRD.

## Cleanup findings

- O cabeçalho anterior dizia "Toda tela implementada deve derivar deste
  contrato"; a regra real, que passou ao núcleo, é mais exigente: toda tela
  nova **ou reimplementada** deriva do contrato e de uma PRD específica.
- A seção 12 anterior misturava ordem de validação com política de teste
  ("Sem execução real, não declarar Red ou Green"). A política foi mantida, na
  seção 8.3, junto do restante das regras de evidência.
- A seção 10 anterior tinha um bloco datado — "estado real — jul/2026, PRD-144
  P2" — no título. A data saiu do título e o conteúdo permaneceu: o inventário
  descreve o que existe, e o changelog é quem guarda a data.
- `docs/AUDIT-2026-06-30-master-findings.md` cita o contrato por número de
  seção em dois achados, apontando para `§9.1` e `§9.2`. Com a renumeração,
  `§9` passou a ser Identidade visual, e as referências virariam armadilha. As
  duas linhas foram anotadas com a numeração da época e a equivalente atual
  (`§11.1` e `§11.2`), preservando o registro histórico. Nenhum outro arquivo
  dos três repositórios referencia o contrato por número de seção — conferido
  por busca em `.md` e `.mdc`, incluindo skills, `.cursor/rules/` e
  `/validar-tela`.

## Follow-up PRDs

Nenhuma reservada nesta PRD.

## Deviations from plan

Duas regras foram acrescentadas ao núcleo por já valerem na prática: o bloco de
acessibilidade mínima e o item de critério de parada sobre dado real de Render
ou Supabase inexistente no repositório. A seção 11 foi reescrita a partir do
`system/urls.py` — não estava previsto reescrevê-la, mas manter uma lista que o
código já contradizia seria preservar um defeito.

## Pending

- Convergência do vocabulário de tokens CSS.
- Nenhuma validação visual foi feita, por não haver superfície alterada.

## Final status

concluída
