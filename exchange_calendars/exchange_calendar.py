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

from abc import ABC, abstractmethod
from calendar import day_name
import collections
from collections.abc import Sequence, Callable
import datetime
import functools
import operator
from typing import TYPE_CHECKING, Literal, Any
import warnings
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import toolz
from pandas.tseries.holiday import AbstractHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay

from exchange_calendars import errors
from .calendar_helpers import (
    UTC,
    NANOSECONDS_PER_MINUTE,
    NP_NAT,
    Date,
    Minute,
    Session,
    TradingMinute,
    _TradingIndex,
    compute_minutes,
    next_divider_idx,
    one_minute_earlier,
    one_minute_later,
    parse_date,
    parse_session,
    parse_timestamp,
    parse_trading_minute,
    previous_divider_idx,
)
from .utils.pandas_utils import days_at_time

if TYPE_CHECKING:
    from pandas._libs.tslibs.nattype import NaTType


GLOBAL_DEFAULT_START = pd.Timestamp.now().floor("D") - pd.DateOffset(years=20)
# Give an aggressive buffer for logic that needs to use the next trading
# day or minute.
GLOBAL_DEFAULT_END = pd.Timestamp.now().floor("D") + pd.DateOffset(years=1)

NANOS_IN_MINUTE = 60000000000
MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY = range(7)
WEEKDAYS = (MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY)
WEEKENDS = (SATURDAY, SUNDAY)


def selection(
    arr: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp
) -> pd.DatetimeIndex:
    predicates = []
    if start is not None:
        predicates.append(start <= arr)
    if end is not None:
        predicates.append(arr < end)

    if not predicates:
        return arr

    return arr[np.all(predicates, axis=0)]


def _group_times(
    sessions: pd.DatetimeIndex,
    times: None | Sequence[tuple[pd.Timestamp | None, datetime.time]],
    tz: ZoneInfo,
    offset: int = 0,
) -> pd.DatetimeIndex | None:
    """Evaluate standard times for a specific session bound.

    For example, if `times` passed as standard times for session opens then
    will return a DatetimeIndex describing standard open times for each
    session.
    """
    if times is None:
        return None
    elements = [
        days_at_time(selection(sessions, start, end), time, tz, offset)
        for (start, time), (end, _) in toolz.sliding_window(
            2, toolz.concatv(times, [(None, None)])
        )
    ]
    return elements[0].append(elements[1:])


