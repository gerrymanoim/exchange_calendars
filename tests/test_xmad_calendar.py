import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xmad import XMADExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXMADCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XMADExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XMAD is open from 9:00 am to 5:30 pm.
        yield 8.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2014
            "2014-01-01",  # New Year's Day
            "2014-04-18",  # Good Friday
            "2014-04-21",  # Easter Monday
            "2014-05-01",  # Labour Day
            "2014-12-25",  # Christmas Day
            "2014-12-26",  # Boxing Day
            #
            # Holidays falling on a weekend and subsequently made up.
            "2004-08-16",  # Assumption day, falls Sun 15th, made up on Monday.
            #
            # Christmas Eve was observed as a full day, and then became a half
            # day from 2010 until 2020, and then went back to being a full day
            # from 2021
            "2010-12-24",
            "2021-12-24",
            #
            # Last observance of holidays that subsequently ceased to be observed.
            "2006-01-06",  # Epiphany
            "2003-08-15",  # Assumption Day
            "2004-10-12",  # National Day
            "2004-11-01",  # All Saints Day
            "2004-12-06",  # Constitution Day
            "2004-12-08",  # Immaculate Conception
            #
            # New Year's Eve was a holiday through to 2010, then became an early
            # close, and then went back to being a full day's holiday from 2021.
            "2010-12-31",
            "2021-12-31",
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
            # Christmas also fell on a Saturday, meaning Boxing Day fell on a
            # Sunday. The market should still be open on the following Monday
            # (note that Christmas Eve was observed as a holiday through 2010,
            # so the market is closed on the previous Friday).
            "2010-12-27",
            #
            # Christmas Eve was an early close from 2012-12-24 to 2020-12-24
            "2012-12-24",
            "2020-12-24",
            #
            # Regular holidays that ceased to be observed.
            # First subsequent 'would-be' occurrence...
            "2009-01-06",  # Epiphany
            "2005-08-15",  # Assumption Day
            "2005-10-12",  # National Day
            "2005-11-01",  # All Saints Day
            "2005-12-06",  # Constitution Day
            "2005-12-08",  # Immaculate Conception
            # New Year's Eve was holiday through to 2010, but then became an early
            # close after that, before becoming a full market holiday again in 2021.
            "2012-12-31",
            "2020-12-31",
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            # Christmas Eve was an early close from 2012-12-24, to 2020-12-24
            "2012-12-24",
            "2020-12-24",
            "2012-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(14, "h")
