# PRD-040: Fluxo intransigente de cadastro com pagamento antes de criar Pessoa

## Resumo do que será implementado

Corrigir o wizard publico de cadastro para que nenhum registro em `Person` seja criado antes da conclusao total do fluxo. O cadastro so pode existir na tabela de pessoas depois de:

1. preencher os dados no wizard;
2. escolher o plano;
3. pagar a mensalidade no Asaas;
4. voltar para a tela de pagamento da mensalidade com mensagem de pagamento confirmado;
5. avancar para materiais;
6. comprar ou pular materiais;
7. revisar o resumo completo;
8. clicar em finalizar cadastro.

Qualquer fluxo que crie `Person`, `PortalAccount`, vinculos, turmas ou acesso antes do passo final esta errado.

## Tipo de demanda

Correcao arquitetural + integracao externa + fluxo de cadastro.

## Problema atual

PRDs anteriores admitiram uma solucao intermediaria em que `Person` era criado com `is_active=False` apos a submissao do plano, porque `RegistrationOrder.person` e uma FK obrigatoria. Essa solucao nao atende ao contrato esperado do produto: o usuario ainda nao concluiu o cadastro, portanto nao deve existir como pessoa cadastrada no dominio.

O comportamento correto e manter os dados do wizard como pre-cadastro/transacao pendente ate o final. O pagamento do plano e o pagamento dos materiais pertencem ao fluxo financeiro de pre-cadastro, nao ao cadastro final da pessoa.

## Objetivo

Tornar obrigatorio e verificavel que:

- `Person.objects.filter(cpf=<cpf_do_wizard>).exists()` permanece `False` ate o clique final em "Finalizar cadastro";
- apos pagar a mensalidade no Asaas, o usuario retorna para o proprio wizard, na tela de pagamento da mensalidade, com mensagem de pagamento confirmado;
- somente depois disso o usuario avanca para escolher materiais;
- pagamento de materiais e resumo ocorrem antes da criacao da pessoa;
- a criacao de `Person`, `PortalAccount`, relacionamentos, turmas e acesso ocorre em uma unica finalizacao atomica.

## Context Ledger

### Arquivos lidos integralmente

- `AGENTS.md`
- `CLAUDE.md`
- `docs/prd/PRD-001-cadastro-cliente.md`
- `docs/prd/PRD-088-revisao-fluxo-cadastro.md`
- `docs/prd/PRD-021-etapas-pagamento-separadas-cadastro.md`
- `docs/prd/PRD-038-redesign-etapa-materiais-wizard.md`
- `docs/prd/PRD-039-fluxo-guardian-asaas-home-multiplicador.md`
- `system/forms/registration_forms.py`
- `system/views/auth_views.py`
- `system/views/payment_views.py`
- `system/views/asaas_views.py`
- `templates/login/register.html`
- `static/system/js/auth/register.js`

### Arquivos adjacentes consultados

- `docs/UI-SCREEN-CONTRACT.md`
- `system/models/registration_order.py`
- `system/models/pre_registration.py`
- `system/services/registration.py`
- `system/services/registration_checkout.py`
- `system/services/asaas_checkout.py`

### Internet / documentacao oficial

- Nao utilizada nesta regeneracao documental. A regra deriva da solicitacao atual do usuario e do contrato local do fluxo.

### MCPs / ferramentas verificadas

- PowerShell — funcional — leitura de arquivos via `Get-Content -Raw -Encoding UTF8`
- `rg` — funcional — busca de referencias do fluxo de cadastro e Asaas

### Limitacoes encontradas

- A implementacao atual ainda usa `RegistrationOrder.person` como FK obrigatoria, o que impede cumprir esta PRD sem refatorar a modelagem de pedido de pre-cadastro ou usar `PreRegistration` como titular temporario do checkout.
- Mudanca de schema, se necessaria, exige ciclo destrutivo executado pelo usuario. O agente nao pode executar `makemigrations` nem `migrate`.
- Pagamento Asaas real exige ngrok ativo, `SITE_BASE_URL` correto e intervencao humana quando o provedor externo exigir acao manual.

