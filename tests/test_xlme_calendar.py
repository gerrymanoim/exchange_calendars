import pytest

from exchange_calendars.exchange_calendar_xlme import XLMEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXLMECalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XLMEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 18

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            "2025-01-01",  # New Year's Day
            "2025-04-18",  # Good Friday
            "2025-04-21",  # Easter Monday
            "2025-05-05",  # Early May Bank Holiday
            "2025-05-26",  # Spring Bank Holiday
            "2025-08-25",  # Summer Bank Holiday
            "2025-12-25",  # Christmas Day
            "2025-12-26",  # Boxing Day
            "2026-01-01",  # New Year's Day
            "2026-04-03",  # Good Friday
            "2026-04-06",  # Easter Monday
            "2026-05-04",  # Early May Bank Holiday
            "2026-05-25",  # Spring Bank Holiday
            "2026-08-31",  # Summer Bank Holiday
            "2026-12-25",  # Christmas Day
            "2026-12-28",  # Boxing Day observed
            "2027-01-01",  # New Year's Day observed
            "2027-03-26",  # Good Friday
            "2027-03-29",  # Easter Monday
            "2027-05-03",  # Early May Bank Holiday
            "2027-05-31",  # Spring Bank Holiday
            "2027-08-30",  # Summer Bank Holiday
            "2027-12-27",  # Christmas Day observed
            "2027-12-28",  # Boxing Day observed
            "2028-01-03",  # New Year's Day observed
            "2028-04-14",  # Good Friday
            "2028-04-17",  # Easter Monday
            "2028-05-01",  # Early May Bank Holiday
            "2028-05-29",  # Spring Bank Holiday
            "2028-08-28",  # Summer Bank Holiday
            "2028-12-25",  # Christmas Day
            "2028-12-26",  # Boxing Day
            "2029-01-01",  # New Year's Day
            "2029-03-30",  # Good Friday
            "2029-04-02",  # Easter Monday
            "2029-05-07",  # Early May Bank Holiday
            "2029-05-28",  # Spring Bank Holiday
            "2029-08-27",  # Summer Bank Holiday
            "2029-12-25",  # Christmas Day
            "2029-12-26",  # Boxing Day
            "2030-01-01",  # New Year's Day
            "2030-04-19",  # Good Friday
            "2030-04-22",  # Easter Monday
            "2030-05-06",  # Early May Bank Holiday
            "2030-05-27",  # Spring Bank Holiday
            "2030-08-26",  # Summer Bank Holiday
            "2030-12-25",  # Christmas Day
            "2030-12-26",  # Boxing Day
            "2031-01-01",  # New Year's Day
            "2031-04-11",  # Good Friday
            "2031-04-14",  # Easter Monday
            "2031-05-05",  # Early May Bank Holiday
            "2031-05-26",  # Spring Bank Holiday
            "2031-08-25",  # Summer Bank Holiday
            "2031-12-25",  # Christmas Day
            "2031-12-26",  # Boxing Day
            "2032-01-01",  # New Year's Day
            "2032-03-26",  # Good Friday
            "2032-03-29",  # Easter Monday
            "2032-05-03",  # Early May Bank Holiday
            "2032-05-31",  # Spring Bank Holiday
            "2032-08-30",  # Summer Bank Holiday
            "2032-12-27",  # Christmas Day observed
            "2032-12-28",  # Boxing Day observed
            "2033-01-03",  # New Year's Day observed
            "2033-04-15",  # Good Friday
            "2033-04-18",  # Easter Monday
            "2033-04-30",  # Early May Bank Holiday
            "2033-05-02",  # Spring Bank Holiday
            "2033-08-29",  # Summer Bank Holiday
            "2033-12-26",  # Christmas Day observed
            "2033-12-27",  # Boxing Day observed
            "2034-01-02",  # New Year's Day observed
            "2034-04-07",  # Good Friday
            "2034-04-10",  # Easter Monday
            "2034-05-01",  # Early May Bank Holiday
            "2034-05-29",  # Spring Bank Holiday
            "2034-08-28",  # Summer Bank Holiday
            "2034-12-25",  # Christmas Day
            "2034-12-26",  # Boxing Day
            "2035-01-01",  # New Year's Day
            "2035-03-23",  # Good Friday
            "2035-03-26",  # Easter Monday
            "2035-05-07",  # Early May Bank Holiday
            "2035-05-28",  # Spring Bank Holiday
            "2035-08-27",  # Summer Bank Holiday
            "2035-12-25",  # Christmas Day
            "2035-12-26",  # Boxing Day
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            "2025-12-29",
            "2030-06-19",  # Tradeable 3rd Wednesday prompt date.
        ]
