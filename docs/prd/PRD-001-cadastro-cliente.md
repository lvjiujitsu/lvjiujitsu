# PRD-001: Cadastro de cliente com validação de CPF

## Resumo

Implementar o fluxo de cadastro de cliente com validação de CPF, persistência via service e feedback visual ao usuário.

## Tipo de demanda

Nova feature

## Problema atual

O sistema não possui cadastro de clientes. Não há validação de CPF, não há persistência estruturada e não há feedback visual para o usuário.

## Objetivo

Permitir que o usuário cadastre um cliente com nome, e-mail e CPF válido, recebendo feedback de sucesso ou erro. O fluxo deve seguir MVT com services, TDD e validação completa.

---

## Context Ledger

### Arquivos lidos integralmente
- `system/models/__init__.py`
- `system/models/client_models.py`
- `system/forms/__init__.py`
- `system/views/__init__.py`
- `system/urls.py`
- `templates/base.html`
- `settings.py`

### Arquivos adjacentes consultados
- `system/services/__init__.py`
- `system/tests/__init__.py`
- `static/system/css/`
- `static/system/js/`

### Internet / documentação oficial
- Django Forms: docs.djangoproject.com/en/4.1/topics/forms/
- Validação de CPF: algoritmo oficial (mod 11)

### MCPs / ferramentas verificadas
- Playwright — funcional — `python -c "from playwright.sync_api import sync_playwright; print('OK')"`
- Context7 — funcional — consulta Django Forms retornou resultado

### Limitações encontradas
- Nenhuma

---

## Prompt de execução

### Persona
Agente de desenvolvimento especialista em Python + Django 4.1, seguindo SDD + TDD + MVT com services.

### Ação
Implementar o fluxo completo de cadastro de cliente com validação de CPF, incluindo model, form com clean_cpf, service de criação, view fina, template com herança de base.html, CSS namespaced, testes por camada e validação visual.

### Contexto
Este é o primeiro fluxo de cadastro do sistema. O model `Client` ainda não existe. O cadastro será acessível via rota `/clientes/cadastrar/`. O sistema usa app única `system/` com arquitetura MVT + services. Banco local SQLite descartável.

### Restrições
- Sem hardcode de regras de validação — CPF validado por algoritmo
- Sem mascaramento de erro — exceção explícita em caso de falha
- Sem migrações — model será criado mas migration não será gerada
- Leitura integral obrigatória dos arquivos do fluxo
- Validação visual obrigatória via Playwright
- Sem comentários ou docstrings desnecessários
- Código limpo, funções pequenas, guard clauses

### Critérios de aceite
- [ ] Ao submeter CPF válido com nome e e-mail, o cliente é criado e mensagem de sucesso exibida (verificável por: teste + shell check + visual)
- [ ] Ao submeter CPF inválido, formulário retorna erro específico no campo CPF (verificável por: teste + visual)
- [ ] Ao submeter CPF duplicado, formulário retorna erro de unicidade (verificável por: teste + visual)
- [ ] Ao submeter formulário vazio, erros de campo obrigatório exibidos (verificável por: teste + visual)
- [ ] Rota `/clientes/cadastrar/` responde 200 com GET e processa POST (verificável por: teste)
- [ ] Template herda `base.html` e usa `{% csrf_token %}` (verificável por: inspeção)
- [ ] CSS em `static/system/css/client_form.css` — sem inline (verificável por: inspeção)
- [ ] Console do navegador sem erros JS (verificável por: Playwright)
- [ ] Terminal sem stack traces (verificável por: inspeção)

### Evidências esperadas
- `manage.py test --verbosity 2` → 0 falhas, 0 erros
- `manage.py check` → sem erros
- `manage.py collectstatic --noinput` → sem erros
- Shell check: `Client.objects.filter(cpf='12345678909').exists()` → True
- Screenshot Playwright da tela de cadastro
- Console do navegador limpo

### Formato de saída
Código implementado + testes por camada + evidências de validação + limpeza final

---

## Escopo

