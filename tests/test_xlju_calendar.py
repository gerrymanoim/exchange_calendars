import pytest
from exchange_calendars.exchange_calendar_xlju import XLJUExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXLJUCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XLJUExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XLJU is open from 9:15 am to 3:15 pm.
        yield 6.0

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2025-01-01",  # New Year's Day
            "2025-01-02",  # New Year Holiday
            "2025-02-08",  # Prešeren Day
            "2025-04-18",  # Good Friday
            "2025-04-21",  # Easter Monday
            "2025-04-27",  # Resistance Day
            "2025-05-01",  # Labour Day
            "2025-05-02",  # Labour Day (Second Day)
            "2025-06-25",  # Statehood Day
            "2025-08-15",  # Assumption Day
            "2025-10-31",  # Reformation Day
            "2025-11-01",  # All Saints' Day
            "2025-12-24",  # Christmas Day
            "2025-12-25",  # Christmas Day
            "2025-12-26",  # Independence and Unity Day
            "2025-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2025-01-03",
            "2025-04-22",
            "2025-06-26",
            "2025-08-14",
            "2025-12-30",
        ]
