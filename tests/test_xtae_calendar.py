from unittest import TestCase

import pandas as pd

from exchange_calendars.exchange_calendar_xtae import XTAEExchangeCalendar
from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class XTAECalendarTestCase(ExchangeCalendarTestBase, TestCase):

    SESSION_WITHOUT_BREAK = T("2019-06-12")

    # Custom values for start/end test, needed due to XTAE-specific weekmask.
    TEST_START_END_FIRST = T("2010-01-02")
    TEST_START_END_LAST = T("2010-01-09")
    TEST_START_END_EXPECTED_FIRST = T("2010-01-03")
    TEST_START_END_EXPECTED_LAST = T("2010-01-07")

    # XTAE doesn't have early closes.
    HAVE_EARLY_CLOSES = False

    MINUTE_INDEX_TO_SESSION_LABELS_START = T("2019-01-07")
    MINUTE_INDEX_TO_SESSION_LABELS_END = T("2019-04-07")

    DAYLIGHT_SAVINGS_DATES = ["2019-03-31", "2019-10-27"]

    answer_key_filename = "xtae"
    calendar_class = XTAEExchangeCalendar

    # Longest session is from 9:59:00 to 17:15:00, theoretically. Since
    # open/close times are randomised by 60 seconds, 7.25 should be very close
    # to the average case.
    MAX_SESSION_HOURS = 7.25

    def test_2019(self):
        expected_holidays_2019 = [
            # Purim
            pd.Timestamp("2019-03-21", tz="Asia/Jerusalem"),
            # Election Day
            pd.Timestamp("2019-04-09", tz="Asia/Jerusalem"),
            # Passover II Eve
            pd.Timestamp("2019-04-25", tz="Asia/Jerusalem"),
            # Passover II
            pd.Timestamp("2019-04-26", tz="Asia/Jerusalem"),
            # Memorial Day
            pd.Timestamp("2019-05-08", tz="Asia/Jerusalem"),
            # Independence Day
            pd.Timestamp("2019-05-09", tz="Asia/Jerusalem"),
            # Pentecost (Shavuot)
            pd.Timestamp("2019-06-09", tz="Asia/Jerusalem"),
            # Fast Day
            pd.Timestamp("2019-08-11", tz="Asia/Jerusalem"),
            # Election Day
            pd.Timestamp("2019-09-17", tz="Asia/Jerusalem"),
            # Jewish New Year Eve
            pd.Timestamp("2019-09-29", tz="Asia/Jerusalem"),
            # Jewish New Year I
            pd.Timestamp("2019-09-30", tz="Asia/Jerusalem"),
            # Jewish New Year II
            pd.Timestamp("2019-10-01", tz="Asia/Jerusalem"),
            # Yom Kiuppur Eve
            pd.Timestamp("2019-10-08", tz="Asia/Jerusalem"),
            # Yom Kippur
            pd.Timestamp("2019-10-09", tz="Asia/Jerusalem"),
            # Feast of Tabernacles (Sukkoth) Eve
            pd.Timestamp("2019-10-13", tz="Asia/Jerusalem"),
            # Feast of Tabernacles
            pd.Timestamp("2019-10-14", tz="Asia/Jerusalem"),
            # Rejoicing of the Law (Simchat Tora) Eve
            pd.Timestamp("2019-10-20", tz="Asia/Jerusalem"),
            # Rejoicing of the Law
            pd.Timestamp("2019-10-21", tz="Asia/Jerusalem"),
        ]

        for session_label in expected_holidays_2019:
            self.assertNotIn(session_label, self.calendar.all_sessions)
