# Documento Único de Mapeamento de Models e Regras de Dados
## Sistema LV JIU JITSU — Blueprint Estrutural da Camada de Models (Django)
**Data:** 17/03/2026  
**Stack-alvo:** Django 5.x/6.x · PostgreSQL · django-allauth · dj-stripe · stripe-python

---

## Visão rápida dos apps

| App | Responsabilidade |
|---|---|
| `core` | Configurações globais da academia, mural e comunicações operacionais. |
| `accounts` | Identidade única por CPF, autenticação, papéis e trilha LGPD. |
| `clientes` | Perfis esportivos, vínculos de dependência e prontuário de emergência. |
| `professores` | Perfil docente, especialidades, disponibilidade e habilitações. |
| `presenca_graduacao` | Turmas, sessões, reservas, presença e motor de graduação. |
| `financeiro` | Planos, benefícios, faturas, pausa, PDV, estoque e caixa. |
| `pagamentos` | Checkout Stripe, comprovantes manuais e processamento de webhooks. |
| `dashboard` | Leitura agregada; sem models transacionais obrigatórios no MVP. |
| `relatorios` | Auditoria, exportações fail-fast e rastreabilidade operacional. |

## 1. Objetivo e escopo

Este documento define o mapeamento mestre da camada de models do sistema LV JIU JITSU. Ele descreve entidades persistentes, relacionamentos, constraints, métodos de domínio e limites entre model, manager, queryset e service.

O objetivo não é apenas listar tabelas, mas orientar a implementação de models coerentes com o CLAUDE_LV_JIU_JITSU_v2.md e o AGENTS_LV_JIU_JITSU_v2.md: identidade única por CPF, multi-papel real, regras esportivas no backend, integração Stripe desacoplada e trilha LGPD consistente.

O documento assume Django 5.x/6.x em monólito modular, PostgreSQL como banco principal e uso de django-allauth, dj-stripe, stripe-python, qrcode e html5-qrcode no restante da arquitetura.

- Fonte de verdade da identidade: CustomUser com CPF único de autenticação, sem duplicar pessoa por papel.
- Fonte de verdade do domínio esportivo: PerfilAluno, PerfilProfessor e modelos do app presenca_graduacao.
- Fonte de verdade do financeiro local: models do app financeiro; objetos da Stripe não devem ser espelhados sem necessidade quando já existirem no dj-stripe.
- Fluxos entre múltiplos agregados devem ser orquestrados em services.py com transaction.atomic(), não em save() gigante nem em view.

## 2. Guardrails de modelagem

- Usar PK física técnica (BigAutoField ou UUID interno) e tratar CPF como chave natural única de login e negócio.
- Declarar username = None no usuário customizado, configurar USERNAME_FIELD = "cpf" e fornecer um `CustomUserManager` próprio (herdando de `BaseUserManager`) para sobrescrever `create_user` e `create_superuser` com CPF como identificador obrigatório.
- Toda entidade transacional relevante deve ter created_at e updated_at.
- Para status e estados textuais de domínio, usar preferencialmente `models.TextChoices`; para enumerações numéricas, usar `models.IntegerChoices`. Evitar strings soltas no código e aproveitar labels nativos/traduzíveis para admin, dashboards e frontend.
- Validadores simples ficam em clean(); orquestrações multi-modelo ficam em services.py.
- Regras simples e invariantes estruturais que não podem depender do fluxo de formulário devem ser reforçadas com `models.CheckConstraint` na `class Meta` (ex.: `capacidade_maxima >= 1`, `hora_fim > hora_inicio`, saldos não negativos), pois `clean()` não protege criações diretas via ORM, scripts ou integrações.
- Validações sensíveis à concorrência não podem depender apenas de `clean()`. Em reservas de vaga, consumo de lotação, fechamento de caixa ou qualquer disputa de recurso escasso, o service transacional deve usar `transaction.atomic()` + `select_for_update()` no PostgreSQL para evitar condição de corrida.
- UniqueConstraint e índices compostos devem ser planejados desde o início para matrícula, reserva, presença, vínculos familiares, faturas e caixa.
- Convenção para textos opcionais: em `CharField` e `TextField`, preferir `blank=True` sem `null=True`, salvando ausência de dado como string vazia. Exceção consciente: campos textuais opcionais que também sejam `unique=True`, onde `null=True` evita colisão de múltiplos valores vazios.
- Todos os valores monetários do projeto (ex.: `valor_base`, `taxa_matricula`, `valor_original`, `valor_final`, `preco_venda`, `saldo_inicial`, `saldo_final_apurado`) devem usar estritamente `models.DecimalField(max_digits=10, decimal_places=2)`. `FloatField` é proibido para dinheiro devido a erros de arredondamento inerentes a ponto flutuante.
- Soft delete só deve existir onde fizer sentido operacional; para pessoas e dados sensíveis o fluxo correto é anonimização/exclusão definitiva conforme regra LGPD.
- Campos calculados frequentemente consultados podem usar @property quando forem baratos; se exigirem muitas queries, migrar para QuerySet/selector ou anotação de banco.

> **Nota:** Decisão importante: este documento separa regra persistente de negócio de detalhe efêmero de infraestrutura. Exemplo: token rotativo do QR pode viver em cache/Redis; a model persistente deve representar a sessão de aula e a presença, não cada rotação do token.

## 3. Convenções transversais para os models

