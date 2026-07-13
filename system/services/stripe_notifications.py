import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def _site_name():
    return getattr(settings, "SITE_NAME", "LV JIU JITSU")


def _from_email():
    return getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@lvjiujitsu.com.br")


def notify_payment_failed(membership, stripe_invoice=None):
    person = membership.person
    to_email = (person.email or "").strip()
    if not to_email:
        logger.warning(
            "notify_payment_failed: membership %s sem e-mail cadastrado — notificação ignorada.",
            membership.pk,
        )
        return

    name = (person.full_name or "").split()[0] or person.full_name
    plan_name = membership.plan.display_name if membership.plan else "sua assinatura"
    site_name = _site_name()
    from_email = _from_email()

    hosted_url = ""
    next_attempt_text = ""

    if stripe_invoice is not None:
        hosted_url = str(stripe_invoice.get("hosted_invoice_url") or "")
        next_attempt = stripe_invoice.get("next_payment_attempt")
        if next_attempt:
            from datetime import datetime, timezone as dt_timezone
            try:
                dt = datetime.fromtimestamp(int(next_attempt), tz=dt_timezone.utc)
                next_attempt_text = dt.strftime("%d/%m/%Y às %H:%Mh (UTC)")
            except (ValueError, TypeError, OSError):
                logger.debug(
                    "next_payment_attempt inválido na invoice Stripe (membership=%s).",
                    membership.pk,
                    exc_info=True,
                )

    subject = f"[{site_name}] Falha no pagamento da sua assinatura"

    body_lines = [
        f"Olá, {name}!",
        "",
        f"Infelizmente não conseguimos processar o pagamento referente ao plano «{plan_name}».",
        "",
        "O que fazer agora:",
        "  1. Verifique se os dados do seu cartão estão corretos e atualizados.",
        "  2. Confirme se há limite disponível no cartão.",
        "  3. Acesse o link abaixo para regularizar o pagamento diretamente:",
        "",
    ]

    if hosted_url:
        body_lines.append(f"  {hosted_url}")
    else:
        body_lines.append(f"  Entre em contato conosco para regularizar sua situação.")

    body_lines.append("")

    if next_attempt_text:
        body_lines.append(f"Faremos uma nova tentativa de cobrança em {next_attempt_text}.")
        body_lines.append("")

    body_lines += [
        "Se não regularizado, o acesso à academia poderá ser suspenso.",
        "",
        f"Qualquer dúvida, responda este e-mail ou procure a equipe {site_name}.",
        "",
        "Atenciosamente,",
        f"Equipe {site_name}",
    ]

    body = "\n".join(body_lines)

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.info(
            "notify_payment_failed: e-mail enviado para %s (membership=%s).",
            to_email,
            membership.pk,
        )
    except Exception:
        logger.exception(
            "notify_payment_failed: falha ao enviar e-mail para %s (membership=%s).",
            to_email,
            membership.pk,
        )


def notify_subscription_past_due(membership):
    person = membership.person
    to_email = (person.email or "").strip()
    if not to_email:
        logger.warning(
            "notify_subscription_past_due: membership %s sem e-mail — notificação ignorada.",
            membership.pk,
        )
        return

    name = (person.full_name or "").split()[0] or person.full_name
    plan_name = membership.plan.display_name if membership.plan else "sua assinatura"
    site_name = _site_name()
    from_email = _from_email()

    subject = f"[{site_name}] Sua assinatura está com pagamento pendente"

    body = "\n".join([
        f"Olá, {name}!",
        "",
        f"Identificamos uma pendência no pagamento do plano «{plan_name}».",
        "",
        "Para manter seu acesso à academia, regularize sua situação o quanto antes:",
        "  • Verifique o cartão cadastrado e atualize se necessário.",
        "  • Caso prefira, entre em contato com nossa equipe.",
        "",
        "Se não regularizado, o acesso poderá ser suspenso.",
        "",
        "Atenciosamente,",
        f"Equipe {site_name}",
    ])

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False,
        )
        logger.info(
            "notify_subscription_past_due: e-mail enviado para %s (membership=%s).",
            to_email,
            membership.pk,
        )
    except Exception:
        logger.exception(
            "notify_subscription_past_due: falha ao enviar e-mail para %s (membership=%s).",
            to_email,
            membership.pk,
        )
