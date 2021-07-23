"""Tests for calendar_helpers module."""

from __future__ import annotations

from collections import abc
import re

import pandas as pd
import pytest

from exchange_calendars import (
    ExchangeCalendar,
    get_calendar,
    errors,
)
from exchange_calendars import calendar_helpers as m

# TODO tests for next_divider_idx, previous_divider_idx, compute_all_minutes (#15)


@pytest.fixture
def one_minute() -> abc.Iterator[pd.DateOffset]:
    yield pd.DateOffset(minutes=1)


@pytest.fixture
def one_day() -> abc.Iterator[pd.DateOffset]:
    yield pd.DateOffset(days=1)


# all fixtures with respect to XHKG
@pytest.fixture
def calendar() -> abc.Iterator[ExchangeCalendar]:
    yield get_calendar("XHKG")


@pytest.fixture
def param_name() -> abc.Iterator[str]:
    yield "parameter's_name"


@pytest.fixture(params=[True, False])
def utc(request) -> abc.Iterator[str]:
    yield request.param


@pytest.fixture(params=["2021-13-13", ("2021-06-06",), "not a timestamp"])
def malformed(request) -> abc.Iterator[str]:
    yield request.param


@pytest.fixture
def minute() -> abc.Iterator[str]:
    yield "2021-06-02 23:00"


@pytest.fixture(
    params=[
        "2021-06-02 23:00",
        pd.Timestamp("2021-06-02 23:00"),
        pd.Timestamp("2021-06-02 23:00", tz="UTC"),
    ]
)
def minute_mult(request) -> abc.Iterator[str | pd.Timestamp]:
    yield request.param


@pytest.fixture
def date(calendar) -> abc.Iterator[str]:
    """Date that does not represent a session of `calendar`."""
    date_ = "2021-06-05"
    assert pd.Timestamp(date_, tz="UTC") not in calendar.schedule.index
    yield date_


@pytest.fixture(
    params=[
        "2021-06-05",
        pd.Timestamp("2021-06-05"),
        pd.Timestamp("2021-06-05", tz="UTC"),
    ]
)
def date_mult(request, calendar) -> abc.Iterator[str | pd.Timestamp]:
    """Date that does not represent a session of `calendar`."""
    date_ = request.param
    try:
        ts_utc = pd.Timestamp(date_, tz="UTC")
    except ValueError:
        ts_utc = date_
    assert ts_utc not in calendar.schedule.index
    yield date_


@pytest.fixture
def session() -> abc.Iterator[str]:
    yield "2021-06-02"


@pytest.fixture
def minute_too_early(calendar, one_minute) -> abc.Iterator[pd.Timestamp]:
    yield calendar.first_trading_minute - one_minute


@pytest.fixture
def minute_too_late(calendar, one_minute) -> abc.Iterator[pd.Timestamp]:
    yield calendar.last_trading_minute + one_minute


@pytest.fixture
def date_too_early(calendar, one_day) -> abc.Iterator[pd.Timestamp]:
    yield calendar.first_session - one_day


@pytest.fixture
def date_too_late(calendar, one_day) -> abc.Iterator[pd.Timestamp]:
    yield calendar.last_session + one_day


def test_parse_timestamp_with_date(date_mult, param_name, utc):
    date = date_mult
    date_is_utc_ts = isinstance(date, pd.Timestamp) and date.tz is not None
    dt = m.parse_timestamp(date, param_name, utc)
    if not utc and not date_is_utc_ts:
        assert dt == pd.Timestamp("2021-06-05")
    else:
        assert dt == pd.Timestamp("2021-06-05", tz="UTC")
    assert dt == dt.floor("T")


def test_parse_timestamp_with_minute(minute_mult, param_name, utc):
    minute = minute_mult
    minute_is_utc_ts = isinstance(minute, pd.Timestamp) and minute.tz is not None
    dt = m.parse_timestamp(minute, param_name, utc)
    if not utc and not minute_is_utc_ts:
        assert dt == pd.Timestamp("2021-06-02 23:00")
    else:
        assert dt == pd.Timestamp("2021-06-02 23:00", tz="UTC")
    assert dt == dt.floor("T")


