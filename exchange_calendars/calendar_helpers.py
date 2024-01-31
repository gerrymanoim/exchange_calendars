from __future__ import annotations

import contextlib
import datetime
import typing
from typing import Literal
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from exchange_calendars import errors

if typing.TYPE_CHECKING:
    from exchange_calendars import ExchangeCalendar

UTC = ZoneInfo("UTC")

NANOSECONDS_PER_MINUTE = int(6e10)

NP_NAT = pd.NaT.value

# Use Date type where input does not need to represent an actual session
# and will be parsed by parse_date.
Date = typing.Union[pd.Timestamp, str, int, float, datetime.datetime]

# Use Session type where input should represent an actual session and will
# be parsed by parse_session.
Session = Date

# Use Minute type where input does not need to represent an actual trading
# minute and will be parsed by parse_timestamp.
Minute = typing.Union[pd.Timestamp, str, int, float, datetime.datetime]

# Use TradingMinute where input should represent a trading minute and will
# be parsed by parse_trading_minute.
TradingMinute = Minute


def next_divider_idx(dividers: np.ndarray, minute_val: int) -> int:
    divider_idx = np.searchsorted(dividers, minute_val, side="right")
    target = dividers[divider_idx]

    if minute_val == target:
        # if dt is exactly on the divider, go to the next value
        return divider_idx + 1
    else:
        return divider_idx


def previous_divider_idx(dividers: np.ndarray, minute_val: int) -> int:
    divider_idx = np.searchsorted(dividers, minute_val)

    if divider_idx == 0:
        raise ValueError("Cannot go earlier in calendar!")

    return divider_idx - 1


def compute_minutes(
    opens_in_ns: np.ndarray,
    break_starts_in_ns: np.ndarray,
    break_ends_in_ns: np.ndarray,
    closes_in_ns: np.ndarray,
    side: Literal["left", "right", "both", "neither"] = "both",
) -> np.ndarray:
    """Return array of trading minutes."""
    start_ext = 0 if side in ["left", "both"] else NANOSECONDS_PER_MINUTE
    # NOTE: Add an extra minute to ending boundaries (break_start and close)
    # so we include the last bar (arange doesn't include its stop).
    end_ext = NANOSECONDS_PER_MINUTE if side in ["right", "both"] else 0

    pieces = []
    for open_time, break_start_time, break_end_time, close_time in zip(
        opens_in_ns, break_starts_in_ns, break_ends_in_ns, closes_in_ns
    ):
        if break_start_time != NP_NAT:
            pieces.append(
                np.arange(
                    open_time + start_ext,
                    break_start_time + end_ext,
                    NANOSECONDS_PER_MINUTE,
                )
            )
            pieces.append(
                np.arange(
                    break_end_time + start_ext,
                    close_time + end_ext,
                    NANOSECONDS_PER_MINUTE,
                )
            )
        else:
            pieces.append(
                np.arange(
                    open_time + start_ext,
                    close_time + end_ext,
                    NANOSECONDS_PER_MINUTE,
                )
            )
    out = np.concatenate(pieces).view("datetime64[ns]")
    return out


def one_minute_earlier(arr: np.ndarray) -> np.ndarray:
    """Return an array of nanos one minute behind a given array."""
    arr = arr.copy()
    arr[arr != NP_NAT] -= NANOSECONDS_PER_MINUTE
    return arr


def one_minute_later(arr: np.ndarray) -> np.ndarray:
    """Return an array of nanos one minute ahead of a given array."""
    arr = arr.copy()
    arr[arr != NP_NAT] += NANOSECONDS_PER_MINUTE
    return arr


def is_date(ts: pd.Timestamp) -> bool:
    """Query if a timestamp represents a date (as opposed to a time).

    `ts` considered to represent a date if tz-naive and has time component
    as 00:00.

    Parameters
    ----------
    ts
        Timestamp to query.

    Returns
    -------
    bool
        Boolean indicating if `ts` represents a date.
    """
    return ts.tz is None and ts == ts.normalize()


def to_utc(ts: pd.Timestamp) -> pd.Timestamp:
    """Return a copy of a given timestamp with timezone set to UTC.

    If `ts` is tz-aware will convert `ts` to UTC.
    If `ts` is tz-naive will localize as UTC.

    Parameters
    ----------
    ts
        Timestamp to return a copy of with timezone set to UTC.
    """
    try:
        return ts.tz_convert(UTC)
    except TypeError:
        return ts.tz_localize(UTC)


