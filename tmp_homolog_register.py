# -*- coding: utf-8 -*-
"""Temporary homologation script — do not commit."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from html import unescape
from typing import Any

import django
import requests

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvjiujitsu.settings")
django.setup()

from django.conf import settings
from system.models import (
    AdministrativeAccessRequest,
    ClassCatalogRequest,
    Person,
    PortalAccount,
    PreRegistration,
)
from system.services import asaas_client
from system.services.asaas_client import _request
from system.services.registration_checkout import create_pre_registration_plan_payment

BASE_URL = "http://localhost:8000"
PASSWORD = "Homolog@2026"
TIMEOUT = 60


@dataclass
class Result:
    profile: str
    email: str
    cpf: str
    reference: str = "-"
    status: str = "pendente"
    login: str = "-"
    notes: str = ""


def csrf_from(html: str) -> str:
    match = re.search(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\']+)', html)
    if not match:
        raise RuntimeError("CSRF nao encontrado em /register/.")
    return unescape(match.group(1))


def first_json_script(html: str, ids: tuple[str, ...]) -> Any:
    for script_id in ids:
        match = re.search(
            rf'<script[^>]+id=["\']{re.escape(script_id)}["\'][^>]*>(.*?)</script>',
            html,
            re.DOTALL | re.IGNORECASE,
        )
        if match:
            raw = unescape(match.group(1)).strip()
            if raw in {"true", "false"}:
                return raw == "true"
            return json.loads(raw)
    raise RuntimeError(f"JSON nao encontrado: {', '.join(ids)}")


def extract_form_errors(html: str) -> str:
    chunks: list[str] = []
    for pattern in (
        r'class=["\']wizard-errors__item["\'][^>]*>(.*?)</p>',
        r'class=["\']wizard-system-message[^"\']*["\'][^>]*>.*?</svg>\s*(.*?)</div>',
        r'class=["\']errorlist["\'][^>]*>\s*<li>(.*?)</li>',
        r'<ul class=["\']errorlist["\']>(.*?)</ul>',
    ):
        for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
            text = re.sub(r"<[^>]+>", " ", unescape(match.group(1)))
            text = re.sub(r"\s+", " ", text).strip()
            if text:
                chunks.append(text)
    # hidden field errors sometimes only in server-rendered values near messages
    for match in re.finditer(r'data-error=["\']([^"\']+)["\']', html):
        chunks.append(unescape(match.group(1)))
    return " | ".join(dict.fromkeys(chunks))[:1500]


def register_page(session: requests.Session) -> tuple[str, str, list[dict[str, Any]], dict[str, str]]:
    response = session.get(f"{BASE_URL}/register/", timeout=TIMEOUT)
    response.raise_for_status()
    html = response.text
    catalog = first_json_script(html, ("reg-plan-catalog-json",))
    class_catalog = first_json_script(html, ("reg-catalog-json",))
    classes: dict[str, str] = {}
    for item in class_catalog:
        audience = item.get("category_audience") or ""
        if audience and audience not in classes:
            classes[audience] = str(item["id"])
    if "adult" not in classes:
        raise RuntimeError("Turma Adulto nao encontrada no HTML de /register/.")
    return html, csrf_from(html), catalog, classes


def plan_id(catalog: list[dict[str, Any]], *, gateway: str, audience: str = "adult") -> str:
    matches = [
        item
        for item in catalog
        if item.get("audience") == audience
        and item.get("weekly_frequency") == 2
        and item.get("billing_cycle") == "monthly"
        and item.get("gateway_code") == gateway
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Plano {audience} 2x mensal {gateway} nao unico: {[m.get('id') for m in matches]}")
    return str(matches[0]["id"])


def post_register(session: requests.Session, payload: dict[str, Any], csrf: str) -> requests.Response:
    data = {"csrfmiddlewaretoken": csrf}
    for key, value in payload.items():
        data[key] = value
    response = session.post(f"{BASE_URL}/register/", data=data, timeout=TIMEOUT, allow_redirects=False)
    if response.status_code >= 500:
        raise RuntimeError(f"POST /register/ HTTP {response.status_code}: {response.text[:800]}")
    if response.status_code == 200:
        details = extract_form_errors(response.text)
        raise RuntimeError(f"Validacao recusou o cadastro: {details or 'sem detalhe HTML'}")
    if response.status_code not in (302, 303):
        raise RuntimeError(f"POST /register/ HTTP {response.status_code}: {response.text[:800]}")
    return response


def base_person(
    prefix: str,
    name: str,
    cpf: str,
    email: str,
    birthdate: str,
    phone: str,
    *,
    sex: str = "male",
    include_birthdate: bool = True,
) -> dict[str, str]:
    data = {
        f"{prefix}_name": name,
        f"{prefix}_cpf": cpf,
        f"{prefix}_biological_sex": sex,
        f"{prefix}_phone": phone,
        f"{prefix}_email": email,
        f"{prefix}_password": PASSWORD,
        f"{prefix}_password_confirm": PASSWORD,
        f"{prefix}_has_martial_art": "no",
        f"{prefix}_postal_code": "74000-000",
        f"{prefix}_address": "Rua de Homologacao",
        f"{prefix}_address_number": "100",
        f"{prefix}_address_neighborhood": "Centro",
        f"{prefix}_city": "Goiania",
    }
    if include_birthdate:
        data[f"{prefix}_birthdate"] = birthdate
    return data


def find_pre_registration(before: set[int], email: str, cpf: str) -> PreRegistration:
    candidates = list(PreRegistration.objects.exclude(pk__in=before).order_by("-created_at"))
    for item in candidates:
        blob = json.dumps(item.form_snapshot or {}, ensure_ascii=False)
        if email in blob or cpf in blob:
            return item
    if candidates:
        return candidates[0]
    raise RuntimeError("PreRegistration nao foi criado.")


def dump_payment_state(pr: PreRegistration) -> str:
    pr.refresh_from_db()
    snap = pr.form_snapshot or {}
    return (
        f"status={pr.status}; keys={sorted(snap.keys())}; "
        f"plan_payment={snap.get('plan_payment')}; checkout={snap.get('checkout_action')}"
    )


def ensure_asaas_plan_payment(pr: PreRegistration) -> str:
    """Ensure plan_payment exists; workaround Asaas domain mismatch on callback URL."""
    pr.refresh_from_db()
    snap = pr.form_snapshot or {}
    payment = snap.get("plan_payment") or {}
    payment_id = payment.get("asaas_payment_id")
    if payment_id:
        return payment_id

    try:
        invoice_url = create_pre_registration_plan_payment(pr, "pix")
        pr.refresh_from_db()
        payment = (pr.form_snapshot or {}).get("plan_payment") or {}
        payment_id = payment.get("asaas_payment_id")
        if payment_id:
            print(f"  [Asaas] pagamento criado via service: {payment_id} url={invoice_url[:80]}")
            return payment_id
    except asaas_client.AsaasClientError as exc:
        print(f"  [Asaas] create_pre_registration_plan_payment falhou: {exc}")
        print(f"  [Asaas] SITE_BASE_URL={settings.SITE_BASE_URL}")
        print("  [Asaas] tentando fallback sem callback.successUrl ...")

    # Fallback: create PIX without callback (domain not registered on Asaas account).
    from system.services.registration_checkout import (
        ensure_pre_registration_asaas_customer,
        parse_selected_plan_payload,
        resolve_catalog_plan,
    )

    pr.refresh_from_db()
    snap = pr.form_snapshot or {}
    selected_plans = parse_selected_plan_payload(snap)
    if not selected_plans:
        raise RuntimeError("Sem planos no snapshot para criar PIX Asaas.")
    plans_by_id = {}
    for item in selected_plans:
        legacy_plan, plan_price = resolve_catalog_plan(item["plan_id"])
        resolved = legacy_plan if legacy_plan is not None else plan_price
        if resolved is None:
            raise RuntimeError(f"Plano invalido: {item['plan_id']}")
        plans_by_id[item["plan_id"]] = resolved
    total = sum((plans_by_id[item["plan_id"]].price for item in selected_plans), Decimal("0.00"))
    customer_id = ensure_pre_registration_asaas_customer(pr)
    due_date = date.today() + timedelta(days=getattr(settings, "ASAAS_CARD_DUE_DAYS", 3))
    payment_resp = asaas_client.create_pix_payment(
        customer_id=customer_id,
        value=total,
        due_date=due_date,
        description=f"Mensalidade LV Jiu Jitsu - pre-cadastro #{pr.pk} (homolog sem callback)",
        external_reference=f"pre-registration:{pr.pk}:plan",
        success_url=None,
    )
    payment_id = payment_resp.get("id") or ""
    if not payment_id:
        raise RuntimeError(f"Asaas sem id no fallback: {payment_resp}")
    snap = pr.form_snapshot or {}
    snap["plan_payment"] = {
        "asaas_payment_id": payment_id,
        "total": str(total),
        "items": [
            {
                "label": item.get("label", ""),
                "plan_id": item["plan_id"],
                "plan_name": plans_by_id[item["plan_id"]].display_name,
                "price": str(plans_by_id[item["plan_id"]].price),
            }
            for item in selected_plans
        ],
        "homolog_fallback_no_callback": True,
    }
    pr.form_snapshot = snap
    pr.save(update_fields=["form_snapshot", "updated_at"])
    if hasattr(pr, "mark_awaiting_payment"):
        pr.mark_awaiting_payment()
    print(f"  [Asaas] fallback OK payment_id={payment_id}")
    return payment_id


def person_by_cpf(cpf: str) -> Person | None:
    return Person.objects.filter(cpf=cpf).first()


def portal_login_for_person(person: Person | None) -> str:
    if person is None:
        return "-"
    account = PortalAccount.objects.filter(person=person).first()
    # PortalAccount has no email/login; auth uses Person.email / CPF.
    email = getattr(person, "email", "") or ""
    cpf = getattr(person, "cpf", "") or ""
    acc_id = account.pk if account else "-"
    return f"PortalAccount:{acc_id}; login=email:{email} ou cpf:{cpf}"


def finalize_paid(session: requests.Session, csrf: str, pr: PreRegistration, gateway: str, owner_cpf: str) -> int:
    pr.refresh_from_db()
    print(f"  [pre] {dump_payment_state(pr)}")
    if gateway == "asaas":
        payment_id = ensure_asaas_plan_payment(pr)
        confirmation = _request("POST", f"/sandbox/payment/{payment_id}/confirm", json_body={})
        print(f"  [Asaas] confirm => {confirmation.get('status')}")
        if confirmation.get("status") not in {"RECEIVED", "CONFIRMED", "RECEIVED_IN_CASH"}:
            raise RuntimeError(f"Asaas nao confirmou: {confirmation}")
        params = {"pre_registration_id": pr.pk, "id": payment_id, "stage": "plan"}
    else:
        payment = (pr.form_snapshot or {}).get("plan_payment") or {}
        if not payment.get("stripe_session_id") and not (pr.form_snapshot or {}).get("plan_paid"):
            # session should exist after checkout redirect creation
            pass
        if not shutil.which("stripe"):
            raise RuntimeError("Stripe CLI indisponivel.")
        cmd = [
            "stripe",
            "trigger",
            "checkout.session.completed",
            "--override",
            f"checkout_session:client_reference_id=pre-registration:{pr.pk}",
        ]
        triggered = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if triggered.returncode:
            raise RuntimeError(f"stripe trigger falhou: {(triggered.stdout or '') + (triggered.stderr or '')}")
        for _ in range(10):
            pr.refresh_from_db()
            if (pr.form_snapshot or {}).get("plan_paid"):
                break
            import time

            time.sleep(0.5)
        pr.refresh_from_db()
        payment = (pr.form_snapshot or {}).get("plan_payment") or {}
        session_id = payment.get("stripe_session_id")
        if not session_id:
            raise RuntimeError(f"Webhook Stripe nao gravou session. state={dump_payment_state(pr)}")
        params = {"pre_registration_id": pr.pk, "session_id": session_id, "stage": "plan"}

    response = session.get(f"{BASE_URL}/pagamentos/sucesso/", params=params, timeout=TIMEOUT, allow_redirects=False)
    if response.status_code not in (302, 303):
        raise RuntimeError(f"GET /pagamentos/sucesso/ HTTP {response.status_code}")

    # refresh csrf after redirects
    _, csrf, _, _ = register_page(session)
    response = session.post(
        f"{BASE_URL}/register/materiais/",
        data={
            "csrfmiddlewaretoken": csrf,
            "selected_products_payload": "[]",
            "checkout_action": "pay_later",
        },
        timeout=TIMEOUT,
        allow_redirects=False,
    )
    if response.status_code not in (302, 303):
        raise RuntimeError(f"Pular materiais falhou: HTTP {response.status_code}")

    _, csrf, _, _ = register_page(session)
    response = session.post(
        f"{BASE_URL}/register/finalizar/",
        data={"csrfmiddlewaretoken": csrf},
        timeout=TIMEOUT,
        allow_redirects=False,
    )
    if response.status_code not in (302, 303):
        raise RuntimeError(f"Finalizacao falhou: HTTP {response.status_code}")

    person = person_by_cpf(owner_cpf)
    return person.pk if person else 0


def handle_checkout_redirect(session: requests.Session, response: requests.Response, pr: PreRegistration, gateway: str) -> None:
    location = response.headers.get("Location", "")
    print(f"  [redirect] {location[:160]}")
    if gateway == "asaas":
        if "asaas" in location.lower() or "invoice" in location.lower():
            # Checkout created; plan_payment should be in ORM
            pr.refresh_from_db()
            print(f"  [asaas redirect] {dump_payment_state(pr)}")
            return
        if "/register" in location:
            # Payment failed — follow to capture flash message, then try fallback
            follow = session.get(f"{BASE_URL}{location}" if location.startswith("/") else location, timeout=TIMEOUT)
            msg = extract_form_errors(follow.text)
            print(f"  [asaas fail msg] {msg or '(sem mensagem)'}")
            print(f"  [asaas fail state] {dump_payment_state(pr)}")
            return
    if gateway == "stripe":
        if "stripe.com" in location or "checkout.stripe" in location:
            pr.refresh_from_db()
            print(f"  [stripe redirect] {dump_payment_state(pr)}")
            return
        if "/register" in location:
            follow = session.get(f"{BASE_URL}{location}" if location.startswith("/") else location, timeout=TIMEOUT)
            raise RuntimeError(f"Stripe checkout falhou: {extract_form_errors(follow.text)}")


def paid_holder(result: Result, gateway: str, catalog: list[dict[str, Any]], classes: dict[str, str]) -> None:
    existing = person_by_cpf(result.cpf)
    if existing and gateway == "stripe_card":
        result.reference = f"person:{existing.pk}"
        result.login = portal_login_for_person(existing)
        result.status = "ja finalizado (skip)"
        return

    session = requests.Session()
    _, csrf, _, _ = register_page(session)
    before = set(PreRegistration.objects.values_list("pk", flat=True))
    selected = plan_id(catalog, gateway=gateway, audience="adult")
    payload = {
        "registration_profile": "holder",
        "include_dependent": "",
        "extra_dependents_payload": "[]",
        "holder_class_groups": classes["adult"],
        "selected_plan": selected,
        "selected_plans_payload": json.dumps([{"person_index": 0, "plan_id": selected}]),
        "selected_products_payload": "[]",
        "checkout_action": "pix" if gateway == "asaas_pix" else "stripe_card",
        **base_person(
            "holder",
            "Homolog Aluno Asaas" if gateway == "asaas_pix" else "Homolog Aluno Stripe",
            result.cpf,
            result.email,
            "15/03/1990",
            "(62) 99111-0001",
        ),
    }
    response = post_register(session, payload, csrf)
    pr = find_pre_registration(before, result.email, result.cpf)
    result.reference = f"pre_registration:{pr.pk}"
    handle_checkout_redirect(session, response, pr, "asaas" if gateway == "asaas_pix" else "stripe")
    person_id = finalize_paid(session, csrf, pr, "asaas" if gateway == "asaas_pix" else "stripe", result.cpf)
    person = person_by_cpf(result.cpf)
    result.reference = f"person:{person.pk if person else person_id}"
    result.login = portal_login_for_person(person)
    result.status = "finalizado"


def paid_guardian(
    result: Result,
    gateway: str,
    catalog: list[dict[str, Any]],
    classes: dict[str, str],
    student_cpf: str,
    student_name: str,
) -> None:
    session = requests.Session()
    _, csrf, _, _ = register_page(session)
    before = set(PreRegistration.objects.values_list("pk", flat=True))
    # student born 2012 => kids/juvenile audience
    selected = plan_id(catalog, gateway=gateway, audience="kids_juvenile")
    student_class = classes.get("juvenile") or classes.get("kids")
    if not student_class:
        raise RuntimeError("Turma kids/juvenil nao encontrada.")
    student = base_person("student", student_name, student_cpf, "", "10/05/2012", "(62) 99111-0002")
    student["student_email"] = ""
    student["student_kinship_type"] = "father"
    payload = {
        "registration_profile": "guardian",
        "include_dependent": "",
        "extra_dependents_payload": "[]",
        "student_class_groups": student_class,
        "selected_plan": selected,
        "selected_plans_payload": json.dumps([{"person_index": 0, "plan_id": selected}]),
        "selected_products_payload": "[]",
        "checkout_action": "pix" if gateway == "asaas_pix" else "stripe_card",
        **base_person(
            "guardian",
            "Homolog Responsavel",
            result.cpf,
            result.email,
            "10/01/1985",
            "(62) 99111-0003",
            include_birthdate=False,
        ),
        **student,
    }
    response = post_register(session, payload, csrf)
    pr = find_pre_registration(before, result.email, result.cpf)
    result.reference = f"pre_registration:{pr.pk}"
    handle_checkout_redirect(session, response, pr, "asaas" if gateway == "asaas_pix" else "stripe")
    finalize_paid(session, csrf, pr, "asaas" if gateway == "asaas_pix" else "stripe", result.cpf)
    guardian = person_by_cpf(result.cpf)
    student_person = person_by_cpf(student_cpf)
    result.reference = (
        f"guardian_person:{(guardian.pk if guardian else '-')}; "
        f"student_person:{(student_person.pk if student_person else '-')}"
    )
    result.login = portal_login_for_person(guardian)
    result.status = "finalizado"


def operational(result: Result, kind: str, catalog: list[dict[str, Any]], classes: dict[str, str]) -> None:
    session = requests.Session()
    _, csrf, _, _ = register_page(session)
    before_pr = set(PreRegistration.objects.values_list("pk", flat=True))
    before_admin = set(AdministrativeAccessRequest.objects.values_list("pk", flat=True))
    before_teacher = set(ClassCatalogRequest.objects.values_list("pk", flat=True))

    is_admin = kind.startswith("admin")
    payload: dict[str, Any] = {
        "registration_profile": "other",
        "other_type_code": "administrative-assistant" if is_admin else "instructor",
        "include_dependent": "",
        "extra_dependents_payload": "[]",
        "selected_products_payload": "[]",
        "checkout_action": "pay_later",
        "selected_plan": "",
        "selected_plans_payload": "[]",
        **base_person(
            "other",
            "Homolog Administrativo" if is_admin else "Homolog Professor",
            result.cpf,
            result.email,
            "10/01/1985",
            "(62) 99111-0004",
        ),
        "operational_training_intent": "none",
        "operational_financial_arrangement": "volunteer",
        "operational_payment_condition": "no_monthly_fee",
        "operational_compensation_preference": "none",
        "operational_payout_method": "none",
        "operational_requested_roles_payload": "",
        "teacher_assignment_mode": "",
        "teacher_existing_class_group": "",
        "teacher_existing_class_groups_payload": "",
        "teacher_proposed_schedule_payload": "",
    }

    if is_admin:
        payload["operational_requested_roles_payload"] = json.dumps(["people-support"])
        if kind == "admin_student":
            # Wizard operacional NAO inclui step-plan (register.js).
            # pays_monthly + training_intent=student ficam no request_payload;
            # cobranca Asaas de mensalidade nao ocorre neste POST.
            payload.update(
                {
                    "operational_training_intent": "student",
                    "operational_financial_arrangement": "pays_monthly",
                    "operational_payment_condition": "pay_monthly",
                    "checkout_action": "pay_later",
                    "selected_plan": "",
                    "selected_plans_payload": "[]",
                }
            )

    if kind == "teacher":
        from system.models import ClassCategory

        category_id = ClassCategory.objects.values_list("pk", flat=True).first()
        if not category_id:
            raise RuntimeError("Nenhuma ClassCategory no banco.")
        payload.update(
            {
                "teacher_assignment_mode": "propose",
                "teacher_proposed_schedule_payload": json.dumps(
                    {
                        "category_id": str(category_id),
                        "category_label": "Adulto",
                        "display_name": "Jiu Jitsu Homolog",
                        "weekdays": ["monday", "wednesday"],
                        "weekday_labels": ["Segunda-feira", "Quarta-feira"],
                        "start_time": "20:00",
                    },
                    ensure_ascii=False,
                ),
                "operational_financial_arrangement": "volunteer",
            }
        )

    response = post_register(session, payload, csrf)
    location = response.headers.get("Location", "")
    print(f"  [operational redirect] {location}")

    if "/login" not in location and location and "/register" in location:
        follow = session.get(f"{BASE_URL}{location}" if location.startswith("/") else location, timeout=TIMEOUT)
        raise RuntimeError(f"Operacional nao concluiu: {extract_form_errors(follow.text) or location}")

    admin_req = (
        AdministrativeAccessRequest.objects.exclude(pk__in=before_admin)
        .filter(cpf=result.cpf)
        .order_by("-pk")
        .first()
    )
    teacher_req = (
        ClassCatalogRequest.objects.exclude(pk__in=before_teacher)
        .filter(cpf=result.cpf)
        .order_by("-pk")
        .first()
    )
    if admin_req:
        result.reference = f"admin_request:{admin_req.pk}"
        intent = ((admin_req.request_payload or {}) if hasattr(admin_req, "request_payload") else {}) or {}
        extra = ""
        if kind == "admin_student":
            extra = " (training=student; pays_monthly intent; sem cobranca Asaas neste wizard)"
        result.status = f"solicitacao:{admin_req.status}{extra}"
        result.login = f"pending request; email:{result.email}"
    elif teacher_req:
        result.reference = f"class_catalog_request:{teacher_req.pk}"
        result.status = f"solicitacao:{teacher_req.status}"
        result.login = f"pending request; email:{result.email}"
    else:
        result.reference = location or "-"
        result.status = "enviado (request nao localizada no ORM)"


def main() -> int:
    session = requests.Session()
    _, _, catalog, classes = register_page(session)
    print(
        "Catalogo: "
        f"adult_asaas={plan_id(catalog, gateway='asaas_pix')}; "
        f"adult_stripe={plan_id(catalog, gateway='stripe_card')}; "
        f"kids_asaas={plan_id(catalog, gateway='asaas_pix', audience='kids_juvenile')}; "
        f"classes={classes}"
    )
    print(f"SITE_BASE_URL={settings.SITE_BASE_URL}")

    results = [
        Result("Aluno Asaas PIX", "homolog.aluno.asaas@lvteste.local", "222.555.888-46"),
        Result("Aluno Stripe", "homolog.aluno.stripe@lvteste.local", "111.444.777-35"),
        Result("Responsavel Asaas + aluno", "homolog.resp.asaas@lvteste.local", "987.654.321-00"),
        Result("Responsavel Stripe + aluno", "homolog.resp.stripe@lvteste.local", "333.666.999-57"),
        Result("Administrativo sem treino", "homolog.admin.only@lvteste.local", "456.789.012-49"),
        Result("Administrativo + aluno", "homolog.admin.aluno@lvteste.local", "258.147.369-09"),
        Result("Professor proposta", "homolog.professor@lvteste.local", "567.890.123-03"),
    ]
    tasks = [
        lambda: paid_holder(results[0], "asaas_pix", catalog, classes),
        lambda: paid_holder(results[1], "stripe_card", catalog, classes),
        lambda: paid_guardian(
            results[2], "asaas_pix", catalog, classes, "147.258.369-82", "Homolog Aluno Resp Asaas"
        ),
        lambda: paid_guardian(
            results[3], "stripe_card", catalog, classes, "123.456.789-09", "Homolog Aluno Resp Stripe"
        ),
        lambda: operational(results[4], "admin_only", catalog, classes),
        lambda: operational(results[5], "admin_student", catalog, classes),
        lambda: operational(results[6], "teacher", catalog, classes),
    ]

    for result, task in zip(results, tasks):
        print(f"\n=== {result.profile} ===")
        try:
            task()
        except Exception as error:
            result.status = f"ERRO: {type(error).__name__}: {error}"
            print(f"  ERROR: {result.status}")

    print("\nperfil | email | senha | cpf | person_id/request_id | login | status")
    for item in results:
        print(
            f"{item.profile} | {item.email} | {PASSWORD} | {item.cpf} | "
            f"{item.reference} | {item.login} | {item.status}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())


