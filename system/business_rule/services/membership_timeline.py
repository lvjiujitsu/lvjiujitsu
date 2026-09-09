from datetime import date, datetime

from django.utils import timezone

from system.business_rule.models.membership_timeline import (
    MembershipTimelineEvent,
    MembershipTimelineEventType,
)
from system.business_rule.selectors.plan_eligibility import get_family_group_members


def record_membership_event(
    person,
    event_type,
    *,
    membership=None,
    actor=None,
    actor_is_admin=False,
    context=None,
):
    return MembershipTimelineEvent.objects.create(
        person=person,
        membership=membership,
        event_type=event_type,
        actor=actor,
        actor_is_admin=actor_is_admin,
        context=context or {},
    )


def build_client_timeline(person, *, limit=30):

    members = get_family_group_members(person)
    events = (
        MembershipTimelineEvent.objects.filter(person__in=members)
        .select_related("person")
        .order_by("-created_at")[:limit]
    )
    return [
        {
            "id": event.pk,
            "created_at": event.created_at,
            "person_name": event.person.full_name,
            "description": describe_for_client(event),
        }
        for event in events
    ]


def build_admin_timeline(*, person=None, event_type="", limit=200):
    events = MembershipTimelineEvent.objects.select_related("person", "actor")
    if person is not None:
        events = events.filter(person=person)
    if event_type:
        events = events.filter(event_type=event_type)
    events = events.order_by("-created_at")[:limit]
    return [
        {
            "id": event.pk,
            "created_at": event.created_at,
            "person_name": event.person.full_name,
            "event_type": event.event_type,
            "event_type_label": event.get_event_type_display(),
            "description": describe_for_admin(event),
        }
        for event in events
    ]


def _fmt_date(value):
    if value is None or value == "":
        return ""
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value[:10])
        except ValueError:
            return value
    if isinstance(value, datetime):
        value = timezone.localtime(value).date() if timezone.is_aware(value) else value.date()
    return value.strftime("%d/%m/%Y")


def _fmt_money(value):
    if value is None:
        return ""
    return f"R$ {value}"


_CLIENT_TEMPLATES = {
    MembershipTimelineEventType.DEPENDENT_ADDED: lambda ctx: (
        f"{ctx.get('dependent_name', 'Dependente')} foi adicionado à família."
    ),
    MembershipTimelineEventType.DEPENDENT_REMOVED: lambda ctx: (
        f"{ctx.get('dependent_name', 'Dependente')} foi removido da família."
    ),
    MembershipTimelineEventType.PAUSE_REQUESTED: lambda ctx: (
        "Pausa da mensalidade solicitada"
        + (f" ({_fmt_date(ctx.get('start_date'))} a {_fmt_date(ctx.get('end_date'))})"
           if ctx.get("start_date") else "")
        + "."
    ),
    MembershipTimelineEventType.PAUSE_APPROVED: lambda ctx: (
        "Pausa da mensalidade aprovada"
        + (f" — vigência prorrogada em {ctx['duration_days']} dia(s)."
           if ctx.get("duration_days") else ".")
    ),
    MembershipTimelineEventType.PAUSE_REJECTED: lambda ctx: (
        "Pausa da mensalidade recusada."
    ),
    MembershipTimelineEventType.PLAN_CHANGED: lambda ctx: (
        f"Plano alterado de {ctx.get('old_plan_name', '—')} para {ctx.get('new_plan_name', '—')}."
    ),
    MembershipTimelineEventType.MEMBERSHIP_CANCELED: lambda ctx: (
        f"Assinatura{(' do plano ' + ctx['plan_name']) if ctx.get('plan_name') else ''} cancelada."
    ),
    MembershipTimelineEventType.CARD_UPDATED: lambda ctx: "Cartão de pagamento atualizado.",
    MembershipTimelineEventType.PAYMENT_CONFIRMED: lambda ctx: (
        f"Pagamento de {_fmt_money(ctx['amount'])} confirmado."
        if ctx.get("amount") else "Pagamento confirmado."
    ),
    MembershipTimelineEventType.PAYMENT_FAILED: lambda ctx: (
        "A cobrança da mensalidade falhou — atualize a forma de pagamento."
    ),
    MembershipTimelineEventType.REFUND_ISSUED: lambda ctx: (
        f"Estorno de {_fmt_money(ctx['amount'])} realizado."
        if ctx.get("amount") else "Estorno realizado."
    ),
    MembershipTimelineEventType.FAMILY_DISCOUNT_CHANGED: lambda ctx: (
        "Desconto família passou a valer na sua mensalidade."
        if ctx.get("discount_applied")
        else "Desconto família deixou de valer na sua mensalidade."
    ),
}

