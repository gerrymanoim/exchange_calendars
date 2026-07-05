import pytest

from exchange_calendars.exchange_calendar_xlim import XLIMExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXLIMCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XLIMExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XLIM is open from 9:00AM to 4:00PM.
        yield 7

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2025-06-07",  # Battle of Arica and Flag Day
            "2025-07-23",  # Peruvian Air Force Day
            "2025-08-06",  # Battle of Junín
            "2025-12-09",  # Battle of Ayacucho
            "2019-01-01",  # New Year's Day
            "2019-04-18",  # Maundy Thursday
            "2019-04-19",  # Good Friday
            "2019-05-01",  # Labour Day
            "2018-06-29",  # St. Peter and St. Paul Day
            "2016-07-28",  # Independence Day 1
            "2016-07-29",  # Independence Day 2
            "2019-08-30",  # Santa Rosa
            "2019-10-08",  # Battle of Angamos
            "2019-11-01",  # All Saints' Day
            "2017-12-08",  # Immaculate Conception
            "2019-12-25",  # Christmas Day
            #
            # New Year's Eve ceased being observed after 2007.
            "2005-12-31",
            "2006-12-31",
            "2007-12-31",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            # Exchange holidays.
            "2009-01-02",
            "2009-07-27",
            "2015-01-02",
            "2015-07-27",
            "2015-10-09",
            # ASPA Summit.
            "2012-10-01",
            "2012-10-02",
            # APEC Summit.
            "2016-11-17",
            "2016-11-18",
            # 8th Summit of the Americas.
            "2018-04-13",
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # New Year's Day on a Sunday.
            "2016-12-30",
            "2017-01-02",
            # Labour Day (May 1st) on a Sunday.
            "2016-04-29",
            "2016-05-02",
            # Saint Peter and Saint Paul Day (June 29th) on a Saturday.
            "2019-06-28",
            "2019-07-01",
            # Independence Days (July 28th and 29th) on a Saturday and Sunday.
            "2018-07-27",
            "2018-07-30",
            # Santa Rosa (August 30th) on a Sunday.
            "2015-08-28",
            "2015-08-31",
            # Battle of Angamos (October 8th) on a Sunday.
            "2017-10-06",
            "2017-10-09",
            # All Saints' Day (November 1st) on a Sunday.
            "2015-10-30",
            "2015-11-02",
            # Immaculate Conception (December 8th) on a Sunday.
            "2019-12-06",
            "2019-12-09",
            # Christmas on a Sunday.
            "2016-12-23",
            "2016-12-26",
            #
            # New Year's Eve ceased being observed after 2007.
            "2008-12-31",
            "2009-12-31",
            "2010-12-31",
        ]
