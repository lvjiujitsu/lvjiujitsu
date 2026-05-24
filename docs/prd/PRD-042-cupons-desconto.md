# PRD-042: Cupons de Desconto

## Resumo do que será implementado

Criar um sistema de cupons de desconto aplicáveis ao pagamento de mensalidade no wizard de cadastro público. Um cupom pode conceder desconto percentual (%) ou desconto de valor fixo (R$) sobre o total do plano. A aplicação ocorre antes da criação do pagamento no gateway (Asaas ou Stripe). O banco registra o cupom aplicado na pre-registration. Seeds carregam cupons iniciais via JSON.

---

## Tipo de demanda

Nova feature — modelo + serviço + UI + seed

---

## Problema atual

Não existe mecanismo de desconto no sistema. Promoções, testes e negociações exigem alteração manual no preço do plano ou isenção operacional fora do sistema. Não há rastreabilidade de descontos concedidos.

---

## Objetivo

Permitir que o usuário informe um código de cupom no step-plan do wizard antes de pagar. O sistema valida o cupom, calcula o valor final com desconto e encaminha esse valor ao gateway. O cupom é registrado na pre-registration para auditoria. Seeds criam cupons iniciais pré-carregados.

---

## Context Ledger

### Arquivos lidos integralmente (obrigatório antes de implementar)

- `system/models/plan.py` — `SubscriptionPlan`, cálculo de preço
- `system/models/pre_registration.py` — `PreRegistration.form_snapshot`
- `system/views/auth_views.py` — `PortalRegisterView._create_pre_registration_plan_payment`, `_parse_selected_plan_payload`
- `system/services/asaas_client.py` — `create_pix_payment`, `create_credit_card_payment`
- `system/views/payment_views.py` — `PaymentSuccessView`
- `static/system/js/auth/register.js` — fluxo do step-plan, submit do form
- `templates/login/register.html` — estrutura do wizard step-plan
- `system/constants.py` — `CheckoutAction`
- `static/initial_data/seed_system_initial_subscription_plans_values.json` — referência de estrutura JSON

### Arquivos adjacentes consultados

- `system/models/__init__.py` — registro de modelos
- `system/urls.py` — rotas
- `system/tests/` — padrão de testes existente
- `lvjiujitsu/settings.py` — sem mudanças esperadas

### Internet / documentação oficial

- Django JSONField queries: https://docs.djangoproject.com/en/4.1/topics/db/queries/#querying-jsonfield
- Django `CheckConstraint`: https://docs.djangoproject.com/en/4.1/ref/models/constraints/

### MCPs / ferramentas verificadas

- `manage.py check` — obrigatório após ciclo destrutivo
- Ciclo destrutivo — obrigatório (novo modelo `Coupon`)

---

## Prompt de execução

### Persona

Agente de desenvolvimento especialista em Django 4.x seguindo SDD + TDD + arquitetura MVT com services. Atenção especial a validação de entrada e integridade de dados.

### Ação

Implementar sistema completo de cupons: modelo, serviço de validação/aplicação, endpoint de verificação AJAX, UI no wizard, seed de cupons iniciais e testes.

### Contexto

O wizard de cadastro permite ao usuário selecionar um plano e pagar. O valor cobrado é `SubscriptionPlan.price`. O cupom deve ser aplicado sobre esse valor antes de criar o pagamento no gateway. O cupom é informado pelo usuário no step-plan, validado via AJAX antes do submit, e o valor com desconto é enviado ao gateway.

A pre-registration já tem `form_snapshot` (JSON) — registrar o cupom aplicado ali para auditoria.

### Restrições

- sem hardcode de códigos de cupom
- sem migrações manuais — ciclo destrutivo executado pelo usuário
- cupom inválido ou expirado → erro exibido no wizard sem redirecionar
- seed não aceita argumentos `--`; toda configuração via `.env`
- idempotente: rodar a seed duas vezes não duplica cupons

---

## Escopo

### Modelo: `Coupon`

**Arquivo:** `system/models/coupon.py`

