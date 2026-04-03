from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from system.models import CashMovement, CashSession, PdvProduct, PdvSale
from system.services.finance import close_cash_session
from system.tests.factories import AdminUserFactory, PdvProductFactory, StudentProfileFactory


@pytest.mark.django_db
def test_admin_can_create_and_toggle_pdv_product(client):
    admin = AdminUserFactory()
    client.force_login(admin)

    create_response = client.post(
        reverse("system:pdv-dashboard"),
        data={
            "action": "product",
            "product-sku": "KIMONO-A1",
            "product-name": "Kimono Oficial A1",
            "product-description": "Produto de recepcao",
            "product-unit_price": "299.00",
            "product-display_order": "1",
            "product-is_active": "on",
        },
    )
    product = PdvProduct.objects.get(sku="KIMONO-A1")

    toggle_response = client.post(reverse("system:pdv-product-toggle", kwargs={"uuid": product.uuid}))
    product.refresh_from_db()

    assert create_response.status_code == 302
    assert toggle_response.status_code == 302
    assert product.is_active is False


@pytest.mark.django_db
def test_admin_can_open_cash_register_and_complete_cash_sale(client):
    admin = AdminUserFactory()
    product = PdvProductFactory(unit_price=Decimal("30.00"))
    client.force_login(admin)

    open_response = client.post(
        reverse("system:pdv-dashboard"),
        data={
            "action": "open_cash",
            "cash_open-opening_balance": "50.00",
            "cash_open-notes": "Abertura do turno da recepcao",
        },
    )
    session = CashSession.objects.get(operator_user=admin)

    sale_response = client.post(
        reverse("system:pdv-dashboard"),
        data={
            "action": "sale",
            "sale-student_query": "",
            "sale-payment_method": PdvSale.PAYMENT_CASH,
            "sale-amount_received": "100.00",
            "sale-notes": "Venda no balcao",
            "sale_items-TOTAL_FORMS": "3",
            "sale_items-INITIAL_FORMS": "0",
            "sale_items-MIN_NUM_FORMS": "0",
            "sale_items-MAX_NUM_FORMS": "1000",
            "sale_items-0-product": str(product.id),
            "sale_items-0-quantity": "2",
            "sale_items-1-product": "",
            "sale_items-1-quantity": "",
            "sale_items-2-product": "",
            "sale_items-2-quantity": "",
        },
    )

    sale = PdvSale.objects.get(cash_session=session)
    session.refresh_from_db()

    assert open_response.status_code == 302
    assert sale_response.status_code == 302
    assert sale.total_amount == Decimal("60.00")
    assert sale.change_amount == Decimal("40.00")
    assert session.expected_cash_total == Decimal("70.00")
    assert session.movements.filter(movement_type=CashMovement.TYPE_OPENING).count() == 1
    assert session.movements.filter(movement_type=CashMovement.TYPE_SALE_IN).count() == 1
    assert session.movements.filter(movement_type=CashMovement.TYPE_CHANGE_OUT).count() == 1


@pytest.mark.django_db
def test_admin_can_complete_non_cash_sale_identifying_student(client):
    admin = AdminUserFactory()
    student = StudentProfileFactory()
    product = PdvProductFactory(unit_price=Decimal("45.00"))
    client.force_login(admin)
    client.post(
        reverse("system:pdv-dashboard"),
        data={
            "action": "open_cash",
            "cash_open-opening_balance": "10.00",
            "cash_open-notes": "",
        },
    )

    response = client.post(
        reverse("system:pdv-dashboard"),
        data={
            "action": "sale",
            "sale-student_query": student.user.cpf,
            "sale-payment_method": PdvSale.PAYMENT_PIX,
            "sale-amount_received": "",
            "sale-notes": "Venda identificada",
            "sale_items-TOTAL_FORMS": "3",
            "sale_items-INITIAL_FORMS": "0",
            "sale_items-MIN_NUM_FORMS": "0",
            "sale_items-MAX_NUM_FORMS": "1000",
            "sale_items-0-product": str(product.id),
            "sale_items-0-quantity": "1",
            "sale_items-1-product": "",
            "sale_items-1-quantity": "",
            "sale_items-2-product": "",
            "sale_items-2-quantity": "",
        },
    )
    sale = PdvSale.objects.get(operator_user=admin, payment_method=PdvSale.PAYMENT_PIX)
    session = CashSession.objects.get(operator_user=admin)

    assert response.status_code == 302
    assert sale.customer_student == student
    assert sale.amount_received == Decimal("45.00")
    assert sale.change_amount == Decimal("0.00")
    assert session.expected_cash_total == Decimal("10.00")


