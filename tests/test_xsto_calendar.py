import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xsto import XSTOExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXSTOCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XSTOExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XSTO is open from 9:00 am to 5:30 pm.
        yield 8.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2018 +
            "2018-01-01",  # New Year's Day
            "2017-01-06",  # Epiphany
            "2018-03-30",  # Good Friday
            "2018-04-02",  # Easter Monday
            "2018-05-01",  # Labour Day
            "2018-05-10",  # Ascension Day
            "2018-06-06",  # National Day
            "2018-06-22",  # Midsummer Eve
            "2018-12-24",  # Christmas Eve
            "2018-12-25",  # Christmas Day
            "2018-12-26",  # Boxing Day
            "2018-12-31",  # New Year's Eve
            #
            # Midsummer Eve falls on the Friday after June 18.
            "2010-06-25",  # 18th a Friday, holiday observed Friday 25th (not 18th).
            "2017-06-23",  # 18th a Sunday, holiday observed following Friday.
            # Holidays that ceased to be observed.
            "2004-05-31",  # Whit Monday last observed in 2004.
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Midsummer Eve falls on the Friday after June 18.
            "2010-06-18",  # 18th a Friday, holiday observed Friday 25th (not 18th)
            #
            # Holidays that fall on a weekend and are not made up. Ensure surrounding
            # days are not holidays.
            # In 2018, the Epiphany fell on a Saturday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2018-01-05",
            "2018-01-08",
            # In 2010, Labour Day fell on a Saturday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2010-04-30",
            "2010-05-03",
            # In 2015, National Day fell on a Saturday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2015-06-05",
            "2015-06-08",
            # In 2010, Christmas fell on a Saturday, meaning Boxing Day fell on
            # a Sunday. The market should thus be open on the following Monday.
            "2010-12-27",
            # In 2017, New Year's Day fell on a Sunday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2016-12-30",
            "2017-01-02",
            #
            # Holidays that ceased to be observed.
            "2005-05-16",  # Whit Monday ceased to be observed from 2005.
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2018-01-05",  # Day before Epiphany.
            "2018-03-29",  # Maundy Thursday.
            "2018-04-30",  # Day before Labour Day.
            "2018-05-09",  # Day before Ascension Day.
            "2018-11-02",  # All Saints' Eve.
            "2015-10-30",  # All Saints' Eve.
            "2010-11-05",  # All Saints' Eve.
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(13, "h")
