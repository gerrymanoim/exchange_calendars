#
# Copyright 2018 Quantopian, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import annotations
from datetime import time
from os.path import abspath, dirname, join
from unittest import TestCase
import re

import pytest
import numpy as np
import pandas as pd
import pandas.testing as tm
from pandas import Timedelta, read_csv
from parameterized import parameterized
from pytz import UTC, timezone
from toolz import concat

from exchange_calendars import get_calendar
from exchange_calendars.calendar_utils import (
    ExchangeCalendarDispatcher,
    _default_calendar_aliases,
    _default_calendar_factories,
)
from exchange_calendars.errors import CalendarNameCollision, InvalidCalendarName
from exchange_calendars.exchange_calendar import ExchangeCalendar, days_at_time
from .test_utils import T


class FakeCalendar(ExchangeCalendar):
    name = "DMY"
    tz = "Asia/Ulaanbaatar"
    open_times = ((None, time(11, 13)),)
    close_times = ((None, time(11, 49)),)


class CalendarRegistrationTestCase(TestCase):
    def setup_method(self, method):
        self.dummy_cal_type = FakeCalendar
        self.dispatcher = ExchangeCalendarDispatcher({}, {}, {})

    def teardown_method(self, method):
        self.dispatcher.clear_calendars()

    def test_register_calendar(self):
        # Build a fake calendar
        dummy_cal = self.dummy_cal_type()

        # Try to register and retrieve the calendar
        self.dispatcher.register_calendar("DMY", dummy_cal)
        retr_cal = self.dispatcher.get_calendar("DMY")
        self.assertEqual(dummy_cal, retr_cal)

        # Try to register again, expecting a name collision
        with self.assertRaises(CalendarNameCollision):
            self.dispatcher.register_calendar("DMY", dummy_cal)

        # Deregister the calendar and ensure that it is removed
        self.dispatcher.deregister_calendar("DMY")
        with self.assertRaises(InvalidCalendarName):
            self.dispatcher.get_calendar("DMY")

    def test_register_calendar_type(self):
        self.dispatcher.register_calendar_type("DMY", self.dummy_cal_type)
        retr_cal = self.dispatcher.get_calendar("DMY")
        self.assertEqual(self.dummy_cal_type, type(retr_cal))

    def test_both_places_are_checked(self):
        dummy_cal = self.dummy_cal_type()

        # if instance is registered, can't register type with same name
        self.dispatcher.register_calendar("DMY", dummy_cal)
        with self.assertRaises(CalendarNameCollision):
            self.dispatcher.register_calendar_type("DMY", type(dummy_cal))

        self.dispatcher.deregister_calendar("DMY")

        # if type is registered, can't register instance with same name
        self.dispatcher.register_calendar_type("DMY", type(dummy_cal))

        with self.assertRaises(CalendarNameCollision):
            self.dispatcher.register_calendar("DMY", dummy_cal)

    def test_force_registration(self):
        self.dispatcher.register_calendar("DMY", self.dummy_cal_type())
        first_dummy = self.dispatcher.get_calendar("DMY")

        # force-register a new instance
        self.dispatcher.register_calendar("DMY", self.dummy_cal_type(), force=True)

        second_dummy = self.dispatcher.get_calendar("DMY")

        self.assertNotEqual(first_dummy, second_dummy)


class DefaultsTestCase(TestCase):
    def test_default_calendars(self):
        dispatcher = ExchangeCalendarDispatcher(
            calendars={},
            calendar_factories=_default_calendar_factories,
            aliases=_default_calendar_aliases,
        )

        # These are ordered aliases first, so that we can deregister the
        # canonical factories when we're done with them, and we'll be done with
        # them after they've been used by all aliases and by canonical name.
        for name in concat([_default_calendar_aliases, _default_calendar_factories]):
            self.assertIsNotNone(
                dispatcher.get_calendar(name), "get_calendar(%r) returned None" % name
            )
            dispatcher.deregister_calendar(name)


class DaysAtTimeTestCase(TestCase):
    @parameterized.expand(
        [
            # NYSE standard day
            (
                "2016-07-19",
                0,
                time(9, 31),
                timezone("America/New_York"),
                "2016-07-19 9:31",
            ),
            # CME standard day
            (
                "2016-07-19",
                -1,
                time(17, 1),
                timezone("America/Chicago"),
                "2016-07-18 17:01",
            ),
            # CME day after DST start
            (
                "2004-04-05",
                -1,
                time(17, 1),
                timezone("America/Chicago"),
                "2004-04-04 17:01",
            ),
            # ICE day after DST start
            (
                "1990-04-02",
                -1,
                time(19, 1),
                timezone("America/Chicago"),
                "1990-04-01 19:01",
            ),
        ]
    )
    def test_days_at_time(self, day, day_offset, time_offset, tz, expected):
        days = pd.DatetimeIndex([pd.Timestamp(day, tz=tz)])
        result = days_at_time(days, time_offset, tz, day_offset)[0]
        expected = pd.Timestamp(expected, tz=tz).tz_convert(UTC)
        self.assertEqual(result, expected)


