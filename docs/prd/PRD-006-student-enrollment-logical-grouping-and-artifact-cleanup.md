# PRD-006: Corrigir vínculo lógico de aluno com turmas/horários e limpar artefatos de validação
## Resumo
Corrigir o fluxo de cadastro e edição de aluno para trabalhar com turmas lógicas em vez de turmas físicas duplicadas, exibir horários derivados corretamente, eliminar redundâncias frágeis da modelagem de pessoa e automatizar a limpeza dos artefatos temporários gerados durante validações.

## Problema atual
- O aluno recém-cadastrado foi persistido com três matrículas ativas em turmas físicas `Adulto · Jiu Jitsu`, apesar de para o usuário existir apenas uma turma lógica Adulto.
- A tela `Visualizar pessoa` repete `Adulto · Jiu Jitsu` três vezes para esse aluno.
- A tela `Editar pessoa` expõe três checkboxes idênticos `Jiu Jitsu - Adulto`, sem indicar corretamente o vínculo lógico nem os horários derivados.
- O cadastro público usa o mesmo catálogo físico e repete `Adulto / Jiu Jitsu` por professor.
- A modelagem atual mantém `Person.class_category`, `Person.class_group` e `Person.class_schedule` como campos redundantes em paralelo a `ClassEnrollment`, criando divergência fácil de estado.
- O campo `birth_date` não é renderizado preenchido no `PersonForm` de edição mesmo quando existe valor salvo.
- O repositório acumula lixo de validação em `.playwright-mcp`, `test_artifacts` e `test_screenshots`.

## Objetivo
- Fazer o cadastro e a edição de aluno operarem sobre turmas lógicas.
- Exibir horários do aluno como derivação consolidada das matrículas.
- Reduzir a redundância frágil da modelagem de vínculo de pessoa com turma/horário.
- Garantir que a edição reflita corretamente os dados já salvos.
- Criar limpeza explícita dos artefatos temporários de validação ao final do fluxo.

## Contexto consultado
- Context7:
  - `/django/django/4.2.21`: `DateInput` deve receber `format` explícito para renderizar valor inicial compatível com input HTML5 de data.
  - `/django/django/4.2.21`: `MultipleChoiceField` com `CheckboxSelectMultiple` mantém `cleaned_data` como coleção de valores válidos, permitindo resolver a seleção lógica para matrículas físicas no serviço.
- Web:
  - Nenhuma busca adicional foi necessária além da documentação oficial consultada via Context7.

## Dependências adicionadas
- nenhuma

## Escopo / Fora do escopo
### Escopo
- Corrigir leitura/escrita do vínculo de turmas do aluno no CRUD administrativo.
- Corrigir o catálogo do wizard público para turmas lógicas.
- Exibir horários consolidados do aluno na visualização de pessoa.
- Ajustar renderização do campo de data no formulário de pessoa.
- Adicionar limpeza de artefatos temporários no fluxo de limpeza local.
- Revalidar com Playwright, ORM e criação real via interface.

### Fora do escopo
- Reescrever integralmente o domínio acadêmico além do necessário para remover a inconsistência atual.
- Criar agenda individual por aluno fora do vínculo derivado das turmas.

## Arquivos impactados
- `docs/prd/PRD-006-student-enrollment-logical-grouping-and-artifact-cleanup.md`
- `system/forms/person_forms.py`
- `system/forms/registration_forms.py`
- `system/services/class_overview.py`
- `system/services/registration.py`
- `system/selectors/person_selectors.py`
- `system/views/person_views.py`
- `system/views/auth_views.py`
- `templates/people/person_detail.html`
- `clear_migrations.py`
- `.gitignore`
- `system/tests/test_forms.py`
- `system/tests/test_models.py`
- `system/tests/test_views.py`
- `system/tests/test_commands.py`

## Riscos e edge cases
- Alterar o fluxo para vínculo lógico sem quebrar seeds e catálogo existente.
- Remover ou reduzir redundância sem quebrar views que ainda leem campos legados.
- Preservar compatibilidade com pessoas já cadastradas com múltiplas turmas físicas de uma mesma turma lógica.
- Limpeza automática não pode apagar arquivos fora do workspace nem tocar na `.venv`.

## Regras e restrições (SDD, TDD, MTV, Design Patterns aplicáveis)
- SDD guiado por este PRD.
- TDD obrigatório: testes vermelhos antes da correção do vínculo lógico e do cleanup.
- MTV: leitura agregada em services/selectors; view fina.
- Manter validação server-side em forms/services.
- Toda limpeza deve continuar restrita ao workspace local.