- Model `Client` (name, email, cpf)
- Form `ClientForm` com `clean_cpf()`
- Service `create_client()`
- View `client_create_view`
- URL `/clientes/cadastrar/`
- Template `clients/client_form.html`
- CSS `static/system/css/client_form.css`
- Testes: test_models, test_forms, test_services, test_views

## Fora do escopo

- Listagem de clientes
- Edição de clientes
- Exclusão de clientes
- Autenticação
- Permissões

## Arquivos impactados

| Ação | Arquivo |
|---|---|
| Criar | `system/models/client_models.py` |
| Criar | `system/forms/client_forms.py` |
| Criar | `system/services/client_service.py` |
| Criar | `system/views/client_views.py` |
| Editar | `system/urls.py` |
| Criar | `templates/clients/client_form.html` |
| Criar | `static/system/css/client_form.css` |
| Criar | `system/tests/test_models.py` |
| Criar | `system/tests/test_forms.py` |
| Criar | `system/tests/test_services.py` |
| Criar | `system/tests/test_views.py` |

## Riscos e edge cases

- CPF com formatação (pontos e traço) vs. só números → aceitar ambos, normalizar para só números
- CPF com todos os dígitos iguais (111.111.111-11) → rejeitar
- E-mail duplicado → permitir (mesmo e-mail pode ter CPFs diferentes)
- Encoding pt-BR em mensagens de erro → garantir UTF-8

---

## Regras e restrições

- SDD: este PRD é a spec — código derivado dele
- TDD: escrever testes que falham (Red) → implementar (Green) → refatorar (Refactor)
- MVT: lógica de negócio em service, view fina, form valida entrada
- Sem hardcode — validação de CPF por algoritmo
- Sem mascaramento de erro — exceção explícita
- Sem migrações — política do projeto
- Leitura integral obrigatória
- Validação visual obrigatória

## Plano

- [ ] 1. Contexto e leitura integral dos arquivos existentes
- [ ] 2. Model `Client` com fields e constraints
- [ ] 3. Testes do model (Red)
- [ ] 4. Form `ClientForm` com `clean_cpf()`
- [ ] 5. Testes do form (Red)
- [ ] 6. Service `create_client()` com `@transaction.atomic`
- [ ] 7. Testes do service (Red)
- [ ] 8. Implementação mínima para testes passarem (Green)
- [ ] 9. View `client_create_view` + URL
- [ ] 10. Testes da view (Red → Green)
- [ ] 11. Template com herança + CSS namespaced
- [ ] 12. Refatoração (Refactor)
- [ ] 13. Validação completa (testes + check + collectstatic + visual + ORM)
- [ ] 14. Limpeza final
- [ ] 15. Atualização documental

---

## Validação visual

### Desktop
- [ ] Formulário renderiza corretamente
- [ ] Labels em pt-BR
- [ ] Mensagens de erro nos campos
- [ ] Mensagem de sucesso após cadastro

### Mobile
- [ ] Layout responsivo funcional

### Console do navegador
- [ ] Sem erros JS
- [ ] Sem 404 de estáticos

### Terminal
- [ ] Sem stack traces
- [ ] Sem warnings críticos

## Validação ORM

### Banco
- [ ] `Client.objects.count()` retorna quantidade esperada após cadastro

### Shell checks
- [ ] `Client.objects.filter(cpf='12345678909').exists()` → True
- [ ] `Client.objects.filter(cpf='00000000000').exists()` → False

### Integridade do fluxo
- [ ] Cadastro cria exatamente 1 registro
- [ ] CPF armazenado sem formatação (só números)

## Validação de qualidade

### Sem hardcode
- [ ] CPF validado por algoritmo, não por lista

### Sem estruturas condicionais quebradiças
- [ ] Guard clauses usadas em vez de cascatas

### Sem `except: pass`
- [ ] Exceções específicas com mensagens claras

### Sem mascaramento de erro
- [ ] Erros de validação propagados para o usuário

### Sem comentários e docstrings desnecessários
- [ ] Código auto-explicativo

---

## Evidências
> (preencher ao final com resultados reais)

## Implementado
> (preencher ao final)

## Desvios do plano
> (preencher ao final)

## Pendências
> (preencher ao final)
