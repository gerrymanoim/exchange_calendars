import pytest

from exchange_calendars.exchange_calendar_xcse import XCSEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBaseNew


class TestXCSECalendar(ExchangeCalendarTestBaseNew):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XCSEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XCSE is open from 9:00 am to 5:00 pm.
        yield 8

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2018
            "2018-01-01",  # New Year's Day
            "2018-03-29",  # Maundy Thursday
            "2018-03-30",  # Good Friday
            "2018-04-02",  # Easter Monday
            "2018-04-27",  # General Prayer Day
            "2018-05-10",  # Ascension Day
            "2018-05-11",  # Bank Holiday
            "2018-05-21",  # Whit Monday
            "2018-06-05",  # Constitution Day
            "2018-12-24",  # Christmas Eve
            "2018-12-25",  # Christmas Day
            "2018-12-26",  # Boxing Day
            "2018-12-31",  # New Year's Eve
            # First occurrence that regular holiday observed.
            "2009-05-22",  # May Bank Holiday
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # In 2016, Constitution Day fell on a Sunday, so the market should
            # be open on both the prior Friday and the following Monday.
            "2016-06-03",
            "2016-06-06",
            # In 2010, Christmas fell on a Saturday, meaning Boxing Day fell on
            # a Sunday. The market should thus be open on the following Monday.
            "2010-12-27",
            # In 2017, New Year's Day fell on a Sunday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2016-12-30",
            "2017-01-02",
            #
            # Year prior to first occurrence when May Bank Holiday observed.
            "2008-05-02",
        ]
