# AUDIT-2026-06-30 — Achados mestres do repositório LV JIU JITSU

Auditoria isolada executada em 2026-06-30. Fontes: `AGENTS.md`, `CLAUDE.md`, contratos em `docs/`, código em `system/`, inventário de templates, testes locais, comparação Obsidian × `OPERACAO-BANCO-SEEDS.md` e snapshot legado em `Downloads/lvjiujitsu-fef9b13890c09fc822baf1e9063a319dd16e14a3`.

## Comandos executados

| Comando | Resultado |
|---|---|
| `manage.py check` | OK — 0 issues |
| `manage.py test --verbosity 2` | **262 testes, 1 ERROR** — `test_calendar_template_loads_external_script_without_inline_logic` (`UnicodeDecodeError` cp1252 ao ler `templates/calendar/calendar.html`) |

## Contagem por categoria

| Categoria | Qtd | Severidade predominante |
|---|---:|---|
| Templates/rotas ausentes | 50 | Crítica |
| Permissões e papéis acumuláveis | 14 | Alta |
| Home / check-in / presença | 11 | Alta |
| Cadastro de pessoa (interno) | 9 | Alta |
| Seeds e bootstrap | 6 | Média |
| Código morto / legado | 8 | Média |
| UI fundação / shell / modal | 7 | Alta |
| Wizard cadastro público | 6 | Média |
| Testes e qualidade | 5 | Média |
| Documentação / governança | 7 | Baixa |
| Módulos CRUD sem superfície | 6 | Crítica |
| **Total de achados numerados** | **129** | — |

## PRDs novos gerados nesta auditoria

| PRD | Foco |
|---|---|
| PRD-091 | UI de papéis operacionais no formulário de pessoa |
| PRD-092 | Home split Minha área / Gestão |
| PRD-093 | Responsável iniciar treino e matrícula |
| PRD-094 | Check-in aluno com papel duplo e pré-condição do professor |
| PRD-095 | Ordem canônica de seeds Obsidian × docs |
| PRD-096 | Encoding UTF-8 do template de cronograma |
| PRD-097 | Views de calendário órfãs sem rota |
| PRD-098 | Módulo de auditoria operacional |
| PRD-099 | Permissão de edição de pessoa para apoio |
| PRD-100 | Rota Perfis vs papéis operacionais |

PRDs 073–090 já existentes cobrem fundação UI, templates em massa, CRUD MVP, papéis no backend, wizard e governança — esta auditoria **não** as duplica; referencia-as onde aplicável.

---

## Lista completa de achados

Legenda de severidade: **C** crítica · **A** alta · **M** média · **B** baixa.

### A. Templates e rotas (C)

1. **C** — 50 `template_name`/`modal_template_name` referenciados em views sem arquivo em `templates/` (script de inventário 2026-06-30). Evidência: `system/views/*.py`. Telas: turmas, financeiro, graduação, materiais, perfis, hub admin, recuperação de senha, modais de pessoa. Experiência esperada: GET 200; atual: `TemplateDoesNotExist`. → PRD-078, PRD-077.
2. **C** — `templates/lv/base.html`, `modal_base.html`, `modal_done.html` ausentes; `PersonCreateView` referencia `lv/modal_done.html`. Evidência: `person_views.py:92`. → PRD-075.
3. **C** — `people/person_form_modal.html` e `person_detail_modal.html` ausentes; fluxo `?modal=1` quebra. Evidência: `person_views.py:142-219`. → PRD-078.
4. **C** — `admin_modules/admin_hub.html` ausente; rota `/administracao/` não renderiza. Evidência: `admin_views.py:24`, `urls.py:190`.
5. **C** — Módulo turmas: 12 templates ausentes (`classes/*`, `class_categories/*`, `class_schedules/*`). Evidência: `class_views.py`, `category_views.py`.
6. **C** — Módulo financeiro: 5 templates ausentes (`billing/*`). Evidência: `billing_admin_views.py`, `asaas_views.py`.
7. **C** — Módulo graduação: 13 templates ausentes. Evidência: `graduation_views.py`.
8. **C** — Módulo materiais/loja: 9 templates ausentes. Evidência: `product_views.py`.
9. **C** — Perfis (`person_types/*`): 5 templates ausentes; rota `/administracao/perfis/` quebra. Evidência: `person_views.py:283-316`.
10. **C** — Recuperação de senha: 4 templates ausentes apesar de rotas ativas. Evidência: `auth_views.py:732-761`, `UI-SCREEN-CONTRACT.md` §9.1 na numeração da época, hoje §11.1.
11. **A** — `calendar/admin_calendar.html` referenciado por `AdminCalendarView` sem arquivo e sem rota em `urls.py`. Evidência: `calendar_views.py:43-44`. → PRD-097.
12. **A** — Rotas 100% em português (`pessoas/`, `turmas/`, `financeiro/`) divergem de PRD-075 e do padrão de rotas em inglês. Evidência: `system/urls.py`.

