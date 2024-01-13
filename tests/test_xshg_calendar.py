import pytest

from exchange_calendars.exchange_calendar_xshg import XSHGExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class TestXSHGCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XSHGExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # Shanghai stock exchange is open from 9:30 am to 3pm
        yield 5.5

    @pytest.fixture
    def start_bound(self):
        yield T("1990-12-03")

    @pytest.fixture
    def end_bound(self):
        yield T("2025-12-31")

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2017
            "2017-01-02",
            "2017-01-27",
            "2017-01-30",
            "2017-01-31",
            "2017-02-01",
            "2017-02-02",
            "2017-04-03",
            "2017-04-04",
            "2017-05-01",
            "2017-05-29",
            "2017-05-30",
            "2017-10-02",
            "2017-10-03",
            "2017-10-04",
            "2017-10-05",
            "2017-10-06",
            # 2020
            "2020-01-31",
            # 2022
            "2022-01-31",
            "2022-09-12",
            "2022-10-06",
            "2022-10-07",
            # 2023
            "2023-05-03",  # Part of Chinese Labor Day 2023
            "2023-06-23",  # Part of Dragon Boat Festival 2023
            # 2024
            "2024-01-01",
            # 2024 Chinese New Year
            "2024-02-12",
            "2024-02-13",
            "2024-02-14",
            "2024-02-15",
            "2024-02-16",
            "2024-04-04",  # Part of Qingming Festival 2024
            "2024-04-05",  # Part of Qingming Festival 2024
            "2024-05-01",  # Part of Chinese Labor Day 2024
            "2024-05-02",
            "2024-05-03",
            "2024-06-10",  # Part of Dragon Boat Festival 2024
            "2024-09-16",  # Part of Mid-Autumn Festival 2024
            "2024-09-17",  # Part of Mid-Autumn Festival 2024
            "2024-10-01",  # Part of National Day 2024
            "2024-10-02",  # Part of National Day 2024
            "2024-10-03",  # Part of National Day 2024
            "2024-10-04",  # Part of National Day 2024
        ]
