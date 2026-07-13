# Percorrendo o wizard rapidamente ate `step-plan` — responsavel com aluno

## Objetivo

Chegar rapidamente ao `step-plan` no fluxo em que um responsavel cadastra aluno(s), para permitir os proximos testes de plano, mensalidade Asaas, materiais e finalizacao.

## Tipo de cadastro

- Perfil: `Responsavel`
- Alunos sob responsabilidade: quantidade rapida recomendada `1`
- Pessoas esperadas antes do final: nenhuma `Person` deve ser criada apenas por chegar ao `step-plan`

## Pre-condicoes

- Servidor Django rodando em `http://localhost:8000`.
- Seeds minimas de turmas e planos executadas quando o teste depender de catalogos reais.
- Abrir `http://localhost:8000/register/`.

## Dados rapidos sugeridos

Use CPFs e e-mails unicos por execucao.

### Responsavel

- Nome: `Responsavel Teste <timestamp>`
- CPF: CPF valido ainda nao usado no banco
- Sexo biologico: qualquer opcao disponivel
- E-mail: `responsavel.<timestamp>@teste.local`
- Senha: `Teste@12345`
- Saude: opcionais vazios
- Artes marciais: `Nao, sou iniciante`

### Aluno

- Grau de parentesco: qualquer opcao disponivel
- Nome: `Aluno Do Responsavel <timestamp>`
- CPF: CPF valido ainda nao usado no banco
- Data de nascimento: usar idade compativel com alguma turma disponivel
- Sexo biologico: qualquer opcao disponivel
- E-mail: `aluno.responsavel.<timestamp>@teste.local`
- Senha: `Teste@12345`
- Saude: opcionais vazios
- Artes marciais: `Nao, sou iniciante`

## Percurso rapido

1. Em `step-profile`, clicar em `Responsavel`.
2. Manter quantidade `1` em `Quantos alunos voce vai cadastrar?`.
3. Clicar em `Proximo`.
4. Em `step-principal`, preencher dados obrigatorios do responsavel.
5. Clicar em `Proximo`.
6. Em `step-health` do responsavel, deixar opcionais vazios.
7. Clicar em `Proximo`.
8. Em `step-martial` do responsavel, selecionar `Nao, sou iniciante`.
9. Clicar em `Proximo`.
10. Em `step-dep`, preencher dados obrigatorios do aluno.
11. Clicar em `Proximo`.
12. Em `step-health` do aluno, deixar opcionais vazios.
13. Clicar em `Proximo`.
14. Em `step-martial` do aluno, selecionar `Nao, sou iniciante`.
15. Clicar em `Proximo`.
16. Em `step-classes` do aluno, selecionar turma elegivel.
17. Clicar em `Proximo`.
18. Confirmar que a tela atual e `step-plan` com titulo `Escolha seu plano`.

## Criterios de parada

- Parar ao chegar em `step-plan`.
- Nao clicar em pagamento.
- Nao concluir cadastro.
- Se for feita validacao ORM neste ponto, os CPFs do responsavel e do aluno ainda nao devem existir em `Person`.

## Proximo teste

Continuar a partir da selecao de plano — catalogo `PlanTier`/`PlanPrice` (PRD-127/129), incluindo desconto familia como modificador de tier — e pagamento da mensalidade via Asaas (PIX/cartao) ou Stripe recorrente conforme o ciclo do plano escolhido (PRD-041/137), seguindo o PRD-040.

Para perfis operacionais sequenciais (professor, administrativo) fora do escopo aluno/dependente/responsavel destes guias, ver PRD-115.
