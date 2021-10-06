import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xdub import XDUBExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBaseNew


class TestXDUBCalendar(ExchangeCalendarTestBaseNew):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XDUBExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XDUB is open from 8:00 am to 4:28 pm.
        yield 8.467

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2018
            "2018-01-01",  # New Year's Day
            "2018-03-30",  # Good Friday
            "2018-04-02",  # Easter Monday
            "2018-05-07",  # May Bank Holiday
            "2018-06-04",  # June Bank Holiday
            "2018-12-25",  # Christmas Day
            "2018-12-26",  # Boxing Day
            #
            # Holidays falling on a weekend are made up on what would otherwise be
            # the next trading day.
            # In 2017 New Year's Day fell on a Sunday, so the following Monday
            # should be a holiday.
            "2017-01-02",
            # In 2010 Christmas fell on a Saturday, meaning Boxing Day fell on
            # a Sunday. The following Monday and Tuesday should both be
            # holidays.
            "2010-12-27",
            "2010-12-28",
            # In 2016 Christmas fell on a Sunday, but again the following
            # Monday and Tuesday should both be holidays.
            "2016-12-26",
            "2016-12-27",
            #
            # Regular holiday's that later ceased to be observed.
            "1996-03-18",  # St. Patrick's Day Observed
            "2000-03-17",  # St. Patrick's Day
            "2009-05-01",  # Labour Day
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield ["2018-03-02"]  # March 2, 2018 was closed due to sever weather.

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Regular holidays that earlier ceased to be observed.
            "2001-03-19",  # St. Patrick's Day Observed
            "2003-03-17",  # St. Patrick's Day
            "2012-05-01",  # Labour Day
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2010-12-24",  # Christmas Eve on a weekday.
            "2018-12-24",  # Christmas Eve on a weekday.
            "2017-12-22",  # Last trading day prior to Christmas Eve.
            "2010-12-31",  # New Year's Eve on a weekday.
            "2018-12-31",  # New Year's Eve on a weekday.
            "2017-12-29",  # Last trading day prior to New Year's Eve.
            "2018-03-01",  # Severe weather, closed early.
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=12, minutes=28)

    @pytest.fixture
    def non_early_closes_sample(self):
        yield [
            # Prior to 2010 Christmas Eve and New Year's Eve were full days
            "2009-12-24",
            "2009-12-31",
            #
            # Just a normal day...
            "2017-03-01",
        ]

    @pytest.fixture
    def non_early_closes_sample_time(self):
        yield pd.Timedelta(hours=16, minutes=28)
