from datetime import time
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.utils import timezone

from system.models import (
    AUDIENCE_ALL_USERS,
    AcademyConfiguration,
    ClassDiscipline,
    ConsentTerm,
    CsvExportControl,
    FinancialPlan,
    NoticeBoardMessage,
    PdvProduct,
    PublicClassSchedule,
    PublicPlan,
    StripePlanPriceMap,
    SystemUser,
)


ACADEMY_CONFIGURATION_DATA = {
    "academy_name": "LV JIU JITSU",
    "hero_title": "LV Culture of Martial Arts",
    "hero_subtitle": (
        "Treine Jiu-Jitsu com disciplina, comunidade e horarios claros, com uma jornada que conecta comercial, "
        "matricula, presenca e pagamentos sem improviso."
    ),
    "public_whatsapp": "62999876471",
    "public_email": "",
    "public_instagram": "@lvjiujitsu",
    "public_address": "",
    "public_notice": (
        "Loja oficial LEALDADE E VIRTUDE, canal Kanri parceiro DMZDUJYE e atendimento comercial pelo WhatsApp."
    ),
}

PUBLIC_PLANS = (
    {
        "name": "Plano Mensal",
        "billing_cycle": PublicPlan.BILLING_MONTHLY,
        "amount": Decimal("250.00"),
        "summary": "Plano convencional divulgado no site com pagamento via Pix, boleto ou credito.",
        "cta_label": "Quero este plano",
        "is_featured": True,
        "display_order": 1,
    },
    {
        "name": "Plano Mensal Irmaos/Pais e Filhos",
        "billing_cycle": PublicPlan.BILLING_MONTHLY,
        "amount": Decimal("225.00"),
        "summary": "Plano comercial para familia, irmaos ou pais e filhos, conforme a vitrine publica da academia.",
        "cta_label": "Quero falar com a equipe",
        "display_order": 2,
    },
    {
        "name": "Plano Trimestral",
        "billing_cycle": PublicPlan.BILLING_QUARTERLY,
        "amount": Decimal("675.00"),
        "summary": "Plano convencional de maior compromisso, publicado na pagina de planos do site oficial.",
        "cta_label": "Quero este plano",
        "display_order": 3,
    },
)

PUBLIC_CLASS_SCHEDULES = (
    ("Turma Matutina 06h30 · Gi", PublicClassSchedule.WEEKDAY_MONDAY, time(6, 30), time(7, 30), "Layon Quirino", 1),
    ("Turma Matutina 06h30 · Gi", PublicClassSchedule.WEEKDAY_TUESDAY, time(6, 30), time(7, 30), "Layon Quirino", 2),
    ("Turma Matutina 06h30 · No-Gi", PublicClassSchedule.WEEKDAY_WEDNESDAY, time(6, 30), time(7, 30), "Layon Quirino", 3),
    ("Turma Matutina 06h30 · Gi", PublicClassSchedule.WEEKDAY_THURSDAY, time(6, 30), time(7, 30), "Layon Quirino", 4),
    ("Turma Matutina 06h30 · Gi", PublicClassSchedule.WEEKDAY_FRIDAY, time(6, 30), time(7, 30), "Layon Quirino", 5),
    ("Turma Matutina 11h · Gi", PublicClassSchedule.WEEKDAY_MONDAY, time(11, 0), time(12, 0), "Vinicius Antonio", 6),
    ("Turma Matutina 11h · Gi", PublicClassSchedule.WEEKDAY_WEDNESDAY, time(11, 0), time(12, 0), "Vinicius Antonio", 7),
    ("Turma Matutina 11h · No-Gi", PublicClassSchedule.WEEKDAY_FRIDAY, time(11, 0), time(12, 0), "Vinicius Antonio", 8),
    ("Turma Noturna 19h · Gi", PublicClassSchedule.WEEKDAY_MONDAY, time(19, 0), time(20, 15), "Lauro Viana", 9),
    ("Turma Noturna 19h · Gi", PublicClassSchedule.WEEKDAY_TUESDAY, time(19, 0), time(20, 15), "Lauro Viana", 10),
    ("Turma Noturna 19h · No-Gi", PublicClassSchedule.WEEKDAY_WEDNESDAY, time(19, 0), time(20, 15), "Lauro Viana", 11),
    ("Turma Noturna 19h · Gi", PublicClassSchedule.WEEKDAY_THURSDAY, time(19, 0), time(20, 15), "Lauro Viana", 12),
    ("Turma Noturna 19h · Gi", PublicClassSchedule.WEEKDAY_FRIDAY, time(19, 0), time(20, 15), "Lauro Viana", 13),
    ("Jiu-Jitsu Kids 18h", PublicClassSchedule.WEEKDAY_TUESDAY, time(18, 0), time(19, 0), "Andre Oliveira", 14),
    ("Jiu-Jitsu Kids 18h", PublicClassSchedule.WEEKDAY_THURSDAY, time(18, 0), time(19, 0), "Andre Oliveira", 15),
    ("Jiu-Jitsu Juvenil 18h", PublicClassSchedule.WEEKDAY_MONDAY, time(18, 0), time(19, 0), "Layon Quirino", 16),
    ("Jiu-Jitsu Juvenil 18h", PublicClassSchedule.WEEKDAY_WEDNESDAY, time(18, 0), time(19, 0), "Layon Quirino", 17),
    ("Jiu-Jitsu Juvenil 18h", PublicClassSchedule.WEEKDAY_FRIDAY, time(18, 0), time(19, 0), "Layon Quirino", 18),
    ("Jiu-Jitsu Feminino 10h30", PublicClassSchedule.WEEKDAY_SATURDAY, time(10, 30), time(11, 30), "Vannessa Ferro", 19),
)

