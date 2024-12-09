"""This exte"""
import logging
import contextlib
from logging import Logger
from urllib.parse import urlparse
from typing import Any, Iterator, Protocol, Callable

import MySQLdb as mdb
from MySQLdb.cursors import Cursor


_logger = logging.getLogger(__file__)

class InvalidOptionValue(Exception):
    """Raised whenever a parsed value is invalid for the specific option."""


def __parse_boolean__(val: str) -> bool:
    """Check whether the variable 'val' has the string value `true`."""
    true_vals = ("t", "T", "true", "TRUE", "True")
    false_vals = ("f", "F", "false", "FALSE", "False")
    if (val.strip() not in (true_vals + false_vals)):
        raise InvalidOptionValue(f"Invalid value: {val}")
    return val.strip().lower() in true_vals


def __parse_db_opts__(opts: str) -> dict:
    """Parse database options into their appropriate values.

    This assumes use of python-mysqlclient library."""
    allowed_opts = (
        "unix_socket", "connect_timeout", "compress", "named_pipe",
        "init_command", "read_default_file", "read_default_group",
        "cursorclass", "use_unicode", "charset", "collation", "auth_plugin",
        "sql_mode", "client_flag", "multi_statements", "ssl_mode", "ssl",
        "local_infile", "autocommit", "binary_prefix")
    conversion_fns: dict[str, Callable] = {
        **{opt: str for opt in allowed_opts},
        "connect_timeout": int,
        "compress": __parse_boolean__,
        "use_unicode": __parse_boolean__,
        # "cursorclass": __load_cursor_class__
        "client_flag": int,
        # "ssl": __parse_ssl_options__,
        "multi_statements": __parse_boolean__,
        "local_infile": __parse_boolean__,
        "autocommit": __parse_boolean__,
        "binary_prefix": __parse_boolean__
    }
    queries = tuple(filter(bool, opts.split("&")))
    if len(queries) > 0:
        keyvals: tuple[tuple[str, ...], ...] = tuple(
            tuple(item.strip() for item in query.split("="))
            for query in queries)
        def __check_opt__(opt):
            assert opt in allowed_opts, (
                f"Invalid database connection option ({opt}) provided.")
            return opt
        return {
            __check_opt__(key): conversion_fns[key](val)
            for key, val in keyvals
        }
    return {}


def parse_db_url(sql_uri: str) -> dict:
    """Parse the `sql_uri` variable into a dict of connection parameters."""
    parsed_db = urlparse(sql_uri)
    return {
        "host": parsed_db.hostname,
        "port": parsed_db.port or 3306,
        "user": parsed_db.username,
        "password": parsed_db.password,
        "database": parsed_db.path.strip("/").strip(),
        **__parse_db_opts__(parsed_db.query)
    }


class Connection(Protocol):
    """Type Annotation for MySQLdb's connection object"""

    def commit(self):
        """Finish a transaction and commit the changes."""

    def rollback(self):
        """Cancel the current transaction and roll back the changes."""

    def cursor(self, *args, **kwargs) -> Any:
        """A cursor in which queries may be performed"""

@contextlib.contextmanager
def database_connection(sql_uri: str, logger: logging.Logger = _logger) -> Iterator[Connection]:
    """Connect to MySQL database."""
    connection = mdb.connect(**parse_db_url(sql_uri))
    try:
        yield connection
        connection.commit()
    except mdb.Error as _mbde:
        logger.error("DB error encountered", exc_info=True)
        connection.rollback()
    finally:
        connection.close()


def debug_query(cursor: Cursor, logger: Logger) -> None:
    """Debug the actual query run with MySQLdb"""
    for attr in ("_executed", "statement", "_last_executed"):
        if hasattr(cursor, attr):
            logger.debug("MySQLdb QUERY: %s", getattr(cursor, attr))
            break
