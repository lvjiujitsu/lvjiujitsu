import os
from dataclasses import dataclass
from pathlib import Path

import dj_database_url
from decouple import Config, RepositoryEmpty, RepositoryEnv
from django.core.exceptions import ImproperlyConfigured

ENVIRONMENT_VARIABLE = "DJANGO_ENVIRONMENT"
ENV_FILE_VARIABLE = "DJANGO_ENV_FILE"


@dataclass(frozen=True)
class EnvironmentContract:
    base_dir: Path
    shared_dir_variable: str
    default_shared_dir: str


def shared_env_dir(contract):
    configured = os.environ.get(contract.shared_dir_variable, "").strip()
    return Path(configured or contract.default_shared_dir)


def env_file_candidates(contract):
    configured = os.environ.get(ENV_FILE_VARIABLE, "").strip()
    if not configured:
        return [shared_env_dir(contract) / ".env", contract.base_dir / ".env"]
    path = Path(configured)
    if path.is_absolute():
        return [path]
    return [shared_env_dir(contract) / path, contract.base_dir / path]


def locate_env_file(contract, name):
    for candidate in (shared_env_dir(contract) / name, contract.base_dir / name):
        if candidate.is_file():
            return candidate
    return None


def load_config(contract):
    candidates = env_file_candidates(contract)
    for candidate in candidates:
        if candidate.is_file():
            return Config(RepositoryEnv(str(candidate)))
    if os.environ.get(ENVIRONMENT_VARIABLE, "").strip():
        return Config(RepositoryEmpty())
    looked = "; ".join(str(candidate) for candidate in candidates)
    raise ImproperlyConfigured(
        f"Nenhuma configuração encontrada. Sem {ENVIRONMENT_VARIABLE} no "
        "ambiente do processo, é obrigatório haver arquivo. Procurado em: "
        f"{looked}. Defina {ENV_FILE_VARIABLE}, restaure o arquivo no "
        "repositório, confira se o diretório compartilhado está montado "
        f"({contract.shared_dir_variable} troca o caminho) ou cadastre as "
        "variáveis no painel da plataforma."
    )


def base_dir_path_setting(contract, config, name, default):
    configured_path = Path(config(name, default=str(default)))
    if configured_path.is_absolute():
        return configured_path
    return contract.base_dir / configured_path


def env_value_strip_outer_quotes(config, name, default=""):
    raw = config(name, default=default).strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "'\"":
        return raw[1:-1].strip()
    return raw


def parse_db_url(config, url):
    parsed = dj_database_url.parse(
        url, conn_max_age=config("DB_CONN_MAX_AGE", default=0, cast=int)
    )
    if not parsed.get("OPTIONS"):
        parsed["OPTIONS"] = {}
    parsed["DISABLE_SERVER_SIDE_CURSORS"] = True
    parsed["CONN_HEALTH_CHECKS"] = True
    return parsed
