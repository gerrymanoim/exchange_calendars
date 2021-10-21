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
from abc import ABC, abstractproperty
from collections import OrderedDict
import functools
import warnings

import numpy as np
import pandas as pd
import toolz
from pandas import DataFrame, date_range
from pandas.tseries.holiday import AbstractHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
from pytz import UTC

from exchange_calendars import errors
from .calendar_helpers import (
    NP_NAT,
    NANOSECONDS_PER_MINUTE,
    compute_minutes,
    one_minute_later,
    one_minute_earlier,
    next_divider_idx,
    previous_divider_idx,
    Session,
    Date,
    Minute,
    TradingMinute,
    parse_timestamp,
    parse_trading_minute,
    parse_session,
    parse_date,
    _TradingIndex,
)
from .utils.memoize import lazyval
from .utils.pandas_utils import days_at_time
from .pandas_extensions.offsets import MultipleWeekmaskCustomBusinessDay

GLOBAL_DEFAULT_START = pd.Timestamp.now(tz=UTC).floor("D") - pd.DateOffset(years=20)
# Give an aggressive buffer for logic that needs to use the next trading
# day or minute.
GLOBAL_DEFAULT_END = pd.Timestamp.now(tz=UTC).floor("D") + pd.DateOffset(years=1)

NANOS_IN_MINUTE = 60000000000
MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)
WEEKDAYS = (MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY)
WEEKENDS = (SATURDAY, SUNDAY)


def selection(arr, start, end):
    predicates = []
    if start is not None:
        predicates.append(start.tz_localize(UTC) <= arr)
    if end is not None:
        predicates.append(arr < end.tz_localize(UTC))

    if not predicates:
        return arr

    return arr[np.all(predicates, axis=0)]


def _group_times(all_days, times, tz, offset=0):
    if times is None:
        return None
    elements = [
        days_at_time(selection(all_days, start, end), time, tz, offset)
        for (start, time), (end, _) in toolz.sliding_window(
            2, toolz.concatv(times, [(None, None)])
        )
    ]
    return elements[0].append(elements[1:])


class deprecate:
    """Decorator for deprecated/renamed ExchangeCalendar methods."""

    def __init__(
        self,
        deprecated_release: str = "3.4",
        removal_release: str = "4.0",
        alt: str = "",
        renamed: bool = True,
        prop: bool = False,
    ):
        self.deprecated_release = "release " + deprecated_release
        self.removal_release = "release " + removal_release
        self.alt = alt
        self.renamed = renamed
        if renamed:
            assert alt, "pass `alt` if renaming"
        self.obj_type = "property" if prop else "method"
        self.is_method = not prop

    def __call__(self, f):
        @functools.wraps(f)
        def wrapped_f(*args, **kwargs):
            warnings.warn(self._message(f), FutureWarning)
            return f(*args, **kwargs)

        return wrapped_f

    def _message(self, f):
        msg = (
            f"`{f.__name__}` was deprecated in {self.deprecated_release}"
            f" and will be removed in {self.removal_release}."
        )
        if self.alt:
            if self.renamed:
                msg += f" The {self.obj_type} has been renamed `{self.alt}`."
                if self.is_method:
                    msg += (
                        f" NB parameter names may also have changed (see "
                        f" documentation for `{self.alt}`)."
                    )
            else:
                msg += f" Use `{self.alt}`."
        return msg


