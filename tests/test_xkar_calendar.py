import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xkar import XKARExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXKARCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    @classmethod
    def calendar_cls(cls):
        yield XKARExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        yield 5.967

    @pytest.fixture
    def regular_holidays_sample(self):
        # iqbal day observed until 2014 (last year of observance 2013)
        yield [f"{year}-11-09" for year in range(2002, 2014)]

    @pytest.fixture
    def non_holidays_sample(self):
        # iqbal day not observed from 2014
        yield [
            f"{year}-11-09"
            for year in range(2014, 2019)
            if pd.Timestamp(f"{year}-11-09").weekday() not in (5, 6)
        ]

    @pytest.mark.parametrize(
        "year, holidays",
        [
            # https://www.psx.com.pk/psx/exchange/general/calendar-holidays
            (
                2019,
                [
                    "2019-02-05",  # Kashmir Day
                    "2019-03-23",  # Pakistan Day
                    "2019-05-01",  # Labour Day
                    "2019-05-31",  # Juma-Tul-Wida
                    "2019-06-04",  # [NOTE: not included on the website]
                    "2019-06-05",  # Eid-ul-Fitr
                    "2019-06-06",  # Eid-ul-Fitr
                    "2019-06-07",  # Eid-ul-Fitr
                    "2019-08-12",  # Eid-ul-Azha
                    "2019-08-13",  # Eid-ul-Azha
                    "2019-08-14",  # Independence Day
                    "2019-08-15",  # Eid-ul-Azha
                    "2019-09-09",  # Muharram (Ashura)
                    "2019-09-10",  # Muharram (Ashura)
                    "2019-11-10",  # Eid Milad-un-Nabi (SAW)
                    "2019-12-25",  # Birthday of Quaid-e-Azam & Christmas
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