DISCIPLINES = (
    ("Jiu-Jitsu Gi", "jiu-jitsu-gi", "Treinos de kimono com base na agenda publica da academia."),
    ("Jiu-Jitsu No-Gi", "jiu-jitsu-no-gi", "Treinos sem kimono conforme os horarios divulgados no site."),
    ("Jiu-Jitsu Kids", "jiu-jitsu-kids", "Turmas infantis divulgadas pela academia."),
    ("Jiu-Jitsu Juvenil", "jiu-jitsu-juvenil", "Turmas juvenis divulgadas pela academia."),
    ("Jiu-Jitsu Feminino", "jiu-jitsu-feminino", "Treino feminino divulgado na agenda publica."),
)

FINANCIAL_PLANS = (
    ("Mensal Publico", "mensal-publico", FinancialPlan.CYCLE_MONTHLY, Decimal("250.00"), "Plano mensal comercial publicado no site oficial."),
    ("Mensal Familia", "mensal-familia", FinancialPlan.CYCLE_MONTHLY, Decimal("225.00"), "Plano comercial para irmaos ou pais e filhos publicado no site."),
    ("Trimestral Publico", "trimestral-publico", FinancialPlan.CYCLE_QUARTERLY, Decimal("675.00"), "Plano trimestral convencional divulgado na pagina de planos."),
    ("Mensal Recorrente Stripe", "mensal-recorrente-stripe", FinancialPlan.CYCLE_MONTHLY, Decimal("250.00"), "Plano mensal recorrente com Price vigente na Stripe."),
    ("Mensal Bolsista", "mensal-bolsista", FinancialPlan.CYCLE_MONTHLY, Decimal("210.00"), "Plano mensal bolsista mapeado no catalogo Stripe."),
    ("Trimestral Recorrente Stripe", "trimestral-recorrente-stripe", FinancialPlan.CYCLE_QUARTERLY, Decimal("400.00"), "Plano trimestral recorrente com Price atual no Stripe."),
    ("Semestral Recorrente Stripe", "semestral-recorrente-stripe", FinancialPlan.CYCLE_SEMIANNUAL, Decimal("800.00"), "Plano semestral recorrente com Price atual no Stripe."),
    ("Anual Recorrente Stripe", "anual-recorrente-stripe", FinancialPlan.CYCLE_ANNUAL, Decimal("1200.00"), "Plano anual recorrente com Price atual no Stripe."),
    ("Anual Credito Mensal Recorrente", "anual-credito-mensal-recorrente", FinancialPlan.CYCLE_MONTHLY, Decimal("135.00"), "Plano anual parcelado mensalmente com Price especifico na Stripe."),
)

