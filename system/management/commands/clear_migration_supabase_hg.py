from ._supabase_public_schema_reset import SupabasePublicSchemaResetCommand


class Command(SupabasePublicSchemaResetCommand):
    help = "Remove objetos relacionais do schema public no Supabase de homologacao."
    target_environment = "hg"
    confirmation_value = "RESET_HG"
