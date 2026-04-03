# Documento Único de Mapeamento de Forms e Serializers
## Sistema LV JIU JITSU - Blueprint Estrutural da Camada de Validação (Django Forms + DRF)

**Data:** 18/03/2026  
**Stack-alvo:** Django 5.x/6.x (Forms / ModelForms) · Django REST Framework (Serializers) · HTMX

### Objetivo
Definir a camada de validação do sistema como uma “alfândega” de entrada: limpar dados, normalizar formatos, validar dependências entre campos e bloquear payloads incorretos ou maliciosos antes que alcancem Views e Services.

---

## 1. Regras de Ouro da Camada de Validação

- **Proibição do over-posting.** É terminantemente proibido usar `fields = '__all__'` em ModelForms ou ModelSerializers. Os campos aceitos devem ser declarados explicitamente para impedir injeção de atributos sensíveis como `is_staff`, status administrativo ou saldo.
- **Alfândega de negócio.** Regras de dependência entre campos devem viver no `clean()` dos Forms ou no `validate()` dos Serializers. Exemplo: se o aluno for menor de idade, o responsável e o aceite do termo passam a ser obrigatórios.
- **Limpeza e normalização rigorosa.** Máscaras de frontend nunca devem chegar ao banco. CPF, telefone e outros identificadores devem ser saneados com regex nos métodos `clean_<campo>()` ou `validate_<campo>()`.
- **Camada passiva.** Forms e Serializers não orquestram Stripe, check-in, graduação ou regras de concorrência. O `save()` apenas consolida `cleaned_data` ou `validated_data` e repassa para a camada de Services.
- **Morte dos vazamentos no soft delete.** Campos de seleção devem obrigatoriamente consumir querysets com `.ativos()` para impedir que planos cancelados, usuários inativos ou turmas desativadas apareçam em dropdowns e APIs.
- **Proteção de leitura versus escrita.** Campos exibidos ao utilizador, mas imutáveis no fluxo, precisam de proteção real no backend. Em Forms MVT, use `disabled = True`; em Serializers DRF, use `read_only=True`.

## 2. Infraestrutura Transversal

### 2.1. Padrão HTMXBaseForm
- **Objetivo.** Permitir a injeção de atributos HTMX diretamente nos widgets para validação inline e interações parciais sem JavaScript customizado excessivo.
- **Regra prática.** Criar uma classe base `HTMXModelForm` para centralizar `attrs` como `hx-post`, `hx-get`, `hx-target`, classes visuais e convenções de resposta parcial.
- **Uploads via HTMX.** Sempre que um formulário submetido com HTMX contiver ficheiros, a tag `<form>` deve declarar obrigatoriamente `hx-encoding="multipart/form-data"`; sem isso, o HTMX não envia o arquivo e a validação cairá em falso negativo de campo obrigatório.

### 2.2. Validador Universal de Uploads (MediaValidator)
- **Objetivo.** Bloquear ficheiros incompatíveis, muito grandes ou perigosos em Selfie, Comprovativo e demais anexos.
- **Regra prática.** Todo Form ou Serializer que aceite uploads deve aplicar `FileExtensionValidator` com lista branca de extensões e validar tamanho máximo no `clean_arquivo()` ou `validate_arquivo()`.
- **Padrão de referência.** Limite sugerido de 5 MB por upload e extensões restritas a `jpg`, `jpeg`, `png` e `pdf`, salvo exceções aprovadas pela arquitetura.
- **Otimização opcional recomendada.** Para imagens, além do limite de tamanho bruto, aplicar redimensionamento e regravação otimizada com Pillow quando o caso de uso for avatar/selfie.

### 2.3. FormSets com Validação em Memória
- **Objetivo.** Impedir duplicações que ainda não existem no banco, mas foram submetidas duas vezes na mesma requisição.
- **Regra prática.** Todo FormSet com risco de duplicidade de CPF, e-mail ou documento deve herdar de `BaseFormSet`/`BaseInlineFormSet` e sobrescrever `clean()` para varrer os formulários em memória antes do `save()`.
- **Exemplo crítico.** No onboarding de dependentes, dois formulários com o mesmo CPF devem disparar `ValidationError` no FormSet, em vez de deixar a falha estourar como quebra de `UniqueConstraint` no PostgreSQL.