STRIPE_PRICE_MAPS = (
    ("mensal-recorrente-stripe", "prod_TlIMpPoIVLi9PX", "price_1SnllzHDywrdzSUoHLdZvLsK", "Plano Mensal Nova Tabela", Decimal("250.00"), "month", 1, True, False, "Plano mensal atual identificado na documentacao Stripe do projeto."),
    ("mensal-recorrente-stripe", "prod_QY0xqmFzwhYSbU", "price_1PguvxHDywrdzSUouHFmUkU3", "Mensal Cartao de Credito Stripe", Decimal("200.00"), "month", 1, False, True, "Price mensal legado do catalogo Stripe."),
    ("mensal-recorrente-stripe", "prod_ReEqIm7GpANsQh", "price_1QkwMRHDywrdzSUoMCesWAva", "Mensal Cartao de Credito TON", Decimal("200.00"), "month", 1, False, True, "Canal alternativo legado de cobranca mensal."),
    ("mensal-bolsista", "prod_Qkhqv2fByxKCpn", "price_1PtCQQHDywrdzSUoB06eY5y2", "Mensal Bolsista", Decimal("210.00"), "month", 1, True, False, "Price de bolsista identificado na documentacao Stripe."),
    ("trimestral-recorrente-stripe", "prod_QY1BH9LekrV0f6", "price_1Po3mMHDywrdzSUoaUQmAuaI", "Trimestral Cartao de Credito Stripe", Decimal("400.00"), "month", 3, True, False, "Price trimestral atual."),
    ("trimestral-recorrente-stripe", "prod_QY1BH9LekrV0f6", "price_1Pgv93HDywrdzSUoHEJfvaNK", "Trimestral Cartao de Credito Stripe", Decimal("390.00"), "month", 3, False, True, "Price trimestral legado."),
    ("semestral-recorrente-stripe", "prod_QY1B0KTL0NyIEM", "price_1Po3nnHDywrdzSUoRs6EwAsn", "Semestral Cartao de Credito Stripe", Decimal("800.00"), "month", 6, True, False, "Price semestral atual."),
    ("semestral-recorrente-stripe", "prod_QY1B0KTL0NyIEM", "price_1Pgv9VHDywrdzSUonYZXbUvX", "Semestral Cartao de Credito Stripe", Decimal("720.00"), "month", 6, False, True, "Price semestral legado."),
    ("anual-recorrente-stripe", "prod_QfOdqBEJiw9315", "price_1Po3pnHDywrdzSUoysx5gH1k", "Anual Cartao de Credito Stripe", Decimal("1200.00"), "month", 12, True, False, "Price anual atual."),
    ("anual-credito-mensal-recorrente", "prod_Qroq1y9hdNsweV", "price_1Q05CxHDywrdzSUooVZhunKH", "Anual Credito Mensal Recorrente", Decimal("135.00"), "month", 1, True, False, "Plano anual parcelado em ciclos mensais."),
)

PDV_PRODUCTS = (
    ("FAIXA-LV", "Faixa LV", "Faixa oficial divulgada na loja publica.", Decimal("75.00"), 1),
    ("KIT-PATCH-LV", "Kit 3 Patch's Kimono", "Kit de patches oficial da loja publica.", Decimal("45.00"), 2),
    ("RASH-GUARD-LV", "Rash Guard LV", "Rash guard oficial da loja publica.", Decimal("150.00"), 3),
    ("KIMONO-PREMIUM-COMP-LV", "Kimono Premium Competition LV", "Kimono premium competition oficial.", Decimal("520.00"), 4),
    ("KIMONO-TRANCADO-BRANCO", "Kimono Tradicional Trancado LV Branco", "Kimono tradicional branco da loja publica.", Decimal("480.00"), 5),
    ("KIMONO-TRANCADO-BRANCO-FEM", "Kimono Tradicional Trancado LV Branco Feminino", "Kimono tradicional branco feminino.", Decimal("480.00"), 6),
    ("KIMONO-TRANCADO-PRETO-FEM", "Kimono Tradicional Trancado LV Preto Feminino", "Kimono tradicional preto feminino.", Decimal("480.00"), 7),
    ("KIMONO-COMP-PRETO-VERM", "Kimono Trancado Competition LV Preto Com Vermelho", "Kimono competition preto com vermelho.", Decimal("480.00"), 8),
    ("KIMONO-COMP-PRETO-VERM-FEM", "Kimono Trancado Competition LV Preto Com Vermelho Feminino", "Kimono competition feminino preto com vermelho.", Decimal("480.00"), 9),
    ("KIMONO-COMP-PRETO-VERM-INF", "Kimono Trancado Competition LV Preto Com Vermelho Infantil", "Kimono competition infantil preto com vermelho.", Decimal("450.00"), 10),
)

