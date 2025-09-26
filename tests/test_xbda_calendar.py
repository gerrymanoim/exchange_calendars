import pandas as pd
import pytest

from exchange_calendars.exchange_calendar_xbda import XBDAExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXBDACalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XBDAExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The XBDA is open from 9:00 am to 4:30 pm.
        yield 7.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2025
            "2025-01-01",  # New Year's Day
            "2025-04-18",  # Good Friday
            "2025-05-23",  # Bermuda Day (the Friday before the last Monday in May)
            "2025-06-16",  # National Heroes Day (third Monday in June)
            "2025-07-31",  # Emancipation Day (Thursday before first Monday in August)
            "2025-08-01",  # Mary Prince Day (Friday after Emancipation Day)
            "2025-09-01",  # Labour Day (first Monday in September)
            "2025-11-11",  # Remembrance Day
            "2025-12-25",  # Christmas Day
            "2025-12-26",  # Boxing Day
            # 2024
            "2024-01-01",  # New Year's Day
            "2024-03-24",  # Good Friday
            "2024-05-24",  # Bermuda Day (the Friday before the last Monday in May)
            "2024-06-17",  # National Heroes Day (third Monday in June)
            "2024-08-01",  # Emancipation Day (Thursday before first Monday in August)
            "2024-08-02",  # Mary Prince Day (Friday after Emancipation Day)
            "2024-09-02",  # Labour Day (first Monday in September)
            "2024-11-11",  # Remembrance Day
            "2024-12-25",  # Christmas Day
            "2024-12-26",  # Boxing Day
            # 2023
            "2023-01-02",  # New Year's Day (observed)
            "2023-04-07",  # Good Friday
            "2023-05-26",  # Bermuda Day (the Friday before the last Monday in May)
            "2023-06-19",  # National Heroes Day (third Monday in June)
            "2023-08-03",  # Emancipation Day (Thursday before first Monday in August)
            "2023-08-04",  # Mary Prince Day (Friday after Emancipation Day)
            "2023-09-04",  # Labour Day (first Monday in September)
            "2023-11-13",  # Remembrance Day (observed, since Nov 11 is a Saturday)
            "2023-12-25",  # Christmas Day
            "2023-12-26",  # Boxing Day
            # 2022
            "2022-01-03",  # New Year's Day (observed)
            "2022-04-15",  # Good Friday
            "2022-05-27",  # Bermuda Day (the Friday before the last Monday in May)
            "2022-06-20",  # National Heroes Day (third Monday in June)
            "2022-07-28",  # Emancipation Day (Thursday before first Monday in August)
            "2022-07-29",  # Mary Prince Day (Friday after Emancipation Day)
            "2022-09-05",  # Labour Day (first Monday in September)
            "2022-11-11",  # Remembrance Day
            "2022-12-26",  # Christmas Day (observed, since Dec 25 is a Sunday)
            "2022-12-27",  # Boxing Day (observed, since Dec 26 is a Monday)
            # 2021
            "2021-01-01",  # New Year's Day
            "2021-04-02",  # Good Friday
            "2021-05-28",  # Bermuda Day (the Friday before the last Monday in May)
            "2021-06-21",  # National Heroes Day (third Monday in June)
            "2021-07-29",  # Emancipation Day (Thursday before first Monday in August)
            "2021-07-30",  # Mary Prince Day (Friday after Emancipation Day)
            "2021-09-06",  # Labour Day (first Monday in September)
            "2021-11-11",  # Remembrance Day
            "2021-12-27",  # Christmas Day (observed, since Dec 25 is a Saturday)
            "2021-12-28",  # Boxing Day (observed, since Dec 26 is a Sunday)
            # 2020
            "2020-01-01",  # New Year's Day
            "2020-04-10",  # Good Friday
            "2020-05-29",  # Bermuda Day (the Friday before the last Monday in May)
            "2020-06-15",  # National Heroes Day (third Monday in June)
            "2020-07-30",  # Emancipation Day (Thursday before first Monday in August)
            "2020-07-31",  # Mary Prince Day (Friday after Emancipation Day)
            "2020-09-07",  # Labour Day (first Monday in September)
            "2020-11-11",  # Remembrance Day
            "2020-12-25",  # Christmas Day
            "2020-12-28",  # Boxing Day (observed, since Dec 26 is a Saturday)
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Days around holidays
            "2025-05-29",  # Thursday before Bermuda Day
            "2025-06-17",  # Tuesday after National Heroes Day
            "2025-08-04",  # Monday after Mary Prince Day
            "2025-12-23",  # Tuesday before Christmas Eve
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            # Christmas Eve (early close at 2:00 PM)
            "2025-12-24",
            "2024-12-24",
            "2023-12-22",  # In 2023, December 24th falls on a Sunday, so the early close for Christmas Eve is observed on Friday, December 22nd.  # noqa: E501
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(14, "h")
