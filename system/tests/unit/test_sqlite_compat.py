import sqlite3
import warnings
from datetime import date

from system.sqlite_compat import register_sqlite_type_handlers


def test_register_sqlite_type_handlers_avoids_default_date_converter_warning():
    register_sqlite_type_handlers()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        connection = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = connection.cursor()
        cursor.execute("create table sample (happens_on date)")
        cursor.execute("insert into sample (happens_on) values (?)", (date(2026, 4, 2),))
        resolved = cursor.execute("select happens_on from sample").fetchone()[0]
        connection.close()

    messages = [str(item.message) for item in caught]

    assert resolved == date(2026, 4, 2)
    assert all("default date converter is deprecated" not in message for message in messages)
