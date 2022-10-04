import pytest

from exchange_calendars.exchange_calendar_xtae import XTAEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXTAECalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XTAEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # Longest session is from 9:59:00 to 17:15:00
        yield 7.25 + (1.0 / 60.0)

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2019
            "2019-03-21",  # Purim
            "2019-04-09",  # Election Day
            "2019-04-25",  # Passover II Eve
            "2019-04-26",  # Passover II
            "2019-05-08",  # Memorial Day
            "2019-05-09",  # Independence Day
            "2019-06-09",  # Pentecost (Shavuot)
            "2019-08-11",  # Fast Day
            "2019-09-17",  # Election Day
            "2019-09-29",  # Jewish New Year Eve
            "2019-09-30",  # Jewish New Year I
            "2019-10-01",  # Jewish New Year II
            "2019-10-08",  # Yom Kiuppur Eve
            "2019-10-09",  # Yom Kippur
            "2019-10-13",  # Feast of Tabernacles (Sukkoth) Eve
            "2019-10-14",  # Feast of Tabernacles
            "2019-10-20",  # Rejoicing of the Law (Simchat Tora) Eve
            "2019-10-21",  # Rejoicing of the Law
        ]
