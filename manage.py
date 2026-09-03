import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvjiujitsu.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Não foi possível importar o Django. Instale as dependências do projeto."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
