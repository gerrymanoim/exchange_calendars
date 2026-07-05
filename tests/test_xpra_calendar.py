import pytest

from exchange_calendars.exchange_calendar_xpra import XPRAExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXPRACalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XPRAExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XPRA is open from 9:00 to 4:20PM
        yield 7.34

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2019 +
            "2019-01-01",  # New Year's Day
            "2019-04-19",  # Good Friday
            "2019-04-22",  # Easter Monday
            "2019-05-01",  # Labour Day
            "2019-05-08",  # Liberation Day
            "2019-07-05",  # St. Cyril/Methodius Day
            "2018-07-06",  # Jan Hus Day
            "2018-09-28",  # Czech Statehood Day
            "2019-10-28",  # Independence Day
            "2017-11-17",  # Freedom/Democracy Day
            "2019-12-24",  # Christmas Eve
            "2019-12-25",  # Christmas Day
            "2019-12-26",  # Second Day of Christmas
            "2019-12-31",  # Exchange Holiday
            #
            # Good Friday is a regular holiday from 2013
            "2013-03-29",
            "2014-04-18",
            "2015-04-03",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "2002-08-14",  # Extreme Flooding
            "2004-01-02",  # Restoration of the Czech Independence Day
            "2005-01-03",  # Restoration of the Czech Independence Day
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend and are not made up. Ensure surrounding
            # days are not holidays.
            # New Years Day on Sunday, Jan 1st
            "2011-12-30",
            "2012-01-02",
            # Labour Day on Sunday, May 1st
            "2016-04-29",
            "2016-05-02",
            # Liberation Day on Sunday, May 8th
            "2016-05-06",
            "2016-05-09",
            # Saints Cyril and Methodius Day on Saturday, Jul 5th
            "2014-07-04",
            "2014-07-07",
            # Jan Hus Day on Saturday, Jul 6th
            #   Note: 7/5/2019 is a holiday
            "2019-07-04",
            "2019-07-08",
            # Czech Statehood Day on Saturday, Sept 28th
            "2019-09-27",
            "2019-09-30",
            # Independence Day on Sunday, Oct 28th
            "2018-10-26",
            "2018-10-29",
            # Struggle for Freedom and Democracy Day on Sunday, Nov 17
            "2019-11-15",
            "2019-11-18",
            # Christmas Eve on a Sunday
            #   Note: 25th, 26th both holidays
            "2017-12-22",
            "2017-12-27",
            # Christmas on a Sunday
            #   Note: 26th a holiday
            "2016-12-23",
            "2016-12-27",
            # 2nd Day of Christmas on Saturday, Dec 26
            #   Note: 25th, 24th both holidays
            "2015-12-23",
            "2015-12-28",
            # Exchange Holiday on Saturday, Dec 31
            "2016-12-30",
            "2017-01-02",
            #
            # Good Friday was not a holiday prior to 2013
            "2010-04-02",
            "2011-04-22",
            "2012-04-06",
        ]
