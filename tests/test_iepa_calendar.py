import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_iepa import IEPAExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestIEPACalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield IEPAExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 22

    @pytest.fixture
    def regular_holidays_sample(self):
        # new year's, good friday, christmas
        yield ["2016-01-01", "2016-03-25", "2016-12-26"]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield ["2012-10-29"]  # hurricane sandy (day one)

    @pytest.fixture
    def non_holidays_sample(self):
        yield ["2012-10-30"]  # hurricane sandy day two - exchange open

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2016-01-18",  # mlk
            "2016-02-15",  # presidents
            "2016-05-30",  # mem day
            "2016-07-04",  # independence day
            "2016-09-05",  # labor
            "2016-11-24",  # thanksgiving
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(13, "h")
