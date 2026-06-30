# PRD-071: Alinhamento da suite legada ao escopo progressivo

## Summary
Registrar o achado da PRD-070: a suite completa do LV ainda contem testes de modulos/templates removidos no reset progressivo, enquanto a etapa atual recriou apenas Login e Home.

## Problem
`manage.py test --verbosity 2` executou 226 testes. O resultado foi 217 OK e 9 erros por `TemplateDoesNotExist`/arquivo ausente em contratos antigos:

- `calendar` espera template de calendario.
- `people` espera templates de lista/detalhe de Pessoas.
- `plans` espera templates de planos.
- `register` espera `templates/login/register.html`.

Esses modulos nao foram recriados nesta etapa e nao devem ser mascarados por skips silenciosos.

## Goal
Decidir e executar uma das estrategias:

1. Remover ou arquivar testes legados dos modulos ainda nao reimplementados.
2. Recriar contratos minimos por modulo quando cada PRD progressiva autorizar o modulo.
3. Separar suites por etapa (`current_scope` vs `legacy_future_scope`) para que o status de regressao reflita o escopo real.

## Out of scope
- Recriar Pessoas completo, Planos, Calendario ou Cadastro publico nesta PRD.
- Criar skips silenciosos sem rastreabilidade.
- Alterar historico de PRDs antigas.

## Evidence
- `manage.py test system.tests.test_home_dashboard system.tests.test_admin_hubs_contract --verbosity 2`: 3 testes OK.
- `manage.py test --verbosity 2`: 226 testes, 9 erros em contratos de templates removidos.

## Acceptance criteria
- Suite proporcional ao escopo progressivo roda verde.
- Testes legados restantes ficam explicitamente separados, removidos ou vinculados a PRDs futuras.
- Nenhum teste aponta para template inexistente sem decisao de escopo.

## Final status
Registrada para decisao posterior.