CONSENT_TERMS = (
    (
        "service_agreement",
        "Termo de matricula, convivencia e pedidos",
        2,
        "Ao realizar matricula ou pedido, o usuario declara que os dados fornecidos sao completos, que esta apto a celebrar contratos e que leu as regras de pedido, cancelamento em ate 14 dias, retirada na loja e devolucao de produtos nao usados divulgadas pela LV Jiu Jitsu.",
    ),
    (
        "privacy_policy",
        "Termo de privacidade e tratamento de dados",
        2,
        "A LV Jiu Jitsu trata dados de cadastro, pedido, pagamento, dispositivo e navegacao para atender compras, prevenir fraude, operar a loja online, prestar servicos e cumprir obrigacoes legais, conforme a politica publica de privacidade divulgada no site oficial.",
    ),
)

NOTICE_BOARD_SEED = {
    "title": "Base inicial sincronizada com a vitrine publica",
    "body": (
        "Horarios, planos publicos, produtos de recepcao e mapeamentos Stripe foram preparados a partir das paginas "
        "publicas da academia em 02/04/2026. Revise apenas o que for realmente operacional antes do go-live."
    ),
}


def run_initial_seed_pipeline(*, stdout):
    steps = (
        ("configuracao publica", _seed_academy_configuration),
        ("disciplinas", _seed_disciplines),
        ("planos publicos", _seed_public_plans),
        ("horarios publicos", _seed_public_class_schedules),
        ("planos financeiros", _seed_financial_plans),
        ("mapeamentos Stripe", _seed_stripe_price_maps),
        ("catalogo PDV", _seed_pdv_products),
        ("termos LGPD", _seed_consent_terms),
        ("mural inicial", _seed_notice_board),
        ("controle de exportacao", _ensure_export_control_ready),
    )
    for label, function in steps:
        stdout.write(f"Executando seed: {label}...")
        stdout.write(f"  -> {function()}")
    return "Seeds iniciais concluidas com sucesso."


def _seed_academy_configuration():
    configuration = AcademyConfiguration.objects.get(singleton_key="default")
    for field_name, value in ACADEMY_CONFIGURATION_DATA.items():
        setattr(configuration, field_name, value)
    configuration.save()
    return "Configuracao da academia atualizada com base no site publico."


def _seed_disciplines():
    created_count = 0
    for name, slug, description in DISCIPLINES:
        _, created = ClassDiscipline.objects.update_or_create(
            slug=slug,
            defaults={"name": name, "description": description, "is_active": True},
        )
        created_count += int(created)
    return f"{len(DISCIPLINES)} disciplinas sincronizadas ({created_count} novas)."


def _seed_public_plans():
    created_count = 0
    for payload in PUBLIC_PLANS:
        _, created = PublicPlan.objects.update_or_create(
            name=payload["name"],
            billing_cycle=payload["billing_cycle"],
            defaults={
                "summary": payload["summary"],
                "amount": payload["amount"],
                "cta_label": payload["cta_label"],
                "is_active": True,
                "is_featured": payload.get("is_featured", False),
                "display_order": payload["display_order"],
            },
        )
        created_count += int(created)
    return f"{len(PUBLIC_PLANS)} planos publicos sincronizados ({created_count} novos)."


def _seed_public_class_schedules():
    created_count = 0
    for class_level, weekday, start_time, end_time, instructor_name, display_order in PUBLIC_CLASS_SCHEDULES:
        _, created = PublicClassSchedule.objects.update_or_create(
            class_level=class_level,
            weekday=weekday,
            start_time=start_time,
            defaults={
                "end_time": end_time,
                "instructor_name": instructor_name,
                "is_active": True,
                "display_order": display_order,
            },
        )
        created_count += int(created)
    return f"{len(PUBLIC_CLASS_SCHEDULES)} horarios publicos sincronizados ({created_count} novos)."


