# Documento Único de Mapeamento de Views e Endpoints
## Sistema LV JIU JITSU - Blueprint Estrutural da Camada de Apresentação (Django MVT + DRF + HTMX)

**Data:** 18/03/2026  
**Stack-alvo:** Django 5.x/6.x (CBVs) · Django REST Framework (APIs) · HTMX / Vanilla JS Fetch

---

## 1. Regras de Ouro da Camada de Views (Guardrails Absolutos)

### Views Finas (Thin Views)
A View é uma catraca de segurança. Ela verifica a identidade (Auth), checa a permissão, recebe os dados, chama a camada de Domínio/Service (`Services.fazer_algo(dados)`) e devolve a resposta. É proibido escrever regras de negócio diretamente nos métodos `get()`, `post()`, `form_valid()` ou nas funções de API.

### Serializers Tão Finos Quanto as Views
No DRF, o Serializer valida tipos e formatos com `is_valid()`. É proibido deslocar regras de negócio para dentro de `create()`, `update()` ou `save()` do Serializer. O método `save()` deve apenas repassar o `validated_data` para a camada de Services.

### Extermínio do N+1 (Views e Serializers)
Nenhuma View será aprovada se o `get_queryset()` não contiver `.select_related()` e `.prefetch_related()`. Atenção: no DRF, é estritamente proibido instanciar queries à base de dados dentro de métodos ligados a `SerializerMethodField`.

### Isolamento por UUID (`lookup_field = 'uuid'`)
A chave primária física (`id`) nunca deve vazar. Todas as `DetailView`, `UpdateView` e APIs devem usar `<uuid:uuid>` na rota. Em `ViewSet` do DRF, configure `lookup_field = 'uuid'`.

### Ações Mutáveis Exigem POST
Qualquer View MVT que altere o estado do sistema (cancelar reserva, trancar matrícula, iniciar checkout, aprovar mudança operacional) deve ser protegida contra requisições `GET` acidentais, exigindo o método `POST` e o Token CSRF.

### Rate Limit Rigoroso
Endpoints críticos de API exigem throttling do DRF. Para proteger páginas MVT como o ecrã de login contra ataques de força bruta, a equipa deve configurar `django-axes` ou mecanismo equivalente via cache/Redis.

### Paginação Inegociável
Qualquer listagem exige paginação. Em tabelas append-only de crescimento infinito (logs, presenças, movimentos de caixa), a paginação padrão por número/offset está proibida; a equipa deve usar paginação por cursor (`CursorPagination`).

---

## 2. Infraestrutura Transversal: Mixins, Middlewares e Permissões

### 2.1. Controle de Acesso (MVT vs DRF)
**Para MVT:** usar herança de Mixins na ordem correta (MRO): `class MinhaView(LoginRequiredMixin, RoleRequiredMixin, ListView)`.

**Para DRF:** `LoginRequiredMixin` não pode ser usado em APIs. O controlo deve ser feito estritamente através de `permission_classes = [IsAuthenticated, IsProfessorRole]` ou equivalentes baseados em `BasePermission`.

### 2.2. O Hard Stop Backend (AdimplenciaRequiredMixin / Permission DRF)
Intercepta rotas de tatame (reserva de vaga, câmara QR e check-in). Lê o `status_operacional` do `PerfilAluno`. Se for `PENDENTE_FINANCEIRO` ou `PAUSADO`, a requisição morre imediatamente (`403 Forbidden`).

### 2.3. O Switch de Contexto (ContextoDependenteMixin)
Lê o parâmetro `?dependente_uuid=xyz` na URL. Valida fisicamente se o utilizador possui direitos. Em caso afirmativo, injeta o aluno dependente no `get_context_data()`, alterando a visão do Dashboard para a perspetiva da criança.

