from system.constants import ROLE_PROFESSOR
from system.models import InstructorProfile
from system.services.students.registry import create_or_update_identity, ensure_role


def create_or_update_instructor_profile(*, cpf, full_name, email="", belt_rank=None, bio="", specialties="", is_active=True):
    user, _ = create_or_update_identity(
        cpf=cpf,
        full_name=full_name,
        email=email,
    )
    ensure_role(user, ROLE_PROFESSOR)
    profile, _ = InstructorProfile.objects.get_or_create(user=user)
    profile.belt_rank = belt_rank
    profile.bio = bio
    profile.specialties = specialties
    profile.is_active = is_active
    profile.full_clean()
    profile.save()
    return profile
