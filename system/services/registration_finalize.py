from django.utils import timezone

from system.forms import PortalRegistrationForm
from system.models.registration_order import PaymentStatus
from system.models.pre_registration import PreRegistrationStatus
from system.services.pre_registration import (
    grant_trial_for_pre_registration,
    normalize_snapshot_for_form,
)
from system.services.registration import create_portal_registration


class RegistrationFinalizeService:
    @staticmethod
    def create_from_pre_registration(pre_registration):
        if (
            pre_registration.status == PreRegistrationStatus.FINALIZED
            and pre_registration.finalized_person
        ):
            return {
                "ok": True,
                "error": None,
                "person": pre_registration.finalized_person,
                "portal_account": getattr(
                    pre_registration.finalized_person, "access_account", None
                ),
                "already_finalized": True,
            }

        form_data = normalize_snapshot_for_form(pre_registration.form_snapshot or {})
        form = PortalRegistrationForm(data=form_data)
        if not form.is_valid():
            return {
                "ok": False,
                "error": "Revise os dados do cadastro antes de finalizar.",
                "person": None,
                "portal_account": None,
                "already_finalized": False,
            }

        created_people = create_portal_registration(form.cleaned_data)
        primary_person = (
            created_people.get("holder")
            or created_people.get("guardian")
            or created_people.get("other")
        )
        if primary_person is None:
            return {
                "ok": False,
                "error": "Não foi possível finalizar o cadastro.",
                "person": None,
                "portal_account": None,
                "already_finalized": False,
            }

        people_to_activate = [primary_person, *created_people.get("dependents", [])]
        for person in people_to_activate:
            if not person.is_active:
                person.is_active = True
                person.save(update_fields=["is_active", "updated_at"])
            account = getattr(person, "access_account", None)
            if account and not account.is_active:
                account.is_active = True
                account.save(update_fields=["is_active", "updated_at"])

        portal_account = getattr(primary_person, "access_account", None)

        pre_registration.mark_finalized(primary_person)

        snapshot = pre_registration.form_snapshot or {}
        order = created_people.get("order")
        if (
            order is not None
            and snapshot.get("plan_paid")
            and order.payment_status == PaymentStatus.PENDING
        ):
            plan_payment = snapshot.get("plan_payment") or {}
            asaas_payment_id = plan_payment.get("asaas_payment_id") or ""
            order.payment_status = PaymentStatus.PAID
            order.paid_at = timezone.now()
            if asaas_payment_id:
                order.asaas_payment_id = asaas_payment_id
            order.save(
                update_fields=["payment_status", "paid_at", "asaas_payment_id", "updated_at"]
            )
            from system.services.membership import activate_membership_from_paid_order

            activate_membership_from_paid_order(
                order,
                notes="Pagamento confirmado via pré-cadastro.",
                stripe_subscription_id=plan_payment.get("stripe_subscription_id", ""),
                stripe_subscription_item_id=plan_payment.get(
                    "stripe_subscription_item_id", ""
                ),
                stripe_customer_id=plan_payment.get("stripe_customer_id", ""),
            )

        if snapshot.get("trial_requested"):
            grant_trial_for_pre_registration(pre_registration, primary_person)

        return {
            "ok": True,
            "error": None,
            "person": primary_person,
            "portal_account": portal_account,
            "already_finalized": False,
        }
