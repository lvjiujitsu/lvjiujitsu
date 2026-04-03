import factory

from system.constants import ROLE_ADMIN_MASTER
from system.models import SystemRole, SystemUser, SystemUserRole


class SystemRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SystemRole

    code = factory.Sequence(lambda index: f"ROLE_{index}")
    name = factory.Sequence(lambda index: f"Role {index}")


class SystemUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SystemUser

    cpf = factory.Sequence(lambda index: f"{index:011d}")
    full_name = factory.Sequence(lambda index: f"User {index}")
    email = factory.Sequence(lambda index: f"user{index}@example.com")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        raw_password = kwargs.pop("password", "StrongPassword123")
        user = model_class.objects.create_user(password=raw_password, **kwargs)
        user.must_change_password = False
        user.save(update_fields=["must_change_password", "updated_at"])
        return user


class AdminUserFactory(SystemUserFactory):
    class Meta:
        model = SystemUser
        skip_postgeneration_save = True

    @factory.post_generation
    def admin_role(self, create, extracted, **kwargs):
        if not create:
            return
        role, _ = SystemRole.objects.get_or_create(code=ROLE_ADMIN_MASTER, defaults={"name": "Admin Master"})
        SystemUserRole.objects.get_or_create(user=self, role=role)
