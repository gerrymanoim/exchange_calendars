from __future__ import annotations
from datetime import time
from unittest import TestCase
from collections import abc

import pytest
import pandas as pd
from pytz import UTC

from exchange_calendars.exchange_calendar_xhkg import XHKGExchangeCalendar

from .test_exchange_calendar import (
    ExchangeCalendarTestBase,
    ExchangeCalendarTestBaseProposal,
)
from .test_utils import T


class XHKGCalendarTestCase(ExchangeCalendarTestBase, TestCase):

    answer_key_filename = "xhkg"
    calendar_class = XHKGExchangeCalendar

    START_BOUND = T("1960-01-01")
    END_BOUND = T("2049-12-31")
    HAVE_BREAKS = True
    SESSION_WITH_BREAK = pd.Timestamp("2018-12-13", tz="UTC")
    SESSION_WITHOUT_BREAK = pd.Timestamp("2018-12-31", tz="UTC")

    MAX_SESSION_HOURS = 6.5

    # Asia/Hong_Kong does not have daylight savings
    DAYLIGHT_SAVINGS_DATES = []

    def test_session_break(self):
        # Test that the calendar correctly reports itself as closed during
        # session break
        normal_minute = pd.Timestamp("2003-01-27 03:30:00")
        break_start_minute = pd.Timestamp("2003-01-27 04:00:00")
        mid_break_minute = pd.Timestamp("2003-01-27 04:30:00")
        break_end_minute = pd.Timestamp("2003-01-27 05:00:00")

        self.assertTrue(self.calendar.is_open_on_minute(normal_minute))
        self.assertTrue(self.calendar.is_open_on_minute(break_start_minute))
        self.assertFalse(self.calendar.is_open_on_minute(mid_break_minute))
        self.assertTrue(self.calendar.is_open_on_minute(break_end_minute))
        # Make sure that ignoring breaks indicates the exchange is open
        self.assertTrue(
            self.calendar.is_open_on_minute(mid_break_minute, ignore_breaks=True)
        )

        current_session_label = self.calendar.minute_to_session_label(
            normal_minute, direction="none"
        )
        self.assertEqual(
            current_session_label,
            self.calendar.minute_to_session_label(
                mid_break_minute, direction="previous"
            ),
        )
        self.assertEqual(
            current_session_label,
            self.calendar.minute_to_session_label(mid_break_minute, direction="next"),
        )

    def test_lunar_new_year_2003(self):
        # NOTE: Lunar Month 12 2002 is the 12th month of the lunar year that
        # begins in 2002; this month actually takes place in January 2003.

        # Lunar Month 12 2002
        #   January-January
        # Su Mo Tu We Th Fr Sa
        #                 3  4
        #  5  6  7  8  9 10 11
        # 12 13 14 15 16 17 18
        # 19 20 21 22 23 24 25
        # 26 27 28 29 30 31

        #  Lunar Month 1 2003
        #    February-March
        # Su Mo Tu We Th Fr Sa
        #                    1
        #  2  3  4  5  6  7  8
        #  9 10 11 12 13 14 15
        # 16 17 18 19 20 21 22
        # 23 24 25 26 27 28  1
        #  2

        start_session = pd.Timestamp("2003-01-27", tz=UTC)
        end_session = pd.Timestamp("2003-02-28", tz=UTC)
        sessions = self.calendar.sessions_in_range(start_session, end_session)

        holidays = pd.to_datetime(
            # prior to 2011, lunar new years eve is a holiday if new years is
            # a Saturday
            ["2003-01-31", "2003-02-03"],
            utc=True,
        )
        for holiday in holidays:
            self.assertNotIn(holiday, sessions)

    def test_lunar_new_year_2018(self):
        # NOTE: Lunar Month 12 2017 is the 12th month of the lunar year that
        # begins in 2017; this month actually takes place in January and
        # February 2018.

        # Lunar Month 12 2017
        #   January-February
        # Su Mo Tu We Th Fr Sa
        #          17 18 19 20
        # 21 22 23 24 25 26 27
        # 28 29 30 31  1  2  3
        #  4  5  6  7  8  9 10
        # 11 12 13 14 15

        #  Lunar Month 1 2018
        #    February-March
        # Su Mo Tu We Th Fr Sa
        #                16 17
        # 18 19 20 21 22 23 24
        # 25 26 27 28  1  2  3
        #  4  5  6  7  8  9 10
        # 11 12 13 14 15 16

        start_session = pd.Timestamp("2018-02-12", tz=UTC)
        end_session = pd.Timestamp("2018-03-15", tz=UTC)
        closes = self.calendar.session_closes_in_range(
            start_session,
            end_session,
        )

        full_holidays = pd.to_datetime(
            ["2018-02-16", "2018-02-19"],
            utc=True,
        )
        for holiday in full_holidays:
            self.assertNotIn(holiday, closes.index)

        self.assertEqual(
            closes.loc["2018-02-15"],
            pd.Timestamp("2018-02-15 12:00", tz="Asia/Hong_Kong"),
        )

    def test_full_year_with_lunar_leap_year(self):
        """2017 Lunar month 6 will be a leap month (double length). This
        affects when all the lunisolar holidays after the 6th month occur.
        """
        #                         Gregorian Calendar
        #                                2017
        #
        #        January               February                 March
        # Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa
        #  1  2  3  4  5  6  7             1  2  3  4             1  2  3  4
        #  8  9 10 11 12 13 14    5  6  7  8  9 10 11    5  6  7  8  9 10 11
        # 15 16 17 18 19 20 21   12 13 14 15 16 17 18   12 13 14 15 16 17 18
        # 22 23 24 25 26 27 28   19 20 21 22 23 24 25   19 20 21 22 23 24 25
        # 29 30 31               26 27 28               26 27 28 29 30 31
        #
        #         April                   May                   June
        # Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa
        #                    1       1  2  3  4  5  6                1  2  3
        #  2  3  4  5  6  7  8    7  8  9 10 11 12 13    4  5  6  7  8  9 10
        #  9 10 11 12 13 14 15   14 15 16 17 18 19 20   11 12 13 14 15 16 17
        # 16 17 18 19 20 21 22   21 22 23 24 25 26 27   18 19 20 21 22 23 24
        # 23 24 25 26 27 28 29   28 29 30 31            25 26 27 28 29 30
        # 30
        #         July                  August                September
        # Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa
        #                    1          1  2  3  4  5                   1  2
        #  2  3  4  5  6  7  8    6  7  8  9 10 11 12    3  4  5  6  7  8  9
        #  9 10 11 12 13 14 15   13 14 15 16 17 18 19   10 11 12 13 14 15 16
        # 16 17 18 19 20 21 22   20 21 22 23 24 25 26   17 18 19 20 21 22 23
        # 23 24 25 26 27 28 29   27 28 29 30 31         24 25 26 27 28 29 30
        # 30 31
        #        October               November               December
        # Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa
        #  1  2  3  4  5  6  7             1  2  3  4                   1  2
        #  8  9 10 11 12 13 14    5  6  7  8  9 10 11    3  4  5  6  7  8  9
        # 15 16 17 18 19 20 21   12 13 14 15 16 17 18   10 11 12 13 14 15 16
        # 22 23 24 25 26 27 28   19 20 21 22 23 24 25   17 18 19 20 21 22 23
        # 29 30 31               26 27 28 29 30         24 25 26 27 28 29 30
        #                                               31

        #                           Lunar Calendar
        #                                2017
        #
        #    Lunar Month 1          Lunar Month 2          Lunar Month 3
        #   January-February        February-March          March-April
        # Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa
        #                   28                                28 29 30 31  1
        # 29 30 31  1  2  3  4   26 27 28  1  2  3  4    2  3  4  5  6  7  8
        #  5  6  7  8  9 10 11    5  6  7  8  9 10 11    9 10 11 12 13 14 15
        # 12 13 14 15 16 17 18   12 13 14 15 16 17 18   16 17 18 19 20 21 22
        # 19 20 21 22 23 24 25   19 20 21 22 23 24 25   23 24 25
        #                        26 27
        #
        #    Lunar Month 4          Lunar Month 5         Lunar Month 6(+)
        #      April-May               May-June             June-August
        # Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa
        #          26 27 28 29                  26 27                     24
        # 30  1  2  3  4  5  6   28 29 30 31  1  2  3   25 26 27 28 29 30  1
        #  7  8  9 10 11 12 13    4  5  6  7  8  9 10    2  3  4  5  6  7  8
        # 14 15 16 17 18 19 20   11 12 13 14 15 16 17    9 10 11 12 13 14 15
        # 21 22 23 24 25         18 19 20 21 22 23      16 17 18 19 20 21 22
        #                                               23 24 25 26 27 28 29
        #                                               30 31  1  2  3  4  5
        #                                                6  7  8  9 10 11 12
        #                                               13 14 15 16 17 18 19
        #                                               20 21
        #
        #    Lunar Month 7          Lunar Month 8          Lunar Month 9
        #   August-September      September-October       October-November
        # Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa
        #       22 23 24 25 26            20 21 22 23                  20 21
        # 27 28 29 30 31  1  2   24 25 26 27 28 29 30   22 23 24 25 26 27 28
        #  3  4  5  6  7  8  9    1  2  3  4  5  6  7   29 30 31  1  2  3  4
        # 10 11 12 13 14 15 16    8  9 10 11 12 13 14    5  6  7  8  9 10 11
        # 17 18 19               15 16 17 18 19         12 13 14 15 16 17
        #
        #    Lunar Month 10         Lunar Month 11         Lunar Month 12
        #  November-December       December-January       January-February
        # Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa   Su Mo Tu We Th Fr Sa
        #                   18      18 19 20 21 22 23            17 18 19 20
        # 19 20 21 22 23 24 25   24 25 26 27 28 29 30   21 22 23 24 25 26 27
        # 26 27 28 29 30  1  2   31  1  2  3  4  5  6   28 29 30 31  1  2  3
        #  3  4  5  6  7  8  9    7  8  9 10 11 12 13    4  5  6  7  8  9 10
        # 10 11 12 13 14 15 16   14 15 16               11 12 13 14 15
        # 17
        full_holidays = [
            # New Year's Day (Sunday to Monday observance)
            T("2017-01-02"),
            # Lunar New Year
            T("2017-01-30"),
            T("2017-01-31"),
            # Qingming Festival (based off qingming solar term, not lunar
            # cycle)
            T("2017-04-04"),
            # Good Friday
            T("2017-04-14"),
            # Easter Monday
            T("2017-04-17"),
            # Labour Day
            T("2017-05-01"),
            # Buddha's Birthday (The 8th day of the 4th lunar month)
            T("2017-05-03"),
            # Tuen Ng Festival (also known as Dragon Boat Festival. The 5th day
            # of the 5th lunar month, then Sunday to Monday observance)
            T("2017-05-30"),
            # National Day (Sunday to Monday observance)
            T("2017-10-02"),
            # The day following the Mid-Autumn Festival (Mid-Autumn Festival
            # is the 15th day of the 8th lunar month. This market holiday is
            # next day because the festival is celebrated at night)
            T("2017-10-05"),
            # Christmas Day
            T("2017-12-25"),
            # The day after Christmas
            T("2017-12-25"),
        ]

        half_days = [
            # Lunar New Year's Eve
            T("2017-01-27"),
            # Christmas Eve and New Year's Eve are both Sunday this year
        ]

        start_session = pd.Timestamp("2017-01-02", tz=UTC)
        end_session = pd.Timestamp("2017-12-29", tz=UTC)
        closes = self.calendar.session_closes_in_range(
            start_session,
            end_session,
        )

        for holiday in full_holidays:
            self.assertNotIn(holiday, closes)

        for half_day in half_days:
            close_time = half_day.tz_convert(None).tz_localize(
                "Asia/Hong_Kong"
            ) + pd.Timedelta(hours=12)
            self.assertEqual(close_time, closes[half_day])

        local_time_close = closes.drop(half_days).dt.tz_convert(
            "Asia/Hong_Kong",
        )
        self.assertEqual({time(16)}, set(local_time_close.dt.time))


class TestXHKGCalendarCase(ExchangeCalendarTestBaseProposal):
    @pytest.fixture(scope="class")
    def calendar_class(self) -> abc.Iterator[XHKGExchangeCalendar]:
        yield XHKGExchangeCalendar
