# PRD-010: Módulo de controle de graduação (faixas, graus, regras e panorama)

## Resumo do que será implementado
Criar módulo dinâmico de controle de graduação para aluno de Jiu Jitsu, sem hardcode da tabela de faixas. Cobre:
1. CRUD de faixas (`BeltRank`) e seus graus (parametrizados na faixa).
2. CRUD de regras de graduação (`GraduationRule`) por faixa/grau, com tempo mínimo e frequência mínima.
3. Histórico de graduações (`Graduation`) por pessoa.
4. Cálculo de progresso baseado em check-ins aprovados (já existentes via PRD-009) e em tempo decorrido.
5. Panorama com lista de quem está próximo de graduar e o que falta (em meses e em aulas) por aluno.
6. Seeds com a tabela IBJJF padrão (adulto + infantil), totalmente editáveis.

## Tipo de demanda
Nova feature com mudança de schema (novos modelos, sem alterar `Person`).

## Problema atual
- `Person.jiu_jitsu_belt` e `Person.jiu_jitsu_stripes` são campos free-text/choice estáticos. Não há histórico, regra, nem cálculo automático.
- Não existe ferramenta para o admin/professor avaliar quem está próximo de graduar.
- Mudanças nas regras IBJJF exigiriam alteração de código.

## Objetivo
- Faixas, graus por faixa e regras de graduação editáveis pelo admin (zero hardcode em código).
- Progresso de graduação calculado a partir do histórico de graduações + check-ins aprovados.
- Panorama com ordenação por proximidade da promoção (% completo da regra atual).

## Context Ledger
### Arquivos lidos integralmente
- `AGENTS.md`, `CLAUDE.md`
- `system/models/person.py` (campos `jiu_jitsu_belt`, `jiu_jitsu_stripes`)
- `system/models/category.py` (`CategoryAudience`, `IbjjfAgeCategory`)
- `system/models/calendar.py` (incluindo nova `CheckinStatus.APPROVED`)
- `system/models/__init__.py`
- `system/services/seeding.py`
- `system/services/class_calendar.py`
- `system/views/__init__.py`, `system/urls.py`
- `templates/base.html` (drawer/menu)

### Internet / documentação oficial
- Não acessível no ambiente; o seed default é parametrizado mas o admin pode editar livremente caso a IBJJF altere uma regra.

### MCPs / ferramentas verificadas
- `read`, `glob`, `grep` — ok
- `bash` para `manage.py check` — ok
- ciclo destrutivo — autorizado pelo usuário

### Limitações encontradas
- Sem acesso direto aos PDFs anexados; seeds usam tabela IBJJF pública conhecida.

## Prompt de execução
### Persona
Agente Django seguindo SDD + TDD + MVT com camada de serviços e selectors.

### Ação
Implementar módulo de graduação dinâmico (modelos + services + selectors + views CRUD + panorama + seeds).

### Contexto
O sistema já tem `Person`, `IbjjfAgeCategory`, `ClassCheckin` (com status approved). Falta a regra de graduação e o histórico.

### Restrições
- sem hardcode de faixas/regras no código
- sem mascaramento de erro
- ciclo destrutivo já autorizado (PRD-009)
- leitura integral obrigatória
- validação obrigatória

