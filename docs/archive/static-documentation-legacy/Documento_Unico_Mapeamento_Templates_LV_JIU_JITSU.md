# Documento Único de Mapeamento de Telas e Requisitos
## Sistema LV JIU JITSU — versão consolidada para levantamento de requisitos
Data: 17/03/2026
### Objetivo
Consolidar em um único documento as informações espalhadas nos arquivos de planejamento e nas telas já mapeadas, normalizando inconsistências e adicionando telas/funcionalidades faltantes para apoiar a implementação.
### Resumo executivo
- Os arquivos enviados descrevem bem 7 telas macro, mas o planejamento do sistema já pressupõe subtelas operacionais que ainda não estavam formalmente mapeadas.
- Foram normalizadas inconsistências de nomenclatura e modelagem para que o documento sirva como base real de implementação e levantamento de requisitos.
- O documento também incorpora telas e fluxos faltantes que hoje aparecem apenas como links, templates, ações internas ou dependências indiretas.
- Esta revisão incorpora refinamentos operacionais na T04, T10 e T11 para lidar com inadimplência preventiva no check-in e com usuários de múltiplos papéis no mesmo CPF.

## 1. Decisões de consistência adotadas
- **Identificador de login:** Padronizar autenticação por CPF como `USERNAME_FIELD` do usuário. E-mail permanece como contato secundário.
- **Modelo de usuário:** Separar credencial de autenticação do perfil de negócio. Um mesmo `CustomUser` pode acumular papéis e vínculos de jornada.
- **Papéis de acesso:** Padronizar ADMIN, PROFESSOR, ALUNO e RESPONSÁVEL. O responsável é necessário porque o onboarding prevê titular que não treina.
- **Autorização real:** Não tratar papel como enum exclusivo. A autorização deve aceitar múltiplos papéis simultâneos por usuário, com acúmulo de permissões por grupo/regra.
- **Nomenclatura de papéis:** `role` pode existir como rótulo legado, mas a camada de autorização deve operar por vínculos/papéis acumuláveis e não por um único campo rígido.
- **Status de acesso:** Padronizar quatro estados visíveis: ATIVO, PENDENTE_FINANCEIRO, PAUSADO e BLOQUEADO. O campo técnico `is_active` continua sendo base de autenticação, enquanto o estado PAUSADO representa trancamento operacional/financeiro sem cancelamento definitivo do vínculo.
- **Presença:** A unicidade de presença deve ser por `aluno + sessao_aula`. Não pode depender apenas do token/`qr_code` rotativo.
- **Pré-validação de presença:** O front deve validar elegibilidade de acesso antes de abrir câmera/WebRTC. Em inadimplência ou bloqueio, a interface deve interromper o fluxo antes da leitura do QR.
- **Graduação:** Separar regras oficiais IBJJF (idade, faixas possíveis) de regras configuráveis da academia (carência interna, frequência mínima, critérios extras).
- **Dependentes:** Dependentes são perfis de aluno vinculados a um responsável financeiro. O responsável pode ou não ser também um aluno. Dependentes acima de uma idade configurável podem receber credencial própria, com escopo restrito ao dashboard do aluno e sem gestão financeira.
- **Professor também aluno:** O mesmo CPF pode existir simultaneamente como professor e aluno, inclusive com plano financeiro, bolsa ou desconto de 100%, sem duplicar usuário.
- **Comprovantes e contratos:** Upload, validação, aceite de termos e histórico contratual precisam de tela/fluxo próprio, não apenas de botões soltos.

## 2. Atores do sistema
- **Visitante:** Vê landing page, horários, planos e agenda aula experimental.
- **Responsável:** Cadastra grupo familiar, paga, acompanha dependentes, atualiza dados e envia comprovantes.
- **Aluno:** Registra presença, acompanha graduação, visualiza financeiro e seus dados.
- **Professor:** Inicia aula, gera sessão/QR, controla presença, acompanha aptidão à graduação.
- **Administrador:** Gerencia cadastros, financeiro, contratos, turmas, relatórios, permissões, auditoria e graduação.

## 3. Fluxo macro do produto
1. Visitante acessa a landing page, consulta horários e planos e pode registrar interesse em aula experimental.
2. O cadastro é iniciado por CPF, cria credencial, perfil principal e dependentes dentro de transação atômica.
3. Após o cadastro, o fluxo obrigatoriamente segue para seleção de plano e checkout. O acesso só é liberado após confirmação financeira.
4. Com assinatura ativa, o usuário é roteado conforme papel para seu dashboard.
5. O professor inicia a aula, abre uma SessaoAula e o sistema passa a rotacionar tokens de QR para check-in.
6. O aluno registra presença; o backend valida vínculo, status de acesso, aula ativa e tentativa duplicada.
7. A graduação é acompanhada continuamente por regras oficiais e critérios internos; quando apto, segue para avaliação e promoção.
8. Inadimplência, bloqueios, reativações, comprovantes e auditoria formam um fluxo transversal entre financeiro, accounts e dashboards.

## 4. Inventário consolidado de telas

### T01 — Landing Page Pública e Portal de Login (Confirmada)
**Objetivo:** Apresentar a academia, capturar leads e oferecer entrada segura ao sistema.

**Perfis:** Visitante, Aluno, Responsável, Professor, Administrador

**Módulos:** core, accounts, financeiro, presenca_graduacao

**Dados exibidos / consumidos:**
- Conteúdo institucional, horários de turma e planos públicos.
- Formulário de login por CPF + senha.
- CTA para cadastro e CTA para aula experimental.
**Ações do usuário:**
- Entrar no sistema.
- Ir para cadastro.
- Agendar aula experimental.
- Acessar recuperação de senha.
**Regras de negócio e validações:**
- Autenticação primária por CPF.
- Redirecionamento por papel após login.
- Bloqueio imediato de usuário inativo/bloqueado.
- Mensagens distintas para credencial inválida e acesso bloqueado.
**Estados e exceções relevantes:**
- Público sem login.
- Erro de autenticação.
- Usuário bloqueado/inadimplente.
- Sem turmas ou planos ativos para exibição.
**Endpoints / rotas:**
- `GET /`
- `POST /accounts/login/`
- `POST /core/agendar-aula/`

