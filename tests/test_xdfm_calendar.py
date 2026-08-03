import pytest

from exchange_calendars.exchange_calendar_xdfm import XDFMExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class TestXDFMCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XDFMExchangeCalendar

    @pytest.fixture
    def start_bound(self):
        yield T("2022-01-03")

    @pytest.fixture
    def end_bound(self):
        yield T("2026-12-31")

    @pytest.fixture
    def max_session_hours(self):
        yield 5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2024-01-01",  # New Year's Day
            "2024-12-02",  # UAE National Day (Day 1)
            "2024-12-03",  # UAE National Day (Day 2)
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "2023-04-20",  # Eid Al Fitr
            "2023-06-28",  # Eid Al Adha
            "2023-12-01",  # Commemoration Day
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Hijri New Year 2024 fell on Sunday 7 Jul (already a
            # weekend day); verify the following Monday is not bridged.
            "2024-07-08",
            # Prophet's Birthday 2024 fell on Sunday 15 Sep (already a
            # weekend day); verify the following Monday is not bridged.
            "2024-09-16",
        ]
