import pytest

from exchange_calendars.exchange_calendar_bvmf import BVMFExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestBVMFCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield BVMFExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 8

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2017
            "2017-01-25",  # Sao Paolo City Anniversary
            "2017-02-27",  # Carnival
            "2017-02-28",  # Carnival
            "2017-04-14",  # Good Friday
            "2017-04-21",  # Tiradentes Day
            "2017-05-01",  # Labor Day
            "2017-06-15",  # Corpus Christi Day
            "2017-09-07",  # Independence Day
            "2017-10-12",  # Our Lady of Aparecida Day
            "2017-11-02",  # All Souls Day
            "2017-11-15",  # Proclamation of the Republic Day
            "2017-11-20",  # Black Consciousness Day
            "2017-12-25",  # Christmas Day
            "2017-12-29",  # Day before New Years
            "2018-01-01",  # New Year's Day
            #
            # First occurrences
            "1998-07-09",  # First occurrence of Constitutionalist Revolution holiday
            "2006-11-20",  # Day of Black Awareness
            #
            # New Year's Eve
            # if Jan 1 is Tuesday through Saturday, exchange closed the day before.
            # if Jan 1 is Monday or Sunday, exchange closed the Friday before.
            "2017-12-29",  # 2018: Jan 1 is Monday, so Friday 12/29 should be closed
            "2016-12-30",  # 2017: Jan 1 is Sunday, so Friday 12/30 should be closed
            "2010-12-31",  # 2011: Jan 1 is Saturday, so Friday 12/31 should be closed
            "2013-12-31",  # 2014: Jan 1 is Wednesday, so Tuesday 12/31 should be closed
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield ["2014-06-12"]  # world-cup

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "1997-07-09",  # year prior to first Constitutionalist Revolution holiday
            "2003-11-20",  # year prior to first Day of Black Awareness holiday
        ]

    @pytest.fixture(scope="class")
    def late_opens_sample(self):
        # Ash Wednesday, 46 days before Easter Sunday
        yield ["2016-02-10", "2017-03-01", "2018-02-14", "2022-03-02"]