## Prompt de execucao

### Persona

Agente de desenvolvimento especialista em Django + Asaas + fluxos transacionais seguindo SDD + TDD + MVT com services.

### Acao

Implementar o fluxo de cadastro em que pagamentos de mensalidade e materiais acontecem antes da criacao de `Person`, e em que a finalizacao atomica e o unico ponto de criacao do cadastro real.

### Contexto

O wizard publico em `templates/login/register.html` e `static/system/js/auth/register.js` coleta dados de aluno titular, aluno titular com dependentes e responsavel por aluno(s). O pagamento ativo e Asaas. O fluxo deve preservar os dados preenchidos ao retornar do Asaas e jamais transformar pre-cadastro em pessoa cadastrada antes do resumo final.

### Restricoes

- sem criar `Person` antes de `register-finalize`;
- sem criar `PortalAccount` antes de `register-finalize`;
- sem criar relacionamentos, vinculos de turma ou acesso antes de `register-finalize`;
- sem mascaramento de erro;
- sem hardcode de host, URL, plano, CPF, produto ou estado de sessao;
- sem usar `request.build_absolute_uri()` para `successUrl` do Asaas;
- sem migracoes autonomas pelo agente;
- leitura integral obrigatoria;
- validacao automatizada e visual obrigatoria.

### Criterios de aceite

- [ ] Antes do pagamento da mensalidade, nenhum `Person` existe para os CPFs informados no wizard (verificavel: teste + ORM).
- [ ] A submissao da mensalidade cria apenas estado de pre-cadastro/pedido financeiro pendente, sem `Person`, `PortalAccount`, relacao familiar ou turma (verificavel: teste + ORM).
- [ ] A `successUrl` do Asaas retorna para o wizard em estado pos-pagamento do plano, mantendo os dados preenchidos e exibindo "Pagamento confirmado" na tela de pagamento da mensalidade (verificavel: navegador + console).
- [ ] Depois da confirmacao do plano, o usuario so avanca para materiais ao clicar em "Continuar para materiais" (verificavel: teste visual).
- [ ] Materiais sao pagos em pedido separado de pre-cadastro; pagar ou pular materiais nao cria `Person` (verificavel: teste + ORM).
- [ ] O resumo final exibe dados do cadastro, plano pago, materiais pagos ou pulados e valor total antes da criacao da pessoa (verificavel: navegador).
- [ ] `Person`, `PortalAccount`, relacionamentos e turmas sao criados somente no POST final de `register-finalize` (verificavel: teste + ORM).
- [ ] A finalizacao e atomica: se qualquer criacao final falhar, nada parcial fica persistido como cadastro real (verificavel: teste de erro).
- [ ] Aluno titular sem dependente cumpre o fluxo completo sem criar `Person` antes do final (verificavel: teste + navegador).
- [ ] Aluno titular com dependente(s) cumpre o fluxo completo sem criar `Person` para titular ou dependentes antes do final (verificavel: teste + navegador).
- [ ] Responsavel cadastrando aluno(s) cumpre o fluxo completo sem criar `Person` para responsavel ou alunos antes do final (verificavel: teste + navegador).
- [ ] Console do navegador sem erro JS critico durante retorno do Asaas e retomada do wizard (verificavel: browser).
- [ ] Terminal do servidor sem stack trace durante checkout, retorno, materiais e finalizacao (verificavel: logs).

### Evidencias esperadas

- `manage.py test --verbosity 2`
- `manage.py check`
- `manage.py collectstatic --noinput` se JS/CSS/template forem alterados
- shell checks de inexistencia de `Person` antes do final
- shell checks de existencia de `Person` somente apos finalizacao
- validacao visual desktop e mobile do wizard
- validacao real Asaas com ngrok ativo

