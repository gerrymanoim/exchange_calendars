import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xosl import XOSLExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXOSLCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XOSLExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XOSL is open from 9:00 am to 4:30 pm.
        yield 7.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2018
            "2018-01-01",  # New Year's Day
            "2018-03-29",  # Maundy Thursday
            "2018-03-30",  # Good Friday
            "2018-04-02",  # Easter Monday
            "2018-05-01",  # Labour Day
            "2018-05-10",  # Ascension Day
            "2018-05-17",  # Constitution Day
            "2018-05-21",  # Whit Monday
            "2018-12-24",  # Christmas Eve
            "2018-12-25",  # Christmas Day
            "2018-12-26",  # Boxing Day
            "2018-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend and are not made up. Ensure surrounding
            # days are not holidays.
            # In 2010, Labour Day fell on a Saturday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2010-04-30",
            "2010-05-03",
            # In 2015, Constitution Day fell on a Sunday, so the market should
            # be open on both the prior Friday and the following Monday.
            "2015-05-15",
            "2015-05-18",
            # In 2010, Christmas fell on a Saturday, meaning Boxing Day fell on
            # a Sunday. The market should thus be open on the following Monday.
            "2010-12-27",
            # In 2017, New Year's Day fell on a Sunday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2016-12-30",
            "2017-01-02",
        ]

    @pytest.fixture
    def early_closes_sample(self):
        # 2011 was first year that Holy Wednesday observed an early close.
        yield ["2011-04-20"]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(13, "h")

    @pytest.fixture
    def non_early_closes_sample(self):
        # 2010 was last year before Holy Wednesday started to observe an early close.
        yield ["2010-03-31"]

    @pytest.fixture
    def non_early_closes_sample_time(self):
        yield pd.Timedelta(hours=16, minutes=20)
