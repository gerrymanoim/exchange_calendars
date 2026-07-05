import pytest
from exchange_calendars.exchange_calendar_xtal import XTALExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXTALCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XTALExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XTAL is open from 10:00 am to 4:00 pm.
        yield 6

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2025 sample year
            "2025-01-01",  # New Year's Day
            "2025-02-24",  # Independence Day
            "2025-04-18",  # Good Friday
            "2025-04-21",  # Easter Monday
            "2025-05-01",  # Labour Day
            "2025-06-23",  # Victory Day
            "2025-06-24",  # Midsummer Day
            "2025-08-20",  # Restoration of Independence
            "2025-12-24",  # Christmas Eve
            "2025-12-26",  # Boxing Day
            "2025-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Days around holidays that should be open
            "2025-01-02",
            "2025-02-25",
            "2025-04-17",
            "2025-05-02",
            "2025-08-21",
            "2025-12-23",
            "2025-12-25",
            "2025-12-30",
        ]
