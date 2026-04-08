# PRD-002: Redesenho relacional de turmas, horários e professores
## Resumo
Corrigir a modelagem percebida e a experiência de cadastro/exibição das turmas para que categoria, turma, professores e horários sejam apresentados como vínculos claros, sem ambiguidade visual ou operacional.

## Problema atual
- A tela pública de informações mostra turmas com nome genérico e pouca relação explícita entre categoria, professores e horários.
- O CRUD administrativo separa demais o cadastro de turma e o cadastro de horário, o que favorece turmas ativas sem contexto completo.
- A lista de turmas e a lista de horários não deixam evidente a equipe docente e os vínculos cruzados.
- O sistema valida compatibilidade etária/sexo no cadastro de alunos, mas não comunica bem invalidez estrutural do catálogo operacional.

## Objetivo
- Tornar o cadastro de turma autoexplicativo, com horários vinculados no mesmo fluxo.
- Impedir que uma turma ativa fique estruturalmente incompleta.
- Exibir relações corretas entre categoria, turma, horários e professores nas telas pública e administrativas.
- Melhorar a leitura estética das telas sem perder os vínculos já existentes no domínio.

## Contexto consultado
- Context7: indisponível no ambiente atual (`unknown MCP server 'context7'`).
- Web:
  - Django docs, formsets/model form functions: https://docs.djangoproject.com/en/4.1/ref/forms/formsets/
  - Django docs, model/form validation flow: https://docs.djangoproject.com/en/4.1/ref/models/instances/
  - Django docs, related objects/reference de relacionamentos: https://docs.djangoproject.com/en/4.1/ref/models/relations/

## Dependências adicionadas
- nenhuma

## Escopo / Fora do escopo
### Escopo
- Reorganizar o CRUD de turma para incluir horários vinculados no mesmo fluxo de edição.
- Criar validações estruturais para turma ativa e horários vinculados.
- Reorganizar a tela pública de informações com leitura relacional por categoria, turma, professor e horário.
- Melhorar as listas administrativas de turmas, horários e professores com vínculos visíveis.

### Fora do escopo
- Alterar a regra de elegibilidade etária/sexo já existente para matrícula de aluno.
- Criar novo app ou refatorar o domínio para uma arquitetura diferente da atual.
- Introduzir calendário avançado, disponibilidade docente ou conflito de agenda automatizado.

## Arquivos impactados
- `docs/prd/PRD-002-class-information-relational-redesign.md`
- `templates/base.html`
- `templates/login/info.html`
- `templates/classes/class_group_form.html`
- `templates/classes/class_group_list.html`
- `templates/class_schedules/class_schedule_form.html`
- `templates/class_schedules/class_schedule_list.html`
- `templates/people/person_list.html`
- `static/system/css/portal/portal.css`
- `static/system/css/portal/class-catalog.css`
- `static/system/js/shared/public-info.js`
- `system/forms/__init__.py`
- `system/forms/class_forms.py`
- `system/views/class_views.py`
- `system/views/auth_views.py`
- `system/views/person_views.py`
- `system/services/class_catalog.py`
- `system/services/class_management.py`
- `system/tests/test_class_catalog.py`
- `system/tests/test_class_portal_views.py`
- `system/tests/test_forms.py`

## Riscos e edge cases
- Turma existente sem professor principal ou sem horários pode falhar ao ser reeditada como ativa.
- Inline formset de horários precisa tratar exclusão, duplicidade e mensagens de erro sem perder dados digitados.
- A mesma pessoa pode ser professor e aluno; a UI precisa separar “turmas ministradas” de “turmas liberadas”.
- A tela pública precisa continuar funcionando quando não houver catálogo ativo.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- SDD: implementação guiada por este PRD.
- TDD: começar por testes de formulário, serviço e view cobrindo falhas estruturais.
- MTV: regra de gravação concentrada em service object; views apenas orquestram form + formset.
- Design Patterns:
  - `ModelForm` + inline formset para vínculo de horários na própria turma.
  - service object com `@transaction.atomic` para persistir turma, equipe auxiliar e horários.
  - consultas com `select_related`/`prefetch_related` para evitar N+1 nas telas relacionais.

## Critérios de aceite (escritos como assertions testáveis)
- [ ] Ao cadastrar uma turma ativa sem professor principal, o sistema deve bloquear o envio com erro explícito no formulário.
- [ ] Ao cadastrar uma turma ativa sem nenhum horário ativo vinculado, o sistema deve bloquear o envio com erro explícito por etapa.
- [ ] Ao salvar uma turma com horários válidos, o sistema deve persistir turma, auxiliares e horários no mesmo fluxo.
- [ ] Ao abrir a lista de turmas, o usuário deve ver categoria, equipe docente e horários vinculados na mesma superfície.
- [ ] Ao abrir a lista de horários, o usuário deve ver a turma, a categoria e os professores vinculados ao horário.
- [ ] Ao abrir a lista de pessoas para um professor, o usuário deve ver as turmas/horários em que ele atua sem confundir com matrícula como aluno.
- [ ] Ao abrir a página pública de informações, o visitante deve conseguir navegar por categoria, professor e horário preservando os vínculos corretos.
- [ ] `manage.py test` deve permanecer verde após a refatoração.
- [ ] `manage.py collectstatic --noinput` deve concluir sem erro.

## Plano (ordenado por dependência — fundações primeiro)
- [x] 1. Criar testes Red para validação estrutural de turma ativa e persistência relacional.
- [x] 2. Implementar formset de horários vinculado ao `ClassGroupForm`.
- [x] 3. Implementar service object transacional para salvar turma, auxiliares e horários.
- [x] 4. Adaptar views de turma para operar com form + formset.
- [x] 5. Reestruturar consultas de catálogo para exibição relacional.
- [x] 6. Reescrever templates/listagens com leitura clara de categoria, turma, professor e horário.
- [x] 7. Adicionar CSS/JS namespaced para a nova UI.
- [x] 8. Validar testes, collectstatic e checks do catálogo.

## Comandos de validação
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_forms system.tests.test_class_catalog system.tests.test_class_portal_views system.tests.test_views --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
- `.\.venv\Scripts\python.exe manage.py findstatic system/css/portal/class-catalog.css`
- `.\.venv\Scripts\python.exe manage.py showmigrations`

## Implementado (preencher ao final)
- `ClassGroupForm` passou a exigir professor principal quando a turma está ativa.
- O cadastro de turma agora salva horários vinculados no mesmo fluxo por inline formset.
- Turma ativa sem horário ativo vinculado passou a ser bloqueada com erro explícito.
- A persistência de turma, equipe auxiliar e horários foi centralizada em service transacional.
- A leitura pública foi reorganizada em seções por categoria, professor e horário.
- As listas administrativas de turmas, horários e pessoas passaram a exibir vínculos relacionais.
- `base.html` recebeu blocos `extra_css` e `extra_js` para telas namespaced.
- Novo CSS `static/system/css/portal/class-catalog.css` e novo JS `static/system/js/shared/public-info.js`.
- Evidências de validação:
  - `manage.py test --verbosity 2` com 42 testes verdes.
  - `manage.py collectstatic --noinput` sem erro.
  - `manage.py findstatic system/css/portal/class-catalog.css` resolvido corretamente.
  - Playwright validou `http://127.0.0.1:8010/info/` e `http://127.0.0.1:8010/class-groups/create/` sem erro de console.

## Desvios do plano
- Context7 permaneceu indisponível no ambiente; a consulta externa foi feita apenas em documentação oficial do Django.
- A validação visual com Playwright exigiu execução fora do sandbox por restrição de subprocesso no Windows.
