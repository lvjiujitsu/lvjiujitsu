from django.urls import reverse


import pytest


@pytest.mark.django_db
def test_home_page_loads(client):
    response = client.get(reverse("system:home"))

    assert response.status_code == 200
    assert "LV JIU JITSU" in response.content.decode()