```python
class DiscountType(models.TextChoices):
    PERCENT = "percent", "Percentual (%)"
    FIXED   = "fixed",   "Valor fixo (R$)"

class Coupon(TimeStampedModel):
    code            = models.CharField("Código", max_length=40, unique=True, db_index=True)
    discount_type   = models.CharField("Tipo de desconto", max_length=10, choices=DiscountType.choices)
    discount_value  = models.DecimalField("Valor do desconto", max_digits=10, decimal_places=2,
                                          validators=[MinValueValidator(Decimal("0.01"))])
    max_uses        = models.PositiveIntegerField("Usos máximos", null=True, blank=True,
                                                  help_text="Nulo = ilimitado")
    uses_count      = models.PositiveIntegerField("Usos realizados", default=0)
    valid_from      = models.DateField("Válido a partir de", null=True, blank=True)
    valid_until     = models.DateField("Válido até", null=True, blank=True)
    is_active       = models.BooleanField("Ativo", default=True)
    description     = models.CharField("Descrição interna", max_length=200, blank=True)

    class Meta:
        verbose_name = "Cupom de desconto"
        verbose_name_plural = "Cupons de desconto"
        constraints = [
            CheckConstraint(
                check=Q(discount_type='fixed') | Q(discount_value__lte=100),
                name="coupon_percent_max_100",
            )
        ]
```

> Não criar campo de relacionamento entre `Coupon` e `PreRegistration` — registrar apenas o código e o desconto calculado no `form_snapshot` da pre-registration.

### Serviço: `system/services/coupon.py`

```python
def validate_coupon(code: str, total: Decimal) -> dict:
    """
    Valida o cupom e retorna o desconto calculado.
    Levanta ValueError com mensagem pt-BR em caso de erro.
    Retorna: {'coupon_id': int, 'code': str, 'discount_type': str,
              'discount_value': Decimal, 'discount_amount': Decimal, 'final_total': Decimal}
    """

def apply_coupon(coupon_id: int) -> None:
    """Incrementa uses_count atomicamente."""
```

Regras de validação (em `validate_coupon`):
1. Cupom não existe → `ValueError("Cupom inválido.")`
2. `is_active=False` → `ValueError("Cupom inativo.")`
3. `valid_from` no futuro → `ValueError("Cupom ainda não é válido.")`
4. `valid_until` no passado → `ValueError("Cupom expirado.")`
5. `max_uses` atingido → `ValueError("Cupom esgotado.")`
6. Desconto percentual: `discount_amount = total * (discount_value / 100)`
7. Desconto fixo: `discount_amount = min(discount_value, total)` — nunca negativo
8. `final_total = max(total - discount_amount, Decimal("0.01"))` — mínimo de R$ 0,01

### Endpoint de validação AJAX

```
GET /cadastro/validar-cupom/?code=XXXXX&total=230.38
```

**View:** `ValidateCouponView`

Resposta de sucesso:
```json
{
  "valid": true,
  "discount_type": "percent",
  "discount_value": "10.00",
  "discount_amount": "23.04",
  "final_total": "207.34",
  "message": "Cupom aplicado: 10% de desconto"
}
```

Resposta de erro:
```json
{"valid": false, "error": "Cupom expirado."}
```

### Integração no form/view

Em `PortalRegistrationForm`:
- Adicionar campo `coupon_code = CharField(max_length=40, required=False)`

Em `PortalRegisterView._build_form_snapshot`:
- `coupon_code` já é capturado pelo loop de POST fields

Em `PortalRegisterView._create_pre_registration_plan_payment`:
```python
coupon_code = snapshot.get("coupon_code", "").strip().upper()
coupon_data = None
if coupon_code:
    coupon_data = validate_coupon(coupon_code, total)
    total = coupon_data["final_total"]

# ... criar pagamento com total já descontado ...

if coupon_data:
    apply_coupon(coupon_data["coupon_id"])
    snapshot["applied_coupon"] = {
        "code": coupon_data["code"],
        "discount_type": coupon_data["discount_type"],
        "discount_value": str(coupon_data["discount_value"]),
        "discount_amount": str(coupon_data["discount_amount"]),
        "final_total": str(coupon_data["final_total"]),
    }
```

### UI no wizard (register.js + template)

No `step-plan` do template:
```html
<div class="form-field coupon-field" id="coupon-field-area">
  <label class="form-label" for="ui-coupon-code">Cupom de desconto <span class="form-label-optional">(opcional)</span></label>
  <div class="coupon-input-row">
    <input type="text" class="form-input" id="ui-coupon-code" placeholder="CÓDIGO DO CUPOM" maxlength="40" autocomplete="off" style="text-transform:uppercase">
    <button type="button" class="btn-coupon-apply" id="btn-apply-coupon">Aplicar</button>
  </div>
  <p class="form-field__error" id="coupon-error" hidden></p>
  <p class="coupon-success" id="coupon-success" hidden></p>
</div>
```