### T02 — Onboarding e Cadastro de Clientes (Confirmada)
**Objetivo:** Cadastrar titular, dependentes, prontuário básico e credenciais de acesso.

**Perfis:** Visitante, Responsável, Aluno maior de idade

**Módulos:** accounts, clientes

**Dados exibidos / consumidos:**
- Tipo de cadastro: aluno maior, responsável, aluno e responsável.
- Dados pessoais, contato, selfie, histórico marcial e dependentes.
- Termos de uso de imagem e responsabilidade.
**Ações do usuário:**
- Avançar/voltar no wizard.
- Validar CPF em tempo real.
- Cadastrar dependentes.
- Finalizar cadastro e seguir para checkout.
**Regras de negócio e validações:**
- Processo inteiro em transaction.atomic.
- CPF único por pessoa.
- Se for menor de 18 anos, exige responsável.
- Dependentes acima de uma idade configurável (`idade_credencial_propria`) podem receber senha própria atrelada ao próprio CPF, com escopo restrito.
- Selfie sanitizada e comprimida.
- Aceite obrigatório dos termos.
**Estados e exceções relevantes:**
- Rascunho em andamento.
- Erro de CPF duplicado.
- Erro em dependente invalida todo o fluxo.
- Cadastro concluído e redirecionado ao checkout.
**Endpoints / rotas:**
- `GET /accounts/cadastro/`
- `POST /accounts/api/validar-cpf/`
- `POST /accounts/cadastro/finalizar/`

### T03 — Seleção de Planos e Checkout Financeiro (Confirmada)
**Objetivo:** Vincular o grupo familiar a um plano e ativar a assinatura recorrente.

**Perfis:** Responsável, Aluno maior de idade, Administrador

**Módulos:** financeiro, pagamentos, clientes

**Dados exibidos / consumidos:**
- Grupo familiar, planos ativos, descontos, taxa de adesão e vencimento.
- Status da assinatura, método de pagamento e mensagens de retorno do gateway.
**Ações do usuário:**
- Selecionar plano.
- Revisar pedido.
- Pagar com cartão/Stripe ou Pix Automático.
- Repetir tentativa em caso de falha.
**Regras de negócio e validações:**
- Assinatura nasce como INCOMPLETA até confirmação assíncrona.
- Ativação do acesso ocorre somente após webhook de sucesso.
- Falha de pagamento mantém o usuário fora dos dashboards internos.
- Sessão de checkout deve carregar metadados do titular e dos dependentes.
**Estados e exceções relevantes:**
- Checkout inicial.
- Pagamento em processamento.
- Pagamento confirmado.
- Pagamento falho/cancelado.
**Endpoints / rotas:**
- `GET /financeiro/planos/`
- `POST /pagamentos/create-checkout-session/`
- `POST /pagamentos/webhook/stripe/`

### T04 — Dashboard do Aluno / Responsável (Confirmada com ampliação)
**Objetivo:** Ser a central de autogestão do praticante e, quando houver, do responsável financeiro.

**Perfis:** Aluno, Responsável

**Módulos:** dashboard, clientes, presenca_graduacao, pagamentos, financeiro

**Dados exibidos / consumidos:**
- Identidade marcial, status de acesso, motivo do bloqueio, faixa, graus, progresso e presença.
- Faturas próprias e de dependentes.
- Próximas turmas compatíveis com o perfil.
- CTA contextual de regularização quando houver pendência.
**Ações do usuário:**
- Escanear QR de presença.
- Fazer check-in prévio / reservar vaga em turmas com lotação.
- Trocar entre perfis de dependentes.
- Pagar/regularizar pendência.
- Consultar status de matrícula pausada/trancada.
- Enviar comprovante.
- Atualizar dados pessoais.
**Regras de negócio e validações:**
- Regra de graduação varia conforme faixa etária.
- Não permite check-in duplicado na mesma sessão.
- Responsável visualiza dependentes sem necessidade de novo login.
- A sessão para portal de cobrança Stripe deve ser gerada sob demanda.
- Antes de abrir a câmera/WebRTC, o sistema deve validar o status de acesso do aluno alvo do check-in.
- Se o status estiver `PENDENTE_FINANCEIRO` ou `BLOQUEADO`, a câmera não pode ser inicializada e o front deve exibir modal de hard stop: “Seu acesso está suspenso devido a pendências financeiras. Clique aqui para regularizar.”
- O CTA do modal deve levar para a regularização no próprio dashboard (faturas em aberto) ou para a sessão temporária do portal de cobrança.
- A mesma lógica deve valer para dependentes: o responsável só pode acionar check-in para um dependente elegível.
- Se o aluno estiver com matrícula `PAUSADA`, o QR também deve ser bloqueado antes da câmera, com mensagem específica de matrícula trancada e orientação para procurar a recepção/administração ou aguardar a data de reativação.
- Em turmas com reserva prévia habilitada, o QR na porta apenas confirma presença física de reserva já existente; aluno sem reserva válida deve ser barrado com feedback claro antes do fluxo de leitura.
**Estados e exceções relevantes:**
- Acesso ativo.
- Pendente financeiro com hard stop antes da câmera.
- Matrícula pausada com hard stop antes da câmera.
- Bloqueado manualmente.
- Sem aula ativa para check-in.
- Reserva obrigatória ausente para turma lotada.
- QR inválido/expirado.
**Critérios de aceite recomendados:**
- Usuário adimplente consegue abrir câmera e seguir para leitura do QR.
- Usuário inadimplente não aciona `getUserMedia`, não vê prompt de câmera e recebe modal com CTA de regularização.
- Dependente inadimplente bloqueia somente o check-in daquele perfil, sem derrubar a sessão do responsável.
- Após regularização confirmada, o status volta a permitir check-in sem novo cadastro ou intervenção manual indevida.
- Aluno com matrícula pausada não consegue abrir câmera nem registrar presença até reativação efetiva da matrícula.
**Endpoints / rotas:**
- `GET /dashboard/aluno/`
- `GET /presenca/api/precheck/`
- `POST /presenca/api/registrar/`
- `GET /pagamentos/portal-session/`

