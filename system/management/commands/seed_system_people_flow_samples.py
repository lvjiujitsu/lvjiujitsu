from datetime import date, time
import warnings

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.constants import PersonTypeCode
from system.models import (
    BiologicalSex,
    ClassCategory,
    ClassEnrollment,
    ClassGroup,
    ClassSchedule,
    IbjjfAgeCategory,
    JiuJitsuBelt,
    MartialArt,
    Person,
    PersonRelationship,
    PersonRelationshipKind,
    PersonType,
    PortalAccount,
    TrainingStyle,
    WeekdayCode,
)
from system.models.category import CategoryAudience


PEOPLE_FLOW_SAMPLE_PASSWORD = "lv-pessoas-2026"


class Command(BaseCommand):
    help = (
        "DEPRECATED: cria amostras locais de Pessoas fora do bootstrap canônico. "
        "Prefira seed_system_initial_test_* documentado em obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md."
    )

    def handle(self, *args, **options):
        warnings.warn(
            "seed_system_people_flow_samples está obsoleto e fora do bootstrap canônico. "
            "Use seed_system_initial_test_students/guardians/teachers/administrative.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.stdout.write(
            self.style.WARNING(
                "AVISO: comando obsoleto — prefira os seeds canônicos "
                "seed_system_initial_test_* (ver obsidian/projetos/lvjiujitsu/operacao-banco-seeds-lvjiujitsu.md)."
            )
        )
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_people_flow_samples"))

        with transaction.atomic():
            person_types = self._get_person_types()
            category = self._upsert_category()
            self._upsert_ibjjf_category()

            administrative = self._upsert_person(
                cpf="900.000.000-00",
                full_name="Administrativo Validação LV",
                person_type=person_types[PersonTypeCode.ADMINISTRATIVE_ASSISTANT],
                birth_date=date(1990, 1, 12),
                biological_sex=BiologicalSex.FEMALE,
                jiu_jitsu_belt="",
                jiu_jitsu_stripes=None,
            )
            self._upsert_access_account(administrative)

            teacher = self._upsert_person(
                cpf="900.000.000-01",
                full_name="Professor Validação LV",
                person_type=person_types[PersonTypeCode.INSTRUCTOR],
                birth_date=date(1986, 5, 14),
                biological_sex=BiologicalSex.MALE,
                jiu_jitsu_belt=JiuJitsuBelt.BLACK,
                jiu_jitsu_stripes=1,
            )
            class_group = self._upsert_class_group(category, teacher)
            self._upsert_schedule(class_group)

            student = self._upsert_person(
                cpf="900.000.000-02",
                full_name="Aluno Branca Quatro Graus",
                person_type=person_types[PersonTypeCode.STUDENT],
                birth_date=date(1998, 8, 20),
                biological_sex=BiologicalSex.MALE,
                jiu_jitsu_belt=JiuJitsuBelt.WHITE,
                jiu_jitsu_stripes=4,
            )
            guardian = self._upsert_person(
                cpf="900.000.000-03",
                full_name="Responsável Validação LV",
                person_type=person_types[PersonTypeCode.GUARDIAN],
                birth_date=date(1982, 3, 9),
                biological_sex=BiologicalSex.FEMALE,
                jiu_jitsu_belt="",
                jiu_jitsu_stripes=None,
            )
            dependent = self._upsert_person(
                cpf="900.000.000-04",
                full_name="Dependente Azul Validação",
                person_type=person_types[PersonTypeCode.DEPENDENT],
                birth_date=date(2003, 11, 2),
                biological_sex=BiologicalSex.FEMALE,
                jiu_jitsu_belt=JiuJitsuBelt.BLUE,
                jiu_jitsu_stripes=1,
            )

            self._upsert_enrollment(student, class_group)
            self._upsert_enrollment(dependent, class_group)
            PersonRelationship.objects.get_or_create(
                source_person=guardian,
                target_person=dependent,
                relationship_kind=PersonRelationshipKind.RESPONSIBLE_FOR,
                defaults={"kinship_type": "parent"},
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Amostras de Pessoas criadas/atualizadas: administrativo, professor, aluno, responsável e dependente."
            )
        )

    def _get_person_types(self):
        codes = (
            PersonTypeCode.ADMINISTRATIVE_ASSISTANT,
            PersonTypeCode.STUDENT,
            PersonTypeCode.GUARDIAN,
            PersonTypeCode.DEPENDENT,
            PersonTypeCode.INSTRUCTOR,
        )
        person_types = {
            person_type.code: person_type
            for person_type in PersonType.objects.filter(code__in=codes)
        }
        missing = [code for code in codes if code not in person_types]
        if missing:
            raise CommandError(
                "Tipos de pessoa ausentes. Execute seed_system_initial_person_type antes: "
                + ", ".join(missing)
            )
        return person_types

    def _upsert_category(self):
        category, _ = ClassCategory.objects.update_or_create(
            code="adult-validation",
            defaults={
                "display_name": "Adulto Validação",
                "audience": CategoryAudience.ADULT,
                "description": "Categoria local minima para validar Pessoas.",
                "display_order": 10,
                "is_active": True,
            },
        )
        return category

    def _upsert_ibjjf_category(self):
        IbjjfAgeCategory.objects.update_or_create(
            code="adult-validation",
            defaults={
                "display_name": "Adulto Validação",
                "audience": CategoryAudience.ADULT,
                "minimum_age": 18,
                "maximum_age": None,
                "display_order": 10,
                "is_active": True,
            },
        )

    def _upsert_person(
        self,
        *,
        cpf,
        full_name,
        person_type,
        birth_date,
        biological_sex,
        jiu_jitsu_belt,
        jiu_jitsu_stripes,
    ):
        person, _ = Person.objects.update_or_create(
            cpf=cpf,
            defaults={
                "full_name": full_name,
                "email": "",
                "phone": "",
                "birth_date": birth_date,
                "biological_sex": biological_sex,
                "person_type": person_type,
                "martial_art": MartialArt.JIU_JITSU if jiu_jitsu_belt else "",
                "martial_art_graduation": "",
                "jiu_jitsu_belt": jiu_jitsu_belt,
                "jiu_jitsu_stripes": jiu_jitsu_stripes,
                "is_active": True,
            },
        )
        return person

    def _upsert_access_account(self, person):
        account, _ = PortalAccount.objects.get_or_create(person=person)
        account.set_password(PEOPLE_FLOW_SAMPLE_PASSWORD)
        account.is_active = True
        account.failed_login_attempts = 0
        account.save(
            update_fields=(
                "password_hash",
                "password_updated_at",
                "is_active",
                "failed_login_attempts",
                "updated_at",
            )
        )
        return account

    def _upsert_class_group(self, category, teacher):
        class_group, _ = ClassGroup.objects.get_or_create(
            class_category=category,
            display_name="Noite Validação",
            defaults={
                "main_teacher": teacher,
                "description": "Turma local minima para validar Pessoas.",
                "default_capacity": 24,
                "is_active": True,
            },
        )
        changed_fields = []
        if class_group.main_teacher_id != teacher.pk:
            class_group.main_teacher = teacher
            changed_fields.append("main_teacher")
        if not class_group.is_active:
            class_group.is_active = True
            changed_fields.append("is_active")
        if changed_fields:
            class_group.save(update_fields=[*changed_fields, "updated_at"])
        return class_group

    def _upsert_schedule(self, class_group):
        ClassSchedule.objects.update_or_create(
            class_group=class_group,
            weekday=WeekdayCode.MONDAY,
            training_style=TrainingStyle.GI,
            start_time=time(19, 0),
            defaults={
                "duration_minutes": 60,
                "display_order": 10,
                "is_active": True,
            },
        )

    def _upsert_enrollment(self, person, class_group):
        ClassEnrollment.objects.update_or_create(
            class_group=class_group,
            person=person,
            defaults={
                "status": "active",
                "notes": "Amostra local para validacao visual.",
            },
        )
        Person.objects.filter(pk=person.pk).update(
            class_category=class_group.class_category,
            class_group=class_group,
            class_schedule=None,
        )