### 2.4. Injeção Segura do Utilizador no DRF
- **Objetivo.** Garantir que o utilizador autenticado entre no `validated_data` sem confiar em campos enviados pelo frontend.
- **Regra prática.** Serializers que dependem do ator logado devem declarar um `HiddenField(default=CurrentUserDefault())` para capturar `request.user` de forma invisível e inviolável.
- **Benefício.** O service recebe um payload completo e seguro, sem depender de `aluno_uuid`, `usuario_uuid` ou identificadores manipuláveis no corpo do request.


### 2.5. Localização de Decimais e Inputs Monetários
- **Objetivo.** Garantir que valores monetários digitados com vírgula em interfaces lusófonas sejam interpretados corretamente antes de chegar ao banco.
- **Regra prática.** Em Forms MVT que recebam dinheiro, preferir `DecimalField(localize=True)` ou `localized_fields` no `ModelForm`. Quando o widget ou fluxo exigir tratamento manual, normalizar explicitamente no `clean_<campo>()` antes de repassar ao service.
- **Exemplo crítico.** `saldo_inicial`, `valor_pago` e campos análogos não podem aceitar parsing ambíguo que transforme `150,50` em valor inválido ou em `15050`.

### 2.6. Otimização Preventiva de Imagens com Pillow
- **Objetivo.** Evitar que imagens válidas em tamanho de arquivo, mas exageradas em resolução, encareçam storage, tráfego e renderização de telas administrativas.
- **Regra prática.** Em `clean_foto_selfie()` e fluxos equivalentes, além da validação de extensão e tamanho, abrir a imagem em memória com Pillow, limitar a resolução máxima (por exemplo, 800x800), regravar em formato otimizado e só então devolver o objeto normalizado ao restante da aplicação.
- **Escopo.** Esta otimização deve ocorrer na camada de validação, antes do `save()` do form ou do serializer, sempre que o caso de uso envolver avatar, selfie ou comprovante de imagem.


### 2.7. Robustez de Imagem, `null` no DRF e Concorrência de Unicidade
- **Objetivo.** Blindar a camada de validação contra arquivos corrompidos, atritos de integração JSON e falsos positivos de unicidade sob concorrência.
- **Imagem inválida ou corrompida.** Sempre que `clean_foto_selfie()` ou fluxo equivalente usar Pillow, a leitura da imagem deve ficar dentro de `try/except` capturando `PIL.UnidentifiedImageError` e `OSError`/`IOError`, convertendo a falha em `ValidationError` amigável. O nome do arquivo ou a extensão nunca são prova suficiente de que o conteúdo é uma imagem real.
- **Texto opcional vindo como `null` no DRF.** Para reduzir atrito com frontends que enviam `null` em JSON, serializers podem aceitar `allow_blank=True` e, quando houver necessidade explícita de compatibilidade, `allow_null=True`; nesses casos, o `validate_<campo>()` deve normalizar `None` para string vazia `""` antes de encaminhar ao service, preservando a convenção do banco.
- **Unicidade em concorrência.** `clean()`, `validate()` e verificações prévias de existência são apenas primeira linha de defesa. A camada de Services deve continuar preparada para capturar `IntegrityError` do PostgreSQL e devolver erro funcional ao utilizador quando uma corrida de concorrência ultrapassar a validação prévia.

## 3. Mapeamento por App

### 3.1. App accounts (Autenticação e LGPD)

#### CustomLoginForm (MVT / allauth)
- **Função.** Substitui o login por e-mail/username por autenticação via CPF.
- **Validação.** No `clean_login()`, remove pontos e traços antes de autenticar, garantindo comparação com o CPF normalizado no banco.

