import os

from django.core.management.base import BaseCommand

from system.constants import ROLE_ADMIN_MASTER
from system.models import SystemRole, SystemUser


class Command(BaseCommand):
    help = "Cria ou atualiza um superusuario administrativo padrao de forma nao interativa."

    def handle(self, *args, **options):
        cpf = os.getenv("DJANGO_ADMIN_CPF", "12345678909")
        full_name = os.getenv("DJANGO_ADMIN_FULL_NAME", "Administrador LV JIU JITSU")
        email = os.getenv("DJANGO_ADMIN_EMAIL", "admin@lvjiujitsu.local")
        password = os.getenv("DJANGO_ADMIN_PASSWORD", "admin123")
        if SystemUser.objects.exclude(cpf=cpf).filter(email=email).exists():
            email = ""

        user = SystemUser.objects.filter(cpf=cpf).first()
        created = user is None
        if created:
            user = SystemUser.objects.create_superuser(
                cpf=cpf,
                password=password,
                full_name=full_name,
                email=email,
            )
        else:
            user.full_name = full_name
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.must_change_password = False
            user.set_password(password)
            user.save()

        admin_role, _ = SystemRole.objects.get_or_create(
            code=ROLE_ADMIN_MASTER,
            defaults={"name": "Admin Master"},
        )
        user.assign_role(admin_role)

        if created:
            self.stdout.write(self.style.SUCCESS("Superusuario administrativo criado com sucesso."))
            return
        self.stdout.write(self.style.SUCCESS("Superusuario administrativo atualizado com sucesso."))
