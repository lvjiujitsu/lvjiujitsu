# PRD-008: Ajustar painéis de professor e aluno para cronograma, check-in e histórico de presença

## Resumo do que será implementado
Ajustar o painel do professor para exibir aulas do dia, acesso ao cronograma e visualização de check-ins (incluindo histórico por aula com lista de alunos presentes). Ajustar o painel do aluno para exibir histórico de presença confirmada por check-in.

## Tipo de demanda
Correção pontual com melhoria funcional de dashboard.

## Problema atual
- O painel do professor não exibe aulas do dia nem histórico útil de presença.
- O professor não consegue visualizar, no próprio painel, quais alunos fizeram check-in nas aulas sob sua responsabilidade.
- O painel do aluno não exibe histórico de presença confirmada por check-in.

## Objetivo
- Exibir no painel do professor: aulas do dia, lista de alunos com check-in no dia, histórico de presença por aula e atalho funcional para cronograma.
- Exibir no painel do aluno: histórico de aulas com presença confirmada.
- Permitir que professor autenticado acesse a rota de cronograma já existente.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `system/views/portal_mixins.py`
- `system/views/__init__.py`
- `system/urls.py`
- `system/services/class_calendar.py`
- `system/models/calendar.py`
- `system/models/class_schedule.py`
- `system/models/class_group.py`
- `system/models/class_membership.py`
- `system/models/person.py`
- `system/models/__init__.py`
- `system/constants.py`
- `system/middleware.py`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `templates/calendar/student_schedule.html`
- `templates/base.html`
- `static/system/css/portal/portal.css`
- `static/system/css/billing/billing.css`
- `system/tests/test_views.py`
- `system/tests/test_calendar.py`
- `system/tests/test_class_portal_views.py`

### Arquivos adjacentes consultados
- `system/services/class_overview.py` (busca por padrões de professor/turma)
- `system/services/class_catalog.py` (busca por padrões de consulta de turma/professor)

### Internet / documentação oficial
- Não aplicável para esta demanda (comportamento é interno ao projeto e ao domínio atual).

### MCPs / ferramentas verificadas
- `read` — ok
- `glob` — ok
- `grep` — ok
- `bash` — pendente para validação final (test/check)

### Limitações encontradas
- Não há tela dedicada de histórico de presença; a entrega será feita no dashboard existente.

## Prompt de execução
### Persona
Agente Django seguindo SDD + TDD + MVT com serviços para regra de negócio.

### Ação
Implementar exibição de cronograma/aulas/check-ins/histórico para professor e histórico de presença para aluno.

### Contexto
O portal já possui check-in e agenda para aluno, porém o dashboard do professor está incompleto e o aluno não possui histórico de presença visível no painel.

### Restrições
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

### Critérios de aceite
- [ ] Professor visualiza aulas do dia no dashboard (verificável por teste de view/template)
- [ ] Professor visualiza alunos com check-in nas aulas do dia (verificável por teste)
- [ ] Professor visualiza histórico de presença por aula (verificável por teste)
- [ ] Professor consegue acessar cronograma pela rota de agenda (verificável por teste)
- [ ] Aluno visualiza histórico de presença confirmada no dashboard (verificável por teste)
- [ ] `manage.py test --verbosity 2` sem falhas
- [ ] `manage.py check` sem erros

### Evidências esperadas
- testes de views passando
- checks de projeto passando
- renderização dos dashboards com as novas seções

### Formato de saída
Código + testes + evidências de validação.

## Escopo
- Serviços de calendário para dados do dashboard de professor e histórico do aluno.
- Contexto de `InstructorHomeView` e `StudentHomeView`.
- Template do dashboard do professor.
- Template do dashboard do aluno.
- Ajuste de autorização para rota de cronograma do aluno também ao professor.
- Estilos CSS necessários para legibilidade das novas seções.
- Testes de view para os novos comportamentos.

## Fora do escopo
- Nova página dedicada de relatórios.
- Exportações/CSV.
- Mudanças de schema.

## Arquivos impactados
- `system/services/class_calendar.py`
- `system/views/home_views.py`
- `system/views/calendar_views.py`
- `templates/home/instructor/dashboard.html`
- `templates/home/student/dashboard.html`
- `static/system/css/portal/portal.css`
- `templates/base.html`
- `system/tests/test_views.py`

## Riscos e edge cases
- Professor com turma sem sessão criada no dia deve ver aula com zero check-ins.
- Sessões canceladas/feriado devem manter sinalização correta.
- Aulas especiais (aulões) precisam aparecer no histórico quando vinculadas ao professor/aluno.

## Regras e restrições
- SDD antes de código
- TDD para implementação
- sem hardcode
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

## Plano
- [x] 1. Contexto e leitura integral
- [ ] 2. Testes (Red)
- [ ] 3. Implementação (Green)
- [ ] 4. Refatoração (Refactor)
- [ ] 5. Validação completa
- [ ] 6. Limpeza final
- [ ] 7. Atualização documental

## Validação visual
### Desktop
- Dashboard do professor e do aluno com as novas seções renderizando sem erro.

### Mobile
- Conferir legibilidade de cards/tabela de histórico.

### Console do navegador
- Sem erros JS críticos.

### Terminal
- Sem stack trace ao abrir os dashboards.

## Validação ORM
### Banco
- Não há alteração de schema.

### Shell checks
- Não aplicável além de testes de view e services.

### Integridade do fluxo
- Check-ins existentes são refletidos em dashboards sem alterar modelo.

## Validação de qualidade
### Sem hardcode
Dados vêm de consultas dinâmicas de sessão/check-in.

### Sem estruturas condicionais quebradiças
Uso de guard clauses e composição de serviços.

### Sem `except: pass`
Nenhum uso.

### Sem mascaramento de erro
Reaproveita tratamento explícito já existente.

### Sem comentários e docstrings desnecessários
Manter código autoexplicativo.

## Evidências
(preencher após execução de testes/check)

## Implementado
(preencher ao final)

## Desvios do plano
(preencher ao final)

## Pendências
- Validação visual em navegador real (Playwright/browser) após conclusão técnica.
