import pytest

from system.models import SystemRole


@pytest.mark.django_db
def test_base_model_fields_are_populated():
    instance = SystemRole.objects.create(code="BASE_TEST_ROLE", name="Base Test Role")

    assert instance.pk is not None
    assert instance.uuid is not None
    assert instance.created_at is not None
    assert instance.updated_at is not None