### B. Permissões e papéis acumuláveis (A)

13. **A** — Não há UI para atribuir `PersonOperationalRole` no cadastro interno; só seeds e Django Admin. Miguel não pode receber papel via “Perfis”. Evidência: `person_forms.py` sem campo operacional; `PersonTypeForm` só edita `PersonType`. → PRD-091, PRD-100.
14. **A** — Rota “Perfis e acessos” (`/administracao/perfis/`) gerencia `PersonType`, não papéis operacionais acumuláveis. Expectativa do usuário: habilitar aluno+apoio; atual: CRUD de tipo global. → PRD-100.
15. **A** — `PersonUpdateView` exige `AdministrativeRequiredMixin` (`MANAGE_ACADEMY`); `PersonCreateView` aceita `SUPPORT_PEOPLE`. Professor pode criar aluno mas não editar. Evidência: `person_views.py:138 vs 159`. → PRD-099.
16. **A** — `portal_is_instructor` no middleware ainda deriva de `person_type.code == instructor`, não de capacidade `ACCESS_INSTRUCTOR_AREA` ou papel `class-assistant`. Evidência: `middleware.py:60-62`.
17. **A** — Aline na seed é `student` + `class-assistant`, não `administrative-assistant`; capacidades corretas no backend, mas UX de “administrativa que treina” depende de matrícula + split na home. Evidência: `initial_administrative.json:5-34`.
18. **M** — `Person.can_enroll_in_class_group()` permite administrativo com faixa ou matrícula ativa, mas formulário bloqueia turmas para tipos fora de `CLASS_ENROLLMENT_PERSON_TYPE_CODES`. Evidência: `person.py:183-193`, `person_forms.py:460-466`.
19. **M** — `TECHNICAL_ADMIN_PERSON_TYPE_CODES` inclui `student` e `guardian` — sessão técnica simula tipos amplos; pode mascarar bugs de permissão em testes. Evidência: `constants.py:187-192`.
20. **M** — `PortalRoleRequiredMixin.has_allowed_role` ignora `allowed_codes` quando `required_capabilities` está definido; capacidade basta mesmo com tipo incompatível. Evidência: `portal_mixins.py:34-36`.
21. **B** — Papéis operacionais default não incluem `ACCESS_STUDENT_AREA` em `class-assistant`; correto por desenho, mas exige `person_type=student` para área de aluno. Evidência: `constants.py:77-85`.
22. **B** — Não há selector/UI para escopo de turma em `PersonOperationalRole` fora da seed. Evidência: `admin.py:51` inline apenas.
23. **A** — Capacidade `MANAGE_ACADEMY` no tipo `administrative-assistant` ainda concede gestão completa monolítica; papéis granulares existem no modelo mas não substituem o tipo no formulário. → PRD-074 (backend parcial).
24. **M** — Testes de home validam Aline como aluno+apoio, mas não cobrem check-in real nem seed após rebuild completo com turmas do dia. Evidência: `test_home_dashboard.py:53-114`.

### C. Home, check-in e presença (A)

