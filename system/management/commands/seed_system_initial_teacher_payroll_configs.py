import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from system.constants import PersonTypeCode
from system.models import ClassGroup, Person, TeacherPayrollConfig
from system.services.payroll_rules import (
    PAYROLL_SCOPE_CLASS_GROUP,
    PayrollRuleError,
    encode_payroll_rules,
)
from system.utils import format_cpf_digits


DATA_FILENAME = "seed_system_initial_teacher_payroll_configs.json"


class Command(BaseCommand):
    help = f"Cria configurações iniciais de repasse a partir de static/initial_data/{DATA_FILENAME}."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("seed_system_initial_teacher_payroll_configs"))
        data = self._load_json()

        if not data:
            self.stdout.write(self.style.WARNING(f"Nenhuma configuração encontrada no arquivo {DATA_FILENAME}."))
            return

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for entry in data:
                teacher = self._get_teacher(entry.get("teacher_cpf", ""))
                rules = self._resolve_rules(entry.get("rules", []))

                try:
                    notes = encode_payroll_rules(rules)
                except PayrollRuleError as exc:
                    raise CommandError(f"Regra de repasse inválida para {teacher.full_name}: {exc}") from exc

                config, created = TeacherPayrollConfig.objects.update_or_create(
                    person=teacher,
                    defaults={
                        "monthly_salary": entry.get("monthly_salary", "0.00"),
                        "payment_day": self._normalize_payment_day(entry.get("payment_day", 28)),
                        "is_active": entry.get("is_active", True),
                        "notes": notes,
                    },
                )

                status = "criada" if created else "atualizada"
                self.stdout.write(
                    f"  [{status}] {teacher.full_name} — R$ {config.monthly_salary} — dia {config.payment_day}"
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nConfigurações de repasse: {created_count} criada(s), {updated_count} atualizada(s)."
            )
        )

    def _load_json(self) -> list:
        path = Path(settings.BASE_DIR) / "static" / "initial_data" / DATA_FILENAME
        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")
        with path.open(encoding="utf-8") as f:
            return json.load(f)

    def _get_teacher(self, raw_cpf: str) -> Person:
        cpf = format_cpf_digits(raw_cpf.strip())
        if not cpf:
            raise CommandError("Entrada inválida no JSON: 'teacher_cpf' é obrigatório.")
        try:
            teacher = Person.objects.get(cpf=cpf)
        except Person.DoesNotExist:
            raise CommandError(
                f"Professor com CPF '{cpf}' não encontrado. "
                "Execute 'seed_system_initial_teacher' antes desta seed."
            )
        if not teacher.has_type_code(PersonTypeCode.INSTRUCTOR):
            raise CommandError(
                f"A pessoa com CPF '{cpf}' não possui o tipo Professor. "
                "Execute 'seed_system_initial_teacher' antes desta seed."
            )
        return teacher

    def _resolve_rules(self, rules: list) -> list:
        resolved = []
        for rule in rules:
            payload = dict(rule)
            if payload.get("scope") == PAYROLL_SCOPE_CLASS_GROUP:
                group = self._get_class_group(
                    payload.pop("class_group_category", ""),
                    payload.pop("class_group_teacher_cpf", ""),
                )
                payload["class_group_id"] = group.pk
            resolved.append(payload)
        return resolved

    def _get_class_group(self, category_code: str, raw_teacher_cpf: str) -> ClassGroup:
        category_code = (category_code or "").strip()
        teacher_cpf = format_cpf_digits((raw_teacher_cpf or "").strip())
        if not category_code or not teacher_cpf:
            raise CommandError(
                "Regra com scope='class_group' exige 'class_group_category' "
                "e 'class_group_teacher_cpf'."
            )
        try:
            return ClassGroup.objects.get(
                class_category__code=category_code,
                main_teacher__cpf=teacher_cpf,
            )
        except ClassGroup.DoesNotExist:
            raise CommandError(
                f"Turma não encontrada para categoria '{category_code}' e professor CPF '{teacher_cpf}'. "
                "Execute 'seed_system_initial_class_catalog' antes desta seed."
            )
        except ClassGroup.MultipleObjectsReturned:
            raise CommandError(
                f"Múltiplas turmas encontradas para categoria '{category_code}' e professor CPF '{teacher_cpf}'. "
                f"Revise o arquivo {DATA_FILENAME}."
            )

    def _normalize_payment_day(self, value: int) -> int:
        try:
            day = int(value)
        except (TypeError, ValueError) as exc:
            raise CommandError("O campo 'payment_day' deve ser um número inteiro.") from exc
        return min(max(day, 1), 28)
