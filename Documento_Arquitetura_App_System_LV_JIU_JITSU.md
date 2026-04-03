# Documento de Arquitetura do App `system` - LV JIU JITSU

> Documento estrutural para sustentar a decisao de app unico `system`.
> Este arquivo nao substitui o `CLAUDE.md`; ele detalha como a arquitetura fisica deve ser organizada para que o dominio continue limpo mesmo sem multiplos apps Django.

---

## 1. Objetivo

Definir como o projeto deve crescer usando:

- um unico app Django chamado `system`;
- modularizacao interna forte por pastas, arquivos e responsabilidades;
- fronteiras claras entre dominio, orquestracao, leitura, interface e integracoes;
- um caminho de implementacao simples no inicio, sem perder disciplina arquitetural.

---

## 2. Decisao estrutural

### 2.1 Decisao principal

O projeto nao deve ser dividido, neste momento, em varios apps Django como `accounts`, `financeiro`, `pagamentos` ou `relatorios`.

O projeto deve usar:

- `system/` como unico app de negocio;
- subpastas internas para separar dominios;
- organizacao por camadas e por modulo interno;
- imports e dependencias controladas.

### 2.2 Motivo da decisao

Para o estado atual do produto, o app unico traz vantagens importantes:

- reduz friccao de migracoes e boot inicial;
- simplifica seed, admin, urls, testes e setup;
- evita fragmentacao artificial antes de o dominio estabilizar;
- acelera o planejamento e a execucao;
- permite absorver a disciplina do `Visary` sem copiar sua regra de negocio.

### 2.3 O que esta decisao nao autoriza

App unico nao significa:

- models todos no mesmo arquivo;
- views gigantes;
- services genericos demais;
- misturar Stripe com regra local de matricula;
- jogar toda consulta em template;
- concentrar toda logica em `system/views.py`.

---

## 3. Estrutura fisica alvo

```text
lvjiujitsu/
|-- manage.py
|-- system/
|   |-- admin.py
|   |-- apps.py
|   |-- urls.py
|   |-- api_urls.py
|   |-- signals.py
|   |-- permissions.py
|   |-- constants.py
|   |-- models/
|   |   |-- base.py
|   |   |-- identity_models.py
|   |   |-- student_models.py
|   |   |-- instructor_models.py
|   |   |-- class_models.py
|   |   |-- attendance_models.py
|   |   |-- finance_models.py
|   |   |-- payment_models.py
|   |   |-- graduation_models.py
|   |   |-- communication_models.py
|   |   |-- lgpd_models.py
|   |   |-- report_models.py
|   |   `-- config_models.py
|   |-- forms/
|   |-- serializers/
|   |-- views/
|   |-- selectors/
|   |-- services/
|   |   |-- auth/
|   |   |-- onboarding/
|   |   |-- students/
|   |   |-- instructors/
|   |   |-- classes/
|   |   |-- attendance/
|   |   |-- finance/
|   |   |-- payments/
|   |   |-- graduation/
|   |   |-- communications/
|   |   |-- lgpd/
|   |   |-- exports/
|   |   `-- settings_seed/
|   |-- management/commands/
|   `-- tests/
|-- templates/system/
`-- static/system/
```

---

## 4. Regras por camada

### 4.1 `models/`

Usar para:

- entidades persistidas;
- constraints;
- choices;
- validacoes de integridade local;
- metodos pequenos ligados ao proprio agregado.

Nao usar para:

- chamadas Stripe;
- regras de onboarding multi-entidade;
- consultas pesadas de dashboard;
- efeitos colaterais dispersos sem controle.

### 4.2 `services/`

Usar para:

- fluxos compostos;
- integracoes;
- transacoes;
- orquestracao entre multiplos modelos;
- validacao de pre-condicoes operacionais.

Todo service critico deve deixar claro:

- entrada;
- pre-condicoes;
- efeito persistido;
- eventos auditaveis;
- retorno esperado.

### 4.3 `selectors/`

Usar para:

- leituras de dashboard;
- listagens;
- consultas para relatorios;
- queries com `select_related()` e `prefetch_related()`;
- montagem de payloads de leitura.

Selector nao grava estado.

### 4.4 `views/`

Usar para:

- autenticacao e permissao;
- parse de request;
- chamada de service ou selector;
- retorno HTML ou JSON.

View nao decide regra central de negocio.

### 4.5 `forms/` e `serializers/`

Usar para:

- validacao de entrada;
- shape do payload;
- protecao contra over-posting;
- mensagens de erro.

