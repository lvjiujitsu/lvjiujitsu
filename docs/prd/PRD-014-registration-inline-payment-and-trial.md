# PRD-014: Reimplementação do checkout no cadastro (inline) + opção pagar depois com 1 aula experimental

## Resumo
Reestruturar o fechamento do cadastro para que a decisão de pagamento aconteça na própria etapa final do wizard, sem depender de uma tela intermediária separada como fluxo principal. O usuário deve poder: (1) pagar com cartão, (2) pagar com PIX, ou (3) concluir sem pagar naquele momento, recebendo mensagem clara e ativação de período experimental de 1 aula.

Também é obrigatório tratar configuração de ENV de forma robusta, evitando erro técnico bruto em tela (ex.: `ASAAS_API_KEY não configurada no .env`) para usuário final.

## Problema atual
1. O wizard de cadastro termina e redireciona para outra tela (`/payments/checkout/<id>/`), quebrando continuidade da UX esperada no print aprovado.
2. Quando o PIX é acionado sem `ASAAS_API_KEY`, o usuário recebe erro técnico bruto (HTTP 400 com mensagem interna), em vez de feedback orientado.
3. Não existe opção explícita de “concluir cadastro e pagar depois” com regra de período experimental de 1 aula.
4. O fluxo atual de bloqueio por pagamento pendente (`payment_pending`) não contempla exceção de trial de forma explícita.

## Objetivo
1. Exibir as opções de pagamento **dentro da etapa Resumo do cadastro** (wizard).
2. Permitir escolha explícita de ação final:
   - pagar agora com cartão (Stripe),
   - pagar agora com PIX (Asaas),
   - concluir e pagar depois (ativando 1 aula experimental).
3. Garantir UX segura para ENV faltante:
   - não expor mensagem técnica crua ao usuário final;
   - mostrar mensagem amigável e ação alternativa.
4. Preservar regras de negócio e trilha de pedidos (`RegistrationOrder`) sem regressão de segurança/autorização.

## Contexto consultado
- **Código interno (fluxo atual):**
  - `templates/login/register.html`
  - `static/system/js/auth/registration-wizard-clean.js`
  - `system/views/auth_views.py`
  - `system/views/payment_views.py`
  - `system/views/asaas_views.py`
  - `system/services/registration_checkout.py`
  - `system/services/portal_auth.py`
  - `system/services/asaas_client.py`
  - `lvjiujitsu/settings.py`
  - `.env.example`
- **Context7:** indisponível nesta sessão; uso de documentação web oficial como fallback.
- **Web:**
  - Stripe Checkout quickstart: https://docs.stripe.com/checkout/quickstart
  - Asaas docs (visão geral): https://docs.asaas.com/docs
  - Asaas criação de cliente: https://docs.asaas.com/docs/criando-um-cliente
  - Asaas webhooks e idempotência: https://docs.asaas.com/docs/sobre-os-webhooks
  - Django messages framework: https://docs.djangoproject.com/en/4.1/ref/contrib/messages/

## Dependências adicionadas
- Nenhuma nova dependência funcional prevista.
- Validar se `requests` está explicitamente fixado em `requirements.txt` (uso direto em `system/services/asaas_client.py`); se não estiver, adicionar explicitamente.

## Escopo / Fora do escopo
### Escopo
- Reimplementar etapa final do wizard para incluir cards/botões de decisão de pagamento inline.
- Introduzir campo de intenção de checkout no form (ex.: `checkout_action`).
- Alterar `PortalRegisterView.form_valid` para resolver o destino conforme ação escolhida.
- Tratar falta de ENV de gateway com fallback de UX (mensagem amigável + opção alternativa), sem erro técnico cru em tela.
- Implementar regra de “1 aula experimental” ao concluir sem pagar:
  - persistência de concessão,
  - consumo da aula no check-in,
  - bloqueio após consumo.
- Ajustar autenticação/portal para respeitar exceção de trial sem abrir acesso irrestrito.
- Cobrir fluxo com testes por camada.

### Fora do escopo
- Alterações de layout globais fora da tela de cadastro e telas de pagamento relacionadas.
- Novos meios de pagamento além Stripe/PIX.
- Política comercial de trial diferente de “1 aula”.
- Alterações em produção (deploy/infra) além checklist de ENV e configuração.

## Arquivos impactados
- **Models / migração**
  - `system/models/` (novo modelo de trial ou extensão equivalente)
  - `system/migrations/`
  - `system/models/__init__.py`
- **Forms**
  - `system/forms/registration_forms.py` (novo campo de ação final)
- **Services**
  - `system/services/registration.py`
  - `system/services/registration_checkout.py`
  - `system/services/portal_auth.py`
  - `system/services/class_calendar.py` (consumo da aula experimental no check-in)
  - `system/services/membership.py` (integração com regra de pending/trial, se necessário)
  - `system/services/asaas_client.py` (mensagens e erro amigável de configuração)
