from unittest import TestCase

from exchange_calendars.exchange_calendar_xbom import XBOMExchangeCalendar

from .test_exchange_calendar import ExchangeCalendarTestBase
from .test_utils import T


class XBOMCalendarTestCase(ExchangeCalendarTestBase, TestCase):

    answer_key_filename = "xbom"
    calendar_class = XBOMExchangeCalendar

    START_BOUND = T("1997-01-01")
    END_BOUND = T("2021-12-31")

    # BSE is open from 9:15 am to 3:30 pm
    MAX_SESSION_HOURS = 6.25

    HAVE_EARLY_CLOSES = False

    def test_normal_year(self):
        expected_holidays_2017 = [
            T("2017-01-26"),
            T("2017-02-24"),
            T("2017-03-13"),
            T("2017-04-04"),
            T("2017-04-14"),
            T("2017-05-01"),
            T("2017-06-26"),
            T("2017-08-15"),
            T("2017-08-25"),
            T("2017-10-02"),
            T("2017-10-20"),
            T("2017-12-25"),
        ]

        for session_label in expected_holidays_2017:
            self.assertNotIn(session_label, self.calendar.all_sessions)
