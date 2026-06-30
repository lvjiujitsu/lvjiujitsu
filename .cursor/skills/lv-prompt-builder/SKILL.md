---
name: lv-prompt-builder
description: "Use esta skill quando o usuário trouxer um problema cru e pedir o melhor prompt de execução para o Claude no LV JIU JITSU. Classifica a demanda, lê os contratos pertinentes e gera um execution prompt auto-suficiente no padrão LV, com skills na ordem, arquivos a ler e gates de PRD/UI/teste/pagamento consolidados. Não implementa: entrega o prompt e para."
argument-hint: <problema a resolver>
disable-model-invocation: true
---

# LV Prompt Builder

Transforma um problema cru no melhor prompt de execução para o Claude operar o LV JIU JITSU com o mínimo de pausas. O produto é o prompt. Não cria PRD nem altera código.

## Receber

1. Trate a entrada como problema a diagnosticar, não como ordem de implementação.
2. GUARD: se o problema vier vazio, genérico ou ambíguo a ponto de não nomear o fluxo, faça UMA pergunta objetiva (tela/rota/erro/objetivo + arquivo) e pare.
3. Não edite arquivos nesta skill.
4. Leia `AGENTS.md`, `CLAUDE.md` e os contratos pertinentes: `docs/AGENT-WORKFLOW.md`, `docs/PRD-STANDARD.md`, `docs/PLATFORM-ADAPTERS.md` e, conforme o caso, `docs/UI-SCREEN-CONTRACT.md`, `docs/OPERACAO-BANCO-SEEDS.md`.

## Classificar

1. Uma categoria de `docs/AGENT-WORKFLOW.md` §2.
2. Precisa de PRD? (nº livre em `docs/prd/`).
3. Tem UI? (gate de design).
4. Tem comportamento testável? (models, forms, services, selectors, views, signals, commands).
5. Toca pagamento/webhook (Asaas/Stripe)? (área sensível).
6. Skills na ordem: `lv-task-intake`; `lv-prd` (se PRD); `lv-ui-delivery` (se UI); `lv-django-delivery` (se Django); `lv-cleanup-audit` ao final.
7. Arquivos a ler integralmente + contratos adjacentes, por camada.

## Decidir gates

Consolidar numa confirmação inicial: implementação do escopo; testes locais proporcionais; execução local de ORM, migrations, reset e seeds quando necessários; aprovação de design se a solicitação não autorizar implementação.

Manter explícitos (pedir antes): cobrança/webhook real Asaas/Stripe, HG, produção, push e deploy.

## Gerar o prompt

Bloco único no formato Execution prompt de `docs/PRD-STANDARD.md`: Persona; Action; Context (arquivos + contratos + pesquisa); Constraints; Acceptance criteria; Test policy; Required skills (`lv-*`); Authorizations + gates; Expected evidence; Output format; Gate único.

## Parar

Entregar o prompt e parar. Listar os gates externos/remotos que ainda exigirão confirmação. Não implementar.

## Restringir

Não inventar arquivo, rota, skill, comando ou fonte. Não declarar validação não feita. Não expandir além do problema. Código em inglês; UI e comunicação em pt-BR.