- Criar um BaseModel abstrato com `id` (`BigAutoField`) para performance interna, `uuid` (`UUIDField`, `default=uuid.uuid4`, `unique=True`, `editable=False`) como identificador público para URLs/APIs, além de `created_at` e `updated_at`. Declarar obrigatoriamente `class Meta: abstract = True` para impedir criação de tabela física inútil e herança multi-table acidental.
- Aplicar o BaseModel às entidades de negócio. Para o `CustomUser` (que já herda de `AbstractUser`), usar um `UUIDTimestampMixin` sem redefinir o campo `id`, adicionando apenas `uuid`, `created_at` e `updated_at` para evitar conflito de herança/mapeamento.
- Rotas públicas, views e serializers não devem expor o `id` interno. Em URLs HTML e APIs, usar o UUID público como identificador externo, com padrões como `path('<uuid:uuid>/')`, `lookup_field = 'uuid'` e querysets filtrados por `uuid`.
- Criar QuerySets e Managers semânticos para filtros recorrentes: ativos(), elegiveis_checkin(), em_aberto(), vigentes(), etc.
- Em entidades com inativação lógica (`ativo=False`, status INATIVO, cancelado sem deleção física), fornecer Manager/QuerySet que esconda registros inativos por padrão ou ofereça acessos explícitos como `objects_ativos`/`all_objects`, evitando vazamento de registros "fantasma" em dropdowns, listagens e fluxos operacionais.
- Usar related_name explícito em todas as relações para facilitar leitura e prefetch_related.
- Quando múltiplas FKs apontarem para `CustomUser`, os `related_name` devem ser extremamente descritivos e sem colisão (ex.: `caixas_abertos`, `caixas_fechados`, `comprovantes_enviados`, `comprovantes_avaliados`), evitando clashes de reverse accessor no `makemigrations` e poluição semântica no modelo central de identidade.
- Declarar db_index em campos de busca frequente: cpf, status_operacional, data_aula, data_vencimento, status_assinatura, status_reserva.
- Regras de deleção (`on_delete`): models financeiros, históricos esportivos e trilhas de auditoria devem preferir `models.PROTECT` ou `models.RESTRICT` em FKs para entidades de domínio. `models.CASCADE` deve ficar restrito a relações de composição forte, como perfis em direção ao usuário e prontuário em direção ao aluno, quando a regra de retenção permitir.
- FKs para modelos espelhados pelo `dj-stripe` (`Customer`, `Subscription`, `Invoice` etc.) devem preferir `models.SET_NULL, null=True` — ou `PROTECT` quando a retenção local exigir vínculo intacto — para evitar perda do histórico financeiro local caso o espelho externo seja removido, reprocessado ou dessincronizado por webhooks/eventos do gateway.
- Evitar lógica com side effects pesados em save(); quando houver integração externa, disparar via service ou task controlada.
- Models singleton operacionais (ex.: `ConfiguracaoAcademia`) não devem depender apenas de convenção humana. A implementação deve forçar instância única via `save()` controlado, service dedicado e restrição administrativa para impedir criação concorrente de múltiplos registros ativos.
- Arquivos e imagens devem ser removidos do storage por método de domínio específico no fluxo de anonimização, nunca por exclusão cega do registro.
- Campos `FileField`/`ImageField` devem usar `upload_to` segmentado por data ou função determinística equivalente (ex.: `alunos/selfies/%Y/%m/`, `financeiro/comprovantes/%Y/%m/`) para evitar concentração excessiva de arquivos em um único diretório e facilitar organização operacional do storage.
- Campos `FileField`/`ImageField` devem declarar validadores no próprio model, incluindo `FileExtensionValidator` e validador de tamanho máximo por arquivo, para não depender apenas de frontend/view na proteção do storage contra tipos indevidos e uploads excessivos.
- Em fluxos LGPD com `FileField`/`ImageField`, primeiro remover o arquivo físico no storage (`field.delete(save=False)` ou `storage.delete(nome)`) e só depois limpar a referência no banco; atribuir `None` ao campo não apaga o arquivo por si só.
- Constraints de unicidade devem usar nome explícito para facilitar manutenção de migrações.
- Quando a regra de negócio for “apenas um registro ativo”, mas o histórico cancelado/expirado precisar coexistir, usar `models.UniqueConstraint(..., condition=Q(...))` no PostgreSQL em vez de unicidade bruta. Exemplo clássico: permitir várias reservas canceladas para a mesma sessão, mas apenas uma reserva ativa por aluno.
- Timezones (`USE_TZ = True`): todos os `DateTimeField` e toda captura do instante atual devem usar `django.utils.timezone.now()`. O uso de `datetime.now()` ingênuo é proibido em regras de TTL de QR, vencimento, janelas de check-in, abertura/fechamento de caixa e auditoria.
- Como o model `Turma` usa `ArrayField`, o projeto deve declarar `django.contrib.postgres` em `INSTALLED_APPS` para suportar corretamente os campos e lookups específicos do PostgreSQL.
- O Django Admin e forms padrão não renderizam `ArrayField(...choices=...)` de forma amigável por padrão. Para campos como `dias_semana`, o admin/form deve sobrescrever o widget para `forms.MultipleChoiceField` com `forms.CheckboxSelectMultiple` (ou widget equivalente), evitando entrada manual frágil como texto separado por vírgulas.
- O Django Admin do usuário customizado exige `CustomUserAdmin` próprio em `accounts/admin.py`, herdando de `UserAdmin` e removendo qualquer dependência do campo `username` em `fieldsets`, `add_fieldsets`, `list_display`, buscas e formulários.
- Em integrações Stripe baseadas em `dj-stripe`, evitar uma view paralela de webhook "crua" competindo com o endpoint do pacote. O app local deve reagir preferencialmente aos `djstripe.signals` emitidos após validação/processamento bem-sucedidos, garantindo que a lógica local leia o espelho já consistente.

> **Nota:** Regra prática: models calculam invariantes locais; services coordenam mudanças entre apps. Exemplo: “meses ativos na faixa” pertence ao domínio; “trancar matrícula + pausar Stripe + registrar auditoria” pertence a um service transacional.

> **Nota técnica de ORM:** Quando `USE_TZ = True`, o Django trabalha com datetimes aware e o banco/ORM podem emitir warnings ou gerar comparações problemáticas ao receber datetimes naïve. Em produção, toda lógica temporal do projeto deve nascer timezone-aware.

## App `core`

**Responsabilidade:** Configurações globais da academia, mural e central de comunicações.

O app core concentra parâmetros operacionais que não pertencem a um aluno específico, evitando hardcode em settings ou em views.

Como o projeto não possui um app comunicacao/ separado na spec final, os modelos de avisos e disparos operacionais ficam aqui.

### Model `ConfiguracaoAcademia`

**Descrição:** Singleton operacional da academia (ou por unidade, caso o projeto evolua para multiunidade).

**Campos principais:**
- nome_fantasia, razao_social, cnpj (quando aplicável), telefone_contato, email_contato
- idade_minima_dependente_com_credencial
- qr_token_ttl_segundos, antecedencia_maxima_reserva_minutos, tolerancia_checkin_minutos
- politica_inadimplencia_dias, permitir_checkin_sem_reserva, exige_prontuario_dependente
- usar_whatsapp, usar_email_transacional, usar_push_dashboard

