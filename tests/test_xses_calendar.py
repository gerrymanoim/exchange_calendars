import pytest

from exchange_calendars.exchange_calendar_xses import XSESExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class TestXSESCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XSESExchangeCalendar

    @pytest.fixture
    def start_bound(self):
        yield T("1986-01-01")

    @pytest.fixture
    def end_bound(self):
        yield T("2023-12-31")

    @pytest.fixture
    def max_session_hours(self):
        # Singapore stock exchange is open from 9am to 5pm
        yield 8

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2017-01-02",
            "2017-01-30",
            "2017-04-14",
            "2017-05-01",
            "2017-05-10",
            "2017-06-26",
            "2017-08-09",
            "2017-09-01",
            "2017-10-18",
            "2017-12-25",
            "2023-12-25",
        ]