### 2.4. A Barreira do Fuso Horário (Timezone Awareness)
O sistema não pode depender do fuso horário padrão do servidor (UTC) para queries de negócio orientadas ao utilizador. Um middleware ou a configuração consistente do fuso horário corrente (por exemplo, `America/Sao_Paulo`) deve estar sempre ativa para que filtros baseados em "hoje" não ocultem aulas noturnas por causa da virada de dia em UTC. Nas Views e Services que dependem do dia corrente, a equipa deve preferir APIs locais do Django, como `timezone.localdate()` ou equivalentes, em vez de assumir que `timezone.now().date()` sempre representa o dia de negócio da academia.

---

## 3. Mapeamento das Views por App

### App `accounts` e `clientes` (Identidade e Onboarding)

#### `OnboardingWizardView` (MVT)
Assistente de passos baseado em `django-formtools`.

**Risco de storage:** a implementação deve configurar um `file_storage` temporário para os passos do wizard, limpando resíduos e movendo os arquivos para o destino definitivo apenas no método `done()`.

#### `PerfilUpdateView` e uploads
Seja via MVT (exigindo `enctype="multipart/form-data"`) ou via API DRF (exigindo `parser_classes = [MultiPartParser, FormParser]`), os uploads devem ser estritamente declarados.

### App `presenca_graduacao` (Motor do Tatame)

#### `PreCheckElegibilidadeAPIView` (DRF - JSON)
Retorna a flag para o Javascript abrir a câmara ou mostrar o modal de bloqueio.

#### `ReservaVagaAPIView` (DRF - POST)
Endpoint de alta concorrência. A View repassa para o Service, que obrigatoriamente abrirá uma `transaction.atomic()` e fará `select_for_update()` na sessão da aula antes de efetivar a reserva.

#### `PainelAptidaoGraduacaoView` (MVT)
View de processamento pesado. O processamento da elegibilidade deve ser em background (Celery) ou através de fragment caching no template, invalidando o cache a cada promoção. Nunca aplicar cache cego da View inteira.

### App `financeiro` e `pagamentos` (Operações Monetárias)

#### A Proteção IDOR (`get_object` seguro)
Em views de detalhe, a query nunca pode ser `Fatura.objects.get(uuid=x)`. Deve obrigatoriamente garantir a posse: `get_object_or_404(Fatura, uuid=x, assinatura__titular_financeiro=request.user)`.

#### Idempotência Visual (Redirecionamento Stripe)
A página `pagamentos/sucesso/` não deve interrogar o banco para dar a fatura como paga. A página deve exibir "A processar pagamento / A aguardar confirmação", orientando o utilizador sem gerar falsos erros devido ao delay do webhook.

### App `relatorios` (Auditoria e Fail-Fast)

#### `ExportacaoBaseCSVView` (MVT/Assíncrona)
Inicializa o `ControleExportacaoCSV`. Se houver lock ou falha, devolve erro `423 Locked` ou `503 Service Unavailable`. Relatórios grandes delegam para o Celery (devolvendo `HTTP 202 Accepted`); relatórios médios usam obrigatoriamente `StreamingHttpResponse`.

---

## 4. O Fluxo de Transição MVT -> DRF -> HTMX e Segurança Frontend

### Páginas de leitura e listagem
Usam Django MVT. Os `ModelChoiceField` devem apontar sempre para `.ativos()` e nunca vazar dados inativos (soft delete).

### Ilhas de interatividade (WebRTC, PDV)
Usam Javascript puro (`fetch`) chamando endpoints DRF. O Javascript deve extrair o token CSRF dos cookies ou do DOM e enviá-lo obrigatoriamente no header `X-CSRFToken` em qualquer requisição `POST`, `PUT`, `PATCH` ou `DELETE`.

### Atualizações Parciais e o Ecossistema HTMX

#### A Armadilha do Redirecionamento (o Modal Esmagado)
Quando uma ação via HTMX (por exemplo, um formulário dentro de um modal) tiver sucesso e precisar redirecionar o utilizador para outra tela, a View não deve retornar um `HTTP 302 Redirect` padrão do Django. Caso contrário, o HTMX seguirá a resposta por AJAX e poderá injetar a página inteira dentro do modal. A View deve responder com o cabeçalho `HX-Redirect` apontando para a nova URL, preferencialmente com uma resposta sem corpo relevante (por exemplo, `204 No Content`), para forçar a navegação física do navegador.

