import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xcbf import XCBFExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBaseNew


class TestXCBFCalendar(ExchangeCalendarTestBaseNew):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XCBFExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 8

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2016
            "2016-01-01",  # new years: jan 1
            "2016-01-18",  # mlk: jan 18
            "2016-02-15",  # presidents: feb 15
            "2016-05-30",  # mem day: may 30
            "2016-07-04",  # independence day: july 4
            "2016-09-05",  # labor day: sep 5
            "2016-11-24",  # thanksgiving day: nov 24
            "2016-12-26",  # christmas (observed): dec 26
            "2017-01-02",  # new years (observed): jan 2 2017
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "1994-04-27",  # hurricane sandy: oct 29 2012, oct 30 2012
            "2004-06-11",  # national days of mourning:
            "2007-01-02",  # - apr 27 1994
            "2012-10-29",  # - june 11 2004
            "2012-10-30",  # - jan 2 2007
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Good Friday is not a holiday when Christas Day or New Year's Day falls
            # on a Friday.
            "2015-04-03",
            "2016-03-25",
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield ["2016-11-25"]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=12, minutes=15)
