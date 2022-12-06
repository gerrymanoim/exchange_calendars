import pytest

from exchange_calendars.exchange_calendar_aixk import AIXKExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class TestAIXKCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield AIXKExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 6

    @pytest.fixture
    def start_bound(self):
        yield T("2017-01-01")

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2013
            "2013-12-01",  # First President Day
            # 2021
            "2021-01-01",  # New Year’s Day
            "2021-01-07",  # Orthodox Christmas Day
            "2021-03-08",  # International Women’s Day
            "2021-03-22",  # Nauryz Holiday
            "2021-03-23",  # Nauryz Holiday
            "2021-03-24",  # Nauryz Holiday
            "2021-05-03",  # Kazakhstan People Solidarity Day
            "2021-05-07",  # Defender’s Day
            "2021-05-10",  # Victory Day Holiday
            "2021-07-06",  # Capital City Day
            "2021-07-20",  # Kurban Ait Holiday
            "2021-08-30",  # Constitution Day
            "2021-12-01",  # First President Day
            "2021-12-16",  # Independence Day
            "2021-12-17",  # Independence Day Holiday
            #
            # Holiday's made up when fall on weekend.
            # Last day of Nauryz on Saturday, 23th
            "2019-03-21",
            "2019-03-22",
            "2019-03-25",
            # First day of Nauryz on Sunday
            "2020-03-22",
            "2020-03-23",
            "2020-03-24",
            # Women's day on Sunday, Mar 8th
            "2020-03-09",
            # Capital day on Sunday, Jul 7th
            "2019-07-08",
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        # Bridge Days
        yield [
            "2018-03-09",  # between Women's day - Weekend
            "2018-04-30",  # between Weekend - Kazakhstan People Solidarity Day
            "2018-05-08",  # between Defender's Day - Victory Day
            "2018-08-31",  # between Constitution Day - Weekend
            "2018-12-31",  # between New Year's Eve - New Year's day
            "2019-05-10",  # between Victory Day - Weekend
            "2020-01-03",  # between New Year's day - Weekend
            "2020-12-18",  # between Independence day - Weekend
            "2021-06-05",  # between Weekend - Capital City day
            "2022-03-07",  # between Weekend - Women's day
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2022-12-01",  # First President Day
        ]