class ExchangeCalendarTestBase(object):

    # Override in subclasses.
    answer_key_filename = None
    calendar_class = None

    # Affects test_start_bound. Should be set to earliest date for which
    # calendar can be instantiated, or None if no start bound.
    START_BOUND: pd.Timestamp | None = None
    # Affects test_end_bound. Should be set to latest date for which
    # calendar can be instantiated, or None if no end bound.
    END_BOUND: pd.Timestamp | None = None

    # Affects tests that care about the empty periods between sessions. Should
    # be set to False for 24/7 calendars.
    GAPS_BETWEEN_SESSIONS = True

    # Affects tests that care about early closes. Should be set to False for
    # calendars that don't have any early closes.
    HAVE_EARLY_CLOSES = True

    # Affects tests that care about late opens. Since most do not, defaulting
    # to False.
    HAVE_LATE_OPENS = False

    # Affects test_for_breaks. True if one or more calendar sessions has a
    # break.
    HAVE_BREAKS = False

    # Affects test_session_has_break.
    SESSION_WITH_BREAK = None  # None if no session has a break
    SESSION_WITHOUT_BREAK = T("2011-06-15")  # None if all sessions have breaks

    # Affects test_sanity_check_session_lengths. Should be set to the largest
    # number of hours that ever appear in a single session.
    MAX_SESSION_HOURS = 0

    # Affects test_minute_index_to_session_labels.
    # Change these if the start/end dates of your test suite don't contain the
    # defaults.
    MINUTE_INDEX_TO_SESSION_LABELS_START = pd.Timestamp("2011-01-04", tz=UTC)
    MINUTE_INDEX_TO_SESSION_LABELS_END = pd.Timestamp("2011-04-04", tz=UTC)

    # Affects tests around daylight savings. If possible, should contain two
    # dates that are not both in the same daylight savings regime.
    DAYLIGHT_SAVINGS_DATES = ["2004-04-05", "2004-11-01"]

    # Affects test_start_end. Change these if your calendar start/end
    # dates between 2010-01-03 and 2010-01-10 don't match the defaults.
    TEST_START_END_FIRST = pd.Timestamp("2010-01-03", tz=UTC)
    TEST_START_END_LAST = pd.Timestamp("2010-01-10", tz=UTC)
    TEST_START_END_EXPECTED_FIRST = pd.Timestamp("2010-01-04", tz=UTC)
    TEST_START_END_EXPECTED_LAST = pd.Timestamp("2010-01-08", tz=UTC)

    @staticmethod
    def load_answer_key(filename):
        """
        Load a CSV from tests/resources/{filename}.csv
        """
        fullpath = join(
            dirname(abspath(__file__)),
            "./resources",
            filename + ".csv",
        )

        return read_csv(
            fullpath,
            index_col=0,
            # NOTE: Merely passing parse_dates=True doesn't cause pandas to set
            # the dtype correctly, and passing all reasonable inputs to the
            # dtype kwarg cause read_csv to barf.
            parse_dates=[0, 1, 2],
            date_parser=lambda x: pd.Timestamp(x, tz=UTC),
        )

    @classmethod
    def setup_class(cls):
        cls.answers = cls.load_answer_key(cls.answer_key_filename)

        cls.start_date = cls.answers.index[0]
        cls.end_date = cls.answers.index[-1]
        cls.calendar = cls.calendar_class(cls.start_date, cls.end_date)

        cls.one_minute = pd.Timedelta(1, "T")
        cls.one_hour = pd.Timedelta(1, "H")
        cls.one_day = pd.Timedelta(1, "D")
        cls.today = pd.Timestamp.now(tz="UTC").floor("D")

    @classmethod
    def teardown_class(cls):
        cls.calendar = None
        cls.answers = None

    def test_bound_start(self):
        if self.START_BOUND is not None:
            cal = self.calendar_class(self.START_BOUND, self.today)
            self.assertIsInstance(cal, ExchangeCalendar)
            start = self.START_BOUND - pd.DateOffset(days=1)
            with pytest.raises(ValueError, match=re.escape(f"{start}")):
                self.calendar_class(start, self.today)
        else:
            # verify no bound imposed
            cal = self.calendar_class(pd.Timestamp("1902-01-01", tz="UTC"), self.today)
            self.assertIsInstance(cal, ExchangeCalendar)

    def test_bound_end(self):
        if self.END_BOUND is not None:
            cal = self.calendar_class(self.today, self.END_BOUND)
            self.assertIsInstance(cal, ExchangeCalendar)
            end = self.END_BOUND + pd.DateOffset(days=1)
            with pytest.raises(ValueError, match=re.escape(f"{end}")):
                self.calendar_class(self.today, end)
        else:
            # verify no bound imposed
            cal = self.calendar_class(self.today, pd.Timestamp("2050-01-01", tz="UTC"))
            self.assertIsInstance(cal, ExchangeCalendar)

    def test_sanity_check_session_lengths(self):
        # make sure that no session is longer than self.MAX_SESSION_HOURS hours
        for session in self.calendar.all_sessions:
            o, c = self.calendar.open_and_close_for_session(session)
            delta = c - o
            self.assertLessEqual(delta.seconds / 3600, self.MAX_SESSION_HOURS)

    def test_calculated_against_csv(self):
        tm.assert_index_equal(self.calendar.schedule.index, self.answers.index)

    def test_adhoc_holidays_specification(self):
        """adhoc holidays should be tz-naive (#33, #39)."""
        dti = pd.DatetimeIndex(self.calendar.adhoc_holidays)
        assert dti.tz is None

    def test_is_open_on_minute(self):
        one_minute = pd.Timedelta(minutes=1)

        for market_minute in self.answers.market_open[1:]:
            market_minute_utc = market_minute
            # The exchange should be classified as open on its first minute
            self.assertTrue(self.calendar.is_open_on_minute(market_minute_utc))

            if self.GAPS_BETWEEN_SESSIONS:
                # Decrement minute by one, to minute where the market was not
                # open
                pre_market = market_minute_utc - one_minute
                self.assertFalse(self.calendar.is_open_on_minute(pre_market))

        for market_minute in self.answers.market_close[:-1]:
            close_minute_utc = market_minute
            # should be open on its last minute
            self.assertTrue(self.calendar.is_open_on_minute(close_minute_utc))

            if self.GAPS_BETWEEN_SESSIONS:
                # increment minute by one minute, should be closed
                post_market = close_minute_utc + one_minute
                self.assertFalse(self.calendar.is_open_on_minute(post_market))

    def _verify_minute(
        self,
        calendar,
        minute,
        next_open_answer,
        prev_open_answer,
        next_close_answer,
        prev_close_answer,
    ):
        self.assertEqual(calendar.next_open(minute), next_open_answer)

        self.assertEqual(self.calendar.previous_open(minute), prev_open_answer)

        self.assertEqual(self.calendar.next_close(minute), next_close_answer)

        self.assertEqual(self.calendar.previous_close(minute), prev_close_answer)

    def test_next_prev_open_close(self):
        # for each session, check:
        # - the minute before the open (if gaps exist between sessions)
        # - the first minute of the session
        # - the second minute of the session
        # - the minute before the close
        # - the last minute of the session
        # - the first minute after the close (if gaps exist between sessions)
        opens = self.answers.market_open.iloc[1:-2]
        closes = self.answers.market_close.iloc[1:-2]

        previous_opens = self.answers.market_open.iloc[:-1]
        previous_closes = self.answers.market_close.iloc[:-1]

        next_opens = self.answers.market_open.iloc[2:]
        next_closes = self.answers.market_close.iloc[2:]

        for (
            open_minute,
            close_minute,
            previous_open,
            previous_close,
            next_open,
            next_close,
        ) in zip(
            opens, closes, previous_opens, previous_closes, next_opens, next_closes
        ):

            minute_before_open = open_minute - self.one_minute

            # minute before open
            if self.GAPS_BETWEEN_SESSIONS:
                self._verify_minute(
                    self.calendar,
                    minute_before_open,
                    open_minute,
                    previous_open,
                    close_minute,
                    previous_close,
                )

            # open minute
            self._verify_minute(
                self.calendar,
                open_minute,
                next_open,
                previous_open,
                close_minute,
                previous_close,
            )

            # second minute of session
            self._verify_minute(
                self.calendar,
                open_minute + self.one_minute,
                next_open,
                open_minute,
                close_minute,
                previous_close,
            )

            # minute before the close
            self._verify_minute(
                self.calendar,
                close_minute - self.one_minute,
                next_open,
                open_minute,
                close_minute,
                previous_close,
            )

            # the close
            self._verify_minute(
                self.calendar,
                close_minute,
                next_open,
                open_minute,
                next_close,
                previous_close,
            )

            # minute after the close
            if self.GAPS_BETWEEN_SESSIONS:
                self._verify_minute(
                    self.calendar,
                    close_minute + self.one_minute,
                    next_open,
                    open_minute,
                    next_close,
                    close_minute,
                )

    def test_next_prev_minute(self):
        all_minutes = self.calendar.all_minutes

        # test 20,000 minutes because it takes too long to do the rest.
        for idx, minute in enumerate(all_minutes[1:20000]):
            self.assertEqual(all_minutes[idx + 2], self.calendar.next_minute(minute))

            self.assertEqual(all_minutes[idx], self.calendar.previous_minute(minute))

        # test a couple of non-market minutes
        if self.GAPS_BETWEEN_SESSIONS:
            for open_minute in self.answers.market_open[1:]:
                hour_before_open = open_minute - self.one_hour
                self.assertEqual(
                    open_minute, self.calendar.next_minute(hour_before_open)
                )

            for close_minute in self.answers.market_close[1:]:
                hour_after_close = close_minute + self.one_hour
                self.assertEqual(
                    close_minute, self.calendar.previous_minute(hour_after_close)
                )

    def test_date_to_session_label(self):
        m = self.calendar.date_to_session_label
        sessions = self.answers.index[:30]  # first 30 sessions

        # test for error if request session prior to first calendar session.
        date = self.answers.index[0] - self.one_day
        error_msg = (
            "Cannot get a session label prior to the first calendar"
            f" session ('{self.answers.index[0]}'). Consider passing"
            " `direction` as 'next'."
        )
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            m(date, "previous")

        # direction as "previous"
        dates = pd.date_range(sessions[0], sessions[-1], freq="D")
        last_session = None
        for date in dates:
            session_label = m(date, "previous")
            if date in sessions:
                assert session_label == date
                last_session = session_label
            else:
                assert session_label == last_session

        # direction as "next"
        last_session = None
        for date in dates.sort_values(ascending=False):
            session_label = m(date, "next")
            if date in sessions:
                assert session_label == date
                last_session = session_label
            else:
                assert session_label == last_session

        # test for error if request session after last calendar session.
        date = self.answers.index[-1] + self.one_day
        error_msg = (
            "Cannot get a session label later than the last calendar"
            f" session ('{self.answers.index[-1]}'). Consider passing"
            " `direction` as 'previous'."
        )
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            m(date, "next")

        if self.GAPS_BETWEEN_SESSIONS:
            not_sessions = dates[~dates.isin(sessions)][:5]
            for not_session in not_sessions:
                error_msg = (
                    f"`date` '{not_session}' is not a session label. Consider"
                    " passing a `direction`."
                )
                with pytest.raises(ValueError, match=re.escape(error_msg)):
                    m(not_session, "none")
                # test default behaviour
                with pytest.raises(ValueError, match=re.escape(error_msg)):
                    m(not_session)

            # non-valid direction (can only be thrown if no gaps between sessions)
            error_msg = (
                "'not a direction' is not a valid `direction`. Valid `direction`"
                ' values are "next", "previous" and "none".'
            )
            with pytest.raises(ValueError, match=re.escape(error_msg)):
                m(not_session, "not a direction")

    def test_minute_to_session_label(self):
        # minute is prior to first session's open
        minute_before_first_open = self.answers.iloc[0].market_open - self.one_minute
        session_label = self.answers.index[0]
        minutes_that_resolve_to_this_session = [
            self.calendar.minute_to_session_label(minute_before_first_open),
            self.calendar.minute_to_session_label(
                minute_before_first_open, direction="next"
            ),
        ]

        unique_session_labels = set(minutes_that_resolve_to_this_session)
        self.assertTrue(len(unique_session_labels) == 1)
        self.assertIn(session_label, unique_session_labels)

        with self.assertRaises(ValueError):
            self.calendar.minute_to_session_label(
                minute_before_first_open, direction="previous"
            )
        with self.assertRaises(ValueError):
            self.calendar.minute_to_session_label(
                minute_before_first_open, direction="none"
            )

        # minute is between first session's open and last session's close
        for idx, (session_label, open_minute, close_minute, _, _) in enumerate(
            self.answers.iloc[1:-2].itertuples(name=None)
        ):
            hour_into_session = open_minute + self.one_hour

            minute_before_session = open_minute - self.one_minute
            minute_after_session = close_minute + self.one_minute

            next_session_label = self.answers.index[idx + 2]
            previous_session_label = self.answers.index[idx]

            # verify that minutes inside a session resolve correctly
            minutes_that_resolve_to_this_session = [
                self.calendar.minute_to_session_label(open_minute),
                self.calendar.minute_to_session_label(open_minute, direction="next"),
                self.calendar.minute_to_session_label(
                    open_minute, direction="previous"
                ),
                self.calendar.minute_to_session_label(open_minute, direction="none"),
                self.calendar.minute_to_session_label(hour_into_session),
                self.calendar.minute_to_session_label(
                    hour_into_session, direction="next"
                ),
                self.calendar.minute_to_session_label(
                    hour_into_session, direction="previous"
                ),
                self.calendar.minute_to_session_label(
                    hour_into_session, direction="none"
                ),
                self.calendar.minute_to_session_label(close_minute),
                self.calendar.minute_to_session_label(close_minute, direction="next"),
                self.calendar.minute_to_session_label(
                    close_minute, direction="previous"
                ),
                self.calendar.minute_to_session_label(close_minute, direction="none"),
                session_label,
            ]

            if self.GAPS_BETWEEN_SESSIONS:
                minutes_that_resolve_to_this_session.append(
                    self.calendar.minute_to_session_label(minute_before_session)
                )
                minutes_that_resolve_to_this_session.append(
                    self.calendar.minute_to_session_label(
                        minute_before_session, direction="next"
                    )
                )

                minutes_that_resolve_to_this_session.append(
                    self.calendar.minute_to_session_label(
                        minute_after_session, direction="previous"
                    )
                )

            self.assertTrue(
                all(
                    x == minutes_that_resolve_to_this_session[0]
                    for x in minutes_that_resolve_to_this_session
                )
            )

            minutes_that_resolve_to_next_session = [
                self.calendar.minute_to_session_label(minute_after_session),
                self.calendar.minute_to_session_label(
                    minute_after_session, direction="next"
                ),
                next_session_label,
            ]

            self.assertTrue(
                all(
                    x == minutes_that_resolve_to_next_session[0]
                    for x in minutes_that_resolve_to_next_session
                )
            )

            self.assertEqual(
                self.calendar.minute_to_session_label(
                    minute_before_session, direction="previous"
                ),
                previous_session_label,
            )

            if self.GAPS_BETWEEN_SESSIONS:
                # Make sure we use the cache correctly
                minutes_that_resolve_to_different_sessions = [
                    self.calendar.minute_to_session_label(
                        minute_after_session, direction="next"
                    ),
                    self.calendar.minute_to_session_label(
                        minute_after_session, direction="previous"
                    ),
                    self.calendar.minute_to_session_label(
                        minute_after_session, direction="next"
                    ),
                ]

                self.assertEqual(
                    minutes_that_resolve_to_different_sessions,
                    [next_session_label, session_label, next_session_label],
                )

            # make sure that exceptions are raised at the right time
            with self.assertRaises(ValueError):
                self.calendar.minute_to_session_label(open_minute, "asdf")

            if self.GAPS_BETWEEN_SESSIONS:
                with self.assertRaises(ValueError):
                    self.calendar.minute_to_session_label(
                        minute_before_session, direction="none"
                    )

        # minute is later than last session's close
        minute_after_last_close = self.answers.iloc[-1].market_close + self.one_minute
        session_label = self.answers.index[-1]

        minute_that_resolves_to_session_label = self.calendar.minute_to_session_label(
            minute_after_last_close, direction="previous"
        )

        self.assertEqual(session_label, minute_that_resolves_to_session_label)

        with self.assertRaises(ValueError):
            self.calendar.minute_to_session_label(minute_after_last_close)
        with self.assertRaises(ValueError):
            self.calendar.minute_to_session_label(
                minute_after_last_close, direction="next"
            )
        with self.assertRaises(ValueError):
            self.calendar.minute_to_session_label(
                minute_after_last_close, direction="none"
            )

    @parameterized.expand(
        [
            (1, 0),
            (2, 0),
            (2, 1),
        ]
    )
    def test_minute_index_to_session_labels(self, interval, offset):
        minutes = self.calendar.minutes_for_sessions_in_range(
            self.MINUTE_INDEX_TO_SESSION_LABELS_START,
            self.MINUTE_INDEX_TO_SESSION_LABELS_END,
        )
        minutes = minutes[range(offset, len(minutes), interval)]

        np.testing.assert_array_equal(
            pd.DatetimeIndex(minutes.map(self.calendar.minute_to_session_label)),
            self.calendar.minute_index_to_session_labels(minutes),
        )

    def test_next_prev_session(self):
        session_labels = self.answers.index[1:-2]
        max_idx = len(session_labels) - 1

        # the very first session
        first_session_label = self.answers.index[0]
        with self.assertRaises(ValueError):
            self.calendar.previous_session_label(first_session_label)

        # all the sessions in the middle
        for idx, session_label in enumerate(session_labels):
            if idx < max_idx:
                self.assertEqual(
                    self.calendar.next_session_label(session_label),
                    session_labels[idx + 1],
                )

            if idx > 0:
                self.assertEqual(
                    self.calendar.previous_session_label(session_label),
                    session_labels[idx - 1],
                )

        # the very last session
        last_session_label = self.answers.index[-1]
        with self.assertRaises(ValueError):
            self.calendar.next_session_label(last_session_label)

    @staticmethod
    def _find_full_session(calendar):
        for session_label in calendar.schedule.index:
            if session_label not in calendar.early_closes:
                return session_label

        return None

    def test_minutes_for_period(self):
        # full session
        # find a session that isn't an early close.  start from the first
        # session, should be quick.
        full_session_label = self._find_full_session(self.calendar)
        if full_session_label is None:
            raise ValueError("Cannot find a full session to test!")

        minutes = self.calendar.minutes_for_session(full_session_label)
        _open, _close = self.calendar.open_and_close_for_session(full_session_label)
        _break_start, _break_end = self.calendar.break_start_and_end_for_session(
            full_session_label
        )
        if not pd.isnull(_break_start):
            constructed_minutes = np.concatenate(
                [
                    pd.date_range(start=_open, end=_break_start, freq="min"),
                    pd.date_range(start=_break_end, end=_close, freq="min"),
                ]
            )
        else:
            constructed_minutes = pd.date_range(start=_open, end=_close, freq="min")

        np.testing.assert_array_equal(
            minutes,
            constructed_minutes,
        )

        # early close period
        if self.HAVE_EARLY_CLOSES:
            early_close_session_label = self.calendar.early_closes[0]
            minutes_for_early_close = self.calendar.minutes_for_session(
                early_close_session_label
            )
            _open, _close = self.calendar.open_and_close_for_session(
                early_close_session_label
            )

            np.testing.assert_array_equal(
                minutes_for_early_close,
                pd.date_range(start=_open, end=_close, freq="min"),
            )

        # late open period
        if self.HAVE_LATE_OPENS:
            late_open_session_label = self.calendar.late_opens[0]
            minutes_for_late_open = self.calendar.minutes_for_session(
                late_open_session_label
            )
            _open, _close = self.calendar.open_and_close_for_session(
                late_open_session_label
            )

            np.testing.assert_array_equal(
                minutes_for_late_open,
                pd.date_range(start=_open, end=_close, freq="min"),
            )

    def test_sessions_in_range(self):
        # pick two sessions
        session_count = len(self.calendar.schedule.index)

        first_idx = session_count // 3
        second_idx = 2 * first_idx

        first_session_label = self.calendar.schedule.index[first_idx]
        second_session_label = self.calendar.schedule.index[second_idx]

        answer_key = self.calendar.schedule.index[first_idx : second_idx + 1]

        np.testing.assert_array_equal(
            answer_key,
            self.calendar.sessions_in_range(first_session_label, second_session_label),
        )

    def get_session_block(self):
        """
        Get an "interesting" range of three sessions in a row. By default this
        tries to find and return a (full session, early close session, full
        session) block.
        """
        if not self.HAVE_EARLY_CLOSES:
            # If we don't have any early closes, just return a "random" chunk
            # of three sessions.
            return self.calendar.all_sessions[10:13]

        shortened_session = self.calendar.early_closes[0]
        shortened_session_idx = self.calendar.schedule.index.get_loc(shortened_session)

        session_before = self.calendar.schedule.index[shortened_session_idx - 1]
        session_after = self.calendar.schedule.index[shortened_session_idx + 1]

        return [session_before, shortened_session, session_after]

    def test_minutes_in_range(self):
        sessions = self.get_session_block()

        first_open, first_close = self.calendar.open_and_close_for_session(sessions[0])
        minute_before_first_open = first_open - self.one_minute

        middle_open, middle_close = self.calendar.open_and_close_for_session(
            sessions[1]
        )

        last_open, last_close = self.calendar.open_and_close_for_session(sessions[-1])
        minute_after_last_close = last_close + self.one_minute

        # get all the minutes between first_open and last_close
        minutes1 = self.calendar.minutes_in_range(first_open, last_close)
        minutes2 = self.calendar.minutes_in_range(
            minute_before_first_open, minute_after_last_close
        )

        if self.GAPS_BETWEEN_SESSIONS:
            np.testing.assert_array_equal(minutes1, minutes2)
        else:
            # if no gaps, then minutes2 should have 2 extra minutes
            np.testing.assert_array_equal(minutes1, minutes2[1:-1])

        # manually construct the minutes
        (
            first_break_start,
            first_break_end,
        ) = self.calendar.break_start_and_end_for_session(sessions[0])
        (
            middle_break_start,
            middle_break_end,
        ) = self.calendar.break_start_and_end_for_session(sessions[1])
        (
            last_break_start,
            last_break_end,
        ) = self.calendar.break_start_and_end_for_session(sessions[-1])

        intervals = [
            (first_open, first_break_start, first_break_end, first_close),
            (middle_open, middle_break_start, middle_break_end, middle_close),
            (last_open, last_break_start, last_break_end, last_close),
        ]
        all_minutes = []

        for _open, _break_start, _break_end, _close in intervals:
            if pd.isnull(_break_start):
                all_minutes.append(
                    pd.date_range(start=_open, end=_close, freq="min"),
                )
            else:
                all_minutes.append(
                    pd.date_range(start=_open, end=_break_start, freq="min"),
                )
                all_minutes.append(
                    pd.date_range(start=_break_end, end=_close, freq="min"),
                )
        all_minutes = np.concatenate(all_minutes)

        np.testing.assert_array_equal(all_minutes, minutes1)

    def test_minutes_for_sessions_in_range(self):
        sessions = self.get_session_block()

        minutes = self.calendar.minutes_for_sessions_in_range(sessions[0], sessions[-1])

        # do it manually
        session0_minutes = self.calendar.minutes_for_session(sessions[0])
        session1_minutes = self.calendar.minutes_for_session(sessions[1])
        session2_minutes = self.calendar.minutes_for_session(sessions[2])

        concatenated_minutes = np.concatenate(
            [session0_minutes.values, session1_minutes.values, session2_minutes.values]
        )

        np.testing.assert_array_equal(concatenated_minutes, minutes.values)

    def test_sessions_window(self):
        sessions = self.get_session_block()

        np.testing.assert_array_equal(
            self.calendar.sessions_window(sessions[0], len(sessions) - 1),
            self.calendar.sessions_in_range(sessions[0], sessions[-1]),
        )

        np.testing.assert_array_equal(
            self.calendar.sessions_window(sessions[-1], -1 * (len(sessions) - 1)),
            self.calendar.sessions_in_range(sessions[0], sessions[-1]),
        )

    def test_session_distance(self):
        sessions = self.get_session_block()

        forward_distance = self.calendar.session_distance(
            sessions[0],
            sessions[-1],
        )
        self.assertEqual(forward_distance, len(sessions))

        backward_distance = self.calendar.session_distance(
            sessions[-1],
            sessions[0],
        )
        self.assertEqual(backward_distance, -len(sessions))

        one_day_distance = self.calendar.session_distance(
            sessions[0],
            sessions[0],
        )
        self.assertEqual(one_day_distance, 1)

    def test_open_and_close_for_session(self):
        for session_label, open_answer, close_answer, _, _ in self.answers.itertuples(
            name=None
        ):

            found_open, found_close = self.calendar.open_and_close_for_session(
                session_label
            )

            # Test that the methods for just session open and close produce the
            # same values as the method for getting both.
            alt_open = self.calendar.session_open(session_label)
            self.assertEqual(alt_open, found_open)

            alt_close = self.calendar.session_close(session_label)
            self.assertEqual(alt_close, found_close)

            self.assertEqual(open_answer, found_open)
            self.assertEqual(close_answer, found_close)

    def test_session_opens_in_range(self):
        found_opens = self.calendar.session_opens_in_range(
            self.answers.index[0],
            self.answers.index[-1],
        )
        found_opens.index.freq = None
        tm.assert_series_equal(found_opens, self.answers["market_open"])

    def test_session_closes_in_range(self):
        found_closes = self.calendar.session_closes_in_range(
            self.answers.index[0],
            self.answers.index[-1],
        )
        found_closes.index.freq = None
        tm.assert_series_equal(found_closes, self.answers["market_close"])

    def test_daylight_savings(self):
        # 2004 daylight savings switches:
        # Sunday 2004-04-04 and Sunday 2004-10-31

        # make sure there's no weirdness around calculating the next day's
        # session's open time.

        m = dict(self.calendar.open_times)
        m[pd.Timestamp.min] = m.pop(None)
        open_times = pd.Series(m)

        for date in self.DAYLIGHT_SAVINGS_DATES:
            next_day = pd.Timestamp(date, tz=UTC)
            open_date = next_day + Timedelta(days=self.calendar.open_offset)

            the_open = self.calendar.schedule.loc[next_day].market_open

            localized_open = the_open.tz_localize(UTC).tz_convert(self.calendar.tz)

            self.assertEqual(
                (open_date.year, open_date.month, open_date.day),
                (localized_open.year, localized_open.month, localized_open.day),
            )

            open_ix = open_times.index.searchsorted(pd.Timestamp(date), side="right")
            if open_ix == len(open_times):
                open_ix -= 1

            self.assertEqual(open_times.iloc[open_ix].hour, localized_open.hour)

            self.assertEqual(open_times.iloc[open_ix].minute, localized_open.minute)

    def test_start_end(self):
        """
        Check ExchangeCalendar with defined start/end dates.
        """
        calendar = self.calendar_class(
            start=self.TEST_START_END_FIRST,
            end=self.TEST_START_END_LAST,
        )

        self.assertEqual(
            calendar.first_trading_session,
            self.TEST_START_END_EXPECTED_FIRST,
        )
        self.assertEqual(
            calendar.last_trading_session,
            self.TEST_START_END_EXPECTED_LAST,
        )

    def test_has_breaks(self):
        has_breaks = self.calendar.has_breaks()
        self.assertEqual(has_breaks, self.HAVE_BREAKS)

    def test_session_has_break(self):
        if self.SESSION_WITHOUT_BREAK is not None:
            self.assertFalse(
                self.calendar.session_has_break(self.SESSION_WITHOUT_BREAK)
            )
        if self.SESSION_WITH_BREAK is not None:
            self.assertTrue(self.calendar.session_has_break(self.SESSION_WITH_BREAK))


