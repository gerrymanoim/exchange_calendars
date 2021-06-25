from unittest import TestCase

import pandas as pd
import pandas.testing as tm

from exchange_calendars.exchange_calendar_xkrx import XKRXExchangeCalendar

from .test_exchange_calendar import NoDSTExchangeCalendarTestBase
from .test_utils import T


class XKRXCalendarTestCase(NoDSTExchangeCalendarTestBase, TestCase):

    answer_key_filename = "xkrx"
    answer_key_filename_old = "xkrx_old"

    calendar_class = XKRXExchangeCalendar

    START_BOUND = T("1956-01-01")
    END_BOUND = T("2050-12-31")

    # Korea exchange is open from 9am to 3:30pm
    MAX_SESSION_HOURS = 6.5
    HAVE_EARLY_CLOSES = False

    # has breaks prior to 2000-05-22
    HAVE_BREAKS = True

    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.answers_old = cls.load_answer_key(cls.answer_key_filename_old)

    @classmethod
    def teardown_class(cls):
        super().teardown_class()
        cls.answers_old = None

    def test_normal_year(self):
        expected_holidays_2017 = [
            T("2017-01-27"),
            T("2017-01-30"),
            T("2017-03-01"),
            T("2017-05-01"),
            T("2017-05-03"),
            T("2017-05-05"),
            T("2017-05-09"),
            T("2017-06-06"),
            T("2017-08-15"),
            T("2017-10-02"),
            T("2017-10-03"),
            T("2017-10-04"),
            T("2017-10-05"),
            T("2017-10-06"),
            T("2017-10-09"),
            T("2017-12-25"),
            T("2017-12-29"),
        ]

        for session_label in expected_holidays_2017:
            self.assertNotIn(session_label, self.calendar.all_sessions)

    def test_calculated_against_old_csv(self):
        start_date = T(
            "1998-12-07"
        )  # the current weekmask (1111100) applies since 1998-12-07
        end_date = T("2021-12-31")  # old answer csv file has index until 2021
        answers_old = self.answers_old.index
        answers_old = answers_old[answers_old.slice_indexer(start_date, end_date)]
        schedule = self.calendar.schedule.index
        schedule = schedule[schedule.slice_indexer(start_date, end_date)]
        tm.assert_index_equal(answers_old, schedule)

    def test_holidays_fall_on_weekend(self):
        # Holidays below falling on a weekend should
        # not be made up during the week.
        expected_holidays = [
            # Memorial Day on Sunday
            T("2010-06-06"),
        ]

        for session_label in expected_holidays:
            self.assertNotIn(session_label, self.calendar.all_sessions)

        expected_sessions = [
            # National Foundation Day on a Saturday, so check
            # Friday and Monday surrounding it
            T("2015-10-02"),
            T("2015-10-05"),
            # Christmas Day on a Saturday
            # Same as Foundation Day idea
            T("2010-12-24"),
            T("2010-12-27"),
        ]

        for session_label in expected_sessions:
            self.assertIn(session_label, self.calendar.all_sessions)

        # Holidays below falling on a weekend should
        # be made up during the week.
        expected_holidays = [
            # Chuseok (Korean Thanksgiving) falls on Sunday through Wednesday
            # but Wednesday (below) the exchange is closed; meant to give
            # people an extra day off rather than letting the Sunday count
            T("2014-09-10"),
            # Chuseok (Korean Thanksgiving) falls on Saturday through Tuesday
            # but Tuesday (below) the exchange is closed; meant to give
            # people an extra day off rather than letting the Saturday count
            T("2015-09-29"),
            # Chuseok again; similar reasoning as above
            T("2017-10-06"),
        ]

        for session_label in expected_holidays:
            self.assertNotIn(session_label, self.calendar.all_sessions)

    def test_hangeul_day_2013_onwards(self):

        expected_hangeul_day = T("2013-10-09")
        unexpected_hangeul_day = T("2012-10-09")

        self.assertNotIn(expected_hangeul_day, self.calendar.all_sessions)
        self.assertIn(unexpected_hangeul_day, self.calendar.all_sessions)

    def test_historical_regular_holidays_fall_into_precomputed_holidays(self):
        precomputed_holidays = pd.DatetimeIndex(self.calendar.adhoc_holidays)

        # precomputed holidays won't include weekends (saturday, sunday)
        self.assertTrue(all(d.weekday() < 5 for d in precomputed_holidays))

        generated_holidays = self.calendar.regular_holidays.holidays(
            precomputed_holidays.min(), precomputed_holidays.max(), return_name=True
        )

        # generated holidays include weekends
        self.assertFalse(all(d.weekday() < 5 for d in generated_holidays.index))

        # filter non weekend generated holidays
        non_weekend_mask = pd.DatetimeIndex(
            [d for d in generated_holidays.index if d.weekday() < 5]
        )
        non_weekend_generated_holidays = generated_holidays[non_weekend_mask]

        # generated holidays should generally fall into one of the precomputed holidays
        # except the future holidays that are not precomputed yet
        isin = non_weekend_generated_holidays.index.isin(precomputed_holidays)
        missing = non_weekend_generated_holidays[~isin]

        self.assertTrue(all(isin), "missing holidays = \n%s" % missing)