### Formato de saida

Codigo implementado + testes + PRD atualizado com evidencias reais + registro de limitacoes.

## Escopo

- Persistencia temporaria de pre-cadastro antes da criacao de `Person`.
- Pedido financeiro de mensalidade vinculado ao pre-cadastro, nao a `Person`.
- Pedido financeiro de materiais vinculado ao pre-cadastro, nao a `Person`.
- Retomada do wizard apos retorno do Asaas com dados preenchidos.
- Finalizacao atomica criando cadastro real apenas no ultimo POST.
- Testes por tipo de cadastro: aluno titular, aluno titular com dependente(s), responsavel com aluno(s).

## Fora do escopo

- Redesign visual amplo do wizard.
- Mudanca de catalogo de planos, precos ou produtos.
- Troca de gateway de pagamento.
- Fluxo administrativo de estorno/cancelamento pos-cadastro.
- Criacao de migracoes pelo agente.

## Arquivos impactados

| Arquivo | Mudanca esperada |
|---|---|
| `system/models/pre_registration.py` | Usar ou ajustar entidade temporaria de pre-cadastro, se suficiente |
| `system/models/registration_order.py` | Permitir pedido de pre-cadastro sem `Person`, se necessario |
| `system/services/registration.py` | Mover criacao de `Person` para finalizacao atomica |
| `system/services/registration_checkout.py` | Criar pedidos de plano/materiais vinculados ao pre-cadastro |
| `system/views/auth_views.py` | Ajustar register, materials checkout e finalize |
| `system/views/payment_views.py` | Retomar wizard pos-Asaas sem login nem pessoa |
| `system/views/asaas_views.py` | Preservar `SITE_BASE_URL` na `successUrl` |
| `templates/login/register.html` | Estados pos-pagamento e dados de retomada |
| `static/system/js/auth/register.js` | Retomada do wizard, materiais e resumo sem cadastro antecipado |
| `system/tests/test_registration_flow.py` | Cobertura do contrato inteiro |
| `docs/prd/PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md` | Evidencias finais |

## Riscos e edge cases

- `RegistrationOrder.person` obrigatorio pode exigir mudanca de schema para suportar `PreRegistration`.
- Usuario paga plano e fecha o navegador antes dos materiais: o pre-cadastro deve ser recuperavel por sessao e/ou token seguro.
- Webhook do Asaas chega antes do redirect: o estado de pre-cadastro deve aceitar confirmacao assincrona.
- Usuario tenta repetir CPF durante pre-cadastro abandonado: CPF ainda nao e `Person`, mas deve haver controle de pre-cadastro expirado/idempotente.
- Usuario paga materiais e abandona antes de finalizar: pedidos ficam vinculados ao pre-cadastro, sem criar pessoa automaticamente.
- Falha na finalizacao atomica: nao pode criar pessoa parcial.
- Responsavel com multiplos alunos: nenhum CPF do grupo pode ser persistido em `Person` antes do final.

## Regras e restricoes

- SDD antes de codigo.
- TDD para implementacao.
- Sem hardcode.
- Sem mascaramento de erro.
- Sem migracoes autonomas.
- Leitura integral obrigatoria.
- Validacao obrigatoria.
- Regra intransigente: pagamento antes de pessoa; pessoa somente no final.

## Hierarquia Visual

- Padrao de leitura: F Pattern.
- Titulo de tela: peso 700-800, token `--text`.
- Secoes/grupos: peso 600, token `--text`.
- Campos/rotulos: peso 500, token `--text`.
- Help text/hints: peso 400, token `--muted`.
- Acao primaria: `--brand-red`, peso 600.
- Acao secundaria: borda `--border`, peso 500.
- Estados confirmados: badge de sucesso visualmente distinto, sem substituir o botao de avancar.

## Wireframe

### Regiao: Topo

