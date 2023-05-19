import pytest

from exchange_calendars.exchange_calendar_xsau import XSAUExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class TestXASUCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XSAUExchangeCalendar

    @pytest.fixture
    def start_bound(self):
        yield T("2021-01-01")

    @pytest.fixture
    def end_bound(self):
        yield T("2023-12-31")

    @pytest.fixture
    def max_session_hours(self):
        yield 5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield ["2023-02-22", "2023-09-23"]
