import pytest

from exchange_calendars.exchange_calendar_xpar import XPARExchangeCalendar
from .test_exchange_calendar import EuronextCalendarTestBase


class TestXPARCalendar(EuronextCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XPARExchangeCalendar

    @pytest.fixture
    def additional_regular_holidays_sample(self):
        yield [
            # Final observance of these regular holidays
            "2001-06-04",  # Whit Monday
            "2000-07-14",  # Bastille Day
            "2001-12-31",  # New Year's Eve
            #
            # Boxing Day and New Year's Eve, observed until 1995 and again
            # from 2000 and 1998 respectively
            "1995-12-26",  # Boxing Day
            "2000-12-26",  # Boxing Day
            "1993-12-31",  # New Year's Eve
            "1998-12-31",  # New Year's Eve
            "1999-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def additional_non_holidays_sample(self):
        yield [
            # First year when previous regular holiday no longer observed
            "2002-05-20",  # Whit Monday
            "2003-07-14",  # Bastille Day
            "2002-12-31",  # New Year's Eve
            #
            # Boxing Day and New Year's Eve were trading days in 1996 and 1997
            "1996-12-26",
            "1996-12-31",
            "1997-12-26",
            "1997-12-31",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            # French public holidays on which the Paris Bourse closed in 1998
            "1998-05-08",  # Victory Day
            "1998-05-21",  # Ascension Day
            "1998-07-13",  # Bridge day before Bastille Day
            "1998-11-11",  # Armistice Day
            "1998-12-24",  # Christmas Eve
        ]