def parse_timestamp(
    timestamp: Date | Minute,
    param_name: str = "minute",
    calendar: ExchangeCalendar | None = None,
    raise_oob: bool = True,
    side: Literal["left", "right", "both", "neither"] | None = None,
    utc: bool = True,
) -> pd.Timestamp:
    """Parse input intended to represent either a date or a minute.

    Parameters
    ----------
    timestamp
        Input to be parsed as either a Date or a Minute. Must be valid
        input to pd.Timestamp.

    param_name
        Name of a parameter that was to receive a Date or Minute.

    calendar
        ExchangeCalendar against which to evaluate out-of-bounds
        timestamps. Only requried if `raise_oob` True of if relying on
        `calendar` for `side`.

    raise_oob : default: True
        True to raise MinuteOutOfBounds if `timestamp` is earlier than the
        first trading minute or later than the last trading minute of
        `calendar`. Pass as False if `timestamp` represents a Date (as
        opposed to a Minute). If True then `calendar` must be passed.

    side : optional, {None, 'left', 'right', 'both', 'neither'}
        The side that determines which minutes at a session's bounds are
        considered as trading minutes (as `ExchangeCalendar` 'side'
        parameter). Only required if `calendar` is not passed or if do not
        wish to rely on `calendar.side`. Ignored if `timestamp` is accurate
        to minute resolution.

    utc : default: True
        True - convert / set timezone to UTC.
        False - leave any timezone unchanged. Note, if timezone of
        `timestamp` is UTC then will remain as UTC.

    Raises
    ------
    TypeError
        If `timestamp` is not of type [pd.Timestamp | str | int | float |
            datetime.datetime].

    ValueError
        If `timestamp` is not an acceptable single-argument input to
        pd.Timestamp.

    exchange_calendars.errors.MinuteOutOfBounds
        If `raise_oob` True and `timestamp` parses to a valid timestamp
        although timestamp is either before `calendar`'s first trading
        minute or after `calendar`'s last trading minute.
    """
    if isinstance(timestamp, pd.Timestamp):
        ts = timestamp
    else:
        try:
            ts = pd.Timestamp(timestamp)
        except Exception as e:
            msg = (
                f"Parameter `{param_name}` receieved as '{timestamp}' although"
                f" a Date or Minute must be passed as a pd.Timestamp or a"
                f" valid single-argument input to pd.Timestamp."
            )
            if isinstance(e, TypeError):
                raise TypeError(msg) from e
            else:
                raise ValueError(msg) from e

    if utc and ts.tz is not UTC:
        ts = ts.tz_localize(UTC) if ts.tz is None else ts.tz_convert(UTC)

    if ts.second or ts.microsecond or ts.nanosecond:
        if side is None and calendar is None:
            raise ValueError(
                "`side` or `calendar` must be passed if `timestamp` has a"
                " non-zero second (or more accurate) component. `timestamp`"
                f" parsed as '{ts}'."
            )
        side = side if side is not None else calendar.side
        if side == "left":
            ts = ts.floor("min")
        elif side == "right":
            ts = ts.ceil("min")
        else:
            raise ValueError(
                "`timestamp` cannot have a non-zero second (or more accurate)"
                f" component for `side` '{side}'. `timestamp` parsed as '{ts}'."
            )

    if raise_oob:
        if calendar is None:
            raise ValueError("`calendar` must be passed if `raise_oob` is True.")
        if calendar._minute_oob(ts):
            raise errors.MinuteOutOfBounds(calendar, ts, param_name)

    return ts


def parse_date_or_minute(
    ts: Date | Minute,
    param_name: str,
    calendar: ExchangeCalendar,
) -> tuple[pd.Timestamp, bool]:
    """Parse input that can be interpreted as a Date or a Minute.

    Parameters
    ----------
    ts
        Input that can be interpreted as a Date or a Minute. Must be valid
        input to pd.Timestamp.

    param_name
        Name of a parameter that was to receive a Date or a Minute.

    calendar
        ExchangeCalendar against which to evaluate out-of-bounds
        timestamps.

    Returns
    -------
    tuple[pd.Timestamp, bool]:
        [0] Parsed input to a pd.Timestamp.
        [1] Boolean indicating if input was interpreted as a Minute (True)
            or a Date (False).
    """
    ts = parse_timestamp(ts, param_name, calendar, raise_oob=False, utc=False)
    is_time = not is_date(ts)
    ts = to_utc(ts) if is_time else ts
    if is_time and calendar._minute_oob(ts):
        raise errors.MinuteOutOfBounds(calendar, ts, param_name)
    elif not is_time and calendar._date_oob(ts):
        raise errors.DateOutOfBounds(calendar, ts, param_name)
    return ts, is_time


