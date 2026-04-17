# PRD-015: Correção de visibilidade da mensalidade no painel do aluno e no administrativo

## Resumo
Corrigir a exibição financeira para que mensalidades pagas apareçam corretamente no painel do aluno e no detalhamento administrativo, incluindo casos de dependente vinculado a responsável e casos legados em que o pedido está pago mas a `Membership` ainda não foi materializada.

## Problema atual
1. Usuário com pedido pago continua vendo “Você ainda não possui uma mensalidade ativa”.
2. No administrativo, o detalhe da pessoa pode não refletir o financeiro quando a cobrança está vinculada ao responsável.
3. Fluxos anteriores deixaram pedidos `paid` sem `Membership`, impedindo renderização de status e próximo vencimento.
4. Dependente não conseguia abrir checkout de pedido do responsável em todos os cenários.

## Objetivo
1. Garantir sincronização automática de `Membership` quando houver pedido pago sem assinatura materializada.
2. Exibir financeiro vinculado ao responsável quando o usuário logado for dependente.
3. Refletir a mesma regra no detalhe administrativo da pessoa.
4. Permitir autorização de checkout entre responsável/dependente sem abrir permissões indevidas.

## Contexto consultado
- **Código interno:**
  - `system/services/membership.py`
  - `system/services/asaas_webhooks.py`
  - `system/views/home_views.py`
  - `system/views/person_views.py`
  - `system/views/payment_views.py`
  - `templates/home/student/dashboard.html`
  - `templates/people/person_detail.html`
  - `system/tests/test_views.py`
  - `system/tests/test_asaas.py`
- **Context7:** indisponível nesta sessão.
- **Web:**
  - Django ORM queries: https://docs.djangoproject.com/en/4.1/topics/db/queries/
  - Django template built-ins: https://docs.djangoproject.com/en/4.1/ref/templates/builtins/

## Dependências adicionadas
- Nenhuma.

## Escopo / Fora do escopo
## Escopo
- Resolver ownership financeiro (pessoa vs responsável) para leitura de mensalidade/pedido pendente.
- Fazer backfill automático de `Membership` a partir de pedido pago elegível.
- Ajustar templates do painel do aluno e do detalhe administrativo.
- Ajustar autorização de checkout para vínculo responsável/dependente.
- Cobrir regressões com testes.

## Fora do escopo
- Alterar regras comerciais de cobrança.
- Mudar layout global do dashboard além do bloco financeiro.
- Refatoração ampla de cadastro além da correção de vínculo financeiro.

## Arquivos impactados
- `system/services/membership.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `system/views/payment_views.py`
- `templates/home/student/dashboard.html`
- `templates/people/person_detail.html`
- `system/tests/test_views.py`

## Riscos e edge cases
- Dependente sem relação válida não pode ganhar acesso indevido ao checkout.
- Pessoa com múltiplos responsáveis exige fallback determinístico.
- Backfill não deve criar assinatura para pedidos gratuitos, estornados ou sem plano.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- SDD aplicado por este PRD.
- TDD com testes de regressão para dashboard, autorização e administrativo.
- MTV preservado: regra em services, views finas, templates apenas apresentação.
- Segurança: sem bypass de autenticação/autorização e sem exposição de erro técnico ao usuário final.

## Critérios de aceite (assertions testáveis)
- [ ] Usuário com pedido pago e sem `Membership` passa a ver mensalidade e próximo vencimento no painel.
- [ ] Dependente com cobrança no responsável visualiza mensalidade do responsável no painel.
- [ ] Detalhe administrativo da pessoa dependente exibe contexto de financeiro vinculado ao responsável.
- [ ] Dependente vinculado consegue abrir checkout de pedido do responsável.
- [ ] Usuário sem vínculo continua bloqueado de pedido de terceiros.

## Plano (ordenado por dependência — fundações primeiro)
- [ ] 1. Consolidar regra de ownership financeiro em `membership.py`.
- [ ] 2. Implementar backfill de `Membership` por pedido pago elegível.
- [ ] 3. Aplicar regra unificada em `StudentHomeView` e `PersonDetailView`.
- [ ] 4. Ajustar autorização de checkout para relacionamento responsável/dependente.
- [ ] 5. Corrigir templates financeiros (aluno e administrativo).
- [ ] 6. Escrever testes de regressão e validar suíte.

## Comandos de validação
```powershell
.\.venv\Scripts\python.exe manage.py test system.tests.test_views system.tests.test_asaas --verbosity 2
.\.venv\Scripts\python.exe manage.py test --verbosity 1
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py findstatic system/css/billing/billing.css
.\.venv\Scripts\python.exe manage.py showmigrations
```

## Implementado (preencher ao final)
- Regra de ownership financeiro adicionada em `membership.py` via `get_membership_owner`.
- Backfill automático implementado em `get_active_membership` para pedidos pagos legados sem `Membership`.
- `StudentHomeView` passou a expor `billing_owner` no contexto e usar regra unificada de financeiro.
- `PersonDetailView` passou a consultar membership/pedidos pelo owner financeiro e exibir contexto correto.
- `payment_views` passou a autorizar checkout para vínculo responsável↔dependente.
- Templates ajustados com mensagem de vínculo financeiro no painel do aluno e no detalhe administrativo.
- Novos testes cobrindo: autorização por vínculo, backfill de membership, dashboard de dependente com responsável e detalhe administrativo com vínculo financeiro.

## Desvios do plano
- Nenhum desvio funcional relevante.
