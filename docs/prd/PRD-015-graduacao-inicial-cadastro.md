# PRD-015: Graduação inicial no cadastro

## Resumo do que será implementado
Garantir que alunos cadastrados sem experiência prévia em jiu jitsu recebam automaticamente a faixa inicial aplicável à idade, com graduação real registrada no módulo de graduação.

## Tipo de demanda
Correção pontual de regra de cadastro com testes automatizados.

## Problema atual
O formulário limpa corretamente os dados de arte marcial quando o aluno informa que nunca treinou, mas o serviço de cadastro só cria graduação quando existe faixa legada informada. Assim, alunos iniciantes podem ficar sem graduação registrada.

## Objetivo
Ao cadastrar aluno titular, dependente ou persona de teste sem histórico de jiu jitsu, criar uma graduação inicial com grau 0 usando a primeira faixa ativa compatível com a idade.

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`
- `CLAUDE.md`
- `system/services/graduation.py`
- `system/services/registration.py`
- `system/models/graduation.py`
- `system/models/person.py`
- `system/forms/registration_forms.py`
- `system/tests/test_graduation.py`
- `system/tests/test_forms.py`
- `system/services/registration_checkout.py`
- `system/forms/__init__.py`
- `system/constants.py`
- `system/models/category.py`
- `system/models/__init__.py`
- `system/management/commands/seed_test_personas.py`

### Arquivos adjacentes consultados
- `system/services/seeding.py`
- `system/tests/test_views.py`
- `system/tests/*.py`

### Internet / documentação oficial
- Não aplicável. A mudança usa contratos locais do Django e modelos existentes.

### MCPs / ferramentas verificadas
- PowerShell — OK — comandos de leitura executados.
- `.venv` Python — OK — versão verificada anteriormente no preflight.
- Django — OK — versão verificada anteriormente no preflight.

### Limitações encontradas
- `rg` falhou com acesso negado no ambiente; consultas foram feitas com PowerShell.
- `system/services/seeding.py` e `system/tests/test_views.py` são grandes e tiveram saída truncada na interface; as seções diretamente impactadas foram consultadas por busca contextual.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django seguindo SDD + TDD + MVT.

### Ação
Implementar graduação inicial automática para alunos sem experiência prévia.

### Contexto
O cadastro público e os seeds de personas criam pessoas e contas de portal. O módulo de graduação já possui `BeltRank`, `Graduation` e regras sem necessidade de migração.

### Restrições
- sem hardcode de faixa fixa quando houver faixa inicial compatível por idade
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória

### Critérios de aceite
- [ ] Ao cadastrar aluno titular adulto sem experiência, deve existir graduação inicial na faixa branca adulta/grau 0.
- [ ] Ao cadastrar dependente infantil sem experiência, deve existir graduação inicial infantil/grau 0.
- [ ] Aluno com histórico informado deve manter a graduação importada do histórico.
- [ ] Personas de teste criadas por seed devem receber graduação inicial compatível quando não houver histórico.
- [ ] O form deve continuar limpando dados manuais quando a resposta for “Não”.

### Evidências esperadas
- Testes focados passando.
- `manage.py check` passando.
- Suíte Django passando.

### Formato de saída
Código implementado + testes + evidências de validação.

## Escopo
Serviços de graduação/cadastro/seeding e testes automatizados relacionados.

## Fora do escopo
Alterações visuais, migrações, novas faixas, mudança no wizard de cadastro e alteração em regras de mensalidade.

## Arquivos impactados
- `system/services/graduation.py`
- `system/services/registration.py`
- `system/services/seeding.py`
- `system/tests/test_graduation.py`
- `docs/prd/PRD-015-graduacao-inicial-cadastro.md`

## Riscos e edge cases
- Ausência de data de nascimento impede resolver idade.
- Ausência de faixas ativas impede criar graduação inicial.
- Faixas infantil e adulta se sobrepõem aos 16/17 anos; a ordenação deve escolher a primeira faixa compatível cadastrada.

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
- [x] 2. Contratos e modelagem
- [x] 3. Testes (Red)
- [x] 4. Implementação (Green)
- [x] 5. Refatoração (Refactor)
- [x] 6. Validação completa
- [x] 7. Limpeza final
- [x] 8. Atualização documental

## Validação visual
### Desktop
Não aplicável inicialmente, pois não há alteração visual.

### Mobile
Não aplicável inicialmente, pois não há alteração visual.

### Console do navegador
Não aplicável inicialmente.

### Terminal
- `.\.venv\Scripts\python.exe manage.py check` — OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_forms system.tests.test_graduation --verbosity 2` — 32 testes OK.
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_models --verbosity 2` — 11 testes OK.
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 312 testes OK.

## Validação ORM
### Banco
Validado por banco de teste Django em memória durante a suíte.

### Shell checks
`manage.py check` executado sem issues.

### Integridade do fluxo
Formulário de cadastro, serviço de cadastro, seed de personas de teste e progresso de graduação cobertos por testes.

## Validação de qualidade
### Sem hardcode
Faixa inicial resolvida por consulta dinâmica em `BeltRank` ativo, usando idade e `display_order`.

### Sem estruturas condicionais quebradiças
Implementação com guard clauses e helpers pequenos.

### Sem `except: pass`
Nenhum `except: pass` introduzido.

### Sem mascaramento de erro
Quando não há faixa inicial compatível, o serviço levanta `ValueError` explícito.

### Sem comentários e docstrings desnecessários
Nenhum comentário ou docstring novo foi necessário.

## Evidências
- Red inicial: testes falharam por ausência de `ensure_initial_graduation_for_beginner`.
- Green focado: `InitialGraduationRegistrationTestCase` passou com 5 testes.
- Seed de personas: `TestPersonaInitialGraduationTestCase` passou.
- Regressão completa: `manage.py test --verbosity 2` passou com 312 testes.

## Implementado
- Helper de faixa inicial por idade em `system/services/graduation.py`.
- Criação idempotente de graduação inicial para iniciantes.
- Hook no cadastro real para aluno/dependente.
- Hook nos seeds para personas e cadastros de teste.
- Testes de titular adulto, outra arte marcial sem jiu jitsu, dependente infantil, histórico prévio, idempotência e personas de teste.

## Desvios do plano
Sem desvios funcionais. Foi necessário semear faixas nos fixtures antigos de cadastro para que a regra obrigatória tivesse catálogo disponível.

## Pendências
Nenhuma pendência identificada.
