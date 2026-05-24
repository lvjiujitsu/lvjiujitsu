# PRD-049: Self-Check-in do Professor

## Resumo do que será implementado

Botão "Registrar presença" no dashboard do professor para cada aula/aulão do dia. Ao clicar, registra presença explícita do professor sem necessidade de aprovação. Frequência do professor passa a ser derivada desse registro (não de aprovações de alunos).

## Tipo de demanda

Nova feature com mudança de schema + nova UI + novos endpoints.

## Problema atual

- A frequência do professor não existe como entidade própria no sistema.
- O histórico de frequência do professor (`attendance_history`) mostrava check-ins de alunos — dado incorreto para representar presença do instrutor.
- Não há mecanismo para o professor registrar que ele mesmo ministrou a aula.

## Objetivo

Dar ao professor controle explícito sobre o registro da própria presença, separando conceitualmente "presença do instrutor" de "presença do aluno".

## Context Ledger

### Arquivos lidos integralmente

- `system/models/calendar.py`
- `system/services/class_calendar.py`
- `system/views/calendar_views.py`
- `system/urls.py`
- `templates/home/dashboard.html`
- `system/tests/test_calendar.py`
- `system/views/home_views.py`

### Limitações encontradas

- Schema change obrigatório: `ClassSession.instructor_present`, `ClassSession.instructor_checked_in_at`, `SpecialClass.instructor_present`, `SpecialClass.instructor_checked_in_at`
- Requer ciclo destrutivo executado pelo usuário

## Regra de negócio

- Professor foi presente se ele mesmo clicou "Registrar presença" naquela sessão/aulão
- Registro é idempotente (clicar duas vezes não duplica)
- Registro só pode ser feito no dia da aula (`date == today`)
- Aula cancelada não permite registro
- Somente o professor responsável pela turma pode registrar presença nela

## Escopo

1. `system/models/calendar.py` — 4 novos campos em `ClassSession` e `SpecialClass`
2. `system/services/class_calendar.py` — 3 novas funções + atualização de `get_today_classes_for_instructor` e `get_instructor_checkin_history`
3. `system/views/calendar_views.py` — 2 novas views JSON
4. `system/urls.py` — 2 novas rotas
5. `templates/home/dashboard.html` — botão por aula + update home-config JSON
6. `static/system/js/dashboard.js` — handler JS para self-checkin
7. `system/tests/test_calendar.py` — testes das novas funções e views

## Fora do escopo

- Edição ou desfazimento do registro de presença pelo professor
- Relatório de frequência consolidado
- Integração automática com cálculo de repasse

## Arquivos impactados

| Arquivo | Mudança |
|---|---|
| `system/models/calendar.py` | `instructor_present`, `instructor_checked_in_at` em `ClassSession` e `SpecialClass` |
| `system/services/class_calendar.py` | `register_instructor_self_checkin`, `register_instructor_self_special_checkin`, `get_instructor_attendance_history` + updates |
| `system/views/calendar_views.py` | `InstructorSelfCheckinView`, `InstructorSelfSpecialCheckinView` |
| `system/urls.py` | 2 rotas novas |
| `templates/home/dashboard.html` | botão por item de aula + URLs no config JSON |
| `static/system/js/dashboard.js` | handler self-checkin |
| `system/tests/test_calendar.py` | novos testes |

## Riscos e edge cases

- Sessão não existe quando professor tenta registrar presença → service cria a sessão (`get_or_create`)
- Professor tenta registrar em aula de outra turma → `PermissionError`
- Aulão em data diferente de hoje → `ValueError`

## Hierarquia Visual

- Padrão de leitura: F Pattern
- Botão "Registrar presença": `btn--sm`, borda `--border`, peso 500
- Badge "Presente": `status-pill--success`, verde, peso 600
- Separação clara do botão de aprovação de alunos

## Wireframe

```
[09:00]  Turma Adulto · Adulto          [3 alunos]
         3 confirmados
         [Registrar presença]   ← novo

[09:00]  Turma Adulto · Adulto          [3 alunos]
         3 confirmados
         ✓ Presente às 09:02   ← após registrar
```

## Máquinas de estado

### Botão de presença por aula

- `not_present`: sessão existe ou não, `instructor_present = False` → botão "Registrar presença"
- `present`: `instructor_present = True` → badge "Presente" + horário
- `cancelled`: aula cancelada → nenhum botão (não aplicável)

## Critérios de aceite

- [ ] Botão "Registrar presença" aparece para cada aula não cancelada do dia (verificável: visual)
- [ ] Após clicar, botão some e badge "Presente" aparece com horário (verificável: visual + DOM)
- [ ] Segunda tentativa retorna `created: false` sem erro (verificável: rede)
- [ ] Professor de outra turma recebe 403 (verificável: terminal)
- [ ] Histórico do professor mostra seus próprios dias de presença (verificável: visual)
- [ ] `manage.py test --verbosity 2` passa (verificável: terminal)
- [ ] `manage.py check` passa (verificável: terminal)

## Plano

- [x] 1. Leitura integral
- [ ] 2. Modelos (schema change)
- [ ] 3. Services
- [ ] 4. Views + URLs
- [ ] 5. Template + JS
- [ ] 6. Testes
- [ ] 7. Ciclo destrutivo (usuário)
- [ ] 8. Validação visual

## Implementado

(preencher após implementação)

## Desvios do plano

(preencher se houver)

## Pendências

- Ciclo destrutivo a ser executado pelo usuário após mudanças de schema