class EuronextCalendarTestBase(ExchangeCalendarTestBase):
    """
    Shared tests for countries on the Euronext exchange.
    """

    # Early close is 2:05 PM.
    # Source: https://www.euronext.com/en/calendars-hours
    TIMEDELTA_TO_EARLY_CLOSE = pd.Timedelta(hours=14, minutes=5)

    def test_normal_year(self):
        expected_holidays_2014 = [
            pd.Timestamp("2014-01-01", tz=UTC),  # New Year's Day
            pd.Timestamp("2014-04-18", tz=UTC),  # Good Friday
            pd.Timestamp("2014-04-21", tz=UTC),  # Easter Monday
            pd.Timestamp("2014-05-01", tz=UTC),  # Labor Day
            pd.Timestamp("2014-12-25", tz=UTC),  # Christmas
            pd.Timestamp("2014-12-26", tz=UTC),  # Boxing Day
        ]

        for session_label in expected_holidays_2014:
            self.assertNotIn(session_label, self.calendar.all_sessions)

        early_closes_2014 = [
            pd.Timestamp("2014-12-24", tz=UTC),  # Christmas Eve
            pd.Timestamp("2014-12-31", tz=UTC),  # New Year's Eve
        ]

        for early_close_session_label in early_closes_2014:
            self.assertIn(
                early_close_session_label,
                self.calendar.early_closes,
            )

    def test_holidays_fall_on_weekend(self):
        # Holidays falling on a weekend should not be made up during the week.
        expected_sessions = [
            # In 2010, Labor Day fell on a Saturday, so the market should be
            # open on both the prior Friday and the following Monday.
            pd.Timestamp("2010-04-30", tz=UTC),
            pd.Timestamp("2010-05-03", tz=UTC),
            # Christmas also fell on a Saturday, meaning Boxing Day fell on a
            # Sunday. The market should still be open on both the prior Friday
            # and the following Monday.
            pd.Timestamp("2010-12-24", tz=UTC),
            pd.Timestamp("2010-12-27", tz=UTC),
        ]

        for session_label in expected_sessions:
            self.assertIn(session_label, self.calendar.all_sessions)

    def test_half_days(self):
        half_days = [
            # In 2010, Christmas Eve and NYE are on Friday, so they should be
            # half days.
            pd.Timestamp("2010-12-24", tz=self.TZ),
            pd.Timestamp("2010-12-31", tz=self.TZ),
        ]
        full_days = [
            # In Dec 2011, Christmas Eve and NYE were both on a Saturday, so
            # the preceding Fridays should be full days.
            pd.Timestamp("2011-12-23", tz=self.TZ),
            pd.Timestamp("2011-12-30", tz=self.TZ),
        ]

        for half_day in half_days:
            half_day_close_time = self.calendar.next_close(half_day)
            self.assertEqual(
                half_day_close_time,
                half_day + self.TIMEDELTA_TO_EARLY_CLOSE,
            )
        for full_day in full_days:
            full_day_close_time = self.calendar.next_close(full_day)
            self.assertEqual(
                full_day_close_time,
                full_day + self.TIMEDELTA_TO_NORMAL_CLOSE,
            )


