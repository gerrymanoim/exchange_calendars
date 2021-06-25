from unittest import TestCase

import pandas as pd
from pytz import UTC

from exchange_calendars.exchange_calendar_xshg import XSHGExchangeCalendar

from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class XSHGCalendarTestCase(ExchangeCalendarTestBase, TestCase):

    answer_key_filename = "xshg"
    calendar_class = XSHGExchangeCalendar

    START_BOUND = T("1999-01-01")
    END_BOUND = T("2025-12-31")

    # Shanghai stock exchange is open from 9:30 am to 3pm
    # (for now, ignoring lunch break)
    MAX_SESSION_HOURS = 5.5

    HAVE_EARLY_CLOSES = False

    MINUTE_INDEX_TO_SESSION_LABELS_END = pd.Timestamp("2011-04-07", tz=UTC)

    def test_normal_year(self):
        expected_holidays_2017 = [
            T("2017-01-02"),
            T("2017-01-27"),
            T("2017-01-30"),
            T("2017-01-31"),
            T("2017-02-01"),
            T("2017-02-02"),
            T("2017-04-03"),
            T("2017-04-04"),
            T("2017-05-01"),
            T("2017-05-29"),
            T("2017-05-30"),
            T("2017-10-02"),
            T("2017-10-03"),
            T("2017-10-04"),
            T("2017-10-05"),
            T("2017-10-06"),
        ]

        for session_label in expected_holidays_2017:
            self.assertNotIn(session_label, self.calendar.all_sessions)
