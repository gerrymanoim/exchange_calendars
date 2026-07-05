import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xkls import XKLSExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXKLSCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XKLSExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XKLS is open from 9AM to 5PM
        yield 8

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2019-01-01",  # New Year's Day
            "2019-01-21",  # Thaipusam
            "2019-02-01",  # Federal Territory Day
            "2019-02-05",  # Chinese New Year Day 1
            "2019-02-06",  # Chinese New Year Day 2
            "2019-05-01",  # Labour Day
            "2019-05-20",  # Wesak Day
            "2019-05-22",  # Nuzul Al Quran
            "2019-06-05",  # Eid al Fitr Day 1
            "2019-06-06",  # Eid al Fitr Day 2
            "2019-08-12",  # Eid al Adha
            "2018-08-31",  # National Day
            "2019-09-02",  # Muharram
            "2019-09-16",  # Malaysia Day
            "2019-10-28",  # Deepavali
            "2018-11-20",  # Birthday of Muhammad
            "2019-12-25",  # Christmas Day
            #
            # Holidays falling on Sundays are made up on the next Monday.
            "2012-01-02",  # New Year's Day
            "2015-02-02",  # Federal Territory Day
            "2017-01-30",  # Chinese New Year 2nd Day
            "2016-05-02",  # Labour Day
            "2014-09-01",  # National Day
            "2012-09-17",  # Malaysia Day
            "2016-12-26",  # Christmas Day
            "2020-05-25",  # Eid al Fitr
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield []

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # New Year's Day on Saturday, Jan 1st.
            #   2010-12-31 is an adhoc holiday
            "2010-12-30",
            "2011-01-03",
            # Labour Day on Saturday, May 1st.
            "2010-04-30",
            "2010-05-03",
            # Nuzul Al-Quran on Saturday, Jul 4th.
            "2017-07-03",
            "2017-07-06",
            # National Day on Saturday, Aug 31st.
            #   2019-09-02 is Muharram
            "2019-08-30",
            "2019-09-03",
            # Muharram on Saturday, Oct 25th.
            "2014-10-24",
            "2014-10-27",
            # Malaysia Day on Saturday, Sep 16th.
            "2017-09-15",
            "2017-09-18",
            # Birthday of Prophet Muhammad on Saturday, Mar 31st.
            "2007-03-30",
            "2007-04-02",
            # Christmas Day on Saturday, Dec 25th.
            "2010-12-24",
            "2010-12-27",
            # Thaipusam on Saturday, Feb 8th.
            "2020-02-07",
            "2020-02-10",
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2019-02-04",  # Day before Chinese New Year.
            "2019-06-04",  # Day before Eid al Fitr.
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=12, minutes=30)