- **Views**
  - `system/views/auth_views.py`
  - `system/views/payment_views.py`
  - `system/views/asaas_views.py`
- **Templates**
  - `templates/login/register.html`
  - `templates/billing/payment_method_choice.html` (rebaixar para fallback/compatibilidade)
  - `templates/billing/pix_checkout.html` (mensagens amigáveis de indisponibilidade)
  - `templates/base.html` / `templates/includes/_messages.html` (garantir render de mensagens globais nas telas baseadas em `base.html`)
- **Static**
  - `static/system/js/auth/registration-wizard-clean.js`
  - `static/system/css/auth/login.css` (estilos dos cards/CTAs de pagamento inline no resumo)
- **Config**
  - `.env.example`
  - `lvjiujitsu/settings.py` (semântica de fallback e flags, se necessário)
- **Tests**
  - `system/tests/test_views.py`
  - `system/tests/test_forms.py`
  - `system/tests/test_models.py`
  - `system/tests/test_calendar.py`
  - `system/tests/test_asaas.py`

## Riscos e edge cases
- Usuário seleciona PIX sem `ASAAS_API_KEY`: deve receber mensagem amigável e opção de fallback (cartão/pagar depois), sem 500/400 técnico exposto.
- Usuário seleciona cartão sem `STRIPE_SECRET_KEY`: mesmo tratamento de fallback.
- Reenvio do formulário em refresh/back (idempotência): evitar múltiplos pedidos ou múltiplas concessões de trial.
- Trial consumido em check-in especial vs. check-in de aula regular: regra deve ser consistente para ambos.
- Usuário com pedido pendente + trial já consumido: login deve orientar pagamento, sem acesso indevido.
- Sessão expirada entre cadastro e pagamento: redirecionar com mensagem e preservar segurança.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- **SDD:** implementação somente após este PRD.
- **TDD (Red-Green-Refactor):** criar testes de regressão antes da alteração do fluxo final.
- **MTV:** regra de negócio em services; views finas.
- **Service Objects:** operações de cadastro/pagamento/trial em serviços transacionais (`@transaction.atomic` quando houver múltiplas escritas).
- **Segurança:** sem hardcode de credenciais; CSRF mantido; validação server-side obrigatória.
- **UX resiliente:** nenhuma tela deve exibir erro técnico bruto por falta de ENV.

## Critérios de aceite (assertions testáveis)
- [ ] Na etapa Resumo do cadastro, o usuário visualiza ações: pagar com cartão, pagar com PIX e concluir/pagar depois.
- [ ] Selecionando cartão no resumo, o fluxo inicia checkout Stripe sem exigir passagem manual pela tela intermediária de método.
- [ ] Selecionando PIX no resumo, o fluxo abre checkout PIX e exibe QR/copia-cola quando ENV estiver configurado.
- [ ] Selecionando concluir/pagar depois, o cadastro finaliza com mensagem explícita de pagamento pendente e concessão de 1 aula experimental.
- [ ] Após 1 check-in válido, o benefício experimental é consumido e não pode ser reutilizado.
- [ ] Sem `ASAAS_API_KEY`, o sistema não exibe erro técnico em tela; mostra mensagem amigável e alternativa de ação.
- [ ] Sem `STRIPE_SECRET_KEY`, o sistema não exibe erro técnico em tela; mostra mensagem amigável e alternativa de ação.
- [ ] Login de usuário com pagamento pendente respeita exceção de trial ativo; após consumo do trial, volta a exigir pagamento.
- [ ] Fluxos existentes não relacionados (cadastro sem cobrança, dashboards administrativos, webhooks) permanecem sem regressão.

## Plano (ordenado por dependência — fundações primeiro)
- [ ] 1. Modelar persistência do trial de 1 aula (model + migration + regras de consumo).
- [ ] 2. Adicionar campo `checkout_action` no form e validação server-side da ação final.
- [ ] 3. Implementar serviço de orquestração de finalização do cadastro por ação (stripe/pix/pay_later).
- [ ] 4. Integrar regra de trial no auth/check-in (bloqueio/liberação e consumo).
- [ ] 5. Atualizar `register.html` para exibir ações de pagamento inline na etapa Resumo.
- [ ] 6. Atualizar JS/CSS do wizard para seleção de ação final e UX de fallback.
- [ ] 7. Readequar telas de pagamento existentes para papel de fallback/compatibilidade.
- [ ] 8. Padronizar tratamento de erro de ENV em Stripe/Asaas para mensagens amigáveis.
- [ ] 9. Implementar testes (forms/services/views/calendar) cobrindo fluxos felizes e de erro.
- [ ] 10. Executar validação completa (testes, collectstatic, checks de ENV e UX).

## Comandos de validação
```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test --verbosity 2
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
.\.venv\Scripts\python.exe manage.py findstatic system/css/auth/login.css
.\.venv\Scripts\python.exe manage.py findstatic system/js/auth/registration-wizard-clean.js
```

## Implementado (preencher ao final)
- Em aberto.

## Desvios do plano
- Em aberto.
