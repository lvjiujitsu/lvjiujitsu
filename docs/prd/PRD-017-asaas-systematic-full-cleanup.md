# PRD-017: Limpeza sistêmica Asaas + financeiro local

## Resumo
Evoluir o utilitário `limpar_asaas.py` para uma limpeza sistêmica e auditável, cobrindo verificação de saldo disponível, estorno/exclusão de movimentações no Asaas, remoção de clientes e opção de limpeza financeira local do sistema.

## Problema atual
1. O script atual limpa cobranças/clientes, mas não evidencia saldo disponível antes/depois da operação.
2. Transferências (movimentações de saída) não entram no ciclo de limpeza sistemática.
3. Não existe opção de limpeza conjunta do estado financeiro local após limpeza remota do Asaas.

## Objetivo
1. Validar e registrar saldo disponível no início e no fim da execução.
2. Processar cobranças com regra explícita de estorno/exclusão.
3. Processar transferências com tentativa de cancelamento para status elegíveis.
4. Remover clientes ao final do ciclo.
5. Opcionalmente limpar também os registros financeiros locais com uma flag explícita.

## Contexto consultado
- **Código interno:**
  - `limpar_asaas.py`
  - `system/services/asaas_client.py`
  - `system/models/asaas.py`
  - `system/models/registration_order.py`
  - `system/models/person.py`
- **Web (Asaas API):**
  - `GET /v3/payments` (listar cobranças)
  - `DELETE /v3/payments/{id}` (excluir cobrança)
  - `POST /v3/payments/{id}/refund` (estornar cobrança)
  - `GET /v3/customers` (listar clientes)
  - `DELETE /v3/customers/{id}` (remover cliente)
  - `GET /v3/transfers` (listar transferências)
  - `GET /v3/finance/balance` (saldo disponível; endpoint já usado no projeto)

## Dependências adicionadas
- Nenhuma.

## Escopo / Fora do escopo
### Escopo
- Refatorar `limpar_asaas.py` para pipeline sistemático:
  1. saldo inicial,
  2. cobranças,
  3. transferências,
  4. clientes,
  5. limpeza financeira local (opcional),
  6. saldo final.
- Manter `dry-run` como padrão seguro e execução destrutiva apenas com `--execute`.
- Adicionar flag explícita para limpeza local: `--reset-local-financial`.

### Fora do escopo
- Reconciliar histórico financeiro no Asaas além dos endpoints disponíveis.
- Alterar lógica de checkout/webhook do sistema.
- Reset destrutivo de migrations/banco completo.

## Arquivos impactados
- `limpar_asaas.py`
- `docs/prd/PRD-017-asaas-systematic-full-cleanup.md`

## Riscos e edge cases
- Estorno pode falhar por saldo insuficiente no sandbox.
- Transferências podem não ser canceláveis conforme status/regra da conta.
- Remoção de clientes pode falhar se ainda houver vínculos em aberto no Asaas.
- Limpeza local financeira é destrutiva e deve ocorrer apenas quando explicitamente solicitada.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- SDD: mudanças guiadas por este PRD.
- Segurança: sem exposição de token/chave.
- Operação destrutiva somente com `--execute`.
- Limpeza local só com flag dedicada (`--reset-local-financial`).

## Critérios de aceite (assertions testáveis)
- [ ] Script exibe saldo disponível inicial e final.
- [ ] Em `dry-run`, nenhuma ação destrutiva é executada.
- [ ] Cobranças `PENDING` são elegíveis para exclusão.
- [ ] Cobranças `RECEIVED`/`CONFIRMED` são elegíveis para estorno.
- [ ] Transferências são listadas e tentadas para cancelamento quando elegíveis.
- [ ] Clientes são processados ao final da rotina.
- [ ] Com `--reset-local-financial`, o script inclui limpeza dos registros financeiros locais.

## Plano
- [x] 1. Revisar script atual e pontos de falha observados.
- [x] 2. Definir pipeline sistemático com saldo/movimentações/clientes.
- [x] 3. Implementar suporte a transferências e saldo inicial/final.
- [x] 4. Implementar limpeza financeira local opcional por flag explícita.
- [ ] 5. Validar execução com dry-run e suíte Django.

## Comandos de validação
- `.\.venv\Scripts\python.exe -m py_compile limpar_asaas.py`
- `.\.venv\Scripts\python.exe limpar_asaas.py --all`
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2`

## Implementado (preencher ao final)
- Script reescrito com pipeline completo de limpeza e sumário detalhado.
- Inclusão de consulta de saldo disponível antes e depois da limpeza.
- Inclusão de listagem/processamento de transferências.
- Inclusão de limpeza local financeira opcional via `--reset-local-financial`.
- `dry-run` mantido como padrão.

## Desvios do plano
- A API de cancelamento de transferência pode variar por conta/ambiente; o script tenta `POST /transfers/{id}/cancel` e, em fallback, `DELETE /transfers/{id}`.
