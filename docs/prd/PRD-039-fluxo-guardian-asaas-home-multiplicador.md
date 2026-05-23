# PRD-039: Padronizar fluxo de cadastro — guardian, Asaas, home, multiplicador de plano

## Resumo do que será implementado

Correções em seis frentes independentes mas relacionadas ao fluxo de cadastro público:

1. **Guardian health/martial** — responsável também passa pelas etapas de saúde e histórico esportivo (igual ao titular)
2. **Asaas city** — campo `city` incluído no `create_customer()` para pré-preencher o pagamento
3. **Multiplicador de plano** — para perfil guardian com N alunos, o plano é cobrado N vezes
4. **UX pós-pagamento** — ao voltar do Asaas, exibe tela de confirmação idêntica à de checkout, com botão "Continuar"; mesmo padrão para materiais
5. **Resumo final** — `step-review` exibe responsável → cada aluno com turma e valor pago
6. **Home vazia** — templates mínimos para as rotas de home já existentes

## Tipo de demanda

Correção de bugs + feature gap

## Arquivos impactados

- `system/forms/registration_forms.py`
- `system/services/registration.py`
- `system/services/registration_checkout.py`
- `system/services/asaas_client.py`
- `system/services/asaas_checkout.py`
- `system/views/auth_views.py`
- `static/system/js/auth/register.js`
- `templates/login/register.html`
- `templates/home/student/dashboard.html` (novo)
- `templates/home/admin/dashboard.html` (novo)
- `templates/home/instructor/dashboard.html` (novo)

## Critérios de aceite

- [ ] Wizard guardian mostra step-health e step-martial para o próprio responsável antes dos alunos
- [ ] Dados de saúde/artes marciais do responsável são persistidos na Person do guardian
- [ ] Endereço completo (incluindo city) é enviado ao Asaas na criação do customer
- [ ] Guardian com 2 alunos em plano não-familiar gera order com total = 2 × plan.price
- [ ] Ao retornar do Asaas após pagar plano, step-checkout exibe badge "Pagamento confirmado" + botão "Continuar para materiais"
- [ ] Ao retornar do Asaas após pagar materiais, step-products exibe badge "Pagamento confirmado" + botão "Continuar para o resumo"
- [ ] step-review exibe responsável (quando guardian) + cada aluno com turma e valor pago + botão Finalizar
- [ ] Após finalizar, person.is_active=True, login feito, redirect para home (não erro 500)
- [ ] Home carrega sem erro para perfis student, admin, instructor

## Plano

- [x] 1. PRD criado
- [ ] 2. Form: adicionar campos guardian health/martial
- [ ] 3. Service registration: passar campos health/martial para guardian
- [ ] 4. Service registration_checkout: multiplicador de treinantes
- [ ] 5. Asaas client + checkout: city
- [ ] 6. View auth: enriquecer pending_person_summary + review_data para incluir alunos
- [ ] 7. JS register.js: guardian health/martial na sequência + save correto
- [ ] 8. JS register.js: pós-pagamento confirmado UX + review melhorado
- [ ] 9. Home templates (mínimos)
- [ ] 10. manage.py check + test
- [ ] 11. collectstatic

## Implementado

(preenchido após execução)

## Desvios do plano

(preenchido após execução)

## Pendências

(preenchido após execução)
