import datetime as dt
from typing import Any, Union
import logging

logger = logging.getLogger(__name__)


def get_monday(date: Union[dt.date, dt.datetime]):
    if isinstance(date, dt.datetime):
        date = date.date()
    return date - dt.timedelta(days=date.weekday())
