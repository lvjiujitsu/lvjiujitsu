# PRD-033: Seed de Feriados Iniciais

## Resumo do que será implementado
Criar uma seed granular para carregar os feriados iniciais de 2026 no modelo `Holiday`, substituindo o comando antigo `seed_holidays --year 2026` sem reintroduzir argumentos de linha de comando.

## Tipo de demanda
Nova feature

## Problema atual
O commit antigo possuia `seed_holidays --year 2026`, mas o projeto atual removeu seeds com argumentos `--` e nao possui comando equivalente para popular `Holiday`.

## Objetivo
Disponibilizar `python manage.py seed_system_initial_holidays`, idempotente, auditavel e baseado em JSON proprio em `static/initial_data/`.

## Context Ledger
### Arquivos lidos integralmente
- `CLAUDE.md`
- `system/models/calendar.py`
- `system/tests/test_commands.py`
- `system/management/commands/seed_system_initial_product_categories.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `system/management/commands/seed_system_initial_teacher_payroll_configs.py`

### Arquivos adjacentes consultados
- `system/models/__init__.py`
- `static/initial_data/`
- comando antigo `seed_holidays.py` no commit baixado

### Internet / documentacao oficial
- Nao aplicavel; comportamento derivado do codigo local e do comando legado.

### MCPs / ferramentas verificadas
- PowerShell — status ok — leitura de arquivos e comandos locais

### Limitacoes encontradas
- Suite completa possui falhas pre-existentes fora do escopo em templates/rotas.

## Prompt de execucao
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD.

### Acao
Implementar seed de feriados iniciais usando JSON e comando granular.

### Contexto
`Holiday` e usado pelos fluxos de calendario/aulas para datas sem expediente. A seed deve repor o comportamento operacional do comando legado para 2026.

### Restricoes
- sem argumentos `--`
- sem migracoes
- sem hardcode dentro do comando
- dados em `static/initial_data/seed_system_initial_holidays.json`
- seed idempotente
- audit log por registro

### Criterios de aceite
- [ ] `python manage.py help seed_system_initial_holidays` registra o comando.
- [ ] Rodar a seed cria os 13 feriados de 2026.
- [ ] Rodar a seed duas vezes nao duplica registros.
- [ ] A seed atualiza nome/status quando a data ja existe.

### Evidencias esperadas
- `python manage.py check`
- `python manage.py test system.tests.test_commands --verbosity 2`

### Formato de saida
Codigo implementado + testes + evidencias de validacao.

## Escopo
- Criar JSON de feriados iniciais.
- Criar comando `seed_system_initial_holidays`.
- Cobrir idempotencia em teste de comando.
- Atualizar documentacao operacional.

## Fora do escopo
- Alterar schema.
- Implementar feriados dinamicos por ano via argumento.
- Corrigir falhas pre-existentes da suite completa.

## Arquivos impactados
- `static/initial_data/seed_system_initial_holidays.json`
- `system/management/commands/seed_system_initial_holidays.py`
- `system/tests/test_commands.py`
- `CLAUDE.md`

## Riscos e edge cases
- Feriados moveis precisam ficar explicitamente registrados no JSON por ano.
- O comando legado aceitava `--without-optional`; a politica atual proibe argumentos, entao o conjunto inicial precisa ser decidido no JSON.

## Regras e restricoes
- SDD antes de codigo
- TDD para implementacao
- sem hardcode no comando
- sem migracoes
- validacao obrigatoria

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Testes
- [x] 4. Implementacao
- [x] 5. Validacao completa possivel
- [x] 6. Atualizacao documental

## Validacao visual
Nao aplicavel; mudanca sem UI.

## Validacao ORM
### Banco
Validado por teste Django com banco de teste.

### Shell checks
Nao necessario.

### Integridade do fluxo
Seed idempotente via `update_or_create(date=...)`.

## Validacao de qualidade
### Sem hardcode
Dados ficam no JSON; comando apenas interpreta estrutura.

### Sem estruturas condicionais quebradicas
Comando linear e validado por campos obrigatorios.

### Sem `except: pass`
Nao introduzido.

### Sem mascaramento de erro
JSON ausente ou entrada invalida gera `CommandError`.

### Sem comentarios e docstrings desnecessarios
Nao introduzidos.

## Evidencias
- `python manage.py help seed_system_initial_holidays` registrou o comando sem argumentos customizados.
- `python manage.py check` passou com `System check identified no issues`.
- `python manage.py test system.tests.test_commands --verbosity 2` passou com 6 testes.

## Implementado
- Criado `static/initial_data/seed_system_initial_holidays.json` com 13 feriados de 2026.
- Criado `seed_system_initial_holidays`, idempotente por data e com audit log por feriado.
- Atualizado teste de governanca dos JSONs e teste de idempotencia da seed.
- Atualizado `CLAUDE.md` com o novo comando operacional.

## Desvios do plano
- Nenhum ate o momento.

## Pendencias
- Suite completa ainda possui falhas pre-existentes fora deste escopo, ja observadas antes desta seed.
