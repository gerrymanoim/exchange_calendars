from unittest import TestCase

import pytest
import pandas as pd
from pytz import UTC

from exchange_calendars.exchange_calendar_xist import XISTExchangeCalendar

from .test_exchange_calendar import NoDSTExchangeCalendarTestBase


class XISTCalendarTestCase(NoDSTExchangeCalendarTestBase, TestCase):

    answer_key_filename = "xist"
    calendar_class = XISTExchangeCalendar

    # The XIST is open from 10:00 am to 6:00 pm
    MAX_SESSION_HOURS = 8.0

    @pytest.mark.xfail(reason=("See issue #33"))
    def test_end_bound(self):
        super().test_end_bound()

    def test_regular_holidays(self):
        all_sessions = self.calendar.all_sessions

        expected_holidays = [
            pd.Timestamp("2019-01-01", tz=UTC),  # New Year's Day
            pd.Timestamp("2019-04-23", tz=UTC),  # Natl Sov and Children's Day
            pd.Timestamp("2019-05-01", tz=UTC),  # Labour Day
            pd.Timestamp("2017-05-19", tz=UTC),  # CAYS Day
            pd.Timestamp("2019-06-04", tz=UTC),  # Eid al Fitr Day 1
            pd.Timestamp("2019-06-05", tz=UTC),  # Eid al Fitr Day 2
            pd.Timestamp("2019-06-06", tz=UTC),  # Eid al Fitr Day 3
            pd.Timestamp("2019-07-15", tz=UTC),  # Dem and Natl Unity Day
            pd.Timestamp("2016-09-12", tz=UTC),  # Eid al Adha Day 1
            pd.Timestamp("2016-09-13", tz=UTC),  # Eid al Adha Day 2
            pd.Timestamp("2016-09-14", tz=UTC),  # Eid al Adha Day 3
            pd.Timestamp("2016-09-15", tz=UTC),  # Eid al Adha Day 4
            pd.Timestamp("2019-08-30", tz=UTC),  # Victory Day
            pd.Timestamp("2019-10-29", tz=UTC),  # Republic Day
        ]

        for holiday_label in expected_holidays:
            self.assertNotIn(holiday_label, all_sessions)

    def test_holidays_fall_on_weekend(self):
        all_sessions = self.calendar.all_sessions

        # All holidays falling on a weekend should not be made up, so verify
        # that the surrounding Fridays/Mondays are trading days.
        expected_sessions = [
            # New Year's Day on Sunday, Jan 1st.
            pd.Timestamp("2011-12-30", tz=UTC),
            pd.Timestamp("2012-01-02", tz=UTC),
            # Natl Sovereignty and Children's Day on Sunday, Apr 23rd.
            pd.Timestamp("2017-04-21", tz=UTC),
            pd.Timestamp("2017-04-24", tz=UTC),
            # Labour Day on Sunday, May 1st.
            pd.Timestamp("2016-04-29", tz=UTC),
            pd.Timestamp("2016-05-02", tz=UTC),
            # Com. of Attaturk Youth and Sport's Day on Saturday, May 19th.
            pd.Timestamp("2018-05-18", tz=UTC),
            pd.Timestamp("2018-05-21", tz=UTC),
            # Eid Al Fitr (Day 3) on Sunday, Jun 17th (Friday is a holiday).
            pd.Timestamp("2018-06-18", tz=UTC),
            # Democracy and National Unity Day on Sunday, Jul 15th.
            pd.Timestamp("2018-08-13", tz=UTC),
            pd.Timestamp("2018-07-16", tz=UTC),
            # Eid Al Adha (Day 1) on Sunday, Aug 11th (Monday is a holiday).
            pd.Timestamp("2019-08-09", tz=UTC),
            # Victory Day on Saturday, Aug 30th.
            pd.Timestamp("2014-08-29", tz=UTC),
            pd.Timestamp("2014-09-01", tz=UTC),
            # Republic Day on Saturday, Oct 29th.
            pd.Timestamp("2016-10-28", tz=UTC),
            pd.Timestamp("2016-10-31", tz=UTC),
        ]

        for session_label in expected_sessions:
            self.assertIn(session_label, all_sessions)

    def test_early_closes(self):
        # The session label and close time for expected early closes.
        expected_early_closes = [
            # Day before Republic Day.
            (
                pd.Timestamp("2019-10-28", tz=UTC),
                pd.Timestamp("2019-10-28 12:30", tz="Europe/Istanbul"),
            ),
            # Day before Eid al Fitr.
            (
                pd.Timestamp("2019-06-03", tz=UTC),
                pd.Timestamp("2019-06-03 12:30", tz="Europe/Istanbul"),
            ),
            # Day before Eid al Adha.
            (
                pd.Timestamp("2018-08-20", tz=UTC),
                pd.Timestamp("2018-08-20 12:30", tz="Europe/Istanbul"),
            ),
        ]

        for session, expected_close in expected_early_closes:
            self.assertEqual(
                self.calendar.session_close(session),
                expected_close,
            )

    def test_adhoc_holidays(self):
        all_sessions = self.calendar.all_sessions

        expected_holidays = [
            # Miscellaneous closures
            pd.Timestamp("2002-01-04", tz=UTC),  # Market Holiday
            pd.Timestamp("2003-11-21", tz=UTC),  # Terror attacks
            pd.Timestamp("2004-01-23", tz=UTC),  # Bad weather
            pd.Timestamp("2004-12-30", tz=UTC),  # Closure for redenomination
            pd.Timestamp("2004-12-31", tz=UTC),  # Closure for redenomination
            # Eid al Adha and Eid al Fitr extra closures
            pd.Timestamp("2003-02-14", tz=UTC),  # Eid al Adha extra holiday
            pd.Timestamp("2003-11-24", tz=UTC),  # Eid al Fitr extra holiday
            pd.Timestamp("2003-11-28", tz=UTC),  # Eid al Fitr extra holiday
            pd.Timestamp("2006-01-13", tz=UTC),  # Eid al Adha extra holiday
        ]

        for holiday_label in expected_holidays:
            self.assertNotIn(holiday_label, all_sessions)
