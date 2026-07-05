import pytest

from exchange_calendars.exchange_calendar_xphs import XPHSExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXPHSCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XPHSExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XPHS is open from 9:30AM to 3:30PM
        yield 6

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2019 +
            "2019-01-01",  # New Year's Day
            "2019-02-05",  # Chinese New Year
            "2019-04-09",  # Araw Ng Kagitingan
            "2019-04-18",  # Maundy Thursday
            "2019-05-01",  # Labour Day
            "2019-06-05",  # Eid al-Fitr
            "2019-06-12",  # Independence Day
            "2019-08-12",  # Eid al-Adha
            "2019-08-21",  # Ninoy Aquino Day
            "2019-08-26",  # National Heroes Day
            "2017-09-01",  # Eid al-Adha
            "2019-11-01",  # All Saint's Day
            "2018-11-30",  # Bonifacio Day
            "2019-12-24",  # Christmas Eve
            "2019-12-25",  # Christmas
            "2019-12-30",  # Rizal Day
            "2019-12-31",  # New Year's Eve
            #
            # National Heroes' Day, last Monday of every August.
            "2019-08-26",
            "2018-08-27",
            "2017-08-28",
            "2016-08-29",
            "2015-08-31",
            "2014-08-25",
            "2013-08-26",
            "2012-08-27",
            "2011-08-29",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            # Holidays prior to 2011 are hard-coded for convenience. Below is a subset
            # of these holidays (those for 2008) to verify they are being recognised.
            "2008-01-01",
            "2008-02-25",
            "2008-03-20",
            "2008-03-21",
            "2008-04-07",
            "2008-05-01",
            "2008-06-09",
            "2008-08-18",
            "2008-08-25",
            "2008-10-01",
            "2008-12-01",
            "2008-12-25",
            "2008-12-26",
            "2008-12-29",
            "2008-12-30",
            "2008-12-31",
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend and are not made up. Ensure surrounding
            # days are not holidays.
            # New Year's Day on Sunday, Jan 1st.
            #  2011-12-30 is Rizal Day
            "2011-12-29",
            "2012-01-02",
            # Chinese New Year's on Saturday, Jan 28th.
            "2017-01-27",
            "2017-01-30",
            # Araw Ng Kagitingan on Sunday, Apr 9th.
            "2017-04-07",
            "2017-04-10",
            # Labour Day on Saturday, May 1st.
            "2016-04-29",
            "2016-05-02",
            # Independence Day on Sunday, Jun 12th.
            "2016-06-10",
            "2016-06-13",
            # Ninoy Aquino Day on Sunday, Aug 21st.
            "2016-08-19",
            "2016-08-22",
            # All Saint's Day on Sunday, Nov 1st.
            "2015-10-30",
            "2015-11-02",
            # Bonifacio Day on Saturday, Nov 30th.
            "2019-11-29",
            "2019-12-02",
            # Christmas Eve + Christmas Day on weekend.
            "2011-12-23",
            "2011-12-26",
            # Rizal Day + New Year's Eve on weekend.
            #  2018-01-01 and 2018-01-02 are both holidays.
            "2017-12-29",
            "2018-01-03",
        ]
