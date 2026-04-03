import pytest
from django.urls import reverse

from system.constants import ROLE_PROFESSOR
from system.models import ClassDiscipline, ClassGroup, ClassSession, InstructorProfile, SystemRole
from system.tests.factories.auth_factories import AdminUserFactory, SystemUserFactory
from system.tests.factories.class_factories import ClassGroupFactory, InstructorProfileFactory


@pytest.mark.django_db
def test_admin_can_create_instructor_profile(client):
    admin = AdminUserFactory()
    belt = InstructorProfileFactory().belt_rank
    client.force_login(admin)

    response = client.post(
        reverse("system:instructor-list"),
        data={
            "instructor-full_name": "Professor Novo",
            "instructor-cpf": "33344455566",
            "instructor-email": "professor@teste.com",
            "instructor-belt_rank": belt.id,
            "instructor-bio": "Professor de fundamentos.",
            "instructor-specialties": "Fundamentos",
            "instructor-is_active": "on",
        },
    )

    assert response.status_code == 302
    assert InstructorProfile.objects.filter(user__cpf="33344455566").exists() is True


@pytest.mark.django_db
def test_professor_cannot_access_admin_instructor_screen(client):
    professor = SystemUserFactory(password="StrongPassword123")
    role, _ = SystemRole.objects.get_or_create(code=ROLE_PROFESSOR, defaults={"name": "Professor"})
    professor.assign_role(role)
    client.force_login(professor)

    response = client.get(reverse("system:instructor-list"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_create_modality_and_class_group(client):
    admin = AdminUserFactory()
    instructor = InstructorProfileFactory()
    belt = instructor.belt_rank
    client.force_login(admin)

    modality_response = client.post(
        reverse("system:discipline-list"),
        data={
            "discipline-name": "Jiu-Jitsu Kids",
            "discipline-slug": "jiu-jitsu-kids",
            "discipline-description": "Turma infantil",
            "discipline-is_active": "on",
        },
    )
    modality = ClassDiscipline.objects.get(slug="jiu-jitsu-kids")
    class_group_response = client.post(
        reverse("system:class-group-list"),
        data={
            "class_group-name": "Kids Noite",
            "class_group-modality": modality.id,
            "class_group-instructor": instructor.id,
            "class_group-reference_belt": belt.id,
            "class_group-weekday": 1,
            "class_group-start_time": "19:00",
            "class_group-end_time": "20:00",
            "class_group-capacity": 18,
            "class_group-reservation_required": "on",
            "class_group-minimum_age": 8,
            "class_group-is_active": "on",
        },
    )

    assert modality_response.status_code == 302
    assert class_group_response.status_code == 302
    assert ClassGroup.objects.filter(name="Kids Noite").exists() is True


@pytest.mark.django_db
def test_admin_can_open_and_close_class_session(client):
    admin = AdminUserFactory()
    class_group = ClassGroupFactory()
    client.force_login(admin)
    create_response = client.post(
        reverse("system:session-list"),
        data={
            "session-class_group": class_group.id,
            "session-starts_at": "2026-04-02 19:00:00",
            "session-ends_at": "2026-04-02 20:00:00",
            "session-status": ClassSession.STATUS_SCHEDULED,
        },
    )
    session = ClassSession.objects.get(class_group=class_group)
    open_response = client.post(reverse("system:session-open", kwargs={"uuid": session.uuid}))
    close_response = client.post(reverse("system:session-close", kwargs={"uuid": session.uuid}))
    session.refresh_from_db()

    assert create_response.status_code == 302
    assert open_response.status_code == 302
    assert close_response.status_code == 302
    assert session.status == ClassSession.STATUS_CLOSED
