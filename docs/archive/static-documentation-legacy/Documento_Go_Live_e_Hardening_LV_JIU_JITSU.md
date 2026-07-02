# Documento de Go-Live e Hardening - LV JIU JITSU

## 1. Objetivo

Consolidar o checklist operacional minimo para colocar o sistema em producao com seguranca, rastreabilidade e capacidade de suporte.

## 2. Guardrails ativos no codigo

- Login por CPF com bloqueio progressivo configuravel via `AUTH_LOGIN_MAX_FAILED_ATTEMPTS` e `AUTH_LOGIN_LOCK_MINUTES`.
- Cookies de sessao e CSRF endurecidos por `settings`.
- Upload de comprovante validado por extensao e tamanho.
- Webhook Stripe idempotente com log de sucesso e falha.
- Exportacao CSV critica protegida por arquivo de controle com fail-fast.
- Divergencia relevante de caixa gera alerta gerencial persistido.
- Auditoria transversal para autenticacao, financeiro, graduacao, emergencia, pagamentos, PDV e exportacoes.

## 3. Checklist antes de subir

- Definir `DJANGO_SECRET_KEY` forte.
- Definir `DJANGO_ALLOWED_HOSTS`.
- Ativar `DJANGO_SECURE_COOKIES=true` em ambiente HTTPS.
- Configurar `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` e `STRIPE_WEBHOOK_SECRET`.
- Confirmar `CRITICAL_EXPORT_CONTROL_FILE` e manter `EXPORT_ALLOWED=1` no arquivo.
- Validar diretório de `REPORT_EXPORTS_DIR` com permissão de escrita.
- Rodar `manage.py migrate`.
- Rodar `manage.py check`.
- Rodar `pytest -q`.

## 4. Validacao operacional minima

- Login, primeiro acesso e reset de senha.
- Onboarding titular e dependente.
- Assinatura local, checkout Stripe e webhook.
- Reserva, pre-check e check-in.
- Graduacao com promocao.
- PDV com abertura, venda e fechamento.
- Relatorio CSV com arquivo de controle valido e invalido.
- Fluxo LGPD e consulta de emergencia.

## 5. Observabilidade minima

- Monitorar logs de `stripe_webhook_processed` e `stripe_webhook_failed`.
- Monitorar logs de `csv_export_succeeded`, `csv_export_failed` e `csv_export_failed_unexpected`.
- Revisar periodicamente `AuditLog`, `AuthenticationEvent`, `SensitiveAccessLog` e `WebhookProcessing`.