def parse_trading_minute(
    calendar: ExchangeCalendar, minute: TradingMinute, param_name: str = "minute"
) -> pd.Timestamp:
    """Parse input intended to represent a trading minute.

    Parameters
    ----------
    calendar
       Calendar which `minute` must be a trading minute of.

    minute
        Input to be parsed as a trading minute. Must be valid input to
        pd.Timestamp and represent a trading minute of `calendar`.

    param_name
        Name of a parameter that was to receive a trading minute.

    Raises
    ------
    Errors as `parse_timestamp` and additionally:

    exchange_calendars.errors.NotTradingMinuteError
        If `minute` parses to a valid timestamp although timestamp does not
        represent a trading minute of `calendar`.
    """
    # let out-of-bounds be handled by more specific NotTradingMinuteError message.
    minute = parse_timestamp(minute, param_name, raise_oob=False, calendar=calendar)
    if calendar._minute_oob(minute) or not calendar.is_trading_minute(
        minute, _parse=False
    ):
        raise errors.NotTradingMinuteError(calendar, minute, param_name)
    return minute


def parse_date(
    date: Date,
    param_name: str = "date",
    calendar: ExchangeCalendar | None = None,
    raise_oob: bool = True,
) -> pd.Timestamp:
    """Parse input intended to represent a date.

     Parameters
     ----------
     date
         Input to be parsed as date. Must be valid input to pd.Timestamp
         and have a time component of 00:00.

     param_name
         Name of a parameter that was to receive a date.

    calendar
        ExchangeCalendar against which to evalute out-of-bounds dates.
        Only requried if `raise_oob` True.

    raise_oob : default: True
        True to raise DateOutOfBounds if `date` is earlier than the
        first session or later than the last session of `calendar`. NB if
        True (default) then `calendar` must be passed.

    Returns
     -------
     pd.Timestamp
         pd.Timestamp (timezone naive with time component of 00:00).

     Raises
     ------
     Errors as `parse_timestamp` and additionally:

     ValueError
         If `date` time component is not 00:00.
         If `date` is timezone aware.

    exchange_calendars.errors.DateOutOfBounds
        If `raise_oob` True and `date` parses to a valid timestamp although
        timestamp is before `calendar`'s first session or after
        `calendar`'s last session.
    """
    # side "left" to get it through 'second' handling. Has undesirable effect of
    # allowing `date` to be defined with a second (or more accurate) compoment
    # if it falls within the minute that follows midnight.
    ts = parse_timestamp(date, param_name, raise_oob=False, side="left", utc=False)

    if ts.tz is not None:
        raise ValueError(
            f"Parameter `{param_name}` received with timezone defined as '{ts.tz.key}'"
            f" although a Date must be timezone naive."
        )

    if not ts == ts.normalize():
        raise ValueError(
            f"Parameter `{param_name}` parsed as '{ts}' although a Date must have"
            f" a time component of 00:00."
        )

    if raise_oob:
        if calendar is None:
            raise ValueError("`calendar` must be passed if `raise_oob` is True.")
        if calendar._date_oob(ts):
            raise errors.DateOutOfBounds(calendar, ts, param_name)

    return ts


def parse_session(
    calendar: ExchangeCalendar, session: Session, param_name: str = "session"
) -> pd.Timestamp:
    """Parse input intended to represent a session label.

    Parameters
    ----------
    calendar
        Calendar against which to evaluate `session`.

    session
        Input to be parsed as session. Must be valid input to pd.Timestamp,
        have a time component of 00:00 and represent a session of
        `calendar`.

    param_name
        Name of a parameter that was to receive a session.

    Returns
    -------
    pd.Timestamp
        pd.Timestamp (timezone naive and with time component of 00:00) that
        represents a real session of `calendar`.

    Raises
    ------
    Errors as `parse_date` and additionally:

    exchange_calendars.errors.NotSessionError
        If `session` parses to a valid date although date does not
        represent a session of `calendar`.
    """
    # let out-of-bounds be handled by more specific NotSessionError message.
    ts = parse_date(session, param_name, raise_oob=False)
    if calendar._date_oob(ts) or not calendar.is_session(ts, _parse=False):
        raise errors.NotSessionError(calendar, ts, param_name)
    return ts


