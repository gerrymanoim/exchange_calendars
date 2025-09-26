import pytest

from exchange_calendars.exchange_calendar_xlit import XLITExchangeCalendar

from .test_exchange_calendar import ExchangeCalendarTestBase







class TestXLITExchangeCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        return XLITExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XLIT is open from 10:00 AM to 4:00 PM on its longest trading day.
        yield 6

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2024-01-01",  # New Year's Day
            "2024-02-16",  # Restoration of the State
            "2024-03-11",  # Restoration of Independence
            "2024-03-29",  # Good Friday
            "2024-04-01",  # Easter Monday
            "2024-05-01",  # Labour Day
            "2024-05-09",  # Ascension Day
            "2024-06-24",  # St. John's Day
            "2024-07-06",  # Statehood Day
            "2024-08-15",  # Assumption Day
            "2024-11-01",  # All Saints' Day
            "2024-12-24",  # Christmas Eve
            "2024-12-26",  # Boxing Day
            "2024-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2024-01-02",  # Not a holiday
            "2024-03-12",  # Not a holiday
            "2024-04-02",  # Not a holiday
            "2024-05-02",  # Not a holiday
            "2024-06-25",  # Not a holiday
        ]
