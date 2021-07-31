from __future__ import annotations
from unittest import TestCase
from collections import abc

import pytest
import pandas as pd
from pytz import UTC

from exchange_calendars.exchange_calendar_xlon import XLONExchangeCalendar

from .test_exchange_calendar import (
    ExchangeCalendarTestBase,
    ExchangeCalendarTestBaseProposal,
)


class XLONCalendarTestCase(ExchangeCalendarTestBase, TestCase):

    answer_key_filename = "xlon"
    calendar_class = XLONExchangeCalendar

    # The XLON exchange is open from 8:00 am to 4:30 pm.
    MAX_SESSION_HOURS = 8.5

    def test_2012(self):
        expected_holidays_2012 = [
            pd.Timestamp("2012-01-02", tz=UTC),  # New Year's observed
            pd.Timestamp("2012-04-06", tz=UTC),  # Good Friday
            pd.Timestamp("2012-04-09", tz=UTC),  # Easter Monday
            pd.Timestamp("2012-05-07", tz=UTC),  # May Day
            pd.Timestamp("2012-06-04", tz=UTC),  # Spring Bank Holiday
            pd.Timestamp("2012-08-27", tz=UTC),  # Summer Bank Holiday
            pd.Timestamp("2012-12-25", tz=UTC),  # Christmas
            pd.Timestamp("2012-12-26", tz=UTC),  # Boxing Day
        ]

        for session_label in expected_holidays_2012:
            self.assertNotIn(session_label, self.calendar.all_sessions)

        early_closes_2012 = [
            pd.Timestamp("2012-12-24", tz=UTC),  # Christmas Eve
            pd.Timestamp("2012-12-31", tz=UTC),  # New Year's Eve
        ]

        for early_close_session_label in early_closes_2012:
            self.assertIn(early_close_session_label, self.calendar.early_closes)

    def test_special_holidays(self):
        # Spring Bank 2002
        self.assertNotIn(
            pd.Timestamp("2002-06-03", tz=UTC),
            self.calendar.all_sessions,
        )
        # Golden Jubilee
        self.assertNotIn(
            pd.Timestamp("2002-06-04", tz=UTC),
            self.calendar.all_sessions,
        )
        # Royal Wedding
        self.assertNotIn(
            pd.Timestamp("2011-04-29", tz=UTC),
            self.calendar.all_sessions,
        )
        # Spring Bank 2012
        self.assertNotIn(
            pd.Timestamp("2012-06-04", tz=UTC),
            self.calendar.all_sessions,
        )
        # DiamondJubilee
        self.assertNotIn(
            pd.Timestamp("2012-06-05", tz=UTC),
            self.calendar.all_sessions,
        )
        # VE Day
        self.assertNotIn(pd.Timestamp("2020-05-08", tz=UTC), self.calendar.all_sessions)

    def test_special_non_holidays(self):
        # May Bank Holiday was instead observed on VE Day
        # in 2020.
        self.assertIn(
            pd.Timestamp("2020-05-04", tz=UTC),
            self.calendar.all_sessions,
        )

    def test_half_days(self):

        half_days = [
            # In Dec 2010, Christmas Eve and NYE are on Friday,
            # so they should be half days
            pd.Timestamp("2010-12-24", tz="Europe/London"),
            pd.Timestamp("2010-12-31", tz="Europe/London"),
            # In Dec 2011, Christmas Eve and NYE were both on a Saturday,
            # so the preceding Fridays (the 23rd and 30th) are half days
            pd.Timestamp("2011-12-23", tz="Europe/London"),
            pd.Timestamp("2011-12-30", tz="Europe/London"),
        ]

        for half_day in half_days:
            half_day_close_time = self.calendar.next_close(half_day)
            self.assertEqual(
                half_day_close_time, half_day + pd.Timedelta(hours=12, minutes=30)
            )


class TestXLONCalendarCase(ExchangeCalendarTestBaseProposal):
    @pytest.fixture(scope="class")
    def calendar_class(self) -> abc.Iterator[XLONExchangeCalendar]:
        yield XLONExchangeCalendar
