import pytest

from exchange_calendars.exchange_calendar_xstu import XSTUExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXSTUCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XSTUExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XSTU is open from 7:30 am to 10:00 pm.
        yield 14.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2025
            "2025-01-01",  # New Year
            "2025-04-18",  # Good Friday
            "2025-04-21",  # Easter Monday
            "2025-05-01",  # Labor Day
            "2025-12-24",  # Christmas Eve
            "2025-12-25",  # Christmas
            "2025-12-26",  # Boxing Day
            "2025-12-31",  # New Year's Eve
            # 2026
            "2026-01-01",  # New Year
            "2026-04-03",  # Good Friday
            "2026-04-06",  # Easter Monday
            "2026-05-01",  # Labor Day
            "2026-12-24",  # Christmas Eve
            "2026-12-25",  # Christmas
            # Boxing Day 2026 is Sat, so not a trading day anyway
            "2026-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield []

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Check Whit Monday and German Unity Day are NOT holidays
            "2025-06-09",  # Whit Monday
            "2025-10-03",  # German Unity Day
            "2026-05-25",  # Whit Monday
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield []

    @pytest.fixture
    def early_closes_sample_time(self):
        yield None
