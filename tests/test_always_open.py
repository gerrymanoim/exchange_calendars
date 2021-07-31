from __future__ import annotations
from unittest import TestCase
from collections import abc

import pytest
import pandas as pd
import pandas.testing as tm
from pytz import UTC

from exchange_calendars.always_open import AlwaysOpenCalendar
from exchange_calendars import ExchangeCalendar
from .test_exchange_calendar import (
    ExchangeCalendarTestBase,
    ExchangeCalendarTestBaseProposal,
    Answers,
)


@pytest.mark.skip
class AlwaysOpenTestCase(ExchangeCalendarTestBase, TestCase):

    answer_key_filename = "24-7"
    calendar_class = AlwaysOpenCalendar
    start_date = (pd.Timestamp("2016", tz=UTC),)
    end_date = (pd.Timestamp("2016-12-31", tz=UTC),)
    MAX_SESSION_HOURS = 24
    GAPS_BETWEEN_SESSIONS = False
    HAVE_EARLY_CLOSES = False
    SESSION_WITHOUT_BREAK = pd.Timestamp("2016-06-15", tz="UTC")

    MINUTE_INDEX_TO_SESSION_LABELS_START = pd.Timestamp("2016-01-01", tz=UTC)
    MINUTE_INDEX_TO_SESSION_LABELS_END = pd.Timestamp("2016-04-04", tz=UTC)

    DAYLIGHT_SAVINGS_DATES = ["2016-04-05", "2016-11-01"]

    def test_open_every_day(self):
        cal = self.calendar

        #    February 2016
        # Su Mo Tu We Th Fr Sa
        #     1  2  3  4  5  6
        #  7  8  9 10 11 12 13
        # 14 15 16 17 18 19 20
        # 21 22 23 24 25 26 27
        # 28 29
        dates = pd.date_range("2016-02-01", "2016-02-28", tz=UTC)
        cal_dates = cal.sessions_in_range(dates[0], dates[-1])
        tm.assert_index_equal(dates, cal_dates)

    def test_open_every_minute(self):
        cal = self.calendar
        minutes = pd.date_range("2016-02-01", "2016-02-28 23:59:00", freq="min", tz=UTC)
        cal_minutes = cal.minutes_for_sessions_in_range(
            pd.Timestamp("2016-02-01", tz=UTC),
            pd.Timestamp("2016-02-28", tz=UTC),
        )
        tm.assert_index_equal(minutes, cal_minutes)

    def test_start_end(self):

        start = pd.Timestamp("2010-1-3", tz=UTC)
        end = pd.Timestamp("2010-1-10", tz=UTC)
        calendar = self.calendar_class(start=start, end=end)

        self.assertTrue(calendar.first_trading_session == start)
        self.assertTrue(calendar.last_trading_session == end)


class TestAlwaysOpenCalendarCase(ExchangeCalendarTestBaseProposal):
    @pytest.fixture(scope="class")
    def calendar_class(self) -> abc.Iterator[ExchangeCalendar]:
        yield AlwaysOpenCalendar

    @pytest.fixture(scope="class", params=["left", "right"])
    def all_calendars_with_answers(
        self, request, calendars, answers
    ) -> abc.Iterator[ExchangeCalendar, Answers]:
        """Parameterized calendars and answers for each side."""
        yield (calendars[request.param], answers[request.param])
