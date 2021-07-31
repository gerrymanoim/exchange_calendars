from __future__ import annotations
from unittest import TestCase
from collections import abc

import pytest
import pandas as pd
import pandas.testing as tm
from pytz import UTC

from exchange_calendars.weekday_calendar import WeekdayCalendar
from exchange_calendars import ExchangeCalendar
from .test_exchange_calendar import (
    ExchangeCalendarTestBase,
    ExchangeCalendarTestBaseProposal,
    Answers,
)


@pytest.mark.skip
class WeekdayCalendarTestCase(ExchangeCalendarTestBase, TestCase):

    answer_key_filename = "24-5"
    calendar_class = WeekdayCalendar
    start_date = pd.Timestamp("2018-01-01", tz=UTC)
    end_date = pd.Timestamp("2018-12-31", tz=UTC)
    MAX_SESSION_HOURS = 24
    GAPS_BETWEEN_SESSIONS = False
    HAVE_EARLY_CLOSES = False
    SESSION_WITHOUT_BREAK = pd.Timestamp("2018-06-13", tz="UTC")

    MINUTE_INDEX_TO_SESSION_LABELS_START = pd.Timestamp("2018-01-01", tz=UTC)
    MINUTE_INDEX_TO_SESSION_LABELS_END = pd.Timestamp("2018-04-04", tz=UTC)

    DAYLIGHT_SAVINGS_DATES = ["2018-04-05", "2018-11-01"]

    def get_session_block(self):
        # This range is chosen specifically because it is "enclosed" by
        # adjacent days that are also sessions. This prevents any edge case
        # issues when looking at market opens or closes.
        return self.calendar.all_sessions[1:4]

    def test_open_every_weekday(self):
        calendar = self.calendar

        dates = pd.date_range(self.start_date, self.end_date, tz=UTC)
        tm.assert_index_equal(
            calendar.sessions_in_range(dates[0], dates[-1]),
            # The pandas weekday is defined as Monday=0 to Sunday=6.
            dates[dates.weekday <= 4],
        )

    def test_open_every_weekday_minute(self):
        calendar = self.calendar

        minutes = pd.date_range(
            self.start_date,
            # Our calendar should include all the minutes of this last session.
            self.end_date + pd.Timedelta("1 Day") - pd.Timedelta("1 Minute"),
            freq="min",
            tz=UTC,
        )
        tm.assert_index_equal(
            calendar.minutes_for_sessions_in_range(
                self.start_date,
                self.end_date,
            ),
            # The pandas weekday is defined as Monday=0 to Sunday=6.
            minutes[minutes.weekday <= 4],
        )


class TestWeekdayCalendarCase(ExchangeCalendarTestBaseProposal):
    @pytest.fixture(scope="class")
    def calendar_class(self) -> abc.Iterator[ExchangeCalendar]:
        yield WeekdayCalendar

    @pytest.fixture(scope="class", params=["left", "right"])
    def all_calendars_with_answers(
        self, request, calendars, answers
    ) -> abc.Iterator[ExchangeCalendar, Answers]:
        """Parameterized calendars and answers for each side."""
        yield (calendars[request.param], answers[request.param])
