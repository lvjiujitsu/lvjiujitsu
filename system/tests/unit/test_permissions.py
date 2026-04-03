import pytest
from rest_framework.test import APIRequestFactory

from system.api_permissions import HasAnyRolePermission
from system.constants import ROLE_ADMIN_MASTER
from system.models import SystemRole, SystemUser


class DummyPermission(HasAnyRolePermission):
    required_roles = (ROLE_ADMIN_MASTER,)


@pytest.mark.django_db
def test_role_permission_allows_user_with_expected_role():
    user = SystemUser.objects.create_user(
        cpf="11122233344",
        password="StrongPassword123",
        full_name="Admin User",
    )
    role, _ = SystemRole.objects.get_or_create(code=ROLE_ADMIN_MASTER, defaults={"name": "Admin Master"})
    user.assign_role(role)

    request = APIRequestFactory().get("/")
    request.user = user

    assert DummyPermission().has_permission(request, None) is True
