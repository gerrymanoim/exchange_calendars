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

import functools
import itertools
import pathlib
import re
import typing
from typing import Literal
from collections import abc
from datetime import time

import numpy as np
import pandas as pd
import pandas.testing as tm
import pytest
import pytz
from pytz import UTC

from exchange_calendars import errors
from exchange_calendars.calendar_utils import (
    ExchangeCalendarDispatcher,
    _default_calendar_aliases,
    _default_calendar_factories,
)
from exchange_calendars.exchange_calendar import ExchangeCalendar, days_at_time
from exchange_calendars.utils import pandas_utils

from .test_utils import T


class FakeCalendar(ExchangeCalendar):
    name = "DMY"
    tz = "Asia/Ulaanbaatar"
    open_times = ((None, time(11, 13)),)
    close_times = ((None, time(11, 49)),)


class TestCalendarRegistration:
    @pytest.fixture
    def dispatcher(self) -> abc.Iterator[ExchangeCalendarDispatcher]:
        dispatcher = ExchangeCalendarDispatcher({}, {}, {})
        yield dispatcher
        dispatcher.clear_calendars()

    @pytest.fixture
    def dummy_cal_type(self) -> abc.Iterator[typing.Type[FakeCalendar]]:
        yield FakeCalendar

    @pytest.fixture
    def dummy_cal(self, dummy_cal_type) -> abc.Iterator[FakeCalendar]:
        yield dummy_cal_type()

    def test_register_calendar(self, dispatcher, dummy_cal):
        # Try to register and retrieve dummy calendar
        dispatcher.register_calendar("DMY", dummy_cal)
        retr_cal = dispatcher.get_calendar("DMY")
        assert dummy_cal == retr_cal

        # Try to register again, expecting a name collision
        with pytest.raises(errors.CalendarNameCollision):
            dispatcher.register_calendar("DMY", dummy_cal)

        # Deregister the calendar and ensure that it is removed
        dispatcher.deregister_calendar("DMY")
        with pytest.raises(errors.InvalidCalendarName):
            dispatcher.get_calendar("DMY")

    def test_register_calendar_type(self, dispatcher, dummy_cal_type):
        dispatcher.register_calendar_type("DMY", dummy_cal_type)
        retr_cal = dispatcher.get_calendar("DMY")
        assert dummy_cal_type == type(retr_cal)

    def test_both_places_are_checked(self, dispatcher, dummy_cal):
        # if instance is registered, can't register type with same name
        dispatcher.register_calendar("DMY", dummy_cal)
        with pytest.raises(errors.CalendarNameCollision):
            dispatcher.register_calendar_type("DMY", type(dummy_cal))

        dispatcher.deregister_calendar("DMY")

        # if type is registered, can't register instance with same name
        dispatcher.register_calendar_type("DMY", type(dummy_cal))

        with pytest.raises(errors.CalendarNameCollision):
            dispatcher.register_calendar("DMY", dummy_cal)

    def test_force_registration(self, dispatcher, dummy_cal_type):
        dispatcher.register_calendar("DMY", dummy_cal_type())
        first_dummy = dispatcher.get_calendar("DMY")

        # force-register a new instance
        dispatcher.register_calendar("DMY", dummy_cal_type(), force=True)

        second_dummy = dispatcher.get_calendar("DMY")

        assert first_dummy != second_dummy


def test_default_calendars():
    """Test dispatcher and calendar default values."""
    dispatcher = ExchangeCalendarDispatcher(
        calendars={},
        calendar_factories=_default_calendar_factories,
        aliases=_default_calendar_aliases,
    )
    for alias in _default_calendar_aliases:
        cal = dispatcher.get_calendar(alias)
        assert cal is not None
        dispatcher.deregister_calendar(alias)

    for name, cal_cls in _default_calendar_factories.items():
        cal = dispatcher.get_calendar(name)
        assert cal is not None
        assert cal.side == "left"
        assert cal.first_session >= cal_cls.default_start()
        assert cal.last_session <= cal_cls.default_end()
        dispatcher.deregister_calendar(name)


@pytest.mark.parametrize(
    "day, day_offset, time_offset, tz, expected",
    [
        # NYSE standard day
        (
            "2016-07-19",
            0,
            time(9, 31),
            pytz.timezone("America/New_York"),
            "2016-07-19 9:31",
        ),
        # CME standard day
        (
            "2016-07-19",
            -1,
            time(17, 1),
            pytz.timezone("America/Chicago"),
            "2016-07-18 17:01",
        ),
        # CME day after DST start
        (
            "2004-04-05",
            -1,
            time(17, 1),
            pytz.timezone("America/Chicago"),
            "2004-04-04 17:01",
        ),
        # ICE day after DST start
        (
            "1990-04-02",
            -1,
            time(19, 1),
            pytz.timezone("America/Chicago"),
            "1990-04-01 19:01",
        ),
    ],
)
def test_days_at_time(day, day_offset, time_offset, tz, expected):
    days = pd.DatetimeIndex([pd.Timestamp(day)])
    result = days_at_time(days, time_offset, tz, day_offset)[0]
    expected = pd.Timestamp(expected, tz=tz).tz_convert(UTC)
    assert result == expected


def get_csv(name: str) -> pd.DataFrame:
    """Get csv file as DataFrame for given calendar `name`."""
    filename = name.replace("/", "-").lower() + ".csv"
    path = pathlib.Path(__file__).parent.joinpath("resources", filename)

    df = pd.read_csv(
        path,
        index_col=0,
        parse_dates=[0, 1, 2, 3, 4],
        infer_datetime_format=True,
    )
    # Necessary for csv saved prior to v4.0
    if df.index.tz is not None:
        df.index = df.index.tz_convert(None)
    # Necessary for csv saved prior to v4.0
    for col in df:
        if df[col].dt.tz is None:
            df[col] = df[col].dt.tz_localize(UTC)
    return df


