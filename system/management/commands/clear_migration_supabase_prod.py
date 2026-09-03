from ._supabase_public_schema_reset import SupabasePublicSchemaResetCommand


class Command(SupabasePublicSchemaResetCommand):
    help = (
        "Reset destrutivo do schema public no Supabase de produção. "
        "Exige DJANGO_ENV_FILE=.env.prod, SUPABASE_RESET_CONFIRM=RESET_PROD, "
        "SUPABASE_PROJECT_REF preenchida, --confirm-ref com o mesmo ref e --execute."
    )
    target_environment = "prod"
    confirmation_value = "RESET_PROD"
    requires_confirmation_variable = True
    requires_project_ref = True
    requires_execute_flag = True
    requires_ref_argument = True