25. **A** — Usuário reporta Aline não consegue marcar presença como aluna: check-in de aluno exige `instructor_present` antes de exibir botão. Evidência: `today_classes_section.html:217-218`. → PRD-094.
26. **A** — `needs_split` na home duplica `id="staff-area-title"` e abre `<section>` de Gestão sem fechar corretamente antes do bloco de acesso rápido. Evidência: `dashboard.html:64-75`. → PRD-092.
27. **A** — Em `needs_split`, bloco “Minha área” usa `personal_today_classes`; Gestão não re-inclui turmas de trabalho do instrutor/apoio de forma consistente quando `staff_work_today_classes` vazio. Evidência: `home_views.py:126-136`.
28. **A** — Pessoa com `MANAGE_ACADEMY` + treino recebe `today_classes` via `get_today_classes_for_administrative`, não via visão aluno, misturando papéis na mesma lista. Evidência: `home_views.py:116-118`.
29. **M** — `show_instructor_area` inclui administrativo (`is_administrative`), expondo toolbar de professor na home mesmo sem papel de aula. Evidência: `home_views.py:79-81`.
30. **M** — Histórico de presença na home usa `get_instructor_checkin_history` para administrativo, não histórico de aluno quando a pessoa também treina. Evidência: `home_views.py:116-121`.
31. **M** — Self-check-in do professor e check-in do aluno compartilham fluxo visual no partial sem distinguir apoio de turma vs titular em mobile. Evidência: `today_classes_section.html`.
32. **B** — KPIs financeiros na home (`Disponível`, `A receber`) aparecem para todo `show_staff_area`; contrato anti-KPI (§15.7) exige PRD nominal — PRD-043/044 podem ter autorizado; registrar decisão.
33. **A** — Calendário único `/cronograma/` existe, mas template com possível byte não-UTF-8 quebra leitura em Windows. → PRD-096.
34. **M** — `static/system/js/home/dashboard.js` não valida resposta de check-in com feedback de erro por campo; erros genéricos. Evidência: `dashboard.js:102+`.
35. **B** — Home não linka para cronograma na topbar; apenas quick links quando staff.

### D. Cadastro interno de pessoa (A)

36. **A** — Cadastro disfuncional: modais e hub inacessíveis (templates ausentes). → PRD-078.
37. **A** — Responsável não pode receber turmas: validação explícita no form. Evidência: `person_forms.py:460-466`. → PRD-093.
38. **A** — Responsável tem `ACCESS_STUDENT_AREA` em `PERSON_TYPE_CAPABILITIES` mas não `CLASS_ENROLLMENT_PERSON_TYPE_CODES`; middleware marca `portal_is_student=True` sem matrícula possível via UI. Evidência: `constants.py:122-125, 183-186`.
39. **M** — `PersonForm` não expõe endereço em `main_field_names` para layout, mas inclui em `Meta.fields`; UX inconsistente entre create/update.
40. **M** — Modal CRUD mixin referencia templates inexistentes; POST modal renderizaria `modal_done` inexistente. Evidência: `person_views.py:86-95`.
41. **M** — Listagem filtra não-gestores para `CLASS_ENROLLMENT_PERSON_TYPE_CODES` apenas; responsáveis cadastrados não aparecem para instrutor. Evidência: `person_views.py:112-115`.
42. **B** — Docstring em `ModalCrudMixin` é órfã de implementação (fundação LV ausente). Evidência: `person_views.py:59`.
43. **M** — Exclusão de pessoa usa página fullscreen `person_confirm_delete.html` em vez de modal/destrutivo inline (desvio do contrato §15.6). → PRD-075.
44. **A** — Sem fluxo para “virar aluno” mantendo outro vínculo: só troca de `person_type` singular. → PRD-091.

### E. Wizard cadastro público (M)

45. **M** — `register.js` usa `innerHTML` extensivamente com dados de API (planos, turmas, materiais). Evidência: `static/system/js/auth/register.js` (30+ ocorrências). → PRD-080.
46. **M** — Rotas mistas PT/EN no wizard (`cadastro/validar-cupom/` vs `register/`). Evidência: `urls.py:147-149`.
47. **M** — `auth_views.py` ~47KB concentra wizard, pagamento e auth — manutenção difícil. → PRD-081.
48. **B** — Template `register.html` duplicado em paths com barra mista no git status (`templates\login\register.html`).
49. **M** — Teste de contrato do wizard passa; teste do calendário falha por encoding — cobertura assimétrica.
50. **B** — `installment_select.html` existe; fluxo de parcelamento Asaas parcialmente isolado do design system home.

