---
name: lv-django-delivery
description: Use esta skill para implementar ou corrigir lógica Django no LV JIU JITSU, incluindo models, forms, services, selectors, views, URLs, signals, commands, pagamentos e persistência. Aplique MVT, autoria test-first, ORM controlado e testes locais proporcionais.
---

# LV Django Delivery

## Contextualizar

1. Executar `lv-task-intake`.
2. Criar ou atualizar a PRD com `lv-prd`.
3. Ler integralmente todas as camadas.
4. Consultar Django e SDKs atuais no Context7 e documentação oficial.
5. Para Asaas/Stripe, ler serviços, views, webhooks, settings e documentos operacionais.

## Escrever primeiro o contrato

1. Criar ou ajustar o teste do comportamento.
2. Cobrir fluxo feliz, erro e edge case proporcional.
3. Executar testes locais proporcionais ao risco do escopo.
4. Registrar comando e resultado.

## Implementar

- Models: invariantes simples.
- Forms: validação server-side.
- Services: regra e múltiplas escritas com `transaction.atomic`.
- Selectors: leitura reutilizável e relações carregadas.
- Views: HTTP fino.
- Templates/JS: apresentação.

Usar guard clauses, exceções específicas e configuração explícita. Não adicionar comentários ou docstrings por padrão.

## Validar

Validação local:

- executar `manage.py check` quando proporcional;
- executar teste focado e/ou suíte proporcional ao risco;
- fazer ORM local quando necessário;
- revisar N+1, diff e contratos.

## Banco

- Testes usam banco isolado.
- Não apagar `db.sqlite3` apenas para testar.
- Criar/aplicar migrations locais, reset local e seeds locais quando necessários ao objetivo solicitado.
- Parar antes de escrita em HG, produção ou integração externa sem confirmação explícita do ambiente.

## Encerrar

Atualizar a PRD e executar `lv-cleanup-audit`.
