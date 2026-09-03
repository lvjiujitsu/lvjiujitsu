from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from lvjiujitsu.settings import (
    SHARED_ENV_DIR_VARIABLE,
    locate_env_file,
    shared_env_dir,
)

CONTRACT_FILE = ".env.example"
ENVIRONMENT_FILES = (".env", ".env.hg", ".env.prod")
TOLERATED_EMPTY = {
    ".env": {"DATABASE_URL", "SUPABASE_PROJECT_REF"},
}


def read_pairs(path):
    if path is None or not path.is_file():
        return None
    pairs = {}
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        pairs[key.strip()] = value.strip()
    return pairs


class Command(BaseCommand):
    help = (
        "Confere que cada arquivo de ambiente é encontrado e declara o mesmo "
        "conjunto de chaves do contrato. Nunca imprime valor."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--shared-dir",
            default="",
            help="Sobrescreve o diretório compartilhado desta execução.",
        )

    def locate(self, name, override):
        if override is None:
            return locate_env_file(name)
        for candidate in (Path(settings.BASE_DIR) / name, override / name):
            if candidate.is_file():
                return candidate
        return None

    def handle(self, *args, **options):
        contract = read_pairs(Path(settings.BASE_DIR) / CONTRACT_FILE)
        if contract is None:
            raise CommandError(f"Contrato ausente: {CONTRACT_FILE}.")

        override = Path(options["shared_dir"]) if options["shared_dir"] else None
        shared = override or shared_env_dir()
        self.stdout.write(f"Compartilhado: {shared}")
        if not shared.is_dir():
            self.stdout.write(
                self.style.WARNING(
                    "Diretório compartilhado inacessível; só valem os arquivos "
                    f"do repositório. {SHARED_ENV_DIR_VARIABLE} troca o caminho."
                )
            )

        problems = []
        for name in ENVIRONMENT_FILES:
            found = self.locate(name, override)
            self.stdout.write(f"== {name}")
            pairs = read_pairs(found)
            if pairs is None:
                problems.append(f"{name}: não encontrado")
                self.stdout.write(self.style.ERROR("   não encontrado"))
                continue

            origin = (
                "repositório"
                if Path(found).parent == Path(settings.BASE_DIR)
                else "compartilhado"
            )
            self.stdout.write(f"   origem: {origin}")

            missing = sorted(set(contract) - set(pairs))
            extra = sorted(set(pairs) - set(contract))
            tolerated = TOLERATED_EMPTY.get(name, set())
            empty = sorted(
                key for key, value in pairs.items() if not value and key not in tolerated
            )
            if missing:
                problems.append(f"{name}: faltam {', '.join(missing)}")
                self.stdout.write(self.style.ERROR("   faltam: " + ", ".join(missing)))
            if extra:
                problems.append(f"{name}: fora do contrato {', '.join(extra)}")
                self.stdout.write(
                    self.style.ERROR("   fora do contrato: " + ", ".join(extra))
                )
            if empty:
                self.stdout.write(self.style.WARNING("   sem valor: " + ", ".join(empty)))
            if not missing and not extra:
                self.stdout.write(self.style.SUCCESS("   contrato: completo"))

        if problems:
            raise CommandError("Ambiente divergente. " + " | ".join(problems))
        self.stdout.write(
            self.style.SUCCESS(
                "Ambiente conferido contra o contrato. Nenhum valor impresso."
            )
        )