### F. Seeds e bootstrap (M)

51. **M** — Ordem Obsidian executa `seed_system_initial_holidays` **antes** de produtos/planos; `OPERACAO-BANCO-SEEDS.md` coloca feriados por último (posição 20). Evidência: `comandos-powershell-lvjiujitsu.md:52-58` vs `OPERACAO-BANCO-SEEDS.md:48-67`. → PRD-095.
52. **M** — Seeds 12–13 (`class_categories_administrative`, `class_catalog_administrative`) legadas/idempotentes ainda listadas nos dois documentos sem aviso de redundância no Obsidian.
53. **M** — Aline depende de turmas/professores de seeds anteriores; ordem incorreta de feriados não quebra, mas documentação divergente gera rebuilds inconsistentes.
54. **B** — `seed_system_people_flow_samples` existe fora da sequência canônica — risco de uso ad hoc.
55. **M** — Miguel seedado como `student` sem matrícula/faixa; não reflete cenário “virar aluno operacional” sem dados de treino.
56. **B** — Comando `create_admin_superuser` no Obsidian após testes; docs oficial colocam antes das seeds — ambos válidos, mas ordem diferente.

### G. Código morto e legado (M)

57. **M** — `AdminCalendarView`, `AdminToggleSessionView`, `AdminSpecialClassCreateView`, `AdminSpecialClassDeleteView` definidas sem entrada em `urls.py`. Evidência: `calendar_views.py:43-219`. → PRD-097.
58. **M** — Aliases `StudentScheduleView`, `InstructorCalendarView` mantidos “por compatibilidade” sem imports externos verificados. Evidência: `calendar_views.py:147-149, 248-249`.
59. **M** — Snapshot legado contém 55 templates que o repo atual apagou; **não reaproveitar** wholesale — reimplementar via PRD-075/077 com tokens atuais.
60. **M** — Legado tinha `templates/admin_modules/base.html`, `templates/base.html` global; atual não tem shell compartilhado.
61. **B** — Legado mantinha dashboards separados `home/admin/`, `home/instructor/`; atual unificou em `home/dashboard.html` (correto por PRD-043), mas contrato UI §9.2 ainda lista pendentes.
62. **M** — `static/documentation/` (se ainda existir) é documentação versionada em static — risco de servir público. → PRD-083.
63. **B** — Views `plan_change_views.py`, `payment_views.py` com templates billing ausentes.
64. **M** — `class_calendar.py` >1300 linhas — selector/service híbrido difícil de testar por papel.

### H. UI fundação e assets (A)

65. **A** — Nenhuma tela autenticada estende shell `lv/base.html`; cada template replica topbar (home, calendar, people). Evidência: inventário `templates/`. → PRD-075.
66. **A** — `static/system/js/lv/crud_modal.js` e `crud_frame.js` ausentes; contrato §15.6 exige. → PRD-075.
67. **M** — `dashboard.css` usado em home **e** cronograma — acoplamento de módulos.
68. **M** — Scripts inline de boot de tema em cada HTML; contrato prefere `theme.js` compartilhado.
69. **B** — Comentários decorativos `<!-- ─── Topbar ───` em templates violam espírito clean-code do projeto.
70. **M** — Cores de faixa hardcoded em `home_views.py` (`_BELT_BODY`) fora de tokens CSS. Evidência: `home_views.py:289-298`. → PRD-084.
71. **B** — Screenshots na raiz do repo (`home_desktop_light.png`, etc.) não versionados em `docs/` — evidência solta.

### I. Testes e qualidade (M)

72. **M** — 1/262 testes com ERROR por `Path.read_text()` sem `encoding='utf-8'` no Windows. Evidência: `test_register_wizard_contract.py:55`. → PRD-096.
73. **M** — `test_admin_hubs_contract` valida `reverse()` mas não renderização — falso negativo para templates ausentes.
74. **B** — Suíte legada parcialmente alinhada por PRD-071; ainda há lacunas de contrato visual.
75. **M** — Não há teste de permissão para check-in de aluno administrativo/acumulado.
76. **B** — `pyflakes` instalado em `.venv` local mas não listado em `requirements-dev.txt` até PRD-082.