**Métodos / propriedades de domínio:**
- clean(): validar ranges operacionais e impedir valores incompatíveis (ex.: TTL zero, tolerância negativa).
- @property janela_padrao_checkin: deriva a janela default da sessão.

**Constraints / índices / observações:**
- Idealmente uma instância ativa por unidade ou uma singleton global do sistema. Na implementação inicial, sobrescrever `save()` para fixar `self.pk = 1` (ou chave técnica equivalente) e tratar novas criações como atualização da configuração existente.

### Model `AvisoMural`

**Descrição:** Mensagem exibida na landing, home pública ou dashboards internos.

**Campos principais:**
- titulo, conteudo_html ou markdown_renderizado, prioridade, publico_alvo
- vigencia_inicio, vigencia_fim, publicado, fixado, autor (FK CustomUser)

**Métodos / propriedades de domínio:**
- @property esta_vigente: considera data atual e flag de publicação.

**Constraints / índices / observações:**
- Índice por publicado + vigência para consulta rápida no mural.

### Model `ComunicadoLote`

**Descrição:** Campanha operacional disparada para grupos de usuários (e-mail, push, WhatsApp, dashboard).

**Campos principais:**
- titulo, mensagem_base, canal, publico_alvo, status, agendado_para, disparado_em
- criado_por (FK CustomUser), usar_template, exige_confirmacao_leitura

**Métodos / propriedades de domínio:**
- pode_disparar(): valida se existem destinatários, canal ativo e conteúdo mínimo.

**Constraints / índices / observações:**
- Não executa entrega por si só; o envio individual deve ser rastreado em tabela filha.

### Model `EntregaComunicado`

**Descrição:** Rastreia envio por destinatário para auditoria e reprocessamento.

**Campos principais:**
- comunicado (FK), destinatario (FK CustomUser), canal, status_entrega, erro_resumido, entregue_em, lido_em

**Métodos / propriedades de domínio:**
- marcar_lido()
- marcar_falha(erro)

**Constraints / índices / observações:**
- UniqueConstraint por comunicado + destinatario + canal.

## App `accounts`

**Responsabilidade:** Identidade única, autenticação por CPF, papéis acumuláveis e trilha LGPD.

O app accounts é a base de identidade do sistema. Ele não deve concentrar regra esportiva nem financeira de negócio, mas precisa expor o esqueleto de autenticação e autorização de toda a plataforma.

A modelagem precisa impedir duplicidade de pessoa e, ao mesmo tempo, permitir acumular múltiplos papéis.

### Model `CustomUser`

**Descrição:** Usuário customizado que substitui username por CPF como campo de autenticação.

**Campos principais:**
- cpf (CharField, unique, indexed)
- email (EmailField, opcional e único quando informado)
- first_name, last_name, telefone_contato
- is_active, is_staff, is_superuser, last_login
- username = None; USERNAME_FIELD = "cpf"; REQUIRED_FIELDS mínimos
- objects = CustomUserManager() (manager obrigatório para criação correta via ORM, comandos de gestão e `createsuperuser`)

**Métodos / propriedades de domínio:**
- clean(): validar formato e dígito verificador do CPF.
- anonimizar_identidade(): hash irreversível do CPF em campo técnico próprio, limpeza de nome/e-mail/telefone e desativação de login quando juridicamente cabível.
- @property display_name: nome completo com fallback para CPF mascarado.

**Constraints / índices / observações:**
- CPF é a chave natural única do login.
- Exige `CustomUserManager` herdando de `BaseUserManager`, sobrescrevendo `create_user` e `create_superuser` para exigir CPF no lugar de `username` e evitar quebra no primeiro `createsuperuser`.
- O Django Admin também deve receber um `CustomUserAdmin` específico, removendo referências a `username` e promovendo `cpf` como campo principal de listagem, busca e edição.
- Flags de papel, se existirem, devem ser cache derivado — não fonte primária de verdade.
- Quando um `UserRoleAssignment` ativo conceder papel administrativo operacional (`ADMIN_MASTER`, `ADMIN_UNIDADE` ou equivalente), o fluxo de serviço deve sincronizar `is_staff=True` no `CustomUser`, pois o acesso ao Django Admin depende de `is_staff` e `is_active`.

### Model `UserRoleAssignment`

**Descrição:** Fonte explícita de papéis de negócio do usuário.

**Campos principais:**
- user (FK CustomUser), role (choices), ativo, origem_atribuicao, atribuida_em, atribuida_por (FK CustomUser, opcional)

**Métodos / propriedades de domínio:**
- clean(): impedir combinações inválidas apenas quando houver regra expressa.

**Constraints / índices / observações:**
- UniqueConstraint por user + role + ativo=True (ou user + role se não houver versionamento).
- A atribuição/remoção de papéis administrativos deve acionar serviço de sincronização de `is_staff` para manter coerência entre RBAC de domínio e acesso ao Django Admin.

### Model `SolicitacaoLGPD`

**Descrição:** Protocolo de solicitação de exclusão, anonimização ou cópia de dados.

**Campos principais:**
- usuario (FK), tipo_solicitacao, motivo, status, solicitado_em, concluido_em, operador_responsavel (FK CustomUser, opcional)
- parecer_operacional, base_legal_retentiva

**Métodos / propriedades de domínio:**
- pode_anonimizar(): valida se não há bloqueio legal/contábil.
- marcar_concluida()

**Constraints / índices / observações:**
- Uma solicitação aberta por tipo para o mesmo usuário, salvo reabertura formal.
- O service transacional de LGPD deve tentar remover ou redigir o vínculo do cliente também no gateway externo antes da anonimização local. Para clientes Stripe já associados, executar a estratégia compatível com o caso de uso da conta (ex.: `stripe.Customer.delete(customer_id)` e/ou ferramentas de redaction suportadas pela Stripe) antes de limpar os dados pessoais no Django.

### Model `AceiteTermo`

**Descrição:** Rastreia aceite de termos de uso, LGPD, regulamento e autorizações de responsável.

**Campos principais:**
- usuario (FK), tipo_termo, versao_termo, aceito_em, ip_origem, user_agent_resumido, aceite_por_responsavel (bool)

**Métodos / propriedades de domínio:**
- @property identificador_termo: combinação de tipo e versão.

**Constraints / índices / observações:**
- UniqueConstraint por usuario + tipo_termo + versao_termo.

