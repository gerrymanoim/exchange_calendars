import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xbue import XBUEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXBUECalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XBUEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XBUE is open from 11:00AM to 5:00PM
        yield 6

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2019
            "2019-01-01",  # New Year's Day
            "2019-03-04",  # Carnival Monday
            "2019-03-05",  # Carnival Tuesday
            "2017-03-24",  # Truth and Justice Mem Day
            "2019-04-02",  # Malvinas Day
            "2019-04-13",  # Maundy Thursday
            "2019-04-14",  # Good Friday
            "2019-05-01",  # Labour Day
            "2018-05-25",  # May Day Revolution
            "2019-06-17",  # Martin Miguel de-Guemes Day
            "2019-06-20",  # National Flag Day
            "2019-07-09",  # Independence Day
            "2019-08-19",  # San Martin's Day
            "2019-10-14",  # Cultural Diversity Day
            "2019-11-18",  # Day of Natl Sovereignty
            "2017-12-08",  # Immaculate Conception
            "2019-12-25",  # Christmas Day
            #
            # Day of Respect for Cultural Diversity follows a "nearest Monday"
            # rule. When Oct 12 falls on a Tuesday or Wednesday the holiday is
            # observed on the previous Monday, and when it falls on any other
            # non-Monday it is observed on the following Monday.  This means
            # the holiday will be observed on the following dates (Mondays).
            "2019-10-14",  # Falls on Saturday
            "2018-10-15",  # Falls on Friday
            "2017-10-16",  # Falls on Thursday
            "2016-10-10",  # Falls on Wednesday
            "2015-10-12",  # Falls on Monday
            "2014-10-13",  # Falls on Sunday
            "2013-10-14",  # Falls on Saturday
            "2010-10-11",  # Falls on Tuesday
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # New Year's Day on Sunday, Jan 1st.
            "2016-12-30",
            "2017-01-02",
            # Truth and Justice Memorial Day on Sunday, Mar 24th.
            "2019-03-22",
            "2019-03-25",
            # Malvinas Day on Saturday, Apr 2nd.
            "2016-04-01",
            "2016-04-04",
            # Labour Day on Sunday, May 1st.
            "2016-04-29",
            "2016-05-02",
            # May Day Revolution on Saturday, May 25th.
            "2019-05-24",
            "2019-05-27",
            # Martin Miguel de-Guemes Day on Sunday, Jun 17th.
            "2018-06-15",
            "2018-06-18",
            # National Flag Day on Saturday, Jun 20th.
            "2015-06-19",
            "2015-06-22",
            # Independence Day on Sunday, Jul 9th.
            "2017-07-07",
            "2017-07-10",
            # Bank Holiday on Sunday, Nov 6th.
            "2016-11-04",
            "2016-11-07",
            # Immaculate Conception on Sunday, Dec 8th.
            "2019-12-06",
            "2019-12-09",
            # Christmas on Sunday
            "2016-12-23",
            "2016-12-26",
        ]

    @pytest.fixture
    def early_closes_sample(self):
        # Christmas Eve, New Year's Eve
        yield ["2019-12-24", "2019-12-31"]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(13, "h")
