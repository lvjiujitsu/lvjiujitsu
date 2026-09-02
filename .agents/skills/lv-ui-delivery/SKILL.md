---
name: lv-ui-delivery
description: Use esta skill em qualquer alteração de template, CSS, JavaScript, tela, componente, modal, wizard ou fluxo visual do LV JIU JITSU. Exija proposta de design aprovada antes do código e valide no navegador interno com evidência desktop/mobile.
---

# LV UI Delivery

## Quando acionar

Em qualquer alteração de template, CSS, JavaScript, tela, componente, modal, wizard ou fluxo visual.

## Passos

1. Executar `lv-task-intake` e ler PRD, `obsidian/projetos/lvjiujitsu/contrato-ui-lvjiujitsu.md` e o contrato do fluxo.
2. Ler integralmente view, form, service, selector, URL, template, CSS, JS e testes.
3. Consultar Context7 e documentação oficial quando aplicável.
4. Antes do código, apresentar objetivo, preservação funcional, hierarquia, wireframe, estados, erros, permissões, desktop, mobile e temas.
5. Aplicar o gate do `AGENTS.md`: pedir aprovação apenas quando a solicitação atual não autorizar o escopo.
6. Escrever e executar o teste aplicável, implementar a menor mudança e manter negócio fora de template/JS.
7. Usar tokens, acessibilidade e assets separados, atualizar `?v=` quando necessário e nunca editar `staticfiles/`.
8. Abrir a rota real em `http://localhost:8000`, validar caminho feliz, edge case, desktop, mobile, temas, permissões, console e terminal.
9. Registrar screenshot ou snapshot, resultados e limitações e encerrar com `lv-cleanup-audit`.

## Saída

```text
Proposta: <hierarquia, wireframe e estados>.
Gate: <autorizado pelo prompt | aprovação obtida>.
Validação visual: <rota, desktop/mobile, temas e evidência>.
Console/terminal: <resultado>.
Status: <concluída | concluída com limitações | não concluída>.
```

## Parar quando

- A rota real estiver validada com evidência visual e sem regressão conhecida.
- Se o browser estiver indisponível ou não houver screenshot, parar como concluída com limitações ou não concluída.
- Antes de gateway externo ou expansão não autorizada, parar e pedir decisão.