### Critérios de aceite
- [ ] Modelo `BeltRank` com `code`, `display_name`, `audience`, `display_order`, `color_hex`, `max_grades`, `next_rank` (FK self), `min_age`, `max_age`, `is_active`.
- [ ] Modelo `GraduationRule` com `belt_rank`, `from_grade`, `to_grade` (None = próxima faixa), `min_months_in_current_grade`, `min_classes_required`, `min_classes_window_months`, `notes`, `is_active`.
- [ ] Modelo `Graduation` com `person`, `belt_rank`, `grade_number`, `awarded_at`, `awarded_by`, `notes`.
- [ ] Service `count_approved_classes_in_window(person, start, end)` baseado em `ClassCheckin`/`SpecialClassCheckin` com `status=approved`.
- [ ] Service `get_current_graduation(person)` que retorna a última `Graduation` ou um `Graduation` virtual a partir de `Person.jiu_jitsu_belt`/`stripes` (compat).
- [ ] Service `compute_graduation_progress(person, reference_date)` que retorna struct com: `current_belt_rank`, `current_grade_number`, `applicable_rule`, `months_in_current_grade`, `required_months`, `months_remaining`, `approved_classes_in_window`, `required_classes`, `missing_classes`, `is_eligible`, `progress_pct`.
- [ ] Service `register_graduation(person, belt_rank, grade_number, awarded_by, notes)` cria registro e força transação.
- [ ] Selector `get_graduation_overview(reference_date)` lista todos `Person` ativos do tipo aluno/dependente com progresso, ordenado por `progress_pct` descendente.
- [ ] CRUD admin de `BeltRank` (list/detail/create/update/delete).
- [ ] CRUD admin de `GraduationRule` (list/detail/create/update/delete).
- [ ] CRUD admin de `Graduation` (list/create/delete).
- [ ] View `GraduationOverviewView` com tabela do panorama.
- [ ] Comando `seed_belts` que carrega faixas IBJJF default + regras.
- [ ] `inicial_seed` invoca `seed_belts`.
- [ ] Admin Django registra os 3 modelos.
- [ ] Drawer admin tem entrada "Graduação" e "Faixas" e "Regras de graduação".
- [ ] Testes em `system/tests/test_graduation.py` cobrem models, services, selectors, views.
- [ ] `manage.py test` passa; `manage.py check` 0 issues.

### Evidências esperadas
- testes passando, ciclo destrutivo executado, validação visual da página de panorama.

### Formato de saída
Código + testes + seeds + evidências.

## Escopo
- `system/models/graduation.py` (novo)
- `system/models/__init__.py`
- `system/services/graduation.py` (novo)
- `system/selectors/graduation.py` (novo)
- `system/forms/graduation_forms.py` (novo)
- `system/views/graduation_views.py` (novo)
- `system/views/__init__.py`
- `system/urls.py`
- `system/services/seeding.py` (`seed_belts`)
- `system/management/commands/seed_belts.py` (novo)
- `system/management/commands/inicial_seed.py` (chamar seed_belts)
- `system/admin.py`
- `templates/graduation/*.html` (novos)
- `templates/base.html` (drawer com novas entradas)
- `static/system/css/portal/portal.css` (estilos do panorama)
- `system/tests/test_graduation.py` (novo)

## Fora do escopo
- Notificação automática para quem atingiu eligibilidade.
- Promoção em massa.
- Importação de histórico de graduações de fontes externas.
- Edição direta da faixa atual em `Person`; passa pelo registro `Graduation`.

## Riscos e edge cases
- Pessoa sem nenhuma `Graduation` nem `jiu_jitsu_belt`: progresso retorna `None`/sem regra aplicável.
- Faixa sem `next_rank`: regras `to_grade=None` ficam inválidas; service retorna `applicable_rule=None`.
- Regra com `min_classes_window_months=0`: ignora janela e considera todos os check-ins desde a última graduação.
- Aluno sem check-ins aprovados: missing_classes = required_classes; progress derivado do tempo apenas.
- Idade não atinge `min_age` da próxima faixa: progresso considera regra mas marca `is_eligible=False`.

## Regras e restrições
SDD, TDD, sem hardcode, ciclo destrutivo autorizado.

## Plano
- [ ] 1. Criar PRD
- [ ] 2. Modelos
- [ ] 3. Services
- [ ] 4. Selectors
- [ ] 5. Forms
- [ ] 6. Views/URLs CRUD + overview
- [ ] 7. Templates
- [ ] 8. Seeds + comando + inicial_seed
- [ ] 9. Admin Django
- [ ] 10. Drawer/menu
- [ ] 11. Tests
- [ ] 12. `manage.py check` (0 issues)
- [ ] 13. Ciclo destrutivo (junto com PRD-009)
- [ ] 14. `manage.py test`
- [ ] 15. Validação visual do panorama
- [ ] 16. Limpeza final

## Validação visual
- Página de panorama exibe alunos com progresso, badges, tempo restante.
- CRUD de faixas/regras navega normalmente.

## Validação ORM
- Após ciclo destrutivo, schema regenerado.
- `Graduation.objects.create(...)` ↔ `get_current_graduation(person)` retorna o registro.
- `compute_graduation_progress` reflete check-ins aprovados.

## Validação de qualidade
Sem hardcode, exceções explícitas, comentários só onde necessário.

## Evidências
(preencher após execução)

## Implementado
(preencher ao final)

## Desvios do plano
(preencher ao final)

## Pendências
(preencher ao final)
