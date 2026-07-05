import pytest
from exchange_calendars.exchange_calendar_xbra import XBRAExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXBRAExchangeCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XBRAExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XBRA is open from 11:00 am to 3:30 pm.
        yield 4.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2025-01-01",  # New Year's Day
            "2025-01-06",  # Epiphany
            "2025-04-18",  # Good Friday
            "2025-04-21",  # Easter Monday
            "2025-05-01",  # Labour Day
            "2025-05-08",  # Victory Day
            "2025-07-05",  # Saints Cyril and Methodius Day
            "2025-08-29",  # Slovak National Uprising Anniversary
            "2025-09-15",  # Day of Our Lady of Sorrows
            "2025-11-01",  # All Saints' Day
            "2025-11-17",  # Struggle for Freedom and Democracy Day
            "2025-12-24",  # Christmas Eve
            "2025-12-25",  # Christmas Day
            "2025-12-26",  # Boxing Day
            "2025-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2025-01-02",
            "2025-01-07",
            "2025-04-17",
            "2025-04-22",
            "2025-05-02",
            "2025-05-09",
            "2025-08-28",
            "2025-09-02",
            "2025-09-16",
            "2025-11-18",
            "2025-12-23",
        ]
