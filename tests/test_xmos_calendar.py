import pytest

from exchange_calendars.exchange_calendar_xmos import XMOSExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXMOSCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XMOSExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XMOS is open from 10:00AM to 6:45PM.
        yield 8.75

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2022
            "2022-03-07",  # Women's Day falls on a Tuesday.
            "2022-05-03",  # LabourDay Holiday extended to Tuesday.
            "2022-05-10",  # Victory Day Holiday extended to Tuesday.
            # 2020
            "2020-06-24",  # Non-Working Day
            "2020-07-01",  # Non-Working Day
            # 2019
            "2019-01-01",  # New Year's Day
            "2019-01-02",  # New Year's Holiday
            "2019-01-07",  # Orthodox Christmas
            "2018-02-23",  # Defender of the Fatherland
            "2019-03-08",  # Women's Day
            "2019-05-01",  # Labour Day
            "2019-05-09",  # Victory Day
            "2019-06-12",  # Day of Russia
            "2019-11-04",  # Unity Day
            "2019-12-31",  # New Year's Eve
            #
            # Holidays falling on a weekend and made up on following Monday.
            # New Year's Day on a Saturday and New Year's Holiday on a Sunday.
            "2011-01-03",
            # Orthodox Christmas (January 7th) on a Sunday.
            "2018-01-08",
            # Defender of the Fatherland Day (February 23rd) on a Saturday.
            "2008-02-25",
            # Women's Day (March 8th) on a Sunday.
            "2015-03-09",
            # Labour Day (May 1st) on a Sunday.
            "2016-05-02",
            # Victory Day (May 9th) on a Saturday.
            "2015-05-11",
            # Day of Russia (June 12th) on a Sunday.
            "2016-06-13",
            # Unity Day (November 4th) on a Sunday.
            "2018-11-05",
            #
            # "bridge days" where a Monday or Friday is made into a holiday
            # to fill gap between weekend and a holiday on Tuesday or Thursday.
            "2016-01-08",  # Orthodox Christmas falls on a Thursday.
            "2010-02-22",  # Defender of the Fatherland falls on a Tuesday.
            "2012-03-09",  # Women's Day falls on a Thursday.
            "2012-04-30",  # Labour Day falls on a Tuesday.
            "2017-05-08",  # Victory Day falls on a Tuesday.
            "2014-06-13",  # Day of Russia falls on a Thursday.
            "2010-11-05",  # Unity Day falls  on a Thursday.
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend and are not made up. Ensure not made up.
            # New Year's Holiday on a Saturday, but the following Monday is a
            # trading day.
            "2016-01-04",
            "2021-01-04",
            "2022-01-03",
            # Orthodox Christmas on a Saturday, but the following Monday is a
            # trading day.
            "2017-01-09",
            "2023-01-09",
            # Orthodox Christmas (January 7th) on a Sunday, but
            # the following Monday is a trading day.
            "2024-01-08",
            # Defender of the Fatherland Day (February 23rd) on a Saturday, but
            # the following Monday is a trading day.
            "2019-02-25",
            # Victory Day (May 9th) on a Sunday, but
            # the following Monday is a trading day.
            "2021-05-10",
            # Day of Russia (June 12th) on a Saturday, but
            # the following Monday is a trading day.
            "2021-06-14",
        ]
