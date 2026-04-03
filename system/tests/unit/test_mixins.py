import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory
from django.views import View

from system.constants import ROLE_ADMIN_MASTER
from system.mixins import OwnerScopeMixin, RoleRequiredMixin
from system.models import PasswordActionToken, SystemRole, SystemUser


class DummyRoleView(RoleRequiredMixin, View):
    required_roles = (ROLE_ADMIN_MASTER,)

    def get(self, request, *args, **kwargs):
        return HttpResponse("ok")


@pytest.mark.django_db
def test_role_required_mixin_blocks_user_without_role():
    request = RequestFactory().get("/")
    user = SystemUser.objects.create_user(
        cpf="55544433322",
        password="StrongPassword123",
        full_name="No Role User",
    )
    request.user = user
    with pytest.raises(PermissionDenied):
        DummyRoleView.as_view()(request)


@pytest.mark.django_db
def test_owner_scope_mixin_filters_queryset_for_regular_user():
    user = SystemUser.objects.create_user(
        cpf="11111111111",
        password="StrongPassword123",
        full_name="Scoped User",
    )
    other_user = SystemUser.objects.create_user(
        cpf="22222222222",
        password="StrongPassword123",
        full_name="Other User",
    )
    own_token = PasswordActionToken.issue(user=user, purpose="password_reset")
    PasswordActionToken.issue(user=other_user, purpose="password_reset")

    mixin = OwnerScopeMixin()
    mixin.request = type("Request", (), {"user": user})()

    scoped_queryset = mixin.scope_queryset(PasswordActionToken.objects.all())

    assert list(scoped_queryset) == [own_token]
