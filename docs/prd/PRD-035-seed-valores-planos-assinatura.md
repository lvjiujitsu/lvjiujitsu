# PRD-035: Seed de Valores dos Planos de Assinatura

## Resumo do que será implementado
Criar `seed_system_initial_subscription_plans_values` para inserir os valores cobrados por plano, frequencia semanal, gateway, forma de pagamento e periodicidade, a partir de JSON proprio.

## Tipo de demanda
Nova feature

## Problema atual
`seed_system_initial_subscription_plans` cria apenas os planos base de categoria. Os valores reais de cobranca estao na planilha anexada pelo usuario e precisam virar dados editaveis no banco.

## Objetivo
Gerar 72 planos precificados: 3 categorias x 2 frequencias x 3 gateways/formas x 4 ciclos de cobranca.

## Context Ledger
### Arquivos lidos integralmente
- `system/models/plan.py`
- `system/management/commands/seed_system_initial_subscription_plans.py`
- `static/initial_data/seed_system_initial_subscription_plans.json`
- `system/tests/test_plan_models.py`
- `system/tests/test_commands.py`

### Arquivos adjacentes consultados
- `system/signals.py`
- `system/models/__init__.py`
- `system/tests/test_plan_eligibility.py`
- anexos de plano resumido e plano detalhado enviados pelo usuario

### Internet / documentação oficial
- Nao aplicavel.

### MCPs / ferramentas verificadas
- PowerShell — status ok — leitura e validacao local.

### Limitações encontradas
- Alguns valores de cartao possuem diferenca de centavos quando recalculados apenas com campos `Decimal(2)` de valor liquido. A seed preserva o valor cobrado do JSON como fonte de verdade.

## Prompt de execução
### Persona
Agente de desenvolvimento Django seguindo SDD + TDD.

### Ação
Implementar seed granular de valores de planos usando o modelo dinamico existente.

### Contexto
O modelo `SubscriptionPlan` ja possui campos para valor liquido mensal desejado, taxa fixa, taxa percentual, desconto do ciclo, gateway, forma de pagamento e periodicidade.

### Restrições
- sem migracoes
- sem argumentos `--`
- dados em `static/initial_data/seed_system_initial_subscription_plans_values.json`
- seed idempotente
- valores cobrados do JSON prevalecem sobre arredondamentos intermediarios

### Critérios de aceite
- [x] O comando `seed_system_initial_subscription_plans_values` existe.
- [x] A seed cria/atualiza 72 planos precificados.
- [x] Rodar duas vezes nao duplica planos.
- [x] Planos base `individual`, `loyalty`, `family` ficam inativos apos aplicar valores.
- [x] `python manage.py test system.tests.test_commands --verbosity 2` passa.
- [x] `python manage.py check` passa.

### Evidências esperadas
- Testes focados passando.
- Check passando.

### Formato de saída
Codigo implementado + comando para execucao manual.

## Escopo
- JSON de valores de planos.
- Comando de seed de valores.
- Teste de comando/idempotencia.
- Atualizacao de documentacao operacional.

## Fora do escopo
- Alterar schema.
- Sincronizar planos no Stripe.
- Recriar telas de escolha de plano.

## Arquivos impactados
- `static/initial_data/seed_system_initial_subscription_plans_values.json`
- `system/management/commands/seed_system_initial_subscription_plans_values.py`
- `system/tests/test_commands.py`
- `CLAUDE.md`

## Riscos e edge cases
- Se o usuario alterar manualmente os valores no admin e rerodar a seed, o JSON volta a ser fonte de verdade.
- Valores de cartao podem ter arredondamento diferente do calculo puro; por isso a seed fixa `price` com o valor cobrado informado.

## Regras e restrições
- SDD antes de codigo
- TDD para implementacao
- sem migracoes
- validacao obrigatoria

## Plano
- [x] 1. Ler modelo e seed existente.
- [x] 2. Extrair valores dos anexos.
- [x] 3. Criar JSON.
- [x] 4. Criar comando.
- [x] 5. Criar teste.
- [x] 6. Validar.

## Validação visual
Nao aplicavel; mudanca sem UI.

## Validação ORM
Validado via testes Django com banco de teste.

## Validação de qualidade
### Sem hardcode
Valores ficam no JSON; comando apenas expande e aplica.

### Sem estruturas condicionais quebradiças
Mapeamentos de ciclos e gateways sao explicitos e pequenos.

### Sem `except: pass`
Nao introduzido.

### Sem mascaramento de erro
Entradas invalidas geram `CommandError`.

### Sem comentários e docstrings desnecessários
Nao introduzido.

## Evidências
- `python manage.py help seed_system_initial_subscription_plans_values`: comando registrado sem argumentos customizados.
- `python manage.py test system.tests.test_commands --verbosity 2`: 7 testes, OK.
- `python manage.py test`: 158 testes, OK.
- `python manage.py check`: sem issues.

## Implementado
- Criado JSON `seed_system_initial_subscription_plans_values.json` com os valores extraidos dos anexos.
- Criado comando `seed_system_initial_subscription_plans_values`.
- Criado teste de idempotencia e valores chave da seed.
- Atualizado `CLAUDE.md` com o comando operacional.

## Desvios do plano
- Nenhum ate o momento.

## Pendências
- Recriar testes de UI quando as telas forem reimplementadas.
