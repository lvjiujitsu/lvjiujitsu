# Índice de PRDs

Índice canônico de `docs/prd/`. Toda PRD usa `PRD-<NNN>-<slug>.md` com número único — ver `docs/PRD-STANDARD.md`.

Antes de criar uma PRD nova, conferir o último número desta tabela (não usar `ls` isolado, que não revela gaps reservados).

## Renumeração de duplicatas (PRD-079)

Em 2026-06-30 havia números duplicados: `008`, `009`, `014`, `015`, `016`, `021`, `028`. Para cada par, o documento com referências de entrada (citado por outra PRD) ou continuidade temática ficou no número original; o outro foi renumerado para o próximo número livre, sem perda de conteúdo (rename via `git mv`, título interno e referências cruzadas atualizados via `rg`).

| Número original | Arquivo mantido no número | Arquivo renumerado | Novo número |
|---|---|---|---|
| 008 | `PRD-008-ajustar-paineis-professor-aluno-checkin-historico.md` | `PRD-008-consolidar-landing-remover-paginas-publicas.md` | `PRD-022` |
| 009 | `PRD-009-loja-portal-prepedido-historico.md` | `PRD-009-checkin-com-aprovacao-do-professor.md` | `PRD-055` |
| 014 | `PRD-014-painel-administrativo-como-pessoa.md` | `PRD-014-wizard-ui-fixes.md` | `PRD-090` |
| 015 | `PRD-015-graduacao-inicial-cadastro.md` | `PRD-015-repasses-sem-saque-antecipado.md` | `PRD-086` |
| 016 | `PRD-016-identidade-menu-lateral.md` | `PRD-016-remover-inicial-seed.md` | `PRD-087` |
| 021 | `PRD-021-etapas-pagamento-separadas-cadastro.md` | `PRD-021-revisao-fluxo-cadastro.md` (superada pelo PRD-040) | `PRD-088` |
| 028 | `PRD-028-home-e-pessoas-fullscreen.md` | `PRD-028-crud-planos-precificacao-dinamica.md` | `PRD-089` |

Os números `022` e `055` eram gaps livres (nunca usados) e foram reaproveitados antes de abrir números novos no final da sequência (`086`–`090`).

## Tabela completa