### T05 — Dashboard do Professor (Confirmada)
**Objetivo:** Operar a aula em tempo real e acompanhar alunos sob sua responsabilidade.

**Perfis:** Professor, Administrador

**Módulos:** dashboard, presenca_graduacao, professores

**Dados exibidos / consumidos:**
- Turmas do professor, aula ativa, mural de presenças e alertas de graduação.
- Prontuário essencial dos alunos (sem financeiro).
**Ações do usuário:**
- Iniciar aula.
- Selecionar modalidade/turma.
- Gerar QR rotativo.
- Fazer check-in manual excepcional.
- Encerrar sessão de aula.
**Regras de negócio e validações:**
- Token de presença deve expirar e rotacionar.
- Professor só enxerga suas turmas e seus alunos.
- Check-in manual gera log de auditoria com motivo.
- Aula ativa registra tempo de permanência do professor.
**Estados e exceções relevantes:**
- Sem turma disponível.
- Aula ativa.
- QR expirado e regenerado.
- Lotação máxima atingida.
**Endpoints / rotas:**
- `POST /presenca/api/gerar-sessao/`
- `GET /professores/minhas-turmas/`
- `POST /presenca/confirmar-manual/`

### T06 — Dashboard Administrativo (Confirmada)
**Objetivo:** Centralizar inteligência de negócio, cadastros, bloqueios e visão financeira.

**Perfis:** Administrador

**Módulos:** dashboard, financeiro, pagamentos, clientes, accounts

**Dados exibidos / consumidos:**
- KPIs de receita, evasão, presença, crescimento e inadimplência.
- Pendências operacionais, bloqueios e comprovantes pendentes.
**Ações do usuário:**
- Bloquear/desbloquear acesso.
- Baixar fatura manual.
- Gerenciar permissões.
- Acessar relatórios e telas de manutenção.
**Regras de negócio e validações:**
- Ações críticas geram auditoria.
- Busca global por CPF, nome, faixa e responsável.
- Indicadores devem respeitar filtros por período.
- Integração com Stripe deve sincronizar status local.
**Estados e exceções relevantes:**
- Visão geral sem filtros.
- Com filtros aplicados.
- Pendências críticas destacadas.
- Falha de sincronização com gateway.
**Endpoints / rotas:**
- `GET /dashboard/admin/stats/`
- `POST /financeiro/baixar-fatura-manual/`
- `POST /financeiro/trancar-matricula/`
- `POST /financeiro/reativar-matricula/`
- `POST /accounts/gerenciar-permissoes/`

### T07 — Painel de Graduação e Promoção de Faixas (Confirmada)
**Objetivo:** Gerenciar elegibilidade, avaliação e histórico de graduação.

**Perfis:** Professor, Administrador

**Módulos:** presenca_graduacao, clientes

**Dados exibidos / consumidos:**
- Lista de elegíveis, monitor de assiduidade, histórico imutável e avaliador.
**Ações do usuário:**
- Filtrar elegíveis.
- Abrir modal de promoção.
- Registrar faixa/grau.
- Gerar certificado.
**Regras de negócio e validações:**
- Validação de idade/faixa via clean().
- Regras infantis e adultas distintas.
- Toda promoção cria histórico e encerra ciclo anterior.
- Frequência mínima é critério configurável da academia.
- O tempo de graduação/carência deve contar apenas períodos de vínculo ativo em treino; intervalos com matrícula `PAUSADA` (trancamento) congelam o relógio de elegibilidade até a reativação.
**Estados e exceções relevantes:**
- Aluno não elegível.
- Elegível aguardando avaliação.
- Promoção concluída.
- Promoção negada/adiada.
- Elegibilidade congelada por matrícula pausada.
**Endpoints / rotas:**
- `GET /graduacao/aptos/`
- `POST /graduacao/registrar-promocao/`

### T08 — Recuperação de Senha e Primeiro Acesso (Tela faltante obrigatória)
**Objetivo:** Fechar o fluxo já referenciado no login e garantir recuperação segura de conta.

**Perfis:** Todos os usuários autenticáveis

**Módulos:** accounts, notificacoes (futuro)

**Dados exibidos / consumidos:**
- CPF/e-mail de recuperação, token temporário, nova senha.
**Ações do usuário:**
- Solicitar recuperação.
- Receber instrução por canal configurado.
- Definir nova senha.
- Finalizar primeiro acesso.
**Regras de negócio e validações:**
- Resposta uniforme para evitar enumeração de contas.
- Token expira e é de uso único.
- Primeiro acesso pode exigir troca de senha provisória.
- Eventos de recuperação devem gerar log.
**Estados e exceções relevantes:**
- Solicitação enviada.
- Token inválido/expirado.
- Senha redefinida.
- Conta bloqueada para suporte.
**Endpoints / rotas:**
- `GET /accounts/esqueci-senha/`
- `POST /accounts/esqueci-senha/`
- `GET/POST /accounts/redefinir-senha/<token>/`

### T09 — Meu Perfil e Configurações de Conta (Tela faltante obrigatória)
**Objetivo:** Permitir manutenção dos dados do próprio usuário sem depender de dashboard específico.

**Perfis:** Aluno, Responsável, Professor, Administrador

**Módulos:** accounts, clientes, professores

