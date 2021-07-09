from unittest import TestCase

from exchange_calendars.exchange_calendar_xses import XSESExchangeCalendar

from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class XSESCalendarTestCase(ExchangeCalendarTestBase, TestCase):

    answer_key_filename = "xses"
    calendar_class = XSESExchangeCalendar

    START_BOUND = T("1986-01-01")
    END_BOUND = T("2021-12-31")

    # Singapore stock exchange is open from 9am to 5pm
    # (for now, ignoring lunch break)
    MAX_SESSION_HOURS = 8

    HAVE_EARLY_CLOSES = False

    def test_normal_year(self):
        expected_holidays_2017 = [
            T("2017-01-02"),
            T("2017-01-30"),
            T("2017-04-14"),
            T("2017-05-01"),
            T("2017-05-10"),
            T("2017-06-26"),
            T("2017-08-09"),
            T("2017-09-01"),
            T("2017-10-18"),
            T("2017-12-25"),
        ]

        for session_label in expected_holidays_2017:
            self.assertNotIn(session_label, self.calendar.all_sessions)
