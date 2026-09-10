from datetime import date
from django.core.management.base import CommandError
from system.business_rule.constants import PersonTypeCode
from system.business_rule.models import MartialArt, Person
from system.business_rule.services.kanri_migration.constants import (
    MIGRATION_CPF_PREFIX,
    PERSON_BELT_BY_RANK_CODE,
)


class KanriPeopleMixin:
    def _sync_record(
        self,
        *,
        record,
        person_types,
        student_document_counts,
        belt_ranks,
        stats,
    ):
        data = record["data"]
        warnings = []
        full_name = self._clean_text(data.get("nome", ""))
        if not full_name:
            raise CommandError(f"Nome ausente em {record['file_name']}.")

        responsible = record["responsible"]
        responsible_person = self._sync_responsible(
            responsible=responsible,
            person_types=person_types,
            stats=stats,
        )

        student_cpf = self._resolve_student_cpf(
            record=record,
            student_document_counts=student_document_counts,
            warnings=warnings,
        )
        if student_cpf.startswith(MIGRATION_CPF_PREFIX):
            stats["migration_cpfs"] += 1
        person_type = (
            person_types[PersonTypeCode.DEPENDENT]
            if responsible_person is not None and responsible_person.cpf != student_cpf
            else person_types[PersonTypeCode.STUDENT]
        )

        student_defaults, address_warnings = self._build_student_defaults(
            data=data,
            full_name=full_name,
            person_type=person_type,
        )
        warnings.extend(address_warnings)
        student, student_created = self._upsert_person(
            cpf=student_cpf,
            defaults=student_defaults,
        )
        self._count_person(stats, student_created)

        relationship_action = ""
        if responsible_person is not None and responsible_person.pk != student.pk:
            relationship, relationship_created = self._sync_relationship(
                guardian=responsible_person,
                dependent=student,
                responsible=responsible,
            )
            if relationship_created:
                stats["relationships_created"] += 1
                relationship_action = ", vínculo criado"
            else:
                stats["relationships_updated"] += 1
                relationship_action = ", vínculo atualizado"
        elif self._has_responsible_identity(responsible):
            warnings.append("responsável não vinculado porque usa a mesma pessoa do aluno")

        graduation_count = self._sync_graduations(
            person=student,
            data=data,
            belt_ranks=belt_ranks,
        )
        stats["graduations_created"] += graduation_count

        financial_count = self._list_count(data.get("financeiro"))
        attendance_count = self._list_count(data.get("historico"))
        stats["financial_skipped"] += financial_count
        stats["attendance_skipped"] += attendance_count

        action = "criado" if student_created else "atualizado"
        grad_label = f", {graduation_count} graduação(ões)" if graduation_count else ""
        financial_label = (
            f", financeiro não importado: {financial_count}"
            if financial_count
            else ""
        )
        attendance_label = (
            f", histórico de aulas não importado: {attendance_count}"
            if attendance_count
            else ""
        )
        self.stdout.write(
            f"  [{action}] {student.full_name} "
            f"(CPF {student.cpf}, tipo={student.person_type.code})"
            f"{relationship_action}{grad_label}{financial_label}{attendance_label}"
        )
        for warning in warnings:
            self.stdout.write(self.style.WARNING(f"    aviso: {record['file_name']}: {warning}"))

    def _sync_responsible(self, *, responsible, person_types, stats):
        responsible_name = self._clean_text(responsible.get("nome", ""))
        responsible_document = self._normalize_cpf(responsible.get("n_documento", ""))
        if not responsible_name and not responsible_document:
            return None
        if not responsible_name or not responsible_document:
            self.stdout.write(
                self.style.WARNING(
                    "    aviso: responsável ignorado por falta de nome ou CPF válido"
                )
            )
            return None

        defaults = {
            "full_name": responsible_name,
            "email": self._clean_text(responsible.get("email", "")),
            "phone": self._clean_text(responsible.get("telefone", "")),
            "person_type": person_types[PersonTypeCode.GUARDIAN],
            "is_active": True,
        }
        person, created = self._upsert_person(cpf=responsible_document, defaults=defaults)
        self._count_person(stats, created)
        return person

    def _build_student_defaults(self, *, data, full_name, person_type):
        birth_date = self._parse_iso_date(data.get("nascimento"))
        evolution_events = self._parse_evolution_events(data, birth_date)
        current_evolution = evolution_events[-1] if evolution_events else None
        start_event = self._get_start_event(evolution_events)
        address_defaults, address_warnings = self._build_address_defaults(data.get("endereco"))

        defaults = {
            "full_name": full_name,
            "email": self._clean_text(data.get("email", "")),
            "phone": self._clean_text(data.get("telefone", "")),
            "birth_date": birth_date,
            "biological_sex": self._map_biological_sex(data.get("sexo", "")),
            "martial_art": MartialArt.JIU_JITSU,
            "person_type": person_type,
            "is_active": True,
            "martial_art_started_at": start_event["date"] if start_event else None,
            "martial_art_last_graduation_at": (
                current_evolution["date"] if current_evolution else None
            ),
            "martial_art_graduation": current_evolution["label"] if current_evolution else "",
            "jiu_jitsu_belt": (
                PERSON_BELT_BY_RANK_CODE.get(current_evolution["belt_code"], "")
                if current_evolution
                else ""
            ),
            "jiu_jitsu_stripes": current_evolution["grade"] if current_evolution else None,
        }
        defaults.update(address_defaults)
        return defaults, address_warnings

    def _build_address_defaults(self, address):
        if not isinstance(address, dict):
            address = {}

        warnings = []
        field_map = {
            "postal_code": "cep",
            "address": "logradouro",
            "address_number": "numero",
            "address_complement": "complemento",
            "address_neighborhood": "bairro",
            "city": "cidade",
        }
        defaults = {}
        for model_field, source_field in field_map.items():
            value, removed_placeholder = self._clean_address_value(address.get(source_field, ""))
            defaults[model_field] = value
            if removed_placeholder:
                warnings.append(f"placeholder de endereço removido em {source_field}")
        return defaults, warnings

    def _upsert_person(self, *, cpf, defaults):
        person, created = Person.objects.get_or_create(cpf=cpf, defaults=defaults)
        if not created:
            for field, value in defaults.items():
                setattr(person, field, value)
            person.save()
        return person, created

    def _count_person(self, stats, created):
        if created:
            stats["persons_created"] += 1
        else:
            stats["persons_updated"] += 1