**Dados exibidos / consumidos:**
- Dados pessoais, foto/selfie, contatos, senha, consentimentos e preferências.
**Ações do usuário:**
- Editar cadastro próprio.
- Trocar senha.
- Atualizar selfie/foto.
- Consultar termos aceitos.
- Solicitar exclusão definitiva de dados.
**Regras de negócio e validações:**
- CPF não editável sem fluxo administrativo.
- Mudança de dados sensíveis gera auditoria.
- Campos exibidos variam conforme papel.
- A solicitação de exclusão definitiva deve abrir fluxo formal de anonimização, com confirmação, registro de protocolo e prazo de processamento.
- A exclusão definitiva não pode quebrar contabilidade nem histórico financeiro; por isso, o backend deve anonimizar dados sensíveis (selfie, CPF identificável, dados médicos), preservando somente identificadores técnicos mascarados e vínculos mínimos exigidos por obrigação legal ou defesa do controlador.
**Estados e exceções relevantes:**
- Visualização.
- Edição.
- Alteração salva.
- Solicitação de exclusão aberta.
- Anonimização concluída.
- Erro de validação.
**Endpoints / rotas:**
- `GET /accounts/profile/`
- `POST /accounts/profile/`
- `POST /accounts/alterar-senha/`

### T10 — Gestão de Alunos e Dependentes (Tela faltante obrigatória)
**Objetivo:** Cobrir o CRUD citado no planejamento para o cadastro operacional de alunos.

**Perfis:** Administrador, Professor (consulta limitada)

**Módulos:** clientes, accounts, financeiro, presenca_graduacao

**Dados exibidos / consumidos:**
- Lista, detalhe, edição, status, responsável financeiro, turma, plano, faixa e vínculos de papel.
- Indicadores de matrícula ativa, elegibilidade para presença e resumo financeiro do aluno.
**Ações do usuário:**
- Listar, buscar, filtrar, criar, editar, desativar e reativar aluno.
- Vincular/desvincular dependente.
- Vincular um `CustomUser` já existente como aluno, sem criar novo CPF.
- Associar plano financeiro, bolsa, desconto parcial ou desconto de 100%.
- Trancar/pausar matrícula com motivo, data de início, data prevista de retorno e observações.
- Acessar histórico resumido.
**Regras de negócio e validações:**
- Exclusão lógica, nunca física.
- Professor sem acesso a dados financeiros sensíveis.
- Filtros por nome, CPF, faixa, status e responsável.
- CPF é único no nível do usuário. Antes de criar novo cadastro de aluno, o sistema deve pesquisar e reutilizar o `CustomUser` existente, quando houver.
- O mesmo usuário pode acumular simultaneamente os papéis de PROFESSOR e ALUNO.
- Um professor-aluno pode ser matriculado em turma de mestres/avançada e, ao mesmo tempo, permanecer alocado como docente em outras turmas.
- O vínculo financeiro do professor-aluno pode apontar para plano normal, bolsa ou desconto de 100%, mantendo histórico e regras de auditoria.
- O trancamento de matrícula deve alterar o status operacional do aluno para `PAUSADO`, bloquear o check-in por QR e registrar período, motivo e responsável pela ação.
- Dependendo da política da academia, o trancamento pode ter data final obrigatória e quantidade máxima por período contratual; essas restrições devem ser parametrizáveis.
**Estados e exceções relevantes:**
- Lista vazia.
- Cadastro ativo.
- Cadastro inativo.
- Dependente sem vínculo válido.
- Usuário existente vinculado com sucesso.
- Tentativa de duplicidade de CPF bloqueada.
- Matrícula pausada/trancada registrada com sucesso.
**Critérios de aceite recomendados:**
- Ao informar um CPF já cadastrado como professor, a tela deve oferecer vinculação ao perfil de aluno em vez de criar um segundo usuário.
- O mesmo CPF deve aparecer corretamente nos contextos de professor e aluno, respeitando permissões e jornadas distintas.
- Plano com desconto de 100% deve continuar registrando vínculo financeiro e motivo da concessão.
- Professor em consulta limitada não visualiza dados financeiros detalhados do aluno.
- Ao trancar a matrícula, o aluno passa a constar como `PAUSADO` em T10 e deixa de conseguir check-in em T04 até reativação.
**Endpoints / rotas:**
- `GET /clientes/`
- `GET/POST /clientes/novo/`
- `GET/POST /clientes/<id>/editar/`
- `POST /clientes/<id>/desativar/`
- `POST /clientes/<id>/vincular-usuario-existente/`

### T11 — Gestão de Professores (Tela faltante obrigatória)
**Objetivo:** Cobrir o CRUD operacional de professores e suas alocações.

**Perfis:** Administrador

**Módulos:** professores, accounts, presenca_graduacao, financeiro, clientes

**Dados exibidos / consumidos:**
- Dados pessoais, faixa, especialidade, status, carga horária, turmas e vínculos adicionais.
- Sinalização se o professor também é aluno, possui plano, bolsa ou desconto.
**Ações do usuário:**
- Criar, editar, ativar/desativar, vincular turmas e consultar carga horária.
- Vincular professor existente a uma jornada de aluno.
- Associar plano financeiro, bolsa ou desconto integral.
- Inserir o professor como aluno em turma de mestres/avançada.
**Regras de negócio e validações:**
- Não permitir professor em turmas conflitantes.
- Histórico de vínculo deve ser preservado.
- O cadastro de professor não pode forçar um novo CPF quando já existir `CustomUser` correspondente.
- A UI deve suportar dupla jornada: docente e aluno no mesmo usuário, sem duplicidade cadastral.
- Quando houver desconto de 100%, o sistema deve preservar o vínculo financeiro para fins de regra, histórico, renovação e auditoria.
- A alocação como professor e a matrícula como aluno devem ser independentes, mas compatíveis no mesmo calendário.
**Estados e exceções relevantes:**
- Ativo.
- Inativo.
- Sem turmas.
- Conflito de agenda.
- Professor também aluno.
- Tentativa de duplicidade de CPF bloqueada.
- Matrícula pausada/trancada registrada com sucesso.
**Critérios de aceite recomendados:**
- Um professor existente pode ser incluído como aluno sem criar segundo usuário.
- O painel exibe claramente a condição “professor também aluno” e o tratamento financeiro associado.
- Turma docente e turma de treino pessoal podem coexistir, desde que sem conflito operacional definido pela academia.
- A edição do professor preserva histórico de turmas e histórico financeiro vinculado.
**Endpoints / rotas:**
- `GET /professores/`
- `GET/POST /professores/novo/`
- `GET/POST /professores/<id>/editar/`
- `POST /professores/<id>/vincular-como-aluno/`

