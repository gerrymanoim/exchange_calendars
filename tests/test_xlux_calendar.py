import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xlux import XLUXExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXLUXCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XLUXExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # XLUX is open from 9:00 am to 5:40 pm.
        yield 8 + (2 / 3)

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2025
            "2025-01-01",  # New Year's Day
            "2025-04-18",  # Good Friday
            "2025-04-21",  # Easter Monday
            "2025-05-01",  # Labour Day
            "2025-12-25",  # Christmas Day
            "2025-12-26",  # Boxing Day
            # 2024
            "2024-01-01",  # New Year's Day
            "2024-03-29",  # Good Friday
            "2024-04-01",  # Easter Monday
            "2024-05-01",  # Labour Day
            "2024-12-25",  # Christmas Day
            "2024-12-26",  # Boxing Day
            # 2023
            "2023-01-01",  # New Year's Day
            "2023-04-07",  # Good Friday
            "2023-04-10",  # Easter Monday
            "2023-05-01",  # Labour Day
            "2023-12-25",  # Christmas Day
            "2023-12-26",  # Boxing Day
            # 2022
            "2022-01-01",  # New Year's Day
            "2022-04-15",  # Good Friday
            "2022-04-18",  # Easter Monday
            "2022-05-01",  # Labour Day
            "2022-12-25",  # Christmas Day
            "2022-12-26",  # Boxing Day
            # 2021
            "2021-01-01",  # New Year's Day
            "2021-04-02",  # Good Friday
            "2021-04-05",  # Easter Monday
            "2021-05-01",  # Labour Day
            "2021-12-25",  # Christmas Day
            "2021-12-26",  # Boxing Day
            # 2020
            "2020-01-01",  # New Year's Day
            "2020-04-10",  # Good Friday
            "2020-04-13",  # Easter Monday
            "2020-05-01",  # Labour Day
            "2020-12-25",  # Christmas Day
            "2020-12-26",  # Boxing Day
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2025-01-02",
            "2025-01-14",
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            # 2025
            "2025-12-24",  # Christmas Eve
            "2025-12-31",  # New Year's Eve
            # 2024
            "2024-12-24",  # Christmas Eve
            "2024-12-31",  # New Year's Eve
            # 2021
            "2021-12-24",  # Christmas Eve
            "2021-12-31",  # New Year's Eve
            # 2020
            "2020-12-24",  # Christmas Eve
            "2020-12-31",  # New Year's Eve
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=14, minutes=5)
