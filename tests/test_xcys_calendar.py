import pytest
from exchange_calendars.exchange_calendar_xcys import XCYSExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXCYSExchangeCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XCYSExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 6.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2024-01-01",  # New Year's Day
            "2024-01-06",  # Epiphany
            "2024-03-18",  # Green Monday
            "2024-03-25",  # Greek Independence Day
            "2024-03-29",  # Catholic Good Friday
            "2024-04-01",  # Catholic Easter Monday / National Holiday
            "2024-05-01",  # Labour Day
            "2024-05-03",  # Orthodox Good Friday
            "2024-05-06",  # Orthodox Easter Monday
            "2024-05-07",  # Orthodox Easter Tuesday
            "2024-06-24",  # Holy Spirit Day
            "2024-08-15",  # Assumption Day
            "2024-10-01",  # Cyprus Independence Day
            "2024-10-28",  # Okhi Day
            "2024-12-24",  # Christmas Eve
            "2024-12-25",  # Christmas Day
            "2024-12-26",  # Boxing Day
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2024-01-02",  # Day after New Year's
            "2024-03-19",  # Day after Green Monday
            "2024-03-26",  # Day after Greek Independence Day
            "2024-05-02",  # Day after Labour Day
            "2024-05-08",  # Day after Orthodox Easter Tuesday
            "2024-06-18",  # Day after Holy Spirit Monday
            "2024-08-16",  # Day after Assumption Day
            "2024-10-02",  # Day after Cyprus Independence Day
            "2024-10-29",  # Day after Okhi Day
            "2024-12-27",  # Day after Boxing Day
        ]