- Logo LV.
- Progresso do wizard.
- Botao voltar preservando o estado atual.

### Regiao: Cadastro inicial

- Perfil: aluno ou responsavel.
- Dados pessoais.
- Saude.
- Artes marciais.
- Turmas.
- Plano.

### Regiao: Pagamento da mensalidade

- Resumo do plano.
- Acoes de pagamento Asaas.
- Apos retorno pago: mesma tela com badge "Pagamento confirmado" e botao "Continuar para materiais".

### Regiao: Materiais

- Catalogo de produtos.
- Configuracao de variante.
- Carrinho.
- Acoes de pagar com cartao, pagar com PIX ou pular materiais.

### Regiao: Resumo final

- Dados do titular/responsavel.
- Dependentes/alunos.
- Turmas.
- Mensalidade paga.
- Materiais pagos ou pulados.
- Botao "Finalizar cadastro e acessar o sistema".

### Estados da tela

- Carregando: wizard aguardando catalogos.
- Vazio: catalogo sem planos/produtos exibe mensagem explicita.
- Com dados: fluxo normal com dados preservados.
- Erro: erro de campo, pagamento ou retomada aparece sem apagar dados preenchidos.

## Maquinas de estado

### Pre-cadastro

- Estados: `draft`, `plan_payment_pending`, `plan_paid`, `materials_payment_pending`, `materials_paid`, `ready_to_finalize`, `finalized`, `expired`, `error`.
- Transicoes: `draft -> plan_payment_pending -> plan_paid -> materials_payment_pending -> materials_paid -> ready_to_finalize -> finalized`.
- Transicao alternativa: `plan_paid -> ready_to_finalize` quando materiais forem pulados.
- Representacao visual: cada estado pos-pagamento deve ter badge explicito e acao unica de continuidade.

### Wizard

- Estados: `editing`, `submitting_plan`, `return_plan_paid`, `editing_materials`, `submitting_materials`, `return_materials_paid`, `review`, `finalizing`, `done`, `error`.
- Transicoes: todo retorno do Asaas deve reconstruir a etapa correta sem criar `Person`.
- Representacao visual: nenhuma etapa pode parecer concluida sem confirmacao financeira real ou acao explicita do usuario.

## Plano

- [ ] 1. Contexto e leitura integral.
- [ ] 2. Contratos e modelagem de pre-cadastro sem `Person`.
- [ ] 3. Testes Red para inexistencia de `Person` antes da finalizacao.
- [ ] 4. Testes Red para retorno Asaas do plano no wizard.
- [ ] 5. Testes Red para materiais sem criar `Person`.
- [ ] 6. Testes Red para finalizacao atomica.
- [ ] 7. Implementacao Green em services/views.
- [ ] 8. Ajustes de template/JS para retomada.
- [ ] 9. Refatoracao.
- [ ] 10. Validacao completa automatizada.
- [ ] 11. Validacao visual desktop/mobile.
- [ ] 12. Validacao real Asaas com ngrok.
- [ ] 13. Atualizacao documental com evidencias.

## Validacao visual

### Desktop

- [ ] Fluxo completo sem sobreposicao de texto.
- [ ] Retorno do pagamento do plano mostra a mesma etapa de mensalidade com confirmacao.
- [ ] Materiais e resumo final aparecem somente depois do plano pago.

### Mobile

- [ ] Fluxo completo sem overflow horizontal.
- [ ] Botoes de continuidade ficam visiveis e nao sobrepoem conteudo.

### Console do navegador

- [ ] Sem erros JS criticos.
- [ ] Sem 404 relevante de estaticos.

### Terminal

- [ ] Sem stack trace em registro, pagamento, retorno, materiais e finalizacao.

## Validacao ORM

### Banco

- [ ] Antes do POST final: `Person.objects.filter(cpf__in=cpfs_do_wizard).count() == 0`.
- [ ] Depois do POST final: quantidade de `Person` corresponde exatamente ao titular/responsavel e alunos/dependentes esperados.

