import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xnze import XNZEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXNZECalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XNZEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The New Zealand Exchange is open from 10:00 am to 4:45 pm.
        yield 6.75

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2014
            "2014-01-01",  # New Year's Day
            "2014-01-02",  # Day after New Year's Day
            "2014-02-06",  # Waitangi Day
            "2014-04-18",  # Good Friday
            "2014-04-21",  # Easter Monday
            "2014-04-25",  # Anzac Day
            "2014-06-02",  # Queen's Birthday
            "2014-10-27",  # Labour Day
            "2014-12-25",  # Christmas
            "2014-12-26",  # Boxing Day
            #
            # Holidays falling on a weekend and subsequently made up.
            "2010-12-27",  # Christmas Day fell on Saturday
            "2010-12-28",  # Boxing Day fell on Sunday
            "2011-01-03",  # New Year's Day fell on Saturday
            "2011-01-04",  # Day after New Year's Day (also a holdiay) fell on Sunday
            "2011-12-27",  # Christmas Day fell on Sunday
            "2012-01-02",  # Day after New Year's Day (a holiday) fell on Monday 2nd...
            "2012-01-03",  # but as New Year's Day fell on Sunday, made up Tuesday 3rd
            "2016-02-08",  # Waitangi Day fell on Saturday (2016 first year made up).
            "2015-04-27",  # Aztec Day fell on Saturday (2015 first year made up).
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "2022-06-24", "2035-06-29", "2049-06-25",  # Mataraki Day (a small selection)
            "2022-09-26"  # National day of mourning for the queen
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # In 2012 New Year's Day fell on Sunday such that Day after New Year's Day
            # (also a holiday), fell on Monday 2nd. New Year's Day was therefore made up
            # on Tuesday 3rd. Make sure nothing being made up on Wednesday 4th...
            "2012-01-04",
            #
            # Prior to 2015, following holidays are not made up if fall on weekend.
            "2010-02-08",  # Monday that followed Waitangi Day that fell on Saturday.
            "2010-04-26",  # Monday that followed Anzac Day that fell on Sunday.
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            # # 2011 was first observance of early closes on the trading day preceeding
            # Christmas Day and New Year's Day
            "2011-12-23",  # NB Christmas Day was a Sunday, so Friday an early close
            "2011-12-30",  # NB New Year's Day was a Sunday, so Friday an early close
            #
            "2014-12-24",  # Christmas Eve
            "2014-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=12, minutes=45)

    @pytest.fixture
    def non_early_closes_sample(self):
        yield [
            "2010-12-24",  # Prior to 2011 Christmas Eve is not an early close.
            "2010-12-31",  # Prior to 2011 New Year's Eve is not an early close.
        ]

    @pytest.fixture
    def non_early_closes_sample_time(self):
        yield pd.Timedelta(hours=16, minutes=45)
