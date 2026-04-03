import pytest
from django.core.exceptions import ValidationError

from system.constants import ROLE_PROFESSOR, ROLE_RESPONSAVEL_FINANCEIRO
from system.models import SystemRole, SystemUser


@pytest.mark.django_db
def test_user_manager_normalizes_cpf_on_create():
    user = SystemUser.objects.create_user(
        cpf="123.456.789-01",
        password="StrongPassword123",
        full_name="Test User",
    )

    assert user.cpf == "12345678901"


@pytest.mark.django_db
def test_duplicate_cpf_is_blocked():
    SystemUser.objects.create_user(
        cpf="12345678901",
        password="StrongPassword123",
        full_name="User One",
    )

    with pytest.raises(ValidationError):
        SystemUser.objects.create_user(
            cpf="12345678901",
            password="StrongPassword123",
            full_name="User Two",
        )


@pytest.mark.django_db
def test_user_supports_multiple_roles():
    user = SystemUser.objects.create_user(
        cpf="98765432100",
        password="StrongPassword123",
        full_name="Multi Role",
    )
    professor, _ = SystemRole.objects.get_or_create(code=ROLE_PROFESSOR, defaults={"name": "Professor"})
    financeiro, _ = SystemRole.objects.get_or_create(
        code=ROLE_RESPONSAVEL_FINANCEIRO,
        defaults={"name": "Financeiro"},
    )

    user.assign_role(professor)
    user.assign_role(financeiro)

    assert user.has_role(ROLE_PROFESSOR)
    assert user.has_any_role(ROLE_PROFESSOR, ROLE_RESPONSAVEL_FINANCEIRO)
