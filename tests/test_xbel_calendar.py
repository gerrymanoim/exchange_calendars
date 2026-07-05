import pytest
from exchange_calendars.exchange_calendar_xbel import XBELExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXBELExchangeCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XBELExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XBEL is open from 9:30 am to 2:00 pm.
        yield 4.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2024-01-01",  # New Year's Day
            "2024-01-02",  # New Year's Day
            "2024-01-07",  # Orthodox Christmas
            "2024-02-15",  # Statehood Day
            "2024-02-16",  # Statehood Day Holiday
            "2024-05-01",  # Labour Day
            "2024-05-02",  # Labour Day Holiday
            "2024-05-03",  # Orthodox Good Friday
            "2024-05-06",  # Orthodox Easter Monday
            "2024-11-11",  # Armistice Day
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2024-01-03",
            "2024-01-15",
            "2024-02-14",
            "2024-03-28",
            "2024-04-02",
            "2024-05-08",
            "2024-05-10",
            "2024-11-12",
            "2024-12-24",
            "2024-12-26",
        ]
