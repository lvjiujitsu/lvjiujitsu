from ._supabase_public_schema_reset import SupabasePublicSchemaResetCommand


class Command(SupabasePublicSchemaResetCommand):
    help = (
        "Reset destrutivo do schema public no Supabase de produção. "
        "Exige DJANGO_ENV_FILE=.env.prod, SUPABASE_RESET_CONFIRM=RESET_PROD e --execute."
    )
    target_environment = "prod"
    confirmation_value = "RESET_PROD"