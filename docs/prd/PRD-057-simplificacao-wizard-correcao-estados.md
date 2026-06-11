# PRD-057: Simplificação do wizard — correção de estados e remoção de código de desenvolvimento

## Resumo do que será implementado

Correção do bug que exibe múltiplos steps simultaneamente no wizard de cadastro, remoção do código de desenvolvimento adicionado no commit `00c39f8` (DevLoadPreRegistrationView + command + autofill JS), e revisão do mecanismo "Recomeçar cadastro".

## Tipo de demanda

Correção pontual + limpeza de código

## Problema atual

### Bug visual crítico (screenshot do usuário)

`step-profile` e `step-plan` são exibidos simultaneamente após retorno do Asaas com `post_plan_payment_complete=True`.

**Causa raiz:**
- `step-profile` não tem atributo `hidden` no template — é visível por padrão
- `showPlanPaidMode()` oculta apenas steps presentes em `state.stepSequence`
- `state.stepSequence` é vazio quando o perfil não foi restaurado (ex: PreRegistration deletado após reset de banco)
- Resultado: `forEach` sobre array vazio → nenhum step oculto → `step-profile` permanece visível junto com `step-plan`

**Mesmo bug existe em:**
- `showPostPaymentMode()` — handler do botão Voltar no `step-plan-confirmed`

### Código dev que aumenta complexidade sem valor

Adicionado no commit `00c39f8`:
- `DevLoadPreRegistrationView` em `system/views/auth_views.py`
- Rota `/dev/carregar-pre-cadastro/<id>/` em `system/urls.py`
- `system/management/commands/dev_create_test_pre_registration.py`
- `static/system/js/auth/register_test_autofill.js`

### `/register/recomecar/` retorna 400 em produção (HG)

Causa exata não identificável sem logs de servidor. O endpoint é simples (`session.pop` + redirect), mas retorna 400. A mudança para `session.flush()` é mais robusta semanticamente.

## Objetivo

1. Corrigir o bug de steps sobrepostos com 1 linha de mudança por ocorrência
2. Remover código de desenvolvimento adicionado em `00c39f8`
3. Tornar `ResetRegistrationView` mais robusto com `session.flush()`
4. Validar localmente antes de qualquer deploy

## Fluxo de cadastro — contrato imutável

```
Criar conta → Etapas de dados (perfil, pessoal, dependentes, saúde, artes marciais, turmas)
→ Pagamento do plano (Asaas — dados persistidos em PreRegistration)
→ Retorno com pagamento confirmado
→ Materiais (pagar ou pular)
→ Resumo
→ Finalizar (grava Person, PortalAccount, etc.)
```

Regras:
- Pode voltar a qualquer momento, dados preservados na sessão/PreRegistration
- `Person` nunca criado antes do POST de finalização
- Nenhum passo pode pular Resumo

## Context Ledger

### Arquivos lidos integralmente
- `static/system/js/auth/register.js` (3049 linhas, v33)
- `templates/login/register.html`
- `system/views/auth_views.py` (ResetRegistrationView, DevLoadPreRegistrationView, PortalRegisterView)
- `system/urls.py`
- `lvjiujitsu/settings.py`
- `system/middleware.py`

### Causa raiz confirmada

```javascript
// showPlanPaidMode() linha 2751-2753 — BUG
state.stepSequence.forEach(function (sid) {
  var el = document.getElementById(sid);
  if (el) el.hidden = true;  // não executa quando stepSequence está vazio
});

// showPostPaymentMode() linha 2158-2160 — mesmo bug
state.stepSequence.forEach(function (sid) {
  var sel = document.getElementById(sid);
  if (sel) sel.hidden = true;
});
```

### Template — `step-profile` é visível por padrão

```html
<section class="wizard-step" id="step-profile" data-step="1">
  <!-- SEM atributo hidden — visível quando a página carrega -->
```

Todos os outros steps dentro de `wizard-form` têm `hidden`.

## Escopo

- `static/system/js/auth/register.js` — 2 correções de `querySelectorAll`
- `system/views/auth_views.py` — remover `DevLoadPreRegistrationView`, mudar `ResetRegistrationView`
- `system/urls.py` — remover rota dev
- `system/management/commands/dev_create_test_pre_registration.py` — deletar
- `static/system/js/auth/register_test_autofill.js` — deletar
- `templates/login/register.html` — bump `?v=34`

## Fora do escopo

- Refatoração do wizard JS (escopo maior, PRD separado)
- Mudanças no modelo `PreRegistration`
- Redesign visual

## Plano

- [x] 1. Diagnóstico e leitura integral
- [ ] 2. Correção do bug em `showPlanPaidMode()`
- [ ] 3. Correção do bug em `showPostPaymentMode()` back handler
- [ ] 4. Remoção do código dev
- [ ] 5. Robustez em `ResetRegistrationView` com `session.flush()`
- [ ] 6. Bump `?v=34` no template
- [ ] 7. Validação local: `manage.py check`, `manage.py test`, servidor + navegador
- [ ] 8. Evidências

## Critérios de aceite

- [ ] Ao retornar do Asaas com `post_plan_payment_complete=True`, apenas `step-plan` (modo pago) deve ser visível — nenhum outro step (verificável: Chrome MCP em `/register/` com sessão pós-pagamento)
- [ ] "Recomeçar cadastro" limpa a sessão e retorna para `/register/` fresco sem erro 400 (verificável: Chrome MCP, console sem erros)
- [ ] Navegação Back em `step-plan-confirmed` mostra apenas `step-plan`, sem `step-profile` visível (verificável: Chrome MCP)
- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 falhas
- [ ] Rota `/dev/carregar-pre-cadastro/` retorna 404 em DEBUG e não existe em produção (removida)
- [ ] `register_test_autofill.js` não existe mais no repositório

## Regras e restrições

- Sem migrações
- Sem hardcode
- Sem mascaramento de erro
- Leitura integral obrigatória ✓
- Validação local obrigatória antes de deploy HG

## Evidências

(a preencher após implementação)

## Desvios do plano

(a preencher)