_ADMIN_TEMPLATES = {
    MembershipTimelineEventType.DEPENDENT_ADDED: lambda ctx: (
        f"Dependente adicionado: {ctx.get('dependent_name', '—')}."
    ),
    MembershipTimelineEventType.DEPENDENT_REMOVED: lambda ctx: (
        f"Dependente removido: {ctx.get('dependent_name', '—')}."
    ),
    MembershipTimelineEventType.PAUSE_REQUESTED: lambda ctx: (
        f"Pausa ({ctx.get('kind', '—')}) solicitada: "
        f"{_fmt_date(ctx.get('start_date'))} a {_fmt_date(ctx.get('end_date'))}."
    ),
    MembershipTimelineEventType.PAUSE_APPROVED: lambda ctx: (
        f"Pausa ({ctx.get('kind', '—')}) aprovada — "
        f"{ctx.get('duration_days', '—')} dia(s) de prorrogação."
    ),
    MembershipTimelineEventType.PAUSE_REJECTED: lambda ctx: (
        f"Pausa ({ctx.get('kind', '—')}) recusada"
        + (f": {ctx['decision_notes']}" if ctx.get("decision_notes") else ".")
    ),
    MembershipTimelineEventType.PLAN_CHANGED: lambda ctx: (
        f"Plano alterado: {ctx.get('old_plan_name', '—')} "
        f"({_fmt_money(ctx.get('old_price'))}) → {ctx.get('new_plan_name', '—')} "
        f"({_fmt_money(ctx.get('new_price'))})."
    ),
    MembershipTimelineEventType.MEMBERSHIP_CANCELED: lambda ctx: (
        f"Assinatura cancelada"
        + (f" (Stripe: {ctx['stripe_subscription_id']})" if ctx.get("stripe_subscription_id") else "")
        + "."
    ),
    MembershipTimelineEventType.CARD_UPDATED: lambda ctx: (
        "Cliente redirecionado ao Stripe Billing Portal para troca de cartão."
    ),
    MembershipTimelineEventType.PAYMENT_CONFIRMED: lambda ctx: (
        f"Pagamento confirmado — {_fmt_money(ctx.get('amount'))}"
        + (f" (order #{ctx['order_id']})" if ctx.get("order_id") else "")
        + (f" (invoice {ctx['stripe_invoice_id']})" if ctx.get("stripe_invoice_id") else "")
        + "."
    ),
    MembershipTimelineEventType.PAYMENT_FAILED: lambda ctx: (
        f"Cobrança falhou — {_fmt_money(ctx.get('amount'))}"
        + (f" (invoice {ctx['stripe_invoice_id']})" if ctx.get("stripe_invoice_id") else "")
        + "."
    ),
    MembershipTimelineEventType.REFUND_ISSUED: lambda ctx: (
        f"Estorno — {_fmt_money(ctx.get('amount'))}"
        + (f" (order #{ctx['order_id']})" if ctx.get("order_id") else "")
        + "."
    ),
    MembershipTimelineEventType.FAMILY_DISCOUNT_CHANGED: lambda ctx: (
        f"Desconto família {'aplicado' if ctx.get('discount_applied') else 'removido'} — "
        f"{_fmt_money(ctx.get('old_price'))} → {_fmt_money(ctx.get('new_price'))}."
    ),
}


def describe_for_client(event):
    template = _CLIENT_TEMPLATES.get(event.event_type)
    if template is None:
        return event.get_event_type_display()
    return template(event.context or {})


def describe_for_admin(event):
    template = _ADMIN_TEMPLATES.get(event.event_type)
    base = template(event.context or {}) if template else event.get_event_type_display()
    actor_label = "Sistema/webhook"
    if event.actor_id:
        actor_label = event.actor.full_name + (" (admin)" if event.actor_is_admin else "")
    return f"{base} — por {actor_label}"
