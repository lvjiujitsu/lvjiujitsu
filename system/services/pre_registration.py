"""
Serviço de pré-cadastro.

Responsável por:
- Criar/atualizar PreRegistration a partir dos dados do wizard
- Restaurar o snapshot para re-popular o formulário
- Finalizar: migrar os dados para a tabela Person
"""

from system.models.pre_registration import PreRegistration, PreRegistrationStatus

# Campos sensíveis que não devem ser armazenados no snapshot
_EXCLUDED_SNAPSHOT_FIELDS = frozenset({
    "holder_password",
    "holder_password_confirm",
    "dependent_password",
    "dependent_password_confirm",
    "guardian_password",
    "guardian_password_confirm",
    "student_password",
    "student_password_confirm",
    "csrfmiddlewaretoken",
})


def build_form_snapshot(post_data: dict) -> dict:
    """
    Extrai do POST data apenas os campos relevantes do wizard,
    excluindo senhas e tokens CSRF.

    Args:
        post_data: QueryDict ou dict com os dados submetidos.

    Returns:
        dict seguro para armazenar no form_snapshot.
    """
    snapshot = {}
    for key, value in post_data.items():
        if key in _EXCLUDED_SNAPSHOT_FIELDS:
            continue
        # QueryDict pode ter listas (ex: class_groups MultipleChoiceField)
        if hasattr(post_data, "getlist"):
            values = post_data.getlist(key)
            snapshot[key] = values if len(values) > 1 else value
        else:
            snapshot[key] = value
    return snapshot


def get_pre_registration_for_session(session_key: str) -> "PreRegistration | None":
    """
    Retorna o PreRegistration ativo (não finalizado, não abandonado)
    para a sessão dada, ou None se não existir.
    """
    return (
        PreRegistration.objects.filter(
            session_key=session_key,
            status__in=(
                PreRegistrationStatus.DRAFT,
                PreRegistrationStatus.AWAITING_PAYMENT,
                PreRegistrationStatus.PAYMENT_CONFIRMED,
            ),
        )
        .select_related("selected_plan", "plan_order", "finalized_person")
        .order_by("-created_at")
        .first()
    )


def create_or_update_pre_registration(
    session_key: str,
    post_data: dict,
    selected_plan=None,
    checkout_action: str = "",
) -> "PreRegistration":
    """
    Cria ou atualiza o PreRegistration para a sessão dada com os dados do wizard.

    Sempre sobrescreve o snapshot com os dados mais recentes.
    Não inclui senhas no snapshot.

    Args:
        session_key: chave da sessão Django.
        post_data: dados brutos do POST (QueryDict ou dict).
        selected_plan: instância de SubscriptionPlan, ou None.
        checkout_action: 'asaas_card' | 'pix' | 'pay_later' | ''.

    Returns:
        A instância de PreRegistration criada ou atualizada.
    """
    snapshot = build_form_snapshot(post_data)

    registration_profile = snapshot.get("registration_profile", "")
    holder_cpf = snapshot.get("holder_cpf", "")
    holder_email = snapshot.get("holder_email", "")

    pre_reg = get_pre_registration_for_session(session_key)

    if pre_reg is None:
        pre_reg = PreRegistration(session_key=session_key)

    pre_reg.registration_profile = registration_profile
    pre_reg.holder_cpf = holder_cpf
    pre_reg.holder_email = holder_email
    pre_reg.form_snapshot = snapshot
    if selected_plan is not None:
        pre_reg.selected_plan = selected_plan
    if checkout_action:
        pre_reg.checkout_action = checkout_action

    pre_reg.save()
    return pre_reg


def restore_form_initial(pre_reg: "PreRegistration") -> dict:
    """
    Converte o form_snapshot de um PreRegistration de volta para um dict
    de initial values adequado para o PortalRegistrationForm.

    Senhas são excluídas — o usuário precisará digitá-las novamente.

    Returns:
        dict com os valores iniciais para passar ao Form como `initial=`.
    """
    if not pre_reg or not pre_reg.form_snapshot:
        return {}
    return {k: v for k, v in pre_reg.form_snapshot.items()}
