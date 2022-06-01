import pytest
import pandas as pd

from exchange_calendars.exchange_calendar_xsgo import XSGOExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class TestXSGOCalendar(ExchangeCalendarTestBase):
    @pytest.fixture(scope="class")
    def calendar_cls(self):
        yield XSGOExchangeCalendar

    @pytest.fixture
    def max_session_hours(self):
        # XSGO's longest session occurs when open from 9:30AM to 5:00PM.
        yield 7.5

    @pytest.fixture
    def regular_holidays_sample(self):
        yield [
            # 2019
            "2019-01-01",  # New Year's Day
            "2019-04-19",  # Good Friday
            "2019-05-01",  # Labour Day
            "2019-05-21",  # Navy Day
            "2019-07-16",  # Our Lady of Mount Carmel Day
            "2019-08-15",  # Assumption Day
            "2019-09-18",  # Independence Day
            "2019-09-19",  # Army Day
            "2019-09-20",  # Public Holiday
            "2019-10-31",  # Evangelical Church Day
            "2019-11-01",  # All Saints' Day
            "2017-12-08",  # Immaculate Conception
            "2019-12-25",  # Christmas Day
            "2019-12-31",  # Bank Holiday
            #
            # Saint Peter and Saint Paul Day follows an unusual rule whereby if June
            # 29th falls on a Saturday, Sunday or Monday then the holiday is
            # acknowledged on that day (Sat/Sun observances are not made up later).
            # Otherwise it is observed on the closest Monday to the 29th.
            "2018-07-02",  # 29th a Friday so next Monday is a holiday.
            "2017-06-26",  # 29th a Thursday so previous Monday is a holiday.
            "2016-06-27",  # 29th a Wednesday so previous Monday is a holiday.
            "2015-06-29",  # 29th a Monday so that Monday is a holiday.
            "2010-06-28",  # 29th a Tuesday so previous Monday is a holiday.
            #
            # Dia de la Raza (also known as Columbus Day) follows same rule as Saint
            # Peter and Saint Paul Day described above, albeit centered on October 12th.
            "2018-10-15",  # 12th a Friday so next Monday is a holiday.
            "2017-10-09",  # 12th a Thursday so previous Monday is a holiday.
            "2016-10-10",  # 12th a Wednesday so previous Monday is a holiday.
            "2015-10-12",  # 12th a Monday so that Monday is a holiday.
            "2010-10-11",  # 12th a Tuesday so previous Monday is a holiday.
            #
            # Independence Day and Army Day fall back-to-back on September 18th and
            # 19th. If they happen to fall on a Tue/Wed then the prior Monday is
            # deemed a Public Holiday. If they happen to fall on a Wed/Thu then the
            # following Friday is deemed a Public Holiday.
            "2019-09-20",  # fall on Wed/Thu so following Friday 20th is also a holiday.
            "2018-09-17",  # fall on Tue/Wed so prior Monday 17th is also a holiday.
            #
            # Evangelical Church Day (also known as Halloween) adheres to the
            # following rule: If October 31st falls on a Tuesday, it is observed the
            # preceding Friday. If it falls on a Wednesday, it is observed the next
            # Friday. If it falls on Thu, Fri, Sat, Sun, or Mon then the holiday is
            # acknowledged that day.
            "2019-10-31",  # 31st is a Thursday, so that Thursday is a holiday.
            "2018-11-02",  # 31st is a Wednesday, so following Friday is a holiday.
            "2017-10-27",  # 31st is a Tuesday, so previous Friday is a holiday.
            "2016-10-31",  # 31st is a Monday, so that Monday is a holiday.
            "2014-10-31",  # 31st is a Friday, so that Friday is a holiday.
        ]

    @pytest.fixture
    def adhoc_holidays_sample(self):
        yield [
            "2010-09-17",  # Bicentennial Celebration.
            "2010-09-20",  # Bicentennial Celebration.
            # For whatever reason New Year's Day, which was a Sunday, was
            # observed on Monday this one year.
            "2017-01-02",
            "2017-04-19",  # Census Day.
            "2018-01-16",  # Pope Visit.
        ]

    @pytest.fixture
    def non_holidays_sample(self):
        yield [
            # Holidays that fall on a weekend and are not made up. Ensure surrounding
            # days are not holidays.
            # Bank Holiday on Saturday, December 31st and  New Year's Day on
            # Sunday, January 1st.
            "2011-12-30",
            "2012-01-02",
            # Labour Day on Sunday, May 1st.
            "2016-04-29",
            "2016-05-02",
            # Navy Day on Sunday, May 21st.
            "2017-05-19",
            "2017-05-22",
            # Saint Peter and Saint Paul Day on Saturday, June 29th.
            "2019-06-28",
            "2019-07-01",
            # Our Lady of Mount Carmel Day on Sunday, July 16th.
            "2017-07-14",
            "2017-07-17",
            # Assumption Day on Saturday, August 15th.
            "2015-08-14",
            "2015-08-17",
            # In 2004 Independence Day and Army Day fell on a Saturday and
            # Sunday, so the surrounding Friday and Monday should both be
            # trading days.
            "2004-09-17",
            "2004-09-20",
            # Dia de la Raza on Saturday, October 12th.
            "2019-10-11",
            "2019-10-14",
            # Evangelical Church Day (Halloween) and All Saints' Day fall on a
            # Saturday and Sunday, so Friday the 30th and Monday the 2nd should
            # both be trading days.
            "2015-10-30",
            "2015-11-02",
            # Immaculate Conception on Sunday, December 8th.
            "2019-12-06",
            "2019-12-09",
            # Christmas on a Sunday.
            "2016-12-23",
            "2016-12-26",
            #
            # Saint Peter and Saint Paul Day follows an unusual rule whereby if June
            # 29th falls on a Saturday, Sunday or Monday then the holiday is
            # acknowledged on that day (Sat/Sun observances are not made up later).
            # Otherwise it is observed on the closest Monday to the 29th.
            "2014-06-30",  # 29th is a Sunday, so closest Monday is not a holiday
            "2019-07-01",  # 29th a Saturday, so closest Monday a trading day
            #
            # # Dia de la Raza (also known as Columbus Day) follows same rule as Saint
            # Peter and Saint Paul Day described above, albeit centered on October 12th.
            "2014-10-13",  # 12th is a Sunday, so closest Monday is not a holiday
            "2019-10-14",  # 12th a Saturday, so closest Monday a trading day
        ]

    @pytest.fixture
    def early_closes_sample(self):
        yield [
            "2019-04-18",  # Maundy Thursday
            "2019-09-17",  # Day before Independence Day
        ]

    @pytest.fixture
    def early_closes_sample_time(self):
        yield pd.Timedelta(hours=13, minutes=30)

    # Calendar-specific tests

    def test_additional_early_closes_sample(self, default_calendar):
        # additional test necessray as early close time here (12:30 local)
        # is different to that for sessions of `early_closes_sample` (13:30 local).
        cal = default_calendar
        early_closes = [
            "2019-12-24",  # Christmas Eve
            "2019-12-30",  # Day before Bank Holiday
        ]

        for date in early_closes:
            assert T(date) in cal.early_closes

        tz = default_calendar.tz
        early_closes_time = pd.Timedelta(hours=12, minutes=30)
        offset = pd.Timedelta(cal.close_offset, "D") + early_closes_time
        for date in early_closes:
            early_close = cal.closes[date].tz_convert(tz)
            expected = pd.Timestamp(date, tz=tz) + offset
            assert early_close == expected

    def test_close_time_change(self, default_calendar):
        """Test twice annual change to close time."""
        # Evert March close time changes from 5:00PM to 4:00PM and every
        # November changes back from 4:00PM to 5:00PM (all local times).
        dates_closes = (
            ("2019-02-28", "2019-02-28 17:00"),
            ("2019-03-01", "2019-03-01 16:00"),
            ("2019-10-30", "2019-10-30 16:00"),
            ("2019-11-04", "2019-11-04 17:00"),
        )
        cal = default_calendar
        for date, close in dates_closes:
            cal.closes[date] == pd.Timestamp(close, tz=cal.tz)
