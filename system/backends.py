from django.contrib.auth.backends import BaseBackend

from system.models import SystemUser
from system.services.auth.cpf import normalize_cpf


class CpfAuthBackend(BaseBackend):
    def authenticate(self, request, cpf=None, password=None, **kwargs):
        normalized_cpf = normalize_cpf(cpf or kwargs.get("username"))
        if not normalized_cpf or not password:
            return None
        try:
            user = SystemUser.objects.get(cpf=normalized_cpf)
        except SystemUser.DoesNotExist:
            return None
        if not user.is_active or not user.check_password(password):
            return None
        return user

    def get_user(self, user_id):
        try:
            return SystemUser.objects.get(pk=user_id)
        except SystemUser.DoesNotExist:
            return None
