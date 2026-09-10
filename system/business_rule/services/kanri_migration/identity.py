class KanriIdentityMixin:
    def _resolve_student_cpf(self, *, record, student_document_counts, warnings):
        data = record["data"]
        student_document = record["student_document"]
        responsible_document = record["responsible_document"]
        document_type = data.get("tipo_documento", "")
        source_code = record["source_code"]

        uses_responsible_document = self._document_type_indicates_responsible(document_type)
        same_as_responsible = (
            bool(student_document)
            and bool(responsible_document)
            and student_document == responsible_document
            and self._names_are_different(
                data.get("nome", ""),
                record["responsible"].get("nome", ""),
            )
        )
        shared_document = bool(student_document) and student_document_counts[student_document] > 1

        if not student_document:
            warnings.append("CPF substituto usado porque o documento do aluno está ausente ou inválido")
            return self._migration_cpf(source_code)
        if uses_responsible_document:
            warnings.append(
                f"CPF substituto usado porque tipo_documento='{document_type}' indica CPF do responsável"
            )
            return self._migration_cpf(source_code)
        if same_as_responsible:
            warnings.append("CPF substituto usado porque o documento do aluno é igual ao do responsável")
            return self._migration_cpf(source_code)
        if shared_document:
            warnings.append("CPF substituto usado porque o documento aparece em mais de um aluno")
            return self._migration_cpf(source_code)
        return student_document

    def _document_type_indicates_responsible(self, value):
        normalized = self._normalize_text(value)
        responsible_markers = ("pai", "mae", "avo", "vo")
        return any(marker in normalized for marker in responsible_markers)

    def _has_responsible_identity(self, responsible):
        return bool(
            self._clean_text(responsible.get("nome", ""))
            or self._normalize_cpf(responsible.get("n_documento", ""))
        )

    def _names_are_different(self, first, second):
        first_normalized = self._normalize_text(first)
        second_normalized = self._normalize_text(second)
        if not first_normalized or not second_normalized:
            return False
        return first_normalized != second_normalized

    def _is_child_at_date(self, birth_date, reference_date):
        if not birth_date:
            return False
        age = reference_date.year - birth_date.year
        has_had_birthday = (reference_date.month, reference_date.day) >= (
            birth_date.month,
            birth_date.day,
        )
        if not has_had_birthday:
            age -= 1
        return age < 16
