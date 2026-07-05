import pytest

from exchange_calendars.exchange_calendar_xwar import XWARExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXWARCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XWARExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XWAR is open from 9:00AM to 5:00PM.
        yield 8

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2019 +
            "2019-01-01",  # New Year's Day
            "2017-01-06",  # Epiphany
            "2019-04-19",  # Good Friday
            "2019-04-22",  # Easter Monday
            "2019-05-01",  # Labour Day
            "2019-05-03",  # Constitution Day
            "2019-06-20",  # Corpus Christi
            "2019-08-15",  # Armed Forces Day
            "2019-11-01",  # All Saints' Day
            "2019-11-11",  # Independence Day
            "2019-12-24",  # Christmas Eve
            "2019-12-25",  # Christmas Day
            "2019-12-26",  # Boxing Day
            "2019-12-31",  # New Year's Eve
            #
            # New Year's Eve observed as regular holiday only from 2011
            "2012-12-31",  # First year fell on otherwise trading day.
            "2013-12-31",
            #
            # The Epithany observed as regular holiday only from 2011
            "2011-01-06",
            "2012-01-06",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "2005-04-08",  # Pope's Funeral.
            "2007-12-31",  # New Year's Eve (adhoc).
            "2008-05-02",  # Exchange Holiday.
            "2009-01-02",  # Exchange Holiday.
            "2013-04-16",  # Exchange Holiday.
            "2018-01-02",  # Exchange Holiday.
            "2018-11-12",  # Independence Holiday.
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # New Year's Eve not a holiday prior to 2011.
            "2008-12-31",
            "2009-12-31",
            "2010-12-31",
            #
            # Epiphany not a holiday prior to 2011.
            "2006-01-06",
            "2009-01-06",
            "2010-01-06",
            #
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # New Year's Eve on a Saturday and New Year's Day on a Sunday.
            "2016-12-30",
            "2017-01-02",
            # Epiphany (January 6th) on a Sunday.
            "2019-01-04",
            "2019-01-07",
            # Labour Day (May 1st) on a Sunday.
            "2016-04-29",
            "2016-05-02",
            # Constitution Day (May 3rd) on a Saturday.
            "2014-05-02",
            "2014-05-05",
            # Armed Forces Day (August 15th) on a Saturday.
            "2015-08-14",
            "2015-08-17",
            # All Saints' Day (November 1st) on a Sunday.
            "2015-10-30",
            "2015-11-02",
            # Independence Day (November 11th) on a Saturday.
            "2017-11-10",
            "2017-11-13",
            # Christmas Eve on a Saturday and Christmas on a Sunday. Note that
            # Monday the 26th is Boxing Day, so check the 27th.
            "2016-12-23",
            "2016-12-27",
        ]