## Critérios de aceite (escritos como assertions testáveis)
- [x] Ao editar um aluno vinculado à turma lógica Adulto, a tela não pode exibir três opções idênticas `Jiu Jitsu - Adulto`.
- [x] Ao visualizar um aluno vinculado à turma lógica Adulto, a tela deve exibir a turma uma única vez e os horários consolidados derivados.
- [x] O cadastro público deve oferecer turmas lógicas sem repetição por professor.
- [x] O ORM não pode depender de `Person.class_schedule` para representar os horários do aluno.
- [x] O formulário de edição deve renderizar `birth_date` preenchido quando a pessoa possui data salva.
- [x] Deve ser possível criar um novo aluno básico pela interface e validar visualmente/ORM que os vínculos ficaram coerentes.
- [x] O fluxo de limpeza deve remover `.playwright-mcp`, `test_artifacts` e `test_screenshots` ao final.

## Plano (ordenado por dependência — fundações primeiro)
- [x] 1. Registrar testes vermelhos para duplicidade lógica, horários derivados, data de edição e limpeza de artefatos.
- [x] 2. Reestruturar o catálogo de turmas para expor opções lógicas em pessoas e cadastro público.
- [x] 3. Ajustar persistência/leitura do aluno para usar relação derivada por matrícula, reduzindo dependência de campos redundantes.
- [x] 4. Atualizar views/templates de pessoa para exibir turma lógica única e horários consolidados.
- [x] 5. Corrigir o `DateInput` da edição de pessoa.
- [x] 6. Adicionar limpeza de artefatos temporários em `clear_migrations.py`.
- [x] 7. Validar com ORM, suíte completa, Playwright headless e criação real via interface.

## Comandos de validação
- `.\.venv\Scripts\python.exe manage.py test system.tests.test_forms system.tests.test_models system.tests.test_views system.tests.test_class_portal_views --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py test --verbosity 2`
- `.\.venv\Scripts\python.exe manage.py collectstatic --noinput`
- `.\.venv\Scripts\python.exe manage.py findstatic system/css/portal/portal.css`
- `.\.venv\Scripts\python.exe manage.py showmigrations`
- `.\.venv\Scripts\python.exe manage.py shell -c "<checagens ORM do aluno e das matrículas>"`
- Playwright headless em `/people/<pk>/`, `/people/<pk>/edit/`, `/register/` e no fluxo de criação real
- `.\.venv\Scripts\python.exe clear_migrations.py`

## Implementado (preencher ao final)
- `PersonForm` passou a trabalhar com escolhas lógicas de turma, resolvendo para turmas físicas apenas no `clean/save`.
- `PortalRegistrationForm` passou a aceitar seleção lógica sem invalidar matrículas expandidas.
- O catálogo público de cadastro agora expõe uma opção por turma lógica e não mais uma opção por professor.
- O detalhe de pessoa agora consolida `Turmas liberadas` e `Horários liberados` a partir de `ClassEnrollment`.
- O formulário de edição de pessoa voltou a renderizar `birth_date` corretamente no input de data.
- `clear_migrations.py` passou a incluir `.playwright-mcp` e `test_screenshots`, e `.gitignore` também foi atualizado.
- A suíte recebeu testes red/green para formulário, registro público, detalhe de pessoa e limpeza de artefatos.

### Evidências coletadas
- ORM antes da correção: aluno administrativo reproduzido com `class_group_id=3`, `class_schedule_id=None` e três matrículas físicas ativas (`adult-lauro`, `adult-layon`, `adult-vinicius`) para uma única turma lógica Adulto.
- Playwright antes da correção: `/people/<pk>/edit/` retornava `checkedClasses = ['Jiu Jitsu - Adulto', 'Jiu Jitsu - Adulto', 'Jiu Jitsu - Adulto']` e `birthDate = ''`.
- Playwright antes da correção: `/register/` expunha três cards/opções `Adulto · Jiu Jitsu`, um por professor.
- ORM após a correção: novo aluno `555.444.333-22` salvo com `class_group_code='adult-lauro'`, `class_category_code='adult'`, `class_schedule_id=None` e três matrículas físicas ativas derivadas de uma única escolha lógica.
- Playwright após a correção: `/register/` mostrou quatro opções lógicas (`Adulto`, `Juvenil`, `Kids`, `Feminino`).
- Playwright após a correção: `/people/6/` mostrou uma única chip `Adulto · Jiu Jitsu` e os horários consolidados.
- Playwright após a correção: `/people/6/edit/` retornou `checkedClasses = ['Adulto · Jiu Jitsu']`, `birthDate = '1994-08-12'` e `classOptionCount = 4`.

## Desvios do plano
- O teste de limpeza em Windows foi ajustado para validar os caminhos enviados a `remove_path`, sem depender da criação física da pasta oculta `.playwright-mcp` durante a suíte.
