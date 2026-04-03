from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from system.services.finance import close_cash_session, create_pdv_sale, open_cash_session
from system.tests.factories import CashSessionFactory, PdvProductFactory, SystemUserFactory


@pytest.mark.django_db
def test_operator_cannot_open_second_cash_session():
    operator = SystemUserFactory()
    open_cash_session(operator_user=operator, actor_user=operator, opening_balance=Decimal("30.00"))

    with pytest.raises(ValidationError, match="Ja existe um caixa aberto"):
        open_cash_session(operator_user=operator, actor_user=operator, opening_balance=Decimal("10.00"))


@pytest.mark.django_db
def test_closed_cash_session_rejects_additional_sales():
    session = CashSessionFactory(opening_balance=Decimal("20.00"), expected_cash_total=Decimal("20.00"))
    product = PdvProductFactory(unit_price=Decimal("15.00"))
    close_cash_session(cash_session=session, closed_by=session.operator_user, counted_cash_total=Decimal("20.00"))

    with pytest.raises(ValidationError, match="Abra um caixa antes de registrar vendas"):
        create_pdv_sale(
            operator_user=session.operator_user,
            payment_method="CASH",
            items=[{"product": product, "quantity": 1}],
            amount_received=Decimal("15.00"),
        )