### T12 — Gestão de Turmas e Modalidades (Tela faltante obrigatória)
**Objetivo:** Criar e manter a malha de horários que alimenta landing, dashboards e presença.

**Perfis:** Administrador

**Módulos:** presenca_graduacao, professores

**Dados exibidos / consumidos:**
- Modalidade, turma, dias, horários, capacidade, professor responsável e status.
**Ações do usuário:**
- Cadastrar modalidade.
- Criar turma.
- Definir capacidade e horários.
- Vincular professor.
- Habilitar ou desabilitar reserva prévia / check-in prévio para turmas de alta demanda.
**Regras de negócio e validações:**
- Impedir sobreposição de professor.
- Controlar capacidade máxima.
- Desativação de turma não pode corromper histórico.
- Quando a turma usar reserva, a capacidade máxima deve ser consumida no momento da reserva, e não no momento da leitura do QR na porta.
- O QR Code da aula valida presença física de reserva existente; não deve funcionar como mecanismo primário de disputa por vaga em turmas lotadas.
**Estados e exceções relevantes:**
- Turma ativa.
- Turma inativa.
- Conflito de alocação.
- Sem professor vinculado.
- Reserva habilitada.
**Endpoints / rotas:**
- `GET /turmas/`
- `GET/POST /turmas/nova/`
- `GET/POST /modalidades/nova/`

### T13 — Financeiro Detalhado: Planos, Faturas e Inadimplência (Tela faltante obrigatória)
**Objetivo:** Materializar os CRUDs e listas financeiras já previstos no projeto.

**Perfis:** Administrador, Responsável, Aluno

**Módulos:** financeiro, pagamentos, clientes

**Dados exibidos / consumidos:**
- Planos, assinaturas, faturas, vencimentos, comprovantes e inadimplentes.
**Ações do usuário:**
- Criar/editar plano.
- Baixar fatura manual.
- Consultar inadimplentes.
- Renegociar ou reprocessar cobrança.
- Trancar/pausar matrícula com reflexo financeiro e data de retomada.
**Regras de negócio e validações:**
- Status financeiros padronizados: INCOMPLETA, ATIVA, PAST_DUE, CANCELADA, ENCERRADA.
- Assinatura e fatura têm ciclos distintos.
- Toda baixa manual exige evidência e auditoria.
- O trancamento deve aplicar `pause_collection` na assinatura Stripe quando houver assinatura recorrente elegível, sem cancelar o contrato.
- Como `pause_collection` pausa a cobrança mas não altera automaticamente o `subscription.status` para `paused`, o sistema deve manter um status local de negócio `PAUSADO` para governar acesso, dashboards e auditoria.
- Reativação deve remover a pausa de cobrança e restabelecer a elegibilidade operacional conforme a data efetiva de retorno.
**Estados e exceções relevantes:**
- Plano ativo/inativo.
- Fatura paga/pendente/atrasada/cancelada.
- Comprovante pendente de análise.
- Assinatura com cobrança pausada / matrícula trancada.
**Endpoints / rotas:**
- `GET /financeiro/planos/`
- `GET /financeiro/faturas/`
- `GET /financeiro/inadimplentes/`
- `POST /financeiro/baixar-fatura-manual/`
- `POST /financeiro/trancar-matricula/`
- `POST /financeiro/reativar-matricula/`

### T14 — Comprovantes, Contratos e Termos (Tela faltante obrigatória)
**Objetivo:** Concentrar tudo o que hoje aparece diluído entre cadastro, dashboards e admin.

**Perfis:** Responsável, Aluno, Administrador

**Módulos:** pagamentos, financeiro, accounts, clientes

**Dados exibidos / consumidos:**
- Arquivos anexados, status de validação, termos aceitos, contratos e certificados.
**Ações do usuário:**
- Enviar comprovante.
- Baixar contrato/termo/certificado.
- Aprovar ou reprovar comprovante.
- Consultar histórico documental.
**Regras de negócio e validações:**
- Versionar termos aceitos.
- Não sobrescrever anexos antigos.
- Admin deve registrar decisão sobre comprovante.
**Estados e exceções relevantes:**
- Anexo recebido.
- Em análise.
- Aprovado.
- Reprovado.
**Endpoints / rotas:**
- `GET /pagamentos/comprovantes/`
- `POST /pagamentos/upload-comprovante/`
- `GET /documentos/termos/`
- `GET /graduacao/certificado/<id>/`

### T15 — Relatórios, Auditoria e Exportações (Tela faltante obrigatória, com ajuste crítico)
**Objetivo:** Dar forma às consultas e relatórios que o dashboard resume, mas não substitui, incluindo exportações seguras para uso operacional e BI.

**Perfis:** Administrador, Professor (escopo restrito)

**Módulos:** dashboard, financeiro, presenca_graduacao, accounts

