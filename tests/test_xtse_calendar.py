import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xtse import XTSEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXTSECalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XTSEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 6.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2012-01-02",  # New Year's Day 1st Jan fell on a Sunday, made up Monday.
            "2012-02-20",  # Family Day
            "2012-04-06",  # Good Friday
            "2012-05-21",  # Victoria Day
            "2012-07-02",  # Canada Day
            "2012-08-06",  # Civic Holiday
            "2012-09-03",  # Labour Day
            "2012-10-08",  # Thanksgiving
            "2012-12-25",  # Christmas
            "2012-12-26",  # Boxing Day
            #
            "2015-05-18",  # Victoria Day observed Monday before 25th, never Mon 25th.
            #
            # Holidays falling on a weekend and made up.
            "2010-12-27",  # Christmas Day 25th fell on Saturday, made up Monday.
            "2010-12-28",  # Boxing Day 26th fell on Sunday, made up Tuesday.
            "2015-12-28",  # Boxing Day 26th fell on Saturday, made up Monday.
            "2016-12-26",  # Christmas Day 26th fell on Monday, make sure holiday.
            "2016-12-27",  # Christmas Day 25th fell on Sunday, made up Tuesday.)
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "2001-09-11",  # 9/11
            "2001-09-12",  # 9/11
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Make sure made up holidays do not extend beyond last made up date.
            "2010-12-29",  # First day (Wed) post Boxing Day that is not a holiday.
            "2016-12-28",  # First day (Wed) post Boxing Day that is not a holiday.
            #
            "2015-05-25",  # Victoria Day observed Monday before 25th, never Mon 25th.
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2010-12-24",  # Christmas Eve, first year that observed early close.
            "2012-12-24",  # Christmas Eve
            "2013-12-24",  # Christmas Eve
            "2014-12-24",  # Christmas Eve
            "2015-12-24",  # Christmas Eve
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(13, "h")

    @pytest.fixture
    def non_early_closes_sample(self):
        yield [
            "2009-12-24",  # Christmas Eve, last year not observing early close.
        ]

    @pytest.fixture
    def non_early_closes_sample_time(self):
        yield pd.Timedelta(16, "h")
