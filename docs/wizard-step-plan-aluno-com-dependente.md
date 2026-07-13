# Percorrendo o wizard rapidamente ate `step-plan` — aluno titular com dependente

## Objetivo

Chegar rapidamente ao `step-plan` com um aluno titular que tambem cadastra dependente(s), preservando o fluxo para os proximos testes.

## Tipo de cadastro

- Perfil: `Aluno`
- Dependentes: marcar `Treino com dependentes tambem`
- Quantidade rapida recomendada: `1`
- Pessoas esperadas antes do final: nenhuma `Person` deve ser criada apenas por chegar ao `step-plan`

## Pre-condicoes

- Servidor Django rodando em `http://localhost:8000`.
- Seeds minimas de turmas e planos executadas quando o teste depender de catalogos reais.
- Abrir `http://localhost:8000/register/`.

## Dados rapidos sugeridos

Use CPFs e e-mails unicos por execucao.

### Titular

- Nome: `Aluno Titular Com Dependente <timestamp>`
- CPF: CPF valido ainda nao usado no banco
- Data de nascimento: `10/10/1990`
- Sexo biologico: qualquer opcao disponivel
- E-mail: `titular.dependente.<timestamp>@teste.local`
- Senha: `Teste@12345`
- Saude: opcionais vazios
- Artes marciais: `Nao, sou iniciante`

### Dependente

- Grau de parentesco: qualquer opcao disponivel
- Nome: `Dependente Teste <timestamp>`
- CPF: CPF valido ainda nao usado no banco
- Data de nascimento: usar idade compativel com alguma turma disponivel
- Sexo biologico: qualquer opcao disponivel
- E-mail: `dependente.<timestamp>@teste.local`
- Senha: `Teste@12345`
- Saude: opcionais vazios
- Artes marciais: `Nao, sou iniciante`

## Percurso rapido

1. Em `step-profile`, clicar em `Aluno`.
2. Marcar `Treino com dependentes tambem`.
3. Manter quantidade `1` para teste rapido.
4. Clicar em `Proximo`.
5. Em `step-principal`, preencher dados obrigatorios do titular.
6. Clicar em `Proximo`.
7. Em `step-health` do titular, deixar opcionais vazios.
8. Clicar em `Proximo`.
9. Em `step-martial` do titular, selecionar `Nao, sou iniciante`.
10. Clicar em `Proximo`.
11. Em `step-dep`, preencher dados obrigatorios do dependente.
12. Clicar em `Proximo`.
13. Em `step-health` do dependente, deixar opcionais vazios.
14. Clicar em `Proximo`.
15. Em `step-martial` do dependente, selecionar `Nao, sou iniciante`.
16. Clicar em `Proximo`.
17. Em `step-classes` do titular, selecionar turma elegivel.
18. Clicar em `Proximo`.
19. Em `step-classes` do dependente, selecionar turma elegivel.
20. Clicar em `Proximo`.
21. Confirmar que a tela atual e `step-plan` com titulo `Escolha seu plano`.

## Criterios de parada

- Parar ao chegar em `step-plan`.
- Nao clicar em pagamento.
- Nao concluir cadastro.
- Se for feita validacao ORM neste ponto, os CPFs do titular e do dependente ainda nao devem existir em `Person`.

## Proximo teste

Continuar a partir da selecao de plano — catalogo `PlanTier`/`PlanPrice` (PRD-127/129), incluindo desconto familia como modificador de tier — e pagamento da mensalidade via Asaas (PIX/cartao) ou Stripe recorrente conforme o ciclo do plano escolhido (PRD-041/137), seguindo o PRD-040.

Para perfis operacionais sequenciais (professor, administrativo) fora do escopo aluno/dependente/responsavel destes guias, ver PRD-115.
