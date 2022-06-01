import pandas as pd
import pytest

from exchange_calendars.exchange_calendar_asex import ASEXExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestASEXCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield ASEXExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The ASEX is open from 10:00 to 5:20PM on its longest trading day
        yield 7 + (1 / 3)

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2019
            "2019-01-01",  # New Year's Day
            "2017-01-06",  # Epiphany
            "2019-03-11",  # Orthodox Ash Monday
            "2019-03-25",  # National Holiday
            "2019-04-19",  # Good Friday
            "2019-04-22",  # Easter Monday
            "2019-04-26",  # Orthodox Good Friday
            "2019-04-29",  # Orthodox Easter Monday
            "2019-05-01",  # Labour Day
            "2019-06-17",  # Orthodox Whit Monday
            "2019-08-15",  # Assumption Day
            "2019-10-28",  # National Holiday
            "2019-12-24",  # Christmas Eve
            "2019-12-25",  # Christmas Day
            "2019-12-26",  # Second Day of Christmas
            #
            # The Athens Stock Exchange observes Orthodox (or Eastern) Easter,
            # as well as Western Easter.  All holidays that are tethered to
            # Easter (i.e. Whit Monday, Good Friday, etc.), are relative to
            # Orthodox Easter. Following tests that Orthodox Easter and all
            # related holidays are correct.
            # Some Orthodox Easter dates
            "2005-05-01",
            "2006-04-23",
            "2009-04-19",
            "2013-05-05",
            "2015-04-12",
            "2018-04-08",
            # Some Orthodox Good Friday dates
            "2002-05-03",
            "2005-04-29",
            "2008-04-25",
            "2009-04-17",
            "2016-04-29",
            "2017-04-14",
            # Some Orthodox Whit Monday dates
            "2002-06-24",
            "2005-06-20",
            "2006-06-12",
            "2008-06-16",
            "2013-06-24",
            "2016-06-20",
            # Some Orthodox Ash Monday dates
            "2002-03-18",
            "2005-03-14",
            "2007-02-19",
            "2011-03-07",
            "2014-03-03",
            "2018-02-19",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        adhocs = [
            "2002-05-07",  # Market Holiday
            "2004-08-13",  # Assumption Day makeup
            "2008-03-04",  # Worker strikes
            "2008-03-05",  # Worker strikes
            "2013-05-07",  # May Day strikes
            "2014-12-31",  # New Year's Eve
            "2016-05-03",  # Labour Day makeup
        ]
        # 2015 Greek debt crisis closed markets for an extended period.
        # Following ensures there are no sessions over this time.
        crisis_dates = pd.date_range("2015-06-29", "2015-07-31")
        yield adhocs + crisis_dates.strftime("%Y-%m-%d").to_list()

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays NOT made up despite falling on weekend. Following ensures
            # surrounding days are not holidays.
            # New Years Day on Sunday, Jan 1st
            "2011-12-30",
            "2012-01-02",
            # Epiphany on Sunday, Jan 6th
            "2019-01-04",
            "2019-01-07",
            # National Holiday on Sunday, Mar 25th
            "2018-03-23",
            "2018-03-26",
            # Labour Day on Sunday, May 1st
            "2011-04-29",
            "2011-05-02",
            # Assumption Day on Saturday, Aug 15th
            "2015-08-14",
            "2015-08-17",
            # National Holiday on Saturday, Oct 28
            "2015-10-27",
            "2015-10-30",
            # Christmas Eve on a Sunday. NB 25th and 26th both holidays.
            "2017-12-22",
            "2017-12-27",
            # Christmas on a Sunday. NB 26th a holiday.
            "2016-12-23",
            "2016-12-27",
            # 2nd Day of Christmas on Saturday, Dec 26th. NB 25th, 24th both holidays.
            "2015-12-23",
            "2015-12-28",
        ]

    # Calendar-specific tests

    def test_close_time_change(self, default_calendar):
        """
        On Sept 29, 2008, the ASEX decided to push its close time back
        from 5:00PM to 5:20PM to close the time gap with Wall Street.
        """
        cal = default_calendar
        close_time = cal.closes["2006-09-29"]
        assert close_time == pd.Timestamp("2006-09-29 17:00", tz="Europe/Athens")

        close_time = cal.closes["2008-09-26"]
        assert close_time == pd.Timestamp("2008-09-26 17:00", tz="Europe/Athens")

        close_time = cal.closes["2008-09-29"]
        assert close_time == pd.Timestamp("2008-09-29 17:20", tz="Europe/Athens")

        close_time = cal.closes["2008-09-30"]
        assert close_time == pd.Timestamp("2008-09-30 17:20", tz="Europe/Athens")