#### SolicitarLGPDForm (MVT)
- **Função.** Confirma a intenção de iniciar o fluxo de anonimização/exclusão.
- **Validação.** Exige `senha_confirmacao` e, no `clean()`, verifica se a senha corresponde ao utilizador autenticado, evitando exclusão acidental em sessão aberta.

### 3.2. App clientes (Onboarding Wizard)

**Nota estrutural.** O onboarding é dividido em Forms menores coordenados por `SessionWizardView`. O banco só deve ser tocado no final do wizard.

#### OnboardingTitularForm (MVT)
- **Campos.** CPF, nome, data de nascimento, telefone e demais dados básicos do titular.
- **Validação.** No `clean_cpf()`, verificar existência prévia e lançar `ValidationError` imediata se o CPF já estiver cadastrado.

#### OnboardingDependenteFormSet (MVT)
- **Função.** Permite cadastrar múltiplos dependentes em sequência, preferencialmente via `inlineformset_factory` ou estrutura equivalente.
- **Validação individual.** Se `data_nascimento` indicar menoridade, exige `aceite_responsavel` ou documento equivalente no formulário.
- **Validação em lote.** O `clean()` do FormSet deve procurar CPFs, documentos ou combinações duplicadas entre os próprios formulários submetidos na mesma requisição.

#### ProntuarioEmergenciaForm (MVT)
- **Campos.** Tipo sanguíneo, alergias, lesões prévias e contato de emergência.
- **Validação.** Sem dependências complexas; foco em texto limpo e obrigatoriedade dos campos críticos para visão rápida no tatame.

#### PerfilUpdateForm (MVT)
- **Função.** Atualizar dados de contacto e selfie do utilizador/aluno sem permitir edição de campos imutáveis.
- **Proteção crítica.** Campos como `cpf` devem ser marcados com `self.fields['cpf'].disabled = True` no `__init__`, para que qualquer tentativa de adulteração no POST seja ignorada pelo Django.

### 3.3. App presenca_graduacao (Tatame e APIs de Alta Velocidade)

#### ReservaVagaSerializer (DRF)
- **Campos.** `sessao_uuid` e `usuario` oculto.
- **Validação.** No `validate()`, confirmar que o UUID existe e que a sessão pertence a uma aula futura e elegível para reserva.
- **Blindagem.** O utilizador deve entrar por `HiddenField(default=CurrentUserDefault())`, nunca por um campo editável enviado pelo frontend.
- **Nota.** Concorrência e contagem final de vagas pertencem ao Service.

#### CheckInCameraSerializer (DRF)
- **Campos.** `token_qr` lido pela câmera.
- **Validação.** Garantir que a string existe, não está vazia e segue o formato esperado do token. O consumo do token e o registro de presença não vivem no Serializer.

#### ExameGraduacaoForm (MVT)
- **Função.** Apoia o cadastro e a validação operacional de exame ou evento de graduação.
- **Validação.** No `clean()`, impedir `data_evento` no passado e exigir que a modalidade selecionada esteja ativa.

### 3.4. App financeiro e pagamentos (Dinheiro e Caixa)

#### TrancamentoMatriculaForm (MVT)
- **Campos.** `data_retorno_prevista` e `motivo`.
- **Validação cruzada.** Impedir data de retorno no passado e limitar o horizonte máximo conforme a regra da academia.

#### CaixaTurnoAberturaForm (MVT)
- **Campos.** `saldo_inicial`.
- **Validação.** Bloquear números negativos e garantir parsing monetário localizado, aceitando entrada com vírgula quando o formulário estiver configurado com `localize=True` ou normalização equivalente.

#### CheckoutPDVSerializer (DRF)
- **Campos.** Lista de itens (SKU e quantidade), `meio_pagamento` e `usuario` oculto.
- **Validação.** No `validate_itens()`, rejeitar lista vazia e confirmar que todos os SKUs existem em `ProdutoPDV.objects.ativos()`.
- **Blindagem.** O operador ou utilizador logado deve ser injetado com `HiddenField(default=CurrentUserDefault())`, nunca confiado ao payload do cliente.

