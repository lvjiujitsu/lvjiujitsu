from django.core.exceptions import ValidationError
from system.business_rule.models import (
    ClassCatalogRequest,
    ClassCatalogRequestStatus,
    ClassCatalogRequestType,
    ClassInstructorAssignment,
    ClassSchedule,
)


def validate_scoped_class_group(person, class_group):
    if class_group is None:
        raise ValidationError("Selecione a turma existente.")
    if class_group.main_teacher_id == person.pk:
        return
    if ClassInstructorAssignment.objects.filter(class_group=class_group, person=person).exists():
        return
    raise ValidationError("Professor pode solicitar horário apenas para turma em que atua.")


def validate_schedule_payload(weekday, training_style, start_time, duration_minutes):
    if not weekday:
        raise ValidationError("Informe o dia da semana.")
    if not training_style:
        raise ValidationError("Informe o estilo de treino.")
    if start_time is None:
        raise ValidationError("Informe o horário de início.")
    if not duration_minutes or int(duration_minutes) <= 0:
        raise ValidationError("Informe uma duração válida.")


def validate_schedule_slot_available(
    *,
    class_group,
    weekday,
    training_style,
    start_time,
    exclude_request_id=None,
):
    if ClassSchedule.objects.filter(
        class_group=class_group,
        weekday=weekday,
        training_style=training_style,
        start_time=start_time,
    ).exists():
        raise ValidationError("Já existe horário igual para esta turma.")
    pending_queryset = ClassCatalogRequest.objects.filter(
        status=ClassCatalogRequestStatus.PENDING,
        target_class_group=class_group,
        weekday=weekday,
        training_style=training_style,
        start_time=start_time,
    )
    if exclude_request_id is not None:
        pending_queryset = pending_queryset.exclude(pk=exclude_request_id)
    if pending_queryset.exists():
        raise ValidationError("Já existe solicitação pendente para este horário.")


def has_pending_new_teacher_request(cpf):
    return ClassCatalogRequest.objects.filter(
        request_type__in=(
            ClassCatalogRequestType.NEW_TEACHER_WITH_SCHEDULE,
            ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS,
        ),
        status=ClassCatalogRequestStatus.PENDING,
        cpf=cpf,
    ).exists()


def has_pending_join_request(cpf, class_group_id):
    return ClassCatalogRequest.objects.filter(
        request_type=ClassCatalogRequestType.TEACHER_JOIN_EXISTING_CLASS,
        status=ClassCatalogRequestStatus.PENDING,
        cpf=cpf,
        target_class_group_id=class_group_id,
    ).exists()


def require_pending(catalog_request):
    if catalog_request.status != ClassCatalogRequestStatus.PENDING:
        raise ValidationError("A solicitação já foi decidida.")
