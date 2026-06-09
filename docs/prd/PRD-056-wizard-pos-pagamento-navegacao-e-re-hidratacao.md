# PRD-056: Wizard pós-pagamento — bloqueio de navegação retroativa e re-hidratação de turmas

## Resumo do que será implementado

Dois bugs no wizard de cadastro público (`/register/`) confirmados após validação no ambiente HG:

1. **Bug de navegação**: após o pagamento da mensalidade, o botão "Voltar" permanece ativo e permite que o usuário retorne ao step de seleção de turma, onde a turma aparece desmarcada.
2. **Bug de re-hidratação**: quando o `sessionStorage` é limpo (o que ocorre ao entrar em `showPlanPaidMode`), o `state.classSelections` não é restaurado a partir dos dados iniciais do formulário Django, causando a exibição visual de "turma desmarcada" e bloqueando a navegação se o usuário conseguir chegar ao step de classes.

## Tipo de demanda

Correção de bug (dois bugs relacionados ao estado pós-pagamento do wizard)

## Problema atual

### Bug 1 — Botão Voltar ativo pós-pagamento

Em `showPlanPaidMode()` (register.js ~linha 2842):
```javascript
if (back) {
  back.style.visibility = 'visible';  // botão visível
  if (backLabel) backLabel.textContent = 'Voltar';
  back.onclick = null;                // sem override — listener addEventListener ainda ativo
}
```

Com `back.onclick = null`, o listener registrado por `addEventListener` (linha ~2043) continua ativo. Esse listener navega para o step anterior da sequência. Como `state.stepIndex` aponta para `step-plan` (não para 0), a navegação ocorre e o usuário retorna ao step de turmas.

### Bug 2 — state.classSelections não restaurado

Quando `regPostPlan = true`, o init chama:
```javascript
clearWizardState();   // remove lv-wiz-v1 do sessionStorage
showPlanPaidMode();
```

Se o usuário consegue chegar ao step de classes (via Bug 1), `tryRestoreWizard()` não encontra nada no sessionStorage. O fallback de init (linha ~2992) restaura apenas perfil e contagem de dependentes — nunca restaura `state.classSelections` a partir dos `<input name="holder_class_groups">` que o Django renderizou via `initial`.

## Objetivo

- Impedir que o usuário retorne a steps anteriores após o pagamento da mensalidade ser confirmado
- Garantir que, quando o init carregar sem sessionStorage, o `state.classSelections` seja populado com os dados de turma já presentes nos hidden inputs do formulário Django

## Context Ledger

### Arquivos lidos integralmente
- `static/system/js/auth/register.js` (completo — v30)
- `system/views/auth_views.py` (completo)
- `system/models/pre_registration.py`

### Arquivos adjacentes consultados
- `templates/login/register.html` (versões de assets)
- `system/models/plan.py`

### Banco HG inspecionado
```
PreRegistration #2
  status: payment_confirmed
  holder_class_groups: ['1::Jiu Jitsu']
  plan_paid: True
```
Os dados estão corretos no banco — os bugs são exclusivamente de estado JS no frontend.

### Limitações encontradas
- Nenhuma

## Escopo

- `static/system/js/auth/register.js` — duas correções de comportamento
- `templates/login/register.html` — bump de versão `?v=30` → `?v=31`

## Fora do escopo

- Restauração de `student_class_groups` / `guardian` (não há caso de teste validado; pode ser feito em PRD separado se reproduzido)
- Qualquer alteração de backend, models ou migrations

## Regras e restrições

- sem migrations
- sem hardcode
- sem criação de arquivos em pastas novas
- leitura integral feita antes da implementação

## Plano

- [x] 1. Leitura integral dos arquivos relevantes
- [ ] 2. Implementar Fix 1: esconder botão Voltar em `showPlanPaidMode()`
- [ ] 3. Implementar Fix 2: restaurar `state.classSelections` no init fallback
- [ ] 4. Bump de versão no template (`?v=31`)
- [ ] 5. `manage.py check`
- [ ] 6. `collectstatic --noinput`
- [ ] 7. Validação visual no Chrome (HG após redeploy)
- [ ] 8. Atualização documental

## Critérios de aceite

- [ ] Após pagamento da mensalidade, o botão "Voltar" está oculto — o usuário só pode avançar para materiais ou recomeçar o cadastro
- [ ] Ao recarregar `/register/` sem sessionStorage mas com pre-registration em sessão, a turma selecionada anteriormente aparece marcada no step de classes
- [ ] O fluxo completo (materiais → resumo → finalizar) funciona normalmente após o pagamento

## Evidências esperadas

- Console do Chrome sem erros JS
- Snapshot do banco com `holder_class_groups` populado
- Step de turmas exibe a turma selecionada quando re-hidratado

## Implementado

*(preencher após implementação)*

## Desvios do plano

*(preencher se houver)*

## Pendências

*(preencher se houver)*
