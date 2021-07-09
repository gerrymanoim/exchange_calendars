from unittest import TestCase

import pytest
import pandas as pd
from pytz import UTC

from exchange_calendars.exchange_calendar_xkls import XKLSExchangeCalendar

from .test_exchange_calendar import NoDSTExchangeCalendarTestBase


class XKLSCalendarTestCase(NoDSTExchangeCalendarTestBase, TestCase):

    answer_key_filename = "xkls"
    calendar_class = XKLSExchangeCalendar

    # The XKLS is open from 9AM to 5PM
    MAX_SESSION_HOURS = 8.0

    @pytest.mark.xfail(reason=("See issue #33"))
    def test_start_bound(self):
        super().test_start_bound()

    @pytest.mark.xfail(reason=("See issue #33"))
    def test_end_bound(self):
        super().test_end_bound()

    def test_regular_holidays(self):
        all_sessions = self.calendar.all_sessions

        expected_holidays = [
            pd.Timestamp("2019-01-01", tz=UTC),  # New Year's Day
            pd.Timestamp("2019-01-21", tz=UTC),  # Thaipusam
            pd.Timestamp("2019-02-01", tz=UTC),  # Federal Territory Day
            pd.Timestamp("2019-02-05", tz=UTC),  # Chinese New Year Day 1
            pd.Timestamp("2019-02-06", tz=UTC),  # Chinese New Year Day 2
            pd.Timestamp("2019-05-01", tz=UTC),  # Labour Day
            pd.Timestamp("2019-05-20", tz=UTC),  # Wesak Day
            pd.Timestamp("2019-05-22", tz=UTC),  # Nuzul Al Quran
            pd.Timestamp("2019-06-05", tz=UTC),  # Eid al Fitr Day 1
            pd.Timestamp("2019-06-06", tz=UTC),  # Eid al Fitr Day 2
            pd.Timestamp("2019-08-12", tz=UTC),  # Eid al Adha
            pd.Timestamp("2018-08-31", tz=UTC),  # National Day
            pd.Timestamp("2019-09-02", tz=UTC),  # Muharram
            pd.Timestamp("2019-09-16", tz=UTC),  # Malaysia Day
            pd.Timestamp("2019-10-28", tz=UTC),  # Deepavali
            pd.Timestamp("2018-11-20", tz=UTC),  # Birthday of Muhammad
            pd.Timestamp("2019-12-25", tz=UTC),  # Christmas Day
        ]

        for holiday_label in expected_holidays:
            self.assertNotIn(holiday_label, all_sessions)

    def test_holidays_fall_on_saturdays(self):
        all_sessions = self.calendar.all_sessions

        # Holidays falling on Saturdays are not made up, so verify surrounding
        # Friday/Monday are trading days.
        expected_sessions = [
            # New Year's Day on Saturday, Jan 1st.
            #   2010-12-31 is an adhoc holiday
            pd.Timestamp("2010-12-30", tz=UTC),
            pd.Timestamp("2011-01-03", tz=UTC),
            # Labour Day on Saturday, May 1st.
            pd.Timestamp("2010-04-30", tz=UTC),
            pd.Timestamp("2010-05-03", tz=UTC),
            # Nuzul Al-Quran on Saturday, Jul 4th.
            pd.Timestamp("2017-07-03", tz=UTC),
            pd.Timestamp("2017-07-06", tz=UTC),
            # National Day on Saturday, Aug 31st.
            #   2019-09-02 is Muharram
            pd.Timestamp("2019-08-30", tz=UTC),
            pd.Timestamp("2019-09-03", tz=UTC),
            # Muharram on Saturday, Oct 25th.
            pd.Timestamp("2014-10-24", tz=UTC),
            pd.Timestamp("2014-10-27", tz=UTC),
            # Malaysia Day on Saturday, Sep 16th.
            pd.Timestamp("2017-09-15", tz=UTC),
            pd.Timestamp("2017-09-18", tz=UTC),
            # Birthday of Prophet Muhammad on Saturday, Mar 31st.
            pd.Timestamp("2007-03-30", tz=UTC),
            pd.Timestamp("2007-04-02", tz=UTC),
            # Christmas Day on Saturday, Dec 25th.
            pd.Timestamp("2010-12-24", tz=UTC),
            pd.Timestamp("2010-12-27", tz=UTC),
            # Thaipusam on Saturday, Feb 8th.
            pd.Timestamp("2020-02-07", tz=UTC),
            pd.Timestamp("2020-02-10", tz=UTC),
        ]

        for session_label in expected_sessions:
            self.assertIn(session_label, all_sessions)

    def test_sunday_to_monday(self):
        all_sessions = self.calendar.all_sessions

        # Holidays falling on Sundays are made up on the next Monday.
        expected_holidays = [
            pd.Timestamp("2012-01-02", tz=UTC),  # New Year's Day
            pd.Timestamp("2015-02-02", tz=UTC),  # Federal Territory Day
            pd.Timestamp("2017-01-30", tz=UTC),  # Chinese New Year 2nd Day
            pd.Timestamp("2016-05-02", tz=UTC),  # Labour Day
            pd.Timestamp("2014-09-01", tz=UTC),  # National Day
            pd.Timestamp("2012-09-17", tz=UTC),  # Malaysia Day
            pd.Timestamp("2016-12-26", tz=UTC),  # Christmas Day
            pd.Timestamp("2020-05-25", tz=UTC),  # Eid al Fitr
        ]

        for holiday_label in expected_holidays:
            self.assertNotIn(holiday_label, all_sessions)

    def test_early_closes(self):
        # The session label and close time for expected early closes.
        expected_early_closes = [
            # Day before Chinese New Year
            (
                pd.Timestamp("2019-02-04", tz=UTC),
                pd.Timestamp("2019-02-04 12:30", tz="Asia/Kuala_Lumpur"),
            ),
            # Day before Eid al Fitr.
            (
                pd.Timestamp("2019-06-04", tz=UTC),
                pd.Timestamp("2019-06-04 12:30", tz="Asia/Kuala_Lumpur"),
            ),
        ]

        for session, expected_close in expected_early_closes:
            self.assertEqual(
                self.calendar.session_close(session),
                expected_close,
            )
