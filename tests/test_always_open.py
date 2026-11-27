import pytest
import pandas as pd

from exchange_calendars.always_open import AlwaysOpenCalendar
from exchange_calendars.calendar_helpers import UTC
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import assert_index_equal_compat


class TestAlwaysOpenCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class", params=["left", "right"])
    @classmethod
    def all_calendars_with_answers(cls, request, calendars, answers):
        yield (calendars[request.param], answers[request.param])

    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield AlwaysOpenCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 24

    # Calendar-specific tests

    def test_open_every_day(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        dates = pd.date_range(*ans.sessions_range)
        assert_index_equal_compat(cal.sessions, dates, check_freq=False)

    def test_open_every_minute(self, calendars, answers, one_minute):
        cal, ans = calendars["left"], answers["left"]
        minutes = pd.date_range(*ans.trading_minutes_range, freq="min", tz=UTC)
        assert_index_equal_compat(cal.minutes, minutes, check_freq=False)

        cal = calendars["right"]
        minutes += one_minute
        assert_index_equal_compat(cal.minutes, minutes, check_freq=False)
