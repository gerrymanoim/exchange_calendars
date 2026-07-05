import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xwbo import XWBOExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXWBOCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XWBOExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XWBO is open from 9:00 am to 5:30 pm.
        yield 8.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2014 +
            "2014-01-01",  # New Year's Day
            "2014-01-06",  # Epiphany
            "2014-04-18",  # Good Friday
            "2014-04-21",  # Easter Monday
            "2014-05-01",  # Labour Day
            "2014-05-29",  # Ascension Day
            "2014-06-09",  # Whit Monday
            "2014-06-19",  # Corpus Christi
            "2014-08-15",  # Assumption Day
            "2014-10-26",  # National Day (Weekend)
            "2015-10-26",  # National Day (Weekday)
            "2013-11-01",  # All Saints Day (Weekday)
            "2014-11-01",  # All Saints Day (Weekend)
            "2014-12-08",  # Immaculate Conception
            "2014-12-24",  # Christmas Eve
            "2014-12-25",  # Christmas Day
            "2014-12-26",  # St. Stephen's Day
            "2014-12-31",  # New Year's Eve
            #
            # 2019
            "2019-01-01",  # New Year's Day
            "2019-04-19",  # Good Friday
            "2019-04-22",  # Easter Monday
            "2019-05-01",  # Labour Day
            "2019-06-10",  # Whit Monday
            "2019-10-26",  # National Day (Weekend)
            "2019-12-24",  # Christmas Eve
            "2019-12-25",  # Christmas Day
            "2019-12-26",  # St. Stephen's Day
            "2019-12-31",  # New Year's Eve
            #
            # Prior to 2016, when New Year's Eve fell on the weekend, it was
            # observed on the preceding Friday.
            "2011-12-30",
            "2006-12-29",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield []

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend and are not made up. Ensure surrounding
            # days are not holidays.
            # Epiphany (January 6th) on a Saturday.
            "2018-01-05",
            "2018-01-08",
            # Assumption Day (August 15th) on a Saturday.
            "2015-08-14",
            "2015-08-17",
            # Labour Day (May 1st) on a Saturday.
            "2010-04-30",
            "2010-05-03",
            # National Day (October 26th) on a Sunday.
            "2014-10-24",
            "2014-10-27",
            # All Saints Day (November 1st) on a Sunday.
            "2015-10-30",
            "2015-11-02",
            # Immaculate Conception (December 8th) on a Saturday.
            "2018-12-07",
            "2018-12-10",
            # Christmas Eve on a Saturday and Christmas on a Sunday. This means
            # that the market should be open on the previous Friday, closed on
            # Monday for St. Stephen's Day, and open again on Tuesday.
            "2011-12-23",
            "2011-12-27",
            #
            # New Year's Eve not made up since 2016. Ensure day on which previously
            # made up (prior Friday) is not a holiday.
            "2016-12-30",
            "2017-12-29",
            # Whit Monday was a trading day in 2023
            "2023-05-29",
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            # Last trading day preceeding New Year's Eve
            "2017-12-29",
            "2018-12-28",
            "2019-12-30",
            "2020-12-30",
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=14, minutes=15)
