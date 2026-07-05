import pytest

from exchange_calendars.exchange_calendar_xhel import XHELExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXHELCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XHELExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 8.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2018-01-01",  # New Year's Day
            "2017-01-06",  # Epiphany
            "2018-03-30",  # Good Friday
            "2018-04-02",  # Easter Monday
            "2018-05-01",  # Labour Day
            "2018-05-10",  # Ascension Day
            "2018-06-22",  # Midsummer Eve
            "2018-12-06",  # Finland Independence Day
            "2018-12-24",  # Christmas Eve
            "2018-12-25",  # Christmas Day
            "2018-12-26",  # Boxing Day
            "2018-12-31",  # New Year's Ev
            # Midsummer Eve falls on Friday following June 18th.
            "2010-06-25",  # fell prior Friday June 18th
            "2017-06-23",  # fell prior Sunday
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield []

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Midsummer Eve falls on Friday following June 18th. In 2010, June 18th was
            # a Friday - check not a holiday (holiday is following Friday, June 25th).
            "2010-06-18",
            #
            # Holidays that fall on a weekend are not made up. Ensure surrounding
            # days are not holidays.
            # In 2018, the Epiphany fell on a Saturday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2018-01-05",
            "2018-01-08",
            # In 2010, Labour Day fell on a Saturday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2010-04-30",
            "2010-05-03",
            # In 2015, Finland Independence Day fell on a Sunday, so the market
            # should be open on both the prior Friday and the following Monday.
            "2015-12-04",
            "2015-12-07",
            # In 2010, Christmas fell on a Saturday, meaning Boxing Day fell on
            # a Sunday. The market should thus be open on the following Monday.
            "2010-12-27",
            # In 2017, New Year's Day fell on a Sunday, so the market should be
            # open on both the prior Friday and the following Monday.
            "2016-12-30",
            "2017-01-02",
        ]