def test_parse_timestamp_error_malformed(malformed, param_name):
    expected_error = TypeError if isinstance(malformed, tuple) else ValueError
    error_msg = re.escape(
        f"Parameter `{param_name}` receieved as '{malformed}' although a Date or"
        f" Minute must be passed as a pd.Timestamp or a valid single-argument"
        f" input to pd.Timestamp."
    )
    with pytest.raises(expected_error, match=error_msg):
        m.parse_timestamp(malformed, param_name)


def test_parse_timestamp_error_oob(
    calendar, param_name, minute_too_early, minute_too_late
):
    # by default parses oob
    assert m.parse_timestamp(minute_too_early, param_name) == minute_too_early

    error_msg = re.escape(
        f"Parameter `{param_name}` receieved as '{minute_too_early}' although"
        f" cannot be earlier than the first trading minute of calendar"
    )
    with pytest.raises(errors.MinuteOutOfBounds, match=error_msg):
        m.parse_timestamp(
            minute_too_early, param_name, raise_oob=True, calendar=calendar
        )

    # by default parses oob
    assert m.parse_timestamp(minute_too_late, param_name) == minute_too_late

    error_msg = re.escape(
        f"Parameter `{param_name}` receieved as '{minute_too_late}' although"
        f" cannot be later than the last trading minute of calendar"
    )
    with pytest.raises(errors.MinuteOutOfBounds, match=error_msg):
        m.parse_timestamp(
            minute_too_late, param_name, raise_oob=True, calendar=calendar
        )


def test_parse_date(date_mult, param_name):
    date = date_mult
    dt = m.parse_date(date, param_name)
    assert dt == pd.Timestamp("2021-06-05", tz="UTC")


def test_parse_date_errors(calendar, param_name, date_too_early, date_too_late):
    dt = pd.Timestamp("2021-06-02", tz="US/Central")
    with pytest.raises(
        ValueError, match="a Date must be timezone naive or have timezone as 'UTC'"
    ):
        m.parse_date(dt, param_name)

    dt = pd.Timestamp("2021-06-02 13:33")
    with pytest.raises(ValueError, match="a Date must have a time component of 00:00."):
        m.parse_date(dt, param_name)

    # by default parses oob
    assert m.parse_date(date_too_early, param_name) == date_too_early

    error_msg = (
        f"Parameter `{param_name}` receieved as '{date_too_early}' although"
        f" cannot be earlier than the first session of calendar"
    )
    with pytest.raises(errors.DateOutOfBounds, match=re.escape(error_msg)):
        m.parse_date(date_too_early, param_name, raise_oob=True, calendar=calendar)

    # by default parses oob
    assert m.parse_date(date_too_late, param_name) == date_too_late

    error_msg = (
        f"Parameter `{param_name}` receieved as '{date_too_late}' although"
        f" cannot be later than the last session of calendar"
    )
    with pytest.raises(errors.DateOutOfBounds, match=re.escape(error_msg)):
        m.parse_date(date_too_late, param_name, raise_oob=True, calendar=calendar)


def test_parse_session(
    calendar, session, date, date_too_early, date_too_late, param_name
):
    ts = m.parse_session(calendar, session, param_name)
    assert ts == pd.Timestamp(session, tz="UTC")

    with pytest.raises(errors.NotSessionError, match="not a session of calendar"):
        m.parse_session(calendar, date, param_name)

    with pytest.raises(
        errors.NotSessionError, match="is earlier than the first session of calendar"
    ):
        m.parse_session(calendar, date_too_early, param_name)

    with pytest.raises(
        errors.NotSessionError, match="is later than the last session of calendar"
    ):
        m.parse_session(calendar, date_too_late, param_name)
