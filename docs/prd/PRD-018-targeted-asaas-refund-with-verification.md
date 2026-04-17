# PRD-018: Estorno pontual Asaas com timer e verificação pós-ação

## Resumo
Evoluir `limpar_asaas.py` para suportar estorno pontual de cobrança específica com timer e verificação após operação, evitando limpeza ampla indevida (como remoção de cliente e outras cobranças).

## Problema atual
1. A execução ampla (`--all`) pode processar cobranças não desejadas para o teste.
2. Não havia modo explícito para operar em apenas uma cobrança de `250`.
3. Faltava verificação pós-estorno com retentativa temporizada.
4. Remoção de cliente pode exigir confirmação adicional (ex.: SMS), quebrando fluxo quando não é o objetivo da operação.

## Objetivo
1. Permitir alvo exato por cobrança (`--payment-id`).
2. Incluir timer e retentativas de verificação pós-estorno.
3. Executar somente estorno quando solicitado (`--refund-only`).
4. Pular clientes/transferências quando necessário (`--skip-customers`, `--skip-transfers`).

## Contexto consultado
- `limpar_asaas.py`
- Referência Asaas:
  - `GET /v3/payments`
  - `POST /v3/payments/{id}/refund`
  - `DELETE /v3/customers/{id}`
  - `GET /v3/finance/balance`

## Dependências adicionadas
- Nenhuma.

## Escopo / Fora do escopo
### Escopo
- Novas flags operacionais para estorno pontual e seguro.
- Verificação com tentativas e espera entre checks.

### Fora do escopo
- Alterar integrações webhooks/checkout.
- Implementar automação de confirmação SMS no Asaas.

## Arquivos impactados
- `limpar_asaas.py`
- `docs/prd/PRD-018-targeted-asaas-refund-with-verification.md`

## Riscos e edge cases
- Estorno pode seguir recusando por saldo insuficiente.
- Status pode demorar a refletir e exigir mais tentativas.

## Critérios de aceite
- [ ] `--payment-id` processa somente cobrança(s) informada(s).
- [ ] `--refund-only` impede caminho de deleção para cobrança pendente.
- [ ] Verificação pós-estorno roda com timer e número de tentativas configurável.
- [ ] `--skip-customers` evita remoção de cliente durante estorno pontual.

## Plano
- [x] 1. Adicionar flags de escopo e segurança.
- [x] 2. Implementar timer e verificação pós-estorno.
- [x] 3. Bloquear combinações ambíguas de escopo.
- [ ] 4. Executar estorno da cobrança alvo de 250.

## Comandos de validação
- `.\.venv\Scripts\python.exe -m py_compile limpar_asaas.py`
- `.\.venv\Scripts\python.exe limpar_asaas.py --payment-id <id> --refund-only --skip-customers --skip-transfers`
- `.\.venv\Scripts\python.exe limpar_asaas.py --payment-id <id> --execute --refund-only --skip-customers --skip-transfers`

## Implementado
- Flags adicionadas: `--payment-id`, `--refund-only`, `--retry-attempts`, `--retry-wait-seconds`, `--skip-customers`, `--skip-transfers`.
- Verificação pós-estorno com espera entre tentativas implementada.

## Desvios do plano
- Nenhum.
