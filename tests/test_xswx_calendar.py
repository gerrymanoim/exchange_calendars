import pytest

from exchange_calendars.exchange_calendar_xswx import XSWXExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestIXSWXCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XSWXExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XSWX is open from 9:00 am to 5:30 pm.
        yield 8.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2012
            # New Year's Day isn't observed because it was on a Sunday
            "2012-01-02",  # Berchtold's Day observed
            "2012-04-06",  # Good Friday
            "2012-04-09",  # Easter Monday
            "2012-05-01",  # Labour Day
            "2012-05-17",  # Ascension Day
            "2012-05-28",  # Whit Monday
            "2012-08-01",  # Swiss National Day
            "2012-12-24",  # Christmas Eve
            "2012-12-25",  # Christmas
            "2012-12-26",  # Boxing Day
            "2012-12-31",  # New Year's Eve
            #
            # Berchtold's Day, observed until 2001 and again from 2003
            "2001-01-02",
            "2003-01-02",
            #
            # Ascension Day and Whit Monday, observed until 2001 and again
            # from 2003
            "2001-05-24",  # Ascension Day
            "2001-06-04",  # Whit Monday
            "2003-05-29",  # Ascension Day
            "2003-06-09",  # Whit Monday
            #
            # Swiss National Day, observed until 2000 and again from 2006
            "2000-08-01",
            "2006-08-01",
            #
            # Christmas Eve and New Year's Eve, observed until 1995 (both on a
            # weekend in 1994 and 1995) and again from 1998
            "1993-12-24",  # Christmas Eve
            "1993-12-31",  # New Year's Eve
            "1998-12-24",  # Christmas Eve
            "1998-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Berchtold's Day, Ascension Day and Whit Monday were trading
            # days in 2002
            "2002-01-02",
            "2002-05-09",  # Ascension Day
            "2002-05-20",  # Whit Monday
            #
            # Swiss National Day was a trading day from 2001 through 2005
            "2001-08-01",
            "2002-08-01",
            "2003-08-01",
            "2005-08-01",
            #
            # Christmas Eve and New Year's Eve were trading days in 1996 and
            # 1997
            "1996-12-24",
            "1996-12-31",
            "1997-12-24",
            "1997-12-31",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "2000-01-03",  # Year 2000 changeover
        ]