## App `clientes`

**Responsabilidade:** Perfis de aluno, dependentes, relações com responsáveis e prontuário.

Aqui ficam os dados do praticante e dos vínculos familiares/financeiros relacionados ao treino.

Um responsável financeiro que não treina não precisa existir como PerfilAluno; por isso o vínculo com dependentes não deve ser um self-FK ingênuo no perfil do aluno.

### Model `PerfilAluno`

**Descrição:** Perfil esportivo de quem efetivamente treina. Professor que também treina pode ter este perfil no mesmo CPF.

**Campos principais:**
- user (OneToOne CustomUser)
- data_nascimento, telefone_emergencial_secundario, endereco_resumido
- foto_selfie (`ImageField` com `upload_to` segmentado, ex.: `alunos/selfies/%Y/%m/`, `FileExtensionValidator(['jpg', 'jpeg', 'png'])` e validador de tamanho), observacoes_internas
- status_operacional (ATIVO, PENDENTE_FINANCEIRO, PAUSADO, BLOQUEADO_ADMIN, INATIVO)
- permite_credencial_propria (bool), data_primeiro_treino

**Métodos / propriedades de domínio:**
- @property idade: calcula idade atual.
- @property possui_credencial_propria: deriva da existência de user ativo + regra etária/configuração.
- @property elegivel_checkin_basico: True apenas quando status permitir acesso esportivo.
- anonimizar_dados_pessoais(): remove selfie do storage e limpa dados pessoais sensíveis não retidos. Na implementação, apagar explicitamente o arquivo físico/bucket antes de limpar o campo no banco.

**Constraints / índices / observações:**
- OneToOne obrigatório com CustomUser; um usuário pode existir sem PerfilAluno, mas não o contrário.
- Padronizar `status_operacional` com `models.TextChoices` para centralizar valores persistidos e labels de exibição.

### Model `VinculoResponsavelAluno`

**Descrição:** Modela titularidade e responsabilidade financeira sem exigir que o responsável tenha PerfilAluno.

**Campos principais:**
- aluno (FK PerfilAluno)
- responsavel (FK CustomUser)
- tipo_vinculo (TITULAR_PROPRIO, RESPONSAVEL_FINANCEIRO, OUTRO_RESPONSAVEL_AUTORIZADO)
- principal (bool), autoriza_acoes_medicas (bool), ativo, inicio_vinculo, fim_vinculo

**Métodos / propriedades de domínio:**
- clean(): garantir no máximo um responsável principal ativo por aluno para o mesmo tipo quando a regra exigir.

**Constraints / índices / observações:**
- UniqueConstraint parcial para responsável principal ativo por aluno.

### Model `ProntuarioEmergencia`

**Descrição:** Dados de emergência e saúde com acesso fortemente restrito.

**Campos principais:**
- aluno (OneToOne PerfilAluno), tipo_sanguineo, alergias, lesoes_previas, medicamentos_continuos
- nome_contato_emergencia, parentesco_contato_emergencia, telefone_emergencia, observacoes_criticas

**Métodos / propriedades de domínio:**
- anonimizar_prontuario(): apaga dados médicos e contatos quando juridicamente cabível.

**Constraints / índices / observações:**
- OneToOne com PerfilAluno; toda leitura deve ser auditada fora da model pelo domínio de relatórios.

### Model `HistoricoTreinoAluno`

**Descrição:** Registro resumido de marcos esportivos do aluno que não cabem em presença/graduacao pura.

**Campos principais:**
- aluno (FK PerfilAluno), tipo_evento, descricao, data_evento, origem

**Constraints / índices / observações:**
- Opcional no MVP; útil para observações esportivas longitudinalmente relevantes.

## App `professores`

**Responsabilidade:** Perfil docente, habilitações e disponibilidade.

O professor é uma pessoa da mesma base de identidade, mas com dados de negócio próprios para docência e alocação em turmas.

### Model `PerfilProfessor`

**Descrição:** Perfil de negócio do docente.

**Campos principais:**
- user (OneToOne CustomUser), data_contratacao, bio_curta, registro_interno, ativo_para_escala
- carga_horaria_mensal_meta, observacoes_administrativas

**Métodos / propriedades de domínio:**
- aulas_ministradas_periodo(inicio, fim): agregação de sessões concluídas associadas ao professor.
- @property pode_ser_alocado: depende de ativo_para_escala e documentos internos válidos, se exigidos.

**Constraints / índices / observações:**
- OneToOne com CustomUser.

### Model `ProfessorModalidade`

**Descrição:** Tabela de habilitação do professor por modalidade/faixa/nível.

**Campos principais:**
- professor (FK PerfilProfessor), modalidade (FK presenca_graduacao.Modalidade), nivel_habilitado, observacoes

**Constraints / índices / observações:**
- UniqueConstraint por professor + modalidade + nivel_habilitado.

### Model `DisponibilidadeProfessor`

**Descrição:** Janela recorrente de disponibilidade para agenda e alocação em turma.

**Campos principais:**
- professor (FK PerfilProfessor), dia_semana, hora_inicio, hora_fim, ativo

**Métodos / propriedades de domínio:**
- clean(): impedir hora_fim <= hora_inicio.

**Constraints / índices / observações:**
- Evitar duplicidade exata de faixa horária por professor e dia. Adicionar `CheckConstraint` para garantir `hora_fim > hora_inicio` também no banco, e não apenas em `clean()`.

## App `presenca_graduacao`

**Responsabilidade:** Modalidades, turmas, reserva, presença, exames e motor de progressão.

Este app une presença e graduação de propósito, porque o acoplamento de negócio é alto: elegibilidade de faixa depende de treino ativo, presença válida e períodos congelados por pausa.

O foco persistente deve estar em sessão, reserva, presença e histórico de graduação; token rotativo efêmero não precisa virar tabela por si só.

### Model `Modalidade`

**Descrição:** Catálogo de modalidades e recortes de turma (BJJ adulto, infantil, no-gi, competição etc.).

**Campos principais:**
- nome, slug, ativa, idade_minima, idade_maxima, exige_reserva_previa_por_padrao

**Constraints / índices / observações:**
- Slug único.

### Model `FaixaIBJJF`

**Descrição:** Catálogo oficial/referencial de faixas.

