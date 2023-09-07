import itertools

import pandas as pd

from exchange_calendars import get_calendar
from exchange_calendars.calendar_helpers import UTC
from exchange_calendars.calendar_utils import (
    ExchangeCalendarDispatcher,
    _default_calendar_aliases,
    _default_calendar_factories,
)


def construct_all_calendars():
    dispatcher = ExchangeCalendarDispatcher(
        calendars={},
        calendar_factories=_default_calendar_factories,
        aliases=_default_calendar_aliases,
    )

    calendar_names = itertools.chain(
        _default_calendar_aliases, _default_calendar_factories
    )

    for name in calendar_names:
        assert dispatcher.get_calendar(name) is not None
        dispatcher.deregister_calendar(name)


def is_open_on_minute_bench(cal, timestamps):
    for timestamp in timestamps:
        cal.is_open_on_minute(timestamp, _parse=False)


def test_calendar_construction(benchmark):
    benchmark(construct_all_calendars)


def test_is_open_on_minute(benchmark):
    xhkg = get_calendar("XHKG")
    timestamps = [
        pd.Timestamp("2019-10-11 01:20:00", tz=UTC),  # pre open
        pd.Timestamp("2019-10-11 01:30:00", tz=UTC),  # open
        pd.Timestamp("2019-10-11 01:31:00", tz=UTC),  # first minute
        pd.Timestamp("2019-10-11 04:31:00", tz=UTC),  # in break
        pd.Timestamp("2019-10-11 08:00:00", tz=UTC),  # close
        pd.Timestamp("2019-10-11 08:01:00", tz=UTC),  # post close
    ]
    benchmark(is_open_on_minute_bench, xhkg, timestamps)