#### Cache Inadvertido
O backend deve assegurar o envio do header `Vary: HX-Request` nas respostas para evitar que o navegador ou camadas intermédias misturem cache da página inteira com o fragmento HTMX.

#### Form Validation UX
Se um formulário enviado via HTMX contiver erros, a View MVT deve retornar o HTML com os erros usando `HTTP 200 OK` - ou `422 Unprocessable Entity` quando a equipa configurar explicitamente um fluxo compatível, como `hx-ext="response-targets"`. Se retornar `400 Bad Request`, o HTMX tende a abortar a substituição do HTML e o utilizador não verá os erros.

### Segurança do navegador e WebRTC
O `navigator.mediaDevices.getUserMedia` exige `HTTPS` ou `localhost`. Em desenvolvimento, abrir a tela de check-in por IP puro da rede local sem TLS tende a falhar.

---

## 5. Avisos de Trincheira (Proteção Estrita para o Desenvolvedor)

### Vulnerabilidade IDOR (`get_object()` solto)
Nunca use `Fatura.objects.get(uuid=kwargs['uuid'])` numa View orientada ao cliente. Views MVT ou DRF baseadas no cliente devem obrigatoriamente forçar a amarração ao utilizador logado em `get_queryset()` ou em `get_object_or_404(...)` já filtrado.

### Soft delete a vazar nos dropdowns
Se o sistema inativar um plano financeiro e a View usar `PlanoFinanceiro.objects.all()`, o plano cancelado reaparecerá no formulário. As Views devem apontar sempre para managers ativos, como `PlanoFinanceiro.objects.ativos()`.

### DRF e `SerializerMethodField`
Mesmo quando a View estiver otimizada com `select_related()` e `prefetch_related()`, um `SerializerMethodField` mal implementado pode recriar N+1 silencioso. É proibido fazer query por item dentro desse tipo de campo.

### Mixins conflituantes (MRO)
No Python, a herança é lida da esquerda para a direita. `class MinhaView(RoleRequiredMixin, LoginRequiredMixin, ListView)` está errado. O correto é estritamente `LoginRequiredMixin, RoleRequiredMixin, ListView`.

### APIs DRF não usam `LoginRequiredMixin`
Nas APIs do tatame, check-in e reserva, é obrigatório usar exclusivamente `permission_classes = [IsAuthenticated, ...]`. Nunca usar os mixins clássicos de autenticação do Django em `APIView`, pois isso pode gerar redirecionamento HTML (`302`) em vez de JSON (`401/403`).

### Sinais e desacoplamento
Views não devem engordar com notificações ou integrações lentas. Após a persistência principal, use signals ou Celery Tasks para disparar emails, sincronizações e side-effects, mantendo a resposta HTML/JSON rápida.

---

## 6. Diretrizes de Implementação Específicas do Ecossistema

### DRF: permissões por `permission_classes`
Nas APIs DRF, o equivalente dos mixins de acesso deve ser implementado via `permission_classes` com classes derivadas de `BasePermission`, em vez de reutilizar mixins MVT.

### DRF: segurança em `ViewSet` e `ModelViewSet`
A proteção contra IDOR deve nascer em `get_queryset()`, devolvendo apenas o subconjunto que pertence ao utilizador ou contexto ativo. O `get_object()` do DRF atuará sobre esse queryset já filtrado.

### DRF: parsers explícitos para upload
Se alguma atualização de selfie ou comprovativo for feita via API em vez de MVT, o endpoint deve declarar explicitamente `parser_classes = [MultiPartParser, FormParser]`.

### HTMX: variabilidade de resposta e cache
Respostas parciais devem variar por `HX-Request`. O backend deve tratar esse header como parte da estratégia de cache para que páginas completas e fragmentos não sejam confundidos pelo navegador ou por proxies.
