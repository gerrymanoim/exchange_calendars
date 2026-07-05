import pytest
from exchange_calendars.exchange_calendar_xzag import XZAGExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXZAGCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XZAGExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XZAG is open from 9:00 am to 4:00 pm.
        yield 7.0

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2025-01-01",  # New Year's Day
            "2025-01-06",  # Epiphany
            "2025-04-18",  # Good Friday
            "2025-04-21",  # Easter Monday
            "2025-05-01",  # Labour Day
            "2025-05-30",  # Statehood Day
            "2025-06-19",  # Corpus Christi
            "2025-08-05",  # Victory and Homeland Thanksgiving Day
            "2025-08-15",  # Assumption of Mary
            "2025-11-01",  # All Saints' Day
            "2025-12-25",  # Christmas Day
            "2025-12-26",  # St. Stephen's Day
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2025-01-02",
            "2025-01-07",
            "2025-04-17",
            "2025-05-02",
            "2025-06-18",
            "2025-08-06",
            "2025-08-14",
            "2025-11-03",
            "2025-12-30",
        ]
