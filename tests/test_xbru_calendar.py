import pytest

from exchange_calendars.exchange_calendar_xbru import XBRUExchangeCalendar
from .test_exchange_calendar import EuronextCalendarTestBase


class TestXBRUCalendar(EuronextCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XBRUExchangeCalendar

    @pytest.fixture
    def additional_regular_holidays_sample(self):
        yield [
            # Final observance of these regular holidays
            "2000-06-01",  # Ascension Day
            "2001-06-04",  # Whit Monday
            "2000-07-21",  # Belgium Independence Day
            "2001-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def additional_non_holidays_sample(self):
        yield [
            # First year when previous regular holiday no longer observed
            "2001-05-24",  # Ascension Day
            "2002-05-20",  # Whit Monday
            "2003-07-21",  # Belgium Independence Day
            "2002-12-31",  # New Year's Eve
        ]
