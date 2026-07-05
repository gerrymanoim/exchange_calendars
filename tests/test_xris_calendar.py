import pytest
from exchange_calendars.exchange_calendar_xris import XRISExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXRISCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XRISExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XRIS is open from 10:00 AM to 4:00 PM.
        yield 6

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2025 sample year
            "2025-01-01",  # New Year's Day
            "2025-04-18",  # Good Friday
            "2025-04-21",  # Easter Monday
            "2025-05-01",  # Labour Day
            "2025-05-04",  # Restoration of Independence
            "2025-06-23",  # Midsummer's Eve
            "2025-06-24",  # Midsummer's Day
            "2025-11-18",  # Proclamation Day
            "2025-12-24",  # Christmas Eve
            "2025-12-26",  # Boxing Day
            "2025-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Days around holidays that should be open
            "2025-01-02",
            "2025-04-17",
            "2025-11-10",
            "2025-12-23",
            "2025-12-25",
            "2025-12-30",
        ]