### Shell checks

```python
from system.models import Person
cpfs = ["000.000.000-00"]
print(Person.objects.filter(cpf__in=cpfs).exists())
```

### Integridade do fluxo

- [ ] Pedidos pagos ficam vinculados ao pre-cadastro ate a finalizacao.
- [ ] Finalizacao atomica cria pessoa e vinculos uma unica vez.

## Validacao de qualidade

### Sem hardcode

- [ ] URLs Asaas usam `settings.SITE_BASE_URL`.
- [ ] Planos e produtos vem de catalogos reais.

### Sem estruturas condicionais quebradicas

- [ ] Estados do fluxo sao explicitos e testados.

### Sem `except: pass`

- [ ] Erros de checkout e finalizacao sao registrados e propagados.

### Sem mascaramento de erro

- [ ] Falha financeira ou de finalizacao nao produz cadastro aparente.

### Sem comentarios e docstrings desnecessarios

- [ ] Comentarios apenas quando explicarem contrato transacional nao trivial.

## Evidencias

- `.\.venv\Scripts\python.exe manage.py test system.tests.test_registration_flow --verbosity 2` — OK, 2 testes.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_registration_flow system.tests.test_forms --verbosity 2` — OK, 6 testes.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — OK, 165 testes.
- `.\.venv\Scripts\python.exe manage.py check` — OK, sem issues.
- `node --check static\system\js\auth\register.js` — OK.
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — OK, 169 arquivos copiados.
- `.\.venv\Scripts\python.exe manage.py seed_system_initial_product_catalog` — OK, 5 produtos atualizados com preco unitario do JSON.
- Shell ORM: produtos com precos `belt-lv=69.90`, `gi-lv-adulto=399.90`, `gi-lv-infantil=329.90`, `patch-kit-3=45.00`, `rash-lv=149.90`.
- Playwright automatizado em `http://127.0.0.1:8000/register/` — OK:
  - CPF ativo existente exibiu erro durante digitacao.
  - Fluxo titular + dependente chegou ao `step-plan`.
  - `step-checkout` nao existe mais na pagina.
  - `step-plan` exibiu selecao de plano por pessoa treinante.
  - Botao do plano ficou como `Pagar mensalidade`.
  - Etapa de materiais pos-plano exibiu precos nao zerados.
  - Pular materiais levou ao resumo sem mensagem falsa de `Materiais confirmados`.
  - Console do navegador sem erros criticos.

## Implementado

- Primeiro POST do wizard cria/atualiza `PreRegistration` e nao cria `Person`.
- `Person` passa a ser criado apenas em `register-finalize`.
- Retorno de sucesso Asaas para pre-cadastro aceita `pre_registration_id` e `stage=plan|materials`.
- Pagamento da mensalidade foi movido para o proprio `step-plan`.
- `step-checkout` foi removido do template e da sequencia JS.
- Selecao de plano passou a ser por pessoa treinante no frontend.
- Feedback falso de pagamento para `pay_later`/pular materiais foi removido.
- Validacao de CPF existente passou a acontecer durante digitacao.
- Precos de materiais passaram a vir do JSON da seed e foram aplicados ao banco local.

## Desvios do plano

- A validacao externa real no Asaas nao foi concluida nesta rodada porque depende de interacao fora do navegador local com o checkout do provedor. O codigo agora gera cobrancas de pre-cadastro sem criar `Person`, mas a confirmacao real do provedor ainda precisa de teste manual com Asaas/ngrok ativo.

## Pendencias

- Validar pagamento real no Asaas com ngrok ativo e retorno para `payment-success`.
- Evoluir backend para persistir historico financeiro final dos pagamentos de pre-cadastro em `RegistrationOrder` apos a criacao da `Person`, se o financeiro administrativo exigir conciliacao por pedido interno.
