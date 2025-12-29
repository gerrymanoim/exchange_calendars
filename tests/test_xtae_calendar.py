import pandas as pd
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
            # 2026
            "2026-03-03",  # Purim
            "2026-04-01",  # Passover Eve
            "2026-04-02",  # Passover
            "2026-04-07",  # Passover II Eve
            "2026-04-08",  # Passover II
            "2026-04-21",  # Memorial Day
            "2026-04-22",  # Independence Day
            "2026-05-21",  # Pentecost (Shavuot) Eve
            "2026-05-22",  # Pentecost (Shavuot)
            "2026-07-23",  # Fast Day (Tisha B'Av)
            "2026-09-11",  # Jewish New Year Eve
            "2026-09-13",  # Jewish New Year II
            "2026-09-18",  # Yom Kippur Eve (in lieu)
            "2026-09-20",  # Yom Kippur Eve (on a Sunday)
            "2026-09-21",  # Yom Kippur
            "2026-09-25",  # Sukkoth Eve
            "2026-10-02",  # Simchat Tora Eve
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            # Passover interim days
            # 2019
            "2019-04-21",
            "2019-04-22",
            "2019-04-23",
            "2019-04-24",
            # 2020
            "2020-04-12",  # another Sunday (see 2022 comment...)
            # 2022
            # '2022-04-17' is a Sunday. Including here checks holiday early
            # close takes precedence over sunday early close
            "2022-04-17",
            "2022-04-18",
            "2022-04-19",
            "2022-04-20",
            # 2023
            "2023-04-09",
            "2023-04-10",
            # 2026
            # Passover interim days
            "2026-04-06",
            # Sukkoth interim days
            "2026-09-28",
            "2026-09-29",
            "2026-09-30",
            "2026-10-01",
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=14, minutes=15)

    @pytest.fixture
    def early_closes_weekdays(self):
        return (6,)

    @pytest.fixture
    def early_closes_weekdays_sample(self):
        # From January 5 2026, Fridays will close early at 14:00
        yield [
            "2026-01-09",  # first Friday with early close after change in 2026
            "2026-01-16",  # second Friday with early close after change in 2026
        ]

    @pytest.fixture
    def early_closes_weekdays_sample_time(self):
        yield pd.Timedelta(hours=13, minutes=50)

    @pytest.fixture
    def non_early_closes_sample(self):
        yield [
            # check standard week
            # 2022-08-21 is a regular early close sunday
            # check all other days have regular closes
            "2022-08-17",
            "2022-08-18",
            "2022-08-22",
            "2022-08-23",
        ]

    @pytest.fixture
    def non_early_closes_sample_time(self):
        yield pd.Timedelta(hours=17, minutes=15)


class TestXTAECalendarEarlyCloseSundaysBefore2026(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XTAEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # Longest session is from 9:59:00 to 17:15:00
        yield 7.25 + (1.0 / 60.0)

    @pytest.fixture
    def early_closes_weekdays_sample(self):
        # Before January 5 2026, Sundays will close early at 15:40
        yield [
            "2022-08-21",  # a sunday of a standard week
            "2026-01-04",  # last sunday with early close before change in 2026
        ]

    @pytest.fixture
    def early_closes_weekdays_sample_time(self):
        yield pd.Timedelta(hours=15, minutes=40)
