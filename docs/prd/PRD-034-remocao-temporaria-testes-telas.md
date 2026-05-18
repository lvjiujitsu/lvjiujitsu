# PRD-034: Remocao Temporaria de Testes de Telas

## Resumo do que será implementado
Remover temporariamente testes automatizados acoplados a telas/templates que estao sendo reimplementados.

## Tipo de demanda
Correcao pontual

## Problema atual
A suite falhava com 5 falhas e 109 erros por contratos antigos de UI, templates ausentes e rotas de tela que estao em reimplementacao.

## Objetivo
Deixar a suite de dominio, services, models, forms, commands e seeds verde enquanto as telas sao recriadas.

## Context Ledger
### Arquivos lidos integralmente
- `CLAUDE.md`
- `system/urls.py`
- `system/views/home_views.py`
- `system/views/person_views.py`
- `templates/login/login_form.html`
- `system/tests/test_views.py`
- `system/tests/test_plan_views.py`
- `system/tests/test_product_views.py`
- `system/tests/test_class_portal_views.py`

### Arquivos adjacentes consultados
- `system/tests/test_calendar.py`
- `system/tests/test_graduation.py`
- listagem de `templates/`

### Internet / documentação oficial
- Nao aplicavel.

### MCPs / ferramentas verificadas
- PowerShell — status ok — execucao de testes e checks.

### Limitações encontradas
- Cobertura automatizada de telas foi removida temporariamente por decisao do usuario.

## Prompt de execução
### Persona
Agente de desenvolvimento Django seguindo SDD + validacao por teste.

### Ação
Remover testes de UI/view antigos e preservar testes de dominio.

### Contexto
As telas serao reimplementadas; os testes antigos validavam HTML, templates e rotas que nao representam mais o contrato atual.

### Restrições
- sem migracoes
- nao apagar testes de services/models/forms/commands
- validar suite depois da remocao

### Critérios de aceite
- [x] Testes de tela antigos removidos.
- [x] Testes de dominio preservados.
- [x] `python manage.py test --verbosity 2` passa.
- [x] `python manage.py check` passa.

### Evidências esperadas
- Suite verde.
- Check verde.

### Formato de saída
Resumo dos testes removidos e evidencias.

## Escopo
- Remover arquivos de teste exclusivamente de views/telas.
- Remover classes de view/dashboard em arquivos mistos.

## Fora do escopo
- Reimplementar telas.
- Criar novos testes de UI.
- Alterar views/templates.

## Arquivos impactados
- `system/tests/test_views.py`
- `system/tests/test_plan_views.py`
- `system/tests/test_product_views.py`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_calendar.py`
- `system/tests/test_graduation.py`

## Riscos e edge cases
- Regressao visual nao sera capturada ate os novos testes de tela serem recriados.
- Fluxos HTTP ficam com menos cobertura temporariamente.

## Regras e restrições
- sem migracoes
- validacao obrigatoria
- preservar testes nao relacionados a UI

## Plano
- [x] 1. Capturar falhas atuais da suite.
- [x] 2. Identificar testes acoplados a UI.
- [x] 3. Remover testes de tela.
- [x] 4. Rodar suite completa.
- [x] 5. Rodar check.

## Validação visual
Nao aplicavel; remocao de testes.

## Validação ORM
Nao aplicavel.

## Validação de qualidade
### Sem hardcode
Nao aplicavel.

### Sem estruturas condicionais quebradiças
Nao aplicavel.

### Sem `except: pass`
Nao introduzido.

### Sem mascaramento de erro
Falhas antigas foram removidas por decisao explicita do usuario durante reimplementacao das telas.

### Sem comentários e docstrings desnecessários
Nao introduzido.

## Evidências
- `python manage.py test --verbosity 2`: 157 testes, OK.
- `python manage.py check`: sem issues.

## Implementado
- Removidos arquivos de teste de views/telas.
- Removidas classes de view/dashboard em `test_calendar.py` e `test_graduation.py`.

## Desvios do plano
- Nenhum.

## Pendências
- Recriar testes de tela novos depois da reimplementacao das telas.
