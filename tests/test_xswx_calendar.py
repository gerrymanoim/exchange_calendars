import pytest

from exchange_calendars.exchange_calendar_xswx import XSWXExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestIXSWXCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XSWXExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XSWX is open from 9:00 am to 5:30 pm.
        yield 8.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2012
            # New Year's Day isn't observed because it was on a Sunday
            "2012-01-02",  # Berchtold's Day observed
            "2012-04-06",  # Good Friday
            "2012-04-09",  # Easter Monday
            "2012-05-01",  # Labour Day
            "2012-05-17",  # Ascension Day
            "2012-05-28",  # Whit Monday
            "2012-08-01",  # Swiss National Day
            "2012-12-24",  # Christmas Eve
            "2012-12-25",  # Christmas
            "2012-12-26",  # Boxing Day
            "2012-12-31",  # New Year's Eve
        ]