Nao usar `fields = "__all__"` em fluxos sensiveis.

### 4.6 `signals.py`

Signals devem ser minimos e reservados para:

- sincronizacao previsivel;
- auditoria nao invasiva;
- efeitos secundarios pequenos e claramente documentados.

Fluxo central de negocio deve preferir service explicito.

---

## 5. Fronteiras internas obrigatorias

### 5.1 `finance_contracts` e `payments_stripe`

- `finance_contracts` define o estado local da matricula;
- `payments_stripe` reflete e sincroniza estado externo;
- Stripe nunca passa a ser dona do acesso esportivo.

### 5.2 `attendance_qr` e `graduation_engine`

- presenca valida alimenta graduacao;
- graduacao nao reescreve presenca;
- pausa e bloqueio financeiro afetam elegibilidade antes do check-in.

### 5.3 `student_registry` e `identity_access`

- identidade unica por CPF vive em `identity_access`;
- dados esportivos, responsavel e dependentes vivem em `student_registry`;
- multiplos papeis reaproveitam a mesma pessoa.

---

## 6. Organizacao de URLs

Mesmo com app unico, as rotas devem ser separadas por namespaces e jornadas:

- `system.urls.public`
- `system.urls.auth`
- `system.urls.portal`
- `system.urls.instructors`
- `system.urls.staff`
- `system.urls.finance`
- `system.urls.payments`
- `system.urls.webhooks`
- `system.urls.reports`
- `system.urls.api`

Se o projeto preferir manter um unico `urls.py`, ele deve apenas agregar submapeamentos.

---

## 7. Organizacao de templates e static

### 7.1 Templates

Organizar por jornada:

- `templates/system/public/`
- `templates/system/auth/`
- `templates/system/portal/`
- `templates/system/students/`
- `templates/system/instructors/`
- `templates/system/classes/`
- `templates/system/attendance/`
- `templates/system/finance/`
- `templates/system/payments/`
- `templates/system/graduation/`
- `templates/system/reports/`

### 7.2 Static

Organizar por responsabilidade:

- `static/system/css/`
- `static/system/js/`
- `static/system/img/`
- `static/system/icons/`

Scripts de pagina devem ser pequenos. Regras de negocio nao ficam no JS.

---

## 8. Seeds, catalogos e configuracoes

O `system` deve centralizar:

- seeds iniciais;
- configuracoes operacionais da academia;
- catalogos como modalidades, tipos de plano, motivos de pausa e regras de no-show;
- comandos de sincronizacao e bootstrap.

Tudo o que muda por academia deve ser configuravel por admin, painel ou modelo persistido.

---

## 9. Politica de testes dentro de `system`

Mesmo com app unico, os testes devem continuar segmentados:

- `tests/unit/identity/`
- `tests/unit/students/`
- `tests/unit/attendance/`
- `tests/unit/finance/`
- `tests/unit/payments/`
- `tests/unit/graduation/`
- `tests/integration/onboarding/`
- `tests/integration/checkin/`
- `tests/integration/stripe/`
- `tests/integration/lgpd/`
- `tests/smoke/`

App unico nao pode virar suite de testes caotica.

---

## 10. Quando sera aceitavel dividir em varios apps no futuro

So considerar quebrar `system` em multiplos apps quando houver simultaneamente:

- fronteiras estaveis por varios ciclos;
- necessidade real de ownership separado;
- volume de migracoes inviavel no app unico;
- administracoes independentes por subdominio;
- teste e deploy ficando piores por causa do acoplamento fisico.

A divisao futura deve ser consequencia de estabilidade, nao tentativa prematura de parecer enterprise.

---

## 11. Decisoes praticas para implementacao

- Toda entidade nova deve entrar em um arquivo tematico correto dentro de `system/models/`.
- Toda regra composta nova deve nascer em `system/services/`.
- Toda leitura de dashboard ou relatorio deve nascer em `system/selectors/`.
- Toda integracao Stripe deve passar por `system/services/payments/`.
- Toda exportacao deve passar por `system/services/exports/`.
- Toda regra de LGPD deve passar por `system/services/lgpd/`.
- Todo fluxo de presenca deve validar elegibilidade antes de qualquer acao de camera.

---

## 12. Resultado esperado

Se esta arquitetura for seguida, o projeto ganha:

- simplicidade estrutural no inicio;
- disciplina suficiente para nao virar um app monolitico desorganizado;
- melhor alinhamento entre documentacao, PRD e implementacao;
- base concreta para executar o sistema inteiro sem precisarmos replanejar a topologia toda a cada fase.
