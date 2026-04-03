#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    base_dir = Path(__file__).resolve().parent
    expected_python = base_dir / ".venv" / "Scripts" / "python.exe"
    if expected_python.exists() and Path(sys.executable).resolve() != expected_python.resolve():
        raise RuntimeError(
            "Use exclusivamente a virtualenv do projeto: .\\.venv\\Scripts\\python.exe manage.py <comando>"
        )
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lvjiujitsu.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
