import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xetr import XETRExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXETRCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XETRExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The FWB is open from 9:00 am to 5:30 pm.
        yield 8.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2012
            # New Year's Day fell on a Sunday, so it is not a holiday this year
            "2012-04-06",  # Good Friday
            "2012-04-09",  # Easter Monday
            "2012-05-01",  # Labour Day
            # Whit Monday was observed in 2007, then 2015 and after.
            # German Unity Day started being celebrated in 2014
            "2012-12-24",  # Christmas Eve
            "2012-12-25",  # Christmas
            "2012-12-26",  # Boxing Day
            "2012-12-31",  # New Year's Eve
            #
            # Whit Monday
            "2015-05-25",  # regularly observed from 2015
            "2016-05-16",
            "2021-05-24"
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "2007-05-28",  # Whit Monday observed as a one-off in 2007
            "2017-10-31",  # Reformation Day observed as a one-off in 2017
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2012-12-28",  # Last working day of 2012
            #
            # Whit Monday
            "2006-06-05",  # not observed prior to 2007 (observed in 2007)
            "2008-05-12",  # and not observed from 2008 through 2014
            "2022-06-06",  # not observed in 2022
            #
            # Reformation Day observed only in 2017, ensure not a holiday
            # in surrounding years.
            "2016-10-31",
            "2018-10-31",
            # German Unity Day was not observed in 2022
            "2022-10-03"
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2011-12-30",  # NYE on Sat, so Fri is a half day
            "2012-12-28",  # NYE on Mon, so preceding Fri is a half day
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(14, "H")
