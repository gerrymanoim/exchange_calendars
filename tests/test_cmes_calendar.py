import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_cmes import CMESExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestCMESCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class", params=["left", "right"])
    def all_calendars_with_answers(self, request, calendars, answers):
        yield (calendars[request.param], answers[request.param])

    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield CMESExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 24

    @pytest.fixture
    def regular_holidays_sample(self):
        # good friday, christmas, new years
        yield ["2016-03-25", "2016-12-26", "2016-01-02"]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2016-01-18",  # mlk day
            "2016-02-15",  # presidents
            "2016-05-30",  # mem day
            "2016-07-04",  # july 4
            "2016-09-05",  # labor day
            "2016-11-24",  # thanksgiving
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(12, "h")
