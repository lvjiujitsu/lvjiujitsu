# PRD-021: Etapas de Pagamento Separadas no Wizard de Cadastro

## Resumo do que será implementado

Separar a decisão de pagamento atual (concentrada no painel Resumo) em duas etapas distintas:

1. **Pagamento da mensalidade** (`plan-payment`): o usuário escolhe como pagar o plano ou opta pela aula experimental.
2. **Pagamento dos materiais** (`materials-payment`): o usuário confirma o pagamento dos materiais em estoque ou reserva os esgotados.
3. **Resumo** (`summary`): tela final de apenas confirmação, sem decisão de pagamento.

## Tipo de demanda

Nova feature de UX / refatoração de fluxo de cadastro.

## Problema atual

A etapa "Resumo" concentra tanto a apresentação do resumo quanto a decisão de como pagar (cartão, PIX ou experiência), misturando responsabilidades. Materiais e plano não têm etapas claras de decisão de pagamento separadas.

## Objetivo

- Tornar o fluxo mais claro: cada decisão tem seu momento
- Mensalidade: o usuário pode pagar ou optar por aula experimental
- Materiais: o usuário é obrigado a pagar (se disponível) ou reservar (se esgotado)
- Resumo: apenas confirmação visual antes de concluir

---

## Context Ledger

### Arquivos lidos integralmente

- `static/system/js/auth/registration-wizard-clean.js` (3002 linhas)
- `templates/login/register.html` (876 linhas)

### Arquivos adjacentes consultados

- `system/forms/__init__.py`
- `system/models/membership.py`

### Limitações encontradas

- Nenhuma

---

## Prompt de execução

### Persona

Agente de desenvolvimento especialista em Django + JS vanilla seguindo SDD + TDD.

### Ação

Refatorar o wizard de cadastro separando a decisão de pagamento em 2 etapas explícitas.

### Contexto

O wizard usa STEP_DEFINITIONS e computeActiveSteps() para construir o fluxo dinamicamente. Os painéis são seções HTML com `data-panel`. A lógica de pagamento vive em `checkoutActionButtons` e `renderSummary()`.

### Restrições

- Sem novas migrações
- Compatibilidade com backend: o campo `checkout_action` continua sendo o mesmo
- Novo campo `materials_action` adicionado mas backend pode ignorar inicialmente

---

## Escopo

### Etapa plan-payment (nova)

- Inserida após `materials` no fluxo
- Mostra resumo do plano selecionado
- Botões de opção:
  - Método do plano (cartão ou PIX, conforme `payment_method` do plano selecionado)
  - "Fazer 1 aula experimental" (pay_later)
- Ao clicar, define `checkout_action` e avança para próxima etapa

### Etapa materials-payment (nova)

- Inserida após `plan-payment` no fluxo
- Se nenhum material selecionado: mensagem informativa, botão Avançar normal
- Se materiais em estoque: lista com aviso de que serão cobrados
- Se materiais esgotados: lista com opção de reserva (manifestar interesse)
- Avançar confirma e segue para summary

### Resumo (modificado)

- Mantém lista de itens e total
- Mostra resumo de como vai pagar (plano + materiais)
- Remove `checkout-decision` (botões de pagamento)
- Submit é feito pelo botão "Concluir cadastro"

## Fora do escopo

- Mudança no backend de processamento do checkout
- Separação de cobrança de materiais e plano em transações distintas

## Arquivos impactados

- `templates/login/register.html`
- `static/system/js/auth/registration-wizard-clean.js`

---

## Plano

- [x] 1. Criar PRD
- [ ] 2. Adicionar painéis HTML plan-payment e materials-payment
- [ ] 3. Modificar painel summary (remover checkout-decision)
- [ ] 4. Adicionar STEP_DEFINITIONS e computeActiveSteps()
- [ ] 5. Criar renderPlanPayment() e renderMaterialsPayment()
- [ ] 6. Modificar renderSummary() para mostrar como vai pagar
- [ ] 7. Ajustar listeners de checkoutActionButtons
- [ ] 8. Atualizar versão do asset

## Critérios de aceite

- [ ] Ao selecionar plano e avançar, a etapa "Pagamento da mensalidade" é exibida com as opções corretas
- [ ] Ao escolher como pagar a mensalidade, avança para "Pagamento dos materiais"
- [ ] Se não há materiais, a etapa de materiais exibe mensagem informativa e avança
- [ ] Se há materiais em estoque, exibe lista com aviso de cobrança
- [ ] Se materiais esgotados, exibe opção de reserva
- [ ] O Resumo final exibe total e forma de pagamento sem botões de decisão
- [ ] O form é submetido pelo botão "Concluir cadastro" no Resumo
- [ ] checkout_action é definido corretamente conforme escolha do usuário
