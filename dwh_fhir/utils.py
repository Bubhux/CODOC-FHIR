import datetime
import os
from typing import Any, Optional

from dateutil import parser
from django.core.exceptions import ImproperlyConfigured


def boolenv(var_name: str, default: Any) -> bool:
    """Allow multiple value to be treated as falsy."""
    return os.getenv(var_name, default) not in {"0", "", "False", "false", False, 0}


def dateenv(var_name: str, default: Any) -> Optional[datetime.date]:
    """Convert a ISO 8601 date string into a `datetime.date` object.

    If the environment variable is not defined, treat `default` as such:
    * If `default` is `None`, return `None`.
    * If `default` is a `datetime.datetime` object, return its date part.
    * If `default` is a `datetime.date` object, return it as it is.
    """
    value = os.getenv(var_name, default)

    if value is None:
        return None

    if isinstance(value, datetime.date):
        return value

    if isinstance(value, datetime.datetime):
        return value.date()

    try:
        return parser.isoparse(value)
    except ValueError:
        raise ImproperlyConfigured(f"Invalid ISO 8601 date: '{value}'")


def intenv(var_name: str, default: Any) -> Optional[int]:
    """Ensure the environment variable value is a valid integer.

    Return `None` if the environment variable is not defined and `default` is
    `None`.
    """
    value = os.getenv(var_name, default)

    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        raise ImproperlyConfigured(f"Invalid integer: '{value}'")
