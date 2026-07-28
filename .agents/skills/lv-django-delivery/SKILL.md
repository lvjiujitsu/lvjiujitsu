---
name: lv-django-delivery
description: Use esta skill para implementar ou corrigir lógica Django no LV JIU JITSU, incluindo models, forms, services, selectors, views, URLs, signals, commands, pagamentos e persistência. Aplique MVT, autoria test-first, ORM controlado e testes locais proporcionais.
---

# LV Django Delivery

## Quando acionar

Em implementação ou correção de lógica Django, persistência, commands e integrações.

## Passos

1. Executar `lv-task-intake`, criar ou atualizar a PRD com `lv-prd` e ler todas as camadas.
2. Consultar Context7 e documentação oficial; em pagamentos, ler settings, serviços, views, webhooks e runbooks.
3. Criar ou ajustar primeiro o teste do comportamento, cobrindo caminho feliz, erro e edge case proporcional.
4. Implementar o mínimo com models para persistência, forms para validação, services para negócio/transações, selectors para leitura e views finas.
5. Usar `transaction.atomic`, relações carregadas, guard clauses, exceções específicas e configuração explícita.
6. Executar `.\.venv\Scripts\python.exe manage.py check`.
7. Executar o teste focado e, quando proporcional, `.\.venv\Scripts\python.exe manage.py test --verbosity 2`.
8. Fazer ORM local quando necessário, revisar N+1, diff e contratos e encerrar com `lv-cleanup-audit`.
9. Testes usam banco isolado; migrations, reset e seeds locais seguem `docs/OPERACAO-BANCO-SEEDS.md`.

## Saída

```text
Contrato test-first: <teste criado ou justificativa>.
Implementado: <camadas e arquivos>.
Validação: <comandos e resultados reais>.
ORM/migrations/seeds: <executado | não aplicável>.
Status: <concluída | concluída com limitações | não concluída>.
```

## Parar quando

- Critérios da PRD estiverem implementados e validados com saída real.
- Se o teste permanecer vermelho, parar como não concluída e registrar a causa.
- Antes de ação externa ou expansão não autorizada, parar e pedir decisão.
