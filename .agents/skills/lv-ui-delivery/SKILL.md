---
name: lv-ui-delivery
description: Use esta skill em qualquer alteração de template, CSS, JavaScript, tela, componente, modal, wizard ou fluxo visual do LV JIU JITSU. Exija proposta de design aprovada antes do código e valide no navegador interno com evidência desktop/mobile.
---

# LV UI Delivery

## Contextualizar

1. Executar `lv-task-intake`.
2. Ler a PRD, `docs/UI-SCREEN-CONTRACT.md` e o contrato específico do fluxo.
3. Ler integralmente view, form, service, selector, URL, template, CSS, JS e testes.
4. Consultar Context7 e documentação oficial quando aplicável.

## Aprovar design

Antes de editar:

1. definir objetivo e preservação funcional;
2. apresentar hierarquia visual;
3. apresentar wireframe;
4. mapear estados, erros, disabled, loading e permissões;
5. explicar desktop, mobile e temas;
6. pedir aprovação.

Usar Plan mode, Figma, mockup ou recurso disponível. Não inventar “Claude Design”.

## Implementar

1. Escrever e executar o teste funcional ou contrato automatizado aplicável quando proporcional.
2. Implementar a menor mudança correta.
3. Manter regra de negócio fora de template e JS.
4. Usar tokens, acessibilidade e assets separados.
5. Atualizar `?v=` quando necessário.
6. Não editar `staticfiles/`.

## Validar no browser

Imediatamente após implementar:

1. abrir a rota real em `localhost:8000`;
2. validar caminho feliz e edge case;
3. validar desktop, mobile, tema claro e escuro;
4. inspecionar console e terminal;
5. verificar permissões e estados;
6. registrar screenshot ou snapshot.

Pagamento Asaas/Stripe segue o guia operacional. Gateway externo, túnel, webhook e retorno não podem ser simulados como sucesso sem evidência.

## Encerrar

- Registrar os testes executados e seus resultados.
- Registrar limitações reais.
- Executar `lv-cleanup-audit`.
