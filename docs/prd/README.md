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

**Próximo número livre: 178**

Status extraído da seção `## Final status` de cada arquivo, nunca
digitado à mão. Regenerar com `python scripts/build_prd_index.py`.

| N | Título | Status | Arquivo |
|---:|---|---|---|
| 001 | Cadastro de cliente com validação de CPF | — | [PRD-001-cadastro-cliente.md](PRD-001-cadastro-cliente.md) |
| 002 | Enxugar a exibição das turmas no cadastro | — | [PRD-002-enxugar-exibicao-turmas-cadastro.md](PRD-002-enxugar-exibicao-turmas-cadastro.md) |
| 003 | Ajustar Pergunta de Arte Marcial no Cadastro | — | [PRD-003-ajustar-pergunta-arte-marcial-cadastro.md](PRD-003-ajustar-pergunta-arte-marcial-cadastro.md) |
| 004 | Corrigir Catálogo de Materiais por Variante | — | [PRD-004-corrigir-catalogo-materiais-por-variante.md](PRD-004-corrigir-catalogo-materiais-por-variante.md) |
| 005 | Corrigir materiais por regra IBJJF e UI de seleção | — | [PRD-005-corrigir-materiais-ibjjf-ui.md](PRD-005-corrigir-materiais-ibjjf-ui.md) |
| 006 | Padronizar tela de troca de plano com o design system do portal | — | [PRD-006-padronizar-tela-troca-plano.md](PRD-006-padronizar-tela-troca-plano.md) |
| 007 | Reformular planos, precificação, elegibilidade e segmentação Adulto vs Kids/Juvenil | — | [PRD-007-reformular-planos-precificacao-elegibilidade.md](PRD-007-reformular-planos-precificacao-elegibilidade.md) |
| 008 | Ajustar painéis de professor e aluno para cronograma, check-in e histórico de presença | — | [PRD-008-ajustar-paineis-professor-aluno-checkin-historico.md](PRD-008-ajustar-paineis-professor-aluno-checkin-historico.md) |
| 009 | Loja no portal autenticado com pré-pedido, fila por chegada e histórico do aluno | — | [PRD-009-loja-portal-prepedido-historico.md](PRD-009-loja-portal-prepedido-historico.md) |
| 010 | Módulo de controle de graduação (faixas, graus, regras e panorama) | — | [PRD-010-modulo-graduacao-faixas-graus.md](PRD-010-modulo-graduacao-faixas-graus.md) |
| 011 | Home com graduação recolhida | — | [PRD-011-home-graduacao-recolhida.md](PRD-011-home-graduacao-recolhida.md) |
| 012 | Modulo financeiro e repasses | — | [PRD-012-modulo-financeiro-repasses.md](PRD-012-modulo-financeiro-repasses.md) |
| 013 | Ações rápidas do professor na home | — | [PRD-013-acoes-rapidas-professor-home.md](PRD-013-acoes-rapidas-professor-home.md) |
| 014 | Painel administrativo como pessoa do portal | — | [PRD-014-painel-administrativo-como-pessoa.md](PRD-014-painel-administrativo-como-pessoa.md) |
| 015 | Graduação inicial no cadastro | — | [PRD-015-graduacao-inicial-cadastro.md](PRD-015-graduacao-inicial-cadastro.md) |
| 016 | Identidade no menu lateral | — | [PRD-016-identidade-menu-lateral.md](PRD-016-identidade-menu-lateral.md) |
| 017 | Seeds Granulares Auditáveis | — | [PRD-017-seeds-granulares-auditaveis.md](PRD-017-seeds-granulares-auditaveis.md) |
| 018 | Botões Mobile Na Home Do Professor | — | [PRD-018-botoes-mobile-home-professor.md](PRD-018-botoes-mobile-home-professor.md) |
| 019 | Padronizar troca de plano com o padrão `plan-selector` do cadastro | — | [PRD-019-troca-plano-padrao-plan-selector.md](PRD-019-troca-plano-padrao-plan-selector.md) |
| 020 | Troca de plano com saldo→tempo, crédito futuro e refund automático | — | [PRD-020-troca-plano-saldo-credito-refund.md](PRD-020-troca-plano-saldo-credito-refund.md) |
| 021 | Etapas de Pagamento Separadas no Wizard de Cadastro | — | [PRD-021-etapas-pagamento-separadas-cadastro.md](PRD-021-etapas-pagamento-separadas-cadastro.md) |
| 022 | Consolidar landing pública e remover páginas públicas obsoletas | — | [PRD-022-consolidar-landing-remover-paginas-publicas.md](PRD-022-consolidar-landing-remover-paginas-publicas.md) |
| 023 | Seeds opcionais, `.env` orquestrador, dados iniciais em JSON | — | [PRD-023-seeds-env-orquestrador-dados-externos.md](PRD-023-seeds-env-orquestrador-dados-externos.md) |
| 024 | Governanca de seeds atomicas e desacopladas | — | [PRD-024-governanca-seeds-atomicas.md](PRD-024-governanca-seeds-atomicas.md) |
| 025 | Redesign responsivo do sistema LV | — | [PRD-025-redesign-ui-responsivo-lv.md](PRD-025-redesign-ui-responsivo-lv.md) |
| 026 | Redesign responsivo de Pessoas | — | [PRD-026-pessoas-redesign-responsivo.md](PRD-026-pessoas-redesign-responsivo.md) |
| 027 | Redesign responsivo da home master | — | [PRD-027-home-admin-redesign-responsivo.md](PRD-027-home-admin-redesign-responsivo.md) |
| 028 | Home e Pessoas em tela cheia | — | [PRD-028-home-e-pessoas-fullscreen.md](PRD-028-home-e-pessoas-fullscreen.md) |
| 029 | Edicao de pessoa com UI proporcional e contexto de graduacao | — | [PRD-029-edicao-pessoa-graduacao-e-ui.md](PRD-029-edicao-pessoa-graduacao-e-ui.md) |
| 030 | Tela de Login — Implementação do Zero | — | [PRD-030-tela-login.md](PRD-030-tela-login.md) |
| 031 | Padronizar JSONs das seeds | — | [PRD-031-padronizar-json-seeds.md](PRD-031-padronizar-json-seeds.md) |
| 032 | Seed de repasses dos professores | — | [PRD-032-seed-repasses-professores.md](PRD-032-seed-repasses-professores.md) |
| 033 | Seed de Feriados Iniciais | — | [PRD-033-seed-feriados-iniciais.md](PRD-033-seed-feriados-iniciais.md) |
| 034 | Remocao Temporaria de Testes de Telas | — | [PRD-034-remocao-temporaria-testes-telas.md](PRD-034-remocao-temporaria-testes-telas.md) |
| 035 | Seed de Valores dos Planos de Assinatura | — | [PRD-035-seed-valores-planos-assinatura.md](PRD-035-seed-valores-planos-assinatura.md) |
| 036 | Icones de Pagamento no Cadastro | — | [PRD-036-icones-pagamento-cadastro.md](PRD-036-icones-pagamento-cadastro.md) |
| 037 | Remover Stripe do checkout e usar Asaas | — | [PRD-037-remover-stripe-checkout-asaas.md](PRD-037-remover-stripe-checkout-asaas.md) |
| 038 | Redesign da etapa "Materiais e equipamentos" no wizard de cadastro | — | [PRD-038-redesign-etapa-materiais-wizard.md](PRD-038-redesign-etapa-materiais-wizard.md) |
| 039 | Padronizar fluxo de cadastro — guardian, Asaas, home, multiplicador de plano | — | [PRD-039-fluxo-guardian-asaas-home-multiplicador.md](PRD-039-fluxo-guardian-asaas-home-multiplicador.md) |
| 040 | Fluxo intransigente de cadastro com pagamento antes de criar Pessoa | — | [PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md](PRD-040-fluxo-cadastro-pagamento-antes-pessoa.md) |
| 041 | Stripe — Planos Recorrentes | — | [PRD-041-stripe-recorrente.md](PRD-041-stripe-recorrente.md) |
| 042 | Cupons de Desconto | — | [PRD-042-cupons-desconto.md](PRD-042-cupons-desconto.md) |
| 043 | Home Unificada por Permissão | — | [PRD-043-home-unificada.md](PRD-043-home-unificada.md) |
| 044 | Home — Redesign Funcional e Visual | — | [PRD-044-home-redesign.md](PRD-044-home-redesign.md) |
| 045 | Módulo Pessoas — Listagem, Detalhe, Formulário e Confirmação de Exclusão | — | [PRD-045-pessoas-listagem-detalhe.md](PRD-045-pessoas-listagem-detalhe.md) |
| 046 | Portal Aluno e Professor — Graduação Enriquecida + Gestão de Cronograma no Dashboard | — | [PRD-046-portal-aluno-professor-cronograma.md](PRD-046-portal-aluno-professor-cronograma.md) |
| 047 | Home Dashboard — Redesign com Modais de Presenças e Histórico de Graduação | — | [PRD-047-home-dashboard-redesign-modal.md](PRD-047-home-dashboard-redesign-modal.md) |
| 048 | Financeiro no Dashboard — Repasse do Professor e Mensalidade do Aluno | — | [PRD-048-financeiro-aluno-professor-dashboard.md](PRD-048-financeiro-aluno-professor-dashboard.md) |
| 049 | Self-Check-in do Professor | — | [PRD-049-instructor-self-checkin.md](PRD-049-instructor-self-checkin.md) |
| 050 | Módulo administrativo de planos | — | [PRD-050-modulo-planos-admin.md](PRD-050-modulo-planos-admin.md) |
| 051 | JSON de migração de alunos Kanri | — | [PRD-051-kanri-students-migration-json.md](PRD-051-kanri-students-migration-json.md) |
| 052 | Seed de migração de alunos Kanri | — | [PRD-052-seed-kanri-students-migration.md](PRD-052-seed-kanri-students-migration.md) |
| 053 | Render Supabase Reset Seguro | — | [PRD-053-render-supabase-reset-seguro.md](PRD-053-render-supabase-reset-seguro.md) |
| 054 | Alinhamento arquitetural e reset seguro | — | [PRD-054-alinhamento-arquitetural-reset-seguro.md](PRD-054-alinhamento-arquitetural-reset-seguro.md) |
| 055 | Check-in com aprovação do professor + paridade de gestão de cronograma | — | [PRD-055-checkin-com-aprovacao-do-professor.md](PRD-055-checkin-com-aprovacao-do-professor.md) |
| 056 | Wizard pós-pagamento — bloqueio de navegação retroativa e re-hidratação de turmas | — | [PRD-056-wizard-pos-pagamento-navegacao-e-re-hidratacao.md](PRD-056-wizard-pos-pagamento-navegacao-e-re-hidratacao.md) |
| 057 | Simplificação do wizard — correção de estados e remoção de código de desenvolvimento | — | [PRD-057-simplificacao-wizard-correcao-estados.md](PRD-057-simplificacao-wizard-correcao-estados.md) |
| 058 | Validação de Webhooks Asaas e Stripe — Local e Homologação | — | [PRD-058-validacao-webhooks-asaas-stripe-local-hg.md](PRD-058-validacao-webhooks-asaas-stripe-local-hg.md) |
| 059 | Governança enxuta para Claude, Codex e Cursor | concluída com limitações | [PRD-059-governanca-agentes-multiplataforma.md](PRD-059-governanca-agentes-multiplataforma.md) |
| 060 | Paridade de governança multiplataforma + skill lv-prompt-builder | concluída com limitações | [PRD-060-paridade-governanca-prompt-builder.md](PRD-060-paridade-governanca-prompt-builder.md) |
| 061 | Alinhamento de governança — workflow e adaptadores | concluída com limitações | [PRD-061-alinhamento-governanca-workflow-adapters.md](PRD-061-alinhamento-governanca-workflow-adapters.md) |
| 062 | Auditoria do padrão sinal → serviço idempotente | não concluída | [PRD-062-auditoria-sinais-servicos-idempotencia.md](PRD-062-auditoria-sinais-servicos-idempotencia.md) |
| 063 | Integridade de exclusão em cascata de Person | concluída com limitações | [PRD-063-integridade-exclusao-cascata-person.md](PRD-063-integridade-exclusao-cascata-person.md) |
| 064 | Wizard público — consolidação da máquina de estados, re-hidratação autoritativa e continuidade pós-pagamento | concluída com limitações | [PRD-064-wizard-maquina-estados-rehidratacao-continuidade.md](PRD-064-wizard-maquina-estados-rehidratacao-continuidade.md) |
| 065 | Hubs administrativos dos módulos LV | concluída com limitações | [PRD-065-hubs-administrativos-modulos-lv.md](PRD-065-hubs-administrativos-modulos-lv.md) |
| 066 | Padrão visual e de CRUD em modal | — | [PRD-066-padrao-visual-modal-crud.md](PRD-066-padrao-visual-modal-crud.md) |
| 067 | Paridade de CSS de Pessoas — filtros, KPIs, linhas e responsividade | — | [PRD-067-paridade-css-pessoas-filtros-kpi-responsividade.md](PRD-067-paridade-css-pessoas-filtros-kpi-responsividade.md) |
| 068 | Login unico progressivo | concluída | [PRD-068-rework-limpo-pessoas-fundacao-lv.md](PRD-068-rework-limpo-pessoas-fundacao-lv.md) |
| 069 | Home do LV com governanca visual madura | concluída | [PRD-069-home-governanca-visual.md](PRD-069-home-governanca-visual.md) |
| 070 | Governanca operacional sem bloqueio local | concluída | [PRD-070-governanca-operacional-sem-bloqueio-local.md](PRD-070-governanca-operacional-sem-bloqueio-local.md) |
| 071 | Alinhamento da suite legada ao escopo progressivo | — | [PRD-071-alinhamento-suite-legada-escopo-progressivo.md](PRD-071-alinhamento-suite-legada-escopo-progressivo.md) |
| 072 | Correcoes da home do professor, presenca e mobile | concluída com limitações | [PRD-072-correcoes-home-professor-presenca-mobile.md](PRD-072-correcoes-home-professor-presenca-mobile.md) |
| 073 | Seeds administrativas e bootstrap consistente | concluída com limitações | [PRD-073-seeds-administrative-bootstrap-consistente.md](PRD-073-seeds-administrative-bootstrap-consistente.md) |
| 074 | Papéis operacionais acumuláveis e permissões mínimas | concluída com limitações | [PRD-074-papeis-operacionais-acumulaveis-permissoes.md](PRD-074-papeis-operacionais-acumulaveis-permissoes.md) |
| 075 | Fundação UI, rotas em inglês e CRUD modal | concluída com limitações | [PRD-075-fundacao-ui-rotas-ingles-modal-crud.md](PRD-075-fundacao-ui-rotas-ingles-modal-crud.md) |
| 076 | Auditoria de legado, governança e documentação | concluída com limitações | [PRD-076-auditoria-legado-governanca-documentacao.md](PRD-076-auditoria-legado-governanca-documentacao.md) |
| 077 | CRUD MVP da academia de artes marciais | concluída com limitações | [PRD-077-crud-mvp-academia-artes-marciais.md](PRD-077-crud-mvp-academia-artes-marciais.md) |
| 078 | Rotas ativas com templates ausentes | concluída com limitações | [PRD-078-rotas-ativas-templates-ausentes.md](PRD-078-rotas-ativas-templates-ausentes.md) |
| 079 | Normalizar índice de PRDs duplicadas | concluída | [PRD-079-normalizar-indice-prds-duplicadas.md](PRD-079-normalizar-indice-prds-duplicadas.md) |
| 080 | Refatorar JavaScript sem innerHTML inseguro | concluída com limitações | [PRD-080-refatorar-js-sem-innerhtml.md](PRD-080-refatorar-js-sem-innerhtml.md) |
| 081 | Extrair serviços de cadastro e pagamento do wizard | concluída com limitações | [PRD-081-extrair-servicos-cadastro-pagamento.md](PRD-081-extrair-servicos-cadastro-pagamento.md) |
| 082 | README e requirements-dev alinhados ao LV | concluída | [PRD-082-readme-requirements-dev-governanca.md](PRD-082-readme-requirements-dev-governanca.md) |
| 083 | Arquivar documentação legada em static | concluída | [PRD-083-arquivar-documentacao-legada-static.md](PRD-083-arquivar-documentacao-legada-static.md) |
| 084 | Tokens CSS e remoção de estilo inline | não concluída | [PRD-084-tokens-css-inline-style.md](PRD-084-tokens-css-inline-style.md) |
| 085 | Saida ASCII em management commands no PowerShell | concluída | [PRD-085-saida-ascii-management-commands-powershell.md](PRD-085-saida-ascii-management-commands-powershell.md) |
| 086 | Repasses sem saque antecipado | — | [PRD-086-repasses-sem-saque-antecipado.md](PRD-086-repasses-sem-saque-antecipado.md) |
| 087 | Remover inicial_seed | — | [PRD-087-remover-inicial-seed.md](PRD-087-remover-inicial-seed.md) |
| 088 | Revisão completa do fluxo de cadastro — pré-registro, pagamento sequencial e finalização explícita | — | [PRD-088-revisao-fluxo-cadastro.md](PRD-088-revisao-fluxo-cadastro.md) |
| 089 | CRUD de Planos com Precificação Dinâmica | — | [PRD-089-crud-planos-precificacao-dinamica.md](PRD-089-crud-planos-precificacao-dinamica.md) |
| 090 | Correções de UI do wizard de cadastro | — | [PRD-090-wizard-ui-fixes.md](PRD-090-wizard-ui-fixes.md) |
| 091 | UI de papéis operacionais no formulário de pessoa | concluída | [PRD-091-ui-papeis-operacionais-formulario-pessoa.md](PRD-091-ui-papeis-operacionais-formulario-pessoa.md) |
| 092 | Home split Minha área e Gestão | concluída | [PRD-092-home-split-minha-area-gestao.md](PRD-092-home-split-minha-area-gestao.md) |
| 093 | Responsável iniciar treino e matrícula | concluída | [PRD-093-responsavel-iniciar-treino-matricula.md](PRD-093-responsavel-iniciar-treino-matricula.md) |
| 094 | Check-in aluno com papel duplo e pré-condição do professor | concluída | [PRD-094-checkin-aluno-papel-duplo-precondicao-professor.md](PRD-094-checkin-aluno-papel-duplo-precondicao-professor.md) |
| 095 | Ordem canônica de seeds Obsidian e documentação | concluída | [PRD-095-ordem-canonica-seeds-obsidian-docs.md](PRD-095-ordem-canonica-seeds-obsidian-docs.md) |
| 096 | Encoding UTF-8 do template de cronograma | concluída | [PRD-096-encoding-utf8-template-cronograma.md](PRD-096-encoding-utf8-template-cronograma.md) |
| 097 | Views de calendário órfãs sem rota | concluída | [PRD-097-views-calendario-orfas-sem-rota.md](PRD-097-views-calendario-orfas-sem-rota.md) |
| 098 | Módulo de auditoria operacional | concluída com limitações | [PRD-098-modulo-auditoria-operacional.md](PRD-098-modulo-auditoria-operacional.md) |
| 099 | Permissão de edição de pessoa para apoio | concluída | [PRD-099-permissao-edicao-pessoa-apoio.md](PRD-099-permissao-edicao-pessoa-apoio.md) |
| 100 | Rota Perfis versus papéis operacionais | concluída | [PRD-100-rota-perfis-vs-papeis-operacionais.md](PRD-100-rota-perfis-vs-papeis-operacionais.md) |
| 101 | Loja pública, pré-pedidos e histórico do aluno | concluída | [PRD-101-loja-publica-prepedidos-historico-aluno.md](PRD-101-loja-publica-prepedidos-historico-aluno.md) |
| 102 | CRUD de categoria de material | concluída | [PRD-102-crud-categoria-material.md](PRD-102-crud-categoria-material.md) |
| 103 | Ações de assinatura no detalhe de pessoa | concluída | [PRD-103-acoes-assinatura-detalhe-pessoa.md](PRD-103-acoes-assinatura-detalhe-pessoa.md) |
| 104 | Remoção de código morto no wizard de cadastro (onEnterCheckout) | concluída | [PRD-104-remocao-dead-code-checkout-wizard.md](PRD-104-remocao-dead-code-checkout-wizard.md) |
| 105 | Seção "Meus dependentes" no home do responsável | concluída | [PRD-105-secao-dependentes-home-responsavel.md](PRD-105-secao-dependentes-home-responsavel.md) |
| 106 | Responsável não consegue comprar/ver materiais em nome do dependente | concluída | [PRD-106-responsavel-compra-materiais-para-dependente.md](PRD-106-responsavel-compra-materiais-para-dependente.md) |
| 107 | Instrutor consegue aprovar check-in de aula regular já cancelada | concluída | [PRD-107-aprovar-checkin-aula-cancelada.md](PRD-107-aprovar-checkin-aula-cancelada.md) |
| 108 | Repasse do professor conta aula cancelada; `TeacherFinancialView` é código morto | concluída | [PRD-108-repasse-professor-aula-cancelada-e-view-morta.md](PRD-108-repasse-professor-aula-cancelada-e-view-morta.md) |
| 109 | Calendário administrativo quebra quando aulão cai em feriado | concluída | [PRD-109-crash-calendario-aulao-em-feriado.md](PRD-109-crash-calendario-aulao-em-feriado.md) |
| 110 | Elegibilidade de graduação conta aula/aulão cancelado | concluída | [PRD-110-graduacao-conta-aula-cancelada.md](PRD-110-graduacao-conta-aula-cancelada.md) |
| 111 | Seeds de homologacao de cadastro N:N | concluída com limitações | [PRD-111-seeds-homologacao-cadastro-nn.md](PRD-111-seeds-homologacao-cadastro-nn.md) |
| 112 | Solicitacao de acesso administrativo pendente | concluída | [PRD-112-solicitacao-acesso-administrativo-pendente.md](PRD-112-solicitacao-acesso-administrativo-pendente.md) |
| 113 | Solicitacao de turmas e horarios por professor | concluída | [PRD-113-solicitacao-turmas-horarios-professor.md](PRD-113-solicitacao-turmas-horarios-professor.md) |
| 114 | Elegibilidade do plano Veterano (ex-Fidelidade) por tempo de casa | concluída | [PRD-114-elegibilidade-plano-veterano.md](PRD-114-elegibilidade-plano-veterano.md) |
| 115 | Wizard de perfis operacionais sequenciais | — | [PRD-115-wizard-perfis-operacionais-sequenciais.md](PRD-115-wizard-perfis-operacionais-sequenciais.md) |
| 116 | Home do aluno com permissoes, cronograma modal e fidelidade | — | [PRD-116-home-aluno-permissoes-cronograma-fidelidade.md](PRD-116-home-aluno-permissoes-cronograma-fidelidade.md) |
| 117 | Fidelidade contratual para planos recorrentes | — | [PRD-117-fidelidade-contratual-planos-recorrentes.md](PRD-117-fidelidade-contratual-planos-recorrentes.md) |
| 118 | Adicionar dependente pós-matrícula | — | [PRD-118-adicionar-dependente-pos-matricula.md](PRD-118-adicionar-dependente-pos-matricula.md) |
| 119 | Dependente com materiais, idempotência e CPF pendente | concluída com limitações | [PRD-119-dependente-materiais-idempotencia-cpf.md](PRD-119-dependente-materiais-idempotencia-cpf.md) |
| 120 | Dependente em modal na home | concluída | [PRD-120-dependente-modal-home.md](PRD-120-dependente-modal-home.md) |
| 121 | Home do cliente com dependentes, mensalidades e CRUD modal | não concluída | [PRD-121-home-cliente-dependentes-mensalidades-crud.md](PRD-121-home-cliente-dependentes-mensalidades-crud.md) |
| 122 | Desfazer check-in pendente do aluno | concluída com limitações | [PRD-122-desfazer-checkin-pendente-aluno.md](PRD-122-desfazer-checkin-pendente-aluno.md) |
| 123 | Modal da conta do cliente com edição e exclusão | concluída | [PRD-123-modal-conta-cliente-editar-excluir.md](PRD-123-modal-conta-cliente-editar-excluir.md) |
| 124 | Dependente com upgrade para plano familiar | concluída | [PRD-124-dependente-upgrade-plano-familiar.md](PRD-124-dependente-upgrade-plano-familiar.md) |
| 125 | Sincronizacao remota do upgrade familiar Stripe | — | [PRD-125-sincronizacao-upgrade-familiar-stripe.md](PRD-125-sincronizacao-upgrade-familiar-stripe.md) |
| 126 | Prevenir cobrança Stripe duplicada no mesmo cartão entre titular e dependente | concluída | [PRD-126-prevenir-cobranca-duplicada-mesmo-cartao-dependente.md](PRD-126-prevenir-cobranca-duplicada-mesmo-cartao-dependente.md) |
| 127 | Desconto família como modificador de tier único (rework de precificação) | concluída | [PRD-127-desconto-familia-tier-unico-precificacao.md](PRD-127-desconto-familia-tier-unico-precificacao.md) |
| 128 | CRUD PlanTier/PlanPrice, UI de desconto e bloqueio real de cancelamento na carência | concluída | [PRD-128-crud-plan-tier-price-ui-desconto-bloqueio-cancelamento.md](PRD-128-crud-plan-tier-price-ui-desconto-bloqueio-cancelamento.md) |
| 129 | Migrar cadastro público (`register.js`) para o catálogo PlanTier/PlanPrice | concluída | [PRD-129-migrar-cadastro-publico-catalogo-plantier-planprice.md](PRD-129-migrar-cadastro-publico-catalogo-plantier-planprice.md) |
| 130 | Migrar troca de plano (upgrade/downgrade) para o catálogo PlanTier/PlanPrice | concluída | [PRD-130-migrar-troca-plano-catalogo-plantier-planprice.md](PRD-130-migrar-troca-plano-catalogo-plantier-planprice.md) |
| 131 | Corrigir professor presente por padrão ao cancelar/restaurar aula | concluída | [PRD-131-corrigir-professor-presente-padrao-cancelar-restaurar-aula.md](PRD-131-corrigir-professor-presente-padrao-cancelar-restaurar-aula.md) |
| 132 | Transição livre entre planos + pausa de mensalidade (atestado e trancamento) | concluída | [PRD-132-transicao-livre-planos-pausa-mensalidade.md](PRD-132-transicao-livre-planos-pausa-mensalidade.md) |
| 133 | Indicador de forma de pagamento + trocar cartão Stripe + histórico de cobrança falhada | concluída | [PRD-133-indicador-pagamento-trocar-cartao-stripe.md](PRD-133-indicador-pagamento-trocar-cartao-stripe.md) |
| 134 | Histórico de eventos de assinatura/família — timeline informativa (cliente) + auditoria técnica (admin) | concluída | [PRD-134-historico-eventos-assinatura-familia-cliente-admin.md](PRD-134-historico-eventos-assinatura-familia-cliente-admin.md) |
| 135 | Cobrança recorrente automatizada Asaas (sincronizada com desconto família) + backfill de eventos históricos da timeline | concluída | [PRD-135-cobranca-recorrente-asaas-backfill-timeline.md](PRD-135-cobranca-recorrente-asaas-backfill-timeline.md) |
| 136 | Falha silenciosa no botão "Pagar mensalidade" + confirmação do fluxo de endereço no Asaas | concluída | [PRD-136-falha-silenciosa-pagar-mensalidade-endereco-asaas.md](PRD-136-falha-silenciosa-pagar-mensalidade-endereco-asaas.md) |
| 137 | Recorrente Stripe ausente em ciclos longos + parcelamento Asaas quebrado no catálogo novo | concluída | [PRD-137-recorrente-stripe-ciclos-parcelamento-asaas-catalogo-novo.md](PRD-137-recorrente-stripe-ciclos-parcelamento-asaas-catalogo-novo.md) |
| 138 | Auditoria arquitetural — fluxo único e consistência do MVP | concluída com limitações | [PRD-138-auditoria-arquitetural-fluxo-unico-consistencia.md](PRD-138-auditoria-arquitetural-fluxo-unico-consistencia.md) |
| 139 | Auditoria de cobertura total — inventário arquivo-a-arquivo | concluída com limitações | [PRD-139-auditoria-cobertura-total-inventario-completo.md](PRD-139-auditoria-cobertura-total-inventario-completo.md) |
| 140 | Correções do wizard de "Adicionar dependente" | concluída | [PRD-140-dependente-wizard-correcoes.md](PRD-140-dependente-wizard-correcoes.md) |
| 141 | Crítica profunda do frontend — problemas identificados | concluída | [PRD-141-critica-frontend-problemas.md](PRD-141-critica-frontend-problemas.md) |
| 142 | Crítica backend — performance e queries | concluída | [PRD-142-critica-backend-performance.md](PRD-142-critica-backend-performance.md) |
| 143 | Crítica MVT — views, models e forms | concluída | [PRD-143-critica-views-models-forms-mvt.md](PRD-143-critica-views-models-forms-mvt.md) |
| 144 | Pendências de implementação — varredura jul/2026 (PRD-138 a 143) | concluída | [PRD-144-pendencias-implementacao-varredura-jul-2026.md](PRD-144-pendencias-implementacao-varredura-jul-2026.md) |
| 145 | Auditoria operacional de cadastros, pagamentos e documentação | concluída com limitações | [PRD-145-auditoria-operacional-cadastros-documentacao.md](PRD-145-auditoria-operacional-cadastros-documentacao.md) |
| 146 | Professor público e vínculo com turmas existentes | concluída | [PRD-146-professor-publico-vinculo-turmas-existentes.md](PRD-146-professor-publico-vinculo-turmas-existentes.md) |
| 147 | Homologação funcional pós-cadastro | concluída com limitações | [PRD-147-homologacao-funcional-pos-cadastro.md](PRD-147-homologacao-funcional-pos-cadastro.md) |
| 148 | Ativação do repasse do professor cadastrado publicamente | concluída com limitações | [PRD-148-repasse-professor-cadastro-publico.md](PRD-148-repasse-professor-cadastro-publico.md) |
| 149 | Requirements único — eliminar `requirements-dev.txt` | concluída | [PRD-149-requirements-unico-sem-dev.md](PRD-149-requirements-unico-sem-dev.md) |
| 150 | Homologação cadastros + correção professor `existing` e docs | concluída | [PRD-150-homologacao-cadastros-professor-propose-docs.md](PRD-150-homologacao-cadastros-professor-propose-docs.md) |
| 151 | Fechamento de lacunas pós-auditoria — admin.py, testes de troca/cancelamento e homologação real via navegador | concluída com limitações | [PRD-151-fechamento-lacunas-admin-testes-homologacao-real.md](PRD-151-fechamento-lacunas-admin-testes-homologacao-real.md) |
| 152 | Ciclo de troca de senha — logado, esquecida com senha padrão e revisão do admin | concluída | [PRD-152-troca-senha-visual-validacao-revisao-admin.md](PRD-152-troca-senha-visual-validacao-revisao-admin.md) |
| 153 | Corrigir filtro "Período de cobrança" para planos recorrentes Stripe no cadastro público | concluída | [PRD-153-corrigir-filtro-periodo-recorrente-stripe-cadastro.md](PRD-153-corrigir-filtro-periodo-recorrente-stripe-cadastro.md) |
| 154 | Natureza MVP descartável e remoção dos gates de ambiente | não iniciada | [PRD-154-natureza-mvp-e-remocao-de-gates.md](PRD-154-natureza-mvp-e-remocao-de-gates.md) |
| 155 | Gate condicional de autorização — alinhar skills ao AGENTS.md | concluída com limitações | [PRD-155-gate-condicional-de-autorizacao.md](PRD-155-gate-condicional-de-autorizacao.md) |
| 156 | Skills — estrutura, comando real, índice de PRD e sincronização verificável | concluída com limitações | [PRD-156-skills-estrutura-comando-real-e-sincronizacao.md](PRD-156-skills-estrutura-comando-real-e-sincronizacao.md) |
| 157 | Desduplicação dos contratos e higiene do CLAUDE.md | não iniciada | [PRD-157-desduplicacao-e-higiene-dos-contratos.md](PRD-157-desduplicacao-e-higiene-dos-contratos.md) |
| 158 | Slash commands para o ciclo operacional repetido | superada | [PRD-158-slash-commands-do-ciclo-repetido.md](PRD-158-slash-commands-do-ciclo-repetido.md) |
| 159 | Hardening da infraestrutura local e CI | concluída com limitações | [PRD-159-hardening-infraestrutura-local-e-ci.md](PRD-159-hardening-infraestrutura-local-e-ci.md) |
| 160 | Reconciliação das variáveis de ambiente | concluída | [PRD-160-reconciliacao-das-variaveis-de-ambiente.md](PRD-160-reconciliacao-das-variaveis-de-ambiente.md) |
| 161 | Slash commands, índice de PRDs e higiene do repositório | concluída | [PRD-161-slash-commands-indice-e-higiene.md](PRD-161-slash-commands-indice-e-higiene.md) |
| 162 | Reset remoto endurecido, deploy documentado e observabilidade | concluída com limitações | [PRD-162-reset-remoto-deploy-e-observabilidade.md](PRD-162-reset-remoto-deploy-e-observabilidade.md) |
| 163 | Validador de skills e homogeneidade do CI | concluída | [PRD-163-validador-de-skills-e-homogeneidade-do-ci.md](PRD-163-validador-de-skills-e-homogeneidade-do-ci.md) |
| 164 | Autocontenção dos contratos e padronização do CI | concluída | [PRD-164-autocontencao-dos-contratos-e-padronizacao-do-ci.md](PRD-164-autocontencao-dos-contratos-e-padronizacao-do-ci.md) |
| 165 | Runner de teste honesto e dependências diretas | concluída | [PRD-165-runner-de-teste-honesto-e-dependencias-diretas.md](PRD-165-runner-de-teste-honesto-e-dependencias-diretas.md) |
| 166 | Densidade dos contratos e inventário de operação | concluída | [PRD-166-densidade-dos-contratos-e-inventario-de-operacao.md](PRD-166-densidade-dos-contratos-e-inventario-de-operacao.md) |
| 167 | Workflow secundário de CI | concluída | [PRD-167-workflow-secundario-de-ci.md](PRD-167-workflow-secundario-de-ci.md) |
| 168 | Guarda de número duplicado no índice de PRD e higiene de settings | concluída | [PRD-168-guarda-de-numero-duplicado-e-higiene-de-settings.md](PRD-168-guarda-de-numero-duplicado-e-higiene-de-settings.md) |
| 169 | Nivelamento dos contratos de protocolo | concluída | [PRD-169-nivelamento-dos-contratos-de-protocolo.md](PRD-169-nivelamento-dos-contratos-de-protocolo.md) |
| 170 | Nivelamento dos contratos de produto | concluída com limitações | [PRD-170-nivelamento-dos-contratos-de-produto.md](PRD-170-nivelamento-dos-contratos-de-produto.md) |
| 171 | Nivelamento de infraestrutura e ambiente | concluída com limitações | [PRD-171-nivelamento-de-infraestrutura-e-ambiente.md](PRD-171-nivelamento-de-infraestrutura-e-ambiente.md) |
| 172 | Limpeza estrutural e código sem comentário | concluída | [PRD-172-limpeza-estrutural-e-codigo-sem-comentario.md](PRD-172-limpeza-estrutural-e-codigo-sem-comentario.md) |
| 173 | Núcleo comum do contrato visual | concluída | [PRD-173-nucleo-comum-do-contrato-visual.md](PRD-173-nucleo-comum-do-contrato-visual.md) |
| 174 | Taxonomia do runbook operacional | concluída | [PRD-174-taxonomia-do-runbook-operacional.md](PRD-174-taxonomia-do-runbook-operacional.md) |
| 175 | Vocabulário único de tokens CSS | concluída | [PRD-175-vocabulario-unico-de-tokens-css.md](PRD-175-vocabulario-unico-de-tokens-css.md) |
| 176 | Folha de tema única | concluída | [PRD-176-folha-de-tema-unica.md](PRD-176-folha-de-tema-unica.md) |
| 177 | Agentes autônomos e acionadores | concluída com limitações | [PRD-177-agentes-autonomos-e-acionadores.md](PRD-177-agentes-autonomos-e-acionadores.md) |
