# PRD-016: Limpeza operacional do sandbox Asaas

## Resumo
Criar um utilitário temporário para limpar cobranças e clientes presos no sandbox Asaas usando a API, sem depender da interface visual do painel.

## Problema atual
O painel sandbox do Asaas pode demorar para refletir operações de pagamento, estorno ou exclusão e pode aparentar restaurar dados após refresh. Isso dificulta limpar cobranças de teste manualmente.

## Objetivo
Permitir listar saldo, cobranças, transferências e clientes do sandbox e, quando confirmado, deletar cobranças pendentes, estornar cobranças recebidas/confirmadas, cancelar transferências pendentes e deletar clientes de teste via API.

## Contexto consultado
- Context7: Requests `/psf/requests`; confirmado uso de `headers`, `params`, `json`, `timeout` e tratamento de exceções HTTP/rede.
- Web:
  - Asaas listar cobranças: `GET /v3/payments` com `offset`, `limit` e filtro `customer`.
  - Asaas excluir cobrança: `DELETE /v3/payments/{id}`.
  - Asaas estornar cobrança: `POST /v3/payments/{id}/refund`.
  - Asaas listar clientes: `GET /v3/customers`.
  - Asaas remover cliente: `DELETE /v3/customers/{id}`.
  - Asaas autenticação: sandbox atual documentado como `https://api-sandbox.asaas.com/v3`; o projeto mantém `ASAAS_API_URL` configurável no `.env`.

## Dependências adicionadas
- `requests==2.33.1` — uso direto já existente em `system/services/asaas_client.py` e agora registrado explicitamente em `requirements.txt`.

## Escopo / Fora do escopo
- Escopo: script temporário `limpar_asaas.py`, leitura segura de `ASAAS_API_KEY`/`ASAAS_API_URL` via settings Django, modo `dry-run` por padrão, execução destrutiva somente com `--execute`, consulta de saldo, cancelamento de transferências pendentes e opção explícita `--reset-local-financial`.
- Fora do escopo: alterar fluxo de checkout, criar comando Django permanente, limpar assinaturas/parcelamentos/links de pagamento.

## Arquivos impactados
- `limpar_asaas.py`
- `lvjiujitsu/settings.py`
- `.env.example`
- `.env`
- `requirements.txt`
- `.gitignore`
- `docs/prd/PRD-016-asaas-sandbox-cleanup.md`

## Riscos e edge cases
- API key sem permissão de leitura, exclusão ou estorno retorna 401/403.
- Cobranças em status diferente de `PENDING`, `RECEIVED` ou `CONFIRMED` podem não ser removidas automaticamente.
- Clientes com cobranças remanescentes podem não ser deletados.
- Estorno pode ser assíncrono e depender de saldo/regras do sandbox.
- Limpeza ampla sem filtro pode apagar clientes de teste que ainda interessam.

## Regras e restrições
- Não hardcodar chaves; usar `.env`.
- Não imprimir valores sensíveis.
- Usar timeout nas chamadas HTTP.
- Usar modo seguro `dry-run` como padrão.
- Registrar dependência direta em `requirements.txt`.

## Critérios de aceite
- [ ] Sem `--execute`, o script deve listar o que faria e não chamar endpoints destrutivos.
- [ ] Com `--customer-id`, o script deve filtrar cobranças pelo cliente informado e tentar remover apenas esse cliente.
- [ ] Com `--all --execute`, o script deve processar todas as cobranças e todos os clientes retornados pela API.
- [ ] Cobranças `PENDING` devem ser removidas via `DELETE /payments/{id}`.
- [ ] Cobranças `RECEIVED` e `CONFIRMED` devem ser estornadas via `POST /payments/{id}/refund`.
- [ ] Erros por item devem ser exibidos e não devem interromper a limpeza dos demais itens.
- [ ] O script deve falhar com mensagem clara se `ASAAS_API_KEY` estiver ausente.
- [ ] Sem `--reset-local-financial`, o script não deve apagar dados financeiros locais.
- [ ] Com `--reset-local-financial --execute`, o script deve limpar registros financeiros locais e vínculos `asaas_customer_id`.

## Plano
- [x] 1. Conferir contexto do projeto e configuração Asaas.
- [x] 2. Consultar docs de Requests e Asaas.
- [x] 3. Registrar `requests` no `requirements.txt`.
- [x] 4. Criar script temporário com `dry-run`, filtro por cliente e execução ampla explícita.
- [x] 5. Validar sintaxe e modo `dry-run`.
- [x] 6. Executar limpeza real via API com aprovação de rede.
- [x] 7. Rodar validações Django essenciais.

## Comandos de validação
- `.\.venv\Scripts\python.exe -m py_compile limpar_asaas.py`
- `.\.venv\Scripts\python.exe limpar_asaas.py --all`
- `.\.venv\Scripts\python.exe limpar_asaas.py --all --execute`
- `.\.venv\Scripts\python.exe limpar_asaas.py --all --execute --reset-local-financial` (somente se a limpeza local for desejada)
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
- `.\.venv\Scripts\python.exe manage.py findstatic system/css/portal/portal.css`
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py showmigrations`

## Implementado
- Criado `limpar_asaas.py` com leitura de configurações via Django, paginação, consulta de saldo, tratamento de cobranças/transferências/clientes, `dry-run` por padrão e execução real via `--execute`.
- Adicionada opção explícita `--reset-local-financial` para limpar dados financeiros locais quando necessário.
- Registrado `requests==2.33.1` explicitamente em `requirements.txt`.
- Atualizada URL padrão/documentada do sandbox Asaas para `https://api-sandbox.asaas.com/v3`.
- `dry-run --all` inicial encontrou 2 cobranças `RECEIVED` e 6 clientes.
- Execução real estornou 1 cobrança e deletou 6 clientes.
- Uma cobrança permaneceu sem estorno porque o Asaas retornou saldo insuficiente: valor líquido `249.01`, saldo sandbox disponível `248.02`.

## Desvios do plano
- A limpeza real não zerou todas as cobranças porque a API recusou estorno integral de uma delas por saldo insuficiente no sandbox.