**Dados exibidos / consumidos:**
- Logs de ações, histórico de status, relatórios de presença, faturamento, graduação e evasão.
- Arquivos de exportação CSV/PDF e artefatos de controle da execução.
**Ações do usuário:**
- Filtrar por período.
- Exportar CSV/PDF.
- Auditar alterações críticas.
- Validar pré-condições da extração antes de liberar download ou processamento.
**Regras de negócio e validações:**
- Relatórios respeitam perfil de acesso.
- Ações críticas precisam exibir autor, data e antes/depois quando aplicável.
- **Fail-fast obrigatório em exportações críticas:** antes de gerar o CSV, o sistema deve validar a existência, acessibilidade e desbloqueio do arquivo de controle da execução.
- Se o arquivo de controle não existir, não puder ser criado, estiver bloqueado, corrompido ou indisponível no diretório esperado, a rotina deve encerrar imediatamente sem gerar CSV, sem continuar a leitura de dados e sem atualizar indicadores derivados.
- Toda tentativa abortada deve registrar log técnico com motivo, horário, operador e contexto da rotina.
- Exportações para BI devem gerar status final inequívoco: `SUCESSO`, `ABORTADA_PRE_VALIDACAO` ou `ERRO_PROCESSAMENTO`.
**Estados e exceções relevantes:**
- Sem resultado.
- Relatório consolidado.
- Exportação concluída.
- Exportação abortada por falha no arquivo de controle.
- Erro de processamento.
**Endpoints / rotas:**
- `GET /relatorios/presenca/`
- `GET /relatorios/financeiro/`
- `GET /auditoria/logs/`
- `POST /relatorios/exportar/validar-controle/`
- `POST /relatorios/exportar/csv/`

### T16 — Leads e Aula Experimental (Tela faltante recomendada)
**Objetivo:** Fechar o ciclo comercial já iniciado pela CTA pública da landing page.

**Perfis:** Visitante, Administrador/Recepção

**Módulos:** core, clientes (futuro CRM leve)

**Dados exibidos / consumidos:**
- Nome, contato, interesse, modalidade e status do lead.
**Ações do usuário:**
- Cadastrar lead.
- Marcar retorno.
- Converter lead em cadastro.
**Regras de negócio e validações:**
- A origem do lead deve ser armazenada.
- Conversão do lead deve reaproveitar dados no onboarding.
**Estados e exceções relevantes:**
- Novo.
- Contato realizado.
- Experimental agendada.
- Convertido.
- Perdido.
**Endpoints / rotas:**
- `POST /core/agendar-aula/`
- `GET /admin/leads/`
- `POST /admin/leads/<id>/converter/`


### T17 — PDV / Caixa Rápido (Tela complementar operacional)
**Objetivo:** Dar suporte à venda balcão de produtos físicos e serviços avulsos sem depender do checkout de assinaturas.

**Perfis:** Administrador, Recepção

**Módulos:** financeiro, loja (opcional), clientes

**Dados exibidos / consumidos:**
- Catálogo de produtos, itens mais vendidos, carrinho, meios de pagamento e identificação opcional do cliente.
**Ações do usuário:**
- Adicionar itens ao carrinho.
- Buscar aluno por CPF/nome ou lançar venda balcão.
- Receber em dinheiro, Pix ou cartão físico.
- Concluir venda e emitir comprovante simplificado.
**Regras de negócio e validações:**
- Toda venda concluída deve baixar estoque.
- Toda liquidação deve gerar movimentação no caixa do turno atual.
- Pagamento em dinheiro calcula troco e registra operador.
- Pode existir opção controlada de “cobrar na próxima fatura”, sujeita a política financeira.
**Estados e exceções relevantes:**
- PDV ocioso.
- Venda em andamento.
- Pagamento confirmado.
- Falha de estoque ou pagamento.
**Endpoints / rotas:**
- `GET /pdv/`
- `POST /pdv/checkout/`

### T18 — Fechamento de Caixa Diário (Tela complementar operacional)
**Objetivo:** Conciliar o caixa físico da recepção, separando o fluxo de gaveta das cobranças online do gateway.

**Perfis:** Administrador, Recepção

**Módulos:** financeiro, dashboard

**Dados exibidos / consumidos:**
- Operador do turno, saldo inicial, entradas por meio de pagamento, conferência cega e resultado da conciliação.
**Ações do usuário:**
- Informar valores contados.
- Registrar justificativa em divergência.
- Encerrar turno.
**Regras de negócio e validações:**
- Fechamento torna o turno imutável para lançamentos retroativos.
- Divergências acima do limite tolerável disparam alerta gerencial.
- O encerramento deve consolidar base para auditoria e contabilidade.
- O operador precisa estar autenticado e associado ao turno aberto.
**Estados e exceções relevantes:**
- Turno aberto.
- Caixa batido.
- Sobra.
- Quebra de caixa.
- Encerramento recusado por dados inconsistentes.
**Endpoints / rotas:**
- `GET /financeiro/caixa/fechamento/`
- `POST /financeiro/caixa/encerrar-turno/`

### T19 — Central de Comunicações e Avisos (Tela complementar operacional)
**Objetivo:** Formalizar os comunicados da academia e substituir a dependência informal de grupos externos para avisos institucionais.

**Perfis:** Administrador

**Módulos:** core, dashboard, clientes

**Dados exibidos / consumidos:**
- Comunicados, filtros de público, canais de disparo, histórico e taxa de leitura quando aplicável.
**Ações do usuário:**
- Redigir comunicado.
- Selecionar público-alvo.
- Publicar no mural.
- Disparar por e-mail.
- Consultar histórico.
**Regras de negócio e validações:**
- Disparos em massa devem ser assíncronos.
- Avisos de mural devem ter vigência/início/fim.
- Mensagens de cobrança não podem ir para mural público.
- Toda campanha deve registrar autor, canal e público-alvo.
**Estados e exceções relevantes:**
- Rascunho.
- Agendado.
- Em processamento.
- Publicado.
- Falha de envio.
**Endpoints / rotas:**
- `GET /comunicacao/`
- `POST /comunicacao/enviar/`

