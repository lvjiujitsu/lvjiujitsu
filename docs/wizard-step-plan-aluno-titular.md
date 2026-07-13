# Percorrendo o wizard rapidamente ate `step-plan` — aluno titular

## Objetivo

Chegar rapidamente ao `step-plan` para continuar os proximos testes, sem validar pagamento nem finalizar cadastro.

## Tipo de cadastro

- Perfil: `Aluno`
- Dependentes: nao marcar "Treino com dependentes tambem"
- Pessoas esperadas antes do final: nenhuma `Person` deve ser criada apenas por chegar ao `step-plan`

## Pre-condicoes

- Servidor Django rodando em `http://localhost:8000`.
- Seeds minimas de turmas e planos executadas quando o teste depender de catalogos reais.
- Abrir `http://localhost:8000/register/`.

## Dados rapidos sugeridos

Use dados unicos por execucao para evitar colisao em validacoes futuras:

- Nome: `Aluno Titular Teste <timestamp>`
- CPF: CPF valido ainda nao usado no banco
- Data de nascimento: `10/10/1990`
- Sexo biologico: qualquer opcao disponivel
- Telefone: opcional
- E-mail: `aluno.titular.<timestamp>@teste.local`
- Senha: `Teste@12345`
- Saude: pode deixar campos opcionais vazios
- Artes marciais: selecionar `Nao, sou iniciante`
- Turma: selecionar qualquer turma elegivel exibida

## Percurso rapido

1. Em `step-profile`, clicar em `Aluno`.
2. Nao marcar `Treino com dependentes tambem`.
3. Clicar em `Proximo`.
4. Em `step-principal`, preencher nome, CPF, data de nascimento, sexo biologico, e-mail, senha e confirmacao.
5. Clicar em `Proximo`.
6. Em `step-health`, deixar opcionais vazios ou preencher apenas se o teste exigir.
7. Clicar em `Proximo`.
8. Em `step-martial`, selecionar `Nao, sou iniciante`.
9. Clicar em `Proximo`.
10. Em `step-classes`, selecionar uma turma elegivel.
11. Clicar em `Proximo`.
12. Confirmar que a tela atual e `step-plan` com titulo `Escolha seu plano`.

## Criterios de parada

- Parar ao chegar em `step-plan`.
- Nao clicar em pagamento.
- Nao concluir cadastro.
- Se for feita validacao ORM neste ponto, o CPF do aluno ainda nao deve existir em `Person`.

## Proximo teste

Continuar a partir da selecao de plano — catalogo `PlanTier`/`PlanPrice` (PRD-127/129) — e pagamento da mensalidade via Asaas (PIX/cartao) ou Stripe recorrente conforme o ciclo do plano escolhido (PRD-041/137), seguindo o PRD-040.

Para perfis operacionais sequenciais (professor, administrativo) fora do escopo aluno/dependente/responsavel destes guias, ver PRD-115.
