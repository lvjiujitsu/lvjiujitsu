from system.constants import ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_PROFESSOR, ROLE_RECEPCAO
from system.selectors.public_selectors import get_active_academy_configuration


KANRI_PARTNER_CODE = "DMZDUJYE"
KANRI_PARTNER_URL = "https://kanri-app.com.br/subscrible_partners?code=DMZDUJYE"
PUBLIC_STORE_URL = "https://lvjiujitsu.sumupstore.com/"
PUBLIC_TERMS_URL = "https://lvjiujitsu.sumupstore.com/pagina/termos-e-condicoes"
PUBLIC_PRIVACY_URL = "https://lvjiujitsu.sumupstore.com/pagina/politica-de-privacidade"
PUBLIC_COOKIES_URL = "https://lvjiujitsu.sumupstore.com/politica-de-cookies"
PUBLIC_CONTACT_URL = "https://lvjiujitsu.sumupstore.com/contato"


def system_layout(request):
    configuration = get_active_academy_configuration()
    return {
        "academy_configuration": configuration,
        "brand_store_url": PUBLIC_STORE_URL,
        "brand_terms_url": PUBLIC_TERMS_URL,
        "brand_privacy_url": PUBLIC_PRIVACY_URL,
        "brand_cookies_url": PUBLIC_COOKIES_URL,
        "brand_contact_url": PUBLIC_CONTACT_URL,
        "brand_kanri_partner_code": KANRI_PARTNER_CODE,
        "brand_kanri_partner_url": KANRI_PARTNER_URL,
        "portal_navigation_sections": _build_portal_navigation_sections(request),
    }


def _build_portal_navigation_sections(request):
    if not getattr(request, "user", None) or not request.user.is_authenticated:
        return ()
    resolver_match = getattr(request, "resolver_match", None)
    current_name = resolver_match.url_name if resolver_match else ""
    sections = [
        {
            "title": "Minha jornada",
            "items": [
                _build_nav_item("Resumo", "system:portal-dashboard", current_name, {"portal-dashboard"}),
                _build_nav_item("Meu perfil", "system:my-profile", current_name, {"my-profile"}),
                _build_nav_item("Avisos", "system:notice-board", current_name, {"notice-board"}),
                _build_nav_item("Comunicacoes", "system:communication-center", current_name, {"communication-center"}),
                _build_nav_item("Financeiro familiar", "system:my-invoices", current_name, {"my-invoices"}),
            ],
        }
    ]
    if request.user.has_any_role(ROLE_PROFESSOR, ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO):
        sections.append(
            {
                "title": "Tatame",
                "items": [
                    _build_nav_item("Dashboard do professor", "system:professor-dashboard", current_name, {"professor-dashboard"}),
                    _build_nav_item("Graduacao", "system:graduation-panel", current_name, {"graduation-panel"}),
                ],
            }
        )
    if request.user.has_any_role(ROLE_ADMIN_MASTER, ROLE_ADMIN_UNIDADE, ROLE_RECEPCAO):
        sections.append(
            {
                "title": "Operacao",
                "items": [
                    _build_nav_item("Dashboard admin", "system:admin-dashboard", current_name, {"admin-dashboard"}),
                    _build_nav_item("Alunos", "system:student-list", current_name, {"student-list", "student-update"}),
                    _build_nav_item("Professores", "system:instructor-list", current_name, {"instructor-list", "instructor-update"}),
                    _build_nav_item("Modalidades", "system:discipline-list", current_name, {"discipline-list", "discipline-update"}),
                    _build_nav_item("Turmas", "system:class-group-list", current_name, {"class-group-list", "class-group-update"}),
                    _build_nav_item("Sessoes", "system:session-list", current_name, {"session-list"}),
                ],
            }
        )
        sections.append(
            {
                "title": "Financeiro",
                "items": [
                    _build_nav_item("Financeiro local", "system:finance-dashboard", current_name, {"finance-dashboard"}),
                    _build_nav_item("Pagamentos Stripe", "system:payment-dashboard", current_name, {"payment-dashboard"}),
                    _build_nav_item("PDV e caixa", "system:pdv-dashboard", current_name, {"pdv-dashboard", "cash-closure"}),
                    _build_nav_item("Relatorios", "system:report-center", current_name, {"report-center"}),
                    _build_nav_item("LGPD", "system:lgpd-request-list", current_name, {"lgpd-request-list", "lgpd-request-process"}),
                    _build_nav_item("Emergencia", "system:emergency-quick-access", current_name, {"emergency-quick-access"}),
                ],
            }
        )
    return tuple(section for section in sections if section["items"])


def _build_nav_item(label, url_name, current_name, active_names):
    return {
        "label": label,
        "url_name": url_name,
        "is_active": current_name in active_names,
    }