**Campos principais:**
- modalidade (FK Modalidade, opcional), nome, ordem, cor_hex, idade_minima_anos, tempo_minimo_meses

**Constraints / índices / observações:**
- UniqueConstraint por modalidade + ordem ou catálogo global quando aplicável.

### Model `RegraGraduacaoAcademia`

**Descrição:** Configuração interna da academia para graus, carências e flexibilizações sem perder referência oficial.

**Campos principais:**
- modalidade (FK), faixa_origem (FK FaixaIBJJF), faixa_destino (FK FaixaIBJJF), meses_minimos_ativos, presencas_minimas, ativa

**Métodos / propriedades de domínio:**
- clean(): impedir origem e destino iguais e validar progressão de ordem.

**Constraints / índices / observações:**
- UniqueConstraint por modalidade + faixa_origem + faixa_destino + ativa.

### Model `HistoricoGraduacao`

**Descrição:** Linha do tempo do aluno por faixa/grau. Não deve ser sobrescrita de forma destrutiva.

**Campos principais:**
- aluno (FK PerfilAluno), faixa (FK FaixaIBJJF), data_inicio, data_fim, graus_atuais, professor_responsavel (FK PerfilProfessor, opcional), origem_evento

**Métodos / propriedades de domínio:**
- @property meses_ativos_na_faixa: subtrai períodos em que o aluno esteve pausado.
- @property elegivel_proxima_faixa: considera regra da academia + referência oficial + idade + status operacional.

**Constraints / índices / observações:**
- Apenas um registro ativo por aluno/faixa vigente quando data_fim for nula.

### Model `ExameGraduacao`

**Descrição:** Evento formal de avaliação/promocão.

**Campos principais:**
- titulo, modalidade (FK), data_evento, status, observacoes, criado_por (FK CustomUser)

**Métodos / propriedades de domínio:**
- pode_publicar_resultado(): exige status finalizado e candidatos avaliados.

### Model `ParticipacaoExameGraduacao`

**Descrição:** Lista de candidatos de um exame com resultado individual.

**Campos principais:**
- exame (FK), aluno (FK PerfilAluno), faixa_destino (FK FaixaIBJJF), resultado, nota_textual, avaliado_por (FK PerfilProfessor, opcional)

**Constraints / índices / observações:**
- UniqueConstraint por exame + aluno.

### Model `Turma`

**Descrição:** Turma recorrente vinculada a modalidade e professor principal.

**Campos principais:**
- modalidade (FK Modalidade), nome, professor_principal (FK PerfilProfessor), capacidade_maxima, exige_reserva_previa, ativa
- hora_inicio, hora_fim, `dias_semana` (`ArrayField` de `IntegerChoices`, ex.: 0=Domingo, 1=Segunda, otimizado para PostgreSQL)

**Métodos / propriedades de domínio:**
- clean(): impedir capacidade < 1, validar janela horária e consistência dos valores aceitos em `dias_semana`.

**Constraints / índices / observações:**
- Nome único por modalidade/horário quando a operação exigir.
- O uso de `ArrayField` em PostgreSQL facilita queries para geração automática de `SessaoAula` e evita serialização frágil em texto como "SEG,QUA,SEX".
- No Django Admin/forms, `dias_semana` deve usar widget múltiplo com checkboxes (`MultipleChoiceField` + `CheckboxSelectMultiple` ou equivalente), nunca campo textual cru para digitação manual de inteiros.

### Model `SessaoAula`

**Descrição:** Instância concreta de aula em uma data/hora, base da presença e da reserva.

**Campos principais:**
- turma (FK), data_aula, inicio_real, fim_real, status (AGENDADA, LIBERADA, EM_ANDAMENTO, ENCERRADA, CANCELADA)
- professor_responsavel (FK PerfilProfessor, opcional override), token_qr_version, checkin_aberto_em, checkin_fecha_em

**Métodos / propriedades de domínio:**
- @property vagas_disponiveis: capacidade - reservas_confirmadas.
- @property aceita_checkin_agora: considera status e janela de tempo.
- validar_token_qr(token_recebido): cruza o token recebido com o estado efêmero em cache/Redis e com `token_qr_version`, impedindo foto antiga ou token rotacionado de gerar presença válida.

**Constraints / índices / observações:**
- UniqueConstraint por turma + data_aula + início previsto/real conforme estratégia adotada.

### Model `ReservaVaga`

**Descrição:** Reserva prévia consumindo lotação antes da chegada do aluno à academia.

**Campos principais:**
- aluno (FK PerfilAluno), sessao (FK SessaoAula), status (CONFIRMADA, CANCELADA, PRESENTE, NO_SHOW, EXPIRADA), reservado_em, cancelado_em

**Métodos / propriedades de domínio:**
- clean(): validar elegibilidade do aluno, sessão aberta para reserva e vagas disponíveis.
- **Nota crítica de concorrência:** esta validação isolada não basta para turmas concorridas. O service de reserva deve abrir `transaction.atomic()`, carregar `SessaoAula` com `select_for_update()` e só então recalcular vagas antes de persistir, impedindo overbooking na última vaga.
- consome_lotacao(): True apenas para status que reservam vaga de fato.

**Constraints / índices / observações:**
- Preferir `UniqueConstraint` condicional para estados ativos, por exemplo restringindo duplicidade apenas quando `status` estiver em `(CONFIRMADA, PRESENTE)`, permitindo múltiplos registros históricos `CANCELADA`/`EXPIRADA` sem bloquear nova reserva.
- Índice por sessao + status.

### Model `PresencaFisica`

**Descrição:** Check-in efetivo do aluno na sessão.

**Campos principais:**
- aluno (FK PerfilAluno), sessao (FK SessaoAula), metodo (QR_CODE, MANUAL), registrada_em, registrada_por (FK CustomUser, opcional)

**Métodos / propriedades de domínio:**
- clean(): impedir duplicidade e revalidar elegibilidade da sessão/aluno.
- sincronizar_reserva(): atualiza ReservaVaga para PRESENTE quando houver reserva associada.

**Constraints / índices / observações:**
- UniqueConstraint por aluno + sessao.

## App `financeiro`

**Responsabilidade:** Planos, benefícios, faturas, pausa, PDV, estoque e caixa.

Este app representa o contrato local da academia, independentemente do gateway.

Ele também precisa cobrir operação de balcão, caixa diário e vendas avulsas, que não podem depender apenas do ecossistema Stripe.

