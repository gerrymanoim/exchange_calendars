import pytest

from exchange_calendars.exchange_calendar_xbom import XBOMExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class TestXBOMCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XBOMExchangeCalendar

    @pytest.fixture
    def start_bound(self):
        yield T("1997-01-01")

    @pytest.fixture
    def end_bound(self):
        yield T("2026-12-31")

    @pytest.fixture
    def max_session_hours(self):
        # BSE is open from 9:15 am to 3:30 pm
        yield 6.25

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # The Muharram holiday was moved from November 14, 2013 to
            # November 15, 2013.
            "2013-11-15",
            "2017-01-26",
            "2017-02-24",
            "2017-03-13",
            "2017-04-04",
            "2017-04-14",
            "2017-05-01",
            "2017-06-26",
            "2017-08-15",
            "2017-08-25",
            "2017-10-02",
            "2017-10-20",
            "2017-12-25",
            "2024-01-22",
            "2025-05-01",
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # The Muharram holiday was moved from November 14, 2013 to
            # November 15, 2013.
            "2013-11-14",
            # Special trading session on Saturday, February 28, 2015.
            "2015-02-28",
            # Special trading session on Saturday, February 1, 2020.
            "2020-02-01",
            # Special trading session on Saturday, January 20, 2024.
            "2024-01-20",
            # Special trading session on Saturday, February 1, 2025.
            "2025-02-01",
            # Special trading session on Sunday, February 1, 2026.
            "2026-02-01",
        ]