### J. Documentação e governança (B)

77. **B** — `UI-SCREEN-CONTRACT.md` §9.2 na numeração da época, hoje §11.2, marcava dashboards separados como pendentes; código usa home unificada — contrato desatualizado.
78. **B** — PRD-065 declara hubs implementados; inventário 2026-06-30 contradiz.
79. **B** — PRD-066/068 declaram fundação modal criada; arquivos ausentes (PRD-076 já registra).
80. **M** — Índice PRD normalizado por PRD-079; auditoria confirma próximo livre = 091.
81. **B** — `docs/prd/PRD-088` marcada superada por PRD-040 mas permanece no índice — OK com nota.
82. **M** — Obsidian e repo divergem na ordem de seeds — fonte operacional duplicada.
83. **B** — `AGENTS.md` autoriza testes locais; README pode estar desalinhado → PRD-082.

### K. Módulos CRUD academia (C)

84. **C** — Auditoria de aula/presença: não existe módulo `/auditoria/` nem modelo de trilha operacional além de check-ins. Expectativa do usuário: CRUD auditoria. → PRD-098.
85. **C** — Estoque/materiais: views completas, zero templates — loja admin e aluno inacessíveis.
86. **C** — Financeiro/repasses: filas e ações POST existem; telas ausentes impedem operação.
87. **C** — Cronograma admin de turmas (horários): CRUD sem UI.
88. **C** — Graduação (faixas, regras, histórico): CRUD sem UI.
89. **A** — Planos: único módulo admin com templates completos (7 arquivos) — referência para PRD-077.
90. **A** — Pessoas: templates base existem (list/form/detail/delete) mas modais e integração CRUD modal faltam.

### L. Padrões a seguir (informativo)

91. **—** — Rotas em inglês e substantivos no plural (`clients/`, `partners/`).
92. **—** — CRUD curto em modal com `?modal=1` + `postMessage`.
93. **—** — Hub/listagem com ações icônicas `.icon-action`.
94. **—** — Um `base.html` de shell autenticado; LV não deve copiar domínio de vistos.

### M. Legado — não reaproveitar (informativo)

95. **—** — Templates antigos sem tokens `lv-*` e sem tema escuro consistente.
96. **—** — Dashboards segregados por pasta (`home/admin/`, `home/instructor/`) como modelo final.
97. **—** — `static/system/js/home/admin-dashboard.js` e CSS `portal/portal.css` do snapshot.
98. **—** — Qualquer regra de negócio de outro domínio.
99. **—** — Restauração em massa de 55 templates sem passar por PRD e validação browser.
100. **—** — Seeds monolíticas `inicial_seed` (já removidas por PRD-087).

### N. Achados adicionais de implementação (M/B)

101. **M** — `PersonTypeUpdateView` permite editar `code` SlugField — risco de quebrar FKs e constantes se alterado em produção.
102. **B** — Docstrings longas em `pre_registration.py`, `registration_checkout.py` — não proibidas, mas acima do padrão mínimo do projeto.
103. **M** — `auth_views.py` docstrings em views de reset/finalize — órfãs de templates ausentes.
104. **B** — `.playwright-mcp/` logs na raiz — artefatos de sessão não ignorados uniformemente.
105. **M** — `calendar_views.py` ~650 linhas com classes admin mortas aumentam superfície de revisão.
106. **B** — Rota `cadastro/validar-cupom/` em português isolada no meio de rotas `register/*`.
107. **M** — `ChromeDevtoolsProbeView` exposta em produção na URLconf — verificar necessidade.
108. **B** — `plan_change_select.html` ausente — troca de plano inacessível pela UI admin.
109. **M** — Dependentes na home: `_build_dependents` não propaga check-in por dependente na área do responsável de forma documentada.
110. **B** — `person_list.html` sem confirmação de paridade PRD-067 (filtros 44px, KPIs removidos) — validação visual pendente.

