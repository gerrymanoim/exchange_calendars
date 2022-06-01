import pytest
import pandas as pd
import pandas.testing as tm
from pytz import UTC

from exchange_calendars.weekday_calendar import WeekdayCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestWeekdayCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class", params=["left", "right"])
    def all_calendars_with_answers(self, request, calendars, answers):
        yield (calendars[request.param], answers[request.param])

    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield WeekdayCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 24

    # Calendar-specific tests

    def test_open_every_weekday(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        dates = pd.date_range(*ans.sessions_range, freq="B")
        tm.assert_index_equal(cal.sessions, dates)

    def test_open_every_weekday_minute(self, calendars, answers, one_minute):
        cal, ans = calendars["left"], answers["left"]
        minutes = pd.date_range(*ans.trading_minutes_range, freq="min", tz=UTC)
        # The pandas weekday is defined as Monday=0 to Sunday=6.
        minutes = minutes[minutes.weekday <= 4]
        tm.assert_index_equal(cal.minutes, minutes)

        cal = calendars["right"]
        minutes += one_minute
        tm.assert_index_equal(cal.minutes, minutes)