class deprecate:
    """Decorator for deprecated ExchangeCalendar methods."""

    def __init__(
        self,
        deprecated_release: str = "4.0",
        message: str | None = None,
    ):
        self.deprecated_release = "release " + deprecated_release
        self.message = message

    def __call__(self, f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapped_f(*args, **kwargs):
            warnings.warn(self._message(f), FutureWarning)
            return f(*args, **kwargs)

        return wrapped_f

    def _message(self, f: Callable) -> str:
        msg = (
            f"`{f.__name__}` was deprecated in {self.deprecated_release}"
            f" and will be removed in a future release."
        )
        if self.message is not None:
            msg += " " + self.message
        return msg


class HolidayCalendar(AbstractHolidayCalendar):
    def __init__(self, rules):
        super().__init__(rules=rules)


class ExchangeCalendar(ABC):
    """Representation of timing information of a single market exchange.

    The timing information comprises sessions, open/close times and, for
    exchanges that observe an intraday break, break_start/break_end times.

    For exchanges that do not observe an intraday break a session
    represents a contiguous set of minutes. Where an exchange observes
    an intraday break a session represents two contiguous sets of minutes
    separated by the intraday break.

    Each session is labeled as the date that the session represents.

    For each session, we store the open and close time together with, for
    those exchanges with breaks, the break start and break end. All times
    are defined as UTC.

    Note that a session may start on the day prior to the session label or
    end on the day following the session label. Such behaviour is common
    for calendars that represent futures exchanges.

    Parameters
    ----------
    start : default: later of 20 years ago or first supported start date.
        First calendar session will be `start`, if `start` is a session, or
        first session after `start`. Cannot be earlier than any date
        returned by class method `bound_min`.

    end : default: earliest of 1 year from 'today' or last supported end
        date. Last calendar session will be `end`, if `end` is a session,
        or last session before `end`. Cannot be later than any date
        returned by class method `bound_max`.

    side : default: "left"
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
    exposed via the `bound_min` and `bound_max` class methods.

    Many calendars do not have bounds defined (in these cases `bound_min`
    and/or `bound_max` return None). These calendars can be created through
    any date range although it should be noted that the earlier the start
    date, the greater the potential for inaccuracies.

    In all cases, no guarantees are offered as to the accuracy of any
    calendar.


    -- Internal method parameters --

    _parse: bool
        Determines if a `minute` or `session` parameter should be
        parsed (default True). Passed as False:
            - internally to prevent double parsing.
            - by tests for efficiency.
    """

    _LEFT_SIDES = ["left", "both"]
    _RIGHT_SIDES = ["right", "both"]

    @classmethod
    def bound_min(cls) -> pd.Timestamp | None:
        """Earliest date from which calendar can be constructed.

        Returns
        -------
        pd.Timestamp or None
            Earliest date from which calendar can be constructed. Must be
            timezone naive. None if no limit.

        Notes
        -----
        To impose a constraint on the earliest date from which a calendar
        can be constructed subclass should override this method and
        optionally override `_bound_min_error_msg`.
        """
        return None

    @classmethod
    def bound_max(cls) -> pd.Timestamp | None:
        """Latest date to which calendar can be constructed.

        Returns
        -------
        pd.Timestamp or None
            Latest date to which calendar can be constructed. Must be
            timezone naive. None if no limit.

        Notes
        -----
        To impose a constraint on the latest date to which a calendar can
        be constructed subclass should override this method and optionally
        override `_bound_max_error_msg`.
        """
        return None

    @classmethod
    def default_start(cls) -> pd.Timestamp:
        """Return default calendar start date.

        Calendar will start from this date if 'start' is not otherwise
        passed to the constructor.
        """
        bound_min = cls.bound_min()
        if bound_min is None:
            return GLOBAL_DEFAULT_START
        else:
            return max(GLOBAL_DEFAULT_START, bound_min)

    @classmethod
    def default_end(cls) -> pd.Timestamp:
        """Return default calendar end date.

        Calendar will end at this date if 'end' is not otherwise passed to
        the constructor.
        """
        bound_max = cls.bound_max()
        if bound_max is None:
            return GLOBAL_DEFAULT_END
        else:
            return min(GLOBAL_DEFAULT_END, bound_max)

    def __init__(
        self,
        start: Date | None = None,
        end: Date | None = None,
        side: Literal["left", "right", "both", "neither"] = "left",
    ):
        if side not in self.valid_sides():
            raise ValueError(
                f"`side` must be in {self.valid_sides()} although received as {side}."
            )
        self._side = side

        if start is None:
            start = self.default_start()
        else:
            start = parse_date(start, "start", raise_oob=False)
            bound_min = self.bound_min()
            if bound_min is not None and start < bound_min:
                raise ValueError(self._bound_min_error_msg(start))

        if end is None:
            end = self.default_end()
        else:
            end = parse_date(end, "end", raise_oob=False)
            bound_max = self.bound_max()
            if bound_max is not None and end > bound_max:
                raise ValueError(self._bound_max_error_msg(end))

        if start >= end:
            raise ValueError(
                "`start` must be earlier than `end` although `start` parsed as"
                f" '{start}' and `end` as '{end}'."
            )

        _all_days = pd.date_range(start, end, freq=self.day)  # session labels
        if _all_days.empty:
            raise errors.NoSessionsError(calendar_name=self.name, start=start, end=end)

        # DatetimeIndex of standard times for each day.
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

        # Apply any special offsets first
        self.apply_special_offsets(_all_days, start, end)

        # Series mapping sessions with non-standard opens/closes.
        _special_opens = self._calculate_special_opens(start, end)
        _special_closes = self._calculate_special_closes(start, end)

        # Overwrite the special opens and closes on top of the standard ones.
        _overwrite_special_dates(_all_days, self._opens, _special_opens)
        _overwrite_special_dates(_all_days, self._closes, _special_closes)
        _remove_breaks_for_special_dates(_all_days, self._break_starts, _special_closes)
        _remove_breaks_for_special_dates(_all_days, self._break_ends, _special_closes)

        break_starts = None if self._break_starts is None else self._break_starts
        break_ends = None if self._break_ends is None else self._break_ends
        self.schedule = pd.DataFrame(
            index=_all_days,
            data=collections.OrderedDict(
                [
                    ("open", self._opens),
                    ("break_start", break_starts),
                    ("break_end", break_ends),
                    ("close", self._closes),
                ]
            ),
            dtype="datetime64[ns, UTC]",
        )

        self.opens_nanos = self.schedule.open.values.astype(np.int64)
        self.break_starts_nanos = self.schedule.break_start.values.astype(np.int64)
        self.break_ends_nanos = self.schedule.break_end.values.astype(np.int64)
        self.closes_nanos = self.schedule.close.values.astype(np.int64)

        _check_breaks_match(self.break_starts_nanos, self.break_ends_nanos)

        self._late_opens = _special_opens.index
        self._early_closes = _special_closes.index

    # --------------- Calendar definition methods/properties --------------
    # Methods and properties in this section should be overriden or
    # extended by subclass if and as required.

    @property
    @abstractmethod
    def name(self) -> str:
        """Calendar name."""
        raise NotImplementedError()

    def _bound_min_error_msg(self, start: pd.Timestamp) -> str:
        """Return error message to handle `start` being out-of-bounds.

        See Also
        --------
        bound_min
        """
        return (
            f"The earliest date from which calendar {self.name} can be"
            f" evaluated is {self.bound_min()}, although received `start` as"
            f" {start}."
        )

    def _bound_max_error_msg(self, end: pd.Timestamp) -> str:
        """Return error message to handle `end` being out-of-bounds.

        See Also
        --------
        bound_max
        """
        return (
            f"The latest date to which calendar {self.name} can be evaluated"
            f" is {self.bound_max()}, although received `end` as {end}."
        )

    @property
    @abstractmethod
    def tz(self) -> ZoneInfo:
        """Calendar timezone."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def open_times(self) -> Sequence[tuple[pd.Timestamp | None, datetime.time]]:
        """Local open time(s).

        Returns
        -------
        Sequence[tuple[pd.Timestamp | None, datetime.time]]:
            Sequence of tuples representing (start_date, open_time) where:
                start_date: date from which `open_time` applies. Must be
                    timezone-naive. None for first item.
                open_time: exchange's local open time.

        Notes
        -----
        Examples for concreting `open_times` on a subclass.

        Example where open time is constant throughout period covered by
        calendar:
            open_times = ((None, datetime.time(9)),)

        Example where open times have varied over period covered by
        calendar:
            open_times = (
                (None, time(9, 30)),
                (pd.Timestamp("1978-04-01"), datetime.time(10, 0)),
                (pd.Timestamp("1986-04-01"), datetime.time(9, 40)),
                (pd.Timestamp("1995-01-01"), datetime.time(9, 30)),
                (pd.Timestamp("1998-12-07"), datetime.time(9, 0)),
            )
        """
        raise NotImplementedError()

    @property
    def break_start_times(
        self,
    ) -> None | Sequence[tuple[pd.Timestamp | None, datetime.time]]:
        """Local break start time(s).

        As `close_times` although times represent the close of the morning
        subsession. None if exchange does not observe a break.
        """
        return None

    @property
    def break_end_times(
        self,
    ) -> None | Sequence[tuple[pd.Timestamp | None, datetime.time]]:
        """Local break end time(s).

        As `open_times` although times represent the open of the afternoon
        subsession. None if exchange does not observe a break.
        """
        return None

    @property
    @abstractmethod
    def close_times(self) -> Sequence[tuple[pd.Timestamp | None, datetime.time]]:
        """Local close time(s).

        Returns
        -------
        Sequence[tuple[pd.Timestamp | None, datetime.time]]:
            Sequence of tuples representing (start_date, close_time) where:
                start_date: date from which `close_time` applies. Must be
                    timezone naive. None for first item.
                close_time: exchange's local close time.

        Notes
        -----
        Examples for concreting `close_times` on a subclass.

        Example where close time is constant throughout period covered by
        calendar:
            close_times = ((None, time(17, 30)),)

        Example where close times have varied over period covered by
        calendar:
            close_times = (
                (None, datetime.time(17, 30)),
                (pd.Timestamp("1986-04-01"), datetime.time(17, 20)),
                (pd.Timestamp("1995-01-01"), datetime.time(17, 0)),
                (pd.Timestamp("2016-08-01"), datetime.time(17, 30)),
            )
        """
        raise NotImplementedError()

    @property
    def weekmask(self) -> str:
        """Indicator of weekdays on which the exchange is open.

        Default is '1111100' (i.e. Monday-Friday).

        See Also
        --------
        numpy.busdaycalendar
        """
        return "1111100"

    @property
    def open_offset(self) -> int:
        """Day offset of open time(s) relative to session.

        Returns
        -------
        int
            0 if the date components of local open times are as the
            corresponding session labels.

            -1 if the date components of local open times are the day
            before the corresponding session labels.
        """
        return 0

    @property
    def close_offset(self) -> int:
        """Day offset of close time(s) relative to session.

        Returns
        -------
        int
            0 if the date components of local close times are as the
            corresponding session labels.

            1 if the date components of local close times are the day
            after the corresponding session labels.
        """
        return 0

    @property
    def regular_holidays(self) -> HolidayCalendar | None:
        """Holiday calendar representing calendar's regular holidays."""
        return None

    @property
    def adhoc_holidays(self) -> list[pd.Timestamp]:
        """List of non-regular holidays.

        Returns
        -------
        list[pd.Timestamp]
            List of tz-naive timestamps representing non-regular holidays.
        """
        return []

    @property
    def special_opens(self) -> list[tuple[datetime.time, HolidayCalendar] | int]:
        """Regular non-standard open times.

        Example of what would be defined as a special open:
            "EVERY YEAR on national lie-in day the exchange opens
            at 13:00 rather than the standard 09:00".

            "Every Monday the exchange opens late, at 10:30 rather than
            the standard 09:00".

        Returns
        -------
        list[tuple[datetime.time, HolidayCalendar | int]]:
            list of tuples each describing a regular non-standard open:
                [0] datetime.time: regular non-standard open time.

                [1] Describes dates with regular non-standard open time
                as [0]. As either:
                    HolidayCalendar: defines annual dates by rules.

                    int : integer defines a weekday with a regular
                    non-standard open (0 - Monday, ..., 6 - Sunday).

            The same date may be described by more than one tuple, for
            example, if a late open on an annual holiday coincides with
            a weekday late open. In this case the time assigned to the
            date will be that defined by the tuple with the lowest index
            in the returned list.
        """
        return []

    @property
    def special_opens_adhoc(
        self,
    ) -> list[tuple[datetime.time, pd.DatetimeIndex]]:
        """Adhoc non-standard open times.

        Defines non-standard open times that cannot be otherwise codified
        within within `special_opens`.

        Example of an event to define as an adhoc special open:
            "On 2022-02-14 due to a typhoon the exchange opened at 13:00,
            rather than the standard 09:00".

        Returns
        -------
        list[tuple[datetime.time, pd.DatetimeIndex]]:
            List of tuples each describing an adhoc non-standard open time:
                [0] datetime.time: non-standard open time.

                [1] pd.DatetimeIndex: date or dates corresponding with the
                non-standard open time. (Must be timezone-naive.)
        """
        return []

    @property
    def special_closes(self) -> list[tuple[datetime.time, HolidayCalendar | int]]:
        """Regular non-standard close times.

        Examples of what would be defined as a special close:
            "On christmas eve the exchange closes at 14:00 rather than
            the standard 17:00".

            "Every Friday the exchange closes early, at 14:00 rather than
            the standard 17:00".

        Returns
        -------
        list[tuple[datetime.time, HolidayCalendar | int]]:
            list of tuples each describing a regular non-standard close:
                [0] datetime.time: regular non-standard close time.

                [1] Describes dates with regular non-standard close time
                as [0]. As either:
                    HolidayCalendar: defines annual dates by rules.

                    int : integer defines a weekday with a regular
                    non-standard close (0 - Monday, ..., 6 - Sunday).

            The same date may be described by more than one tuple, for
            example, if an early close on an annual holiday coincides with
            a weekday early close. In this case the time assigned to the
            date will be that defined by the tuple with the lowest index
            in the returned list.
        """
        return []

    @property
    def special_closes_adhoc(
        self,
    ) -> list[tuple[datetime.time, pd.DatetimeIndex]]:
        """Adhoc non-standard close times.

        Defines non-standard close times that cannot be otherwise codified
        within within `special_closes`.

        Example of an event to define as an adhoc special close:
            "On 2022-02-19 due to a typhoon the exchange closed at 12:00,
            rather than the standard 16:00".

        Returns
        -------
        list[tuple[datetime.time, pd.DatetimeIndex]]:
            List of tuples each describing an adhoc non-standard close
            time:
                [0] datetime.time: non-standard close time.

                [1] pd.DatetimeIndex: date or dates corresponding with the
                non-standard close time. (Must be timezone-naive.)
        """
        return []

    def apply_special_offsets(
        self, sessions: pd.DatetimeIndex, start: pd.Timestamp, end: pd.Timestamp
    ) -> None:
        """Hook for subclass to apply changes.

        Method executed by constructor prior to overwritting special dates.

        Parameters
        ----------
        sessions
            All calendar sessions.

        start
            Date from which special offsets to be applied.

        end
            Date through which special offsets to be applied.

        Notes
        -----
        Incorporated to provide hook to `exchange_calendar_xkrx`.
        """
        return None

    # ------------------------------------------------------------------
    # -- NO method below this line should be overriden on a subclass! --
    # ------------------------------------------------------------------

    # Methods and properties that define calendar (continued...).

    @functools.cached_property
    def day(self) -> CustomBusinessDay:
        """CustomBusinessDay instance representing calendar sessions."""
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

    @property
    def side(self) -> Literal["left", "right", "both", "neither"]:
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

    @functools.cached_property
    def sessions_nanos(self) -> np.ndarray:
        """All calendar sessions as nano seconds."""
        return self.sessions.values.astype("int64")

    @property
    def opens(self) -> pd.Series:
        """Open time of each session.

        Returns
        -------
        pd.Series
            index : pd.DatetimeIndex
                All sessions.
            dtype : datetime64[ns, UTC]
                UTC open time of corresponding session.
        """
        return self.schedule.open

    @property
    def closes(self) -> pd.Series:
        """Close time of each session.

        Returns
        -------
        pd.Series
            index : pd.DatetimeIndex
                All sessions.
            dtype : datetime64[ns, UTC]
                UTC close time of corresponding session.
        """
        return self.schedule.close

    @property
    def break_starts(self) -> pd.Series:
        """Break start time of each session.

        Returns
        -------
        pd.Series
            index : pd.DatetimeIndex
                All sessions.
            dtype : datetime64[ns, UTC]
                UTC break-start time of corresponding session. Value is
                missing (pd.NaT) for any session that does not have a
                break.
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
            dtype : datetime64[ns, UTC]
                UTC break-end time of corresponding session.Value is
                missing (pd.NaT) for any session that does not have a
                break.
        """
        return self.schedule.break_end

    @functools.cached_property
    def first_minutes_nanos(self) -> np.ndarray:
        """Each session's first minute as an integer."""
        if self.side in self._LEFT_SIDES:
            return self.opens_nanos
        else:
            return one_minute_later(self.opens_nanos)

    @functools.cached_property
    def last_minutes_nanos(self) -> np.ndarray:
        """Each session's last minute as an integer."""
        if self.side in self._RIGHT_SIDES:
            return self.closes_nanos
        else:
            return one_minute_earlier(self.closes_nanos)

    @functools.cached_property
    def last_am_minutes_nanos(self) -> np.ndarray:
        """Each morning subsessions's last minute as an integer."""
        if self.side in self._RIGHT_SIDES:
            return self.break_starts_nanos
        else:
            return one_minute_earlier(self.break_starts_nanos)

    @functools.cached_property
    def first_pm_minutes_nanos(self) -> np.ndarray:
        """Each afternoon subsessions's first minute as an integer."""
        if self.side in self._LEFT_SIDES:
            return self.break_ends_nanos
        else:
            return one_minute_later(self.break_ends_nanos)

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

    def _minutes(
        self, side: Literal["left", "right", "both", "neither"]
    ) -> pd.DatetimeIndex:
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

    @functools.cached_property
    def minutes(self) -> pd.DatetimeIndex:
        """All trading minutes."""
        return self._minutes(self.side)

    @functools.cached_property
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
        return self.opens.iloc[0]

    @property
    def last_session_close(self) -> pd.Timestamp:
        """Close time of calendar's last session."""
        return self.closes.iloc[-1]

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
        session_ = parse_session(self, session) if _parse else session
        if TYPE_CHECKING:
            assert isinstance(session_, pd.Timestamp)
        return self.sessions_nanos.searchsorted(session_.value, side="left")

    def session_open(self, session: Session, _parse: bool = True) -> pd.Timestamp:
        """Return open time for a given session."""
        if _parse:
            session = parse_session(self, session, "session")
        return self.schedule.at[session, "open"]

    def session_close(self, session: Session, _parse: bool = True) -> pd.Timestamp:
        """Return close time for a given session."""
        if _parse:
            session = parse_session(self, session, "session")
        return self.schedule.at[session, "close"]

    def session_break_start(
        self, session: Session, _parse: bool = True
    ) -> pd.Timestamp | NaTType:
        """Return break-start time for a given session.

        Returns pd.NaT if no break.
        """
        if _parse:
            session = parse_session(self, session, "session")
        break_start = self.schedule.at[session, "break_start"]
        return break_start

    def session_break_end(
        self, session: Session, _parse: bool = True
    ) -> pd.Timestamp | NaTType:
        """Return break-end time for a given session.

        Returns pd.NaT if no break.
        """
        if _parse:
            session = parse_session(self, session, "session")
        break_end = self.schedule.at[session, "break_end"]
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
    ) -> tuple[pd.Timestamp | NaTType, pd.Timestamp | NaTType]:
        """Return break-start and break-end times for a given session.

        Parameters
        ----------
        session
            Session for which require break-start and break-end.

        Returns
        -------
        tuple[pd.Timestamp | NaTType, pd.Timestamp | NaTType]
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
    ) -> pd.Timestamp | pd.NaT:
        """Return last trading minute of am subsession of a given session."""
        nanos = self.last_am_minutes_nanos
        return self._get_session_minute_from_nanos(session, nanos, _parse)

    def session_first_pm_minute(
        self, session: Session, _parse: bool = True
    ) -> pd.Timestamp | pd.NaT:
        """Return first trading minute of pm subsession of a given session."""
        nanos = self.first_pm_minutes_nanos
        return self._get_session_minute_from_nanos(session, nanos, _parse)

    def session_first_last_minute(
        self,
        session: Session,
        _parse: bool = True,
    ) -> tuple[pd.Timestamp, pd.Timestamp]:
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
        errors.RequestedSessionOutOfBounds
            If `session` is the last calendar session.

        See Also
        --------
        date_to_session
        """
        idx = self._get_session_idx(session, _parse=_parse)
        try:
            return self.schedule.index[idx + 1]
        except IndexError:
            if idx == len(self.schedule.index) - 1:
                raise errors.RequestedSessionOutOfBounds(self, False) from None
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
        errors.RequestedSessionOutOfBounds
            If `session` is the first calendar session.

        See Also
        --------
        date_to_session
        """
        idx = self._get_session_idx(session, _parse=_parse)
        if not idx:
            raise errors.RequestedSessionOutOfBounds(self, True)
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
        return self.minutes_in_range(start=first, end=last)

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
        date_ = parse_date(date, "date", self) if _parse else date
        if TYPE_CHECKING:
            assert isinstance(date_, pd.Timestamp)
        return self.sessions_nanos.searchsorted(date_.value, side="left")

    def _date_oob(self, date: pd.Timestamp) -> bool:
        """Is `date` out-of-bounds."""
        return (
            date.value < self.sessions_nanos[0] or date.value > self.sessions_nanos[-1]
        )

    def is_session(self, date: Date, _parse: bool = True) -> bool:
        """Query if a date is a valid session.

        Parameters
        ----------
        date
            Date to be queried.

        Return
        ------
        bool
            True if `date` is a session, False otherwise.
        """
        if _parse:
            date = parse_date(date, "date", self)
        idx = self._get_date_idx(date, _parse=False)
        return bool(self.sessions_nanos[idx] == date.value)  # convert from np.bool_

    def date_to_session(
        self,
        date: Date,
        direction: Literal["next", "previous", "none"] = "none",
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
        is_open_at_time
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
        self, minute: Minute, ignore_breaks: bool = False, _parse: bool = True
    ) -> bool:
        """Query if exchange is open on a given minute.

        Note: `self.side` determines whether exchange will be considered
        open or closed on session open, session close, break start and
        break end.

        Parameters
        ----------
        minute
            Minute being queried.

        ignore_breaks
            Should exchange be considered open during any break?
                True - treat exchange as open during any break.
                False - treat exchange as closed during any break.

        Returns
        -------
        bool
            Boolean indicting if exchange is open on `minute`.

        See Also
        --------
        is_trading_minute
        is_open_at_time
        """
        if _parse:
            minute = parse_timestamp(minute, "minute", self)

        is_trading_minute = self.is_trading_minute(minute, _parse=False)
        if is_trading_minute or not ignore_breaks:
            return is_trading_minute
        else:
            # not a trading minute although should return True if in break
            return self.is_break_minute(minute, _parse=False)

    def is_open_at_time(
        self,
        timestamp: pd.Timestamp,
        side: Literal["left", "right", "both", "neither"] = "left",
        ignore_breaks: bool = False,
    ) -> bool:
        """Query if exchange is open at a given timestamp.

        Note: method differs from `is_trading_minute` and
        `is_open_on_minute` in that it does not consider if the market is
        open over an evaluated minute, but rather as at a specific
        instance that can be of any resolution.

        Parameters
        ----------
        timestamp
            Timestamp being queried.

            Can have any resolution (i.e. can be defined with second and
            more accurate components).

            If timezone naive then will be assumed as representing UTC.

        side
            Determines whether the exchange will be considered open or
            closed on a session's open, close, break-start and break-end:

                "left" - treat exchange as open on session open and
                any break-end, treat as closed on session close and any
                break-start.

                "right" - treat exchange as open on session close and
                any break-start, treat as closed on session open and any
                break-end.

                "both" (default) - treat exchange as open on all of session
                open, close and any break-start and break-end.

                "neither" - treat exchange as closed on all of session
                open, close and any break-start and break-end.

        ignore_breaks
            Should exchange be considered open during any break?
                True - treat exchange as open during any break.
                False - treat exchange as closed during any break.

        Returns
        -------
        bool
            Boolean indicting if exchange is open at time.

        See Also
        --------
        is_trading_minute
        is_open_on_minute
        """
        ts = timestamp
        if not isinstance(ts, pd.Timestamp):
            raise TypeError(
                "`timestamp` expected to receive type pd.Timestamp although"
                f" got type {type(ts)}."
            )

        if ts.tz is not UTC:
            ts = ts.tz_localize(UTC) if ts.tz is None else ts.tz_convert(UTC)

        if self._minute_oob(ts):
            raise errors.MinuteOutOfBounds(self, ts, "timestamp")

        op_left = operator.le if side in self._LEFT_SIDES else operator.lt
        op_right = operator.le if side in self._RIGHT_SIDES else operator.lt

        nano = ts.value
        if not self.has_break or ignore_breaks:
            # only one check requried
            bv = op_left(self.opens_nanos, nano) & op_right(nano, self.closes_nanos)
            return bv.any()

        break_starts_nanos = self.break_starts_nanos.copy()
        bv_missing = self.break_starts.isna()
        close_replacement = self.closes_nanos[bv_missing]
        break_starts_nanos[bv_missing] = close_replacement
        break_ends_nanos = self.break_ends_nanos.copy()
        break_ends_nanos[bv_missing] = close_replacement

        bv_am = op_left(self.opens_nanos, nano) & op_right(nano, break_starts_nanos)
        bv_pm = op_left(break_ends_nanos, nano) & op_right(nano, self.closes_nanos)
        return (bv_am | bv_pm).any()

    def next_open(self, minute: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return next open that follows a given minute.

        If `minute` is a session open, the next session's open will be
        returned.

        Parameters
        ----------
        minute
            Minute for which to get the next open.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the next open.
        """
        if _parse:
            minute = parse_timestamp(minute, "minute", self)
        try:
            idx = next_divider_idx(self.opens_nanos, minute.value)
        except IndexError:
            if minute >= self.opens.iloc[-1]:
                raise ValueError(
                    "Minute cannot be the last open or later (received `minute`"
                    f" parsed as '{minute}'.)"
                ) from None
            else:
                raise

        return pd.Timestamp(self.opens_nanos[idx], tz=UTC)

    def next_close(self, minute: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return next close that follows a given minute.

        If `minute` is a session close, the next session's close will be
        returned.

        Parameters
        ----------
        minute
            Minute for which to get the next close.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the next close.
        """
        if _parse:
            minute = parse_timestamp(minute, "minute", self)
        try:
            idx = next_divider_idx(self.closes_nanos, minute.value)
        except IndexError:
            if minute == self.closes.iloc[-1]:
                raise ValueError(
                    "Minute cannot be the last close (received `minute` parsed as"
                    f" '{minute}'.)"
                ) from None
            else:
                raise
        return pd.Timestamp(self.closes_nanos[idx], tz=UTC)

    def previous_open(self, minute: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return previous open that preceeds a given minute.

        If `minute` is a session open, the previous session's open will be
        returned.

        Parameters
        ----------
        minute
            Minute for which to get the previous open.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the previous open.
        """
        if _parse:
            minute = parse_timestamp(minute, "minute", self)
        try:
            idx = previous_divider_idx(self.opens_nanos, minute.value)
        except ValueError:
            if minute == self.opens.iloc[0]:
                raise ValueError(
                    "Minute cannot be the first open (received `minute` parsed as"
                    f" '{minute}'.)"
                ) from None
            else:
                raise

        return pd.Timestamp(self.opens_nanos[idx], tz=UTC)

    def previous_close(self, minute: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return previous close that preceeds a given minute.

        If `minute` is a session close, the previous session's close will be
        returned.

        Parameters
        ----------
        minute
            Minute for which to get the previous close.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the previous close.
        """
        if _parse:
            minute = parse_timestamp(minute, "minute", self)
        try:
            idx = previous_divider_idx(self.closes_nanos, minute.value)
        except ValueError:
            if minute <= self.closes.iloc[0]:
                raise ValueError(
                    "Minute cannot be the first close or earlier (received"
                    f" `minute` parsed as '{minute}'.)"
                ) from None
            else:
                raise

        return pd.Timestamp(self.closes_nanos[idx], tz=UTC)

    def next_minute(self, minute: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return trading minute that immediately follows a given minute.

        Parameters
        ----------
        minute
            Minute for which to get next trading minute. Minute can be a
            trading or a non-trading minute.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the next minute.

        Raises
        ------
        errors.RequestedSessionOutOfBounds
            If `minute` is the last calendar minute.
        """
        if _parse:
            minute = parse_timestamp(minute, "minute", self)
        try:
            idx = next_divider_idx(self.minutes_nanos, minute.value)
        except IndexError:
            # dt > last_minute handled via parsing
            if minute == self.last_minute:
                raise errors.RequestedMinuteOutOfBounds(self, False) from None
        return self.minutes[idx]

    def previous_minute(self, minute: Minute, _parse: bool = True) -> pd.Timestamp:
        """Return trading minute that immediately preceeds a given minute.

        Parameters
        ----------
        minute
            Minute for which to get previous trading minute. Minute can be
            a trading or a non-trading minute.

        Returns
        -------
        pd.Timestamp
            UTC timestamp of the previous minute.

        Raises
        ------
        errors.RequestedSessionOutOfBounds
            If `minute` is the first calendar minute.
        """
        if _parse:
            minute = parse_timestamp(minute, "minute", self)
        try:
            idx = previous_divider_idx(self.minutes_nanos, minute.value)
        except ValueError:
            # dt < first_minute handled via parsing
            if minute == self.first_minute:
                raise errors.RequestedMinuteOutOfBounds(self, True) from None
        return self.minutes[idx]

    def minute_to_session(
        self,
        minute: Minute,
        direction: Literal["next", "previous", "none"] = "next",
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
                    f"Received `minute` as '{minute}' although this is earlier than the"
                    f" calendar's first trading minute ({self.first_minute}). Consider"
                    " passing `direction` as 'next' to get first session."
                )

        if minute.value > self.minutes_nanos[-1]:
            # Resolve call here.
            if direction == "previous":
                return self.last_session
            else:
                raise ValueError(
                    f"Received `minute` as '{minute}' although this is later than the"
                    f" calendar's last trading minute ({self.last_minute}). Consider"
                    " passing `direction` as 'previous' to get last session."
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
            raise ValueError(f"Invalid direction parameter: {direction}")

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
            base_session = self.next_session(current_session, _parse=False)
        else:
            base_session = self.minute_to_session(minute, "next", _parse=False)
        count -= 1
        return self.session_offset(base_session, count, _parse=False)

    def minute_to_trading_minute(
        self,
        minute: Minute,
        direction: Literal["next", "previous", "none"] = "none",
        _parse: bool = True,
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
                raise errors.RequestedMinuteOutOfBounds(self, too_early=False) from None
        else:
            try:
                target_session = self.minute_to_past_session(minute, abs(count))
            except errors.RequestedSessionOutOfBounds:
                raise errors.RequestedMinuteOutOfBounds(self, too_early=True) from None

        base_session = self.minute_to_session(minute)
        day_offset = (minute.normalize() - base_session.tz_localize(UTC)).days

        minute = target_session.replace(hour=minute.hour, minute=minute.minute)
        minute = minute.tz_localize(UTC)
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
        self, start: Minute, end: Minute, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return all trading minutes between given minutes.

        Parameters
        ----------
        start
            Minute representing start of desired range. Can be a trading
            minute or non-trading minute.

        end
            Minute representing end of desired range. Can be a trading
            minute or non-trading minute.
        """
        slc = self._get_minutes_slice(start, end, _parse)
        return self.minutes[slc]

    def minutes_window(
        self, minute: TradingMinute, count: int, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return block of given size of consecutive trading minutes.

        Parameters
        ----------
        minute
            Minute representing the first (if `count` positive) or last
            (if `count` negative) minute of minutes window.

        count
            Number of mintues to include in window.
            Positive to return a block of minutes from `minute`
            Negative to return a block of minutes to `minute`.
        """
        if not count:
            raise ValueError("`count` cannot be 0.")
        if _parse:
            minute = parse_trading_minute(self, minute, "minute")

        start_idx = self._get_minute_idx(minute, _parse=False)
        end_idx = start_idx + count + (-1 if count > 0 else 1)

        if end_idx < 0:
            raise ValueError(
                f"Minutes window cannot begin before the calendar's first minute"
                f" ({self.first_minute}). `count` cannot be lower than"
                f" {count - end_idx} for `minute` '{minute}'."
            )
        elif end_idx >= len(self.minutes_nanos):
            raise ValueError(
                f"Minutes window cannot end after the calendar's last minute"
                f" ({self.last_minute}). `count` cannot be higher than"
                f" {count - (end_idx - len(self.minutes_nanos) + 1)} for `minute`"
                f" '{minute}'."
            )
        return self.minutes[min(start_idx, end_idx) : max(start_idx, end_idx) + 1]

    def minutes_distance(self, start: Minute, end: Minute, _parse: bool = True) -> int:
        """Return the number of minutes in a range.

        Parameters
        ----------
        start
            Start of minute range (range inclusive of `start`).

        end
            End of minute range (range inclusive of `end`).

        Returns
        -------
        int
            Number of minutes in minute range, If `start` is later than
            `end` then return will be negated.
        """
        if _parse:
            start = parse_timestamp(start, "start", self)
            end = parse_timestamp(end, "end", self)
        negate = end < start
        if negate:
            start, end = end, start
        slc = self._get_minutes_slice(start, end, _parse=False)
        return slc.start - slc.stop if negate else slc.stop - slc.start

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
        self, start: Date, end: Date, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return sessions within a given range.

        Parameters
        ----------
        start
            Start of session range (range inclusive of `start`).

        end
            End of session range (range inclusive of `end`).

        Returns
        -------
        pd.DatetimeIndex
            Sessions from `start` through `end`.
        """
        slc = self._get_sessions_slice(start, end, _parse)
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
        self, session: Session, count: int, _parse: bool = True
    ) -> pd.DatetimeIndex:
        """Return block of given size of consecutive sessions.

        Parameters
        ----------
        session
            Session representing the first (if `count` positive) or last
            (if `count` negative) session of session window.

        count
            Number of sessions to include in window.
            Positive to return window of sessions from `session`
            Negative to return window of sessions to `session`.
        """
        if not count:
            raise ValueError("`count` cannot be 0.")
        if _parse:
            session = parse_session(self, session, "session")
        start_idx = self._get_session_idx(session, _parse=False)
        end_idx = start_idx + count + (-1 if count > 0 else 1)
        if end_idx < 0:
            raise ValueError(
                f"Sessions window cannot begin before the first calendar session"
                f" ({self.first_session}). `count` cannot be lower than"
                f" {count - end_idx} for `session` '{session}'."
            )
        elif end_idx >= len(self.sessions):
            raise ValueError(
                f"Sessions window cannot end after the last calendar session"
                f" ({self.last_session}). `count` cannot be higher than"
                f" {count - (end_idx - len(self.sessions) + 1)} for"
                f" `session` '{session}'."
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
        dist = slc.start - slc.stop if negate else slc.stop - slc.start
        return int(dist)  # otherwise returned as `numpy.int64`

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
        start: Date | Minute,
        end: Date | Minute,
        period: pd.Timedelta | str,
        intervals: bool = True,
        closed: Literal["left", "right", "both", "neither"] = "left",
        force_close: bool = False,
        force_break_close: bool = False,
        force: bool | None = None,
        curtail_overlaps: bool = False,
        ignore_breaks: bool = False,
        align: pd.Timedelta | str = pd.Timedelta(1, "min"),
        align_pm: pd.Timedelta | bool = True,
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
            Timestamp representing start of index.

            If `start` is passed as a date then the first indice will be:
                if `start` is a session, then the first indice of that
                    session (i.e. the left side of the first indice will be
                    the session open).
                otherwise, the first indice of the nearest session
                    following `start`.

            If `start` is passed as a minute then the first indice will be:
                if `start` coincides with (the left side of*) an indice,
                    then that indice.
                otherwise the nearest indice to `start` (with a left side*)
                    that is later than `start`.
                * if `intervals` is True (default)

            `start` will be interpreted as a date if it is timezone-naive
            and does not have a time component (or any time component is
            00:00). Otherwise `start` will be interpreted as a time.

            If `period` is one day ("1d") then `start` must be passed as
            a date. The first indice will be either `start`, if `start` is
            a session, or otherwise the nearest session following `start`.

        end
            Timestamp representing end of index.

            If `end` is passed as a date then the last indice will be:
                if `end` is a session, then the last indice of that
                    session (i.e. either the right side of the final indice
                    will be the session close or the final indice will
                    contain the session close).
                otherwise, the last indice of the nearest session
                    preceeding `end`.

            If `end` is passed as a minute then the last indice will be:
                if `end` coincides with (the right side of*) an indice,
                    then that indice.
                otherwise the nearest indice to `end` (with a right side*)
                    that is earlier than `end`.
                * if `intervals` is True (default)

            `end` will be interpreted as a date if it is timezone-naive
            and does not have a time component (or any time component is
            00:00). Otherwise `start` will be interpreted as a time.

            If `period` is one day ("1d") then `end` must be passed as
            a date. The last indice will be either `end`, if `end` is
            a session, or otherwise the nearest session prceeding `end`.

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
            (ignored if `force` is passed.)
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
            (ignored if `force` is passed.)
            (ignored if `period` is '1d'.)
            (irrelevant if `intervals` is False and `closed` is "left" or
            "neither.)

            Defines behaviour if right side of last pre-break period falls
            after the start of the break.

            If True, defines right side of this period as break start.

            If False, defines right side of this period after the break
            start. In this case the represented period will include a
            non-trading period.

        force : optional
            (ignored if `period` is '1d'.)
            (irrelevant if `intervals` is False and `closed` is "left" or
            "neither.)

            Convenience option to set both `force_close` and
            `force_break_close`. If passed then values passsed to
            `force_close` and `force_break_close` will be ignored.

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

        ignore_breaks : default: False
            (ignored if `period` is '1d')
            (irrelevant if no session has a break)

            Defines whether trading index should respect session breaks.

            If False, treat sessions with breaks as comprising independent
            morning and afternoon subsessions.

            If True, treat all sessions as continuous, ignoring any
            breaks.

        parse : default: True
            Determines if `start` and `end` values are parsed. If these
            arguments are passed as tz-naive pd.Timestamp with no time
            component then can pass `parse` as False to save around
            500µs on the execution.

        align : default: pd.Timedelta(1, "min")
            Anchor the first indice of each session such that it aligns
            with the nearest occurrence of a specific fraction of an hour.

            Pass as a pd.Timedelta or a str that's acceptable as a single
            input to pd.Timedelta. Pass +ve values to shift indices
            forwards, -ve values to shift indices backwards.

            Valid values are (or equivalent):
                "2min", "3min", "4min", "5min", "6min", "10min", "12min", "15min", "20min",
                "30min", "-2min", "-4min", "-5min", "-6min", "-10min", "-12min", "-15min",
                "-20min", "-30min"

            For example, if `intervals` is True and `period` is '5T' then
            the first interval of a session with open time as 07:59 would
            be:
                07:59 - 08:04 if `align` is pd.Timedelta(1, "min")  (default)
                08:00 - 08:05 if `align` is '5T'
                07:55 - 08:00 if `align` is '-5T'

            Subsequent indices will be similarly shifted.

            Note: A session's indices will not be shifted if the session
            open already aligns with `align`. For example, if the open time
            were 08:00 then the first interval will always have a left side
            as 08:00 regardless of `align`.

        align_pm : default: True
            (ignored if `ignore_break` is True)
            (irrelevant if no session has a break)

            Anchor the first indice of each afternoon subsession such that
            it aligns with the nearest occurrence of a specific fraction of
            an hour.

                True: (default) Treat as `align`.

                False: Do not shift post-break indices.

                pd.Timedelta or str: Align post-break indices to the
                nearest occurence of this fraction of an hour. Valid values
                as for `align`.

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
        if not isinstance(period, pd.Timedelta):
            try:
                period = pd.Timedelta(period)
            except ValueError:
                msg = (
                    f"`period` receieved as '{period}' although takes type"
                    " 'pd.Timedelta' or a 'str' that is valid as a single input"
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
            start, end = self._parse_start_end_dates(start, end, parse)
            return self.sessions_in_range(start, end)

        if intervals and closed in ["both", "neither"]:
            raise ValueError(
                f"If `intervals` is True then `closed` cannot be '{closed}'."
            )

        def get_align(name: Literal["align", "align_pm"], value: Any) -> pd.Timedelta:
            """Convert value received for an align parameter to Timestamp.

            Raises `ValueError` if value is invalid or not of a valid type.

            Parameters
            ----------
            name
                Parameter name.

            value
                Value assigned to parameter.
            """
            try:
                value = pd.Timedelta(value)
            except ValueError:
                insert = " bool," if name == "align_pm" else ""
                msg = (
                    f"`{name}` receieved as '{value}' although takes type{insert}"
                    f" 'pd.Timedelta' or a 'str' that is valid as a single input"
                    " to 'pd.Timedelta'. Examples of valid input: pd.Timestamp('5T'),"
                    " '5min', '5T', pd.Timedelta('-5T'), '-5min', '-5T'."
                )
                raise ValueError(msg) from None

            ONE_HOUR = pd.Timedelta("1h")
            if value > ONE_HOUR or value < -ONE_HOUR or not value or (ONE_HOUR % value):
                raise ValueError(
                    f"`{name}` must be factor of 1H although received '{value}'."
                )

            if value % pd.Timedelta(1, "min"):
                raise ValueError(
                    f"`{name}` cannot include a fraction of a minute although received"
                    f" '{value}'."
                )
            return value

        align = get_align("align", align)

        if align_pm is False:
            align_pm = pd.Timedelta(1, "min")
        else:
            align_pm = align if align_pm is True else get_align("align_pm", align_pm)

        if force is not None:
            force_close = force_break_close = force

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
            ignore_breaks,
            align,
            align_pm,
        )

        if not intervals:
            return _trading_index.trading_index()
        else:
            return _trading_index.trading_index_intervals()

    # Internal methods called by constructor.

    def _special_dates(
        self,
        regular_dates: list[tuple[datetime.time, HolidayCalendar | int]],
        ad_hoc_dates: list[tuple[datetime.time, pd.DatetimeIndex]],
        start_date: pd.Timestamp,
        end_date: pd.Timestamp,
    ) -> pd.Series:
        """Evaluate times associated with special dates.

        Parameters
        ----------
        regular_dates
            Regular non-standard times and corresponding HolidayCalendars or Int day-of-week.

        ad_hoc_dates
            Adhoc non-standard times and corresponding sessions.

        start_date
            Start of the range over which to evaluate special dates. Must
            be timezone naive.

        end_date
            End of the range over which to evaluate special dates. Must be
            timezone naive.

        Returns
        -------
        special_dates: pd.Series
            Series mapping trading sessions with special times.

            Index is timezone naive.
            dtype is datetime64[ns, UTC].
        """
        # List of Series for regularly-scheduled times.
        regular = [
            scheduled_special_times(
                holiday_calendar,
                start_date,
                end_date,
                time_,
                self.tz,
            )
            for time_, holiday_calendar in regular_dates
        ]

        # List of Series for ad-hoc times.
        ad_hoc = []
        for time_, dti in ad_hoc_dates:
            dti = dti[(dti >= start_date) & (dti <= end_date)]
            srs = pd.Series(index=dti, data=days_at_time(dti, time_, self.tz, 0))
            ad_hoc.append(srs)

        merged = ad_hoc + regular
        if not merged:
            # Concat barfs if the input has length 0.
            return pd.Series(
                [], index=pd.DatetimeIndex([]), dtype="datetime64[ns, UTC]"
            )

        result = pd.concat(merged)
        # where there are multiple occurrences of the same date, keep only the first
        result = result[~result.index.duplicated(keep="first")]
        result = result.sort_index()
        # exclude any special date that coincides with a holiday
        adhoc_holidays = pd.DatetimeIndex(self.adhoc_holidays)
        result = result[~result.index.isin(adhoc_holidays)]
        regular_holidays = self.regular_holidays
        if regular_holidays is not None:
            reg_holidays = regular_holidays.holidays(start_date, end_date)
            if not reg_holidays.empty:
                result = result[~result.index.isin(reg_holidays)]
        return result

    def _calculate_special_opens(
        self, start: pd.Timestamp, end: pd.Timestamp
    ) -> pd.Series:
        return self._special_dates(
            self.special_opens,
            self.special_opens_adhoc,
            start,
            end,
        )

    def _calculate_special_closes(
        self, start: pd.Timestamp, end: pd.Timestamp
    ) -> pd.Series:
        return self._special_dates(
            self.special_closes,
            self.special_closes_adhoc,
            start,
            end,
        )


def _check_breaks_match(break_starts_nanos: np.ndarray, break_ends_nanos: np.ndarray):
    """Checks that break_starts_nanos and break_ends_nanos match."""
    nats_match = np.equal(NP_NAT == break_starts_nanos, NP_NAT == break_ends_nanos)
    if not nats_match.all():
        raise ValueError(
            f"""
            Mismatched market breaks
            Break starts:
            {break_starts_nanos[~nats_match]}
            Break ends:
            {break_ends_nanos[~nats_match]}
            """
        )


def scheduled_special_times(
    special_days: HolidayCalendar | int,
    start: pd.Timestamp,
    end: pd.Timestamp,
    time: datetime.time,
    tz: ZoneInfo,
) -> pd.Series:
    """Return map of dates to special times.

    Parameters
    ----------
    special_days
        Describes dates with a special time. Pass as either:
            HolidayCalendar : calendar with rules describing the dates on
            which special times apply

            int : integer describing a weekday with a regular special
            time (0 - Monday, ..., 6 - Sunday).

    start
        Date from which to evaluate mapping (inclusive of `start`).

    end
        Date to which to evaluate mapping (inclusive of `end`).

    time
        Special time for dates described by `special_days`.

    tz
        The timezone in which to interpret `time`.

    Returns
    -------
    pd.Series
        Series mapping dates to special times.

        Index is timezone naive.
        dtype is datetime64[ns, UTC].
    """
    if isinstance(special_days, int):
        day_str = "W-" + day_name[special_days].upper()[0:3]
        days = pd.date_range(start, end, freq=day_str)
    else:
        days = special_days.holidays(start, end)
    if not isinstance(days, pd.DatetimeIndex):
        # days will be pd.Index if empty
        days = pd.DatetimeIndex(days)
    return pd.Series(
        index=days,
        data=days_at_time(days, time, tz=tz, day_offset=0),
    )


def _overwrite_special_dates(
    session_labels: pd.DatetimeIndex,
    standard_times: pd.DatetimeIndex,
    special_times: pd.Series,
) -> None:
    """Overwrite standard times of a session bound with special times.

    `session_labels` required for alignment.
    """
    # Short circuit when nothing to apply.
    if special_times.empty:
        return

    len_m, len_oc = len(session_labels), len(standard_times)
    if len_m != len_oc:
        raise ValueError(
            "Found misaligned dates while building calendar.\nExpected"
            " session_labels to be the same length as open_or_closes but,\n"
            f"len(session_labels)={len_m}, len(open_or_closes)={len_oc}"
        )

    # Find the array indices corresponding to each special date.
    indexer = session_labels.get_indexer(special_times.index)

    # -1 indicates that no corresponding entry was found.  If any -1s are
    # present, then we have special dates that doesn't correspond to any
    # trading day.
    if -1 in indexer:
        bad_dates = list(special_times[indexer == -1])
        raise ValueError(f"Special dates {bad_dates} are not sessions.")

    # NOTE: This is a slightly dirty hack.  We're in-place overwriting the
    # internal data of an Index, which is conceptually immutable.  Since we're
    # maintaining sorting, this should be ok, but this is a good place to
    # sanity check if things start going haywire with calendar computations.
    standard_times.values[indexer] = special_times.values


def _remove_breaks_for_special_dates(
    session_labels: pd.DatetimeIndex,
    standard_break_times: pd.DatetimeIndex | None,
    special_times: pd.Series,
) -> None:
    """Remove standard break times for sessions with special times."

    Overwrites standard break times with NaT for sessions with speical
    times. Anticipated that `special_times` will be special times for
    'opens' or 'closes'.

    `session_labels` required for alignment.
    """
    # Short circuit when we have no breaks
    if standard_break_times is None:
        return

    # Short circuit when nothing to apply.
    if special_times.empty:
        return

    len_m, len_oc = len(session_labels), len(standard_break_times)
    if len_m != len_oc:
        raise ValueError(
            "Found misaligned dates while building calendar.\n"
            "Expected session_labels to be the same length as break_starts,\n"
            f"but len(session_labels)={len_m}, len(break_start_or_end)={len_oc}"
        )

    # Find the array indices corresponding to each special date.
    indexer = session_labels.get_indexer(special_times.index)

    # -1 indicates that no corresponding entry was found.  If any -1s are
    # present, then we have special dates that doesn't correspond to any
    # trading day.
    if -1 in indexer:
        bad_dates = list(special_times[indexer == -1])
        raise ValueError(f"Special dates {bad_dates} are not trading days.")

    # NOTE: This is a slightly dirty hack.  We're in-place overwriting the
    # internal data of an Index, which is conceptually immutable.  Since we're
    # maintaining sorting, this should be ok, but this is a good place to
    # sanity check if things start going haywire with calendar computations.
    standard_break_times.values[indexer] = NP_NAT
