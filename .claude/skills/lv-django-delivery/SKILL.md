---
name: lv-django-delivery
description: Use esta skill para implementar ou corrigir lógica Django no LV JIU JITSU, incluindo models, forms, services, selectors, views, URLs, signals, commands, pagamentos e persistência. Aplique MVT, autoria test-first, ORM controlado e testes somente sob autorização.
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
3. Não executar sem autorização.
4. Registrar “teste escrito, não executado por política”.

## Implementar

- Models: invariantes simples.
- Forms: validação server-side.
- Services: regra e múltiplas escritas com `transaction.atomic`.
- Selectors: leitura reutilizável e relações carregadas.
- Views: HTTP fino.
- Templates/JS: apresentação.

Usar guard clauses, exceções específicas e configuração explícita. Não adicionar comentários ou docstrings por padrão.

## Validar

Sem autorização de testes:

- executar `manage.py check` quando proporcional;
- fazer ORM read-only quando necessário;
- revisar N+1, diff e contratos;
- perguntar pela execução do teste focado.

Não executar suíte completa por inferência.

## Banco

- Testes usam banco isolado.
- Não apagar `db.sqlite3` para testar.
- Não criar ou aplicar migrations.
- Não executar reset ou seeds.
- Parar se exigir schema ou mutação não autorizada.

## Encerrar

Atualizar a PRD e executar `lv-cleanup-audit`.