No `register.js` — novo bloco de cupom:
- Ao clicar "Aplicar": chama `/cadastro/validar-cupom/?code=X&total=Y` via `fetch`
- Sucesso: exibe mensagem verde, preenche `id_coupon_code`, atualiza valor exibido no card do plano selecionado
- Erro: exibe mensagem vermelha
- Ao trocar de plano: limpa o cupom aplicado e reseta o campo

Em `elStepPlanNext.addEventListener`:
```javascript
setHidden('id_coupon_code', document.getElementById('ui-coupon-code').value.trim().toUpperCase());
```

### Campo oculto no form do template

```html
<input type="hidden" name="coupon_code" id="id_coupon_code" value="">
```

### Seed

**Comando:** `seed_system_initial_coupons`

- Lê `static/initial_data/seed_system_initial_coupons.json`
- Depende de: nenhuma
- Idempotente: `get_or_create` por `code`
- Audit log por cupom criado/já existente

**Arquivo:** `static/initial_data/seed_system_initial_coupons.json`

```json
[
  {
    "code": "BEMVINDO10",
    "discount_type": "percent",
    "discount_value": "10.00",
    "max_uses": null,
    "valid_from": null,
    "valid_until": null,
    "is_active": true,
    "description": "Desconto de boas-vindas — 10% na mensalidade"
  },
  {
    "code": "PROMO50",
    "discount_type": "fixed",
    "discount_value": "50.00",
    "max_uses": 100,
    "valid_from": null,
    "valid_until": null,
    "is_active": true,
    "description": "Promoção fixa de R$ 50 de desconto"
  },
  {
    "code": "FAMILIA20",
    "discount_type": "percent",
    "discount_value": "20.00",
    "max_uses": null,
    "valid_from": null,
    "valid_until": null,
    "is_active": true,
    "description": "Desconto para planos família — 20%"
  },
  {
    "code": "TESTE100",
    "discount_type": "fixed",
    "discount_value": "999.00",
    "max_uses": 5,
    "valid_from": null,
    "valid_until": null,
    "is_active": true,
    "description": "Cupom de teste — cobre valor total do plano"
  }
]
```

---

## Fora do escopo

- Cupons aplicáveis a materiais (apenas mensalidade neste PRD)
- Cupons de uso único por CPF
- Interface administrativa de criação de cupons em tempo real (usar Django admin)
- Integração com cupons nativos do Stripe ou Asaas
- Cupons aplicados no fluxo de troca de plano (PRD futuro)

---

## Arquivos impactados

| Arquivo | Tipo de mudança |
|---|---|
| `system/models/coupon.py` | **novo** — modelo `Coupon` |
| `system/models/__init__.py` | exportar `Coupon`, `DiscountType` |
| `system/services/coupon.py` | **novo** — `validate_coupon`, `apply_coupon` |
| `system/views/auth_views.py` | integrar `validate_coupon` + `apply_coupon` em `_create_pre_registration_plan_payment` |
| `system/views/coupon_views.py` | **novo** — `ValidateCouponView` |
| `system/forms/__init__.py` | adicionar `coupon_code` ao `PortalRegistrationForm` (ou form separado) |
| `system/urls.py` | rota `/cadastro/validar-cupom/` |
| `templates/login/register.html` | campo de cupom no step-plan + hidden input |
| `static/system/js/auth/register.js` | lógica de aplicação de cupom via fetch |
| `system/management/commands/seed_system_initial_coupons.py` | **novo** |
| `static/initial_data/seed_system_initial_coupons.json` | **novo** |
| `system/tests/test_coupon_service.py` | **novo** |
| `system/tests/test_coupon_views.py` | **novo** |
| `CLAUDE.md` | atualizar tabela de seeds |

---

## Riscos e edge cases