Todos os valores monetários deste app e do app `pagamentos` devem ser modelados com `DecimalField(max_digits=10, decimal_places=2)`.

### Model `PlanoFinanceiro`

**Descrição:** Plano comercial local da academia.

**Campos principais:**
- nome, periodicidade, valor_base, ativo, permite_dependentes, recorrencia_gateway_habilitada
- stripe_price (FK `djstripe.Price`, opcional)
- taxa_matricula, regras_resumidas

**Constraints / índices / observações:**
- Nome único ativo quando a operação exigir catálogo limpo.
- Valores monetários do plano devem ser persistidos com `DecimalField(max_digits=10, decimal_places=2)`.
- Para manter consistência com o ecossistema `dj-stripe`, preferir relação ORM direta com `djstripe.Price` usando `on_delete=models.SET_NULL` e `null=True`, em vez de armazenar apenas `stripe_price_id` textual.

### Model `BeneficioFinanceiro`

**Descrição:** Bolsa, desconto, cortesia ou regra promocional aplicável ao contrato.

**Campos principais:**
- nome, tipo (PERCENTUAL, VALOR_FIXO, CORTESIA), valor, ativo, exige_aprovacao, motivo_padrao

**Métodos / propriedades de domínio:**
- @property fator_efetivo: converte benefício para cálculo padronizado.

### Model `Assinatura`

**Descrição:** Contrato local do titular/dependente com a academia.

**Campos principais:**
- titular_financeiro (FK CustomUser), plano (FK PlanoFinanceiro), status_assinatura (ATIVA, PAST_DUE, PAUSADA, CANCELADA, ENCERRADA)
- beneficio_aplicado (FK BeneficioFinanceiro, opcional), data_inicio, data_fim, dia_vencimento, observacoes
- stripe_subscription (FK `djstripe.Subscription`, opcional), stripe_customer (FK `djstripe.Customer`, opcional)

**Métodos / propriedades de domínio:**
- @property esta_vigente
- @property bloqueia_acesso_esportivo: deriva de status e política de inadimplência.

**Constraints / índices / observações:**
- Índice por titular_financeiro + status_assinatura.
- Preferir relação ORM direta com `dj-stripe` em vez de espelhar IDs textuais soltos, reduzindo consultas manuais à API e facilitando joins no banco.
- Nessas FKs para `dj-stripe`, preferir `on_delete=models.SET_NULL` com `null=True` para preservar o contrato local mesmo que o objeto espelhado externo deixe de existir ou seja reprocessado.

### Model `AssinaturaAluno`

**Descrição:** Vincula alunos cobertos por uma assinatura familiar ou individual.

**Campos principais:**
- assinatura (FK Assinatura), aluno (FK PerfilAluno), papel_no_contrato (TITULAR_TREINANTE, DEPENDENTE, BOLSISTA), ativo

**Constraints / índices / observações:**
- UniqueConstraint por assinatura + aluno.

### Model `TrancamentoMatricula`

**Descrição:** Histórico auditável de pausas de matrícula.

**Campos principais:**
- assinatura (FK Assinatura), data_inicio, data_retorno_prevista, data_retorno_real, motivo, status (EM_VIGOR, ENCERRADO, CANCELADO)
- solicitado_por (FK CustomUser), aprovado_por (FK CustomUser, opcional)

**Métodos / propriedades de domínio:**
- @property esta_em_vigor
- encerrar_trancamento(data_retorno_real)

**Constraints / índices / observações:**
- No máximo um trancamento em vigor por assinatura.

### Model `FaturaMensal`

**Descrição:** Cobrança local vinculada à assinatura, independentemente do gateway.

**Campos principais:**
- assinatura (FK), `competencia` (`DateField`, sempre persistido no primeiro dia do mês, ex.: `2026-03-01`), valor_original, valor_final, vencimento_em, pago_em, status (ABERTA, PAGA, ATRASADA, CANCELADA, ISENTA)
- origem_cobranca, observacoes
- stripe_invoice (FK `djstripe.Invoice`, opcional), stripe_subscription (FK `djstripe.Subscription`, opcional), stripe_customer (FK `djstripe.Customer`, opcional)

**Métodos / propriedades de domínio:**
- @property em_atraso
- liquidar_manual(meio_pagamento, operador=None)

**Constraints / índices / observações:**
- UniqueConstraint por assinatura + competencia. Índice por status + vencimento_em.
- `competencia` não deve ser `CharField` textual como `"03/2026"`; a convenção é `DateField` no primeiro dia do mês para preservar ordenação cronológica, filtros por intervalo (`competencia__gte`) e agregações temporais do PostgreSQL.
- As FKs para `djstripe.Invoice`/`Subscription`/`Customer` devem seguir a mesma regra defensiva de `SET_NULL`/`PROTECT`, preservando a fatura local como registro contábil da academia.
- Quando houver espelho de cobrança no gateway, preferir relações com modelos do `dj-stripe` ao invés de copiar apenas identificadores em texto.

### Model `ProdutoPDV`

**Descrição:** Produto ou serviço vendido na recepção.

**Campos principais:**
- nome, sku, tipo_item (PRODUTO, SERVICO, ALUGUEL), preco_venda, controla_estoque, estoque_atual, estoque_minimo, ativo

**Métodos / propriedades de domínio:**
- baixar_estoque(qtd)
- repor_estoque(qtd)

**Constraints / índices / observações:**
- SKU único quando informado.

### Model `VendaPDV`

**Descrição:** Venda avulsa no balcão.

**Campos principais:**
- caixa (FK CaixaTurno), cliente_user (FK CustomUser, opcional), total_bruto, desconto_total, total_liquido, meio_pagamento, status, vendida_em, operador (FK CustomUser)

**Métodos / propriedades de domínio:**
- finalizar(): consolida itens, baixa estoque e gera movimentação de caixa se aplicável.

### Model `ItemVendaPDV`

**Descrição:** Itens de uma venda no PDV.

**Campos principais:**
- venda (FK VendaPDV), produto (FK ProdutoPDV), quantidade, valor_unitario, valor_total

**Constraints / índices / observações:**
- UniqueConstraint opcional por venda + produto quando não quiser linhas repetidas.

### Model `CaixaTurno`

**Descrição:** Sessão operacional do caixa/recepção.

