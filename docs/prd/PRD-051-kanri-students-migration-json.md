# PRD-051: JSON de migração de alunos Kanri

## Resumo do que será implementado
Criar artefatos JSON auditáveis, um por aluno, com os dados extraídos do Kanri para apoiar a migração futura para o sistema LV JIU JITSU.

## Tipo de demanda
Regeneração documental e preparação de dados de migração.

## Problema atual
Os dados dos alunos estão no Kanri e ainda não existe um arquivo local versionável com a captura estruturada para análise, conferência e futura importação.

## Objetivo
Adicionar a pasta `static/initial_data/kanri_students_migration/` com um JSON por aluno, contendo apenas os campos operacionais pedidos para revisão da migração: e-mail, nome, sexo, nascimento, documento, telefone, endereço, responsável, financeiro, evolução e histórico, sem criar registros no banco e sem criar migrações Django.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `system/models/person.py`
- `system/forms/person_forms.py`
- `system/models/graduation.py`
- `system/models/class_membership.py`
- `system/models/plan.py`
- `system/models/membership.py`
- `system/constants.py`
- `static/initial_data/initial_teachers.json`
- `static/initial_data/initial_administrative.json`
- `static/initial_data/seed_system_initial_belt_ranks.json`
- `static/initial_data/seed_system_initial_class_categories.json`
- `static/initial_data/seed_system_initial_class_catalog.json`
- `system/management/commands/seed_system_initial_teacher.py`
- `docs/prd/PRD-031-padronizar-json-seeds.md`

### Arquivos adjacentes consultados
- `static/initial_data/`
- `docs/prd/`
- `system/management/commands/`

### Internet / documentação oficial
- Não aplicável. A tarefa usa página autenticada já aberta pelo usuário e contratos locais do repositório.

### MCPs / ferramentas verificadas
- PowerShell — OK — versão `7.6.0`
- Python local — OK — `.\.venv\Scripts\python.exe --version` retornou `Python 3.12.10`
- Browser MCP — OK — sessão autenticada no Kanri acessível em `https://kanri-app.com.br/teacher/students`
- ripgrep — OK — `rg --files` e buscas de contrato executadas

### Limitações encontradas
- O workspace já possuía alterações não relacionadas antes desta tarefa; elas não serão revertidas.
- Este PRD não implementa importador nem cria cadastros no banco local.
- Dados pessoais sensíveis serão mantidos apenas no artefato local solicitado pelo usuário.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD + governança de dados de migração.

### Ação
Criar arquivos JSON individuais de migração com os alunos extraídos do Kanri.

### Contexto
O projeto usa dados iniciais em `static/initial_data/`; os modelos atuais de destino incluem `Person`, `PortalAccount`, `Graduation`, `ClassEnrollment` e `Membership`, mas esta etapa deve produzir apenas um artefato de dados para conferência.

### Restrições
- sem criar registros no banco
- sem criar ou editar migrations
- sem executar `makemigrations` ou `migrate`
- sem incluir tokens de autenticidade, senhas ou campos de formulário descartáveis
- remover metadados, URLs, imagens, grupos auxiliares, IDs de gateway e campos não solicitados
- validação obrigatória de JSON

### Critérios de aceite
- [x] A pasta `static/initial_data/kanri_students_migration/` existe.
- [x] Existe um arquivo JSON por aluno extraído do Kanri.
- [x] Cada JSON possui apenas os campos de topo `email`, `nome`, `sexo`, `nascimento`, `tipo_documento`, `n_documento`, `telefone`, `endereco`, `responsavel`, `financeiro`, `evolucao` e `historico`.
- [x] Campos de senha, token CSRF/autenticidade e submits não são persistidos.
- [x] Todos os JSONs são parseáveis por Python.
- [x] A contagem de arquivos bate com a listagem extraída do Kanri.
- [x] O JSON consolidado `static/initial_data/initial_kanri_students_migration.json` não permanece como artefato final.
- [x] Nenhuma migration Django é criada ou alterada por esta tarefa.

### Evidências esperadas
- Validação Python carregando o JSON e conferindo a contagem.
- `manage.py check`.
- `git status --short` mostrando apenas arquivos desta tarefa além de alterações preexistentes.

### Formato de saída
PRD + pasta de JSONs individuais de migração + evidências de validação.

## Escopo
- Extrair listagem de alunos do Kanri.
- Entrar nas páginas de edição dos alunos via sessão autenticada do navegador.
- Capturar e manter apenas campos principais, endereço, responsável, financeiro, evolução e histórico quando presentes no DOM.
- Criar JSONs locais individuais para revisão.

## Fora do escopo
- Criar seed/management command de importação.
- Criar registros `Person`, `PortalAccount`, `Graduation`, `ClassEnrollment` ou `Membership`.
- Baixar ou manter imagens/fotos.
- Manter metadados de origem, URLs, grupos auxiliares, IDs de gateway ou campos não solicitados dentro dos JSONs finais.
- Alterar templates, views, services, models ou migrations.