### T20 — Prontuário de Emergência (Visão Rápida) (Tela complementar operacional)
**Objetivo:** Expor, em um clique, apenas os dados vitais necessários para resposta rápida a incidentes no tatame.

**Perfis:** Professor, Administrador

**Módulos:** clientes, dashboard

**Dados exibidos / consumidos:**
- Foto, nome, idade, tipo sanguíneo, alergias/lesões e contato de emergência.
**Ações do usuário:**
- Buscar aluno por nome.
- Abrir ficha rápida.
- Ligar ou acionar WhatsApp do contato de emergência.
**Regras de negócio e validações:**
- Busca precisa ser instantânea e restrita aos alunos sob responsabilidade do professor.
- A tela deve exibir somente dados vitais, sem CPF completo, endereço ou financeiro.
- Logs de acesso devem existir por se tratar de dado sensível operacional.
**Estados e exceções relevantes:**
- Sem aluno encontrado.
- Resultado rápido exibido.
- Falha de carregamento do modal.
**Endpoints / rotas:**
- `GET /clientes/api/busca-rapida/?q=nome`
- `GET /clientes/emergencia/<id>/`

## 5. Matriz de permissões
> Nota: os papéis **não são mutuamente exclusivos**. Um mesmo CPF pode acumular permissões de professor, aluno e/ou responsável; nesse caso, as jornadas coexistem e a interface deve respeitar o contexto ativo sem duplicar usuário. Para refletir a operação real da academia, esta matriz separa **Aluno Titular** e **Aluno Dependente com credencial própria**, mantendo o financeiro restrito ao titular/responsável quando aplicável.

### 5.1 Visitante
- Pode acessar landing page, planos, horários e fluxo inicial de cadastro.
- Não acessa login autenticado, QR de presença, financeiro, dashboards internos ou dados sensíveis.

### 5.2 Responsável
- Pode realizar cadastro do núcleo familiar e visualizar dependentes vinculados.
- Pode fazer login, recuperar senha e alternar o contexto de dependentes elegíveis.
- Pode reservar vaga/check-in prévio para dependente, quando a regra da turma permitir.
- Pode visualizar dados financeiros familiares, planos, faturas e regularização.
- Não inicia aula, não gera QR, não opera caixa e não acessa relatórios gerenciais.

### 5.3 Aluno Titular
- Pode fazer login, recuperar senha, acessar T04, visualizar seu histórico marcial e operar seu próprio check-in.
- Pode reservar vaga em turmas lotadas, quando houver check-in prévio habilitado.
- Pode acessar seu próprio financeiro quando for o pagante do plano.
- Pode solicitar exclusão definitiva de dados no próprio perfil.
- Não acessa CRUD administrativo, caixa, relatórios ou comunicações como emissor.

### 5.4 Aluno Dependente com credencial própria
- Pode fazer login com credencial própria quando a regra de idade/configuração permitir.
- Pode acessar apenas o dashboard restrito de aluno, com QR de presença, reserva de vaga, histórico marcial e dados pessoais mínimos.
- Não pode visualizar financeiro familiar, planos ou faturas.
- Pode solicitar exclusão definitiva de dados apenas dentro do fluxo compatível com representação legal aplicável.
- Não acessa CRUD administrativo, relatórios, caixa ou emissão de comunicados.

### 5.5 Professor
- Pode fazer login, recuperar senha, acessar T05, iniciar aula, gerar QR, confirmar presença manualmente e visualizar prontuário de emergência.
- Pode consultar histórico marcial e dados operacionais de alunos sob sua responsabilidade.
- Pode ter escopo limitado em relatórios e consultas de alunos, sem acesso a financeiro detalhado, salvo quando também acumular papel de aluno titular no mesmo CPF.
- Não opera PDV, fechamento de caixa nem comunicações em massa como emissor padrão.

### 5.6 Administrador
- Possui acesso integral às telas operacionais e gerenciais: cadastros, dashboards, permissões, financeiro, graduação, relatórios, comunicações, PDV, fechamento de caixa e prontuário de emergência.
- Pode vincular múltiplos papéis ao mesmo CPF, trancar/reativar matrícula, aprovar comprovantes e acionar rotinas críticas com auditoria.

## 6. Lacunas e inconsistências identificadas
- **Login**  
  Situação encontrada: a arquitetura original menciona e-mail, enquanto a T01 já usa CPF.  
  Decisão consolidada: usar CPF como identificador primário no login e na recuperação assistida.

- **Papéis**  
  Situação encontrada: há ADMIN, PROFESSOR e ALUNO, mas o onboarding prevê responsável que não treina.  
  Decisão consolidada: adicionar RESPONSÁVEL como papel funcional ou separar papel de acesso do perfil civil.

- **Nomenclatura**  
  Situação encontrada: os documentos alternam `role`, `tipo` e `tipo_usuario`.  
  Decisão consolidada: padronizar a linguagem, mas tratar autorização por papéis acumuláveis e permissões, e não por enum exclusivo.

- **Usuário**  
  Situação encontrada: aparecem `accounts_customuser` e `accounts_user`.  
  Decisão consolidada: tratar como um único modelo customizado de usuário.

- **Multi-papel real**  
  Situação encontrada: a arquitetura diz que a mesma pessoa pode ter múltiplos papéis, mas as telas de cadastro ainda induziam duplicidade de CPF.  
  Decisão consolidada: permitir professor também aluno/responsável no mesmo `CustomUser`, com vínculos distintos por módulo.

- **Presença**  
  Situação encontrada: há rotação de QR, mas a regra anti-duplicidade está implicitamente ligada ao QR code.  
  Decisão consolidada: persistir `SessaoAula` e impedir mais de um check-in por aluno na mesma sessão.

- **Inadimplência no check-in**  
  Situação encontrada: o dashboard mostrava pendência, mas não definia o que acontece ao clicar em “Escanear QR”.  
  Decisão consolidada: criar hard stop antes da câmera, com bloqueio preventivo e CTA de regularização.