#### ComprovativoManualForm (MVT)
- **Função.** Receber comprovativos manuais de pagamento.
- **Validação.** Aplicar `MediaValidator` ativamente: apenas PDF/JPG/PNG permitidos, com tamanho máximo configurado.

#### ComprovativoManualSerializer (DRF)
- **Função.** Alternativa de envio via API para anexos financeiros.
- **Validação.** O remetente autenticado deve entrar como campo oculto e o arquivo deve respeitar os mesmos validadores de extensão e tamanho definidos para o MVT.

### 3.5. App relatorios (Exportações)

#### FiltroExportacaoForm (MVT)
- **Campos.** `data_inicio`, `data_fim` e `tipo_relatorio`.
- **Validação.** Garantir que `data_fim` seja maior ou igual a `data_inicio` e limitar o intervalo máximo para proteger o banco de consultas exageradas.

## 4. Avisos de Trincheira para Implementação

- **Cegueira dos FormSets.** Validar apenas cada formulário isoladamente não basta. Duplicidades entre formulários da mesma requisição precisam ser barradas no `clean()` do FormSet.
- **Armadilha do instance no Serializer.** Em updates via DRF, o Serializer deve ser instanciado com a instância atual. Sem isso, o framework tentará criar um novo registro em vez de atualizar o existente.
- **`partial=True` e validações obrigatórias.** Em `PATCH`, regras que dependem de dois campos devem usar fallback para valores já existentes na instância, evitando `KeyError` e falsos negativos.
- **`clean()` global não pode assumir campos presentes.** Como `clean_<campo>()` pode falhar antes, o campo pode desaparecer de `cleaned_data`. Em validações cruzadas de Forms, use sempre `self.cleaned_data.get('campo')` e teste `None` antes de depender do valor, evitando `KeyError` e erro 500.
- **Senhas em clear-text no Serializer.** Qualquer serializer de alteração de senha deve declarar `password` como `write_only` para impedir vazamento em respostas de leitura.
- **Booleanos em HTML.** Checkboxes não marcados não vêm no POST. A validação deve confiar em `cleaned_data.get('campo', False)` e nunca em `request.POST['campo']`.
- **Strings falsas em `multipart/form-data` no DRF.** Em payloads de upload, flags como `aceita_termos` podem chegar como texto. Regras de validação não devem depender de `if data.get('campo'):` sem coerção explícita; o serializer precisa confiar no parser correto do DRF ou converter o valor antes de aplicar regras condicionais.
- **O “falso .jpg” não pode derrubar o backend.** `FileExtensionValidator` filtra nome/extensão, mas não garante integridade binária. Toda abertura de imagem com Pillow precisa capturar erro de arquivo inválido/corrompido e convertê-lo em `ValidationError`, nunca em erro 500.
- **`null` versus string vazia nas APIs.** Quando o frontend enviar `null` para campo textual opcional, o serializer deve ter estratégia explícita: ou rejeita por contrato, ou aceita e normaliza para `""`. O sistema não pode deixar essa decisão implícita.
- **Validação de unicidade não elimina corrida de banco.** Mesmo após `clean_cpf()` e `validate()`, o código final precisa estar pronto para tratar `IntegrityError` em concorrência real e devolver mensagem educada ao utilizador.
- **Campos “readonly” apenas no HTML não são segurança.** Em MVT, um `readonly` no template pode ser removido pelo navegador; a proteção real é `disabled=True` no Form. Em DRF, o equivalente é `read_only=True`, fazendo o campo aparecer no GET, mas ser ignorado em `POST`, `PUT` e `PATCH`.
- **Utilizador logado não vem do frontend.** Em APIs DRF, campos que representam o ator autenticado devem entrar por `CurrentUserDefault()` e não por UUID enviado no payload.

## 5. Conclusão e Separação de Responsabilidades

- **Models.** Guardam invariantes do banco e restrições estruturais.
- **Views.** Orquestram HTTP, permissão, contexto e encaminhamento para Services.
- **Forms e Serializers.** Normalizam, saneiam e validam entrada.
- **Services.** Concentram regras de negócio, concorrência, integrações externas e *side effects*.