class ExchangeCalendar(ABC):
    """Representation of timing information of a single market exchange.

    The timing information comprises sessions, open/close times and, for
    exchanges that observe an intraday break, break_start/break_end times.

    For exchanges that do not observe an intraday break a session
    represents a contiguous set of minutes. Where an exchange observes
    an intraday break a session represents two contiguous sets of minutes
    separated by the intraday break.

    Each session has a label that is midnight UTC. It is important to note
    that a session label should not be considered a specific point in time,
    and that midnight UTC is just being used for convenience.

    For each session, we store the open and close time together with, for
    those exchanges with breaks, the break start and break end. All times
    are defined as UTC.

    Parameters
    ----------
    start : default: later of 20 years ago or first supported start date.
        First calendar session will be `start`, if `start` is a session, or
        first session after `start`.

    end : default: earliest of 1 year from 'today' or last supported end date.
        Last calendar session will be `end`, if `end` is a session, or last
        session before `end`.

    side : default: "both" ("left" for 24 hour calendars)
        Define which of session open/close and break start/end should
            be treated as a trading minute:
        "left" - treat session open and break_start as trading minutes,
            do not treat session close or break_end as trading minutes.
        "right" - treat session close and break_end as trading minutes,
            do not treat session open or break_start as tradng minutes.
        "both" - treat all of session open, session close, break_start
            and break_end as trading minutes.
        "neither" - treat none of session open, session close,
            break_start or break_end as trading minutes.

    Raises
    ------
    ValueError
        If `start` is earlier than the earliest supported start date.
        If `end` is later than the latest supported end date.
        If `start` parses to a later date than `end`.

    Notes
    -----
    Exchange calendars were originally defined for the Zipline package from
    Quantopian under the package 'trading_calendars'. Since 2021 they have
    been maintained under the 'exchange_calendars' package (a fork of
    'trading_calendars') by an active community of contributing users.

    Some calendars have defined start and end bounds within which
    contributors have endeavoured to ensure the calendar's accuracy and
    outside of which the calendar would not be accurate. These bounds
    are enforced such that passing `start` or `end` as dates that are
    out-of-bounds will raise a ValueError. The bounds of each calendar are
    exposed via the `bound_start` and `bound_end` properties.

    Many calendars do not have bounds defined (in these cases `bound_start`
    and/or `bound_end` return None). These calendars can be created through
    any date range although it should be noted that the earlier the start
    date, the greater the potential for inaccuracies.

    In all cases, no guarantees are offered as to the accuracy of any
    calendar.


    Internal method parameters:

        _parse: bool
            Determines if a `minute` or `session` parameter should be
            parsed (default True). Passed as False:
                - internally to prevent double parsing.
                - by tests for efficiency.
    """

    _LEFT_SIDES = ["left", "both"]
    _RIGHT_SIDES = ["right", "both"]

    def __init__(
        self,
        start: Date | None = None,
        end: Date | None = None,
        side: str | None = None,
    ):
        side = side if side is not None else self.default_side()
        if side not in self.valid_sides():
            raise ValueError(
                f"`side` must be in {self.valid_sides()} although received as {side}."
            )
        self._side = side

        if start is None:
            start = self.default_start
        else:
            start = parse_date(start, "start", raise_oob=False)
            if self.bound_start is not None and start < self.bound_start:
                raise ValueError(self._bound_start_error_msg(start))

        if end is None:
            end = self.default_end
        else:
            end = parse_date(end, "end", raise_oob=False)
            if self.bound_end is not None and end > self.bound_end:
                raise ValueError(self._bound_end_error_msg(end))

        if start >= end:
            raise ValueError(
                "`start` must be earlier than `end` although `start` parsed as"
                f" '{start}' and `end` as '{end}'."
            )

        # Midnight in UTC for each trading day.
        _all_days = date_range(start, end, freq=self.day, tz=UTC)
        if _all_days.empty:
            raise errors.NoSessionsError(calendar_name=self.name, start=start, end=end)

        # `DatetimeIndex`s of standard opens/closes for each day.
        self._opens = _group_times(
            _all_days,
            self.open_times,
            self.tz,
            self.open_offset,
        )
        self._break_starts = _group_times(
            _all_days,
            self.break_start_times,
            self.tz,
        )
        self._break_ends = _group_times(
            _all_days,
            self.break_end_times,
            self.tz,
        )
        self._closes = _group_times(
            _all_days,
            self.close_times,
            self.tz,
            self.close_offset,
        )

        # Apply special offsets first
        self._calculate_and_overwrite_special_offsets(_all_days, start, end)

        # Series mapping sessions with nonstandard opens/closes.
        _special_opens = self._calculate_special_opens(start, end)
        _special_closes = self._calculate_special_closes(start, end)

        # Overwrite the special opens and closes on top of the standard ones.
        _overwrite_special_dates(_all_days, self._opens, _special_opens)
        _overwrite_special_dates(_all_days, self._closes, _special_closes)
        _remove_breaks_for_special_dates(
            _all_days,
            self._break_starts,
            _special_closes,
        )
        _remove_breaks_for_special_dates(
            _all_days,
            self._break_ends,
            _special_closes,
        )

        if self._break_starts is None:
            break_starts = None
        else:
            break_starts = self._break_starts.tz_localize(None)
        if self._break_ends is None:
            break_ends = None
        else:
            break_ends = self._break_ends.tz_localize(None)
        self.schedule = DataFrame(
            index=_all_days,
            data=OrderedDict(
                [
                    ("market_open", self._opens.tz_localize(None)),
                    ("break_start", break_starts),
                    ("break_end", break_ends),
                    ("market_close", self._closes.tz_localize(None)),
                ]
            ),
            dtype="datetime64[ns]",
        )

        self.opens_nanos = self.schedule.market_open.values.astype(np.int64)
        self.break_starts_nanos = self.schedule.break_start.values.astype(np.int64)
        self.break_ends_nanos = self.schedule.break_end.values.astype(np.int64)
        self.closes_nanos = self.schedule.market_close.values.astype(np.int64)

        _check_breaks_match(self.break_starts_nanos, self.break_ends_nanos)

        self._late_opens = _special_opens.index
        self._early_closes = _special_closes.index

    # Methods and properties that define calendar and which should be
    # overriden or extended, if and as required, by subclass.

    @abstractproperty
    def name(self) -> str:
        raise NotImplementedError()

    @property
    def bound_start(self) -> pd.Timestamp | None:
        """Earliest date from which calendar can be constructed.

        Returns
        -------
        pd.Timestamp or None
            Earliest date from which calendar can be constructed. Must have
            tz as "UTC". None if no limit.

        Notes
        -----
        To impose a constraint on the earliest date from which a calendar
        can be constructed subclass should override this method and
        optionally override `_bound_start_error_msg`.
        """
        return None

    @property
    def bound_end(self) -> pd.Timestamp | None:
        """Latest date to which calendar can be constructed.

        Returns
        -------
        pd.Timestamp or None
            Latest date to which calendar can be constructed. Must have tz
            as "UTC". None if no limit.

        Notes
        -----
        To impose a constraint on the latest date to which a calendar can
        be constructed subclass should override this method and optionally
        override `_bound_end_error_msg`.
        """
        return None

    def _bound_start_error_msg(self, start: pd.Timestamp) -> str:
        """Return error message to handle `start` being out-of-bounds.

        See Also
        --------
        bound_start
        """
        return (
            f"The earliest date from which calendar {self.name} can be"
            f" evaluated is {self.bound_start}, although received `start` as"
            f" {start}."
        )

    def _bound_end_error_msg(self, end: pd.Timestamp) -> str:
        """Return error message to handle `end` being out-of-bounds.

        See Also
        --------
        bound_end
        """
        return (
            f"The latest date to which calendar {self.name} can be evaluated"
            f" is {self.bound_end}, although received `end` as {end}."
        )

    @property
    def default_start(self) -> pd.Timestamp:
        if self.bound_start is None:
            return GLOBAL_DEFAULT_START
        else:
            return max(GLOBAL_DEFAULT_START, self.bound_start)

    @property
    def default_end(self) -> pd.Timestamp:
        if self.bound_end is None:
            return GLOBAL_DEFAULT_END
        else:
            return min(GLOBAL_DEFAULT_END, self.bound_end)

    @abstractproperty
    def tz(self):
        raise NotImplementedError()

    @abstractproperty
    def open_times(self):
        """
        Returns a list of tuples of (start_date, open_time).  If the open
        time is constant throughout the calendar, use None for the start_date.
        """
        raise NotImplementedError()

    @property
    def break_start_times(self):
        """
        Returns a optional list of tuples of (start_date, break_start_time).
        If the break start time is constant throughout the calendar, use None
        for the start_date. If there is no break, return `None`.
        """
        return None

    @property
    def break_end_times(self):
        """
        Returns a optional list of tuples of (start_date, break_end_time).  If
        the break end time is constant throughout the calendar, use None for
        the start_date. If there is no break, return `None`.
        """
        return None

    @abstractproperty
    def close_times(self):
        """
        Returns a list of tuples of (start_date, close_time).  If the close
        time is constant throughout the calendar, use None for the start_date.
        """
        raise NotImplementedError()

    @property
    def weekmask(self):
        """
        String indicating the days of the week on which the market is open.

        Default is '1111100' (i.e., Monday-Friday).

        See Also
        --------
        numpy.busdaycalendar
        """
        return "1111100"

    @property
    def open_offset(self):
        return 0

    @property
    def close_offset(self):
        return 0

    @property
    def regular_holidays(self):
        """
        Returns
        -------
        pd.AbstractHolidayCalendar: a calendar containing the regular holidays
        for this calendar
        """
        return None

    @property
    def adhoc_holidays(self):
        """
        Returns
        -------
        list: A list of tz-naive timestamps representing unplanned closes.
        """
        return []

    @property
    def special_opens(self):
        """
        A list of special open times and corresponding HolidayCalendars.

        Returns
        -------
        list: List of (time, AbstractHolidayCalendar) tuples
        """
        return []

    @property
    def special_opens_adhoc(self):
        """
        Returns
        -------
        list: List of (time, DatetimeIndex) tuples that represent special
         closes that cannot be codified into rules.
        """
        return []

    @property
    def special_closes(self):
        """
        A list of special close times and corresponding HolidayCalendars.

        Returns
        -------
        list: List of (time, AbstractHolidayCalendar) tuples
        """
        return []

    @property
    def special_closes_adhoc(self):
        """
        Returns
        -------
        list: List of (time, DatetimeIndex) tuples that represent special
         closes that cannot be codified into rules.
        """
        return []

    @property
    def special_weekmasks(self):
        """
        Returns
        -------
        list: List of (date, date, str) tuples that represent special
         weekmasks that applies between dates.
        """
        return []

    @property
    def special_offsets(self):
        """
        Returns
        -------
        list: List of (timedelta, timedelta, timedelta, timedelta, AbstractHolidayCalendar) tuples
         that represent special open, break_start, break_end, close offsets
         and corresponding HolidayCalendars.
        """
        return []

    @property
    def special_offsets_adhoc(self):
        """
        Returns
        -------
        list: List of (timedelta, timedelta, timedelta, timedelta, DatetimeIndex) tuples
         that represent special open, break_start, break_end, close offsets
         and corresponding DatetimeIndexes.
        """
        return []

    # ------------------------------------------------------------------
    # -- NO method below this line should be overriden on a subclass! --
    # ------------------------------------------------------------------

    # Methods and properties that define calendar (continued...).

    @lazyval
    def day(self):
        if self.special_weekmasks:
            return MultipleWeekmaskCustomBusinessDay(
                holidays=self.adhoc_holidays,
                calendar=self.regular_holidays,
                weekmask=self.weekmask,
                weekmasks=self.special_weekmasks,
            )
        else:
            return CustomBusinessDay(
                holidays=self.adhoc_holidays,
                calendar=self.regular_holidays,
                weekmask=self.weekmask,
            )

    @classmethod
    def valid_sides(cls) -> list[str]:
        """List of valid `side` options."""
        if cls.close_times == cls.open_times:
            return ["left", "right"]
        else:
            return ["both", "left", "right", "neither"]

    @classmethod
    def default_side(cls) -> str:
        """Default `side` option."""
        if cls.close_times == cls.open_times:
            return "right"
        else:
            return "both"

    @property
    def side(self) -> str:
        """Side on which sessions are closed.

        Returns
        -------
        str
            "left" - Session open and break_start are trading minutes.
                Session close and break_end are not trading minutes.
            "right" - Session close and break_end are trading minutes,
                Session open and break_start are not tradng minutes.
            "both" - Session open, session close, break_start and
                break_end are all trading minutes.
            "neither" - Session open, session close, break_start and
                break_end are all not trading minutes.

        Notes
        -----
        Subclasses should NOT override this method.
        """
        return self._side

    # Properties covering all sessions.

    @property
    def sessions(self) -> pd.DatetimeIndex:
        """All calendar sessions."""
        return self.schedule.index

    @functools.lru_cache(maxsize=1)
    def _sessions_nanos(self) -> np.ndarray:
        return self.sessions.values.astype("int64")

    @property
    def sessions_nanos(self) -> np.ndarray:
        """All calendar sessions as nano seconds."""
        return self._sessions_nanos()

    @property
    def opens(self) -> pd.Series:
        """Open time of each session.

        Returns
        -------
        pd.Series
            index : pd.DatetimeIndex
                All sessions.
            dtype : datetime64[ns]
                Open time of corresponding session. NB Times are UTC
                although dtype is timezone-naive.
        """
        return self.schedule.market_open

    @property
    def closes(self) -> pd.Series:
        """Close time of each session.

        Returns
        -------
        pd.Series
            index : pd.DatetimeIndex
                All sessions.
            dtype : datetime64[ns]
                Close time of corresponding session. NB Times are UTC
                although dtype is timezone-naive.
        """
        return self.schedule.market_close

    @property
    def break_starts(self) -> pd.Series:
        """Break start time of each session.

        Returns
        -------
        pd.Series
            index : pd.DatetimeIndex
                All sessions.
            dtype : datetime64[ns]
                Break-start time of corresponding session. NB Times are UTC
                although dtype is timezone-naive. Value is missing
                (pd.NaT) for any session that does not have a break.
        """
        return self.schedule.break_start

    @property
    def break_ends(self) -> pd.Series:
        """Break end time of each session.

        Returns
        -------
        pd.Series
            index : pd.DatetimeIndex
                All sessions.
            dtype : datetime64[ns]
                Break-end time of corresponding session.  NB Times are UTC
                although dtype is timezone-naive. Value is missing
                (pd.NaT) for any session that does not have a break.
        """
        return self.schedule.break_end

    @functools.lru_cache(maxsize=1)
    def _first_minutes_nanos(self) -> np.ndarray:
        if self.side in self._LEFT_SIDES:
            return self.opens_nanos
        else:
            return one_minute_later(self.opens_nanos)

    @property
    def first_minutes_nanos(self) -> np.ndarray:
        return self._first_minutes_nanos()

    @functools.lru_cache(maxsize=1)
    def _last_minutes_nanos(self) -> np.ndarray:
        if self.side in self._RIGHT_SIDES:
            return self.closes_nanos
        else:
            return one_minute_earlier(self.closes_nanos)

    @property
    def last_minutes_nanos(self) -> np.ndarray:
        return self._last_minutes_nanos()

    @functools.lru_cache(maxsize=1)
    def _last_am_minutes_nanos(self) -> np.ndarray:
        if self.side in self._RIGHT_SIDES:
            return self.break_starts_nanos
        else:
            return one_minute_earlier(self.break_starts_nanos)

    @property
    def last_am_minutes_nanos(self) -> np.ndarray:
        return self._last_am_minutes_nanos()

    @functools.lru_cache(maxsize=1)
    def _first_pm_minutes_nanos(self) -> np.ndarray:
        if self.side in self._LEFT_SIDES:
            return self.break_ends_nanos
        else:
            return one_minute_later(self.break_ends_nanos)

    @property
    def first_pm_minutes_nanos(self) -> np.ndarray:
        return self._first_pm_minutes_nanos()

    def _minutes_as_series(self, nanos: np.ndarray, name: str) -> pd.Series:
        """Convert trading minute nanos to pd.Series."""
        ser = pd.Series(pd.DatetimeIndex(nanos, tz=UTC), index=self.sessions)
        ser.name = name
        return ser

    @property
    def first_minutes(self) -> pd.Series:
        """First trading minute of each session."""
        return self._minutes_as_series(self.first_minutes_nanos, "first_minutes")

    @property
    def last_minutes(self) -> pd.Series:
        """Last trading minute of each session."""
        return self._minutes_as_series(self.last_minutes_nanos, "last_minutes")

    @property
    def last_am_minutes(self) -> pd.Series:
        """Last am trading minute of each session."""
        return self._minutes_as_series(self.last_am_minutes_nanos, "last_am_minutes")

    @property
    def first_pm_minutes(self) -> pd.Series:
        """First pm trading minute of each session."""
        return self._minutes_as_series(self.first_pm_minutes_nanos, "first_pm_minutes")

    # Properties covering all minutes.

    def _minutes(self, side: str) -> pd.DatetimeIndex:
        return pd.DatetimeIndex(
            compute_minutes(
                self.opens_nanos,
                self.break_starts_nanos,
                self.break_ends_nanos,
                self.closes_nanos,
                side,
            ),
            tz=UTC,
        )

    @lazyval
    def minutes(self) -> pd.DatetimeIndex:
        """All trading minutes."""
        return self._minutes(self.side)

    @lazyval
    def minutes_nanos(self) -> np.ndarray:
        """All trading minutes as nanoseconds."""
        return self.minutes.values.astype(np.int64)

    # Calendar properties.

    @property
    def first_session(self) -> pd.Timestamp:
        """First calendar session."""
        return self.sessions[0]

    @property
    def last_session(self) -> pd.Timestamp:
        """Last calendar session."""
        return self.sessions[-1]

    @property
    def first_session_open(self) -> pd.Timestamp:
        """Open time of calendar's first session."""
        return self.opens[0]

    @property
    def last_session_close(self) -> pd.Timestamp:
        """Close time of calendar's last session."""
        return self.closes[-1]

    @property
    def first_minute(self) -> pd.Timestamp:
        """Calendar's first trading minute."""
        return pd.Timestamp(self.minutes_nanos[0], tz=UTC)

    @property
    def last_minute(self) -> pd.Timestamp:
        """Calendar's last trading minute."""
        return pd.Timestamp(self.minutes_nanos[-1], tz=UTC)

    @property
    def has_break(self) -> bool:
        """Query if any calendar session has a break."""
        return self.sessions_has_break(
            self.first_session, self.last_session, _parse=False
        )

    @property
    def late_opens(self) -> pd.DatetimeIndex:
        """Sessions that open later than the prevailing normal open.

        NB. Prevailing normal open as defined by `open_times`.
        """
        return self._late_opens

    @property
    def early_closes(self) -> pd.DatetimeIndex:
        """Sessions that close earlier than the prevailing normal close.

        NB. Prevailing normal close as defined by `close_times`.
        """
        return self._early_closes

    # Methods that interrogate a given session.

    def _get_session_idx(self, session: Date, _parse=True) -> int:
        """Index position of a session."""
        if _parse:
            session = parse_session(self, session)
        return self.sessions_nanos.searchsorted(session.value, side="left")

    def session_open(self, session_label: Session, _parse: bool = True) -> pd.Timestamp:
        """Return open time for a given session."""
        if _parse:
            session_label = parse_session(self, session_label, "session_label")
        return self.schedule.at[session_label, "market_open"].tz_localize(UTC)

    def session_close(
        self, session_label: Session, _parse: bool = True
    ) -> pd.Timestamp:
        """Return close time for a given session."""
        if _parse:
            session_label = parse_session(self, session_label, "session_label")
        return self.schedule.at[session_label, "market_close"].tz_localize(UTC)

    def session_break_start(
        self, session_label: Session, _parse: bool = True
    ) -> pd.Timestamp | pd.NaT:
        """Return break-start time for a given session.

        Returns pd.NaT if no break.
        """
        if _parse:
            session_label = parse_session(self, session_label, "session_label")
        break_start = self.schedule.at[session_label, "break_start"]
        if not pd.isnull(break_start):
            break_start = break_start.tz_localize(UTC)
        return break_start

    def session_break_end(
        self, session_label: Session, _parse: bool = True
    ) -> pd.Timestamp | pd.NaT:
        """Return break-end time for a given session.

        Returns pd.NaT if no break.
        """
        if _parse:
            session_label = parse_session(self, session_label, "session_label")
        break_end = self.schedule.at[session_label, "break_end"]
        if not pd.isnull(break_end):
            break_end = break_end.tz_localize(UTC)
        return break_end

    def session_open_close(
        self, session: Session, _parse: bool = True
    ) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Return open and close times for a given session.

        Parameters
        ----------
        session
            Session for which require open and close.

        Returns
        -------
        tuple[pd.Timestamp, pd.Timestamp]
            [0] Open time of `session`.
            [1] Close time of `session`.
        """
        if _parse:
            session = parse_session(self, session)
        return self.session_open(session), self.session_close(session)

    def session_break_start_end(
        self, session: Session, _parse: bool = True
    ) -> tuple[pd.Timestamp | pd.NaT, pd.Timestamp | pd.NaT]:
        """Return break-start and break-end times for a given session.

        Parameters
        ----------
        session
            Session for which require break-start and break-end.

        Returns
        -------
        tuple[pd.Timestamp | pd.NaT, pd.Timestamp | pd.NaT]
            [0] Break-start time of `session`, or pd.NaT if no break.
            [1] Close time of `session`, or pd.NaT if no break.
        """
        if _parse:
            session = parse_session(self, session)
        return self.session_break_start(session), self.session_break_end(session)

    def _get_session_minute_from_nanos(
        self, session: Session, nanos: np.ndarray, _parse: bool
    ) -> pd.Timestamp:
        idx = self._get_session_idx(session, _parse=_parse)
        return pd.Timestamp(nanos[idx], tz=UTC)

    def session_first_minute(
        self, session: Session, _parse: bool = True
    ) -> pd.Timestamp:
        """Return first trading minute of a given session."""
        nanos = self.first_minutes_nanos
        return self._get_session_minute_from_nanos(session, nanos, _parse)

    def session_last_minute(
        self, session: Session, _parse: bool = True
    ) -> pd.Timestamp:
        """Return last trading minute of a given session."""
        nanos = self.last_minutes_nanos
        return self._get_session_minute_from_nanos(session, nanos, _parse)

    def session_last_am_minute(
        self, session: Session, _parse: bool = True
    ) -> pd.Timestamp | pd.NaT:  # Literal[pd.NaT] - when move to min 3.8
        """Return last trading minute of am subsession of a given session."""
        nanos = self.last_am_minutes_nanos
        return self._get_session_minute_from_nanos(session, nanos, _parse)

    def session_first_pm_minute(
        self, session: Session, _parse: bool = True
    ) -> pd.Timestamp | pd.NaT:  # Literal[pd.NaT] - when move to min 3.8
        """Return first trading minute of pm subsession of a given session."""
        nanos = self.first_pm_minutes_nanos
        return self._get_session_minute_from_nanos(session, nanos, _parse)

    def session_first_last_minute(
        self,
        session: Session,
        _parse: bool = True,
    ) -> tuple(pd.Timestamp, pd.Timestamp):
        """Return first and last trading minutes of a given session."""
        idx = self._get_session_idx(session, _parse=_parse)
        first = pd.Timestamp(self.first_minutes_nanos[idx], tz=UTC)
        last = pd.Timestamp(self.last_minutes_nanos[idx], tz=UTC)
        return (first, last)

    def session_has_break(self, session: Session, _parse: bool = True) -> bool:
        """Query if a given session has a break.

        Parameters
        ----------
        session
            Session to query.

        Returns
        -------
        bool
            True if `session` has a break, false otherwise.
        """
        if _parse:
            session = parse_session(self, session)
        return pd.notna(self.session_break_start(session))

    def next_session(self, session: Session, _parse: bool = True) -> pd.Timestamp:
        """Return session that immediately follows a given session.

        Parameters
        ----------
        session
            Session whose next session is desired.

        Raises
        ------
        ValueError
            If `session` is the last calendar session.

        See Also
        --------
        date_to_session
        """
        idx = self._get_session_idx(session, _parse=_parse)
        try:
            return self.schedule.index[idx + 1]
        except IndexError as err:
            if idx == len(self.schedule.index) - 1:
                raise ValueError(
                    "There is no next session as this is the end"
                    " of the exchange calendar."
                ) from err
            else:
                raise

    def previous_session(self, session: Session, _parse: bool = True) -> pd.Timestamp:
        """Return session that immediately preceeds a given session.

        Parameters
        ----------
        session
            Session whose previous session is desired.

        Raises
        ------
        ValueError
            If `session` is the first calendar session.

        See Also
        --------
        date_to_session
        """
        idx = self._get_session_idx(session, _parse=_parse)
        if idx == 0:
            raise ValueError(
                "There is no previous session as this is the"
                " beginning of the exchange calendar."
            )
        return self.schedule.index[idx - 1]

    def session_minutes(
        self, session: Session, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return trading minutes corresponding to a given session.

        Parameters
        ----------
        session
            Session for which require trading minutes.

        Returns
        -------
        pd.DateTimeIndex
            Trading minutes for `session`.
        """
        first, last = self.session_first_last_minute(session, _parse=_parse)
        return self.minutes_in_range(start_minute=first, end_minute=last)

    def session_offset(
        self, session: Session, count: int, _parse: bool = True
    ) -> pd.Timestamp:
        """Offset a given session by a number of sessions.

        Parameters
        ----------
        session
            Session from which to offset.

        count
            Number of sessions to offset `session`. Positive to offset
            forwards, negative to offset backwards.

        Returns
        -------
        pd.Timestamp
            Offset session.

        Raises
        ------
        exchange_calendars.errors.RequestedSessionOutOfBounds
            If offset session would be either before the calendar's first
            session or after the calendar's last session.
        """
        idx = self._get_session_idx(session, _parse=_parse) + count
        if idx >= len(self.sessions):
            raise errors.RequestedSessionOutOfBounds(self, too_early=False)
        elif idx < 0:
            raise errors.RequestedSessionOutOfBounds(self, too_early=True)
        return self.sessions[idx]

    # Methods that interrogate a date.

    def _get_date_idx(self, date: Date, _parse=True) -> int:
        """Index position of a date.

        Returns
        -------
            Index position of session if `date` represents a session,
                otherwise index position of session that immediately
                follows `date`.
        """
        if _parse:
            date = parse_date(date, "date", self)
        return self.sessions_nanos.searchsorted(date.value, side="left")

    def _date_oob(self, date: Date) -> bool:
        """Is `date` out-of-bounds."""
        return (
            date.value < self.sessions_nanos[0] or date.value > self.sessions_nanos[-1]
        )

    def is_session(self, dt: Date, _parse: bool = True) -> bool:
        """Query if a date is a valid session.

        Parameters
        ----------
        dt
            Date to be queried.

        Return
        ------
        bool
            True if `dt` is a session, False otherwise.
        """
        if _parse:
            dt = parse_date(dt, "dt", self)
        idx = self._get_date_idx(dt, _parse=False)
        return bool(self.sessions_nanos[idx] == dt.value)  # convert from np.bool_

    def date_to_session(
        self,
        date: Date,
        direction: str = "none",  # when min 3.8, Literal["none", "previous", "next"]
        _parse: bool = True,
    ) -> pd.Timestamp:
        """Return a session corresponding to a given date.

        Parameters
        ----------
        date
            Date for which require session. Can be a date that does not
            represent an actual session (see `direction`).

        direction : default: "none"
            Defines behaviour if `date` does not represent a session:
                "next" - return first session following `date`.
                "previous" - return first session prior to `date`.
                "none" - raise ValueError.

        See Also
        --------
        next_session
        previous_session
        """
        if _parse:
            date = parse_date(date, calendar=self)
        if self.is_session(date, _parse=False):
            return date
        elif direction in ["next", "previous"]:
            idx = self._get_date_idx(date, _parse=False)
            if direction == "previous":
                idx -= 1
            return self.sessions[idx]
        elif direction == "none":
            raise ValueError(
                f"`date` '{date}' does not represent a session. Consider passing"
                " a `direction`."
            )
        else:
            raise ValueError(
                f"'{direction}' is not a valid `direction`. Valid `direction`"
                ' values are "next", "previous" and "none".'
            )

    # Methods that interrogate a given minute (trading or non-trading).

    def _get_minute_idx(self, minute: Minute, _parse=True) -> int:
        """Index position of a minute.

        Returns
        -------
            Index position of trading minute if `minute` represents a
                trading minute, otherwise index position of trading
                minute that immediately follows `minute`.
        """
        if _parse:
            minute = parse_timestamp(minute, "minute", self)
        return self.minutes_nanos.searchsorted(minute.value, side="left")

    def _minute_oob(self, minute: Minute) -> bool:
        """Is `minute` out-of-bounds."""
        return (
            minute.value < self.minutes_nanos[0]
            or minute.value > self.minutes_nanos[-1]
        )

    def is_trading_minute(self, minute: Minute, _parse: bool = True) -> bool:
        """Query if a given minute is a trading minute.

        Minutes during breaks are not considered trading minutes.

        Note: `self.side` determines whether exchange will be considered
        open or closed on session open, session close, break start and
        break end.

        Parameters
        ----------
        minute
            Minute being queried.

        Returns
        -------
        bool
            Boolean indicting if `minute` is a trading minute.

        See Also
        --------
        is_open_on_minute
        """
        if _parse:
            minute = parse_timestamp(minute, calendar=self)
        idx = self._get_minute_idx(minute, _parse=False)
        # convert from np.bool_
        return bool(self.minutes_nanos[idx] == minute.value)

    def is_break_minute(self, minute: Minute, _parse: bool = True) -> bool:
        """Query if a given minute is within a break.

        Note: `self.side` determines whether either, both or one of break
        start and break end are treated as break minutes.

        Parameters
        ----------
        minute
            Minute being queried.

        Returns
        -------
        bool
            Boolean indicting if `minute` is a break minute.
        """
        if _parse:
            minute = parse_timestamp(minute, calendar=self)
        session_idx = np.searchsorted(self.first_minutes_nanos, minute.value) - 1
        break_start = self.last_am_minutes_nanos[session_idx]
        break_end = self.first_pm_minutes_nanos[session_idx]
        # NaT comparisions evalute as False
        numpy_bool = break_start < minute.value < break_end
        return bool(numpy_bool)

    def is_open_on_minute(
        self, dt: Minute, ignore_breaks: bool = False, _parse: bool = True
    ) -> bool:
        """Query if exchange is open on a given minute.

        Note: `self.side` determines whether exchange will be considered
        open or closed on session open, session close, break start and
        break end.

        Parameters
        ----------
        dt
            Minute being queried.

        ignore_breaks
            Should exchange be considered open during any break?
                True - treat exchange as open during any break.
                False - treat exchange as closed during any break.

        Returns
        -------
        bool
            Boolean indicting if exchange is open on `dt`.

        See Also
        --------
        is_trading_minute
        """
        if _parse:
            dt = parse_timestamp(dt, "dt", self)

        is_trading_minute = self.is_trading_minute(dt, _parse=False)
        if is_trading_minute or not ignore_breaks:
            return is_trading_minute
        else:
            # not a trading minute although should return True if in break
            return self.is_break_minute(dt, _parse=False)

    def next_open(self, dt: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return next open that follows a given minute.

        If `dt` is a session open, the next session's open will be
        returned.

        Parameters
        ----------
        dt
            Minute for which to get the next open.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the next open.
        """
        if _parse:
            dt = parse_timestamp(dt, "dt", self)
        try:
            idx = next_divider_idx(self.opens_nanos, dt.value)
        except IndexError:
            if dt.tz_convert(None) >= self.opens[-1]:
                raise ValueError(
                    "Minute cannot be the last open or later (received `dt`"
                    f" parsed as '{dt}'.)"
                ) from None
            else:
                raise

        return pd.Timestamp(self.opens_nanos[idx], tz=UTC)

    def next_close(self, dt: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return next close that follows a given minute.

        If `dt` is a session close, the next session's close will be
        returned.

        Parameters
        ----------
        dt
            Minute for which to get the next close.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the next close.
        """
        if _parse:
            dt = parse_timestamp(dt, "dt", self)
        try:
            idx = next_divider_idx(self.closes_nanos, dt.value)
        except IndexError:
            if dt.tz_convert(None) == self.closes[-1]:
                raise ValueError(
                    "Minute cannot be the last close (received `dt` parsed as"
                    f" '{dt}'.)"
                ) from None
            else:
                raise
        return pd.Timestamp(self.closes_nanos[idx], tz=UTC)

    def previous_open(self, dt: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return previous open that preceeds a given minute.

        If `dt` is a session open, the previous session's open will be
        returned.

        Parameters
        ----------
        dt
            Minute for which to get the previous open.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the previous open.
        """
        if _parse:
            dt = parse_timestamp(dt, "dt", self)
        try:
            idx = previous_divider_idx(self.opens_nanos, dt.value)
        except ValueError:
            if dt.tz_convert(None) == self.opens[0]:
                raise ValueError(
                    "Minute cannot be the first open (received `dt` parsed as"
                    f" '{dt}'.)"
                ) from None
            else:
                raise

        return pd.Timestamp(self.opens_nanos[idx], tz=UTC)

    def previous_close(self, dt: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return previous close that preceeds a given minute.

        If `dt` is a session close, the previous session's close will be
        returned.

        Parameters
        ----------
        dt
            Minute for which to get the previous close.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the previous close.
        """
        if _parse:
            dt = parse_timestamp(dt, "dt", self)
        try:
            idx = previous_divider_idx(self.closes_nanos, dt.value)
        except ValueError:
            if dt.tz_convert(None) <= self.closes[0]:
                raise ValueError(
                    "Minute cannot be the first close or earlier (received"
                    f" `dt` parsed as '{dt}'.)"
                ) from None
            else:
                raise

        return pd.Timestamp(self.closes_nanos[idx], tz=UTC)

    def next_minute(self, dt: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return trading minute that immediately follows a given minute.

        Parameters
        ----------
        dt
            Minute for which to get next trading minute. Minute can be a
            trading or a non-trading minute.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the next minute.
        """
        if _parse:
            dt = parse_timestamp(dt, "dt", self)
        try:
            idx = next_divider_idx(self.minutes_nanos, dt.value)
        except IndexError:
            # dt > last_minute handled via parsing
            if dt == self.last_minute:
                raise ValueError(
                    "Minute cannot be the last trading minute or later"
                    f" (received `dt` parsed as '{dt}'.)"
                ) from None
        return self.minutes[idx]

    def previous_minute(self, dt: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return trading minute that immediately preceeds a given minute.

        Parameters
        ----------
        dt
            Minute for which to get previous trading minute. Minute can be
            a trading or a non-trading minute.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the previous minute.
        """
        if _parse:
            dt = parse_timestamp(dt, "dt", self)
        try:
            idx = previous_divider_idx(self.minutes_nanos, dt.value)
        except ValueError:
            # dt < first_minute handled via parsing
            if dt == self.first_minute:
                raise ValueError(
                    "Minute cannot be the first trading minute or earlier"
                    f" (received `dt` parsed as '{dt}'.)"
                ) from None
        return self.minutes[idx]

    # NOTE: when min to 3.8, direction annotation to Literal["next", "previous", "none"]
    def minute_to_session(
        self,
        minute: Minute,
        direction: str = "next",
        _parse: bool = True,
    ) -> pd.Timestamp:
        """Get session corresponding with a trading or break minute.

        Parameters
        ----------
        minute
            Minute for which require corresponding session.

        direction
            How to resolve session in event that `minute` is not a trading
            or break minute:
                "next" (default) - return first session subsequent to
                    `minute`.
                "previous" - return first session prior to `minute`.
                "none" - raise ValueError.

        Returns
        -------
        pd.Timestamp
            Corresponding session label.

        Raises
        ------
        ValueError
            If `minute` is not a trading minute and `direction` is "none".

        See Also
        --------
        minute_to_past_session
        minute_to_future_session
        session_offset
        """
        if _parse:
            minute = parse_timestamp(minute, calendar=self)

        if minute.value < self.minutes_nanos[0]:
            # Resolve call here.
            if direction == "next":
                return self.first_session
            else:
                raise ValueError(
                    "Received `minute` as '{0}' although this is earlier than the"
                    " calendar's first trading minute ({1}). Consider passing"
                    " `direction` as 'next' to get first session.".format(
                        minute, self.first_minute
                    )
                )

        if minute.value > self.minutes_nanos[-1]:
            # Resolve call here.
            if direction == "previous":
                return self.last_session
            else:
                raise ValueError(
                    "Received `minute` as '{0}' although this is later than the"
                    " calendar's last trading minute ({1}). Consider passing"
                    " `direction` as 'previous' to get last session.".format(
                        minute, self.last_minute
                    )
                )

        idx = np.searchsorted(self.last_minutes_nanos, minute.value)
        current_or_next_session = self.schedule.index[idx]

        if direction == "next":
            return current_or_next_session
        elif direction == "previous":
            if not self.is_open_on_minute(minute, ignore_breaks=True, _parse=False):
                return self.schedule.index[idx - 1]
        elif direction == "none":
            if not self.is_open_on_minute(minute, ignore_breaks=True, _parse=False):
                # if the exchange is closed, blow up
                raise ValueError(
                    f"`minute` '{minute}' is not a trading minute. Consider passing"
                    " `direction` as 'next' or 'previous'."
                )
        else:
            # invalid direction
            raise ValueError("Invalid direction parameter: " "{0}".format(direction))

        return current_or_next_session

    def minute_to_past_session(
        self, minute: Minute, count: int = 1, _parse: bool = True
    ) -> pd.Timestamp:
        """Get a session that closed before a given minute.

        Parameters
        ----------
        minute
            Minute for which to return a previous session. Can be a
            trading minute or non-trading minute.
            Note: if `minute` is a trading minute then returned session
            will not be the session of which `minute` is a trading minute,
            but rather a session that closed before `minute`.

        count : default: 1
            Number of sessions prior to `minute` for which require session.

        Returns
        -------
        pd.Timstamp
            Session that is `count` full sessions before `minute`.

        See Also
        --------
        minute_to_session
        minute_to_future_session
        session_offset
        """
        if _parse:
            minute = parse_timestamp(minute, calendar=self)
        if count <= 0:
            raise ValueError("`count` must be higher than 0.")
        if self.is_open_on_minute(minute, ignore_breaks=True, _parse=False):
            current_session = self.minute_to_session(minute, _parse=False)
            if current_session == self.first_session:
                raise errors.RequestedSessionOutOfBounds(self, too_early=True)
            base_session = self.previous_session(current_session, _parse=False)
        else:
            base_session = self.minute_to_session(minute, "previous", _parse=False)
        count -= 1
        return self.session_offset(base_session, -count, _parse=False)

    def minute_to_future_session(
        self,
        minute: Minute,
        count: int = 1,
        _parse: bool = True,
    ) -> pd.Timestamp:
        """Get a session that opens after a given minute.

        Parameters
        ----------
        minute
            Minute for which to return a future session. Can be a trading
            minute or non-trading minute.
            Note: if `minute` is a trading minute then returned session
            will not be the session of which `minute` is a trading minute,
            but rather a session that opens after `minute`.

        count : default: 1
            Number of sessions following `minute` for which require
            session.

        Returns
        -------
        pd.Timstamp
            Session that is `count` full sessions after `minute`.

        See Also
        --------
        minute_to_session
        minute_to_past_session
        session_offset
        """
        if _parse:
            minute = parse_timestamp(minute, calendar=self)
        if count <= 0:
            raise ValueError("`count` must be higher than 0.")
        if self.is_open_on_minute(minute, ignore_breaks=True, _parse=False):
            current_session = self.minute_to_session(minute, _parse=False)
            if current_session == self.last_session:
                raise errors.RequestedSessionOutOfBounds(self, too_early=False)
            base_session = self.next_session(current_session, _parse=False)
        else:
            base_session = self.minute_to_session(minute, "next", _parse=False)
        count -= 1
        return self.session_offset(base_session, count, _parse=False)

    # NOTE: when min to 3.8, direction annotation to Literal["next", "previous", "none"]
    def minute_to_trading_minute(
        self, minute: Minute, direction: str = "none", _parse: bool = True
    ) -> pd.Timestamp:
        """Resolve a minute to a trading minute.

        Differs from `previous_minute` and `next_minute` by returning
        `minute` unchanged if `minute` is a trading minute.

        Parameters
        ----------
        minute
            Timestamp to be resolved to a trading minute.

        direction:
            How to resolve `minute` if does not represent a trading minute:
                'next' - return trading minute that immediately follows
                    `minute`.
                'previous' - return trading minute that immediately
                    preceeds `minute`.
                'none' - raise KeyError

        Returns
        -------
        pd.Timestamp
            Returns `minute` if `minute` is a trading minute otherwise
            first trading minute that, in accordance with `direction`,
            either immediately follows or preceeds `minute`.

        Raises
        ------
        ValueError
            If `minute` is not a trading minute and `direction` is None.

        See Also
        --------
        next_mintue
        previous_minute
        """
        if _parse:
            minute = parse_timestamp(minute, calendar=self)
        if self.is_trading_minute(minute, _parse=False):
            return minute
        elif direction == "next":
            return self.next_minute(minute, _parse=False)
        elif direction == "previous":
            return self.previous_minute(minute, _parse=False)
        else:
            raise ValueError(
                f"`minute` '{minute}' is not a trading minute. Consider passing"
                " `direction` as 'next' or 'previous'."
            )

    def minute_offset(
        self, minute: TradingMinute, count: int, _parse: bool = True
    ) -> pd.Timestamp:
        """Offset a given trading minute by a number of trading minutes.

        Parameters
        ----------
        minute
            Trading minute from which to offset.

        count
            Number of trading minutes to offset `minute`. Positive to
            offset forwards, negative to offset backwards.

        Returns
        -------
        pd.Timstamp
            Offset trading minute.

        Raises
        ------
        ValueError
            If offset minute would be either before the calendar's first
            trading minute or after the calendar's last trading minute.
        """
        if _parse:
            minute = parse_trading_minute(self, minute)
        idx = self._get_minute_idx(minute) + count
        if idx >= len(self.minutes_nanos):
            raise errors.RequestedMinuteOutOfBounds(self, too_early=False)
        elif idx < 0:
            raise errors.RequestedMinuteOutOfBounds(self, too_early=True)
        return self.minutes[idx]

    def minute_offset_by_sessions(
        self,
        minute: TradingMinute,
        count: int = 1,
        _parse: bool = True,
    ) -> pd.Timestamp:
        """Offset trading minute by a given number of sessions.

        If trading minute is not represented in target session (due to a late
        open for example) then offset minute will be rolled (with respect to
        the target session):
            - forwards to first session minute, if offset minute otherwise
                falls earlier than first session minute.
            - back to last session minute, if offset minute otherwise falls
                later than last session minute.
            - back to last minute before break, if offset otherwise
                falls in session break.

        Parameters
        ----------
        minute
            Trading minute to be offset.

        count
            Number of sessions by which to offset trading minute. Negative
            to offset to an earlier session.
        """
        if _parse:
            minute = parse_trading_minute(self, minute)
        if not count:
            return minute

        if count > 0:
            try:
                target_session = self.minute_to_future_session(minute, abs(count))
            except errors.RequestedSessionOutOfBounds:
                raise errors.RequestedMinuteOutOfBounds(self, too_early=False)
        else:
            try:
                target_session = self.minute_to_past_session(minute, abs(count))
            except errors.RequestedSessionOutOfBounds:
                raise errors.RequestedMinuteOutOfBounds(self, too_early=True)

        base_session = self.minute_to_session(minute)

        day_offset = (minute.normalize() - base_session.normalize()).days
        minute = target_session.replace(hour=minute.hour, minute=minute.minute)
        minute += pd.Timedelta(days=day_offset)

        if self._minute_oob(minute):
            if minute.value < self.minutes_nanos[0]:
                errors.RequestedMinuteOutOfBounds(self, too_early=True)
            if minute.value > self.minutes_nanos[-1]:
                raise errors.RequestedMinuteOutOfBounds(self, too_early=False)

        if self.is_trading_minute(minute, _parse=False):
            # this guard is necessary as minute can be for a different session than the
            # intended if the gap between sessions is less than any difference in the
            # open or close times (i.e. only relevant if base and target sessions have
            # different open/close times.
            if self.minute_to_session(minute, _parse=False) == target_session:
                return minute
        first_minute = self.session_first_minute(target_session, _parse=False)
        if minute < first_minute:
            return first_minute
        last_minute = self.session_last_minute(target_session, _parse=False)
        if minute > last_minute:
            return last_minute
        elif self.is_break_minute(minute, _parse=False):
            return self.session_last_am_minute(target_session, _parse=False)
        assert False, "offset minute should have resolved!"

    # Methods that evaluate or interrogate a range of minutes.

    def _get_minutes_slice(self, start: Minute, end: Minute, _parse=True) -> slice:
        """Slice representing a range of trading minutes."""
        if _parse:
            start = parse_timestamp(start, "start", self)
            end = parse_timestamp(end, "end", self)
        slice_start = self.minutes_nanos.searchsorted(start.value, side="left")
        slice_end = self.minutes_nanos.searchsorted(end.value, side="right")
        return slice(slice_start, slice_end)

    def minutes_in_range(
        self, start_minute: Minute, end_minute: Minute, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return all trading minutes between given minutes.

        Parameters
        ----------
        start_minute
            Minute representing start of desired range. Can be a trading
            minute or non-trading minute.

        end_minute
            Minute representing end of desired range. Can be a trading
            minute or non-trading minute.
        """
        slc = self._get_minutes_slice(start_minute, end_minute, _parse)
        return self.minutes[slc]

    def minutes_window(
        self, start_dt: TradingMinute, count: int, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return block of given size of consecutive trading minutes.

        Parameters
        ----------
        start_dt
            Minute representing the first (if `count` positive) or last
            (if `count` negative) minute of minutes window.

        count
            Number of mintues to include in window in addition to
                `start_dt` (i.e. 0 will return block of length 1 with
                `start_dt` as only value).
            Positive to return block of minutes from `start_dt`
            Negative to return block of minutes to `start_dt`.
        """
        if _parse:
            start_dt = parse_trading_minute(self, start_dt, "start_dt")

        start_idx = self._get_minute_idx(start_dt, _parse=False)
        end_idx = start_idx + count

        if end_idx < 0:
            raise ValueError(
                f"Minutes window cannot begin before the calendar's first"
                f" trading minute ({self.first_minute}). `count`"
                f" cannot be lower than {count - end_idx} for `start`"
                f" '{start_dt}'."
            )
        elif end_idx >= len(self.minutes_nanos):
            raise ValueError(
                f"Minutes window cannot end after the calendar's last"
                f" trading minute ({self.last_minute}). `count`"
                f" cannot be higher than"
                f" {count - (end_idx - len(self.minutes_nanos) + 1)} for"
                f" `start` '{start_dt}'."
            )
        return self.minutes[min(start_idx, end_idx) : max(start_idx, end_idx) + 1]

    def minutes_to_sessions(self, minutes: pd.DatetimeIndex) -> pd.DatetimeIndex:
        """Return sessions corresponding to multiple trading minutes.

        For the purpose of this method trading minutes are considered as:
            - Trading minutes as determined by `self.side`.
            - All minutes of any breaks.

        Parameters
        ----------
        minutes
            Sorted DatetimeIndex representing market minutes for which to get
            corresponding sessions.

        Returns
        -------
        pd.DatetimeIndex
            Sessions corresponding to `minutes`.

        Raises
        ------
        ValueError
            If any indice of `minute` is not a trading minute.
        """
        if not minutes.is_monotonic_increasing:
            raise ValueError("`index` must be ordered.")
        # Find the indices of the previous first session minute and the next
        # last session minute for each minute.
        index_nanos = minutes.values.astype(np.int64)
        first_min_nanos = self.first_minutes_nanos
        last_min_nanos = self.last_minutes_nanos
        prev_first_mins_idxs = (
            first_min_nanos.searchsorted(index_nanos, side="right") - 1
        )
        next_last_mins_idxs = last_min_nanos.searchsorted(index_nanos, side="left")

        # If they don't match, the minute is outside the trading day. Barf.
        mismatches = prev_first_mins_idxs != next_last_mins_idxs
        if mismatches.any():
            # Show the first bad minute in the error message.
            bad_ix = np.flatnonzero(mismatches)[0]
            example = minutes[bad_ix]

            prev_session_idx = prev_first_mins_idxs[bad_ix]
            prev_first_min = pd.Timestamp(first_min_nanos[prev_session_idx], tz=UTC)
            prev_last_min = pd.Timestamp(last_min_nanos[prev_session_idx], tz=UTC)
            next_first_min = pd.Timestamp(first_min_nanos[prev_session_idx + 1], tz=UTC)
            next_last_min = pd.Timestamp(last_min_nanos[prev_session_idx + 1], tz=UTC)

            raise ValueError(
                f"{mismatches.sum()} non-trading minutes in"
                f" minutes_to_sessions:\nFirst Bad Minute: {example}\n"
                f"Previous Session: {prev_first_min} -> {prev_last_min}\n"
                f"Next Session: {next_first_min} -> {next_last_min}"
            )

        return self.schedule.index[prev_first_mins_idxs]

    # Methods that evaluate or interrogate a range of sessions.

    def _parse_start_end_dates(
        self, start: Date, end: Date, _parse: bool
    ) -> tuple[pd.Timestamp, pd.Timestamp]:
        if not _parse:
            return start, end
        return parse_date(start, "start", self), parse_date(end, "end", self)

    def _get_sessions_slice(self, start: Date, end: Date, _parse=True) -> slice:
        """Slice representing a range of sessions."""
        start, end = self._parse_start_end_dates(start, end, _parse)
        slice_start = self.sessions_nanos.searchsorted(start.value, side="left")
        slice_end = self.sessions_nanos.searchsorted(end.value, side="right")
        return slice(slice_start, slice_end)

    def sessions_in_range(
        self, start_session_label: Date, end_session_label: Date, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return sessions within a given range.

        Parameters
        ----------
        start_session_label
            Start of session range (range inclusive of `start`).

        end_session_label
            End of session range (range inclusive of `end`).

        Returns
        -------
        pd.DatetimeIndex
            Sessions from `start_session_label` through `end_session_label`.
        """
        slc = self._get_sessions_slice(start_session_label, end_session_label, _parse)
        return self.sessions[slc]

    def sessions_has_break(self, start: Date, end: Date, _parse: bool = True) -> bool:
        """Query if at least one session in a session range has a break.

        Parameters
        ----------
        start
            Start of session range (range inclusive of `start`).

        end
            End of session range (range inclusive of `end`).

        Returns
        -------
        bool
            True if any session in session range has a break, False otherwise.
        """
        slc = self._get_sessions_slice(start, end, _parse)
        return self.break_starts[slc].notna().any()

    def sessions_window(
        self, session_label: Session, count: int, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return block of given size of consecutive sessions.

        Parameters
        ----------
        session_label
            Session representing the first (if `count` positive) or last
            (if `count` negative) session of session window.

        count
            Number of sessions to include in window in addition to
                `session_label` (i.e. 0 will return window of length 1 with
                `session_label` as only value).
            Positive to return window of sessions from `session_label`
            Negative to return window of sessions to `session_label`.
        """
        if _parse:
            session_label = parse_session(self, session_label, "session_label")
        start_idx = self._get_session_idx(session_label, _parse=False)
        end_idx = start_idx + count
        if end_idx < 0:
            raise ValueError(
                f"Sessions window cannot begin before the first calendar session"
                f" ({self.first_session}). `count` cannot be lower than"
                f" {count - end_idx} for `session` '{session_label}'."
            )
        elif end_idx >= len(self.sessions):
            raise ValueError(
                f"Sessions window cannot end after the last calendar session"
                f" ({self.last_session}). `count` cannot be higher than"
                f" {count - (end_idx - len(self.sessions) + 1)} for"
                f" `session` '{session_label}'."
            )
        return self.sessions[min(start_idx, end_idx) : max(start_idx, end_idx) + 1]

    def sessions_distance(self, start: Date, end: Date, _parse: bool = True) -> int:
        """Return the number of sessions in a range.

        Parameters
        ----------
        start
            Start of session range (range inclusive of `start`).

        end
            End of session range (range inclusive of `end`).

        Returns
        -------
        int
            Number of sessions in session range, If `start` is later than
            `end` then return will be negated.
        """
        start, end = self._parse_start_end_dates(start, end, _parse)
        negate = end < start
        if negate:
            start, end = end, start
        slc = self._get_sessions_slice(start, end, _parse=False)
        return slc.start - slc.stop if negate else slc.stop - slc.start

    def sessions_minutes(
        self, start: Date, end: Date, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return trading minutes over a sessions range.

        Parameters
        ----------
        start
            Start of session range (range inclusive of `start`).

        end
            End of session range (range inclusive of `end`).

        Returns
        -------
        pd.DatetimeIndex
            Trading minutes for sessions in range.
        """
        start, end = self._parse_start_end_dates(start, end, _parse)
        start = self.date_to_session(start, "next", _parse=False)
        end = self.date_to_session(end, "previous", _parse=False)
        first_minute = self.session_first_minute(start)
        last_minute = self.session_last_minute(end)
        return self.minutes_in_range(first_minute, last_minute)

    def sessions_opens(self, start: Date, end: Date, _parse: bool = True) -> pd.Series:
        """Return UTC open time by session for sessions in given range.

        Parameters
        ----------
        start
            Start of session range (range inclusive of `start`).

        end
            End of session range (range inclusive of `end`).

        Returns
        -------
        pd.Series
            index:
                Sessions from `start` through `end` (inclusive of both).
            values:
                UTC open times for corresponding sessions.
        """
        start, end = self._parse_start_end_dates(start, end, _parse)
        return self.schedule.loc[start:end, "market_open"].dt.tz_localize(UTC)

    def sessions_closes(self, start: Date, end: Date, _parse: bool = True) -> pd.Series:
        """Return UTC close time by session for sessions in given range.

        Parameters
        ----------
        start
            Start of session range (range inclusive of `start`).

        end
            End of session range (range inclusive of `end`).

        Returns
        -------
        pd.Series
            index:
                Sessions from `start` through `end` (inclusive of both).
            values:
                UTC close times for corresponding sessions.
        """
        start, end = self._parse_start_end_dates(start, end, _parse)
        return self.schedule.loc[start:end, "market_close"].dt.tz_localize(UTC)

    def sessions_minutes_count(
        self, start: Date, end: Date, _parse: bool = True
    ) -> int:
        """Return number of trading minutes in a range of sessions.

        Parameters
        ----------
        start
            Start of session range (range inclusive of `start`).

        end
            End of session range (range inclusive of `end`).

        Returns
        -------
        int
            Total number of trading minutes in sessions range.
        """
        slc = self._get_sessions_slice(start, end, _parse)
        session_diff = self.last_minutes_nanos[slc] - self.first_minutes_nanos[slc]
        session_diff += NANOSECONDS_PER_MINUTE
        break_diff = self.first_pm_minutes_nanos[slc] - self.last_am_minutes_nanos[slc]
        break_diff[break_diff != 0] -= NANOSECONDS_PER_MINUTE
        nanos = session_diff - break_diff
        return (nanos // NANOSECONDS_PER_MINUTE).sum()

    def trading_index(
        self,
        start: Date,
        end: Date,
        period: pd.Timedelta | str,
        intervals: bool = True,
        closed: str = "left",  # when move to min 3.8 Literal["left", "right", "both", "neither"]
        force_close: bool = False,
        force_break_close: bool = False,
        curtail_overlaps: bool = False,
        parse: bool = True,
    ) -> pd.DatetimeIndex | pd.IntervalIndex:
        """Create a trading index.

        Create a trading index of given `period` over a given range of
        dates.

        NB. Which minutes the calendar treats as trading minutes, according
        to `self.side`, is irrelevant in the evaluation of the trading
        index.

        NB. Execution time is related to the number of indices created. The
        longer the range of dates covered and/or the shorter the period
        (i.e. higher the frequency), the longer the execution. Whilst an
        index with 4000 indices might be created in a couple of
        miliseconds, a high frequency index with 2 million indices might
        take a second or two.

        Parameters
        ----------
        start
            Start of session range over which to create index.

        end
            End of session range over which to create index.

        period
            If `intervals` is True, the length of each interval. If
            `intervals` is False, the distance between indices. Period
            should be passed as a pd.Timedelta or a str that's acceptable
            as a single input to pd.Timedelta. `period` cannot be greater
            than 1 day.

            Examples of valid `period` input:
                pd.Timedelta(minutes=15), pd.Timedelta(minutes=15, hours=2)
                '15min', '15T', '1H', '4h', '1d', '30s', '2s', '500ms'.
            Examples of invalid `period` input:
                '15minutes', '2d'.

        intervals : default: True
            True to return trading index as a pd.IntervalIndex with indices
            representing explicit intervals.

            False to return trading index as a pd.DatetimeIndex with
            indices that implicitely represent a period according to
            `closed`.

            If `period` is '1d' then trading index will be returned as a
            pd.DatetimeIndex.

        closed : {"left", "right", "both", "neither"}
            (ignored if `period` is '1d'.)

            If `intervals` is True, the side that intervals should be
            closed on. Must be either "left" or "right" (any time during a
            session must belong to one interval and one interval only).

            If `intervals` is False, the side of each period that an
            indice should be defined. The first and last indices of each
            (sub)session will be defined according to:
                "left" - include left side of first period, do not include
                    right side of last period.
                "right" - do not include left side of first period, include
                    right side of last period.
                "both" - include both left side of first period and right
                    side of last period.
                "neither" - do not include either left side of first period
                    or right side of last period.
            NB if `period` is not a factor of the (sub)session length then
            "right" or "both" will result in an indice being defined after
            the (sub)session close. See `force_close` and
            `force_break_close`.

        force_close : default: False
            (ignored if `period` is '1d')
            (irrelevant if `intervals` is False and `closed` is "left" or
            "neither")

            Defines behaviour if right side of a session's last period
            falls after the session close.

            If True, defines right side of this period as session close.

            If False, defines right side of this period after the session
            close. In this case the represented period will include a
            non-trading period.

        force_break_close : default: False
            (ignored if `period` is '1d'.)
            (irrelevant if `intervals` is False and `closed` is "left" or
            "neither.)

            Defines behaviour if right side of last pre-break period falls
            after the start of the break.

            If True, defines right side of this period as break start.

            If False, defines right side of this period after the break
            start. In this case the represented period will include a
            non-trading period.

        curtail_overlaps : default: False
            (ignored if `period` is '1d')
            (irrelevant if (`intervals` is False) or (`force_close` and
            `force_break_close` are both True).)

            Defines action to take if a period ends after the start of the
            next period. (This can occur if `period` is longer
            than a break or the gap between one session's close and the
            next session's open.)

                If True, the right of the earlier of two overlapping
                periods will be curtailed to the left of the latter period.
                (NB consequently the period length will not be constant for
                all periods.)

                If False, will raise IntervalsOverlapError.

        parse : default: True
            Determines if `start` and `end` values are parsed. If these
            arguments are passed as pd.Timestamp with no time component
            and tz as UTC then can pass `parse` as False to save around
            500µs on the execution.

        Returns
        -------
        pd.IntervalIndex or pd.DatetimeIndex
            Trading index.

            If `intervals` is False or `period` is '1d' then returned as a
                pd.DatetimeIndex.
            If `intervals` is True (default) returned as pd.IntervalIndex.

        Raises
        ------
        exchange_calendars.errors.IntervalsOverlapError
            If `intervals` is True and right side of one or more indices
            would fall after the left of the subsequent indice. This can
            occur if `period` is longer than a break or the gap between one
            session's close and the next session's open.

        exchange_calendars.errors.IntervalsOverlapError
            If `intervals` is False and an indice would otherwise fall to
            the right of the subsequent indice. This can occur if `period`
            is longer than a break or the gap between one session's close
            and the next session's open.

        Credit to @Stryder-Git at pandas_market_calendars for showing the
        way with a vectorised solution to creating trading indices (a
        variation of which is employed within the underlying _TradingIndex
        class).
        """
        start, end = self._parse_start_end_dates(start, end, parse)

        if not isinstance(period, pd.Timedelta):
            try:
                period = pd.Timedelta(period)
            except ValueError:
                msg = (
                    f"`period` receieved as '{period}' although takes type"
                    " 'pd.Timedelta' or a type 'str' that is valid as a single input"
                    " to 'pd.Timedelta'. Examples of valid input: pd.Timestamp('15T'),"
                    " '15min', '15T', '1H', '4h', '1d', '5s', 500ms'."
                )
                raise ValueError(msg) from None

        if period > pd.Timedelta(1, "D"):
            msg = (
                "`period` cannot be greater than one day although received as"
                f" '{period}'."
            )
            raise ValueError(msg)

        if period == pd.Timedelta(1, "D"):
            return self.sessions_in_range(start, end)

        if intervals and closed in ["both", "neither"]:
            raise ValueError(
                f"If `intervals` is True then `closed` cannot be '{closed}'."
            )

        # method exposes public methods of _TradingIndex.
        _trading_index = _TradingIndex(
            self,
            start,
            end,
            period,
            closed,
            force_close,
            force_break_close,
            curtail_overlaps,
        )

        if not intervals:
            return _trading_index.trading_index()
        else:
            return _trading_index.trading_index_intervals()

    # Internal methods called by constructor.

    def _special_dates(self, calendars, ad_hoc_dates, start_date, end_date):
        """
        Compute a Series of times associated with special dates.

        Parameters
        ----------
        holiday_calendars : list[(datetime.time, HolidayCalendar)]
            Pairs of time and calendar describing when that time occurs. These
            are used to describe regularly-scheduled late opens or early
            closes.
        ad_hoc_dates : list[(datetime.time, list[pd.Timestamp])]
            Pairs of time and list of dates associated with the given times.
            These are used to describe late opens or early closes that occurred
            for unscheduled or otherwise irregular reasons.
        start_date : pd.Timestamp
            Start of the range for which we should calculate special dates.
        end_date : pd.Timestamp
            End of the range for which we should calculate special dates.

        Returns
        -------
        special_dates : pd.Series
            Series mapping trading sessions with special opens/closes to the
            special open/close for that session.
        """
        # List of Series for regularly-scheduled times.
        regular = [
            scheduled_special_times(
                calendar,
                start_date,
                end_date,
                time_,
                self.tz,
            )
            for time_, calendar in calendars
        ]

        # List of Series for ad-hoc times.
        ad_hoc = [
            pd.Series(
                index=pd.to_datetime(datetimes, utc=True),
                data=days_at_time(datetimes, time_, self.tz),
            )
            for time_, datetimes in ad_hoc_dates
        ]

        merged = regular + ad_hoc
        if not merged:
            # Concat barfs if the input has length 0.
            return pd.Series(
                [], index=pd.DatetimeIndex([], tz=UTC), dtype="datetime64[ns, UTC]"
            )

        result = pd.concat(merged).sort_index()
        # end_date + one day to include all times of last day, otherwise if
        # end_date */12/31 00:00 then */12/31 12:30 would be excluded.
        end_rng = end_date + pd.Timedelta(1, "D")
        result = result.loc[(result >= start_date) & (result < end_rng)]
        # exclude any special date that conincides with a holiday
        adhoc_holidays = pd.DatetimeIndex(self.adhoc_holidays, tz="UTC")
        result = result[~result.index.isin(adhoc_holidays)]
        reg_holidays = self.regular_holidays.holidays(
            start_date.tz_convert(None), end_date.tz_convert(None)
        )
        if not reg_holidays.empty:
            result = result[~result.index.isin(reg_holidays.tz_localize(UTC))]
        return result

    def _calculate_special_opens(self, start, end):
        return self._special_dates(
            self.special_opens,
            self.special_opens_adhoc,
            start,
            end,
        )

    def _calculate_special_closes(self, start, end):
        return self._special_dates(
            self.special_closes,
            self.special_closes_adhoc,
            start,
            end,
        )

    def _overwrite_special_offsets(
        self,
        session_labels,
        opens_or_closes,
        calendars,
        ad_hoc_dates,
        start_date,
        end_date,
        strict=False,
    ):
        # Short circuit when nothing to apply.
        if opens_or_closes is None or not len(opens_or_closes):
            return

        len_m, len_oc = len(session_labels), len(opens_or_closes)
        if len_m != len_oc:
            raise ValueError(
                "Found misaligned dates while building calendar.\n"
                "Expected session_labels to be the same length as "
                "open_or_closes but,\n"
                "len(session_labels)=%d, len(open_or_closes)=%d" % (len_m, len_oc)
            )

        regular = []
        for offset, calendar in calendars:
            days = calendar.holidays(start_date, end_date)
            series = pd.Series(
                index=pd.DatetimeIndex(days, tz=UTC),
                data=offset,
            )
            regular.append(series)

        ad_hoc = []
        for offset, datetimes in ad_hoc_dates:
            series = pd.Series(
                index=pd.to_datetime(datetimes, utc=True),
                data=offset,
            )
            ad_hoc.append(series)

        merged = regular + ad_hoc
        if not merged:
            return pd.Series([], dtype="timedelta64[ns]")

        result = pd.concat(merged).sort_index()
        offsets = result.loc[(result.index >= start_date) & (result.index <= end_date)]

        # Find the array indices corresponding to each special date.
        indexer = session_labels.get_indexer(offsets.index)

        # -1 indicates that no corresponding entry was found.  If any -1s are
        # present, then we have special dates that doesn't correspond to any
        # trading day.
        if -1 in indexer and strict:
            bad_dates = list(offsets.index[indexer == -1])
            raise ValueError("Special dates %s are not trading days." % bad_dates)

        special_opens_or_closes = opens_or_closes[indexer] + offsets

        # Short circuit when nothing to apply.
        if not len(special_opens_or_closes):
            return

        # NOTE: This is a slightly dirty hack.  We're in-place overwriting the
        # internal data of an Index, which is conceptually immutable.  Since we're
        # maintaining sorting, this should be ok, but this is a good place to
        # sanity check if things start going haywire with calendar computations.
        opens_or_closes.values[indexer] = special_opens_or_closes.values

    def _calculate_and_overwrite_special_offsets(self, session_labels, start, end):
        _special_offsets = self.special_offsets
        _special_offsets_adhoc = self.special_offsets_adhoc

        _special_open_offsets = [
            (t[0], t[-1]) for t in _special_offsets if t[0] is not None
        ]
        _special_open_offsets_adhoc = [
            (t[0], t[-1]) for t in _special_offsets_adhoc if t[0] is not None
        ]
        _special_break_start_offsets = [
            (t[1], t[-1]) for t in _special_offsets if t[1] is not None
        ]
        _special_break_start_offsets_adhoc = [
            (t[1], t[-1]) for t in _special_offsets_adhoc if t[1] is not None
        ]
        _special_break_end_offsets = [
            (t[2], t[-1]) for t in _special_offsets if t[2] is not None
        ]
        _special_break_end_offsets_adhoc = [
            (t[2], t[-1]) for t in _special_offsets_adhoc if t[2] is not None
        ]
        _special_close_offsets = [
            (t[3], t[-1]) for t in _special_offsets if t[3] is not None
        ]
        _special_close_offsets_adhoc = [
            (t[3], t[-1]) for t in _special_offsets_adhoc if t[3] is not None
        ]

        self._overwrite_special_offsets(
            session_labels,
            self._opens,
            _special_open_offsets,
            _special_open_offsets_adhoc,
            start,
            end,
        )
        self._overwrite_special_offsets(
            session_labels,
            self._break_starts,
            _special_break_start_offsets,
            _special_break_start_offsets_adhoc,
            start,
            end,
        )
        self._overwrite_special_offsets(
            session_labels,
            self._break_ends,
            _special_break_end_offsets,
            _special_break_end_offsets_adhoc,
            start,
            end,
        )
        self._overwrite_special_offsets(
            session_labels,
            self._closes,
            _special_close_offsets,
            _special_close_offsets_adhoc,
            start,
            end,
        )

    # Deprecated methods to be removed in release 4.0.

    @deprecate(renamed=False)
    def execution_time_from_open(self, open_dates, _parse=False):
        return open_dates

    @deprecate(renamed=False)
    def execution_time_from_close(self, close_dates, _parse=False):
        return close_dates

    @deprecate(alt="minutes_for_session", renamed=False)
    def execution_minutes_for_session(
        self, session_label: Session, _parse=False
    ) -> pd.DatetimeIndex:
        """
        Given a session label, return the execution minutes for that session.

        Parameters
        ----------
        session_label
            A session label whose session's minutes are desired.

        Returns
        -------
        pd.DateTimeIndex
            All the execution minutes for the given session.
        """
        return self.session_minutes(session_label)

    @deprecate(alt="minutes_for_sessions_in_range", renamed=False)
    def execution_minutes_for_sessions_in_range(self, start, stop, _parse=False):
        minutes = self.execution_minutes_for_session
        return pd.DatetimeIndex(
            np.concatenate(
                [minutes(session) for session in self.sessions_in_range(start, stop)]
            ),
            tz=UTC,
        )

    @deprecate(alt="date_to_session")
    def date_to_session_label(
        self,
        date: Date,
        direction: str = "none",
        _parse: bool = True,
    ) -> pd.Timestamp:
        """Method renamed. Use `date_to_session`."""
        return self.date_to_session(date, direction, _parse)

    @deprecate(alt="session_open_close")
    def open_and_close_for_session(
        self, session_label: Session, _parse: bool = True
    ) -> tuple[pd.Timestamp, pd.Timestamp]:
        """Method renamed. Use `session_open_close`."""
        self.session_open_close(session_label, _parse)

    @deprecate(alt="session_break_start_end")
    def break_start_and_end_for_session(
        self, session_label: Session, _parse: bool = True
    ) -> tuple[pd.Timestamp | pd.NaT, pd.Timestamp | pd.NaT]:
        """Method renamed. Use `session_break_start_end."""
        return self.session_break_start_end(session_label, _parse)

    @deprecate(alt="next_session")
    def next_session_label(
        self, session_label: Session, _parse: bool = True
    ) -> pd.Timestamp:
        """Method renamed. Use `next_session`."""
        return self.next_session(session_label, _parse)

    @deprecate(alt="previous_session")
    def previous_session_label(
        self, session_label: Session, _parse: bool = True
    ) -> pd.Timestamp:
        """Method renamed. Use `previous_session`."""
        return self.previous_session(session_label, _parse)

    @deprecate(alt="session_minutes")
    def minutes_for_session(
        self, session_label: Session, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Method renamed. Use `session_minutes`."""
        return self.session_minutes(session_label, _parse)

    @property
    @deprecate(alt="sessions", prop=True)
    def all_sessions(self) -> pd.DatetimeIndex:
        """Property renamed. See `sessions`."""
        return self.sessions

    @property
    @deprecate(alt="minutes", prop=True)
    def all_minutes(self) -> pd.DatetimeIndex:
        """Property renamed. Use `minutes`."""
        return self.minutes

    @property
    @deprecate(alt="minutes_nanos", prop=True)
    def all_minutes_nanos(self) -> pd.DatetimeIndex:
        """Property renamed. Use `minutes_nanos`."""
        return self.minutes_nanos

    @property
    @deprecate(alt="first_minute", prop=True)
    def first_trading_minute(self) -> pd.Timestamp:
        """Property renamed. Use `first_minute`."""
        return self.first_minute

    @property
    @deprecate(alt="last_minute", prop=True)
    def last_trading_minute(self) -> pd.Timestamp:
        """Property renamed. Use `last_minute`."""
        return self.last_minute

    @property
    @deprecate(alt="first_session", prop=True)
    def first_trading_session(self) -> pd.Timestamp:
        """Property renamed. Use `first_session`."""
        return self.first_session

    @property
    @deprecate(alt="last_session", prop=True)
    def last_trading_session(self) -> pd.Timestamp:
        """Property renamed. Use `last_session`."""
        return self.last_session

    @deprecate(alt="sessions_has_break")
    def has_breaks(
        self, start: Date | None = None, end: Date | None = None, _parse: bool = True
    ) -> bool:
        """Method renamed. Use `sessions_has_break`."""
        return self.sessions_has_break(start, end, _parse)

    @property
    @deprecate(alt="opens_nanos", prop=True)
    def market_opens_nanos(self) -> np.ndarray:
        """Attribute renamed. Use `opens_nanos`."""
        return self.opens_nanos

    @property
    @deprecate(alt="closes_nanos", prop=True)
    def market_closes_nanos(self) -> np.ndarray:
        """Attribute renamed. Use `closes_nanos`."""
        return self.closes_nanos

    @property
    @deprecate(alt="break_starts_nanos", prop=True)
    def market_break_starts_nanos(self) -> np.ndarray:
        """Attribute renamed. Use `break_starts_nanos`."""
        return self.break_starts_nanos

    @property
    @deprecate(alt="break_ends_nanos", prop=True)
    def market_break_ends_nanos(self) -> np.ndarray:
        """Attribute renamed. Use `break_ends_nanos`."""
        return self.break_ends_nanos

    @deprecate(alt="minute_to_session")
    def minute_to_session_label(
        self,
        dt: Minute,
        direction: str = "next",
        _parse: bool = True,
    ) -> pd.Timestamp:
        """Method renamed. Use `minute_to_session`."""
        return self.minute_to_session(dt, direction, _parse)

    @deprecate(alt="minutes_to_sessions")
    def minute_index_to_session_labels(
        self, index: pd.DatetimeIndex
    ) -> pd.DatetimeIndex:
        """Method renamed. Use `minutes_to_sessions`."""
        return self.minutes_to_sessions(index)

    @deprecate(alt="sessions_distance")
    def session_distance(
        self,
        start_session_label: Date,
        end_session_label: Date,
        _parse: bool = True,
    ) -> int:
        """Method renamed. Use `sessions_distance`."""
        return self.sessions_distance(start_session_label, end_session_label, _parse)

    @deprecate(alt="sessions_minutes")
    def minutes_for_sessions_in_range(
        self,
        start_session_label: Date,
        end_session_label: Date,
        _parse: bool = True,
    ) -> pd.DatetimeIndex:
        """Method renamed. Use `sessions_minutes`."""
        return self.sessions_minutes(start_session_label, end_session_label, _parse)

    @deprecate(alt="sessions_opens")
    def session_opens_in_range(
        self, start_session_label: Date, end_session_label: Date, _parse: bool = True
    ) -> pd.Series:
        """Method renamed. Use `sessions_opens`."""
        return self.sessions_opens(start_session_label, end_session_label, _parse)

    @deprecate(alt="sessions_closes")
    def session_closes_in_range(
        self, start_session_label: Date, end_session_label: Date, _parse: bool = True
    ) -> pd.Series:
        """Method renamed. Use `sessions_closes`."""
        return self.sessions_closes(start_session_label, end_session_label, _parse)

    @deprecate(alt="sessions_minutes_count")
    def minutes_count_for_sessions_in_range(
        self, start_session: Date, end_session: Date, _parse=False
    ) -> int:
        """Method renamed. Use `sessions_minutes_count`."""
        return self.sessions_minutes_count(start_session, end_session, _parse)


def _check_breaks_match(break_starts_nanos: np.ndarray, break_ends_nanos: np.ndarray):
    """Checks that break_starts_nanos and break_ends_nanos match."""
    nats_match = np.equal(NP_NAT == break_starts_nanos, NP_NAT == break_ends_nanos)
    if not nats_match.all():
        raise ValueError(
            """
            Mismatched market breaks
            Break starts:
            {0}
            Break ends:
            {1}
            """.format(
                break_starts_nanos[~nats_match],
                break_ends_nanos[~nats_match],
            )
        )


def scheduled_special_times(calendar, start, end, time, tz):
    """
    Returns a Series mapping each holiday (as a UTC midnight Timestamp)
    in ``calendar`` between ``start`` and ``end`` to that session at
    ``time`` (as a UTC Timestamp).
    """
    days = calendar.holidays(start, end)
    return pd.Series(
        index=pd.DatetimeIndex(days, tz=UTC),
        data=days_at_time(days, time, tz=tz),
    )


def _overwrite_special_dates(session_labels, opens_or_closes, special_opens_or_closes):
    """
    Overwrite dates in open_or_closes with corresponding dates in
    special_opens_or_closes, using session_labels for alignment.
    """
    # Short circuit when nothing to apply.
    if not len(special_opens_or_closes):
        return

    len_m, len_oc = len(session_labels), len(opens_or_closes)
    if len_m != len_oc:
        raise ValueError(
            "Found misaligned dates while building calendar.\n"
            "Expected session_labels to be the same length as "
            "open_or_closes but,\n"
            "len(session_labels)=%d, len(open_or_closes)=%d" % (len_m, len_oc)
        )

    # Find the array indices corresponding to each special date.
    indexer = session_labels.get_indexer(special_opens_or_closes.index)

    # -1 indicates that no corresponding entry was found.  If any -1s are
    # present, then we have special dates that doesn't correspond to any
    # trading day.
    if -1 in indexer:
        bad_dates = list(special_opens_or_closes[indexer == -1])
        raise ValueError("Special dates %s are not trading days." % bad_dates)

    # NOTE: This is a slightly dirty hack.  We're in-place overwriting the
    # internal data of an Index, which is conceptually immutable.  Since we're
    # maintaining sorting, this should be ok, but this is a good place to
    # sanity check if things start going haywire with calendar computations.
    opens_or_closes.values[indexer] = special_opens_or_closes.values


def _remove_breaks_for_special_dates(
    session_labels, break_start_or_end, special_opens_or_closes
):
    """
    Overwrite breaks in break_start_or_end with corresponding dates in
    special_opens_or_closes, using session_labels for alignment.
    """
    # Short circuit when we have no breaks
    if break_start_or_end is None:
        return

    # Short circuit when nothing to apply.
    if not len(special_opens_or_closes):
        return

    len_m, len_oc = len(session_labels), len(break_start_or_end)
    if len_m != len_oc:
        raise ValueError(
            "Found misaligned dates while building calendar.\n"
            "Expected session_labels to be the same length as break_starts,\n"
            "but len(session_labels)=%d, len(break_start_or_end)=%d" % (len_m, len_oc)
        )

    # Find the array indices corresponding to each special date.
    indexer = session_labels.get_indexer(special_opens_or_closes.index)

    # -1 indicates that no corresponding entry was found.  If any -1s are
    # present, then we have special dates that doesn't correspond to any
    # trading day.
    if -1 in indexer:
        bad_dates = list(special_opens_or_closes[indexer == -1])
        raise ValueError("Special dates %s are not trading days." % bad_dates)

    # NOTE: This is a slightly dirty hack.  We're in-place overwriting the
    # internal data of an Index, which is conceptually immutable.  Since we're
    # maintaining sorting, this should be ok, but this is a good place to
    # sanity check if things start going haywire with calendar computations.
    break_start_or_end.values[indexer] = NP_NAT


class HolidayCalendar(AbstractHolidayCalendar):
    def __init__(self, rules):
        super(HolidayCalendar, self).__init__(rules=rules)