- **Graduação**  
  Situação encontrada: há conflito entre carência configurável e regra oficial para promoção.  
  Decisão consolidada: separar critérios oficiais da federação e critérios internos da academia, congelando o tempo elegível durante matrícula pausada.

- **Trancamento de matrícula**  
  Situação encontrada: o fluxo financeiro tratava inadimplência e cancelamento, mas não previa pausa temporária com retorno.  
  Decisão consolidada: criar status local `PAUSADO`, pausar cobrança recorrente quando aplicável, bloquear check-in e congelar tempo de graduação até reativação.

- **Dashboards**  
  Situação encontrada: o aluno vê financeiro familiar, mas não existe tela formal do responsável.  
  Decisão consolidada: unificar T04 como Dashboard do Aluno/Responsável.

- **Turmas/Modalidades**  
  Situação encontrada: são consumidas por várias telas, mas não há tela administrativa mapeada.  
  Decisão consolidada: criar T12 como tela obrigatória.

- **Documentos**  
  Situação encontrada: comprovantes, termos e certificado aparecem dispersos.  
  Decisão consolidada: criar T14 com trilha documental centralizada.

- **Operação de balcão**  
  Situação encontrada: o ciclo de assinaturas não cobre venda avulsa, estoque local e caixa físico.  
  Decisão consolidada: incluir T17 e T18 como operação essencial da recepção.

- **Comunicação institucional**  
  Situação encontrada: a landing e os dashboards consomem avisos, mas faltava o emissor formal e histórico de comunicados.  
  Decisão consolidada: criar T19 como central de comunicações e mural administrável.

- **Emergência**  
  Situação encontrada: os dados de emergência existem no cadastro, mas não havia tela de consulta rápida para tatame/recepção.  
  Decisão consolidada: criar T20 como prontuário operacional enxuto e rastreável.

- **Exportações BI**  
  Situação encontrada: T15 previa exportar, mas não tinha pré-validação dura do artefato de controle.  
  Decisão consolidada: tornar fail-fast obrigatório antes de qualquer CSV crítico.

## 7. Priorização sugerida
### MVP 1
- T01, T02, T03, T04, T05, T06, T07, T08, T12 e T13.
- Incluir desde a primeira entrega o **recorte mínimo de T10 para trancar/reativar matrícula**, porque essa regra atravessa acesso, cobrança e graduação.

### MVP 2
- T09, T10 completo, T11, T14, T17 e T18.

### MVP 3
- T15, T16, T19, T20, notificações proativas, geofencing avançado e relatórios avançados.

### Leitura executiva da priorização
- O conjunto T01 a T16 continua sendo um MVP robusto e suficiente para iniciar a codificação do núcleo do produto, mas o fluxo de trancamento/pausa deve entrar já na primeira entrega por atravessar acesso, cobrança e graduação.
- T17 e T18 deixam de ser “luxo” e passam a ser complementos operacionais fortemente recomendados para qualquer academia com recepção e caixa físico.
- T19 e T20 podem entrar como MVP 3, mas já devem ser previstos na arquitetura e no modelo de permissões para evitar retrabalho.
- O endurecimento da T15 deve ser tratado desde a primeira versão da camada de exportação, mesmo que os relatórios avançados fiquem para fases posteriores.

## 8. Checklist final para início da implementação
- [ ] Definir modelo de usuário e perfis sem ambiguidade antes das migrations.
- [ ] Especificar máquina de estados para assinatura, fatura, presença e graduação.
- [ ] Definir regras de visibilidade por papel em nível de view e de template.
- [ ] Tratar papéis como acumuláveis no mesmo CPF, com contexto ativo e sem duplicidade de usuário.
- [ ] Criar catálogo de erros e mensagens do sistema (login, pagamento, presença, validação).
- [ ] Definir mensagem padrão de hard stop por inadimplência e o CTA de regularização da T04.
- [ ] Mapear todos os anexos aceitos: selfie, comprovante, contrato, certificado.
- [ ] Padronizar logs de auditoria para ações críticas.
- [ ] Definir política de soft delete, anonimização e exclusão definitiva conforme LGPD.
- [ ] Parametrizar idade mínima para credencial própria de dependente e escopo de visibilidade desse perfil.
- [ ] Modelar reserva prévia/check-in antecipado para turmas com lotação controlada e política de no-show.
- [ ] Definir política de trancamento: motivos aceitos, prazo máximo, data de retorno, limite por período e regra de reativação.
- [ ] Testar webhooks com idempotência e reprocessamento.
- [ ] Definir abertura, operação e fechamento de caixa por turno.
- [ ] Modelar catálogo de produtos, estoque e movimentação do PDV.
- [ ] Criar política de comunicação em massa com filas assíncronas e vigência de avisos.
- [ ] Definir escopo mínimo do prontuário de emergência e trilha de auditoria de acesso.
- [ ] Criar critérios de aceite por tela antes do desenvolvimento do front-end.

## 9. Fontes consolidadas utilizadas
- Planejamento Sistema Academia Jiu Jitsu.md
- LV_JIU_JITSU_Sistema_Completo.md
- Tela_01_Landing_Page_e_Login.md
- Tela_02_Cadastro_e_Onboarding.md
- Tela_03_Checkout_e_Assinaturas.md
- Tela_04_Dashboard_do_Aluno.md
- Tela_05_Dashboard_do_Professor.md
- Tela_06_Dashboard_Administrativo_Master.md
- Tela_07_Painel_de_Graduacao_e_Exame.md
- Tela_17_PDV_e_Caixa_Rapido.md
- Tela_18_Fechamento_de_Caixa_Diario.md
- Tela_19_Central_de_Comunicacoes_e_Avisos.md
- Tela_20_Prontuario_de_Emergencia_Visao_Rapida.md