class _TradingIndex:
    """Create a trading index.

    Credit to @Stryder-Git at pandas_market_calendars for showing the way
    with a vectorised solution to creating trading indices.

    Parameters
    ----------
    All parameters as ExchangeCalendar.trading_index except:

    align_pm
        As 'align' parameter of `ExchangeCalendar.trading_index` although
        applied exclusively to the post-break subsessions.
    """

    def __init__(
        self,
        calendar: ExchangeCalendar,
        start_: Date | Minute,
        end_: Date | Minute,
        period: pd.Timedelta,
        closed: Literal["left", "right", "both", "neither"],
        force_close: bool,
        force_break_close: bool,
        curtail_overlaps: bool,
        ignore_breaks: bool,
        align: pd.Timedelta,
        align_pm: pd.Timedelta,
    ):
        self.closed = closed
        self.force_break_close = False if ignore_breaks else force_break_close
        self.force_close = force_close
        self.curtail_overlaps = curtail_overlaps

        # parse `start_` and `end_`
        start_, self.start_as_time = parse_date_or_minute(start_, "start", calendar)
        end_, self.end_as_time = parse_date_or_minute(end_, "end", calendar)
        self.start_, self.end_ = start_, end_
        # define start and end as sessions
        start = (
            calendar.minute_to_session(start_, "next") if self.start_as_time else start_
        )
        end = calendar.minute_to_session(end_, "previous") if self.end_as_time else end_

        # get session bound values over requested range
        slice_start = calendar.sessions.searchsorted(start)
        slice_end = calendar.sessions.searchsorted(end, side="right")
        slce = slice(slice_start, slice_end)

        self.interval_nanos = period.value
        self.dtype = np.int64 if self.interval_nanos < 3000000000 else np.int32

        self.closes = calendar.closes_nanos[slce]

        def align_opens(opens: pd.Series, align: pd.Timedelta) -> np.ndarray:
            """Return opens as nanos shifted for alignment."""
            opens = opens.dt.ceil(align)
            return opens.values.astype(np.int64)

        if align != pd.Timedelta(1, "min"):
            self.opens = align_opens(calendar.opens[slce], align)
        else:
            self.opens = calendar.opens_nanos[slce]

        if ignore_breaks:
            self.has_break = False
        else:
            self.break_starts = calendar.break_starts_nanos[slce]

            if align_pm != pd.Timedelta(1, "min"):
                self.break_ends = align_opens(calendar.break_ends[slce], align_pm)
            else:
                self.break_ends = calendar.break_ends_nanos[slce]

            self.mask = self.break_starts != pd.NaT.value  # break mask
            self.has_break = self.mask.any()

        self.defaults = {
            "closed": self.closed,
            "force_close": self.force_close,
            "force_break_close": self.force_break_close,
        }

    @property
    def closed_right(self) -> bool:
        return self.closed in ["right", "both"]

    @property
    def closed_left(self) -> bool:
        return self.closed in ["left", "both"]

    def verify_non_overlapping(self):
        """Raise IndicesOverlapError if indices will overlap."""
        if not self.closed_right:
            return

        def _check(
            start_nanos: np.ndarray, end_nanos: np.ndarray, next_start_nanos: np.ndarray
        ):
            """Raise IndicesOverlap Error if indices would overlap.

            `next_start_nanos` describe start of (sub)session that follows and could
            overlap with (sub)session described by `start_nanos` and `end_nanos`.

            All inputs should be of same length.
            """
            num_intervals = np.ceil((end_nanos - start_nanos) / self.interval_nanos)
            right = start_nanos + num_intervals * self.interval_nanos
            if self.closed == "right" and (right > next_start_nanos).any():
                raise errors.IndicesOverlapError()
            if self.closed == "both" and (right >= next_start_nanos).any():
                raise errors.IndicesOverlapError()

        if self.has_break:
            if not self.force_break_close:
                _check(
                    self.opens[self.mask],
                    self.break_starts[self.mask],
                    self.break_ends[self.mask],
                )

        if not self.force_close:
            opens, closes, next_opens = (
                self.opens[:-1],
                self.closes[:-1],
                self.opens[1:],
            )
            _check(opens, closes, next_opens)
            if self.has_break:
                mask = self.mask[:-1]
                _check(self.break_ends[:-1][mask], closes[mask], next_opens[mask])

    def _create_index_for_sessions(
        self,
        start_nanos: np.ndarray,
        end_nanos: np.ndarray,
        force_close: bool,
    ) -> np.ndarray:
        """Create nano array of indices for sessions of given bounds."""
        if start_nanos.size == 0:
            return start_nanos

        # evaluate number of indices for each session
        num_intervals = (end_nanos - start_nanos) / self.interval_nanos
        num_indices = np.ceil(num_intervals).astype("int")

        if force_close:
            if self.closed_right:
                on_freq = (num_intervals == num_indices).all()
                if not on_freq:
                    num_indices -= 1  # add the close later
            else:
                on_freq = True

        if self.closed == "both":
            num_indices += 1
        elif self.closed == "neither":
            num_indices -= 1

        # by session, evaluate a range of int such that indices of a session
        # could be evaluted from [ session_open + (freq * i) for i in range ]
        start = 0 if self.closed_left else 1
        func = np.vectorize(lambda stop: np.arange(start, stop), otypes=[np.ndarray])
        stop = num_indices if self.closed_left else num_indices + 1
        ranges = np.concatenate(func(stop), axis=0, dtype=self.dtype)

        # evaluate index as nano array
        base = start_nanos.repeat(num_indices)
        index = base + ranges * self.interval_nanos

        if force_close and not on_freq:
            index = np.concatenate((index, end_nanos))
            index.sort()

        return index

    def _trading_index(self) -> np.ndarray:
        """Create trading index as nano array.

        Notes
        -----
        If `self.has_break` then index is returned UNSORTED. Why?
        Returning unsorted allows `trading_index_intervals` to create
        indices for the left and right sides and then arrange the right
        in the same order as the sorted left. Although as required, there
        are rare circumstances in which the resulting right side will not
        be in ascending order (it will later be curtailed or an error
        raised). This can happen when, for example, a calendar has breaks,
        `force_break_close` is False although `force_close` is True and the
        period is sufficiently long that the right side of the last
        interval of a morning subsession exceeds the day close, i.e.
        exceeds the right side of the subsequent interval. In these cases,
        sorting the right index by value would result in the indices
        becoming unsynced with the corresponding left indices.
        """
        if self.has_break:
            # sessions with breaks
            index_am = self._create_index_for_sessions(
                self.opens[self.mask],
                self.break_starts[self.mask],
                self.force_break_close,
            )

            index_pm = self._create_index_for_sessions(
                self.break_ends[self.mask], self.closes[self.mask], self.force_close
            )

            # sessions without a break
            index_day = self._create_index_for_sessions(
                self.opens[~self.mask], self.closes[~self.mask], self.force_close
            )

            # put it all together
            index = np.concatenate((index_am, index_pm, index_day))

        else:
            index = self._create_index_for_sessions(
                self.opens, self.closes, self.force_close
            )

        return index

    def curtail_for_times(
        self, index: pd.DatetimeIndex | pd.IntervalIndex
    ) -> pd.DatetimeIndex | pd.IntervalIndex:
        """Curtail start and end of trading index.

        Curtails any unwanted rows from the start and end of `index` if
        class received `start_` and/or `end_` as times.
        """
        intervals = isinstance(index, pd.IntervalIndex)
        bv: np.ndarray | None = None
        if self.start_as_time:
            bv = index.left >= self.start_ if intervals else index >= self.start_
        if self.end_as_time:
            bv_end = index.right <= self.end_ if intervals else index <= self.end_
            bv = bv & bv_end if bv is not None else bv_end
        return index if bv is None else index[bv]

    def trading_index(self) -> pd.DatetimeIndex:
        """Create trading index as a DatetimeIndex."""
        self.verify_non_overlapping()
        index = self._trading_index()
        if self.has_break:
            index.sort()
        index = pd.DatetimeIndex(index, tz=UTC)
        return self.curtail_for_times(index)

    @contextlib.contextmanager
    def _override_defaults(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        yield
        for k, v in self.defaults.items():
            setattr(self, k, v)

    def trading_index_intervals(self) -> pd.IntervalIndex:
        """Create trading index as a pd.IntervalIndex."""
        with self._override_defaults(
            closed="left", force_close=False, force_break_close=False
        ):
            left = self._trading_index()

        if not (self.force_close or self.force_break_close):
            if self.has_break:
                left.sort()
            right = left + self.interval_nanos
        else:
            with self._override_defaults(closed="right"):
                right = self._trading_index()
            if self.has_break:
                # See _trading_index.__doc__ for note on what's going on here.
                indices = left.argsort()
                left.sort()
                right = right[indices]

        overlaps_next = right[:-1] > left[1:]
        if overlaps_next.any():
            if self.curtail_overlaps:
                right[:-1][overlaps_next] = left[1:][overlaps_next]
            else:
                raise errors.IntervalsOverlapError()

        left = pd.DatetimeIndex(left, tz=UTC)
        right = pd.DatetimeIndex(right, tz=UTC)
        index = pd.IntervalIndex.from_arrays(left, right, self.closed)
        return self.curtail_for_times(index)