**Campos principais:**
- operador_abertura (FK CustomUser), operador_fechamento (FK CustomUser, opcional), aberto_em, fechado_em, saldo_inicial, saldo_final_informado, saldo_final_apurado, status

**Métodos / propriedades de domínio:**
- @property diferenca_caixa: saldo_final_informado - saldo_final_apurado.
- pode_fechar()

**Constraints / índices / observações:**
- Um caixa aberto por operador/unidade, conforme política operacional.
- Implementar `UniqueConstraint` condicional para impedir dois caixas simultaneamente abertos pelo mesmo operador (e, quando aplicável, pela mesma unidade), por exemplo com `condition=Q(status='ABERTO')`. Isso protege inclusive contra duplo clique ou concorrência de abertura no PostgreSQL.

### Model `MovimentacaoCaixa`

**Descrição:** Entradas e saídas do caixa físico.

**Campos principais:**
- caixa (FK CaixaTurno), tipo (ENTRADA, SAIDA), origem (PDV, FATURA_MANUAL, SANGRIA, SUPRIMENTO, AJUSTE), meio_pagamento, valor, descricao, registrada_em, registrada_por (FK CustomUser)

**Constraints / índices / observações:**
- Índice por caixa + tipo + registrada_em.

## App `pagamentos`

**Responsabilidade:** Integração técnica com Stripe, comprovantes manuais e processamento assíncrono.

Como a arquitetura usa dj-stripe, os objetos canônicos da Stripe (Customer, Subscription, Invoice, Event etc.) devem ser lidos prioritariamente das tabelas do próprio pacote quando isso bastar.

A aplicação local não deve competir com o endpoint oficial de webhook do `dj-stripe` com uma segunda implementação paralela para os mesmos eventos. A extensão do domínio da academia deve reagir preferencialmente via `djstripe.signals`, após o pacote validar a assinatura, persistir o espelho local e concluir o processamento principal.

Receivers conectados a `djstripe.signals` que atualizem `Assinatura`, `FaturaMensal` ou outros agregados locais devem rodar dentro de `transaction.atomic()`, preservando consistência entre o espelho do gateway e o domínio da academia quando houver falha na lógica local.

Este app local deve guardar apenas o que é específico do fluxo do negócio da academia e o que a integração precisa rastrear fora do espelho padrão do dj-stripe.

### Model `CheckoutSolicitacao`

**Descrição:** Rastro local da intenção de checkout/assinatura.

**Campos principais:**
- titular (FK CustomUser), plano (FK financeiro.PlanoFinanceiro), status, stripe_checkout_session_id, criado_em, expirado_em, metadata_resumo

**Métodos / propriedades de domínio:**
- @property expirado
- marcar_concluido()

**Constraints / índices / observações:**
- UniqueConstraint por stripe_checkout_session_id quando informado.

### Model `WebhookProcessamento`

**Descrição:** Controle interno da aplicação sobre processamento de eventos vindos do gateway.

**Campos principais:**
- gateway, event_id_externo, tipo_evento, recebido_em, processado_em, status_processamento, erro_resumido, payload_hash

**Métodos / propriedades de domínio:**
- marcar_processado()
- marcar_falha(erro)
- **Nota de implementação:** o receiver/handler que reagir ao evento processado pelo `dj-stripe` deve encapsular suas atualizações locais em `transaction.atomic()`.

**Constraints / índices / observações:**
- UniqueConstraint por gateway + event_id_externo para garantir idempotência local.

### Model `ComprovanteManual`

**Descrição:** Comprovante enviado pelo usuário para análise manual.

**Campos principais:**
- fatura (FK financeiro.FaturaMensal), arquivo (`FileField` com `upload_to` segmentado, ex.: `financeiro/comprovantes/%Y/%m/`, `FileExtensionValidator(['jpg', 'jpeg', 'png', 'pdf'])` e validador de tamanho), enviado_por (FK CustomUser), enviado_em, status_analise, analisado_por (FK CustomUser, opcional), analisado_em, observacoes

**Métodos / propriedades de domínio:**
- aprovar()
- rejeitar(motivo)

**Constraints / índices / observações:**
- Índice por status_analise + enviado_em.
- Padronizar `status_analise` com `models.TextChoices` para expor labels legíveis no admin e no fluxo operacional de aprovação.

## App `dashboard`

**Responsabilidade:** Camada de leitura agregada para painéis do aluno, professor e administrativo.

Por padrão, o app dashboard não deve carregar models transacionais próprias no MVP.

Ele deve ser implementado com selectors, querysets otimizados, caches e, só quando realmente necessário, snapshots materializados para performance.

### Model `DashboardSnapshotDiario (opcional)`

**Descrição:** Snapshot materializado de indicadores quando performance ou custo de query justificar.

**Campos principais:**
- data_referencia, tipo_dashboard, escopo, payload_json, gerado_em

**Constraints / índices / observações:**
- Opcional; evitar introduzir cedo se selectors resolverem bem o problema.

## App `relatorios`

**Responsabilidade:** Auditoria, exportações seguras e trilha de ações sensíveis.

Relatórios não são só leitura; eles precisam registrar quem exportou, o que foi exportado e se as pré-condições de I/O foram respeitadas.

### Model `LogAuditoria`

**Descrição:** Registro central de ações críticas do sistema.

**Campos principais:**
- usuario_ator (FK CustomUser, opcional para eventos sistêmicos), categoria, acao, app_label, model_name, objeto_id, descricao_resumo, antes_json, depois_json, ip_origem, criado_em

**Constraints / índices / observações:**
- Índice por categoria + criado_em e por app/model/objeto_id.
- Observação técnica: para logs automáticos de CRUD e ações profundas em services, a captura de `usuario_ator` deve ser apoiada por middleware (usando `request.user`) e/ou sinais (`signals.py`) ligados aos services transacionais, evitando registros órfãos.

### Model `SolicitacaoExportacao`

**Descrição:** Pedido de geração de arquivo analítico ou operacional.

**Campos principais:**
- solicitante (FK CustomUser), tipo_relatorio, filtros_json, status (PENDENTE, EM_PROCESSAMENTO, PRONTO, FALHA_PRE_VALIDACAO, FALHA_PROCESSAMENTO), solicitado_em, iniciado_em, concluido_em

**Métodos / propriedades de domínio:**
- pode_iniciar()

