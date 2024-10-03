import pytest

from exchange_calendars.exchange_calendar_xtai import XTAIExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXTAICalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XTAIExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XTAI is open from 9:00AM to 1:30PM
        yield 4.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2019
            "2019-01-01",  # New Year's Day
            "2019-02-04",  # Chinese New Year's Eve
            "2019-02-05",  # Chinese New Year
            "2019-02-28",  # Peace Memorial Day
            "2019-04-04",  # Women and Children's Day
            "2019-04-05",  # Tomb Sweeping Day
            "2019-05-01",  # Labour Day
            "2019-06-07",  # Dragon Boat Festival
            "2019-09-13",  # Mid-Autumn Festival
            "2019-10-10",  # National Day
            #
            # Holidays falling on a Sat/Sun are made up on Fri/Mon respectively.
            "2017-01-02",  # New Year's Day on Sunday, Jan 1st.
            "2017-01-27",  # Chinese New Year on Saturday, Jan 28th.
            "2016-02-29",  # Peace Memorial Day on Sunday, Feb 28th.
            "2015-04-03",  # Women and Children's Day on Saturday, Apr 4th.
            "2015-04-06",  # Tomb Sweeping Day on Sunday, Apr 5th.
            "2016-05-02",  # Labour Day on Sunday, May 1st.
            "2015-06-19",  # Dragon Boat Festival on Saturday, Jun 20th.
            "2015-09-28",  # Mid-Autumn Festival on Sunday, Sep 27th.
            "2015-10-09",  # National Day on Saturday, Oct 10th.
            #
            # "bridge days" where a Monday or Friday is made into a holiday
            # to fill gap between weekend and a holiday on Tuesday or Thursday.
            "2015-01-02",  # New Year's Day on Thursday, Jan 1st.
            "2017-02-27",  # Peace Memorial day on Tuesday, Feb 28th.
            "2017-04-03",  # Women and Children's Day on Tuesday, Apr 4th.
            "2019-10-11",  # National Day on Thursday, Oct 10th.
            "2018-04-06",  # Tomb Sweeping Day on Thursday, Apr 5th.
            "2017-05-29",  # Dragon Boat Festival on Tuesday, May 30th.
            "2016-09-16",  # Mid-Autumn Festival on Thursday, Sep 15th.
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays falling on a Sat/Sun are made up on Fri/Mon respectively,
            # make sure made up in correct direction (e.g. if fell on Sat, make sure
            # Mon not a holiday / if fell on Sun, make sure Fri not a holiday).
            "2016-12-30",  # New Year's Day on Sunday, Jan 1st.
            "2016-02-26",  # Peace Memorial Day on Sunday, Feb 28th.
            "2014-04-07",  # Tomb Sweeping Day on Saturday, Apr 5th.
            "2016-04-29",  # Labour Day on Sunday, May 1st.
            "2015-06-22",  # Dragon Boat Festival on Saturday, Jun 20th.
            "2015-09-25",  # Mid-Autumn Festival on Sunday, Sep 27th.
            "2015-10-12",  # National Day on Saturday, Oct 10th.
            "2024-09-16",  # Mid-Autumn Festival on Tuesday, Sep 17th.
            "2024-10-11",  # National Day on Thursday, Oct 10th.
            "2030-09-13",  # Mid-Autumn Festival on Thursday, Sep 12th.
        ]