def _seed_financial_plans():
    created_count = 0
    for name, slug, billing_cycle, base_price, description in FINANCIAL_PLANS:
        _, created = FinancialPlan.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "billing_cycle": billing_cycle,
                "base_price": base_price,
                "description": description,
                "allows_pause": True,
                "blocks_checkin_on_overdue": True,
                "is_active": True,
            },
        )
        created_count += int(created)
    return f"{len(FINANCIAL_PLANS)} planos financeiros sincronizados ({created_count} novos)."


def _seed_stripe_price_maps():
    created_count = 0
    plan_by_slug = {
        plan.slug: plan
        for plan in FinancialPlan.objects.filter(slug__in=[item[0] for item in STRIPE_PRICE_MAPS])
    }
    for plan_slug, product_id, price_id, product_name, amount, interval, interval_count, is_current, is_legacy, notes in STRIPE_PRICE_MAPS:
        price_map, created = StripePlanPriceMap.objects.update_or_create(
            stripe_price_id=price_id,
            defaults={
                "plan": plan_by_slug[plan_slug],
                "stripe_product_id": product_id,
                "product_name": product_name,
                "lookup_key": "",
                "currency": "brl",
                "amount": amount,
                "recurring_interval": interval,
                "recurring_interval_count": interval_count,
                "livemode": False,
                "is_active": True,
                "is_current": is_current,
                "is_legacy": is_legacy,
                "supports_pause_collection": True,
                "notes": notes,
            },
        )
        if is_current:
            StripePlanPriceMap.objects.filter(plan=plan_by_slug[plan_slug]).exclude(pk=price_map.pk).update(is_current=False)
        created_count += int(created)
    return f"{len(STRIPE_PRICE_MAPS)} mapeamentos Stripe sincronizados ({created_count} novos)."


def _seed_pdv_products():
    created_count = 0
    for sku, name, description, unit_price, display_order in PDV_PRODUCTS:
        _, created = PdvProduct.objects.update_or_create(
            sku=sku,
            defaults={
                "name": name,
                "description": description,
                "unit_price": unit_price,
                "display_order": display_order,
                "is_active": True,
            },
        )
        created_count += int(created)
    return f"{len(PDV_PRODUCTS)} produtos PDV sincronizados ({created_count} novos)."


def _seed_consent_terms():
    updated_codes = []
    for code, title, version, content in CONSENT_TERMS:
        ConsentTerm.objects.filter(code=code).exclude(version=version).update(is_active=False)
        ConsentTerm.objects.update_or_create(
            code=code,
            version=version,
            defaults={
                "title": title,
                "content": content,
                "audience": ConsentTerm.AUDIENCE_ALL,
                "required_for_onboarding": True,
                "is_active": True,
                "published_at": timezone.now(),
            },
        )
        updated_codes.append(code)
    return f"Termos atualizados: {', '.join(updated_codes)}."


def _seed_notice_board():
    admin_user = SystemUser.objects.filter(is_superuser=True).order_by("created_at").first()
    NoticeBoardMessage.objects.update_or_create(
        title=NOTICE_BOARD_SEED["title"],
        defaults={
            "body": NOTICE_BOARD_SEED["body"],
            "audience": AUDIENCE_ALL_USERS,
            "created_by": admin_user,
            "is_active": True,
        },
    )
    return "Mensagem inicial do mural preparada."


def _ensure_export_control_ready():
    control_file = Path(settings.CRITICAL_EXPORT_CONTROL_FILE)
    control_file.parent.mkdir(parents=True, exist_ok=True)
    control_file.write_text("EXPORT_ALLOWED=1\n", encoding="utf-8")
    CsvExportControl.objects.update_or_create(
        name="critical_csv_exports",
        defaults={
            "control_file_path": str(control_file),
            "is_active": True,
        },
    )
    return "Arquivo de controle de exportacao criado com EXPORT_ALLOWED=1."
