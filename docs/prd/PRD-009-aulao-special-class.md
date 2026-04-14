# PRD-009: Aulão (aula especial avulsa)

## Resumo
Permitir que um administrador crie rapidamente um "aulão" — uma aula especial avulsa
que **não** pertence ao cronograma semanal regular (ClassSchedule), podendo acontecer
em qualquer data (inclusive feriados), autorizando todos os alunos da academia a treinar
naquele dia/horário. Alunos visualizam e fazem check-in próprio; apenas alunos com
check-in ficam autorizados a participar.

## Problema atual
O cronograma atual (`ClassSchedule` semanal + `ClassSession` por dia) cancela aulas
automaticamente em feriados (`Holiday`) e só permite check-in via horários regulares.
Não existe forma de o administrador autorizar uma aula avulsa em qualquer data, aberta
a todos os alunos — inclusive sobre um feriado.

## Objetivo
- Adicionar o conceito de **Aulão** (aula especial pontual) independente do cronograma semanal.
- Admin cria/remove aulões diretamente no calendário com um botão rápido.
- Aulão aparece no calendário (admin e aluno), no "Aulas de hoje" do aluno e permite check-in.
- Aulão é liberado mesmo em feriados e mesmo para alunos sem enrollment regular na turma.
- Autorização para treinar naquele aulão é dada pela existência do check-in.

## Contexto consultado (Context7 + Web)
- Django 4.1 ModelForm, UniqueConstraint, `transaction.atomic`.
- Padrões existentes do projeto em `class_calendar.py` (`toggle_session_cancel`, `perform_checkin`).

## Dependências adicionadas
Nenhuma nova dependência externa.

## Escopo
- Novo model `SpecialClass` (data, horário, duração, professor, título, observação).
- Novo model `SpecialClassCheckin` (constraint único por pessoa/aulão).
- Serviços: `create_special_class`, `delete_special_class`,
  `perform_special_class_checkin`, extensão de `get_calendar_month_data` e
  `get_today_classes_for_person`.
- Form `SpecialClassForm`.
- Views admin (criar/deletar) e aluno (check-in).
- Templates: botão "Novo aulão" no admin calendar com modal, pill especial,
  check-in no student_schedule, exibição no student dashboard.
- Testes por camada (models, services, views).

## Fora do escopo
- Edição de aulão existente (apenas criação/remoção).
- Limite de capacidade/waitlist para aulões.
- Cancelamento parcial de aulão (basta deletar).
- Notificação por e-mail/push aos alunos.

## Arquivos impactados
- `system/models/calendar.py` — novos models.
- `system/models/__init__.py` — export.
- `system/services/class_calendar.py` — serviços + integração.
- `system/forms/class_forms.py` — `SpecialClassForm`.
- `system/views/calendar_views.py` — novas views.
- `system/views/__init__.py` — export.
- `system/urls.py` — rotas.
- `templates/calendar/admin_calendar.html` — botão + modal.
- `templates/calendar/student_schedule.html` — pill especial + check-in.
- `templates/home/student/dashboard.html` — inclusão no "Aulas do dia".
- `static/css/base.css` — estilos de pill especial e modal.
- `system/tests/test_calendar.py` — novos testes.
- `system/migrations/0002_special_class.py` — migração.

## Riscos e edge cases
- Feriados: aulão ignora feriado (intencional).
- Aluno sem enrollment: autorizado via check-in.
- Duplo check-in: bloqueado por unique constraint.
- Aulão cancelado após check-ins: delete em cascata dos check-ins.
- Conflito visual com ClassSession regular no mesmo horário: exibidos lado a lado
  sem colisão, aulão marcado visualmente.

## Regras e restrições
- SDD: PRD escrito antes da implementação.
- TDD: testes primeiro por camada.
- MTV: form valida, service executa lógica, view só orquestra.
- `@transaction.atomic` em escritas múltiplas.
- CSRF habilitado nos endpoints JSON.
- Sem CSS/JS inline de nova lógica além do padrão já adotado em admin_calendar.

## Critérios de aceite
1. Admin consegue criar um aulão em qualquer data (inclusive feriado) pelo calendário.
2. Aulão aparece no calendário do admin com pill diferenciada (classe CSS
   `calendar-class-pill--special`).
3. Aulão aparece no calendário do aluno e no "Aulas de hoje" do dashboard aluno.
4. Aluno consegue fazer check-in no aulão; segundo check-in é idempotente.
5. Aulão ignora feriado (não é auto-cancelado).
6. Admin consegue remover um aulão a partir do calendário; check-ins são removidos.
7. Endpoint de criação retorna 400 para dados inválidos, 403 para não-admin.
8. Testes por camada passando: models, services, views.

## Plano
1. Modelagem (`SpecialClass`, `SpecialClassCheckin`) + export.
2. Migração `0002`.
3. Serviços + integração em `get_calendar_month_data` / `get_today_classes_for_person`.
4. Form `SpecialClassForm`.
5. Views (`AdminSpecialClassCreateView`, `AdminSpecialClassDeleteView`,
   `StudentSpecialClassCheckinView`).
6. URLs.
7. Templates e CSS.
8. Testes.
9. `makemigrations`, `migrate`, `test`, `collectstatic`.

## Comandos de validação
```powershell
.\.venv\Scripts\python.exe manage.py makemigrations
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py test system.tests.test_calendar
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

## Implementado
- Models `SpecialClass` e `SpecialClassCheckin` (migração `0002`).
- Serviços `create_special_class`, `delete_special_class`, `perform_special_class_checkin`.
- `get_calendar_month_data` e `get_today_classes_for_person` passam a incluir aulões.
- Form `SpecialClassForm`.
- Views `AdminSpecialClassCreateView`, `AdminSpecialClassDeleteView`, `StudentSpecialClassCheckinView`.
- URLs `admin-special-class-create`, `admin-special-class-delete`, `student-special-checkin`.
- Admin calendar: botão "Novo aulão" + modal, pill diferenciada, remoção via painel de detalhe.
- Student schedule e dashboard "Aulas do dia": pill/card especial + botão de check-in.
- CSS de pill especial e modal em `portal.css`.
- 14 novos testes (models/services/views). Suite completa: 135 testes, 0 falhas.
- `makemigrations`, `migrate`, `test`, `collectstatic` OK.

## Desvios do plano
(a preencher se houver)
