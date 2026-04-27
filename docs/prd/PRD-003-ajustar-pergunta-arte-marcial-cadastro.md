# PRD-003: Ajustar Pergunta de Arte Marcial no Cadastro

## Resumo do que será implementado
Separar no wizard de cadastro a resposta binária da pergunta `Já praticou arte marcial?` da escolha da modalidade praticada, para que a interface exiba `Sim` e `Não` como resposta primária e só peça a modalidade quando a resposta for `Sim`.

## Tipo de demanda
Correção pontual

## Problema atual
O campo atual usa a própria modalidade como resposta da pergunta `Já praticou arte marcial?`. Isso faz a opção vazia aparecer como `Não possui`, mistura duas intenções diferentes no mesmo seletor e gera uma UX incorreta para a pergunta binária.

## Objetivo
Exibir `Sim` e `Não` como resposta da pergunta sobre experiência prévia em arte marcial, mostrar a modalidade apenas quando aplicável e manter a validação atual de faixa/graduação coerente com a modalidade escolhida.

## Context Ledger
### Arquivos lidos integralmente
- `CLAUDE.md`
- `system/forms/registration_forms.py`
- `templates/login/register.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `system/services/registration_validation.py`
- `system/services/registration.py`
- `system/views/auth_views.py`
- `system/models/person.py`
- `system/tests/test_views.py`
- `system/tests/test_forms.py`
- `system/tests/test_models.py`

### Arquivos adjacentes consultados
- `system/urls.py`

### Internet / documentação oficial
- Não aplicável. Correção local em código existente, sem dependência de API externa ou comportamento temporariamente instável.

### MCPs / ferramentas verificadas
- shell / PowerShell — ok — leitura integral dos arquivos do fluxo

### Limitações encontradas
- Nenhuma no diagnóstico inicial.

## Prompt de execução
### Persona
Agente de desenvolvimento especialista em Django monolítico com templates server-rendered, seguindo SDD + TDD.

### Ação
Implementar a separação entre resposta binária (`Sim`/`Não`) e modalidade praticada no prontuário do wizard de cadastro.

### Contexto
O cadastro público em `templates/login/register.html` usa `PortalRegistrationForm`, validação incremental via `RegistrationStepValidationView` e comportamento de UI em `registration-wizard-clean.js`.

### Restrições
- sem hardcode frágil
- sem mascaramento de erro
- sem migrações
- leitura integral obrigatória
- validação obrigatória
- manter persistência existente em `Person.martial_art`

### Critérios de aceite
- [ ] A pergunta `Já praticou arte marcial?` deve expor `Sim` e `Não` no wizard (verificável por: teste de view e validação visual)
- [ ] A modalidade praticada deve aparecer somente quando a resposta for `Sim` (verificável por: validação visual)
- [ ] Se a resposta for `Sim` e a modalidade for `Jiu Jitsu`, a etapa médica deve exigir faixa (verificável por: teste da rota de validação)
- [ ] Se a resposta for `Não`, o backend não deve exigir modalidade, faixa ou graduação e deve limpar esses dados do payload final (verificável por: teste de formulário)

### Evidências esperadas
- testes passando
- console do navegador limpo
- terminal sem stack trace
- `manage.py check` sem erros

### Formato de saída
Código implementado + testes + evidências de validação

## Escopo
- adicionar campo binário de experiência prévia no `PortalRegistrationForm`
- ajustar template do cadastro para refletir pergunta binária + seletor de modalidade condicional
- ajustar JS do wizard para mostrar/esconder modalidade, faixa e graduação corretamente
- ajustar validação incremental e limpeza de dados no backend
- atualizar testes do fluxo

## Fora do escopo
- alteração do CRUD administrativo de pessoa
- mudança de schema
- revisão de textos fora do wizard de cadastro público

## Arquivos impactados
- `docs/prd/PRD-003-ajustar-pergunta-arte-marcial-cadastro.md`
- `system/forms/registration_forms.py`
- `system/services/registration_validation.py`
- `templates/login/register.html`
- `static/system/js/auth/registration-wizard-clean.js`
- `system/tests/test_views.py`
- `system/tests/test_forms.py`

## Riscos e edge cases
- draft salvo com payload antigo do wizard
- dependentes adicionais precisam serializar a nova resposta binária
- a limpeza de campos derivados não pode apagar dados quando a resposta permanecer `Sim`

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
- validar a tela `/register/` com a pergunta exibindo `Sim` e `Não`

### Mobile
- validar o mesmo fluxo em viewport móvel

### Console do navegador
- sem erros JS críticos

### Terminal
- sem stack trace

## Validação ORM
### Banco
- sem alteração de schema

### Shell checks
- não obrigatório se os testes cobrirem a limpeza do payload e a persistência permanecer inalterada

### Integridade do fluxo
- persistir `martial_art` apenas quando houver resposta positiva

## Validação de qualidade
### Sem hardcode
- manter respostas e decisões acopladas ao contrato do form

### Sem estruturas condicionais quebradiças
- usar helpers de limpeza e decisão por prefixo

### Sem `except: pass`
- não introduzir

### Sem mascaramento de erro
- manter mensagens explícitas de validação

### Sem comentários e docstrings desnecessários
- não introduzir

## Evidências
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2` — 189 testes OK
- `.\.venv\Scripts\python.exe manage.py check` — sem erros
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput` — OK
- `.\.venv\Scripts\python.exe manage.py showmigrations` — somente `system.0001_initial`
- Playwright em `http://127.0.0.1:8000/register/` — desktop e mobile com opções `Selecione`, `Sim`, `Não`; modalidade escondida em `Não`; graduação visível para modalidade não-Jiu Jitsu; faixa visível para `Jiu Jitsu`; console sem erros e sem warnings

## Implementado
- Campo binário `*_has_martial_art` no `PortalRegistrationForm`
- Campo de modalidade separado do binário no template do cadastro
- Regras de limpeza/validação no backend para `Sim`/`Não`
- Compatibilidade defensiva com draft legado quando houver modalidade preenchida sem flag binária
- Testes de view e form cobrindo o novo contrato

## Desvios do plano
- Nenhum até o momento

## Pendências
- Nenhuma
