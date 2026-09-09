from ._supabase_public_schema_reset import SupabasePublicSchemaResetCommand


class Command(SupabasePublicSchemaResetCommand):
    help = (
        "Reset destrutivo do schema public no Supabase de homologação. "
        "Exige DJANGO_ENV_FILE=.env.hg, SUPABASE_RESET_CONFIRM=RESET_HG e --execute."
    )
    target_environment = "hg"
    confirmation_value = "RESET_HG"