class Answers:
    """Inputs and expected output for testing a given calendar and side.

    Inputs and expected outputs are provided by public instance methods and
    properties. These either read directly from the corresponding .csv file
    or are evaluated from the .csv file contents. NB Properites / methods
    MUST NOT make evaluations by way of repeating the code of the
    ExchangeCalendar method they are intended to test!

    Parameters
    ----------
    calendar_name
        Canonical name of calendar for which require answer info. For
        example, 'XNYS'.

    side {'both', 'left', 'right', 'neither'}
        Side of sessions to treat as trading minutes.
    """

    ONE_MIN = pd.Timedelta(1, "T")
    TWO_MIN = pd.Timedelta(2, "T")
    ONE_DAY = pd.Timedelta(1, "D")

    LEFT_SIDES = ["left", "both"]
    RIGHT_SIDES = ["right", "both"]

    def __init__(
        self,
        calendar_name: str,
        side: Literal["left", "right", "both", "neither"],
    ):
        self._name = calendar_name.upper()
        self._side = side

    # --- Exposed constructor arguments ---

    @property
    def name(self) -> str:
        """Name of corresponding calendar."""
        return self._name

    @property
    def side(self) -> str:
        """Side of calendar for which answers valid."""
        return self._side

    # --- Properties read (indirectly) from csv file ---

    @functools.cached_property
    def answers(self) -> pd.DataFrame:
        """Answers as correspoding csv."""
        return get_csv(self.name)

    @property
    def sessions(self) -> pd.DatetimeIndex:
        """Session labels."""
        return self.answers.index

    @property
    def opens(self) -> pd.Series:
        """Market open time for each session."""
        return self.answers.open

    @property
    def closes(self) -> pd.Series:
        """Market close time for each session."""
        return self.answers.close

    @property
    def break_starts(self) -> pd.Series:
        """Break start time for each session."""
        return self.answers.break_start

    @property
    def break_ends(self) -> pd.Series:
        """Break end time for each session."""
        return self.answers.break_end

    # --- get and helper methods ---

    def get_next_session(self, session: pd.Timestamp) -> pd.Timestamp:
        """Get session that immediately follows `session`."""
        if session == self.last_session:
            raise IndexError("Cannot get session later than last answers' session.")
        idx = self.sessions.get_loc(session) + 1
        return self.sessions[idx]

    def get_next_sessions(self, session: pd.Timestamp, count: int) -> pd.Timestamp:
        """Get `count` consecutive sessions starting with `session`."""
        assert count >= 0, "count can only take positive integers."
        start = self.sessions.get_loc(session)
        stop = start + count
        if stop > len(self.sessions):
            raise IndexError("Cannot get sessions later than last answers' session.")
        return self.sessions[start:stop]

    def get_prev_sessions(self, session: pd.Timestamp, count: int) -> pd.Timestamp:
        """Get `count` consecutive sessions ending with `session`."""
        assert count >= 0, "count can only take positive integers."
        stop = self.sessions.get_loc(session) + 1
        start = stop - count
        if start < 0:
            raise IndexError("Cannot get sessions earlier than first answers' session.")
        return self.sessions[start:stop]

    def session_has_break(self, session: pd.Timestamp) -> bool:
        """Query if `session` has a break."""
        return session in self.sessions_with_break

    @staticmethod
    def get_sessions_sample(sessions: pd.DatetimeIndex):
        """Return sample of given `sessions`.

        Sample includes:
            All sessions within first two years of `sessions`.
            All sessions within last two years of `sessions`.
            All sessions falling:
                within first 3 days of any month.
                from 28th of any month.
                from 14th through 16th of any month.
        """
        if sessions.empty:
            return sessions

        mask = (
            (sessions < sessions[0] + pd.DateOffset(years=2))
            | (sessions > sessions[-1] - pd.DateOffset(years=2))
            | (sessions.day <= 3)
            | (sessions.day >= 28)
            | (14 <= sessions.day) & (sessions.day <= 16)
        )
        return sessions[mask]

    def get_sessions_minutes(
        self, start: pd.Timestamp, end: pd.Timestamp | int = 1
    ) -> pd.DatetimeIndex:
        """Get trading minutes for 1 or more consecutive sessions.

        Parameters
        ----------
        start
            Session from which to get trading minutes.
        end
            Session through which to get trading mintues. Can be passed as:
                pd.Timestamp: return will include trading minutes for `end`
                    session.
                int: where int represents number of consecutive sessions
                    inclusive of `start`, for which require trading
                    minutes. Default is 1, such that by default will return
                    trading minutes for only `start` session.
        """
        idx = self.sessions.get_loc(start)
        stop = idx + end if isinstance(end, int) else self.sessions.get_loc(end) + 1
        indexer = slice(idx, stop)

        dtis = []
        for first, last, last_am, first_pm in zip(
            self.first_minutes[indexer],
            self.last_minutes[indexer],
            self.last_am_minutes[indexer],
            self.first_pm_minutes[indexer],
        ):
            if pd.isna(last_am):
                dtis.append(pd.date_range(first, last, freq="T"))
            else:
                dtis.append(pd.date_range(first, last_am, freq="T"))
                dtis.append(pd.date_range(first_pm, last, freq="T"))

        return pandas_utils.indexes_union(dtis)

    def get_session_minutes(
        self, session: pd.Timestamp
    ) -> tuple[pd.DatetimeIndex, ...]:
        """Get trading minutes a single `session`.

        Returns
        -------
        tuple[pd.DatetimeIndex, ...]
            If `session` has a break, returns 2-tuple where:
                [0] minutes of am session.
                [1] minutes of pm session.
            If `session` does not have a break, returns 1-tuple with
            element holding minutes of session.
        """
        first = self.first_minutes[session]
        last = self.last_minutes[session]
        last_am = self.last_am_minutes[session]
        first_pm = self.first_pm_minutes[session]

        if pd.isna(last_am):
            return (pd.date_range(first, last, freq="T"),)
        else:
            return (
                pd.date_range(first, last_am, freq="T"),
                pd.date_range(first_pm, last, freq="T"),
            )

    def get_session_break_minutes(self, session: pd.Timestamp) -> pd.DatetimeIndex:
        """Get break minutes for single `session`."""
        if not self.session_has_break(session):
            return pd.DatetimeIndex([], tz=UTC)
        else:
            am_minutes, pm_minutes = self.get_session_minutes(session)
        first = am_minutes[-1] + self.ONE_MIN
        last = pm_minutes[0] - self.ONE_MIN
        return pd.date_range(first, last, freq="T")

    def get_session_edge_minutes(
        self, session: pd.Timestamp, delta: int = 0
    ) -> pd.Timestamp:
        """Get edge trading minutes for a `session`.

        Return will include first and last trading minutes of session and,
        if applicable, subsessions. Passing `delta` will double length
        of return by including trading minutes at `delta` minutes 'inwards'
        from the standard edge minutes. NB `delta` should be less than
        the session/subsession duration - this condition is NOT
        VERIFIED by this method.
        """
        delta = pd.Timedelta(delta, "T")
        first_minute = self.first_minutes[session]
        last_minute = self.last_minutes[session]
        has_break = self.session_has_break(session)
        if has_break:
            last_am_minute = self.last_am_minutes[session]
            first_pm_minute = self.first_pm_minutes[session]

        minutes = [first_minute, last_minute]
        if delta:
            minutes.append(first_minute + delta)
            minutes.append(last_minute - delta)
        if has_break:
            last_am_minute = self.last_am_minutes[session]
            first_pm_minute = self.first_pm_minutes[session]
            minutes.extend([last_am_minute, first_pm_minute])
            if delta:
                minutes.append(last_am_minute - delta)
                minutes.append(first_pm_minute + delta)

        return pd.DatetimeIndex(minutes)

    # --- Evaluated general calendar properties ---

    @functools.cached_property
    def has_a_session_with_break(self) -> pd.DatetimeIndex:
        """Does any session of answers have a break."""
        return self.break_starts.notna().any()

    @property
    def has_a_session_without_break(self) -> bool:
        """Does any session of answers not have a break."""
        return self.break_starts.isna().any()

    # --- Evaluated properties for first and last sessions ---

    @property
    def first_session(self) -> pd.Timestamp:
        """First session covered by answers."""
        return self.sessions[0]

    @property
    def last_session(self) -> pd.Timestamp:
        """Last session covered by answers."""
        return self.sessions[-1]

    @property
    def sessions_range(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        """First and last sessions covered by answers."""
        return self.first_session, self.last_session

    @property
    def first_session_open(self) -> pd.Timestamp:
        """Open time of first session covered by answers."""
        return self.opens[0]

    @property
    def last_session_close(self) -> pd.Timestamp:
        """Close time of last session covered by answers."""
        return self.closes[-1]

    @property
    def first_minute(self) -> pd.Timestamp:
        open_ = self.first_session_open
        return open_ if self.side in self.LEFT_SIDES else open_ + self.ONE_MIN

    @property
    def last_minute(self) -> pd.Timestamp:
        close = self.last_session_close
        return close if self.side in self.RIGHT_SIDES else close - self.ONE_MIN

    @property
    def trading_minutes_range(self) -> tuple[pd.Timestamp, pd.Timestamp]:
        """First and last trading minutes covered by answers."""
        return self.first_minute, self.last_minute

    # --- out-of-bounds properties ---

    @property
    def minute_too_early(self) -> pd.Timestamp:
        """Minute earlier than first trading minute."""
        return self.first_minute - self.ONE_MIN

    @property
    def minute_too_late(self) -> pd.Timestamp:
        """Minute later than last trading minute."""
        return self.last_minute + self.ONE_MIN

    @property
    def session_too_early(self) -> pd.Timestamp:
        """Date earlier than first session."""
        return self.first_session - self.ONE_DAY

    @property
    def session_too_late(self) -> pd.Timestamp:
        """Date later than last session."""
        return self.last_session + self.ONE_DAY

    # --- Evaluated properties covering every session. ---

    @functools.cached_property
    def first_minutes(self) -> pd.Series:
        """First trading minute of each session (UTC)."""
        if self.side in self.LEFT_SIDES:
            minutes = self.opens.copy()
        else:
            minutes = self.opens + self.ONE_MIN
        minutes.name = "first_minutes"
        return minutes

    @property
    def first_minutes_plus_one(self) -> pd.Series:
        """First trading minute of each session plus one minute."""
        return self.first_minutes + self.ONE_MIN

    @property
    def first_minutes_less_one(self) -> pd.Series:
        """First trading minute of each session less one minute."""
        return self.first_minutes - self.ONE_MIN

    @functools.cached_property
    def last_minutes(self) -> pd.Series:
        """Last trading minute of each session."""
        if self.side in self.RIGHT_SIDES:
            minutes = self.closes.copy()
        else:
            minutes = self.closes - self.ONE_MIN
        minutes.name = "last_minutes"
        return minutes

    @property
    def last_minutes_plus_one(self) -> pd.Series:
        """Last trading minute of each session plus one minute."""
        return self.last_minutes + self.ONE_MIN

    @property
    def last_minutes_less_one(self) -> pd.Series:
        """Last trading minute of each session less one minute."""
        return self.last_minutes - self.ONE_MIN

    @functools.cached_property
    def last_am_minutes(self) -> pd.Series:
        """Last pre-break trading minute of each session.

        NaT if session does not have a break.
        """
        if self.side in self.RIGHT_SIDES:
            minutes = self.break_starts.copy()
        else:
            minutes = self.break_starts - self.ONE_MIN
        minutes.name = "last_am_minutes"
        return minutes

    @property
    def last_am_minutes_plus_one(self) -> pd.Series:
        """Last pre-break trading minute of each session plus one minute."""
        return self.last_am_minutes + self.ONE_MIN

    @property
    def last_am_minutes_less_one(self) -> pd.Series:
        """Last pre-break trading minute of each session less one minute."""
        return self.last_am_minutes - self.ONE_MIN

    @functools.cached_property
    def first_pm_minutes(self) -> pd.Series:
        """First post-break trading minute of each session.

        NaT if session does not have a break.
        """
        if self.side in self.LEFT_SIDES:
            minutes = self.break_ends.copy()
        else:
            minutes = self.break_ends + self.ONE_MIN
        minutes.name = "first_pm_minutes"
        return minutes

    @property
    def first_pm_minutes_plus_one(self) -> pd.Series:
        """First post-break trading minute of each session plus one minute."""
        return self.first_pm_minutes + self.ONE_MIN

    @property
    def first_pm_minutes_less_one(self) -> pd.Series:
        """First post-break trading minute of each session less one minute."""
        return self.first_pm_minutes - self.ONE_MIN

    # --- Evaluated session sets and ranges that meet a specific condition ---

    @property
    def _mask_breaks(self) -> pd.Series:
        return self.break_starts.notna()

    @functools.cached_property
    def sessions_with_break(self) -> pd.DatetimeIndex:
        return self.sessions[self._mask_breaks]

    @functools.cached_property
    def sessions_without_break(self) -> pd.DatetimeIndex:
        return self.sessions[~self._mask_breaks]

    @property
    def sessions_without_break_run(self) -> pd.DatetimeIndex:
        """Longest run of consecutive sessions without a break."""
        s = self.break_starts.isna()
        if s.empty:
            return pd.DatetimeIndex([], tz=UTC)
        return pandas_utils.longest_run(s)

    @property
    def sessions_without_break_range(self) -> tuple[pd.Timestamp, pd.Timestamp] | None:
        """Longest session range that does not include a session with a break.

        Returns None if all sessions have a break.
        """
        sessions = self.sessions_without_break_run
        if sessions.empty:
            return None
        return sessions[0], sessions[-1]

    @property
    def _mask_sessions_without_gap_after(self) -> pd.Series:
        if self.side == "neither":
            # will always have gap after if neither open or close are trading
            # minutes (assuming sessions cannot overlap)
            return pd.Series(False, index=self.sessions)

        elif self.side == "both":
            # a trading minute cannot be a minute of more than one session.
            assert not (self.closes == self.opens.shift(-1)).any()
            # there will be no gap if next open is one minute after previous close
            closes_plus_min = self.closes + pd.Timedelta(1, "T")
            return self.opens.shift(-1) == closes_plus_min

        else:
            return self.opens.shift(-1) == self.closes

    @property
    def _mask_sessions_without_gap_before(self) -> pd.Series:
        if self.side == "neither":
            # will always have gap before if neither open or close are trading
            # minutes (assuming sessions cannot overlap)
            return pd.Series(False, index=self.sessions)

        elif self.side == "both":
            # a trading minute cannot be a minute of more than one session.
            assert not (self.closes == self.opens.shift(-1)).any()
            # there will be no gap if previous close is one minute before next open
            opens_minus_one = self.opens - pd.Timedelta(1, "T")
            return self.closes.shift(1) == opens_minus_one

        else:
            return self.closes.shift(1) == self.opens

    @functools.cached_property
    def sessions_without_gap_after(self) -> pd.DatetimeIndex:
        """Sessions not followed by a non-trading minute.

        Rather, sessions immediately followed by first trading minute of
        next session.
        """
        mask = self._mask_sessions_without_gap_after
        return self.sessions[mask][:-1]

    @functools.cached_property
    def sessions_with_gap_after(self) -> pd.DatetimeIndex:
        """Sessions followed by a non-trading minute."""
        mask = self._mask_sessions_without_gap_after
        return self.sessions[~mask][:-1]

    @functools.cached_property
    def sessions_without_gap_before(self) -> pd.DatetimeIndex:
        """Sessions not preceeded by a non-trading minute.

        Rather, sessions immediately preceeded by last trading minute of
        previous session.
        """
        mask = self._mask_sessions_without_gap_before
        return self.sessions[mask][1:]

    @functools.cached_property
    def sessions_with_gap_before(self) -> pd.DatetimeIndex:
        """Sessions preceeded by a non-trading minute."""
        mask = self._mask_sessions_without_gap_before
        return self.sessions[~mask][1:]

    # times are changing...

    @property
    def sessions_unchanging_times_run(self) -> pd.DatetimeIndex:
        """Longest run of sessions that have unchanging times."""
        bv = ~self.sessions.isin(self.sessions_next_time_different)
        s = pd.Series(bv, index=self.sessions)
        return pandas_utils.longest_run(s)

    @functools.lru_cache(maxsize=16)
    def _get_sessions_with_times_different_to_next_session(
        self,
        column: Literal["opens", "closes", "break_starts", "break_ends"],
    ) -> list[pd.DatetimeIndex]:
        """For a given answers column, get session labels where time differs
        from time of next session.

        Where `column` is a break time ("break_starts" or "break_ends"), return
        will not include sessions when next session has a different `has_break`
        status. For example, if session_0 has a break and session_1 does not have
        a break, or vice versa, then session_0 will not be included to return. For
        sessions followed by a session with a different `has_break` status, see
        `_get_sessions_with_has_break_different_to_next_session`.

        Returns
        -------
        list of pd.Datetimeindex
            [0] sessions with earlier next session
            [1] sessions with later next session
        """
        # column takes string to allow lru_cache (Series not hashable)

        is_break_col = column[0] == "b"
        column_ = getattr(self, column)

        if is_break_col:
            if column_.isna().all():
                return [pd.DatetimeIndex([])] * 2
            column_ = column_.fillna(method="ffill").fillna(method="bfill")

        diff = (column_.shift(-1) - column_)[:-1]
        remainder = diff % pd.Timedelta(hours=24)
        mask = remainder != pd.Timedelta(0)
        sessions = self.sessions[:-1][mask]
        next_session_earlier_mask = remainder[mask] > pd.Timedelta(hours=12)
        next_session_earlier = sessions[next_session_earlier_mask]
        next_session_later = sessions[~next_session_earlier_mask]

        if is_break_col:
            mask = next_session_earlier.isin(self.sessions_without_break)
            next_session_earlier = next_session_earlier.drop(next_session_earlier[mask])
            mask = next_session_later.isin(self.sessions_without_break)
            next_session_later = next_session_later.drop(next_session_later[mask])

        return [next_session_earlier, next_session_later]

    @property
    def _sessions_with_opens_different_to_next_session(
        self,
    ) -> list[pd.DatetimeIndex]:
        return self._get_sessions_with_times_different_to_next_session("opens")

    @property
    def _sessions_with_closes_different_to_next_session(
        self,
    ) -> list[pd.DatetimeIndex]:
        return self._get_sessions_with_times_different_to_next_session("closes")

    @property
    def _sessions_with_break_start_different_to_next_session(
        self,
    ) -> list[pd.DatetimeIndex]:
        return self._get_sessions_with_times_different_to_next_session("break_starts")

    @property
    def _sessions_with_break_end_different_to_next_session(
        self,
    ) -> list[pd.DatetimeIndex]:
        return self._get_sessions_with_times_different_to_next_session("break_ends")

    @property
    def sessions_next_open_earlier(self) -> pd.DatetimeIndex:
        return self._sessions_with_opens_different_to_next_session[0]

    @property
    def sessions_next_open_later(self) -> pd.DatetimeIndex:
        return self._sessions_with_opens_different_to_next_session[1]

    @property
    def sessions_next_open_different(self) -> pd.DatetimeIndex:
        return self.sessions_next_open_earlier.union(self.sessions_next_open_later)

    @property
    def sessions_next_close_earlier(self) -> pd.DatetimeIndex:
        return self._sessions_with_closes_different_to_next_session[0]

    @property
    def sessions_next_close_later(self) -> pd.DatetimeIndex:
        return self._sessions_with_closes_different_to_next_session[1]

    @property
    def sessions_next_close_different(self) -> pd.DatetimeIndex:
        return self.sessions_next_close_earlier.union(self.sessions_next_close_later)

    @property
    def sessions_next_break_start_earlier(self) -> pd.DatetimeIndex:
        return self._sessions_with_break_start_different_to_next_session[0]

    @property
    def sessions_next_break_start_later(self) -> pd.DatetimeIndex:
        return self._sessions_with_break_start_different_to_next_session[1]

    @property
    def sessions_next_break_start_different(self) -> pd.DatetimeIndex:
        earlier = self.sessions_next_break_start_earlier
        later = self.sessions_next_break_start_later
        return earlier.union(later)

    @property
    def sessions_next_break_end_earlier(self) -> pd.DatetimeIndex:
        return self._sessions_with_break_end_different_to_next_session[0]

    @property
    def sessions_next_break_end_later(self) -> pd.DatetimeIndex:
        return self._sessions_with_break_end_different_to_next_session[1]

    @property
    def sessions_next_break_end_different(self) -> pd.DatetimeIndex:
        earlier = self.sessions_next_break_end_earlier
        later = self.sessions_next_break_end_later
        return earlier.union(later)

    @functools.cached_property
    def _get_sessions_with_has_break_different_to_next_session(
        self,
    ) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
        """Get sessions with 'has_break' different to next session.

        Returns
        -------
        tuple[pd.DatetimeIndex, pd.DatetimeIndex]
            [0] Sessions that have a break and are immediately followed by
            a session which does not have a break.
            [1] Sessions that do not have a break and are immediately
            followed by a session which does have a break.
        """
        mask = (self.break_starts.notna() & self.break_starts.shift(-1).isna())[:-1]
        sessions_with_break_next_session_without_break = self.sessions[:-1][mask]

        mask = (self.break_starts.isna() & self.break_starts.shift(-1).notna())[:-1]
        sessions_without_break_next_session_with_break = self.sessions[:-1][mask]

        return (
            sessions_with_break_next_session_without_break,
            sessions_without_break_next_session_with_break,
        )

    @property
    def sessions_with_break_next_session_without_break(self) -> pd.DatetimeIndex:
        return self._get_sessions_with_has_break_different_to_next_session[0]

    @property
    def sessions_without_break_next_session_with_break(self) -> pd.DatetimeIndex:
        return self._get_sessions_with_has_break_different_to_next_session[1]

    @functools.cached_property
    def sessions_next_time_different(self) -> pd.DatetimeIndex:
        """Sessions where next session has a different time for any column.

        Includes sessions where next session has a different `has_break`
        status.
        """
        return pandas_utils.indexes_union(
            [
                self.sessions_next_open_different,
                self.sessions_next_close_different,
                self.sessions_next_break_start_different,
                self.sessions_next_break_end_different,
                self.sessions_with_break_next_session_without_break,
                self.sessions_without_break_next_session_with_break,
            ]
        )

    # session blocks...

    def _create_changing_times_session_block(
        self, session: pd.Timestamp
    ) -> pd.DatetimeIndex:
        """Create block of sessions with changing times.

        Given a `session` known to have at least one time (open, close,
        break_start or break_end) different from the next session, returns
        a block of consecutive sessions ending with the first session after
        `session` that has the same times as the session that immediately
        preceeds it (i.e. the last two sessions of the block will have the
        same times), or the last calendar session.
        """
        start_idx = self.sessions.get_loc(session)
        end_idx = start_idx + 1
        while self.sessions[end_idx] in self.sessions_next_time_different:
            end_idx += 1
        end_idx += 2  # +1 to include session with same times, +1 to serve as end index
        return self.sessions[start_idx:end_idx]

    def _get_normal_session_block(self) -> pd.DatetimeIndex:
        """Block of 3 sessions with unchanged timings."""
        start_idx = len(self.sessions) // 3
        end_idx = start_idx + 21

        def times_equal(*s):
            for elems in zip(*s):
                if not set(elems) == {pd.NaT}:
                    if not len({elem.time() for elem in elems}) == 1:
                        return False
            return True

        for i in range(start_idx, end_idx):
            times_1 = self.answers.iloc[i]
            times_2 = self.answers.iloc[i + 1]
            times_3 = self.answers.iloc[i + 2]
            if times_equal(times_1, times_2, times_3):
                break
            assert i < (end_idx - 1), "Unable to evaluate a normal session block!"
        return self.sessions[i : i + 3]

    def _get_session_block(
        self, from_session_of: pd.DatetimeIndex, to_session_of: pd.DatetimeIndex
    ) -> pd.DatetimeIndex:
        """Get session block with bounds defined by sessions of given indexes.

        Block will start with middle session of `from_session_of`.

        Block will run to the nearest subsequent session of `to_session_of`
        (or `self.final_session` if this comes first). Block will end with
        the session that immedidately follows this session.
        """
        i = len(from_session_of) // 2
        start_session = from_session_of[i]

        start_idx = self.sessions.get_loc(start_session)
        end_idx = start_idx + 1
        end_session = self.sessions[end_idx]

        while end_session not in to_session_of and end_session != self.last_session:
            end_idx += 1
            end_session = self.sessions[end_idx]

        return self.sessions[start_idx : end_idx + 2]

    @functools.cached_property
    def session_blocks(self) -> dict[str, pd.DatetimeIndex]:
        """Dictionary of session blocks of a particular behaviour.

        A block comprises either a single session or multiple contiguous
        sessions.

        Keys:
            "normal" - three sessions with unchanging timings.
            "first_three" - answers' first three sessions.
            "last_three" - answers's last three sessions.
            "next_open_earlier" - session 1 open is earlier than session 0
                open.
            "next_open_later" - session 1 open is later than session 0
                open.
            "next_close_earlier" - session 1 close is earlier than session
                0 close.
            "next_close_later" - session 1 close is later than session 0
                close.
            "next_break_start_earlier" - session 1 break_start is earlier
                than session 0 break_start.
            "next_break_start_later" - session 1 break_start is later than
                session 0 break_start.
            "next_break_end_earlier" - session 1 break_end is earlier than
                session 0 break_end.
            "next_break_end_later" - session 1 break_end is later than
                session 0 break_end.
            "with_break_to_without_break" - session 0 has a break, session
                1 does not have a break.
            "without_break_to_with_break" - session 0 does not have a
                break, session 1 does have a break.
            "without_gap_to_with_gap" - session 0 is not followed by a
                gap, session -2 is followed by a gap, session -1 is
                preceeded by a gap.
            "with_gap_to_without_gap" - session 0 is followed by a gap,
                session -2 is not followed by a gap, session -1 is not
                preceeded by a gap.
            "follows_non_session" - one or two sessions where session 0
                is preceeded by a date that is a non-session.
            "follows_non_session" - one or two sessions where session -1
                is followed by a date that is a non-session.
            "contains_non_session" = two sessions with at least one
                non-session date in between.

        If no such session block exists for any key then value will take an
        empty DatetimeIndex (UTC).
        """
        blocks = {}
        blocks["normal"] = self._get_normal_session_block()
        blocks["first_three"] = self.sessions[:3]
        blocks["last_three"] = self.sessions[-3:]

        # blocks here include where:
        #     session 1 has at least one different time from session 0
        #     session 0 has a break and session 1 does not (and vice versa)
        sessions_indexes = (
            ("next_open_earlier", self.sessions_next_open_earlier),
            ("next_open_later", self.sessions_next_open_later),
            ("next_close_earlier", self.sessions_next_close_earlier),
            ("next_close_later", self.sessions_next_close_later),
            ("next_break_start_earlier", self.sessions_next_break_start_earlier),
            ("next_break_start_later", self.sessions_next_break_start_later),
            ("next_break_end_earlier", self.sessions_next_break_end_earlier),
            ("next_break_end_later", self.sessions_next_break_end_later),
            (
                "with_break_to_without_break",
                self.sessions_with_break_next_session_without_break,
            ),
            (
                "without_break_to_with_break",
                self.sessions_without_break_next_session_with_break,
            ),
        )

        for name, index in sessions_indexes:
            if index.empty:
                blocks[name] = pd.DatetimeIndex([])
            else:
                session = index[0]
                blocks[name] = self._create_changing_times_session_block(session)

        # blocks here move from session with gap to session without gap and vice versa
        if (not self.sessions_with_gap_after.empty) and (
            not self.sessions_without_gap_after.empty
        ):
            without_gap_to_with_gap = self._get_session_block(
                self.sessions_without_gap_after, self.sessions_with_gap_after
            )
            with_gap_to_without_gap = self._get_session_block(
                self.sessions_with_gap_after, self.sessions_without_gap_after
            )
        else:
            without_gap_to_with_gap = pd.DatetimeIndex([])
            with_gap_to_without_gap = pd.DatetimeIndex([])

        blocks["without_gap_to_with_gap"] = without_gap_to_with_gap
        blocks["with_gap_to_without_gap"] = with_gap_to_without_gap

        # blocks that adjoin or contain a non_session date
        follows_non_session = pd.DatetimeIndex([])
        preceeds_non_session = pd.DatetimeIndex([])
        contains_non_session = pd.DatetimeIndex([])
        if len(self.non_sessions) > 1:
            diff = self.non_sessions[1:] - self.non_sessions[:-1]
            mask = diff != pd.Timedelta(
                1, "D"
            )  # non_session dates followed by a session
            valid_non_sessions = self.non_sessions[:-1][mask]
            if len(valid_non_sessions) > 1:
                slce = self.sessions.slice_indexer(
                    valid_non_sessions[0], valid_non_sessions[1]
                )
                sessions_between_non_sessions = self.sessions[slce]
                block_length = min(2, len(sessions_between_non_sessions))
                follows_non_session = sessions_between_non_sessions[:block_length]
                preceeds_non_session = sessions_between_non_sessions[-block_length:]
                # take session before and session after non-session
                contains_non_session = self.sessions[slce.stop - 1 : slce.stop + 1]

        blocks["follows_non_session"] = follows_non_session
        blocks["preceeds_non_session"] = preceeds_non_session
        blocks["contains_non_session"] = contains_non_session

        return blocks

    def session_block_generator(self) -> abc.Iterator[tuple[str, pd.DatetimeIndex]]:
        """Generator of session blocks of a particular behaviour."""
        for name, block in self.session_blocks.items():
            if not block.empty:
                yield (name, block)

    @functools.cached_property
    def session_block_minutes(self) -> dict[str, pd.DatetimeIndex]:
        """Trading minutes for each `session_block`.

        Key:
            Session block name as documented to `session_blocks`.
        Value:
            Trading minutes of corresponding session block.
        """
        d = {}
        for name, block in self.session_blocks.items():
            if block.empty:
                d[name] = pd.DatetimeIndex([], tz=UTC)
                continue
            d[name] = self.get_sessions_minutes(block[0], len(block))
        return d

    @property
    def sessions_sample(self) -> pd.DatetimeIndex:
        """Sample of normal and unusual sessions.

        Sample comprises set of sessions of all `session_blocks` (see
        `session_blocks` doc). In this way sample includes at least one
        sample of every indentified unique circumstance.
        """
        dtis = list(self.session_blocks.values())
        return pandas_utils.indexes_union(dtis)

    # non-sessions...

    @functools.cached_property
    def non_sessions(self) -> pd.DatetimeIndex:
        """Dates (UTC midnight) within answers range that are not sessions."""
        all_dates = pd.date_range(
            start=self.first_session, end=self.last_session, freq="D"
        )
        return all_dates.difference(self.sessions)

    @property
    def sessions_range_defined_by_non_sessions(
        self,
    ) -> tuple[tuple[pd.Timestamp, pd.Timestamp], pd.Datetimeindex] | None:
        """Range containing sessions although defined with non-sessions.

        Returns
        -------
        tuple[tuple[pd.Timestamp, pd.Timestamp], pd.Datetimeindex]:
            [0] tuple[pd.Timestamp, pd.Timestamp]:
                [0] range start as non-session date.
                [1] range end as non-session date.
            [1] pd.DatetimeIndex:
                Sessions in range.
        """
        non_sessions = self.non_sessions
        if len(non_sessions) <= 1:
            return None
        limit = len(self.non_sessions) - 2
        i = 0
        start, end = non_sessions[i], non_sessions[i + 1]
        while (end - start) < pd.Timedelta(4, "D"):
            i += 1
            start, end = non_sessions[i], non_sessions[i + 1]
            if i == limit:
                # Unable to evaluate range from consecutive non-sessions
                # that covers >= 3 sessions. Just go with max range...
                start, end = non_sessions[0], non_sessions[-1]
        slice_start, slice_end = self.sessions.searchsorted((start, end))
        return (start, end), self.sessions[slice_start:slice_end]

    @property
    def non_sessions_run(self) -> pd.DatetimeIndex:
        """Longest run of non_sessions."""
        ser = self.sessions.to_series()
        diff = ser.shift(-1) - ser
        max_diff = diff.max()
        if max_diff == pd.Timedelta(1, "D"):
            return pd.DatetimeIndex([])
        session_before_run = diff[diff == max_diff].index[-1]
        run = pd.date_range(
            start=session_before_run + pd.Timedelta(1, "D"),
            periods=(max_diff // pd.Timedelta(1, "D")) - 1,
            freq="D",
        )
        assert run.isin(self.non_sessions).all()
        assert run[0] > self.first_session
        assert run[-1] < self.last_session
        return run

    @property
    def non_sessions_range(self) -> tuple[pd.Timestamp, pd.Timestamp] | None:
        """Longest range covering a period without a session."""
        non_sessions_run = self.non_sessions_run
        if non_sessions_run.empty:
            return None
        else:
            return self.non_sessions_run[0], self.non_sessions_run[-1]

    # --- Evaluated sets of minutes ---

    @functools.cached_property
    def _evaluate_trading_and_break_minutes(self) -> tuple[tuple, tuple]:
        """Edge trading minutes of `sessions_sample`.

        Returns
        -------
        tuple of tuple[tuple[trading_minutes], session]

            tuple[trading_minutes] includes:
                first two trading minutes of a session.
                last two trading minutes of a session.
                If breaks:
                    last two trading minutes of session's am subsession.
                    first two trading minutes of session's pm subsession.

            session
                Session of trading_minutes
        """
        sessions = self.sessions_sample
        first_mins = self.first_minutes[sessions]
        first_mins_plus_one = first_mins + self.ONE_MIN
        last_mins = self.last_minutes[sessions]
        last_mins_less_one = last_mins - self.ONE_MIN

        trading_mins = []
        break_mins = []

        for session, mins_ in zip(
            sessions,
            zip(first_mins, first_mins_plus_one, last_mins, last_mins_less_one),
        ):
            trading_mins.append((mins_, session))

        if self.has_a_session_with_break:
            last_am_mins = self.last_am_minutes[sessions]
            last_am_mins = last_am_mins[last_am_mins.notna()]
            first_pm_mins = self.first_pm_minutes[last_am_mins.index]

            last_am_mins_less_one = last_am_mins - self.ONE_MIN
            last_am_mins_plus_one = last_am_mins + self.ONE_MIN
            last_am_mins_plus_two = last_am_mins + self.TWO_MIN

            first_pm_mins_plus_one = first_pm_mins + self.ONE_MIN
            first_pm_mins_less_one = first_pm_mins - self.ONE_MIN
            first_pm_mins_less_two = first_pm_mins - self.TWO_MIN

            for session, mins_ in zip(
                last_am_mins.index,
                zip(
                    last_am_mins,
                    last_am_mins_less_one,
                    first_pm_mins,
                    first_pm_mins_plus_one,
                ),
            ):
                trading_mins.append((mins_, session))

            for session, mins_ in zip(
                last_am_mins.index,
                zip(
                    last_am_mins_plus_one,
                    last_am_mins_plus_two,
                    first_pm_mins_less_one,
                    first_pm_mins_less_two,
                ),
            ):
                break_mins.append((mins_, session))

        return (tuple(trading_mins), tuple(break_mins))

    @property
    def trading_minutes(self) -> tuple[tuple[tuple[pd.Timestamp], pd.Timestamp]]:
        """Edge trading minutes of `sessions_sample`.

        Returns
        -------
        tuple of tuple[tuple[trading_minutes], session]

            tuple[trading_minutes] includes:
                first two trading minutes of a session.
                last two trading minutes of a session.
                If breaks:
                    last two trading minutes of session's am subsession.
                    first two trading minutes of session's pm subsession.

            session
                Session of trading_minutes
        """
        return self._evaluate_trading_and_break_minutes[0]

    def trading_minutes_only(self) -> abc.Iterator[pd.Timestamp]:
        """Generator of trading minutes of `self.trading_minutes`."""
        for mins, _ in self.trading_minutes:
            for minute in mins:
                yield minute

    @property
    def trading_minute(self) -> pd.Timestamp:
        """A single trading minute."""
        return self.trading_minutes[0][0][0]

    @property
    def break_minutes(self) -> tuple[tuple[tuple[pd.Timestamp], pd.Timestamp]]:
        """Sample of break minutes of `sessions_sample`.

        Returns
        -------
        tuple of tuple[tuple[break_minutes], session]

            tuple[break_minutes]:
                first two minutes of a break.
                last two minutes of a break.

            session
                Session of break_minutes
        """
        return self._evaluate_trading_and_break_minutes[1]

    def break_minutes_only(self) -> abc.Iterator[pd.Timestamp]:
        """Generator of break minutes of `self.break_minutes`."""
        for mins, _ in self.break_minutes:
            for minute in mins:
                yield minute

    @functools.cached_property
    def non_trading_minutes(
        self,
    ) -> tuple[tuple[tuple[pd.Timestamp], pd.Timestamp, pd.Timestamp]]:
        """non_trading_minutes that edge `sessions_sample`.

        NB. Does not include break minutes.

        Returns
        -------
        tuple of tuple[tuple[non-trading minute], previous session, next session]

            tuple[non-trading minute]
                Two non-trading minutes.
                    [0] first non-trading minute to follow a session.
                    [1] last non-trading minute prior to the next session.

            previous session
                Session that preceeds non-trading minutes.

            next session
                Session that follows non-trading minutes.

        See Also
        --------
        break_minutes
        """
        non_trading_mins = []

        sessions = self.sessions_sample
        sessions = prev_sessions = sessions[sessions.isin(self.sessions_with_gap_after)]

        next_sessions = self.sessions[self.sessions.get_indexer(sessions) + 1]

        last_mins_plus_one = self.last_minutes[sessions] + self.ONE_MIN
        first_mins_less_one = self.first_minutes[next_sessions] - self.ONE_MIN

        for prev_session, next_session, mins_ in zip(
            prev_sessions, next_sessions, zip(last_mins_plus_one, first_mins_less_one)
        ):
            non_trading_mins.append((mins_, prev_session, next_session))

        return tuple(non_trading_mins)

    def non_trading_minutes_only(self) -> abc.Iterator[pd.Timestamp]:
        """Generator of non-trading minutes of `self.non_trading_minutes`."""
        for mins, _, _ in self.non_trading_minutes:
            for minute in mins:
                yield minute

    # --- Evaluated minutes of a specific circumstance ---

    def _trading_minute_to_break_minute(
        self, sessions, break_sessions
    ) -> list[pd.DatetimeIndex, pd.DatetimeIndex, pd.DatetimeIndex]:
        times = (self.last_am_minutes[break_sessions] + pd.Timedelta(1, "T")).dt.time

        mask = (self.first_minutes[sessions].dt.time.values < times.values) & (
            times.values < self.last_minutes[sessions].dt.time.values
        )

        minutes = []
        for session, break_session in zip(sessions[mask], break_sessions[mask]):
            break_minutes = self.get_session_break_minutes(break_session)
            trading_minutes = self.get_session_minutes(session)[0]
            bv = np.in1d(trading_minutes.time, break_minutes.time)
            minutes.append([trading_minutes[bv][-1], session, break_session])
        return minutes

    @property
    def trading_minute_to_break_minute_next(
        self,
    ) -> list[pd.DatetimeIndex, pd.DatetimeIndex, pd.DatetimeIndex]:
        """Trading minutes where same minute of next session is a break minute.

        Returns
        -------
        tuple
            [0] trading minute
            [1] session of which [0] ia a trading minute
            [2] next session, i.e. session of which a minute with same time as
                [0] is a break minute.
        """
        sessions = self.sessions_without_break_next_session_with_break
        idxr = self.sessions.get_indexer(sessions)
        break_sessions = self.sessions[idxr + 1]
        lst = self._trading_minute_to_break_minute(sessions, break_sessions)

        sessions = self.sessions_next_break_end_later
        idxr = self.sessions.get_indexer(sessions) + 1
        target_sessions = self.sessions[idxr]
        minutes = self.first_pm_minutes[sessions]
        offset_minutes = minutes.dt.tz_convert(None) - sessions + target_sessions
        # only include offset minute if verified as break minute of target
        # (it wont be if the break has shifted by more than the break duration)
        mask = offset_minutes.values > self.last_am_minutes[target_sessions].values
        lst.extend(list(zip(minutes[mask], sessions[mask], target_sessions[mask])))

        sessions = self.sessions_next_break_start_earlier
        idxr = self.sessions.get_indexer(sessions) + 1
        target_sessions = self.sessions[idxr]
        minutes = self.last_am_minutes[sessions]
        offset_minutes = minutes.dt.tz_convert(None) - sessions + target_sessions
        # only include offset minute if verified as break minute of target
        mask = offset_minutes.values < self.first_pm_minutes[target_sessions].values
        lst.extend(list(zip(minutes[mask], sessions[mask], target_sessions[mask])))
        return lst

    @property
    def trading_minute_to_break_minute_prev(
        self,
    ) -> list[pd.DatetimeIndex, pd.DatetimeIndex, pd.DatetimeIndex]:
        """Trading minutes where same minute of previous session is a break minute.

        Returns
        -------
        tuple
            [0] trading minute
            [1] session of which [0] ia a trading minute
            [2] previous session, i.e. session of which a minute with same time as
                [0] is a break minute.
        """
        break_sessions = self.sessions_with_break_next_session_without_break
        idxr = self.sessions.get_indexer(break_sessions)
        sessions = self.sessions[idxr + 1]
        lst = self._trading_minute_to_break_minute(sessions, break_sessions)

        target_sessions = self.sessions_next_break_end_earlier
        idxr = self.sessions.get_indexer(target_sessions) + 1
        sessions = self.sessions[idxr]  # previous break ends later
        minutes = self.first_pm_minutes[sessions]
        offset_minutes = minutes.dt.tz_convert(None) - sessions + target_sessions
        # only include offset minute if verified as break minute of target
        # (it wont be if the break has shifted by more than the break duration)
        mask = offset_minutes.values > self.last_am_minutes[target_sessions].values
        lst.extend(list(zip(minutes[mask], sessions[mask], target_sessions[mask])))

        target_sessions = self.sessions_next_break_start_later
        idxr = self.sessions.get_indexer(target_sessions) + 1
        sessions = self.sessions[idxr]  # previous break starts earlier
        minutes = self.last_am_minutes[sessions]
        offset_minutes = minutes.dt.tz_convert(None) - sessions + target_sessions
        # only include offset minute if verified as break minute of target
        mask = offset_minutes.values < self.first_pm_minutes[target_sessions].values
        lst.extend(list(zip(minutes[mask], sessions[mask], target_sessions[mask])))

        return lst

    # --- method-specific inputs/outputs ---

    def prev_next_open_close_minutes(
        self,
    ) -> abc.Iterator[
        tuple[
            pd.Timestamp,
            tuple[
                pd.Timestamp | None,
                pd.Timestamp | None,
                pd.Timestamp | None,
                pd.Timestamp | None,
            ],
        ]
    ]:
        """Generator of test parameters for prev/next_open/close methods.

        Inputs include following minutes of each session:
            open
            one minute prior to open (not included for first session)
            one minute after open
            close
            one minute before close
            one minute after close (not included for last session)

        NB Assumed that minutes prior to first open and after last close
        will be handled via parse_timestamp.

        Yields
        ------
        2-tuple:
            [0] Input a minute sd pd.Timestamp
            [1] 4 tuple of expected output of corresponding method:
                [0] previous_open as pd.Timestamp | None
                [1] previous_close as pd.Timestamp | None
                [2] next_open as pd.Timestamp | None
                [3] next_close as pd.Timestamp | None

                NB None indicates that corresponding method is expected to
                raise a ValueError for this input.
        """
        close_is_next_open_bv = self.closes == self.opens.shift(-1)
        open_was_prev_close_bv = self.opens == self.closes.shift(+1)
        close_is_next_open = close_is_next_open_bv[0]

        # minutes for session 0
        minute = self.opens[0]
        yield (minute, (None, None, self.opens[1], self.closes[0]))

        minute = minute + self.ONE_MIN
        yield (minute, (self.opens[0], None, self.opens[1], self.closes[0]))

        minute = self.closes[0]
        next_open = self.opens[2] if close_is_next_open else self.opens[1]
        yield (minute, (self.opens[0], None, next_open, self.closes[1]))

        minute += self.ONE_MIN
        prev_open = self.opens[1] if close_is_next_open else self.opens[0]
        yield (minute, (prev_open, self.closes[0], next_open, self.closes[1]))

        minute = self.closes[0] - self.ONE_MIN
        yield (minute, (self.opens[0], None, self.opens[1], self.closes[0]))

        # minutes for sessions over [1:-1] except for -1 close and 'close + one_min'
        opens = self.opens[1:-1]
        closes = self.closes[1:-1]
        prev_opens = self.opens[:-2]
        prev_closes = self.closes[:-2]
        next_opens = self.opens[2:]
        next_closes = self.closes[2:]
        opens_after_next = self.opens[3:]
        # add dummy row to equal lengths (won't be used)
        opens_after_next = pd.concat(
            [
                opens_after_next,
                pd.Series(pd.Timestamp("2200-01-01", tz=UTC)),
            ]
        )
        stop = closes[-1]

        for (
            open_,
            close,
            prev_open,
            prev_close,
            next_open,
            next_close,
            open_after_next,
            close_is_next_open,
            open_was_prev_close,
        ) in zip(
            opens,
            closes,
            prev_opens,
            prev_closes,
            next_opens,
            next_closes,
            opens_after_next,
            close_is_next_open_bv[1:-2],
            open_was_prev_close_bv[1:-2],
        ):
            if not open_was_prev_close:
                # only include open minutes if not otherwise duplicating
                # evaluations already made for prior close.
                yield (open_, (prev_open, prev_close, next_open, close))
                yield (open_ - self.ONE_MIN, (prev_open, prev_close, open_, close))
                yield (open_ + self.ONE_MIN, (open_, prev_close, next_open, close))

            yield (close - self.ONE_MIN, (open_, prev_close, next_open, close))

            if close != stop:
                next_open_ = open_after_next if close_is_next_open else next_open
                yield (close, (open_, prev_close, next_open_, next_close))

                open_ = next_open if close_is_next_open else open_
                yield (close + self.ONE_MIN, (open_, close, next_open_, next_close))

        # close and 'close + one_min' for session -2
        minute = self.closes[-2]
        next_open = None if close_is_next_open_bv[-2] else self.opens[-1]
        yield (minute, (self.opens[-2], self.closes[-3], next_open, self.closes[-1]))

        minute += self.ONE_MIN
        prev_open = self.opens[-1] if close_is_next_open_bv[-2] else self.opens[-2]
        yield (minute, (prev_open, self.closes[-2], next_open, self.closes[-1]))

        # minutes for session -1
        if not open_was_prev_close_bv[-1]:
            open_ = self.opens[-1]
            prev_open = self.opens[-2]
            prev_close = self.closes[-2]
            next_open = None
            close = self.closes[-1]
            yield (open_, (prev_open, prev_close, next_open, close))
            yield (open_ - self.ONE_MIN, (prev_open, prev_close, open_, close))
            yield (open_ + self.ONE_MIN, (open_, prev_close, next_open, close))

        minute = self.closes[-1]
        next_open = self.opens[2] if close_is_next_open_bv[-1] else self.opens[1]
        yield (minute, (self.opens[-1], self.closes[-2], None, None))

        minute -= self.ONE_MIN
        yield (minute, (self.opens[-1], self.closes[-2], None, self.closes[-1]))

    # dunder

    def __repr__(self) -> str:
        return f"<Answers: calendar {self.name}, side {self.side}>"


def no_parsing(f: typing.Callable):
    """Wrap a method under test so that it skips input parsing."""
    return lambda *args, **kwargs: f(*args, _parse=False, **kwargs)


class ExchangeCalendarTestBase:
    """Test base for an ExchangeCalendar.

    Notes
    -----

    === Fixtures ===

    In accordance with the pytest framework, whilst methods are requried to
    have `self` as their first argument, no method should use `self`.
    All required inputs should come by way of fixtures received to the
    test method's arguments.

    Methods that are directly or indirectly dependent on the evaluation of
    trading minutes should be tested against the parameterized
    `all_calendars_with_answers` fixture. This fixture will execute the
    test against multiple calendar instances, one for each viable `side`.

    The following properties directly evaluate trading minutes:
        minutes
        last_minutes_nanos
        last_am_minutes_nanos
        first_minutes_nanos
        first_pm_minutes_nanos
    NB this list does not include methods that indirectly evaluate methods
    by way of calling (directly or indirectly) one of the above methods.

    Methods that are not dependent on the evaluation of trading minutes
    should only be tested against only the `default_calendar_with_answers`
    or `default_calendar` fixture.

    Calendar instances provided by fixtures should be used exclusively to
    call the method being tested. NO TEST INPUT OR EXPECTED OUTPUT SHOULD
    BE EVALUATED BY WAY OF CALLING A CALENDAR METHOD. Rather, test
    inputs and expected output should be taken directly, or evaluated from,
    properties/methods of the corresponding Answers fixture.

    Subclasses are required to override a limited number of fixtures and
    may be required to override others. Refer to the block comments.
    """

    # subclass must override the following fixtures

    @pytest.fixture(scope="class")
    def calendar_cls(self) -> abc.Iterator[typing.Type[ExchangeCalendar]]:
        """ExchangeCalendar class to be tested.

        Examples:
            XNYSExchangeCalendar
            AlwaysOpenCalendar
        """
        raise NotImplementedError("fixture must be implemented on subclass")

    @pytest.fixture
    def max_session_hours(self) -> abc.Iterator[int | float]:
        """Largest number of hours that can comprise a single session.

        Examples:
            8
            6.5
        """
        raise NotImplementedError("fixture must be implemented on subclass")

    # if subclass has a 24h session then subclass must override this fixture.
    # Define on subclass as is here with only difference being passing
    # ["left", "right"] to decorator's 'params' arg (24h calendars cannot
    # have a side defined as 'both' or 'neither'.).
    @pytest.fixture(scope="class", params=["both", "left", "right", "neither"])
    def all_calendars_with_answers(
        self, request, calendars, answers
    ) -> abc.Iterator[tuple[ExchangeCalendar, Answers]]:
        """Parameterized calendars and answers for each side."""
        yield (calendars[request.param], answers[request.param])

    # subclass should override the following fixtures in the event that the
    # default defined here does not apply.

    @pytest.fixture
    def start_bound(self) -> abc.Iterator[pd.Timestamp | None]:
        """Earliest date for which calendar can be instantiated, or None if
        there is no start bound."""
        yield None

    @pytest.fixture
    def end_bound(self) -> abc.Iterator[pd.Timestamp | None]:
        """Latest date for which calendar can be instantiated, or None if
        there is no end bound."""
        yield None

    # Subclass can optionally override the following fixtures. By overriding
    # a fixture the associated test will be executed with input as yielded
    # by the fixture. Where fixtures are not overriden the associated tests
    # will be skipped.

    @pytest.fixture
    def regular_holidays_sample(self) -> abc.Iterator[list[str]]:
        """Sample of known regular calendar holidays. Empty list if no holidays.

        `test_regular_holidays_sample` will check that each date does not
        represent a calendar session.

        Typical test cases:
            - All regular holidays over a full calendar year.
            - First observance of a regular holiday which started being
                observed from a specific year.
            - Last observance of a regular holiday that ceased to be
                observed from a specific year.
            - Where a regular holiday falls on a weekend and is made up on
                a prior Friday or following Monday, verify that holiday
                is made up on that day.
            - Verify bridge days fall as expected (i.e. verify Mondays or
                Fridays that are recognised holidays due to a regular
                bridged holiday falling on a Tuesday or Thursday
                respectively).
            - Verify unusual rules, for example if a holiday is only
                observed if it falls on a Monday, check that holiday is
                observed when it falls on a Monday.

        Example yield:
            ["2020-12-25", "2021-01-01", ...]
        """
        yield []

    @pytest.fixture
    def non_holidays_sample(self) -> abc.Iterator[list[str]]:
        """Sample of known dates that are not holidays.

        `test_non_holidays_sample` will check that each date represents a
        calendar session.

        Subclass should use this fixture if wishes to test edge cases, for
        example where a session is an exception to a rule, or where session
        preceeds/follows a holiday that is an exception to a rule.

        Typical test cases:
            - Final non-observance of a regular holiday that began
                to be observed in a subsequent year, i.e. verify still
                being treated as a non-holiday in this year.
            - First non-observance of a regular holiday that ceased
                to be observed in a prior year, i.e. verify now being
                treated as a non-holiday in this year.
            - Verify the first trading day following a made up holiday(s)
                is not a holiday. For example, where a two-day holiday
                falls over a Saturaday and Sunday, and is made up on the
                subsequent Monday and Tuesday, verify that the Wednesday is
                not a holiday.
            - For holidays that fall on a weekend and are not made up,
                test that the Friday/Monday are not holidays (i.e. verify
                that the regular holiday is not being made up.)
            - When a non-bridged regular holiday falls on Tuesday/Thursday,
                verify that the prior/subsequent Monday/Friday is not a
                holiday.
            - Verify an irregular non-observance of a regular holiday.
            - Verify unusual rules, for example if a holiday is only
                observed if it falls on a Monday, check that holiday is
                not observed when falls on other days.

        Example return:
            ["2019-12-27", "2020-01-02", ...]
        """
        yield []

    @pytest.fixture
    def adhoc_holidays_sample(self) -> abc.Iterator[list[str]]:
        """Sample of adhoc calendar holidays. Empty list if no adhoc holidays.

        `test_adhoc_holidays_sample` will check that each date does not
        represent a calendar session.

        Typical test cases:
            - Closures that were not planned. For example, due to weather,
                system errors etc.
            - One-off holidays.

        Example return:
            ["2015-04-17", "2021-09-12", ...]
        """
        yield []

    @pytest.fixture
    def late_opens_sample(self) -> abc.Iterator[list[str]]:
        """Sample of dates representing sessions with late opens.

        `test_late_opens_sample` will check that each date represents a
        session with a late open.

        Typical test cases:
            - All regular annual late opens over a year.
            - First observance of an annual late open that started being
                observed from a specific year.
            - Last observance of an annual late open that ceased to be
                observed from a specific year.
            - Any adhoc late opens.

        Example returns:
            ["2022-01-03", "2022-04-22", ...]
        """
        yield []

    @pytest.fixture
    def early_closes_sample(self) -> abc.Iterator[list[str]]:
        """Sample of dates representing sessions with early closes.

        `test_early_closes_sample` will check that each date represents a
        session with an early close.

        Typical test cases:
            - All regular annual early closes over a year.
            - First observance of an annual early close that started being
                observed from a specific year.
            - Last observance of an annual early close that ceased to be
                observed from a specific year.
            - Any adhoc early closes.

        Example returns:
            ["2019-12-24", "2019-12-31", ...]
        """
        yield []

    @pytest.fixture
    def early_closes_sample_time(self) -> abc.Iterator[pd.Timedelta | None]:
        """Local close time of sessions of `early_closes_sample` fixture.

        `test_early_closes_sample_time` will check all sessions of
        `early_closes_sample` have this close time.

        Only override fixture if:
            - `early_closes_sample` is overriden by subclass
            - ALL sessions of `early_closes_sample` have the same local
                close time (if sessions of `early_closes_sample` have
                different local close times then the subclass should
                instead check close times with a test defined on the
                subclass).

        Example returns:
            pd.Timedelta(14, "H")  # 14:00 local time
            pd.Timedelta(hours=13, minutes=15)  # 13:15 local time
        """
        yield None

    @pytest.fixture
    def early_closes_weekdays(self) -> abc.Iterator[tuple(int)]:
        """Weekdays with non-standard close times.

        `test_early_closes_weekdays` will check that all sessions on these
        weekdays have early closes.

        Example return:
            (2, 3)  # Thursday and Friday sessions have an early close.
            (6,)  # Sunday sessions have an early close
        """
        yield tuple()

    @pytest.fixture
    def early_closes_weekdays_sample(self):
        """Sample of dates representing sessions with early closes due to weekday.

        `test_early_closes_weekdays_time` will check that each of these
        dates represents a session that closes at the time returned by the
        fixture `early_closes_weekdays_sample_time`.

        If the `early_closes_weekdays` fixture has length > 1 and the early
        close time is different for the different weekdays then this sample
        should be limited to dates representing sessions that all have
        the same close time. (Dates representing sessions with other close
        times should checked with a test defined on the subclass.)

        Example returns:
            ["2022-08-21", "2022-08-28", ...]
        """
        yield []

    @pytest.fixture
    def early_closes_weekdays_sample_time(self) -> abc.Iterator[pd.Timedelta | None]:
        """Local close time of dates returned by `early_closes_weekdays_sample` fixture.

        `test_early_closes_weekdays_time` will check that each date of
        `early_closes_weekdays_sample` fixture represents a session that
        closes at this time.

        Only override fixture if `early_closes_weekdays_sample` is
        overriden by subclass.

        Example returns:
            pd.Timedelta(14, "H")  # 14:00 local time
            pd.Timedelta(hours=13, minutes=15)  # 13:15 local time
        """
        yield None

    @pytest.fixture
    def non_early_closes_sample(self) -> abc.Iterator[list[str]]:
        """Sample of known calendar sessions with normal close times.

        `test_non_early_closes_sample` will check each date does not
        represent a calendar session with an early close.

        Subclass should use this fixture to test edge cases, for example
        where an otherwise early close is an exception to a rule.

        Typical test cases:
            - Where an early close is observed from a certain year, verify
                that the closest prior year, for which the early close
                would have been otherwise observed, was not an early
                close.
            - Where an early close ceases to be observed from a certain
                year, verify that the closest following year, for which the
                early close would have been otherwse observed, is not an
                early close.

        Example return:
            ["2022-12-23", "2022-12-30]
        """
        yield []

    @pytest.fixture
    def non_early_closes_sample_time(self) -> abc.Iterator[pd.Timedelta | None]:
        """Local close time of sessions of `non_early_closes_sample` fixture.

        `test_non_early_closes_sample_time` will check all sessions of
        `non_early_closes_sample` have this close time.

        Only override fixture if:
            - `non_early_closes_sample` is overriden by subclass.
            - ALL sessions of `non_early_closes_sample` have the same local
                close time (if sessions of `non_early_closes_sample` have
                different local close times then the subclass should
                instead check close times with a test defined on the
                subclass).

        Example returns:
            pd.Timedelta(17, "H")  # 17:00 local time
            pd.Timedelta(hours=16, minutes=30)  # 16:30 local time
        """
        yield None

    # --- NO FIXTURE BELOW THIS LINE SHOULD BE OVERRIDEN ON A SUBCLASS ---

    def test_testbase_integrity(self):
        """Ensure integrity of TestBase.

        Raises error if a reserved fixture is overriden by the subclass.
        """
        cls = self.__class__
        for fixture in [
            "test_testbase_integrity",
            "name",
            "has_24h_session",
            "default_side",
            "sides",
            "answers",
            "default_answers",
            "calendars",
            "default_calendar",
            "calendars_with_answers",
            "default_calendar_with_answers",
            "one_minute",
            "today",
            "all_directions",
            "valid_overrides",
            "non_valid_overrides",
            "daylight_savings_dates",
            "late_opens",
            "early_closes",
        ]:
            if getattr(cls, fixture) != getattr(ExchangeCalendarTestBase, fixture):
                raise RuntimeError(f"fixture '{fixture}' should not be overriden!")

    # Base class fixtures

    @pytest.fixture(scope="class")
    def name(self, calendar_cls) -> abc.Iterator[str]:
        """Calendar name."""
        yield calendar_cls.name

    @pytest.fixture(scope="class")
    def has_24h_session(self, name) -> abc.Iterator[bool]:
        df = get_csv(name)
        yield (df.close == df.open.shift(-1)).any()

    @pytest.fixture(scope="class")
    def default_side(self) -> abc.Iterator[str]:
        """Default calendar side."""
        yield "left"

    @pytest.fixture(scope="class")
    def sides(self, has_24h_session) -> abc.Iterator[list[str]]:
        """All valid sides options for calendar."""
        if has_24h_session:
            yield ["left", "right"]
        else:
            yield ["both", "left", "right", "neither"]

    # Calendars and answers

    @pytest.fixture(scope="class")
    def answers(self, name, sides) -> abc.Iterator[dict[str, Answers]]:
        """Dict of answers, key as side, value as corresoponding answers."""
        yield {side: Answers(name, side) for side in sides}

    @pytest.fixture(scope="class")
    def default_answers(self, answers, default_side) -> abc.Iterator[Answers]:
        yield answers[default_side]

    @pytest.fixture(scope="class")
    def calendars(
        self, calendar_cls, default_answers, sides
    ) -> abc.Iterator[dict[str, ExchangeCalendar]]:
        """Dict of calendars, key as side, value as corresoponding calendar."""
        start = default_answers.first_session
        end = default_answers.last_session
        yield {side: calendar_cls(start, end, side) for side in sides}

    @pytest.fixture(scope="class")
    def default_calendar(
        self, calendars, default_side
    ) -> abc.Iterator[ExchangeCalendar]:
        yield calendars[default_side]

    @pytest.fixture(scope="class")
    def calendars_with_answers(
        self, calendars, answers, sides
    ) -> abc.Iterator[dict[str, tuple[ExchangeCalendar, Answers]]]:
        """Dict of calendars and answers, key as side."""
        yield {side: (calendars[side], answers[side]) for side in sides}

    @pytest.fixture(scope="class")
    def default_calendar_with_answers(
        self, calendars_with_answers, default_side
    ) -> abc.Iterator[tuple[ExchangeCalendar, Answers]]:
        yield calendars_with_answers[default_side]

    # General use fixtures.

    @pytest.fixture(scope="class")
    def one_minute(self) -> abc.Iterator[pd.Timedelta]:
        yield pd.Timedelta(1, "T")

    @pytest.fixture(scope="class")
    def today(self) -> abc.Iterator[pd.Timedelta]:
        yield pd.Timestamp.now().floor("D")

    @pytest.fixture(scope="class", params=["next", "previous", "none"])
    def all_directions(self, request) -> abc.Iterator[str]:
        """Parameterised fixture of direction to go if minute is not a trading minute"""
        yield request.param

    @pytest.fixture(scope="class")
    def valid_overrides(self) -> abc.Iterator[list[str]]:
        """Names of methods that can be overriden by a subclass."""
        yield [
            "name",
            "bound_min",
            "bound_max",
            "_bound_min_error_msg",
            "_bound_max_error_msg",
            "default_start",
            "default_end",
            "tz",
            "open_times",
            "break_start_times",
            "break_end_times",
            "close_times",
            "weekmask",
            "open_offset",
            "close_offset",
            "regular_holidays",
            "adhoc_holidays",
            "special_opens",
            "special_opens_adhoc",
            "special_closes",
            "special_closes_adhoc",
            "apply_special_offsets",
        ]

    @pytest.fixture(scope="class")
    def non_valid_overrides(self, valid_overrides) -> abc.Iterator[list[str]]:
        """Names of methods that cannot be overriden by a subclass."""
        yield [
            name
            for name in dir(ExchangeCalendar)
            if name not in valid_overrides
            and not name.startswith("__")
            and not name == "_abc_impl"
        ]

    @pytest.fixture(scope="class")
    def daylight_savings_dates(
        self, default_calendar
    ) -> abc.Iterator[list[pd.Timestamp]]:
        """All dates in a specific year that mark the first day of a new
        time regime.

        Yields empty list if timezone's UCT offset does not change.

        Notes
        -----
        NB Any test that employs this fixture assumes the accuarcy of the
        default calendar's `tz` property.
        """
        cal = default_calendar
        year = cal.last_session.year - 1
        days = pd.date_range(str(year), str(year + 1), freq="D")
        tzinfo = pytz.timezone(cal.tz.zone)

        prev_offset = tzinfo.utcoffset(days[0])
        dates = []
        for day in days[1:]:
            try:
                offset = tzinfo.utcoffset(day)
            except pytz.NonExistentTimeError:
                offset = tzinfo.utcoffset(day + pd.Timedelta(1, "H"))
            if offset != prev_offset:
                dates.append(day)
                if len(dates) == 2:
                    break
            prev_offset = offset
        yield dates

    @pytest.fixture(scope="class")
    def late_opens(
        self, default_calendar_with_answers
    ) -> abc.Iterator[pd.DatetimeIndex]:
        """Calendar sessions with a late open.

        Late opens evaluated as those that are later than the prevailing
        open time as defined by `default_calendar.open_times`.

        Notes
        -----
        NB Any test that employs this fixture ASSUMES the accuarcy of the
        following calendar properties:
            `open_times`
            `tz`
        """
        cal, ans = default_calendar_with_answers

        d = dict(cal.open_times)
        d[pd.Timestamp.min] = d.pop(None)
        s = pd.Series(d).sort_index(ascending=False)

        date_to = pd.Timestamp.max
        dtis: list[pd.DatetimeIndex] = []
        # For each period over which a distinct open time prevails...
        for date_from, time_ in s.iteritems():
            opens = ans.opens[date_from:date_to]
            sessions = opens.index
            td = pd.Timedelta(hours=time_.hour, minutes=time_.minute)
            # Evaluate session opens as if were all normal open time.
            normal_opens = sessions + pd.Timedelta(cal.open_offset, "D") + td
            normal_opens_utc = normal_opens.tz_localize(cal.tz).tz_convert(UTC)
            # Append those sessions with opens (according to answers) later than
            # what would be normal.
            dtis.append(sessions[opens > normal_opens_utc])
            if date_from != pd.Timestamp.min:
                date_to = date_from - pd.Timedelta(1, "D")

        late_opens = pandas_utils.indexes_union(dtis)
        yield late_opens

    @pytest.fixture(scope="class")
    def early_closes(
        self, default_calendar_with_answers
    ) -> abc.Iterator[pd.DatetimeIndex]:
        """Calendar sessions with a late open.

        Early closes evaluated as those that are earlier than the
        prevailing close time as defined by `default_calendar.close_times`.

        Notes
        -----
        NB Any test that employs this fixture ASSUMES the accuarcy of the
        following calendar properties:
            `close_times`
            `tz`
        """
        cal, ans = default_calendar_with_answers

        d = dict(cal.close_times)
        d[pd.Timestamp.min] = d.pop(None)
        s = pd.Series(d).sort_index(ascending=False)

        date_to = pd.Timestamp.max
        dtis: list[pd.DatetimeIndex] = []
        for date_from, time_ in s.iteritems():
            closes = ans.closes[date_from:date_to]  # index to tz-naive
            sessions = closes.index
            td = pd.Timedelta(hours=time_.hour, minutes=time_.minute)
            normal_closes = sessions + pd.Timedelta(cal.close_offset, "D") + td
            normal_closes_utc = normal_closes.tz_localize(cal.tz).tz_convert(UTC)
            dtis.append(sessions[closes < normal_closes_utc])
            if date_from != pd.Timestamp.min:
                date_to = date_from - pd.Timedelta(1, "D")

        early_closes = pandas_utils.indexes_union(dtis)
        yield early_closes

    # --- TESTS ---

    # Tests for calendar definition and construction methods.

    def test_base_integrity(self, calendar_cls, non_valid_overrides):
        cls = calendar_cls
        for name in non_valid_overrides:
            on_cls, on_base = getattr(cls, name), getattr(ExchangeCalendar, name)
            # covers properties, instance methods and class mathods...
            try:
                assert on_cls == on_base or on_cls.__qualname__ == on_base.__qualname__
            except AttributeError:
                if not (cls.name == "XKRX" and name == "day"):
                    # allow exchange_calendar_xkrx to overwrite 'day'.
                    raise

    def test_calculated_against_csv(self, default_calendar_with_answers):
        calendar, ans = default_calendar_with_answers
        tm.assert_index_equal(calendar.schedule.index, ans.sessions)

    def test_start_end(self, default_answers, calendar_cls):
        ans = default_answers
        sessions = ans.session_blocks["normal"]
        start, end = sessions[0], sessions[-1]
        cal = calendar_cls(start, end)
        assert cal.first_session == start
        assert cal.last_session == end

        if len(ans.non_sessions) > 1:
            # start and end as non-sessions
            (start, end), sessions = ans.sessions_range_defined_by_non_sessions
            cal = calendar_cls(start, end)
            assert cal.first_session == sessions[0]
            assert cal.last_session == sessions[-1]

    def test_invalid_input(self, calendar_cls, sides, default_answers, name):
        ans = default_answers

        invalid_side = "both" if "both" not in sides else "invalid_side"
        error_msg = f"`side` must be in {sides} although received as {invalid_side}."
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            calendar_cls(side=invalid_side)

        start = ans.sessions[1]
        end_same_as_start = ans.sessions[1]
        error_msg = (
            "`start` must be earlier than `end` although `start` parsed as"
            f" '{start}' and `end` as '{end_same_as_start}'."
        )
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            calendar_cls(start=start, end=end_same_as_start)

        end_before_start = ans.sessions[0]
        error_msg = (
            "`start` must be earlier than `end` although `start` parsed as"
            f" '{start}' and `end` as '{end_before_start}'."
        )
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            calendar_cls(start=start, end=end_before_start)

        if len(ans.non_sessions) > 1:
            start, end = ans.non_sessions_range
            error_msg = (
                f"The requested ExchangeCalendar, {name.upper()}, cannot be created as"
                f" there would be no sessions between the requested `start` ('{start}')"
                f" and `end` ('{end}') dates."
            )
            with pytest.raises(errors.NoSessionsError, match=re.escape(error_msg)):
                calendar_cls(start=start, end=end)

    def test_bound_min(self, calendar_cls, start_bound, today):
        assert calendar_cls.bound_min() == start_bound
        if start_bound is not None:
            cal = calendar_cls(start_bound, today)
            assert isinstance(cal, ExchangeCalendar)

            start = start_bound - pd.DateOffset(days=1)
            with pytest.raises(ValueError, match=re.escape(f"{start}")):
                calendar_cls(start, today)
        else:
            # verify no bound imposed
            cal = calendar_cls(pd.Timestamp("1902-01-01"), today)
            assert isinstance(cal, ExchangeCalendar)

    def test_bound_max(self, calendar_cls, end_bound, today):
        assert calendar_cls.bound_max() == end_bound
        if end_bound is not None:
            cal = calendar_cls(today, end_bound)
            assert isinstance(cal, ExchangeCalendar)

            end = end_bound + pd.DateOffset(days=1)
            with pytest.raises(ValueError, match=re.escape(f"{end}")):
                calendar_cls(today, end)
        else:
            # verify no bound imposed
            cal = calendar_cls(today, pd.Timestamp("2050-01-01"))
            assert isinstance(cal, ExchangeCalendar)

    def test_sanity_check_session_lengths(self, default_calendar, max_session_hours):
        cal = default_calendar
        cal_max_secs = (cal.closes_nanos - cal.opens_nanos).max()
        assert cal_max_secs / 3600000000000 <= max_session_hours

    def test_adhoc_holidays_specification(self, default_calendar):
        """adhoc holidays should be tz-naive (#33, #39)."""
        dti = pd.DatetimeIndex(default_calendar.adhoc_holidays)
        assert dti.tz is None

    def test_daylight_savings(self, default_calendar, daylight_savings_dates):
        # make sure there's no weirdness around calculating the next day's
        # session's open time.
        if daylight_savings_dates:
            cal = default_calendar
            d = dict(cal.open_times)
            d[pd.Timestamp.min] = d.pop(None)
            open_times = pd.Series(d)

            for date in daylight_savings_dates:
                # where `next day` is first session of new daylight savings regime
                next_day = cal.date_to_session(T(date), "next")
                open_date = next_day + pd.Timedelta(days=cal.open_offset)

                the_open = cal.schedule.loc[next_day].open

                localized_open = the_open.tz_convert(cal.tz)

                assert open_date.year == localized_open.year
                assert open_date.month == localized_open.month
                assert open_date.day == localized_open.day

                open_ix = open_times.index.searchsorted(date, side="right")
                if open_ix == len(open_times):
                    open_ix -= 1

                open_time = open_times.iloc[open_ix]
                assert open_time.hour == localized_open.hour
                assert open_time.minute == localized_open.minute

    # Tests for properties covering all sessions.

    def test_sessions(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        ans_sessions = ans.sessions
        cal_sessions = cal.sessions
        tm.assert_index_equal(ans_sessions, cal_sessions)

    def test_opens_closes_break_starts_ends(self, default_calendar_with_answers):
        """Test `opens`, `closes, `break_starts` and `break_ends` properties."""
        cal, ans = default_calendar_with_answers
        for prop in (
            "opens",
            "closes",
            "break_starts",
            "break_ends",
        ):
            ans_series = getattr(ans, prop)
            cal_series = getattr(cal, prop)
            tm.assert_series_equal(ans_series, cal_series, check_freq=False)

    def test_minutes_properties(self, all_calendars_with_answers):
        """Test minute properties.

        Tests following calendar properties:
            all_first_minutes
            all_last_minutes
            all_last_am_minutes
            all_first_pm_minutes
        """
        cal, ans = all_calendars_with_answers

        for prop in (
            "first_minutes",
            "last_minutes",
            "last_am_minutes",
            "first_pm_minutes",
        ):
            ans_minutes = getattr(ans, prop)
            cal_minutes = getattr(cal, prop)
            tm.assert_series_equal(ans_minutes, cal_minutes, check_freq=False)

    # Tests for properties covering all minutes.

    def test_minutes(self, all_calendars_with_answers, one_minute):
        """Test trading minutes at sessions' bounds."""
        calendar, ans = all_calendars_with_answers

        side = ans.side
        mins = calendar.minutes
        assert isinstance(mins, pd.DatetimeIndex)
        assert not mins.empty
        mins_plus_1 = mins + one_minute
        mins_less_1 = mins - one_minute

        if side in ["left", "neither"]:
            # Test that close and break_start not in mins,
            # but are in mins_plus_1 (unless no gap after)

            # do not test here for sessions with no gap after as for "left" these
            # sessions' close IS a trading minute as it's the same as next session's
            # open.
            # NB For "neither" all sessions will have gap after.
            closes = ans.closes[ans.sessions_with_gap_after]
            # closes should not be in minutes
            assert not mins.isin(closes).any()
            # all closes should be in minutes plus 1
            # for speed, use only subset of mins that are of interest
            mins_plus_1_on_close = mins_plus_1[mins_plus_1.isin(closes)]
            assert closes.isin(mins_plus_1_on_close).all()

            # as noted above, if no gap after then close should be a trading minute
            # as will be first minute of next session.
            closes = ans.closes[ans.sessions_without_gap_after]
            mins_on_close = mins[mins.isin(closes)]
            assert closes.isin(mins_on_close).all()

            if ans.has_a_session_with_break:
                # break start should not be in minutes
                assert not mins.isin(ans.break_starts).any()
                # break start should be in minutes plus 1
                break_starts = ans.break_starts[ans.sessions_with_break]
                mins_plus_1_on_start = mins_plus_1[mins_plus_1.isin(break_starts)]
                assert break_starts.isin(mins_plus_1_on_start).all()

        if side in ["left", "both"]:
            # Test that open and break_end are in mins,
            # but not in mins_plus_1 (unless no gap before)
            mins_on_open = mins[mins.isin(ans.opens)]
            assert ans.opens.isin(mins_on_open).all()

            opens = ans.opens[ans.sessions_with_gap_before]
            assert not mins_plus_1.isin(opens).any()

            opens = ans.opens[ans.sessions_without_gap_before]
            mins_plus_1_on_open = mins_plus_1[mins_plus_1.isin(opens)]
            assert opens.isin(mins_plus_1_on_open).all()

            if ans.has_a_session_with_break:
                break_ends = ans.break_ends[ans.sessions_with_break]
                mins_on_end = mins[mins.isin(ans.break_ends)]
                assert break_ends.isin(mins_on_end).all()

        if side in ["right", "neither"]:
            # Test that open and break_end are not in mins,
            # but are in mins_less_1 (unless no gap before)
            opens = ans.opens[ans.sessions_with_gap_before]
            assert not mins.isin(opens).any()

            mins_less_1_on_open = mins_less_1[mins_less_1.isin(opens)]
            assert opens.isin(mins_less_1_on_open).all()

            opens = ans.opens[ans.sessions_without_gap_before]
            mins_on_open = mins[mins.isin(opens)]
            assert opens.isin(mins_on_open).all()

            if ans.has_a_session_with_break:
                assert not mins.isin(ans.break_ends).any()
                break_ends = ans.break_ends[ans.sessions_with_break]
                mins_less_1_on_end = mins_less_1[mins_less_1.isin(break_ends)]
                assert break_ends.isin(mins_less_1_on_end).all()

        if side in ["right", "both"]:
            # Test that close and break_start are in mins,
            # but not in mins_less_1 (unless no gap after)
            mins_on_close = mins[mins.isin(ans.closes)]
            assert ans.closes.isin(mins_on_close).all()

            closes = ans.closes[ans.sessions_with_gap_after]
            assert not mins_less_1.isin(closes).any()

            closes = ans.closes[ans.sessions_without_gap_after]
            mins_less_1_on_close = mins_less_1[mins_less_1.isin(closes)]
            assert closes.isin(mins_less_1_on_close).all()

            if ans.has_a_session_with_break:
                break_starts = ans.break_starts[ans.sessions_with_break]
                mins_on_start = mins[mins.isin(ans.break_starts)]
                assert break_starts.isin(mins_on_start).all()

    # Tests for calendar properties.

    def test_calendar_bounds_properties(self, all_calendars_with_answers):
        """Test calendar properties that define a calendar bound.

        Tests following calendar properties:
            first_session
            last_session
            first_session_open
            last_session_close
            first_minute
            last_minute
        """
        cal, ans = all_calendars_with_answers
        assert ans.first_session == cal.first_session
        assert ans.last_session == cal.last_session
        assert ans.first_session_open == cal.first_session_open
        assert ans.last_session_close == cal.last_session_close
        assert ans.first_minute == cal.first_minute
        assert ans.last_minute == cal.last_minute

    def test_has_break(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        assert cal.has_break == ans.has_a_session_with_break

    def test_regular_holidays_sample(self, default_calendar, regular_holidays_sample):
        """Test that calendar-specific sample of holidays are not sessions."""
        if regular_holidays_sample:
            for holiday in regular_holidays_sample:
                assert T(holiday) not in default_calendar.sessions

    def test_adhoc_holidays_sample(self, default_calendar, adhoc_holidays_sample):
        """Test that calendar-specific sample of holidays are not sessions."""
        if adhoc_holidays_sample:
            for holiday in adhoc_holidays_sample:
                assert T(holiday) not in default_calendar.sessions

    def test_non_holidays_sample(self, default_calendar, non_holidays_sample):
        """Test that calendar-specific sample of non-holidays are sessions."""
        if non_holidays_sample:
            for date in non_holidays_sample:
                assert T(date) in default_calendar.sessions

    def test_late_opens_sample(self, default_calendar, late_opens_sample):
        """Test calendar-specific sample of sessions are included to late opens."""
        if late_opens_sample:
            for date in late_opens_sample:
                assert T(date) in default_calendar.late_opens

    def test_early_closes_sample(self, default_calendar, early_closes_sample):
        """Test calendar-specific sample of sessions are included to early closes."""
        if early_closes_sample:
            for date in early_closes_sample:
                assert T(date) in default_calendar.early_closes

    def test_early_closes_sample_time(
        self, default_calendar, early_closes_sample, early_closes_sample_time
    ):
        """Test close time of calendar-specific sample of early closing sessions.

        Notes
        -----
        TEST RELIES ON ACCURACY OF CALENDAR PROPERTIES `closes`, `tz` and
        `close_offset`.
        """
        if early_closes_sample_time is not None:
            cal, tz = default_calendar, default_calendar.tz
            offset = pd.Timedelta(cal.close_offset, "D") + early_closes_sample_time
            for date in early_closes_sample:
                early_close = cal.closes[date].tz_convert(tz)
                expected = pd.Timestamp(date, tz=tz) + offset
                assert early_close == expected

    def test_early_closes_weekdays(
        self, default_calendar_with_answers, early_closes_weekdays
    ):
        """Test weekday sessions with early closes are included to early closes."""
        if not early_closes_weekdays:
            return
        cal, ans = default_calendar_with_answers
        bv = ans.sessions.weekday.isin(early_closes_weekdays)
        expected = ans.sessions[bv]
        assert expected.difference(cal.early_closes).empty

    def test_early_closes_weekdays_time(
        self,
        default_calendar,
        early_closes_weekdays_sample,
        early_closes_weekdays_sample_time,
    ):
        """Test weekday early close time of calendar-specific sample of sessions.

        Notes
        -----
        TEST RELIES ON ACCURACY OF CALENDAR PROPERTIES `closes`, `tz` and
        `close_offset`.
        """
        if (
            not early_closes_weekdays_sample
            and early_closes_weekdays_sample_time is None
        ):
            return
        cal, tz = default_calendar, default_calendar.tz
        offset = pd.Timedelta(cal.close_offset, "D") + early_closes_weekdays_sample_time
        for date in early_closes_weekdays_sample:
            early_close = cal.closes[date].tz_convert(tz)
            expected = pd.Timestamp(date, tz=tz) + offset
            assert early_close == expected

    def test_non_early_closes_sample(self, default_calendar, non_early_closes_sample):
        """Test calendar-specific sample of sessions are not early closes."""
        if non_early_closes_sample:
            for date in non_early_closes_sample:
                assert T(date) not in default_calendar.early_closes

    def test_non_early_closes_sample_time(
        self, default_calendar, non_early_closes_sample, non_early_closes_sample_time
    ):
        """Test close time of calendar-specific sample of sessions with normal closes.

        Notes
        -----
        TEST RELIES ON ACCURACY OF CALENDAR PROPERTIES `closes`, `tz` and
        `close_offset`.
        """
        if non_early_closes_sample_time is not None:
            cal, tz = default_calendar, default_calendar.tz
            offset = pd.Timedelta(cal.close_offset, "D") + non_early_closes_sample_time
            for date in non_early_closes_sample:
                close = cal.closes[date].tz_convert(tz)
                expected_close = pd.Timestamp(date, tz=tz) + offset
                assert close == expected_close

    def test_late_opens(self, default_calendar, late_opens):
        """Test late opens.

        Notes
        -----
        TEST RELIES ON ACCURACY OF CALENDAR PROPERTIES `open_times` and
        `tz`. See `late_opens` fixture.
        """
        tm.assert_index_equal(late_opens, default_calendar.late_opens.unique())

    def test_early_closes(self, default_calendar, early_closes):
        """Test early closes.

        Notes
        -----
        TEST RELIES ON ACCURACY OF CALENDAR PROPERTIES `close_times` and
        `tz`. See `early_closes` fixture.
        """
        tm.assert_index_equal(early_closes, default_calendar.early_closes.unique())

    # Tests for methods that interrogate a given session.

    def test_session_open_close_break_start_end(self, default_calendar_with_answers):
        """Test methods that get session open, close, break_start, break_end.

        Tests following calendar methods:
            session_open
            session_close
            session_open_close
            session_break_start
            session_break_end
            session_break_start_end
        """
        # considered sufficient to limit test to sessions of session blocks.
        cal, ans = default_calendar_with_answers
        for _, block in ans.session_block_generator():
            for session in block:
                ans_open = ans.opens[session]
                ans_close = ans.closes[session]
                assert cal.session_open(session, _parse=False) == ans_open
                assert cal.session_close(session, _parse=False) == ans_close
                assert cal.session_open_close(session, _parse=False) == (
                    ans_open,
                    ans_close,
                )

                break_start = cal.session_break_start(session, _parse=False)
                break_end = cal.session_break_end(session, _parse=False)
                break_start_and_end = cal.session_break_start_end(session, _parse=False)
                ans_break_start = ans.break_starts[session]
                ans_break_end = ans.break_ends[session]
                if pd.isna(ans_break_start):
                    assert pd.isna(break_start) and pd.isna(break_end)
                    assert pd.isna(break_start_and_end[0])
                    assert pd.isna(break_start_and_end[1])
                else:
                    assert break_start == ans_break_start
                    assert break_end == ans_break_end
                    assert break_start_and_end[0] == ans_break_start
                    assert break_start_and_end[1] == ans_break_end

    def test_session_minute_methods(self, all_calendars_with_answers):
        """Test methods that get a minute bound of a session or subsession.

        Tests following calendar methods:
            session_first_minute
            session_last_minute
            session_last_am_minute
            session_first_pm_minute
            session_first_last_minute
        """
        # considered sufficient to limit test to sessions of session blocks.
        cal, ans = all_calendars_with_answers
        for _, block in ans.session_block_generator():
            for session in block:
                ans_first_minute = ans.first_minutes[session]
                ans_last_minute = ans.last_minutes[session]
                assert (
                    cal.session_first_minute(session, _parse=False) == ans_first_minute
                )
                assert cal.session_last_minute(session, _parse=False) == ans_last_minute
                assert cal.session_first_last_minute(session, _parse=False) == (
                    ans_first_minute,
                    ans_last_minute,
                )

                last_am_minute = cal.session_last_am_minute(session, _parse=False)
                first_pm_minute = cal.session_first_pm_minute(session, _parse=False)
                ans_last_am_minute = ans.last_am_minutes[session]
                ans_first_pm_minute = ans.first_pm_minutes[session]
                if pd.isna(ans_last_am_minute):
                    assert pd.isna(last_am_minute) and pd.isna(first_pm_minute)
                else:
                    assert last_am_minute == ans_last_am_minute
                    assert first_pm_minute == ans_first_pm_minute

    def test_session_has_break(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        f = no_parsing(cal.session_has_break)

        # test every 10th session...
        for session in ans.sessions_with_break[::10]:
            assert f(session)
        for session in ans.sessions_without_break[::10]:
            assert not f(session)

    def test_next_prev_session(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        f_prev = no_parsing(cal.previous_session)
        f_next = no_parsing(cal.next_session)

        # NB non-sessions handled by methods via parse_session

        # first session
        match = "Requested session would fall before the calendar's first session"
        with pytest.raises(errors.RequestedSessionOutOfBounds, match=match):
            f_prev(ans.first_session)

        # middle sessions (and m_prev for last session)
        for session, next_session in zip(ans.sessions[:-1], ans.sessions[1:]):
            assert f_next(session) == next_session
            assert f_prev(next_session) == session

        # last session
        match = "Requested session would fall after the calendar's last session"
        with pytest.raises(errors.RequestedSessionOutOfBounds, match=match):
            f_next(ans.last_session)

    def test_session_minutes(self, all_calendars_with_answers):
        cal, ans = all_calendars_with_answers
        f = no_parsing(cal.session_minutes)

        # Limit test to every session of each session block.

        for _, block in ans.session_block_generator():
            for session in block:
                tm.assert_index_equal(f(session), ans.get_sessions_minutes(session))

    def test_session_offset(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        f = no_parsing(cal.session_offset)

        for _, block_sessions in ans.session_block_generator():
            num_sessions = max(len(block_sessions), 5)
            session = block_sessions[0]
            try:
                sessions = ans.get_next_sessions(session, num_sessions)
            except IndexError:
                sessions = ans.get_next_sessions(session, len(block_sessions))
            for i in range(len(sessions)):
                offset_session = f(session, i)
                assert offset_session == sessions[i]

        for _, block_sessions in ans.session_block_generator():
            num_sessions = max(len(block_sessions), 5)
            session = block_sessions[-1]
            try:
                sessions = ans.get_prev_sessions(session, num_sessions)
            except IndexError:
                sessions = ans.get_prev_sessions(session, len(block_sessions))
            for i in range(len(sessions)):
                offset_session = f(session, -i)
                assert offset_session == sessions[-(i + 1)]

        # verify raises errors
        offset_session = f(ans.first_session, 0)
        assert offset_session == ans.first_session
        with pytest.raises(errors.RequestedSessionOutOfBounds, match="before"):
            offset_session = f(ans.first_session, -1)

        offset_session = f(ans.last_session, 0)
        assert offset_session == ans.last_session
        with pytest.raises(errors.RequestedSessionOutOfBounds, match="after"):
            f(ans.last_session, 1)

    # Tests for methods that interrogate a date.

    def test_is_session(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        f = no_parsing(cal.is_session)

        for session in ans.sessions:
            assert f(session)

        for session in ans.non_sessions:
            assert not f(session)

    def test_date_to_session(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        f = no_parsing(cal.date_to_session)

        sessions = ans.sessions

        # direction as "previous"
        dates = pd.date_range(sessions[0], sessions[-1], freq="D")
        date_is_session = dates.isin(sessions)

        last_session = None
        for date, is_session in zip(dates, date_is_session):
            session_label = f(date, "previous")
            if is_session:
                assert session_label == date
                last_session = session_label
            else:
                assert session_label == last_session

        # direction as "next"
        last_session = None
        for date, is_session in zip(
            dates.sort_values(ascending=False), date_is_session[::-1]
        ):
            session_label = f(date, "next")
            if date in sessions:
                assert session_label == date
                last_session = session_label
            else:
                assert session_label == last_session

        # test for non_sessions without direction
        if not ans.non_sessions.empty:
            for non_session in ans.non_sessions[0 : None : len(ans.non_sessions) // 9]:
                error_msg = (
                    f"`date` '{non_session}' does not represent a session. Consider"
                    " passing a `direction`."
                )
                with pytest.raises(ValueError, match=re.escape(error_msg)):
                    f(non_session, "none")
                # test default behaviour
                with pytest.raises(ValueError, match=re.escape(error_msg)):
                    f(non_session)

            # non-valid direction (only raised if pass a date that is not a session)
            error_msg = (
                "'not a direction' is not a valid `direction`. Valid `direction`"
                ' values are "next", "previous" and "none".'
            )
            with pytest.raises(ValueError, match=re.escape(error_msg)):
                f(non_session, "not a direction")

    # Tests for methods that interrogate a given minute (trading or non-trading)

    def test_is_trading_minute(self, all_calendars_with_answers):
        calendar, ans = all_calendars_with_answers
        f = no_parsing(calendar.is_trading_minute)

        for non_trading_min in ans.non_trading_minutes_only():
            assert f(non_trading_min) is False

        for trading_min in ans.trading_minutes_only():
            assert f(trading_min) is True

        for break_min in ans.break_minutes_only():
            assert f(break_min) is False

    def test_is_break_minute(self, all_calendars_with_answers):
        calendar, ans = all_calendars_with_answers
        f = no_parsing(calendar.is_break_minute)

        for non_trading_min in ans.non_trading_minutes_only():
            assert f(non_trading_min) is False

        for trading_min in ans.trading_minutes_only():
            assert f(trading_min) is False

        for break_min in ans.break_minutes_only():
            assert f(break_min) is True

    def test_is_open_on_minute(self, all_calendars_with_answers):
        calendar, ans = all_calendars_with_answers
        f = no_parsing(calendar.is_open_on_minute)

        # minimal test as is_open_on_minute delegates evaluation to is_trading_minute
        # and is_break_minute, both of which are comprehensively tested.

        for non_trading_min in itertools.islice(ans.non_trading_minutes_only(), 50):
            assert f(non_trading_min) is False

        for trading_min in itertools.islice(ans.trading_minutes_only(), 50):
            assert f(trading_min) is True

        for break_min in ans.break_minutes_only():
            rtrn = f(break_min, ignore_breaks=True)
            assert rtrn is True
            rtrn = f(break_min)
            assert rtrn is False

    def test_is_open_at_time(self, all_calendars_with_answers, one_minute):
        cal, ans = all_calendars_with_answers

        one_min = one_minute
        one_sec = pd.Timedelta(1, "S")

        sides = ("left", "both", "right", "neither")

        # verify raises expected errors
        oob_time = ans.first_minute - one_sec
        for side in sides:
            with pytest.raises(errors.MinuteOutOfBounds):
                cal.is_open_at_time(oob_time, side, ignore_breaks=True)

        match = (
            "`timestamp` expected to receive type pd.Timestamp although got type"
            " <class 'str'>."
        )
        with pytest.raises(TypeError, match=match):
            cal.is_open_at_time("2022-06-21 14:22", "left", ignore_breaks=True)

        # verify expected returns
        bools = (True, False)

        def get_returns(
            ts: pd.Timestamp,
            ignore_breaks: bool,
        ) -> list[bool]:
            return [cal.is_open_at_time(ts, side, ignore_breaks) for side in sides]

        gap_before = ans.sessions_with_gap_before
        gap_after = ans.sessions_with_gap_after

        for session in ans.sessions_sample:
            ts = ans.opens[session]
            expected = [True, True, False, False]
            expected_no_gap = [True, True, True, False]
            if ts > ans.first_minute:
                for ignore in bools:
                    expected_ = expected if session in gap_before else expected_no_gap
                    assert get_returns(ts, ignore) == expected_

                for ignore, ts_ in itertools.product(
                    bools, (ts - one_sec, ts - one_min)
                ):
                    if session in gap_before:
                        assert not any(get_returns(ts_, ignore))
                    else:
                        assert all(get_returns(ts_, ignore))

                for ignore, ts_ in itertools.product(
                    bools, (ts + one_sec, ts + one_min)
                ):
                    assert all(get_returns(ts_, ignore))

            if ans.session_has_break(session):
                ts = ans.break_ends[session]
                assert get_returns(ts, ignore_breaks=False) == expected
                assert all(get_returns(ts, ignore_breaks=True))

                for ignore, ts_ in itertools.product(
                    bools, (ts + one_sec, ts + one_min)
                ):
                    assert all(get_returns(ts_, ignore))

                for ts_ in (ts - one_sec, ts - one_min):
                    assert not any(get_returns(ts_, ignore_breaks=False))
                    assert all(get_returns(ts_, ignore_breaks=True))

            ts = ans.closes[session]
            expected = [False, True, True, False]
            expected_no_gap = [True, True, True, False]
            if ts < ans.last_minute:
                for ignore in bools:
                    expected_ = expected if session in gap_after else expected_no_gap
                    # check interprets tz-naive timestamp as UTC
                    assert get_returns(ts.astimezone(None), ignore) == expected_

                for ignore, ts_ in itertools.product(
                    bools, (ts - one_sec, ts - one_min)
                ):
                    assert all(get_returns(ts_, ignore))

                for ignore, ts_ in itertools.product(
                    bools, (ts + one_sec, ts + one_min)
                ):
                    if session in gap_after:
                        assert not any(get_returns(ts_, ignore))
                    else:
                        assert all(get_returns(ts_.astimezone(None), ignore))

            if ans.session_has_break(session):
                ts = ans.break_starts[session]
                assert get_returns(ts, ignore_breaks=False) == expected
                assert all(get_returns(ts, ignore_breaks=True))

                for ignore, ts_ in itertools.product(
                    bools, (ts - one_sec, ts - one_min)
                ):
                    assert all(get_returns(ts_, ignore))

                for ts_ in (ts + one_sec, ts + one_min):
                    assert not any(get_returns(ts_, ignore_breaks=False))
                    assert all(get_returns(ts_, ignore_breaks=True))

    def test_prev_next_open_close(self, default_calendar_with_answers):
        """Test methods that return previous/next open/close.

        Tests methods:
            previous_open
            previous_close
            next_open
            next_close
        """
        cal, ans = default_calendar_with_answers
        generator = ans.prev_next_open_close_minutes()

        for minute, (prev_open, prev_close, next_open, next_close) in generator:
            if prev_open is None:
                with pytest.raises(ValueError):
                    cal.previous_open(minute, _parse=False)
            else:
                assert cal.previous_open(minute, _parse=False) == prev_open

            if prev_close is None:
                with pytest.raises(ValueError):
                    cal.previous_close(minute, _parse=False)
            else:
                assert cal.previous_close(minute, _parse=False) == prev_close

            if next_open is None:
                with pytest.raises(ValueError):
                    cal.next_open(minute, _parse=False)
            else:
                assert cal.next_open(minute, _parse=False) == next_open

            if next_close is None:
                with pytest.raises(ValueError):
                    cal.next_close(minute, _parse=False)
            else:
                assert cal.next_close(minute, _parse=False) == next_close

    def test_prev_next_minute(self, all_calendars_with_answers, one_minute):
        """Test methods that return previous/next minute.

        Test focuses on and inside of edge cases.

        Tests methods:
            next_minute
            previous_minute
        """
        cal, ans = all_calendars_with_answers
        f_next = no_parsing(cal.next_minute)
        f_prev = no_parsing(cal.previous_minute)

        # minutes of first session
        first_min = ans.first_minutes[0]
        first_min_plus_one = ans.first_minutes_plus_one[0]
        first_min_less_one = ans.first_minutes_less_one[0]
        last_min = ans.last_minutes[0]
        last_min_plus_one = ans.last_minutes_plus_one[0]
        last_min_less_one = ans.last_minutes_less_one[0]

        match = "Requested minute would fall before the calendar's first trading minute"
        with pytest.raises(errors.RequestedMinuteOutOfBounds, match=match):
            f_prev(first_min)
        # minutes earlier than first_minute assumed handled via parse_timestamp
        assert f_next(first_min) == first_min_plus_one
        assert f_next(first_min_plus_one) == first_min_plus_one + one_minute
        assert f_prev(first_min_plus_one) == first_min
        assert f_prev(last_min) == last_min_less_one
        assert f_prev(last_min_less_one) == last_min_less_one - one_minute
        assert f_next(last_min_less_one) == last_min
        assert f_prev(last_min_plus_one) == last_min

        prev_last_min = last_min
        for (
            first_min,
            first_min_plus_one,
            first_min_less_one,
            last_min,
            last_min_plus_one,
            last_min_less_one,
            gap_before,
        ) in zip(
            ans.first_minutes[1:],
            ans.first_minutes_plus_one[1:],
            ans.first_minutes_less_one[1:],
            ans.last_minutes[1:],
            ans.last_minutes_plus_one[1:],
            ans.last_minutes_less_one[1:],
            ~ans._mask_sessions_without_gap_before[1:],
        ):
            assert f_next(prev_last_min) == first_min
            assert f_prev(first_min) == prev_last_min
            assert f_next(first_min) == first_min_plus_one
            assert f_prev(first_min_plus_one) == first_min
            assert f_next(first_min_less_one) == first_min
            assert f_prev(last_min) == last_min_less_one
            assert f_next(last_min_less_one) == last_min
            assert f_prev(last_min_plus_one) == last_min

            if gap_before:
                assert f_next(prev_last_min + one_minute) == first_min
                assert f_prev(first_min_less_one) == prev_last_min
            else:
                assert f_next(prev_last_min + one_minute) == first_min_plus_one
                assert f_next(prev_last_min + one_minute) == first_min_plus_one

            prev_last_min = last_min

        match = "Requested minute would fall after the calendar's last trading minute"
        with pytest.raises(errors.RequestedMinuteOutOfBounds, match=match):
            f_next(last_min)
        # minutes later than last_minute assumed handled via parse_timestamp

        if ans.has_a_session_with_break:
            for (
                last_am_min,
                last_am_min_less_one,
                last_am_min_plus_one,
                first_pm_min,
                first_pm_min_less_one,
                first_pm_min_plus_one,
            ) in zip(
                ans.last_am_minutes,
                ans.last_am_minutes_less_one,
                ans.last_am_minutes_plus_one,
                ans.first_pm_minutes,
                ans.first_pm_minutes_less_one,
                ans.first_pm_minutes_plus_one,
            ):
                if pd.isna(last_am_min):
                    continue
                assert f_next(last_am_min_less_one) == last_am_min
                assert f_next(last_am_min) == first_pm_min
                assert f_prev(last_am_min) == last_am_min_less_one
                assert f_next(last_am_min_plus_one) == first_pm_min
                assert f_prev(last_am_min_plus_one) == last_am_min

                assert f_prev(first_pm_min_less_one) == last_am_min
                assert f_next(first_pm_min_less_one) == first_pm_min
                assert f_prev(first_pm_min) == last_am_min
                assert f_next(first_pm_min) == first_pm_min_plus_one
                assert f_prev(first_pm_min_plus_one) == first_pm_min

    def test_minute_to_session(self, all_calendars_with_answers, all_directions):
        direction = all_directions
        calendar, ans = all_calendars_with_answers
        f = no_parsing(calendar.minute_to_session)

        for non_trading_mins, prev_session, next_session in ans.non_trading_minutes:
            for non_trading_min in non_trading_mins:
                if direction == "none":
                    with pytest.raises(ValueError):
                        f(non_trading_min, direction)
                else:
                    session = f(non_trading_min, direction)
                    if direction == "next":
                        assert session == next_session
                    else:
                        assert session == prev_session

        for trading_minutes, session in ans.trading_minutes:
            for trading_minute in trading_minutes:
                rtrn = f(trading_minute, direction)
                assert rtrn == session

        if ans.has_a_session_with_break:
            for break_minutes, session in ans.break_minutes[:15]:
                for break_minute in break_minutes:
                    rtrn = f(break_minute, direction)
                    assert rtrn == session

        oob_minute = ans.minute_too_early
        if direction in ["previous", "none"]:
            error_msg = (
                f"Received `minute` as '{oob_minute}' although this is earlier than"
                f" the calendar's first trading minute ({ans.first_minute})"
            )
            with pytest.raises(ValueError, match=re.escape(error_msg)):
                f(oob_minute, direction)
        else:
            session = f(oob_minute, direction)
            assert session == ans.first_session

        oob_minute = ans.minute_too_late
        if direction in ["next", "none"]:
            error_msg = (
                f"Received `minute` as '{oob_minute}' although this is later"
                f" than the calendar's last trading minute ({ans.last_minute})"
            )
            with pytest.raises(ValueError, match=re.escape(error_msg)):
                f(oob_minute, direction)
        else:
            session = f(oob_minute, direction)
            assert session == ans.last_session

    def test_minute_to_past_session(self, all_calendars_with_answers, one_minute):
        """
        Only lightly tested given method is little more than a wrapper over
        comprehensively tested methods.
        """
        cal, ans = all_calendars_with_answers
        f = no_parsing(cal.minute_to_past_session)

        for _, block_sessions in ans.session_block_generator():
            num_sessions = max(len(block_sessions), 5)
            session = block_sessions[-1]
            try:
                sessions = ans.get_prev_sessions(session, num_sessions)
            except IndexError:
                sessions = ans.get_prev_sessions(session, len(block_sessions))

            num_sessions = len(sessions)
            prev_session = sessions[-2]
            first_minute = ans.first_minutes[session]
            # trading_minutes
            minutes = [first_minute, ans.last_minutes[session]]
            if ans.session_has_break(session):
                # break minutes
                minutes.append(ans.last_am_minutes[session] + one_minute)
                minutes.append(ans.first_pm_minutes[session] - one_minute)
            if session in ans.sessions_with_gap_before:
                # non break minutes
                minutes.append(first_minute - one_minute)
                minutes.append(ans.last_minutes[prev_session] + one_minute)

            for i in range(1, num_sessions - 1):
                rtrn = sessions[-(i + 1)]  # all minutes should resolve to this session.
                for minute in minutes:
                    assert rtrn == f(minute, i)

        # verify raises errors.
        for count in [0, -1]:
            with pytest.raises(ValueError):
                f(minute, count)

    def test_minute_to_future_session(self, all_calendars_with_answers, one_minute):
        """
        Only lightly tested given method is little more than a wrapper over
        comprehensively tested methods.
        """
        cal, ans = all_calendars_with_answers
        f = no_parsing(cal.minute_to_future_session)

        for _, block_sessions in ans.session_block_generator():
            num_sessions = max(len(block_sessions), 5)
            session = block_sessions[0]
            try:
                sessions = ans.get_next_sessions(session, num_sessions)
            except IndexError:
                sessions = ans.get_next_sessions(session, len(block_sessions))

            num_sessions = len(sessions)
            next_session = sessions[1]
            last_minute = ans.last_minutes[session]
            # trading_minutes
            minutes = [ans.first_minutes[session], last_minute]
            if ans.session_has_break(session):
                # break minutes
                minutes.append(ans.last_am_minutes[session] + one_minute)
                minutes.append(ans.first_pm_minutes[session] - one_minute)
            if session in ans.sessions_with_gap_after:
                # non break minutes
                minutes.append(last_minute + one_minute)
                minutes.append(ans.first_minutes[next_session] - one_minute)

            for i in range(1, num_sessions - 1):
                rtrn = sessions[i]  # all minutes should resolve to this session.
                for minute in minutes:
                    assert rtrn == f(minute, i)

        # verify raises errors.
        for count in [0, -1]:
            with pytest.raises(ValueError):
                f(minute, count)

    def test_minute_to_trading_minute(self, all_calendars_with_answers, all_directions):
        """
        Limited testing as tested method is simply a filter for
        comprehensively tested methods.
        """
        direction = all_directions
        calendar, ans = all_calendars_with_answers
        f = no_parsing(calendar.minute_to_trading_minute)

        for minute in itertools.islice(ans.trading_minutes_only(), 6):
            assert minute == f(minute, direction=direction)

        for minutes, session in ans.break_minutes[:1]:
            for minute in minutes:
                if direction == "previous":
                    f(minute, direction) == ans.last_am_minutes[session]
                elif direction == "next":
                    f(minute, direction) == ans.first_pm_minutes[session]
                else:
                    error_msg = (
                        f"`minute` '{minute}' is not a trading minute. Consider passing"
                        " `direction` as 'next' or 'previous'."
                    )
                    with pytest.raises(ValueError, match=re.escape(error_msg)):
                        f(minute, direction)

        for minutes, prev_session, next_session in ans.non_trading_minutes[:1]:
            for minute in minutes:
                if direction == "previous":
                    assert f(minute, direction) == ans.last_minutes[prev_session]
                elif direction == "next":
                    assert f(minute, direction) == ans.first_minutes[next_session]
                else:
                    error_msg = f"`minute` '{minute}' is not a trading minute."
                    with pytest.raises(ValueError, match=re.escape(error_msg)):
                        f(minute, direction)

    def test_minute_offset(self, all_calendars_with_answers, one_minute):
        calendar, ans = all_calendars_with_answers
        f = no_parsing(calendar.minute_offset)

        for _, sessions in ans.session_block_generator():
            for i, session in enumerate(sessions):

                # intra session
                first_minute = ans.first_minutes[session]
                rtrn = f(first_minute + pd.Timedelta(20, "T"), 10)
                assert rtrn == first_minute + pd.Timedelta(30, "T")

                last_minute = ans.last_minutes[session]
                rtrn = f(last_minute - pd.Timedelta(20, "T"), -10)
                assert rtrn == last_minute - pd.Timedelta(30, "T")

                # crossing break
                if ans.session_has_break(session):
                    last_am_minute = ans.last_am_minutes[session]
                    first_pm_minute = ans.first_pm_minutes[session]

                    rtrn = f(last_am_minute - one_minute, 3)
                    assert rtrn == first_pm_minute + one_minute

                    rtrn = f(first_pm_minute + one_minute, -3)
                    assert rtrn == last_am_minute - one_minute

                # crossing sessions
                prev_session = False if i == 0 else sessions[i - 1]
                next_session = False if i == len(sessions) - 1 else sessions[i + 1]
                if prev_session:
                    rtrn = f(first_minute + one_minute, -3)
                    assert rtrn == ans.last_minutes[prev_session] - one_minute

                if next_session:
                    rtrn = f(last_minute - one_minute, 3)
                    assert rtrn == ans.first_minutes[next_session] + one_minute

        # Verify raising expected errors.

        rtrn = f(ans.first_minute, 0)
        assert rtrn == ans.first_minute
        with pytest.raises(errors.RequestedMinuteOutOfBounds, match="before"):
            f(ans.first_minute, -1)

        rtrn = f(ans.last_minute, 0)
        assert rtrn == ans.last_minute
        with pytest.raises(errors.RequestedMinuteOutOfBounds, match="after"):
            f(ans.last_minute, 1)

    def test_minute_offset_by_sessions(self, all_calendars_with_answers):
        cal, ans = all_calendars_with_answers
        f = no_parsing(cal.minute_offset_by_sessions)
        delta_int = 20
        delta = pd.Timedelta(delta_int, "T")

        # tests for rtrn with same time.

        def assertions(
            minute: pd.Timestamp,
            target_session: pd.Timestamp,
            rtrn: pd.Timestamp,
        ):
            assert (rtrn.hour == minute.hour) and (rtrn.minute == minute.minute)
            assert rtrn >= ans.first_minutes[target_session]
            assert rtrn <= ans.last_minutes[target_session]

        sessions_unchanging_times_run = ans.sessions_unchanging_times_run

        session = sessions_unchanging_times_run[0]
        minutes = ans.get_session_edge_minutes(session, delta_int)
        target_sessions = sessions_unchanging_times_run[1:6]
        for i, target_session in enumerate(target_sessions):
            for minute in minutes:
                assertions(minute, target_session, f(minute, i + 1))

        session = sessions_unchanging_times_run[-1]
        minutes = ans.get_session_edge_minutes(session, delta_int)
        target_sessions = sessions_unchanging_times_run[-6:-1]
        for i, target_session in enumerate(reversed(target_sessions)):
            for minute in minutes:
                assertions(minute, target_session, f(minute, -(i + 1)))

        sessions = ans.sessions_next_close_later[-5:]
        for session in sessions:
            target_session = ans.get_next_session(session)
            minute_ = ans.last_minutes[session]
            for minute in [minute_, minute_ - delta]:
                assertions(minute, target_session, f(minute, 1))

        target_sessions = ans.sessions_next_close_earlier[-5:]
        for target_session in target_sessions:
            session = ans.get_next_session(target_session)  # previous close later
            minute_ = ans.last_minutes[session]
            for minute in [minute_, minute_ - delta]:
                assertions(minute, target_session, f(minute, -1))

        sessions = ans.sessions_next_open_earlier[-5:]
        for session in sessions:
            target_session = ans.get_next_session(session)
            minute_ = ans.first_minutes[session]
            for minute in [minute_, minute_ + delta]:
                assertions(minute, target_session, f(minute, 1))

        target_sessions = ans.sessions_next_open_later[-5:]
        for target_session in target_sessions:
            session = ans.get_next_session(target_session)  # previous open earlier
            minute_ = ans.first_minutes[session]
            for minute in [minute_, minute_ + delta]:
                assertions(minute, target_session, f(minute, -1))

        if ans.has_a_session_with_break:

            sessions = ans.sessions_next_break_start_later[-5:]
            for session in sessions:
                target_session = ans.get_next_session(session)
                minute_ = ans.last_am_minutes[session]
                for minute in [minute_, minute_ - delta]:
                    assertions(minute, target_session, f(minute, 1))

            target_sessions = ans.sessions_next_break_start_earlier[-5:]
            for target_session in target_sessions:
                session = ans.get_next_session(target_session)  # prev break start later
                minute_ = ans.last_am_minutes[session]
                for minute in [minute_, minute_ - delta]:
                    assertions(minute, target_session, f(minute, -1))

            sessions = ans.sessions_next_break_end_earlier[-5:]
            for session in sessions:
                target_session = ans.get_next_session(session)
                minute_ = ans.first_pm_minutes[session]
                for minute in [minute_, minute_ + delta]:
                    assertions(minute, target_session, f(minute, 1))

            target_sessions = ans.sessions_next_break_end_later[-5:]
            for target_session in target_sessions:
                session = ans.get_next_session(target_session)  # prev break end earlier
                minute_ = ans.first_pm_minutes[session]
                for minute in [minute_, minute_ + delta]:
                    assertions(minute, target_session, f(minute, -1))

        # tests for rtrn with different time.

        sessions = ans.sessions_next_close_earlier[-5:]
        if ans.sessions[-2] in sessions:  # guard against offset minute exceeding bound
            sessions = sessions[sessions != ans.sessions[-2]]
        for session in sessions:
            target_session = ans.get_next_session(session)
            minute = ans.last_minutes[session]
            assert f(minute, 1) == ans.last_minutes[target_session]

        target_sessions = ans.sessions_next_close_later[-5:]
        for target_session in target_sessions:
            session = ans.get_next_session(target_session)  # previous close earlier
            minute = ans.last_minutes[session]
            assert f(minute, -1) == ans.last_minutes[target_session]

        sessions = ans.sessions_next_open_later[-5:]
        for session in sessions:
            target_session = ans.get_next_session(session)
            minute = ans.first_minutes[session]
            assert f(minute, 1) == ans.first_minutes[target_session]

        target_sessions = ans.sessions_next_open_earlier[-5:]
        if ans.sessions[1] in sessions:  # guard against offset minute exceeding bound
            sessions = sessions[sessions != ans.sessions[1]]
        for target_session in target_sessions:
            session = ans.get_next_session(target_session)  # previous open later
            minute = ans.first_minutes[session]
            assert f(minute, -1) == ans.first_minutes[target_session]

        # tests for trading minutes that would otherwise offset to a break minute.

        for minute, _, target_session in ans.trading_minute_to_break_minute_next:
            assert f(minute, 1) == ans.last_am_minutes[target_session]

        for minute, _, target_session in ans.trading_minute_to_break_minute_prev:
            assert f(minute, -1) == ans.last_am_minutes[target_session]

        # Verify expected errors raised.

        minutes = [ans.first_minutes[ans.last_session], ans.last_minute]
        for minute in minutes:
            for i in range(1, 3):
                with pytest.raises(errors.RequestedMinuteOutOfBounds, match="after"):
                    f(minute, i)

        minutes = [ans.first_minute, ans.last_minutes[ans.first_session]]
        for minute in minutes:
            for i in range(-2, 0):
                with pytest.raises(errors.RequestedMinuteOutOfBounds, match="before"):
                    f(minute, i)

    # Tests for methods that evaluate or interrogate a range of minutes.

    def test_minutes_in_range(self, all_calendars_with_answers, one_minute):
        cal, ans = all_calendars_with_answers
        f = no_parsing(cal.minutes_in_range)

        block_minutes = ans.session_block_minutes
        for name, block in ans.session_block_generator():
            ans_dti = block_minutes[name]
            from_ = ans.first_minutes[block[0]]
            to = ans.last_minutes[block[-1]]
            cal_dti = f(from_, to)
            tm.assert_index_equal(ans_dti, cal_dti)

            # test consequence of getting range from one minute before/after the
            # block's first/last trading minute.
            if name in ["first_three", "last_three"]:
                continue
            cal_dti = f(from_ - one_minute, to + one_minute)
            start_idx = 1 if block[0] in ans.sessions_without_gap_before else 0
            end_idx = -1 if block[-1] in ans.sessions_without_gap_after else None
            tm.assert_index_equal(ans_dti, cal_dti[start_idx:end_idx])

        # intra-session
        from_ = ans.first_minutes[ans.first_session] + pd.Timedelta(15, "T")
        to = ans.first_minutes[ans.first_session] + pd.Timedelta(45, "T")
        expected = pd.date_range(from_, to, freq="T")
        rtrn = f(from_, to)
        tm.assert_index_equal(expected, rtrn)

        # inter-session
        if not ans.sessions_with_gap_after.empty:
            session = ans.sessions_with_gap_after[0]
            next_session = ans.get_next_session(session)
            from_ = ans.last_minutes[session] + one_minute
            to = ans.first_minutes[next_session] - one_minute
            assert f(from_, to).empty

    def test_minutes_window(self, all_calendars_with_answers):
        cal, ans = all_calendars_with_answers
        f = no_parsing(cal.minutes_window)

        block_minutes = ans.session_block_minutes
        for name, block in ans.session_block_generator():
            start = ans.first_minutes[block[0]]
            ans_dti = block_minutes[name]
            count = len(ans_dti)
            cal_dti = f(start, count)
            tm.assert_index_equal(ans_dti, cal_dti)

            start = ans.last_minutes[block[-1]]
            cal_dti = f(start, -count)
            tm.assert_index_equal(ans_dti, cal_dti)

        # intra-session
        from_ = ans.first_minutes[ans.first_session] + pd.Timedelta(15, "T")
        count = 30
        expected = pd.date_range(from_, periods=count, freq="T")
        rtrn = f(from_, count)
        tm.assert_index_equal(expected, rtrn)

        # inter-session
        if not ans.sessions_with_gap_after.empty:
            session = ans.sessions_with_gap_after[0]
            next_session = ans.get_next_session(session)
            from_ = ans.last_minutes[session] - pd.Timedelta(4, "T")
            count = 10
            expected_1 = pd.date_range(from_, periods=5, freq="T")
            from_2 = ans.first_minutes[next_session]
            expected_2 = pd.date_range(from_2, periods=5, freq="T")
            expected = expected_1.union(expected_2)
            rtrn = f(from_, count)
            tm.assert_index_equal(expected, rtrn)

        # verify raises ValueError when window extends beyond calendar's minute bounds
        # at limit, window starts on first calendar minute
        delta = pd.Timedelta(2, "T")
        minute = ans.first_minute + delta
        assert f(minute, count=-3)[0] == ans.first_minute
        # window would start before first calendar minute
        match = re.escape(
            "Minutes window cannot begin before the calendar's first minute"
            f" ({ans.first_minute}). `count` cannot be lower than -3 for `minute`"
            f" '{minute}'."
        )
        with pytest.raises(ValueError, match=match):
            f(minute, count=-4)

        # at limit, window ends on last calendar minute
        minute = ans.last_minute - delta
        assert f(minute, count=3)[-1] == ans.last_minute
        # window would end after last calendar minute
        match = re.escape(
            "Minutes window cannot end after the calendar's last minute"
            f" ({ans.last_minute}). `count` cannot be higher than 3 for `minute`"
            f" '{minute}'."
        )
        with pytest.raises(ValueError):
            f(minute, count=4)

        # verify raises ValueError if `count` passed as 0
        with pytest.raises(ValueError, match="`count` cannot be 0."):
            f(ans.first_minute, count=0)

    def test_minutes_distance(self, all_calendars_with_answers, one_minute):
        cal, ans = all_calendars_with_answers
        f = no_parsing(cal.minutes_distance)

        for mins in ans.session_block_minutes.values():
            if mins.empty:
                continue
            mins = mins[7:-7]
            distance = len(mins)
            assert f(mins[0], mins[-1]) == distance
            assert f(mins[-1], mins[0]) == -distance

        # test for same start / end
        assert f(ans.trading_minute, ans.trading_minute) == 1

        # tests where start and end are non-trading minutes
        if ans.non_trading_minutes:
            # test that range within which there are no minutes returns 0
            assert f(*ans.non_trading_minutes[0][0]) == 0

            # test range defined with start and end as non-trading minutes
            sessions = ans.sessions_with_gap_before.intersection(
                ans.sessions_with_gap_after
            )
            if not sessions.empty:
                session = sessions[0]
                distance = len(ans.get_sessions_minutes(session, 1))
                start = ans.first_minutes[session] - one_minute
                end = ans.last_minutes[session] + one_minute
                assert f(start, end) == distance

    def test_minutes_to_sessions(self, all_calendars_with_answers):
        calendar, ans = all_calendars_with_answers
        f = calendar.minutes_to_sessions

        trading_minute = ans.trading_minute
        for minute in ans.non_trading_minutes_only():
            with pytest.raises(ValueError):
                f(pd.DatetimeIndex([minute]))
            with pytest.raises(ValueError):
                f(pd.DatetimeIndex([trading_minute, minute]))

        mins, sessions = [], []
        for trading_minutes, session in ans.trading_minutes[:30]:
            mins.extend(trading_minutes)
            sessions.extend([session] * len(trading_minutes))

        index = pd.DatetimeIndex(mins).sort_values()
        sessions_labels = f(index)
        tm.assert_index_equal(sessions_labels, pd.DatetimeIndex(sessions).sort_values())

    # Tests for methods that evaluate or interrogate a range of sessions.

    def test_sessions_in_range(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        f = no_parsing(cal.sessions_in_range)

        # test where start and end are sessions
        start, end = ans.sessions[10], ans.sessions[-10]
        tm.assert_index_equal(f(start, end), ans.sessions[10:-9])

        # test session blocks
        for _, block in ans.session_block_generator():
            tm.assert_index_equal(f(block[0], block[-1]), block)

        # tests where start and end are non-session dates
        if len(ans.non_sessions) > 1:
            # test that range within which there are no sessions returns empty
            assert f(*ans.non_sessions_range).empty

            # test range defined with start and end as non-sessions
            (start, end), sessions = ans.sessions_range_defined_by_non_sessions
            tm.assert_index_equal(f(start, end), sessions)

    def test_sessions_has_break(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        f = no_parsing(cal.sessions_has_break)

        has_a_break = ans.has_a_session_with_break
        assert f(ans.first_session, ans.last_session) == has_a_break

        if ans.has_a_session_without_break:
            assert not f(*ans.sessions_without_break_range)

            if has_a_break:
                # i.e. mixed, some sessions have a break, some don't
                block = ans.session_blocks["with_break_to_without_break"]
                if not block.empty:
                    # guard against starting with no breaks, then an introduction
                    # of breaks to every session after a certain date
                    # (i.e. there would be no with_break_to_without_break)
                    assert f(block[0], block[-1])
                block = ans.session_blocks["without_break_to_with_break"]
                if not block.empty:
                    # ...guard against opposite case (e.g. XKRX)
                    assert f(block[0], block[-1])
        else:
            # in which case all sessions must have a break. Make sure...
            assert cal.break_starts.notna().all()

    def test_sessions_window(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        f = no_parsing(cal.sessions_window)

        for _, block in ans.session_block_generator():
            count = len(block)
            tm.assert_index_equal(f(block[0], count), block)
            tm.assert_index_equal(f(block[-1], -count), block)

        # verify raises ValueError if window extends beyond calendar's session bounds.
        # at limit, window starts on first calendar session
        assert f(ans.sessions[2], count=-3)[0] == ans.first_session
        # window would start before first calendar session
        match = re.escape(
            "Sessions window cannot begin before the first calendar session"
            f" ({ans.first_session}). `count` cannot be lower than -3 for `session`"
            f" '{ans.sessions[2]}'."
        )
        with pytest.raises(ValueError, match=match):
            f(ans.sessions[2], count=-4)

        # at limit, window ends on last calendar session
        assert f(ans.sessions[-3], count=3)[-1] == ans.last_session
        # window would end after last calendar session
        match = re.escape(
            "Sessions window cannot end after the last calendar session"
            f" ({ans.last_session}). `count` cannot be higher than 3 for `session`"
            f" '{ans.sessions[-3]}'."
        )
        with pytest.raises(ValueError):
            f(ans.sessions[-3], count=4)

        # verify raises ValueError if `count` passed as 0
        with pytest.raises(ValueError, match="`count` cannot be 0."):
            f(ans.sessions[0], count=0)

    def test_sessions_distance(self, default_calendar_with_answers):
        cal, ans = default_calendar_with_answers
        f = no_parsing(cal.sessions_distance)

        for _, block in ans.session_block_generator():
            distance = len(block)
            assert f(block[0], block[-1]) == distance
            assert f(block[-1], block[0]) == -distance

        # test for same start / end
        assert f(ans.sessions[0], ans.sessions[0]) == 1

        # tests where start and end are non-session dates
        if len(ans.non_sessions) > 1:
            # test that range within which there are no sessions returns 0
            assert f(*ans.non_sessions_range) == 0

            # test range defined with start and end as non_sessions
            (start, end), sessions = ans.sessions_range_defined_by_non_sessions
            assert f(start, end) == len(sessions)

    def test_sessions_minutes(self, all_calendars_with_answers):
        cal, ans = all_calendars_with_answers
        f = no_parsing(cal.sessions_minutes)

        block_minutes = ans.session_block_minutes
        for name, block in ans.session_block_generator():
            ans_minutes = block_minutes[name]
            cal_minutes = f(block[0], block[-1])
            tm.assert_index_equal(ans_minutes, cal_minutes)

        # tests where start and end are non-session dates
        if len(ans.non_sessions) > 1:
            # test that range within which there are no sessions returns empty
            assert f(*ans.non_sessions_range).empty

            # test range defined with start and end as non-sessions
            (start, end), sessions = ans.sessions_range_defined_by_non_sessions
            minutes = ans.get_sessions_minutes(sessions[0], sessions[-1])
            tm.assert_index_equal(f(start, end), minutes)

    def test_sessions_minutes_count(self, all_calendars_with_answers):
        cal, ans = all_calendars_with_answers
        f = no_parsing(cal.sessions_minutes_count)

        block_minutes = ans.session_block_minutes
        for name, block in ans.session_block_generator():
            ans_minutes = len(block_minutes[name])
            cal_minutes = f(block[0], block[-1])
            assert cal_minutes == ans_minutes

        # tests where start and end are non-session dates
        if len(ans.non_sessions) > 1:
            # test that range within which there are no sessions returns 0
            assert f(*ans.non_sessions_range) == 0

            # test range defined with start and end as non-sessions
            (start, end), sessions = ans.sessions_range_defined_by_non_sessions
            minutes = ans.get_sessions_minutes(sessions[0], sessions[-1])
            assert f(start, end) == len(minutes)

        # Additional belt-and-braces test to reconcile with cal.minutes
        assert f(ans.first_session, ans.last_session) == len(cal.minutes)

    def test_trading_index(self, calendars, answers):
        """Test trading index with options as default values.

        Tests multitude of concrete cases covering product of all
        session blocks and various periods.

        Assumes default value (False) for each of `force_close`,
        `force_break_close` and `curtail_overlaps`. See test class
        `test_calendar_helpers.TestTradingIndex` for more comprehensive
        testing (including fuzz tests and parsing tests).
        """
        cal, ans = calendars["left"], answers["left"]

        def unite(dtis: list[pd.DatetimeIndex]) -> pd.DatetimeIndex:
            return dtis[0].append(dtis[1:])  # append to not sort or remove duplicates

        for _, sessions in ans.session_block_generator():
            for mins in [5, 17, 60, 123, 333, 1033]:
                period = pd.Timedelta(mins, "T")
                dtis = []
                for session in sessions:
                    indexes = ans.get_session_minutes(session)
                    for i, index in enumerate(indexes):
                        # Create closed 'both' trading index for each session/subsession
                        if i == 0 and len(indexes) == 2:
                            ends = ans.break_starts
                        else:
                            ends = ans.closes
                        # index for a 'left' calendar, add end so evaluated as if 'both'
                        index = index.append(pd.DatetimeIndex([ends[session]]))

                        index = index[::mins]  # only want every period
                        if not index[-1] == ends[session]:
                            # if period doesn't coincide with end, add right side of
                            # last interval which lies beyond end.
                            last_indice = index[-1] + period
                            index = index.append(pd.DatetimeIndex([last_indice]))
                        dtis.append(index)

                both_index = unite(dtis)
                left_index = unite([dti[:-1] for dti in dtis])
                right_index = unite([dti[1:] for dti in dtis])
                neither_index = unite([dti[1:-1] for dti in dtis])

                overlaps = (right_index[:-1] > left_index[1:]).any()
                if overlaps:
                    both_overlaps = overlaps
                else:
                    both_overlaps = False
                    for dti, next_dti in zip(dtis, dtis[1:]):
                        if dti[-1] == next_dti[0]:
                            both_overlaps = True
                            break

                def get_index(closed: str, intervals: bool):
                    start, end = sessions[0], sessions[-1]
                    return cal.trading_index(
                        start, end, period, intervals, closed, parse=False
                    )

                def tst_indices_index(
                    expected: pd.DatetimeIndex, closed: str, overlaps: bool
                ):
                    if not overlaps:
                        rtrn = get_index(closed, False)
                        pd.testing.assert_index_equal(expected, rtrn)
                    else:
                        with pytest.raises(errors.IndicesOverlapError):
                            get_index(closed, False)

                tst_indices_index(both_index, "both", both_overlaps)
                tst_indices_index(left_index, "left", False)
                tst_indices_index(right_index, "right", overlaps)
                tst_indices_index(neither_index, "neither", False)

                def tst_intervals_index(closed: str, overlaps: bool):
                    if not overlaps:
                        rtrn = get_index(closed, True)
                        expected = pd.IntervalIndex.from_arrays(
                            left_index, right_index, closed
                        )
                        pd.testing.assert_index_equal(expected, rtrn)
                    else:
                        with pytest.raises(errors.IntervalsOverlapError):
                            get_index(closed, True)

                tst_intervals_index("left", overlaps)
                tst_intervals_index("right", overlaps)

    def test_deprecated(self, default_calendar_with_answers):
        """Test currently deprecated properties/methods raise FutureWarning."""
        cal, ans = default_calendar_with_answers

        # deprecated properties / attributes
        for name in []:
            with pytest.warns(FutureWarning):
                getattr(cal, name)

        # deprecated class methods
        for name in ["bound_start", "bound_end"]:
            with pytest.warns(FutureWarning):
                getattr(cal, name)()

        # deprecated methods that take a single 'session' argument.
        session = ans.sessions[-5]
        for name in []:
            with pytest.warns(FutureWarning):
                getattr(cal, name)(session, _parse=False)

        # deprecated methods that take start and end session parameters.
        start = ans.sessions[-10]
        end = session
        for name in [
            "sessions_opens",
            "sessions_closes",
        ]:
            with pytest.warns(FutureWarning):
                getattr(cal, name)(start, end, _parse=False)

        # deprecated methods that take a single 'minute' argument.
        minute = ans.trading_minutes[len(ans.trading_minutes) // 2][0][1]
        for name in []:
            with pytest.warns(FutureWarning):
                getattr(cal, name)(minute, _parse=False)


class EuronextCalendarTestBase(ExchangeCalendarTestBase):
    """Common calendar-specific fixtures for Euronext exchanges."""

    # Subclass should override the following fixtures if close times differ
    # from the default yielded.

    @pytest.fixture
    def early_closes_sample_time(self):
        # Early close is 2:05 PM.
        # Source: https://www.euronext.com/en/calendars-hours
        yield pd.Timedelta(hours=14, minutes=5)

    @pytest.fixture
    def non_early_closes_sample_time(self):
        yield pd.Timedelta(hours=17, minutes=30)

    # Subclass can override the following fixtures to add to calendar-specific samples.

    @pytest.fixture
    def additional_regular_holidays_sample(self):
        yield []

    @pytest.fixture
    def additional_non_holidays_sample(self):
        yield []

    # Subclass should NOT override any of the following fixtures.

    @pytest.fixture
    def max_session_hours(self):
        yield 8.5

    @pytest.fixture
    def regular_holidays_sample(self, additional_regular_holidays_sample):
        yield additional_regular_holidays_sample + [
            # 2014
            "2014-01-01",  # New Year's Day
            "2014-04-18",  # Good Friday
            "2014-04-21",  # Easter Monday
            "2014-05-01",  # Labor Day
            "2014-12-25",  # Christmas
            "2014-12-26",  # Boxing Day
        ]

    @pytest.fixture
    def non_holidays_sample(self, additional_non_holidays_sample):
        yield additional_non_holidays_sample + [
            # Holidays falling on a weekend that are not made up. Ensure
            # surrounding sessions are not holidays...
            # In 2010, Labor Day fell on a Saturday, so the market should be open...
            "2010-04-30",  # ...on prior Friday...
            "2010-05-03",  # ...and following Monday.
            # Christmas fell on a Saturday and Boxing Day on a Sunday...
            "2010-12-24",  # market should be open on both the prior Friday...
            "2010-12-27",  # ...and following Monday.
        ]

    @pytest.fixture
    def early_closes_sample(self):
        # Christmas Eve, New Year's Eve, Christmas Eve, New Year's Eve
        yield ["2010-12-24", "2010-12-31", "2014-12-24", "2014-12-31"]

    @pytest.fixture
    def non_early_closes_sample(self):
        # In Dec 2011, Christmas Eve and NYE were both on a Saturday, so
        # the preceding Fridays should be full days.
        yield ["2011-12-23", "2011-12-30"]