**Constraints / índices / observações:**
- Índice por status + solicitado_em.

### Model `ControleExportacaoCSV`

**Descrição:** Artefato de lock/controle fail-fast para extrações críticas.

**Campos principais:**
- solicitacao (OneToOne SolicitacaoExportacao), caminho_arquivo, lock_token, status_lock, criado_em, validado_em, mensagem_erro

**Métodos / propriedades de domínio:**
- validar_precondicoes_io(): confirma existência/criação do arquivo de controle, permissões e lock exclusivo antes da extração pesada.

**Constraints / índices / observações:**
- OneToOne com a solicitação de exportação.

## 4. Regras transversais entre apps

- Identidade única: PerfilAluno e PerfilProfessor sempre penduram em CustomUser; nunca criar dois usuários para a mesma pessoa.
- Dependente com credencial: o dependente usa o próprio CustomUser para login, mas a responsabilidade financeira fica em VinculoResponsavelAluno e Assinatura.
- Professor que também treina: um único CustomUser pode ter PerfilProfessor e PerfilAluno, inclusive com BeneficioFinanceiro de 100%.
- Hard stop antes da câmera: T04 deve consultar o backend para elegibilidade de check-in; o backend decide com base em PerfilAluno, Assinatura, TrancamentoMatricula, ReservaVaga e SessaoAula.
- Pausa de matrícula: TrancamentoMatricula impacta financeiro, presença e graduação ao mesmo tempo; a mudança coordenada deve ocorrer em service transacional.
- LGPD: anonimização percorre accounts + clientes + arquivos anexos + trilha de auditoria, preservando apenas o mínimo legal e financeiro necessário.
- Exportação fail-fast: antes de qualquer query pesada, ControleExportacaoCSV precisa validar lock/arquivo de controle e registrar auditoria.

## 5. O que deve ficar fora dos models

- Integração direta com Stripe API, pause_collection e Customer Portal: service do app pagamentos/financeiro.
- Onboarding completo de titular + dependente + assinatura + aceite de termos: service transacional.
- Processamento de webhook com validação de assinatura, idempotência e efeitos colaterais: handler/service.
- Abertura da câmera e UX do QR: frontend progressivo + endpoint backend de pré-validação.
- Consultas analíticas de dashboard: selectors/querysets otimizados, não properties que disparem N+1.

> **Nota:** Regra orientadora do AGENTS: model gordo não significa model onipotente. Invariantes locais ficam na model; orquestração entre agregados e integrações externas ficam em services, tasks e selectors.

## 6. Ajustes importantes em relação ao rascunho inicial

- Comunicação foi reposicionada para o app core, porque a spec final não mantém um app comunicacao/ separado.
- dashboard foi tratado como app preferencialmente sem models transacionais obrigatórios.
- O vínculo de dependência deixou de ser um self-FK em PerfilAluno e passou a usar VinculoResponsavelAluno, permitindo responsável sem treino.
- A integração Stripe foi enxugada: o documento privilegia dj-stripe para espelho do gateway e mantém no app pagamentos apenas o rastreamento específico do negócio.
- PDV foi aprofundado com ProdutoPDV, VendaPDV e ItemVendaPDV, cobrindo estoque local e operação real do balcão.
- Graduação ganhou models de evento de exame, além do histórico contínuo por faixa.

## 7. Ordem sugerida de implementação

- Fase A: accounts + clientes (CustomUser, UserRoleAssignment, PerfilAluno, VinculoResponsavelAluno, ProntuarioEmergencia, AceiteTermo).
- Fase B: financeiro + pagamentos mínimos (PlanoFinanceiro, BeneficioFinanceiro, Assinatura, AssinaturaAluno, FaturaMensal, CheckoutSolicitacao, WebhookProcessamento).
- Fase C: presenca_graduacao (Modalidade, FaixaIBJJF, Turma, SessaoAula, ReservaVaga, PresencaFisica, HistoricoGraduacao).
- Fase D: trancamento, PDV, caixa, exames de graduação, comunicações e relatórios/auditoria.
- Fase E: snapshots de dashboard e refinamentos de performance somente quando medição justificar.

> **Nota:** Essa ordem reduz retrabalho: primeiro a identidade e o contrato local, depois presença/graduacao, depois operação avançada.

## Apêndice V10 — Otimizações de Performance PostgreSQL e Concorrência

Estas notas complementam a modelagem principal com diretrizes de implementação focadas em performance e previsibilidade em produção. Elas não alteram o domínio do sistema, mas devem orientar a escrita do código e das migrações.

### 1. Índice GIN para `Turma.dias_semana`

Como `Turma.dias_semana` usa `ArrayField` no PostgreSQL, a implementação deve prever um `GinIndex(fields=['dias_semana'])` em `Meta.indexes` para acelerar buscas como “quais turmas acontecem na segunda-feira” e evitar *full table scan* na montagem da grade horária.

### 2. Ordenação padrão por `created_at` com uso criterioso

O `BaseModel` deve permitir `ordering = ['-created_at']` nas entidades em que “mais recentes primeiro” seja a leitura natural do negócio. Essa convenção melhora a previsibilidade do ORM em telas administrativas, auditorias, histórico de eventos e filas operacionais. Porém, ela não deve ser aplicada cegamente a toda model; cada caso deve avaliar o custo de ordenação e a necessidade real da query.

### 3. Lock pessimista também no `CaixaTurno`

O mesmo padrão de concorrência usado em `ReservaVaga` deve ser aplicado aos services que consolidam `VendaPDV` e `MovimentacaoCaixa`. Sempre que o saldo apurado do caixa puder ser alterado por dois operadores ou processos ao mesmo tempo, o service deve abrir `transaction.atomic()`, carregar o `CaixaTurno` com `select_for_update()` e só então recalcular e aplicar a movimentação financeira.

### 4. Backlog de implementação associado

- `presenca_graduacao/models.py`: adicionar `GinIndex(fields=['dias_semana'])` em `Turma.Meta.indexes`.
- `core/models.py`, `financeiro/models.py`, `relatorios/models.py` e demais apps com histórico temporal: avaliar `ordering = ['-created_at']` apenas onde o acesso por recência for comportamento natural.
- `financeiro/services.py`: consolidar vendas e caixa com `transaction.atomic()` + `select_for_update()` no `CaixaTurno`, evitando condição de corrida em saldo final apurado.

