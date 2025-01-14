from datetime import date

import pandas as pd
import pytest

from exchange_calendars.exchange_calendar_xkrx import XKRXExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class TestXKRXCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XKRXExchangeCalendar

    @pytest.fixture
    def start_bound(self):
        yield T("1956-01-01")

    @pytest.fixture
    def end_bound(self):
        yield T("2050-12-31")

    @pytest.fixture
    def max_session_hours(self):
        # Korea exchange is open from 9am to 3:30pm
        yield 6.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2017
            "2017-01-27",
            "2017-01-30",
            "2017-03-01",
            "2017-05-01",
            "2017-05-03",
            "2017-05-05",
            "2017-05-09",
            "2017-06-06",
            "2017-08-15",
            "2017-10-02",
            "2017-10-03",
            "2017-10-04",
            "2017-10-05",
            "2017-10-06",
            "2017-10-09",
            "2017-12-25",
            "2017-12-29",
            #
            "2010-06-06",  # Memorial Day on Sunday
            #
            # Chuseok holidays falling on a weekend and subsequently made up.
            "2014-09-10",  # falls on Sunday, made up following Wednesday
            "2015-09-29",  # falls on Saturday, made up following Tuesday
            "2017-10-06",
            #
            "2013-10-09",  # Hangeul_day, observance commenced this year
            #
            # Revised alternate holiday rule
            # Since 2021-08-04, the alternative holiday rule, which previously
            # applied to Children's Day only, now also applies to the followings:
            #  - Independence Movement Day (03-01)
            #  - National Liberation Day (08-15)
            #  - Korean National Foundation Day (10-03)
            #  - Hangul Proclamation Day (10-09)
            # National Liberation Day on Sunday
            # so the next monday becomes alternative holiday
            "2021-08-16",
            # Korean National Foundation Day on Sunday
            # so the next monday becomes alternative holiday
            "2021-10-04",
            # Hangul Proclamation Day on Saturday
            # so the next monday becomes alternative holiday
            "2021-10-11",
            # korean thanks giving day on sunday
            # so the next monday becomes alternative holiday
            "2022-09-12",
            # Hangul Proclamation Day on Saturday
            # so the next monday becomes alternative holiday
            "2022-10-10",
            # Buddha's birthday was on 27th May (Saturday),
            # so the next monday becomes alternative holiday
            "2023-05-29",
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend and are not made up. Ensure surrounding
            # days are not holidays.
            # National Foundation Day on a Saturday, so check
            # Friday and Monday surrounding it
            "2015-10-02",
            "2015-10-05",
            # Christmas Day on a Saturday
            # Same as Foundation Day idea
            "2010-12-24",
            "2010-12-27",
            #
            "2012-10-09",  # Hangeul_day, last year before observance commenced.
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            # Temporary Public Holiday (Added to create a 6-day long holiday period)
            "2025-01-27",
        ]

    # TODO Issue #94
    def test_late_opens(self, default_calendar, late_opens):
        # overrides base to mark as xfail
        msg = "Calendar has late opens although `late_opens` is empty. Issue #94"
        pytest.xfail(msg)

    # Calendar-specific tests

    def test_historical_regular_holidays_fall_into_precomputed_holidays(
        self,
        default_calendar,
    ):
        cal = default_calendar
        precomputed = pd.DatetimeIndex(cal.adhoc_holidays)
        # precomputed holidays should not include weekends (saturday, sunday)
        assert (precomputed.weekday < 5).all()

        regular = cal.regular_holidays.holidays(
            precomputed.min(),
            pd.Timestamp("2021-08-15"),
            return_name=True,
        )

        # filter non weekend generated holidays
        non_weekend_regular = regular[regular.index.weekday < 5]

        # regular holidays should generally fall into one of the precomputed holidays
        # except the future holidays that are not precomputed yet
        bv = non_weekend_regular.index.isin(precomputed)
        assert bv.all(), f"missing holidays = \n{non_weekend_regular[~bv]}"

    def test_feb_29_2022_in_lunar_calendar(self, default_calendar):
        # This test asserts that the following does not throw an exception.
        default_calendar.regular_holidays.holidays(date(2022, 3, 31), date(2022, 3, 31))