| Arquivo | Título |
|---|---|
| [PRD-001-cadastro-cliente.md](PRD-001-cadastro-cliente.md) | Cadastro de cliente com validação de CPF |
| [PRD-002-enxugar-exibicao-turmas-cadastro.md](PRD-002-enxugar-exibicao-turmas-cadastro.md) | Enxugar a exibição das turmas no cadastro |
| [PRD-003-ajustar-pergunta-arte-marcial-cadastro.md](PRD-003-ajustar-pergunta-arte-marcial-cadastro.md) | Ajustar Pergunta de Arte Marcial no Cadastro |
| [PRD-004-corrigir-catalogo-materiais-por-variante.md](PRD-004-corrigir-catalogo-materiais-por-variante.md) | Corrigir Catálogo de Materiais por Variante |
| [PRD-005-corrigir-materiais-ibjjf-ui.md](PRD-005-corrigir-materiais-ibjjf-ui.md) | Corrigir materiais por regra IBJJF e UI de seleção |
| [PRD-006-padronizar-tela-troca-plano.md](PRD-006-padronizar-tela-troca-plano.md) | Padronizar tela de troca de plano com o design system do portal |
| [PRD-007-reformular-planos-precificacao-elegibilidade.md](PRD-007-reformular-planos-precificacao-elegibilidade.md) | Reformular planos, precificação, elegibilidade e segmentação Adulto vs Kids/Juvenil |
| [PRD-008-ajustar-paineis-professor-aluno-checkin-historico.md](PRD-008-ajustar-paineis-professor-aluno-checkin-historico.md) | Ajustar painéis de professor e aluno para cronograma, check-in e histórico de presença |
| [PRD-009-loja-portal-prepedido-historico.md](PRD-009-loja-portal-prepedido-historico.md) | Loja no portal autenticado com pré-pedido, fila por chegada e histórico do aluno |
| [PRD-010-modulo-graduacao-faixas-graus.md](PRD-010-modulo-graduacao-faixas-graus.md) | Módulo de controle de graduação (faixas, graus, regras e panorama) |
| [PRD-011-home-graduacao-recolhida.md](PRD-011-home-graduacao-recolhida.md) | Home com graduação recolhida |
| [PRD-012-modulo-financeiro-repasses.md](PRD-012-modulo-financeiro-repasses.md) | Modulo financeiro e repasses |
| [PRD-013-acoes-rapidas-professor-home.md](PRD-013-acoes-rapidas-professor-home.md) | Ações rápidas do professor na home |
| [PRD-014-painel-administrativo-como-pessoa.md](PRD-014-painel-administrativo-como-pessoa.md) | Painel administrativo como pessoa do portal |
| [PRD-015-graduacao-inicial-cadastro.md](PRD-015-graduacao-inicial-cadastro.md) | Graduação inicial no cadastro |
| [PRD-016-identidade-menu-lateral.md](PRD-016-identidade-menu-lateral.md) | Identidade no menu lateral |
| [PRD-017-seeds-granulares-auditaveis.md](PRD-017-seeds-granulares-auditaveis.md) | Seeds Granulares Auditáveis |
| [PRD-018-botoes-mobile-home-professor.md](PRD-018-botoes-mobile-home-professor.md) | Botões Mobile Na Home Do Professor |
| [PRD-019-troca-plano-padrao-plan-selector.md](PRD-019-troca-plano-padrao-plan-selector.md) | Padronizar troca de plano com o padrão `plan-selector` do cadastro |
| [PRD-020-troca-plano-saldo-credito-refund.md](PRD-020-troca-plano-saldo-credito-refund.md) | Troca de plano com saldo→tempo, crédito futuro e refund automático |
| [PRD-021-etapas-pagamento-separadas-cadastro.md](PRD-021-etapas-pagamento-separadas-cadastro.md) | Etapas de Pagamento Separadas no Wizard de Cadastro |
| [PRD-022-consolidar-landing-remover-paginas-publicas.md](PRD-022-consolidar-landing-remover-paginas-publicas.md) | Consolidar landing pública e remover páginas públicas obsoletas |
| [PRD-023-seeds-env-orquestrador-dados-externos.md](PRD-023-seeds-env-orquestrador-dados-externos.md) | Seeds opcionais, `.env` orquestrador, dados iniciais em JSON |
| [PRD-024-governanca-seeds-atomicas.md](PRD-024-governanca-seeds-atomicas.md) | Governanca de seeds atomicas e desacopladas |
| [PRD-025-redesign-ui-responsivo-lv.md](PRD-025-redesign-ui-responsivo-lv.md) | Redesign responsivo do sistema LV |
| [PRD-026-pessoas-redesign-responsivo.md](PRD-026-pessoas-redesign-responsivo.md) | Redesign responsivo de Pessoas |
| [PRD-027-home-admin-redesign-responsivo.md](PRD-027-home-admin-redesign-responsivo.md) | Redesign responsivo da home master |
| [PRD-028-home-e-pessoas-fullscreen.md](PRD-028-home-e-pessoas-fullscreen.md) | Home e Pessoas em tela cheia |
| [PRD-029-edicao-pessoa-graduacao-e-ui.md](PRD-029-edicao-pessoa-graduacao-e-ui.md) | Edicao de pessoa com UI proporcional e contexto de graduacao |
| [PRD-030-tela-login.md](PRD-030-tela-login.md) | Tela de Login — Implementação do Zero |
| [PRD-031-padronizar-json-seeds.md](PRD-031-padronizar-json-seeds.md) | Padronizar JSONs das seeds |
| [PRD-032-seed-repasses-professores.md](PRD-032-seed-repasses-professores.md) | Seed de repasses dos professores |
| [PRD-033-seed-feriados-iniciais.md](PRD-033-seed-feriados-iniciais.md) | Seed de Feriados Iniciais |
| [PRD-034-remocao-temporaria-testes-telas.md](PRD-034-remocao-temporaria-testes-telas.md) | Remocao Temporaria de Testes de Telas |
| [PRD-035-seed-valores-planos-assinatura.md](PRD-035-seed-valores-planos-assinatura.md) | Seed de Valores dos Planos de Assinatura |
| [PRD-036-icones-pagamento-cadastro.md](PRD-036-icones-pagamento-cadastro.md) | Icones de Pagamento no Cadastro |
| [PRD-037-remover-stripe-checkout-asaas.md](PRD-037-remover-stripe-checkout-asaas.md) | Remover Stripe do checkout e usar Asaas |
| [PRD-038-redesign-etapa-materiais-wizard.md](PRD-038-redesign-etapa-materiais-wizard.md) | Redesign da etapa "Materiais e equipamentos" no wizard de cadastro |
| [PRD-039-fluxo-guardian-asaas-home-multiplicador.md](PRD-039-fluxo-guardian-asaas-home-multiplicador.md) | Padronizar fluxo de cadastro — guardian, Asaas, home, multiplicador de plano |
| [PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md](PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md) | Fluxo intransigente de cadastro com pagamento antes de criar Pessoa |
| [PRD-041-stripe-recorrente.md](PRD-041-stripe-recorrente.md) | Stripe — Planos Recorrentes |
| [PRD-042-cupons-desconto.md](PRD-042-cupons-desconto.md) | Cupons de Desconto |
| [PRD-043-home-unificada.md](PRD-043-home-unificada.md) | Home Unificada por Permissão |
| [PRD-044-home-redesign.md](PRD-044-home-redesign.md) | Home — Redesign Funcional e Visual |
| [PRD-045-pessoas-listagem-detalhe.md](PRD-045-pessoas-listagem-detalhe.md) | Módulo Pessoas — Listagem, Detalhe, Formulário e Confirmação de Exclusão |
| [PRD-046-portal-aluno-professor-cronograma.md](PRD-046-portal-aluno-professor-cronograma.md) | Portal Aluno e Professor — Graduação Enriquecida + Gestão de Cronograma no Dashboard |
| [PRD-047-home-dashboard-redesign-modal.md](PRD-047-home-dashboard-redesign-modal.md) | Home Dashboard — Redesign com Modais de Presenças e Histórico de Graduação |
| [PRD-048-financeiro-aluno-professor-dashboard.md](PRD-048-financeiro-aluno-professor-dashboard.md) | Financeiro no Dashboard — Repasse do Professor e Mensalidade do Aluno |
| [PRD-049-instructor-self-checkin.md](PRD-049-instructor-self-checkin.md) | Self-Check-in do Professor |
| [PRD-050-modulo-planos-admin.md](PRD-050-modulo-planos-admin.md) | Módulo administrativo de planos |
| [PRD-051-kanri-students-migration-json.md](PRD-051-kanri-students-migration-json.md) | JSON de migração de alunos Kanri |
| [PRD-052-seed-kanri-students-migration.md](PRD-052-seed-kanri-students-migration.md) | Seed de migração de alunos Kanri |
| [PRD-053-render-supabase-reset-seguro.md](PRD-053-render-supabase-reset-seguro.md) | Render Supabase Reset Seguro |
| [PRD-054-alinhamento-arquitetural-lv-visary.md](PRD-054-alinhamento-arquitetural-lv-visary.md) | Alinhamento Arquitetural LV × Visary |
| [PRD-055-checkin-com-aprovacao-do-professor.md](PRD-055-checkin-com-aprovacao-do-professor.md) | Check-in com aprovação do professor + paridade de gestão de cronograma |
| [PRD-056-wizard-pos-pagamento-navegacao-e-re-hidratacao.md](PRD-056-wizard-pos-pagamento-navegacao-e-re-hidratacao.md) | Wizard pós-pagamento — bloqueio de navegação retroativa e re-hidratação de turmas |
| [PRD-057-simplificacao-wizard-correcao-estados.md](PRD-057-simplificacao-wizard-correcao-estados.md) | Simplificação do wizard — correção de estados e remoção de código de desenvolvimento |
| [PRD-058-validacao-webhooks-asaas-stripe-local-hg.md](PRD-058-validacao-webhooks-asaas-stripe-local-hg.md) | Validação de Webhooks Asaas e Stripe — Local e Homologação |
| [PRD-059-governanca-agentes-multiplataforma.md](PRD-059-governanca-agentes-multiplataforma.md) | Governança enxuta para Claude, Codex e Cursor |
| [PRD-060-paridade-governanca-prompt-builder.md](PRD-060-paridade-governanca-prompt-builder.md) | Paridade de governança multiplataforma + skill lv-prompt-builder |
| [PRD-061-alinhamento-governanca-workflow-adapters.md](PRD-061-alinhamento-governanca-workflow-adapters.md) | Alinhamento de governança — workflow e adaptadores ao padrão Visary |
| [PRD-062-auditoria-sinais-servicos-idempotencia.md](PRD-062-auditoria-sinais-servicos-idempotencia.md) | Auditoria do padrão sinal → serviço idempotente (lição PRD-105 do Visary) |
| [PRD-063-integridade-exclusao-cascata-person.md](PRD-063-integridade-exclusao-cascata-person.md) | Integridade de exclusão em cascata de Person (lição PRD-116 do Visary) |
| [PRD-064-wizard-maquina-estados-rehidratacao-continuidade.md](PRD-064-wizard-maquina-estados-rehidratacao-continuidade.md) | Wizard público — consolidação da máquina de estados, re-hidratação autoritativa e continuidade pós-pagamento |
| [PRD-065-hubs-administrativos-modulos-lv.md](PRD-065-hubs-administrativos-modulos-lv.md) | Hubs administrativos dos módulos LV |
| [PRD-066-portabilidade-visary-modal-crud.md](PRD-066-portabilidade-visary-modal-crud.md) | Portabilidade do padrão visual e de CRUD em modal do Visary para o LV |
| [PRD-067-paridade-css-pessoas-filtros-kpi-responsividade.md](PRD-067-paridade-css-pessoas-filtros-kpi-responsividade.md) | Paridade de CSS de Pessoas — filtros, KPIs, linhas e responsividade |
| [PRD-068-rework-limpo-pessoas-fundacao-lv.md](PRD-068-rework-limpo-pessoas-fundacao-lv.md) | Login unico progressivo |
| [PRD-069-home-lv-paridade-visary.md](PRD-069-home-lv-paridade-visary.md) | Home LV com governanca visual Visary |
| [PRD-070-governanca-operacional-sem-bloqueio-local.md](PRD-070-governanca-operacional-sem-bloqueio-local.md) | Governanca operacional sem bloqueio local |
| [PRD-071-alinhamento-suite-legada-escopo-progressivo.md](PRD-071-alinhamento-suite-legada-escopo-progressivo.md) | Alinhamento da suite legada ao escopo progressivo |
| [PRD-072-correcoes-home-professor-presenca-mobile.md](PRD-072-correcoes-home-professor-presenca-mobile.md) | Correcoes da home do professor, presenca e mobile |
| [PRD-073-seeds-administrative-bootstrap-consistente.md](PRD-073-seeds-administrative-bootstrap-consistente.md) | Seeds administrativas e bootstrap consistente |
| [PRD-074-papeis-operacionais-acumulaveis-permissoes.md](PRD-074-papeis-operacionais-acumulaveis-permissoes.md) | Papéis operacionais acumuláveis e permissões mínimas |
| [PRD-075-fundacao-ui-rotas-ingles-modal-crud.md](PRD-075-fundacao-ui-rotas-ingles-modal-crud.md) | Fundação UI, rotas em inglês e CRUD modal |
| [PRD-076-auditoria-legado-governanca-documentacao.md](PRD-076-auditoria-legado-governanca-documentacao.md) | Auditoria de legado, governança e documentação |
| [PRD-077-crud-mvp-academia-artes-marciais.md](PRD-077-crud-mvp-academia-artes-marciais.md) | CRUD MVP da academia de artes marciais |
| [PRD-078-rotas-ativas-templates-ausentes.md](PRD-078-rotas-ativas-templates-ausentes.md) | Rotas ativas com templates ausentes |
| [PRD-079-normalizar-indice-prds-duplicadas.md](PRD-079-normalizar-indice-prds-duplicadas.md) | Normalizar índice de PRDs duplicadas |
| [PRD-080-refatorar-js-sem-innerhtml.md](PRD-080-refatorar-js-sem-innerhtml.md) | Refatorar JavaScript sem innerHTML inseguro |
| [PRD-081-extrair-servicos-cadastro-pagamento.md](PRD-081-extrair-servicos-cadastro-pagamento.md) | Extrair serviços de cadastro e pagamento do wizard |
| [PRD-082-readme-requirements-dev-governanca.md](PRD-082-readme-requirements-dev-governanca.md) | README e requirements-dev alinhados ao LV |
| [PRD-083-arquivar-documentacao-legada-static.md](PRD-083-arquivar-documentacao-legada-static.md) | Arquivar documentação legada em static |
| [PRD-084-tokens-css-inline-style.md](PRD-084-tokens-css-inline-style.md) | Tokens CSS e remoção de estilo inline |
| [PRD-085-saida-ascii-management-commands-powershell.md](PRD-085-saida-ascii-management-commands-powershell.md) | Saida ASCII em management commands no PowerShell |
| [PRD-086-repasses-sem-saque-antecipado.md](PRD-086-repasses-sem-saque-antecipado.md) | Repasses sem saque antecipado |
| [PRD-087-remover-inicial-seed.md](PRD-087-remover-inicial-seed.md) | Remover inicial_seed |
| [PRD-088-revisao-fluxo-cadastro.md](PRD-088-revisao-fluxo-cadastro.md) | Revisão completa do fluxo de cadastro — pré-registro, pagamento sequencial e finalização explícita (superada pelo PRD-040) |
| [PRD-089-crud-planos-precificacao-dinamica.md](PRD-089-crud-planos-precificacao-dinamica.md) | CRUD de Planos com Precificação Dinâmica |
| [PRD-090-wizard-ui-fixes.md](PRD-090-wizard-ui-fixes.md) | Correções de UI do wizard de cadastro |
| [AUDIT-2026-06-30-master-findings.md](AUDIT-2026-06-30-master-findings.md) | Auditoria mestre 2026-06-30 — achados numerados e mapa de telas |
| [PRD-091-ui-papeis-operacionais-formulario-pessoa.md](PRD-091-ui-papeis-operacionais-formulario-pessoa.md) | UI de papéis operacionais no formulário de pessoa |
| [PRD-092-home-split-minha-area-gestao.md](PRD-092-home-split-minha-area-gestao.md) | Home split Minha área e Gestão |
| [PRD-093-responsavel-iniciar-treino-matricula.md](PRD-093-responsavel-iniciar-treino-matricula.md) | Responsável iniciar treino e matrícula |
| [PRD-094-checkin-aluno-papel-duplo-precondicao-professor.md](PRD-094-checkin-aluno-papel-duplo-precondicao-professor.md) | Check-in aluno com papel duplo e pré-condição do professor |
| [PRD-095-ordem-canonica-seeds-obsidian-docs.md](PRD-095-ordem-canonica-seeds-obsidian-docs.md) | Ordem canônica de seeds Obsidian e documentação |
| [PRD-096-encoding-utf8-template-cronograma.md](PRD-096-encoding-utf8-template-cronograma.md) | Encoding UTF-8 do template de cronograma |
| [PRD-097-views-calendario-orfas-sem-rota.md](PRD-097-views-calendario-orfas-sem-rota.md) | Views de calendário órfãs sem rota |
| [PRD-098-modulo-auditoria-operacional.md](PRD-098-modulo-auditoria-operacional.md) | Módulo de auditoria operacional |
| [PRD-099-permissao-edicao-pessoa-apoio.md](PRD-099-permissao-edicao-pessoa-apoio.md) | Permissão de edição de pessoa para apoio |
| [PRD-100-rota-perfis-vs-papeis-operacionais.md](PRD-100-rota-perfis-vs-papeis-operacionais.md) | Rota Perfis versus papéis operacionais |
| [PRD-111-seeds-homologacao-cadastro-nn.md](PRD-111-seeds-homologacao-cadastro-nn.md) | Seeds de homologacao de cadastro N:N |
| [PRD-112-solicitacao-acesso-administrativo-pendente.md](PRD-112-solicitacao-acesso-administrativo-pendente.md) | Solicitacao de acesso administrativo pendente |
| [PRD-113-solicitacao-turmas-horarios-professor.md](PRD-113-solicitacao-turmas-horarios-professor.md) | Solicitacao de turmas e horarios por professor |
| [PRD-114-elegibilidade-plano-veterano.md](PRD-114-elegibilidade-plano-veterano.md) | Elegibilidade do plano Veterano (ex-Fidelidade) por tempo de casa |
| [PRD-115-wizard-perfis-operacionais-sequenciais.md](PRD-115-wizard-perfis-operacionais-sequenciais.md) | Wizard de perfis operacionais sequenciais |
| [PRD-116-home-aluno-permissoes-cronograma-fidelidade.md](PRD-116-home-aluno-permissoes-cronograma-fidelidade.md) | Home do aluno com permissoes, cronograma modal e fidelidade |
| [PRD-117-fidelidade-contratual-planos-recorrentes.md](PRD-117-fidelidade-contratual-planos-recorrentes.md) | Fidelidade contratual para planos recorrentes |
| [PRD-118-adicionar-dependente-pos-matricula.md](PRD-118-adicionar-dependente-pos-matricula.md) | Adicionar dependente pós-matrícula |
| [PRD-119-dependente-materiais-idempotencia-cpf.md](PRD-119-dependente-materiais-idempotencia-cpf.md) | Dependente com materiais, idempotência e CPF pendente |
| [PRD-120-dependente-modal-home.md](PRD-120-dependente-modal-home.md) | Dependente em modal na home |
| [PRD-121-home-cliente-dependentes-mensalidades-crud.md](PRD-121-home-cliente-dependentes-mensalidades-crud.md) | Home do cliente com dependentes, mensalidades e CRUD modal |
| [PRD-122-desfazer-checkin-pendente-aluno.md](PRD-122-desfazer-checkin-pendente-aluno.md) | Desfazer check-in pendente do aluno |
| [PRD-123-modal-conta-cliente-editar-excluir.md](PRD-123-modal-conta-cliente-editar-excluir.md) | Modal da conta do cliente com edição e exclusão |
| [PRD-124-dependente-upgrade-plano-familiar.md](PRD-124-dependente-upgrade-plano-familiar.md) | Dependente com upgrade para plano familiar |
| [PRD-125-sincronizacao-upgrade-familiar-stripe.md](PRD-125-sincronizacao-upgrade-familiar-stripe.md) | Sincronizacao remota do upgrade familiar Stripe |
| [PRD-126-prevenir-cobranca-duplicada-mesmo-cartao-dependente.md](PRD-126-prevenir-cobranca-duplicada-mesmo-cartao-dependente.md) | Prevenir cobrança Stripe duplicada no mesmo cartão entre titular e dependente |
| [PRD-127-desconto-familia-tier-unico-precificacao.md](PRD-127-desconto-familia-tier-unico-precificacao.md) | Desconto família como modificador de tier único (rework de precificação) |
| [PRD-128-crud-plan-tier-price-ui-desconto-bloqueio-cancelamento.md](PRD-128-crud-plan-tier-price-ui-desconto-bloqueio-cancelamento.md) | CRUD PlanTier/PlanPrice, UI de desconto e bloqueio real de cancelamento na carência |
| [PRD-129-migrar-cadastro-publico-catalogo-plantier-planprice.md](PRD-129-migrar-cadastro-publico-catalogo-plantier-planprice.md) | Migrar cadastro público (register.js) para o catálogo PlanTier/PlanPrice |
| [PRD-130-migrar-troca-plano-catalogo-plantier-planprice.md](PRD-130-migrar-troca-plano-catalogo-plantier-planprice.md) | Migrar troca de plano (upgrade/downgrade) para o catálogo PlanTier/PlanPrice |
| [PRD-131-corrigir-professor-presente-padrao-cancelar-restaurar-aula.md](PRD-131-corrigir-professor-presente-padrao-cancelar-restaurar-aula.md) | Corrigir professor presente por padrão ao cancelar/restaurar aula (regressão de check-in) |
| [PRD-132-transicao-livre-planos-pausa-mensalidade.md](PRD-132-transicao-livre-planos-pausa-mensalidade.md) | Transição livre entre planos (qualquer gateway) + pausa de mensalidade (atestado médico e trancamento self-service) |
| [PRD-133-indicador-pagamento-trocar-cartao-stripe.md](PRD-133-indicador-pagamento-trocar-cartao-stripe.md) | Indicador de forma de pagamento/gateway + trocar cartão via Stripe Billing Portal + histórico de cobrança falhada |
| [PRD-134-historico-eventos-assinatura-familia-cliente-admin.md](PRD-134-historico-eventos-assinatura-familia-cliente-admin.md) | Histórico de eventos de assinatura/família — timeline informativa (cliente) + auditoria técnica (admin) |
| [PRD-135-cobranca-recorrente-asaas-backfill-timeline.md](PRD-135-cobranca-recorrente-asaas-backfill-timeline.md) | Cobrança recorrente automatizada Asaas (sincronizada com desconto família) + backfill de eventos históricos da timeline |