| Risco | Mitigação |
|---|---|
| Race condition: dois usuários aplicam o mesmo cupom limitado simultâneamente | `apply_coupon` usa `F()` com `select_for_update` ou validação após incremento |
| Cupom aplicado mas pagamento falha → cupom consumido sem pagamento | `apply_coupon` só é chamado após confirmação do pagamento (ou usar transação atômica com rollback) |
| Usuário altera o `total` no DOM e envia valor menor | serviço recalcula sempre a partir do `SubscriptionPlan.price` no backend — nunca confia no total enviado pelo cliente |
| Cupom com desconto maior que o total | `final_total = max(total - discount, Decimal("0.01"))` — nunca zero para evitar rejeição pelo gateway |
| Código de cupom em caixa mista | normalizar para `upper()` antes de comparar |

---

## Regras e restrições

- SDD antes de código
- TDD para implementação
- sem hardcode
- sem `except: pass`
- sem migrações manuais — instruir ciclo destrutivo
- leitura integral obrigatória
- validação visual obrigatória (aplicar cupom no wizard, confirmar desconto exibido)

---

## Plano

- [ ] 1. Ler integralmente todos os arquivos listados no Context Ledger
- [ ] 2. Criar `system/models/coupon.py` e registrar em `__init__.py`
- [ ] 3. Solicitar ciclo destrutivo ao usuário (novo modelo)
- [ ] 4. Criar `system/services/coupon.py` (`validate_coupon`, `apply_coupon`)
- [ ] 5. Escrever testes do serviço — Red
- [ ] 6. Implementar serviço — Green
- [ ] 7. Refatorar
- [ ] 8. Criar `ValidateCouponView` e rota
- [ ] 9. Escrever testes da view
- [ ] 10. Adicionar campo `coupon_code` ao form
- [ ] 11. Integrar `validate_coupon` + `apply_coupon` em `_create_pre_registration_plan_payment`
- [ ] 12. Adicionar campo hidden no template + campo UI no step-plan
- [ ] 13. Implementar JS: fetch de validação, exibição de desconto, limpeza ao trocar plano
- [ ] 14. Criar JSON de dados dos cupons iniciais
- [ ] 15. Criar comando `seed_system_initial_coupons`
- [ ] 16. Validar fluxo completo no navegador
- [ ] 17. Limpeza final
- [ ] 18. Atualizar CLAUDE.md

---

## Validação visual

### Desktop

- step-plan exibe campo de cupom abaixo dos cards de plano
- digitar código inválido e clicar Aplicar → mensagem de erro vermelha inline
- digitar código válido → mensagem verde com valor do desconto e novo total exibido
- trocar plano → cupom limpo e campo resetado
- clicar "Pagar mensalidade" com cupom aplicado → gateway recebe valor com desconto

### Mobile

- campo de cupom visível e usável em tela pequena

### Console do navegador

- sem erros JS na validação de cupom via fetch

### Terminal

- sem stack trace no endpoint de validação
- sem stack trace na criação do pagamento com desconto

---

## Validação ORM

```python
from system.models import Coupon
Coupon.objects.filter(is_active=True).count()
# retorna 4 (ou o número de cupons do JSON)

from system.models import PreRegistration
pr = PreRegistration.objects.latest('created_at')
pr.form_snapshot.get('applied_coupon')
# retorna {'code': 'BEMVINDO10', 'discount_type': 'percent', ...}

from system.models import Coupon
Coupon.objects.get(code='BEMVINDO10').uses_count
# deve ter incrementado após pagamento confirmado
```

---

## Validação de qualidade

- `validate_coupon` nunca retorna `None` silencioso — levanta `ValueError` explícito
- `apply_coupon` usa operação atômica
- Total enviado ao gateway calculado no backend — nunca confia em campo do POST
- Sem CSS/JS inline desnecessário

---

## Evidências (preencher após implementação)

- [ ] `manage.py check` — 0 issues
- [ ] `manage.py test --verbosity 2` — 0 falhas
- [ ] `Coupon.objects.all().count()` == 4 após seed
- [ ] Cupom válido aplicado no wizard — desconto exibido
- [ ] Cupom inválido → mensagem de erro
- [ ] Pagamento criado no Asaas com valor descontado
- [ ] `PreRegistration.form_snapshot['applied_coupon']` preenchido
- [ ] `Coupon.uses_count` incrementado após pagamento confirmado

## Implementado

_(preencher após conclusão)_

## Desvios do plano

_(preencher após conclusão)_

## Pendências

_(preencher após conclusão)_
