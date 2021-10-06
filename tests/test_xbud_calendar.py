import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xbud import XBUDExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBaseNew


class TestXBUDCalendar(ExchangeCalendarTestBaseNew):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XBUDExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XBUD is open from 9:00 to 5:00PM
        yield 8

    @pytest.fixture
    def regular_holidays_sample(self):
        hols = [
            # 2019
            "2019-01-01",  # New Year's Day
            "2019-03-15",  # National Holiday
            "2019-04-19",  # Good Friday
            "2019-04-22",  # Easter Monday
            "2019-05-01",  # Labour Day
            "2019-06-10",  # Whit Monday
            "2019-08-20",  # St. Stephen's Day
            "2019-10-23",  # National Holiday
            "2019-11-01",  # All Saint's Day
            "2019-12-24",  # Christmas Eve
            "2019-12-25",  # Christmas Day
            "2019-12-26",  # Second Day of Christmas
            "2019-12-31",  # New Year's Eve
            # Bridge Days. If some holidays fall on a Tuesday or Thursday
            # then Monday or Friday is also a holiday (bridge day).
            # New Years Day on Thursday, Jan 1
            "2015-01-01",
            "2015-01-02",
            # National Holiday on Tuesday, March 15
            "2016-03-15",
            "2016-03-14",
            # Labour Day on Tuesday, May 1
            "2018-05-01",
            "2018-04-30",
            # St. Stephen's Day on Thursday, Aug 20
            "2015-08-20",
            "2015-08-21",
            # National Holiday on Thursday, Oct 23
            "2014-10-23",
            "2014-10-24",
            # All Saint's Day on Tuesday, Nov 1
            "2016-11-01",
            "2016-10-31",
            # Second Day of Christmas on Thursday, Dec 26
            "2019-12-27",
            # Observance of bridge day when Second Day of Christmas falls on a Thursday
            # is not strict, although was observed in 2013, 2019.
            "2013-12-27",  # Friday
            "2019-12-27",  # Friday
        ]
        # New Year's Eve only a holiday from 2011.
        hols.extend([f"{year}-12-31" for year in range(2011, 2020)])
        yield hols

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield []

    @pytest.fixture
    def non_holidays_sample(self):
        non_hols = [
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # New Years Day on Sunday, Jan 1st
            "2011-12-30",
            "2012-01-02",
            # National Holiday on Sunday, March 15th
            "2015-03-13",
            "2015-03-16",
            # Labour Day on Sunday, May 1st
            "2016-04-29",
            "2016-05-02",
            # St. Stephen's Day on Saturday, August 20th
            "2016-08-19",
            "2016-08-22",
            # National Holiday on Sunday, Oct 23rd
            "2016-10-21",
            "2016-10-24",
            # All Saint's Day on Sunday, Nov 1
            "2015-10-30",
            "2015-11-02",
            # Christmas Eve on a Sunday. Note: 25th, 26th both holidays
            "2017-12-22",
            "2017-12-27",
            # Christmas on a Sunday. Note: 26th a holiday
            "2016-12-23",
            "2016-12-27",
            # 2nd Day of Christmas on Saturday, Dec 26. Note: 25th, 24th both holidays
            "2015-12-23",
            "2015-12-28",
            # New Year's Eve on Saturday, Dec 31
            "2016-12-30",
            "2017-01-02",
            #
            # Christmas Eve and New Years Eve are holidays although do not provoke
            # a bridge day if they fall on a Tuesday or Thursday. Following ensures
            # that what would be the bridge day is not a holiday.
            # Dec 23 Mondays
            "2002-12-23",
            "2013-12-23",
            "2019-12-23",
            # Dec 30 Mondays
            "2002-12-30",
            "2013-12-30",
            "2019-12-30",
            #
            # Although strictly a bridge day, 2002-12-27 is not observed as a holiday
            # (falls on a Friday following a holiday (Second Day of Christmas)).
            "2002-12-27",
        ]
        # Prior to 2011 New Year's Eve was only a holiday if it fell on a Monday (in
        # which case was treated as a bridge day). Check that nye not a holiday prior
        # to 2011 if it didn't fall on a Monday (or weekend).
        nye = [f"{year}-12-31" for year in range(2000, 2011)]
        nye_sessions = [
            date for date in nye if pd.Timestamp(date).weekday() not in [0, 5, 6]
        ]
        non_hols.extend(nye_sessions)
        yield non_hols
