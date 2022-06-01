import pytest
import pandas as pd
import pandas.testing as tm
from pytz import UTC

from exchange_calendars.always_open import AlwaysOpenCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestAlwaysOpenCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class", params=["left", "right"])
    def all_calendars_with_answers(self, request, calendars, answers):
        yield (calendars[request.param], answers[request.param])

    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield AlwaysOpenCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 24

    # Calendar-specific tests

    def test_open_every_day(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        dates = pd.date_range(*ans.sessions_range)
        tm.assert_index_equal(cal.sessions, dates)

    def test_open_every_minute(self, calendars, answers, one_minute):
        cal, ans = calendars["left"], answers["left"]
        minutes = pd.date_range(*ans.trading_minutes_range, freq="min", tz=UTC)
        tm.assert_index_equal(cal.minutes, minutes)

        cal = calendars["right"]
        minutes += one_minute
        tm.assert_index_equal(cal.minutes, minutes)