## Arquivos impactados
- `docs/prd/PRD-051-kanri-students-migration-json.md`
- `static/initial_data/kanri_students_migration/*.json`

## Riscos e edge cases
- Dados do Kanri podem estar incompletos ou inconsistentes; o JSON deve preservar o valor bruto.
- Algumas faixas infantis não cabem diretamente em `Person.jiu_jitsu_belt`; nesses casos o mapeamento deve usar snapshot de graduação e manter o campo bruto.
- Alunos podem ter múltiplos grupos; o JSON deve preservar todos os grupos selecionados e não escolher turma única de forma silenciosa.
- Histórico financeiro e de presença pode estar paginado ou parcialmente renderizado pelo Kanri; o JSON deve registrar o que foi observado na página.

## Regras e restrições
- SDD antes de código/dados persistidos
- sem hardcode de credenciais
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [x] 2. Contratos e modelagem
- [x] 3. Extração da listagem Kanri
- [x] 4. Extração das páginas de edição
- [x] 5. Geração do JSON
- [x] 6. Validação completa
- [x] 7. Limpeza final
- [x] 8. Atualização documental

## Validação visual
### Desktop
Não aplicável; não há alteração de UI no sistema LV.
### Mobile
Não aplicável.
### Console do navegador
Não aplicável para o sistema LV; o Browser MCP será usado apenas como fonte de extração do Kanri.
### Terminal
Validar JSON e `manage.py check`.

## Validação ORM
### Banco
Não haverá alteração de banco.
### Shell checks
Carregar o JSON e conferir metadados/contagem.
### Integridade do fluxo
Não há fluxo Django alterado nesta etapa.

## Validação de qualidade
### Sem hardcode
O JSON preserva dados extraídos; não adiciona credenciais nem segredos.
### Sem estruturas condicionais quebradiças
Não aplicável a código de produção.
### Sem `except: pass`
Não aplicável.
### Sem mascaramento de erro
Falhas de extração devem ser registradas no JSON em `extraction_errors`.
### Sem comentários e docstrings desnecessários
Não aplicável.

## Evidências
- Browser MCP — listagem Kanri lida em 14 páginas, totalizando 199 alunos.
- Browser MCP — páginas de edição processadas: 199 de 199; falhas: 0.
- Arquivo consolidado temporário gerado e depois removido: `static/initial_data/initial_kanri_students_migration.json`.
- Pasta final gerada: `static/initial_data/kanri_students_migration/`.
- Arquivos individuais gerados: 199.
- `.\.venv\Scripts\python.exe -c "...json.loads..."` — passou: `{'students': 199, 'list_record_count': 199, 'detail_record_count': 199, 'errors': 0}`.
- Validação dos arquivos individuais — passou: `{'files': 199, 'unique_source_ids': 199, 'first': '100531-felipe-juca-delmondes.json', 'last': '99901-maicon-douglas.json'}`.
- Sanitização final — passou: `{'files': 199, 'top_level_fields': ['email', 'endereco', 'evolucao', 'financeiro', 'historico', 'n_documento', 'nascimento', 'nome', 'responsavel', 'sexo', 'telefone', 'tipo_documento']}`.
- Busca por metadados/campos removidos — sem ocorrências para `schema_version`, `source`, `target_`, `field_mapping`, `extraction`, `student_id`, `edit_url`, `selected_groups`, `photo`, `stripe`, `asaas`, `password`, `authenticity_token`, `csrf`.
- `Test-Path static\initial_data\initial_kanri_students_migration.json` — retornou `False`.
- Validação recursiva de campos proibidos — passou: `{'forbidden_password_or_auth_fields': 0}`.
- `.\.venv\Scripts\python.exe manage.py check` — passou: `System check identified no issues (0 silenced).`

## Implementado
- Criada a pasta `static/initial_data/kanri_students_migration/`.
- Criados 199 arquivos JSON individuais, um por aluno, nomeados no padrão `<source_id>-<slug-do-nome>.json`.
- Cada arquivo foi sanitizado para conter somente: `email`, `nome`, `sexo`, `nascimento`, `tipo_documento`, `n_documento`, `telefone`, `endereco`, `responsavel`, `financeiro`, `evolucao` e `historico`.
- Removido o arquivo consolidado `static/initial_data/initial_kanri_students_migration.json` para evitar um artefato "com tudo".
- Removidos metadados, URLs, imagens, grupos auxiliares, IDs Stripe/Asaas, senha, autenticação, CSRF, token e submit.

## Desvios do plano
- Nenhum desvio funcional.
- A captura de tabelas internas preserva apenas linhas renderizadas no DOM da página de edição do Kanri; se o Kanri paginar internamente alguma aba, a paginação deve ser tratada em etapa futura.

## Pendências
- Criar importador/seed futuro para transformar este JSON em `Person`, `Graduation`, `ClassEnrollment`, `PortalAccount` e `Membership`.
- Conferir manualmente dados sensíveis e campos ambíguos antes de qualquer importação real.
