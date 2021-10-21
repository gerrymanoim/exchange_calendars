import pytest

import pandas as pd

from exchange_calendars.exchange_calendar_xjse import XJSEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase


class TestXJSECalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XJSEExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # The JSE is open from 09:00 to 17:00.
        yield 8

    def test_no_weekend_sessions(self, default_calendar):
        bv = default_calendar.sessions.weekday.isin((5, 6))
        assert default_calendar.sessions[bv].empty

    @pytest.mark.parametrize(
        "year, holidays",
        [
            (
                2019,
                [
                    "2019-01-01",  # New Year's Day
                    "2019-03-21",  # Human Rights Day
                    "2019-04-19",  # Good Friday
                    "2019-04-22",  # Family Day
                    "2019-04-27",  # Freedom Day (falls on Saturday, not made up)
                    "2019-05-01",  # Workers' Day
                    "2019-05-08",  # Election Day (ad-hoc)
                    "2019-06-16",  # Youth Day
                    "2019-06-17",  # Youth Day (Monday make-up)
                    "2019-08-09",  # National Women's Day
                    "2019-09-24",  # Heritage Day
                    "2019-12-16",  # Day of Reconciliation
                    "2019-12-25",  # Christmas
                    "2019-12-26",  # Day of Goodwill
                ],
            ),
            (
                2018,
                [
                    "2018-01-01",  # New Year's Day
                    "2018-03-21",  # Human Rights Day
                    "2018-03-30",  # Good Friday
                    "2018-04-02",  # Family Day
                    "2018-04-27",  # Freedom Day
                    "2018-05-01",  # Workers' Day
                    "2018-06-16",  # Youth Day (falls on Saturday, not made up)
                    "2018-08-09",  # National Women's Day
                    "2018-09-24",  # Heritage Day
                    "2018-12-16",  # Day of Reconciliation
                    "2018-12-17",  # Day of Reconciliation (Monday make-up)
                    "2018-12-25",  # Christmas
                    "2018-12-26",  # Day of Goodwill
                ],
            ),
            (
                2016,
                [
                    "2016-01-01",  # New Year's Day
                    "2016-03-21",  # Human Rights Day
                    "2016-03-25",  # Good Friday
                    "2016-03-28",  # Family Day
                    "2016-04-27",  # Freedom Day
                    "2016-05-01",  # Workers' Day
                    "2016-05-02",  # Workers' Day (Monday make-up)
                    "2016-06-16",  # Youth Day
                    "2016-08-03",  # Election Day
                    "2016-08-09",  # National Women's Day
                    "2016-09-24",  # Heritage Day (falls on Saturday, not made up)
                    "2016-12-16",  # Day of Reconciliation
                    "2016-12-25",  # Christmas
                    "2016-12-26",  # Christmas (Monday make-up)
                    "2016-12-27",  # Day of Goodwill (Ad-hoc make-up observance)
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