@pytest.mark.django_db
def test_cash_closure_registers_difference_and_prevents_second_close(client):
    admin = AdminUserFactory()
    product = PdvProductFactory(unit_price=Decimal("20.00"))
    client.force_login(admin)
    client.post(
        reverse("system:pdv-dashboard"),
        data={
            "action": "open_cash",
            "cash_open-opening_balance": "50.00",
            "cash_open-notes": "",
        },
    )
    session = CashSession.objects.get(operator_user=admin)
    client.post(
        reverse("system:pdv-dashboard"),
        data={
            "action": "sale",
            "sale-student_query": "",
            "sale-payment_method": PdvSale.PAYMENT_CASH,
            "sale-amount_received": "20.00",
            "sale-notes": "",
            "sale_items-TOTAL_FORMS": "3",
            "sale_items-INITIAL_FORMS": "0",
            "sale_items-MIN_NUM_FORMS": "0",
            "sale_items-MAX_NUM_FORMS": "1000",
            "sale_items-0-product": str(product.id),
            "sale_items-0-quantity": "1",
            "sale_items-1-product": "",
            "sale_items-1-quantity": "",
            "sale_items-2-product": "",
            "sale_items-2-quantity": "",
        },
    )

    close_response = client.post(
        reverse("system:cash-closure", kwargs={"uuid": session.uuid}),
        data={
            "cash_close-counted_cash_total": "65.00",
            "cash_close-notes": "Fechamento com quebra de caixa",
        },
    )
    session.refresh_from_db()

    assert close_response.status_code == 302
    assert session.status == CashSession.STATUS_CLOSED
    assert session.expected_cash_total == Decimal("70.00")
    assert session.counted_cash_total == Decimal("65.00")
    assert session.difference_amount == Decimal("-5.00")
    assert session.requires_manager_review is False

    with pytest.raises(ValidationError):
        close_cash_session(
            cash_session=session,
            closed_by=admin,
            counted_cash_total=Decimal("65.00"),
            notes="Tentativa indevida",
        )


@pytest.mark.django_db
def test_cash_closure_flags_manager_alert_when_difference_exceeds_threshold(client, settings):
    settings.CASH_CLOSURE_ALERT_THRESHOLD = Decimal("10.00")
    admin = AdminUserFactory()
    product = PdvProductFactory(unit_price=Decimal("25.00"))
    client.force_login(admin)
    client.post(
        reverse("system:pdv-dashboard"),
        data={
            "action": "open_cash",
            "cash_open-opening_balance": "50.00",
            "cash_open-notes": "",
        },
    )
    session = CashSession.objects.get(operator_user=admin)
    client.post(
        reverse("system:pdv-dashboard"),
        data={
            "action": "sale",
            "sale-student_query": "",
            "sale-payment_method": PdvSale.PAYMENT_CASH,
            "sale-amount_received": "25.00",
            "sale-notes": "",
            "sale_items-TOTAL_FORMS": "3",
            "sale_items-INITIAL_FORMS": "0",
            "sale_items-MIN_NUM_FORMS": "0",
            "sale_items-MAX_NUM_FORMS": "1000",
            "sale_items-0-product": str(product.id),
            "sale_items-0-quantity": "1",
            "sale_items-1-product": "",
            "sale_items-1-quantity": "",
            "sale_items-2-product": "",
            "sale_items-2-quantity": "",
        },
    )

    response = client.post(
        reverse("system:cash-closure", kwargs={"uuid": session.uuid}),
        data={
            "cash_close-counted_cash_total": "30.00",
            "cash_close-notes": "Quebra relevante",
        },
    )
    session.refresh_from_db()

    assert response.status_code == 302
    assert session.requires_manager_review is True
    assert session.manager_alert_reason == "Quebra de caixa acima do limite gerencial."
