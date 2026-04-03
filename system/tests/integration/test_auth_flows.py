import pytest
from django.urls import reverse

from system.constants import PASSWORD_ACTION_FIRST_ACCESS, PASSWORD_ACTION_RESET
from system.models import AuthenticationEvent, PasswordActionToken, SystemUser


@pytest.mark.django_db
def test_login_with_cpf(client):
    user = SystemUser.objects.create_user(
        cpf="12345678901",
        password="StrongPassword123",
        full_name="Login User",
    )

    response = client.post(
        reverse("system:login"),
        data={"cpf": "123.456.789-01", "password": "StrongPassword123"},
    )

    assert response.status_code == 302
    assert response.url == reverse("system:portal-dashboard")
    assert "_auth_user_id" in client.session
    assert client.session["_auth_user_id"] == str(user.pk)


@pytest.mark.django_db
def test_password_reset_request_creates_single_use_token(client):
    SystemUser.objects.create_user(
        cpf="12345678901",
        password="StrongPassword123",
        full_name="Reset User",
    )

    response = client.post(reverse("system:password-reset"), data={"cpf": "12345678901"})

    assert response.status_code == 302
    token = PasswordActionToken.objects.get(purpose=PASSWORD_ACTION_RESET)
    assert token.is_usable is True


@pytest.mark.django_db
def test_password_action_confirm_consumes_token(client):
    user = SystemUser.objects.create_user(
        cpf="12345678901",
        password=None,
        full_name="First Access User",
    )
    token = PasswordActionToken.issue(user=user, purpose=PASSWORD_ACTION_FIRST_ACCESS)

    response = client.post(
        reverse(
            "system:password-action-confirm",
            kwargs={"purpose": PASSWORD_ACTION_FIRST_ACCESS, "token": token.token},
        ),
        data={"password": "StrongPassword123", "password_confirmation": "StrongPassword123"},
    )

    token.refresh_from_db()
    user.refresh_from_db()

    assert response.status_code == 302
    assert token.used_at is not None
    assert user.must_change_password is False
    assert user.check_password("StrongPassword123")


@pytest.mark.django_db
def test_login_invalid_credentials_returns_error(client):
    SystemUser.objects.create_user(
        cpf="12345678901",
        password="StrongPassword123",
        full_name="Invalid Login User",
    )

    response = client.post(
        reverse("system:login"),
        data={"cpf": "12345678901", "password": "wrong-password"},
    )

    assert response.status_code == 200
    assert "CPF ou senha invalidos." in response.content.decode()


@pytest.mark.django_db
def test_inactive_user_cannot_authenticate(client):
    user = SystemUser.objects.create_user(
        cpf="12345678901",
        password="StrongPassword123",
        full_name="Inactive User",
    )
    user.is_active = False
    user.save(update_fields=["is_active", "updated_at"])

    response = client.post(
        reverse("system:login"),
        data={"cpf": "12345678901", "password": "StrongPassword123"},
    )

    assert response.status_code == 200
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
def test_expired_token_is_rejected(client):
    user = SystemUser.objects.create_user(
        cpf="12345678901",
        password=None,
        full_name="Expired Token User",
    )
    token = PasswordActionToken.issue(user=user, purpose=PASSWORD_ACTION_RESET, ttl_minutes=-1)

    response = client.get(
        reverse(
            "system:password-action-confirm",
            kwargs={"purpose": PASSWORD_ACTION_RESET, "token": token.token},
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_authentication_events_are_recorded(client):
    SystemUser.objects.create_user(
        cpf="12345678901",
        password="StrongPassword123",
        full_name="Audit User",
    )

    client.post(reverse("system:password-reset"), data={"cpf": "12345678901"})
    client.post(
        reverse("system:login"),
        data={"cpf": "12345678901", "password": "StrongPassword123"},
    )
    client.post(reverse("system:logout"))

    event_types = list(AuthenticationEvent.objects.values_list("event_type", flat=True))

    assert AuthenticationEvent.EVENT_PASSWORD_RESET_REQUEST in event_types
    assert AuthenticationEvent.EVENT_LOGIN_SUCCESS in event_types
    assert AuthenticationEvent.EVENT_LOGOUT in event_types


@pytest.mark.django_db
def test_login_rate_limit_blocks_after_repeated_failures(client):
    SystemUser.objects.create_user(
        cpf="12345678901",
        password="StrongPassword123",
        full_name="Rate Limited User",
    )

    for _ in range(5):
        response = client.post(
            reverse("system:login"),
            data={"cpf": "12345678901", "password": "wrong-password"},
        )
        assert response.status_code == 200

    blocked_response = client.post(
        reverse("system:login"),
        data={"cpf": "12345678901", "password": "StrongPassword123"},
    )

    assert blocked_response.status_code == 200
    assert "Muitas tentativas." in blocked_response.content.decode()


@pytest.mark.django_db
def test_login_rate_limit_respects_settings_override(client, settings):
    settings.AUTH_LOGIN_MAX_FAILED_ATTEMPTS = 2
    settings.AUTH_LOGIN_LOCK_MINUTES = 1
    SystemUser.objects.create_user(
        cpf="12345678901",
        password="StrongPassword123",
        full_name="Rate Limited User 2",
    )

    for _ in range(2):
        response = client.post(
            reverse("system:login"),
            data={"cpf": "12345678901", "password": "wrong-password"},
        )
        assert response.status_code == 200

    blocked_response = client.post(
        reverse("system:login"),
        data={"cpf": "12345678901", "password": "StrongPassword123"},
    )

    assert blocked_response.status_code == 200
    assert "Muitas tentativas." in blocked_response.content.decode()
