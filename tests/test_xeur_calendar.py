import pytest

from exchange_calendars.exchange_calendar_xeur import XEURExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXEURCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XEURExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # Open from 8:00 am to 10:00 pm.
        yield 14

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2026
            "2026-01-01",  # New Year's Day
            "2026-04-03",  # Good Friday
            "2026-04-06",  # Easter Monday
            "2026-05-01",  # Labour Day
            "2026-12-24",  # Christmas Eve
            "2026-12-25",  # Christmas
            # "2026-12-26",  Boxing Day is Saturday
            "2026-12-31",  # New Year's Eve
            # 2027
            "2027-01-01",  # New Year's Day
            "2027-03-26",  # Good Friday
            "2027-03-29",  # Easter Monday
            # "2027-05-01",  Labour day is Saturday
            "2027-12-24",
            # "2027-12-25",  Christmas is Saturday
            # "2027-12-26",  Boxing Day is Sunday
            "2027-12-31",
            # 2028
            # "2028-01-01",  New Year's Day is Saturday
            "2028-04-14",  # Good Friday
            "2028-04-17",  # Easter Monday
            "2028-05-01",  # Labour Day
            # "2028-12-24",  Christmas Eve is Sunday
            "2028-12-25",  # Christmas
            "2028-12-26",  # Boxing Day
            # "2028-12-31",  New Year's Eve is Sunday
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Whit Monday
            "2026-05-25",
            "2027-05-17",
            # German Unity Day
            "2028-10-03",  # Tuesday
        ]
