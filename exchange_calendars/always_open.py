from datetime import time

from .exchange_calendar import ExchangeCalendar
from exchange_calendars.calendar_helpers import UTC


class AlwaysOpenCalendar(ExchangeCalendar):
    """A ExchangeCalendar for an exchange that's open every minute of every day."""

    name = "24/7"
    tz = UTC
    weekmask = "1111111"
    open_times = ((None, time(0)),)
    close_times = ((None, time(0, 0)),)
    close_offset = 1
