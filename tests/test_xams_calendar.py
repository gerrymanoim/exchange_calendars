import pytest

from exchange_calendars.exchange_calendar_xams import XAMSExchangeCalendar
from .test_exchange_calendar import EuronextCalendarTestBase


class TestXAMSCalendar(EuronextCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XAMSExchangeCalendar

    @pytest.fixture
    def additional_regular_holidays_sample(self):
        yield [
            # Final observance of these regular holidays
            "2000-06-01",  # Ascension Day
            "2001-06-04",  # Whit Monday
            "2001-04-30",  # Queen's Day
            "2001-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def additional_non_holidays_sample(self):
        yield [
            # First year when previous regular holiday no longer observed
            "2001-05-24",  # Ascension Day
            "2002-05-20",  # Whit Monday
            "2002-04-30",  # Queen's Day
            "2002-12-31",  # New Year's Eve
        ]