### O. Problemas explícitos do usuário — validação

111. **A** — **Aline administrativa não marca presença como aluna:** seed é aluna + apoio; bloqueio principal é `instructor_present` e possível confusão de listas admin vs aluno na home. → PRD-094, PRD-092.
112. **A** — **Miguel não vira aluno em perfis:** rota Perfis edita `PersonType`, não matrícula/aluno; sem papel operacional nem turmas na seed. → PRD-091, PRD-100.
113. **A** — **Responsável não pode começar a treinar:** form bloqueia turmas para `guardian`. → PRD-093.
114. **A** — **Cadastro de pessoa disfuncional:** templates modais/hub ausentes + permissão update restritiva. → PRD-078, PRD-099.
115. **A** — **Home administrativo split Minha área/Gestão:** implementação parcial com IDs duplicados e gestão incompleta no split. → PRD-092.
116. **C** — **CRUD academia incompleto:** pessoas parcial, demais módulos sem templates; auditoria inexistente. → PRD-077, PRD-098.

### P. Telas principais — resumo capacidade atual

| Tela | Rota | O usuário deve poder | Implementação atual |
|---|---|---|---|
| Login | `/login/` | Autenticar com tema claro/escuro | **Permite** — template e testes OK |
| Cadastro público | `/register/` | Wizard pagamento→pessoa | **Parcial** — fluxo existe; `innerHTML`; pós-pagamento frágil |
| Home | `/home/` | Painel por papel; split treino/gestão | **Parcial** — unificada; split com bugs; staff OK para admin técnico |
| Pessoas lista | `/pessoas/` | Listar/filtrar/cadastrar | **Parcial** — list/form existem; modal/hub quebram |
| Pessoa detalhe/editar | `/pessoas/<id>/` | Ver/editar com papéis e turmas | **Limitada** — update só admin; sem UI de papéis operacionais |
| Perfis | `/administracao/perfis/` | Configurar papéis acumuláveis | **Não permite** — template ausente; modelo errado (PersonType) |
| Turmas | `/turmas/` | CRUD turmas/categorias/horários | **Não permite** — templates ausentes |
| Cronograma | `/cronograma/` | Ver agenda; check-in/aprovar | **Parcial** — template existe; encoding; papel duplo confuso |
| Financeiro | `/financeiro/` | Pedidos, repasses, filas | **Não permite** — templates ausentes |
| Materiais | `/materiais/` | Estoque catálogo admin | **Não permite** — templates ausentes |
| Loja | `/loja/` | Pedido aluno | **Não permite** — template ausente |
| Graduação | `/graduacao/` | Faixas, regras, histórico | **Não permite** — templates ausentes |
| Planos | `/planos/` | CRUD planos | **Permite** — módulo mais completo |
| Hub admin | `/administracao/` | Atalhos módulos | **Não permite** — template ausente |
| Senha | `/password-reset/` | Recuperar senha | **Não permite** — templates ausentes |
| Auditoria | — | Trilha operacional | **Inexistente** — sem rota/modelo |

---

## Top 10 bloqueadores

1. Cinquenta templates ausentes → maioria das rotas admin retorna 500.
2. Fundação `templates/lv/*` e JS modal inexistente → CRUD modal inviável.
3. Sem UI de `PersonOperationalRole` → papéis acumuláveis só via seed/admin.
4. `PersonUpdateView` restrito a gestão completa → cadastro interno disfuncional para professor.
5. Responsável bloqueado de receber turmas no formulário → não inicia treino.
6. Home split Minha área/Gestão com HTML inválido/IDs duplicados → experiência dual quebrada.
7. Check-in de aluno condicionado a presença do professor → Aline e alunos não check-in antes disso.
8. Rota “Perfis” gerencia `PersonType` → expectativa de habilitar aluno (Miguel) não atendida.
9. Módulo auditoria operacional inexistente → gap de CRUD academia.
10. Divergência ordem seeds Obsidian × docs → rebuilds inconsistentes.

## Status da auditoria

**Concluída com limitações** — sem validação browser nesta fase (somente PRDs). Testes: 261 OK, 1 ERROR. HG/produção não inspecionados.
