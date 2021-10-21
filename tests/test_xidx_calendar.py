import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xidx import XIDXExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXIDXCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XIDXExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 6 + (5 / 6)

    # Calendar-specific tests

    def test_trading_days(self, default_calendar):
        cal = default_calendar
        # Data obtained from https://www.idx.co.id/en-us/news/trading-holiday/
        expected_trading_days = {
            # year: (trading days in year, [trading days in each month])
            2016: (246, [20, 20, 21, 21, 20, 22, 16, 22, 21, 21, 22, 20]),
            2017: (238, [21, 19, 22, 17, 20, 15, 21, 22, 19, 22, 22, 18]),
            # XXX: The website says only 21 trading days for July 2018.
            2018: (240, [22, 19, 21, 21, 20, 13, 22, 21, 19, 23, 21, 18]),
            2019: (245, [22, 19, 20, 19, 21, 15, 23, 22, 21, 23, 21, 19]),
            2020: (244, [22, 20, 21, 21, 14, 21, 22, 19, 22, 21, 21, 20]),
        }
        for year, (total_days, monthly_days) in expected_trading_days.items():
            assert sum(monthly_days) == total_days  # Sanity check

            sessions = cal.sessions[cal.sessions.year == year]
            assert total_days == len(sessions), year

    @pytest.mark.parametrize(
        "year, holidays",
        [
            (
                2019,
                [
                    "2019-01-01",  # New Year 2019
                    "2019-02-05",  # Chinese New Year 2570 Kongzili
                    "2019-03-07",  # Hindu Saka New Year 1941
                    "2019-04-03",  # Isra Mikraj of Prophet Muhammad SAW
                    "2019-04-17",  # Indonesia General Election 2019
                    "2019-04-19",  # Good Friday
                    "2019-05-01",  # Labor Day
                    "2019-05-30",  # Ascension Day Of Jesus Christ
                    "2019-06-03",  # Commemoration of Eid ul-Fitr 1440 Hijriyah
                    "2019-06-04",  # Commemoration of Eid ul-Fitr 1440 Hijriyah
                    "2019-06-05",  # Eid ul-Fitr 1440 Hijriyah
                    "2019-06-06",  # Eid ul-Fitr 1440 Hijriyah
                    "2019-06-07",  # Commemoration of Eid ul-Fitr 1440 Hijriyah
                    "2019-12-24",  # Commemoration Of Christmas Day
                    "2019-12-25",  # Christmas Day
                    "2019-12-31",  # Trading Holiday
                ],
            ),
            (
                2018,
                [
                    "2018-01-01",  # New Year 2018
                    "2018-02-16",  # Chinese New Year 2569 Kongzili
                    "2018-03-17",  # Hindu Saka New Year 1940.
                    "2018-03-30",  # Good Friday
                    "2018-04-14",  # Isra Mikraj of Prophet Muhammad SAW
                    "2018-05-01",  # Labor Day
                    "2018-05-10",  # Ascension Day Of Jesus Christ
                    "2018-05-29",  # Vesak Day 2562
                    "2018-06-01",  # Pancasila Day
                    "2018-06-11",  # Commemoration of Eid ul-Fitr 1439 Hijriyah
                    "2018-06-12",  # Commemoration of Eid ul-Fitr 1439 Hijriyah
                    "2018-06-13",  # Commemoration of Eid ul-Fitr 1439 Hijriyah
                    "2018-06-14",  # Commemoration of Eid ul-Fitr 1439 Hijriyah
                    "2018-06-15",  # Eid ul-Fitr 1440 Hijriyah
                    "2018-06-18",  # Commemoration of Eid ul-Fitr 1439 Hijriyah
                    "2018-06-19",  # Commemoration of Eid ul-Fitr 1439 Hijriyah
                    "2018-08-17",  # Independence Day of Indonesia
                    "2018-08-22",  # Eid al-Adha 1439 Hijriyah
                    "2018-09-11",  # Islamic New Year 1442 Hijriyah
                    "2018-11-20",  # Birth of Prophet Muhammad
                    "2018-12-24",  # Commemoration Of Christmas Day
                    "2018-12-25",  # Christmas Day
                    "2018-12-31",  # Trading Holiday
                ],
            ),
        ],
    )
    def test_holidays_in_year(self, default_calendar, year, holidays):
        cal = default_calendar
        days = pd.date_range(start=f"{year}-01-01", end=f"{year}-12-31", freq="B")
        days = days.strftime("%Y-%m-%d")

        for holiday in holidays:
            # Sanity check
            assert holiday in days or pd.Timestamp(holiday).weekday() in (5, 6)

        for day in days:
            if day in holidays:
                assert not cal.is_session(day)
            else:
                assert cal.is_session(day)
