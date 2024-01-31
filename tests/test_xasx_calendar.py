import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xasx import XASXExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXASXCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XASXExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 6

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2018
            "2018-01-01",  # New Year's Day
            "2018-01-26",  # Australia Day
            "2018-03-30",  # Good Friday
            "2018-04-02",  # Easter Monday
            "2018-04-25",  # Anzac Day
            "2018-06-11",  # Queen's Birthday
            "2018-12-25",  # Christmas
            "2018-12-26",  # Boxing Day
            #
            # Holidays made up when fall on weekend.
            # Anzac Day is observed on the following Monday only when falling
            # on a Sunday. In years where Anzac Day falls on a Saturday, there
            # is no make-up.
            "2017-01-02",  # New Year's Day on a Sunday, observed on Monday.
            "2014-01-27",  # Australia Day on a Sunday, observed on Monday (from 2010).
            "2010-04-26",  # Anzac Day on a Sunday, observed on Monday.
            # Christmas/Boxing Day are special cases, whereby if Christmas is a
            # Saturday and Boxing Day is a Sunday, the next Monday and Tuesday will
            # be holidays. If Christmas is a Sunday and Boxing Day is a Monday then
            # Monday and Tuesday will still both be holidays.
            # Christmas on a Sunday, Boxing Day on Monday.
            "2016-12-26",
            "2016-12-27",
            # Christmas on a Saturday, Boxing Day on Sunday.
            "2010-12-27",
            "2010-12-28",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        # National day of mourning for the queen
        yield ["2022-09-22"]

    @pytest.fixture
    def non_holidays_sample(self):
        # Anzac Day on a Saturday, does not have a make-up (prior to 2010).
        yield ["2015-04-27", "2004-04-26"]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            # In 2018, the last trading days before Christmas and New Year's
            # are on Mondays, so they should be early closes.
            "2018-12-24",
            "2018-12-31",
            # In 2017, Christmas and New Year's fell on Mondays, so the last
            # trading days before them were Fridays, which should be early closes.
            "2017-12-22",
            "2017-12-29",
            # In 2016, Christmas and New Year's fell on Sundays, so the last
            # trading days before them were Fridays, which should be early closes.
            "2016-12-23",
            "2016-12-30",
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=14, minutes=10)

    @pytest.fixture
    def non_early_closes_sample(self):
        # In 2009 the early close rules should not be in effect yet.
        yield ["2009-12-24", "2009-12-31"]

    @pytest.fixture
    def non_early_closes_sample_time(self):
        yield pd.Timedelta(16, "h")
