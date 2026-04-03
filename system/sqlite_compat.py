import sqlite3
from datetime import date, datetime

from django.utils.dateparse import parse_date, parse_datetime


_SQLITE_HANDLERS_REGISTERED = False


def register_sqlite_type_handlers():
    global _SQLITE_HANDLERS_REGISTERED
    if _SQLITE_HANDLERS_REGISTERED:
        return

    sqlite3.register_adapter(date, _adapt_date_iso)
    sqlite3.register_adapter(datetime, _adapt_datetime_iso)
    sqlite3.register_converter("date", _convert_date)
    sqlite3.register_converter("datetime", _convert_datetime)
    sqlite3.register_converter("timestamp", _convert_datetime)
    _SQLITE_HANDLERS_REGISTERED = True


def _adapt_date_iso(value):
    return value.isoformat()


def _adapt_datetime_iso(value):
    return value.isoformat(" ")


def _convert_date(value):
    return parse_date(value.decode())


def _convert_datetime(value):
    return parse_datetime(value.decode())