class OpenDetectionTestCase(TestCase):
    # This is an extra set of unit tests that were added during a rewrite of
    # `minute_index_to_session_labels` to ensure that the existing
    # calendar-generic test suite correctly covered edge cases around
    # non-market minutes.
    def test_detect_non_market_minutes(self):
        cal = get_calendar("NYSE")
        # NOTE: This test is here instead of being on the base class for all
        # calendars because some of our calendars are 24/7, which means there
        # aren't any non-market minutes to find.
        day0 = cal.minutes_for_sessions_in_range(
            pd.Timestamp("2013-07-03", tz=UTC),
            pd.Timestamp("2013-07-03", tz=UTC),
        )
        for minute in day0:
            self.assertTrue(cal.is_open_on_minute(minute))

        day1 = cal.minutes_for_sessions_in_range(
            pd.Timestamp("2013-07-05", tz=UTC),
            pd.Timestamp("2013-07-05", tz=UTC),
        )
        for minute in day1:
            self.assertTrue(cal.is_open_on_minute(minute))

        def NYSE_timestamp(s):
            return pd.Timestamp(s, tz="America/New_York").tz_convert(UTC)

        non_market = [
            # After close.
            NYSE_timestamp("2013-07-03 16:01"),
            # Holiday.
            NYSE_timestamp("2013-07-04 10:00"),
            # Before open.
            NYSE_timestamp("2013-07-05 9:29"),
        ]
        for minute in non_market:
            self.assertFalse(cal.is_open_on_minute(minute), minute)

            input_ = pd.to_datetime(
                np.hstack([day0.values, minute.asm8, day1.values]),
                utc=True,
            )
            with self.assertRaises(ValueError) as e:
                cal.minute_index_to_session_labels(input_)

            exc_str = str(e.exception)
            self.assertIn("First Bad Minute: {}".format(minute), exc_str)


class NoDSTExchangeCalendarTestBase(ExchangeCalendarTestBase):
    def test_daylight_savings(self):
        """
        Several countries in Africa / Asia do not observe DST
        so we need to skip over this test for those markets
        """
        pass
