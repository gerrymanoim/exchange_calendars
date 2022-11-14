"""Tests for calendar_helpers module."""

from __future__ import annotations

import datetime
from datetime import time
import itertools
import operator
import re
from collections import abc

import numpy as np
import pandas as pd
import pytest
import pytz
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from pandas.testing import assert_index_equal

from exchange_calendars import ExchangeCalendar
from exchange_calendars import calendar_helpers as m
from exchange_calendars import calendar_utils, errors
from exchange_calendars.calendar_utils import XTAEExchangeCalendar

from .test_exchange_calendar import Answers

# TODO tests for next_divider_idx, previous_divider_idx, compute_minutes (#15)


@pytest.fixture(scope="class")
def one_min() -> abc.Iterator[pd.Timedelta]:
    yield pd.Timedelta(1, "T")


def test_is_date(one_min):
    f = m.is_date
    T = pd.Timestamp

    assert f(T("2021-11-02"))
    assert f(T("2021-11-02 00:00"))
    assert f(T("2021-11-02 00:00:00.0000000"))
    assert not f(T("2021-11-02 00:00:00.000001"))
    assert not f(T("2021-11-01 23:59:00.999999"))
    assert not f(T("2021-11-02 12:00"))

    minutes = [
        T("2021-11-02", tz=pytz.UTC),
        T("2021-11-02", tz="US/Eastern"),
        T("2021-11-02", tz=pytz.UTC).tz_convert("US/Eastern"),
    ]
    for minute in minutes:
        assert not f(minute)
        assert not f(minute + one_min)


def test_is_utc():
    f = m.to_utc
    T = pd.Timestamp

    expected = T("2021-11-02", tz="UTC")
    assert f(T("2021-11-02", tz="UTC")) == expected
    assert f(T("2021-11-02")) == expected

    expected = T("2021-11-02 13:33", tz="UTC")
    assert f(T("2021-11-02 13:33")) == expected
    assert f(T("2021-11-02 09:33", tz="US/Eastern")) == expected


@pytest.fixture
def one_day() -> abc.Iterator[pd.DateOffset]:
    yield pd.DateOffset(days=1)


# all fixtures with respect to XHKG
@pytest.fixture
def calendar() -> abc.Iterator[calendar_utils.XHKGExchangeCalendar]:
    yield calendar_utils.XHKGExchangeCalendar()


@pytest.fixture
def param_name() -> abc.Iterator[str]:
    yield "parameter's_name"


@pytest.fixture(params=[True, False])
def utc(request) -> abc.Iterator[str]:
    yield request.param


@pytest.fixture(params=["2021-13-13", ("2021-06-06",), "not a timestamp"])
def malformed(request) -> abc.Iterator[str]:
    yield request.param


@pytest.fixture
def minute() -> abc.Iterator[str]:
    yield "2021-06-02 23:00"


@pytest.fixture(
    params=[
        "2021-06-02 23:00",
        pd.Timestamp("2021-06-02 23:00"),
        pd.Timestamp("2021-06-02 23:00", tz="UTC"),
    ]
)
def minute_mult(request) -> abc.Iterator[str | pd.Timestamp]:
    yield request.param


@pytest.fixture
def date(calendar) -> abc.Iterator[str]:
    """Date that does not represent a session of `calendar`."""
    date_ = "2021-06-05"
    assert pd.Timestamp(date_) not in calendar.schedule.index
    yield date_


@pytest.fixture(params=["2021-06-05", pd.Timestamp("2021-06-05")])
def date_mult(request, calendar) -> abc.Iterator[str | pd.Timestamp]:
    """Date that does not represent a session of `calendar`."""
    date = request.param
    ts = pd.Timestamp(date)
    assert ts not in calendar.schedule.index
    yield date


@pytest.fixture
def second() -> abc.Iterator[str]:
    yield "2021-06-02 23:01:30"


@pytest.fixture(params=["left", "right", "both", "neither"])
def sides(request) -> abc.Iterator[str]:
    yield request.param


@pytest.fixture
def session() -> abc.Iterator[str]:
    yield "2021-06-02"


@pytest.fixture
def trading_minute() -> abc.Iterator[str]:
    yield "2021-06-02 05:30"


@pytest.fixture
def minute_too_early(calendar, one_min) -> abc.Iterator[pd.Timestamp]:
    yield calendar.first_minute - one_min


@pytest.fixture
def minute_too_late(calendar, one_min) -> abc.Iterator[pd.Timestamp]:
    yield calendar.last_minute + one_min


@pytest.fixture
def date_too_early(calendar, one_day) -> abc.Iterator[pd.Timestamp]:
    yield calendar.first_session - one_day


@pytest.fixture
def date_too_late(calendar, one_day) -> abc.Iterator[pd.Timestamp]:
    yield calendar.last_session + one_day


def test_parse_timestamp_with_date(date_mult, param_name, calendar, utc):
    date = date_mult
    date_is_utc_ts = isinstance(date, pd.Timestamp) and date.tz is not None
    dt = m.parse_timestamp(date, param_name, calendar, utc=utc)
    if not utc and not date_is_utc_ts:
        assert dt == pd.Timestamp("2021-06-05")
    else:
        assert dt == pd.Timestamp("2021-06-05", tz="UTC")
    assert dt == dt.floor("T")


def test_parse_timestamp_with_minute(minute_mult, param_name, calendar, utc):
    minute = minute_mult
    minute_is_utc_ts = isinstance(minute, pd.Timestamp) and minute.tz is not None
    dt = m.parse_timestamp(minute, param_name, calendar, utc=utc)
    if not utc and not minute_is_utc_ts:
        assert dt == pd.Timestamp("2021-06-02 23:00")
    else:
        assert dt == pd.Timestamp("2021-06-02 23:00", tz="UTC")
    assert dt == dt.floor("T")


def test_parse_timestamp_with_second(second, sides, param_name):
    side = sides
    if side not in ["right", "left"]:
        error_msg = re.escape(
            "`timestamp` cannot have a non-zero second (or more accurate)"
            f" component for `side` '{side}'."
        )
        with pytest.raises(ValueError, match=error_msg):
            m.parse_timestamp(second, param_name, raise_oob=False, side=side)
    else:
        parsed = m.parse_timestamp(second, param_name, raise_oob=False, side=side)
        if side == "left":
            assert parsed == pd.Timestamp("2021-06-02 23:01", tz="UTC")
        else:
            assert parsed == pd.Timestamp("2021-06-02 23:02", tz="UTC")


def test_parse_timestamp_error_malformed(malformed, param_name, calendar):
    expected_error = TypeError if isinstance(malformed, tuple) else ValueError
    error_msg = re.escape(
        f"Parameter `{param_name}` receieved as '{malformed}' although a Date or"
        f" Minute must be passed as a pd.Timestamp or a valid single-argument"
        f" input to pd.Timestamp."
    )
    with pytest.raises(expected_error, match=error_msg):
        m.parse_timestamp(malformed, param_name, calendar)


def test_parse_timestamp_error_oob(
    calendar, param_name, minute_too_early, minute_too_late
):
    # by default raises error if oob
    error_msg = re.escape(
        f"Parameter `{param_name}` receieved as '{minute_too_early}' although"
        f" cannot be earlier than the first trading minute of calendar"
    )
    with pytest.raises(errors.MinuteOutOfBounds, match=error_msg):
        m.parse_timestamp(minute_too_early, param_name, calendar)

    # verify parses if oob and raise_oob False
    rtrn = m.parse_timestamp(minute_too_early, param_name, raise_oob=False, side="left")
    assert rtrn == minute_too_early

    # by default raises error if oob
    error_msg = re.escape(
        f"Parameter `{param_name}` receieved as '{minute_too_late}' although"
        f" cannot be later than the last trading minute of calendar"
    )
    with pytest.raises(errors.MinuteOutOfBounds, match=error_msg):
        m.parse_timestamp(minute_too_late, param_name, calendar)

    # verify parses if oob and raise_oob False
    rtrn = m.parse_timestamp(minute_too_late, param_name, raise_oob=False, side="left")
    assert rtrn == minute_too_late


def test_parse_date_or_minute_for_minute(
    calendar, param_name, minute, minute_mult, date
):
    """Tests `parse_date_or_minute` for input that represents a Minute."""

    def f(ts: pd.Timestamp) -> tuple[pd.Timestamp, bool]:
        return m.parse_date_or_minute(ts, param_name, calendar)

    assert f(minute_mult) == (pd.Timestamp(minute, tz=pytz.UTC), True)
    # verify that midnight with tz as UTC intepreted as minute, not date.
    assert f(pd.Timestamp(date, tz=pytz.UTC)) == (pd.Timestamp(date, tz=pytz.UTC), True)


def test_parse_date_or_minute_for_date(calendar, param_name, date, date_mult):
    """Tests `parse_date_or_minute` for input that represents a Minute."""
    f = m.parse_date_or_minute
    assert f(date_mult, param_name, calendar) == (pd.Timestamp(date), False)


def test_parse_date_or_minute_oob(
    calendar,
    param_name,
    date_too_early,
    date_too_late,
    minute_too_early,
    minute_too_late,
):
    """Tests `parse_date_or_minute` for out-of-bounds input.

    Tests as if an extension of parse_timestamp, i.e. only tests added
    functionality.
    """

    def f(ts: pd.Timestamp) -> tuple[pd.Timestamp, bool]:
        return m.parse_date_or_minute(ts, param_name, calendar)

    # Verify raises errors for out-of-bounds ts
    first_min = calendar.first_minute
    last_min = calendar.last_minute
    first_date = calendar.first_session
    last_date = calendar.last_session
    # verify returns at calendar's minute bounds
    assert f(first_min) == (first_min, True)
    assert f(last_min) == (last_min, True)
    # verify raises error other side of calendar's minute bounds
    with pytest.raises(errors.MinuteOutOfBounds):
        f(minute_too_early)
    with pytest.raises(errors.MinuteOutOfBounds):
        f(minute_too_late)
    # verify returns at calendar's session bounds
    assert f(first_date) == (first_date, False)
    assert f(last_date) == (last_date, False)
    # verify raises error other side of calendar's session bounds
    with pytest.raises(errors.DateOutOfBounds):
        f(date_too_early)
    with pytest.raises(errors.DateOutOfBounds):
        f(date_too_late)


def test_parse_date(date_mult, param_name):
    date = date_mult
    dt = m.parse_date(date, param_name, raise_oob=False)
    assert dt == pd.Timestamp("2021-06-05")


def test_parse_date_errors(calendar, param_name, date_too_early, date_too_late):
    dt = pd.Timestamp("2021-06-02", tz="US/Central")
    with pytest.raises(ValueError, match="a Date must be timezone naive"):
        m.parse_date(dt, param_name, raise_oob=False)

    dt = pd.Timestamp("2021-06-02 13:33")
    with pytest.raises(ValueError, match="a Date must have a time component of 00:00."):
        m.parse_date(dt, param_name, raise_oob=False)

    # by default raises error if oob
    error_msg = (
        f"Parameter `{param_name}` receieved as '{date_too_early}' although"
        f" cannot be earlier than the first session of calendar"
    )
    with pytest.raises(errors.DateOutOfBounds, match=re.escape(error_msg)):
        m.parse_date(date_too_early, param_name, calendar)

    # verify parses if oob and raise_oob False
    assert m.parse_date(date_too_early, param_name, raise_oob=False) == date_too_early

    # by default parses oob
    error_msg = (
        f"Parameter `{param_name}` receieved as '{date_too_late}' although"
        f" cannot be later than the last session of calendar"
    )
    with pytest.raises(errors.DateOutOfBounds, match=re.escape(error_msg)):
        m.parse_date(date_too_late, param_name, calendar)

    # verify parses if oob and raise_oob False
    assert m.parse_date(date_too_late, param_name, raise_oob=False) == date_too_late


def test_parse_session(
    calendar, session, date, date_too_early, date_too_late, param_name
):
    ts = m.parse_session(calendar, session, param_name)
    assert ts == pd.Timestamp(session)

    with pytest.raises(errors.NotSessionError, match="not a session of calendar"):
        m.parse_session(calendar, date, param_name)

    with pytest.raises(
        errors.NotSessionError, match="is earlier than the first session of calendar"
    ):
        m.parse_session(calendar, date_too_early, param_name)

    with pytest.raises(
        errors.NotSessionError, match="is later than the last session of calendar"
    ):
        m.parse_session(calendar, date_too_late, param_name)


def test_parse_trading_minute(
    calendar, trading_minute, minute, minute_too_early, minute_too_late, param_name
):
    ts = m.parse_trading_minute(calendar, trading_minute, param_name)
    assert ts == pd.Timestamp(trading_minute, tz="UTC")

    with pytest.raises(
        errors.NotTradingMinuteError, match="not a trading minute of calendar"
    ):
        m.parse_trading_minute(calendar, minute, param_name)

    with pytest.raises(
        errors.NotTradingMinuteError,
        match="is earlier than the first trading minute of calendar",
    ):
        m.parse_trading_minute(calendar, minute_too_early, param_name)

    with pytest.raises(
        errors.NotTradingMinuteError,
        match="is later than the last trading minute of calendar",
    ):
        m.parse_trading_minute(calendar, minute_too_late, param_name)


def st_align() -> st.SearchStrategy[pd.Timedelta]:
    """SearchStrategy for a valid alignment."""
    sample_pos = [pd.Timedelta(i, "T") for i in range(1, 31) if not 60 % i]
    sample_neg = [-td for td in sample_pos]
    return st.sampled_from(sample_pos + sample_neg)


class TestTradingIndex:
    """Tests for _TradingIndex.

    Subjects selected calendars (each of a unique behaviour) to fuzz tests
    verifying expected behaviour / no unexpected errors. These tests cover
    all date ranges, periods (from 1 minute to 1 day) and options.

    Also includes:
        - concrete tests to verify overlap handling.
        - concrete test to verify passing start and/or end as a time.
        - parsing tests for ExchangeCalendar.trading_index.

    NOTE: `_TradingIndex` is also tested via
    `ExchangeCalendarTestBase.test_trading_index` which tests a multitude
    of concrete cases (options as default values).
    """

    CALENDAR_NAMES = ["XLON", "XHKG", "XTAE", "CMES", "24/7"]
    """Selection of calendars with a particular behaviour:
    "XLON" - calendars without breaks.
    "XHKG" - calendars with breaks.
    "XTAE" - opens at 9:59am, useful for testing `align`
    "CMES" - 24 hour calendar, not 7 days a week.
    "24/7" - 24 hour calendar.
    """

    # Fixtures

    @pytest.fixture(scope="class")
    def answers(self) -> abc.Iterator[dict[str, Answers]]:
        """Dict of answers for tested calendars, key as name, value as Answers."""
        d = {}
        for name in self.CALENDAR_NAMES:
            d[name] = Answers(name, side="left")
        return d

    @pytest.fixture(scope="class")
    def calendars(self, answers) -> abc.Iterator[dict[str, ExchangeCalendar]]:
        """Dict of tested calendars, key as name, value as calendar."""
        d = {}
        for name, ans in answers.items():
            cls = calendar_utils._default_calendar_factories[name]
            d[name] = cls(start=ans.first_session, end=ans.last_session)
        return d

    @pytest.fixture(scope="class", params=CALENDAR_NAMES)
    def calendars_with_answers(
        self, request, calendars, answers
    ) -> abc.Iterator[tuple[ExchangeCalendar, Answers]]:
        """Parameterized fixture."""
        yield (calendars[request.param], answers[request.param])

    # Helper strategies

    @staticmethod
    @st.composite
    def _st_times_different(
        draw, ans
    ) -> st.SearchStrategy[tuple[pd.Timestamp, pd.Timestamp]]:
        """SearchStrategy for two consecutive sessions with different times."""
        session = draw(st.sampled_from(ans.sessions_next_time_different.to_list()))
        next_session = ans.get_next_session(session)
        return (session, next_session)

    @staticmethod
    @st.composite
    def _st_start_end(
        draw, ans
    ) -> st.SearchStrategy[tuple[pd.Timestamp, pd.Timestamp]]:
        """SearchStrategy for start and end dates in calendar range and
        a calendar specific maximum distance."""
        first = ans.first_session
        last = ans.last_session

        one_day = pd.Timedelta(1, "D")
        # reasonable to quicken test by limiting 24/7 as rules for 24/7 are unchanging.
        distance = (
            pd.DateOffset(weeks=2) if ans.name == "24/7" else pd.DateOffset(years=1)
        )

        end = draw(st.datetimes(min(first + distance, last), last))
        end = pd.Timestamp(end).floor("D")
        start = draw(st.datetimes(max(end - distance, first), end - one_day))
        start = pd.Timestamp(start).floor("D")
        start, end = start, end
        assume(not ans.answers[start:end].empty)
        return start, end

    def st_start_end(
        self, ans: Answers
    ) -> st.SearchStrategy[tuple[pd.Timestamp, pd.Timestamp]]:
        """SearchStrategy for trading index start and end dates."""
        st_startend = self._st_start_end(ans)
        if not ans.sessions_next_time_different.empty:
            st_times_differ = self._st_times_different(ans)
            st_startend = st.one_of(st_startend, st_times_differ)
        return st_startend

    @staticmethod
    @st.composite
    def st_periods(
        draw,
        minimum: pd.Timedelta = pd.Timedelta(1, "T"),
        maximum: pd.Timedelta = pd.Timedelta(1, "D") - pd.Timedelta(1, "T"),
    ) -> st.SearchStrategy[pd.Timedelta]:
        """SearchStrategy for a period between a `minimum` and `maximum`."""
        period = draw(st.integers(minimum.seconds // 60, maximum.seconds // 60))
        return pd.Timedelta(period, "T")

    # Helper methods

    @staticmethod
    def could_overlap(ans: Answers, slc: slice, has_break) -> bool:
        """Query if there's at least one period at which intervals overlap.

        Can right side of last interval of any session/subsession of a
        slice of Answers fall later than the left side of the first
        interval of the next session/subsession?
        """
        can_overlap = False
        if has_break:
            duration = ans.break_starts[slc] - ans.opens[slc]
            gap = ans.break_ends[slc] - ans.break_starts[slc]
            can_overlap = (gap < duration).any()
        if not can_overlap:
            duration = ans.closes[slc] - ans.opens[slc]
            gap = ans.opens.shift(-1)[slc] - ans.closes[slc]
            can_overlap = (gap < duration).any()
        return can_overlap

    @staticmethod
    def evaluate_overrun(
        starts: pd.Series,
        ends: pd.Series,
        period: pd.Timedelta,
    ) -> pd.Series:
        """Evaluate extent that right side of last interval exceeds end.

        For session/subsessions with `starts` and `ends` evaluate the
        distance beyond the `ends` that the right of the last interval will
        fall (where interval length is `period`).
        """
        duration = ends - starts
        shortfall = duration % period
        on_end_mask = shortfall == pd.Timedelta(0)
        overrun = period - shortfall
        overrun[on_end_mask] = pd.Timedelta(0)
        return overrun

    @staticmethod
    def sessions_bounds(
        ans: Answers,
        slc: slice,
        period: pd.Timedelta,
        closed: str | None,
        force_break_close: bool,
        force_close: bool,
        align: pd.Timedelta,
        align_pm: pd.Timedelta,
        curtail: bool = False,
    ) -> tuple[pd.Series, pd.Series]:
        """First and last trading indice of each session/subsession.

        `closed` should be passed as None if evaluating bounds for an
        intervals index.
        """
        closed_left = closed in [None, "left", "both"]
        closed_right = closed in [None, "right", "both"]

        opens = ans.opens[slc]
        closes = ans.closes[slc]
        has_break = ans.break_starts[slc].notna().any()

        def bounds(start: pd.Series, end: pd.Series, force: bool, align: pd.Timedelta):
            """Evaluate bounds of trading index by session/subsession.

            Parameters
            ----------
            start
                Index: pd.DatetimeIndex
                    session. Must be the same as `end.index`.
                Value: pd.DatetimeIndex
                    Start time of session or a subsession of session (where
                    session is index value).

            end
                As for `start` albeit indicating end times.
            """
            start = start.dt.ceil(align) if align else start
            lower_bounds = start if closed_left else start + period
            if force and closed_right:
                if (lower_bounds > end).any():
                    # period longer than session/subsession duration
                    lower_bounds[lower_bounds > end] = end
                return lower_bounds, end

            duration = end - start
            func = np.ceil if closed_right else np.floor
            num_periods = func(duration / period)
            if not closed_right and closed is not None:
                num_periods[duration % period == pd.Timedelta(0)] -= 1

            upper_bounds = start + (num_periods * period)

            if closed == "neither" and (num_periods == 0).any:  # edge case
                # lose bounds where session/subsession has no indice.
                upper_bounds = upper_bounds[num_periods != 0]
                lower_bounds = lower_bounds[upper_bounds.index]

            return lower_bounds, upper_bounds

        if has_break:
            break_starts = ans.break_starts[slc]
            break_ends = ans.break_ends[slc]
            mask = break_starts.notna()  # which sessions have a break

            # am sessions bounds
            am_lower, am_upper = bounds(
                opens[mask], break_starts[mask], force_break_close, align
            )

            # pm sessions bounds
            pm_lower, pm_upper = bounds(
                break_ends[mask], closes[mask], force_close, align_pm
            )

            # sessions without breaks
            if (~mask).any():
                day_lower, day_upper = bounds(
                    opens[~mask], closes[~mask], force_close, align
                )
            else:
                day_upper = day_lower = pd.Series([], dtype="datetime64[ns, UTC]")

            lower_bounds = pd.concat((am_lower, pm_lower, day_lower))
            upper_bounds = pd.concat((am_upper, pm_upper, day_upper))

        else:
            lower_bounds, upper_bounds = bounds(opens, closes, force_close, align)

        if curtail and not (force_close and force_break_close):
            indices = lower_bounds.argsort()
            lower_bounds.sort_values(inplace=True)
            upper_bounds = upper_bounds[indices]
            curtail_mask = upper_bounds > lower_bounds.shift(-1)
            if curtail_mask.any():
                upper_bounds[curtail_mask] = lower_bounds.shift(-1)[curtail_mask]

        return lower_bounds, upper_bounds

    # Fuzz tests for unexpected errors and return behaviour.

    @given(
        data=st.data(),
        force_close=st.booleans(),
        force_break_close=st.booleans(),
        align=st_align(),
        align_pm=st_align(),
    )
    @settings(deadline=None)
    def test_indices_fuzz(
        self,
        data,
        calendars_with_answers,
        force_close: bool,
        force_break_close: bool,
        align,
        align_pm,
        one_min,
    ):
        """Fuzz for unexpected errors and options behaviour.

        Expected errors tested for separately.

        'period' limited to avoid IndicesOverlapError.

        'start' and 'end' set to:
            be within calendar bounds.
            dates covering at least one session.
        """
        cal, ans = calendars_with_answers
        start, end = data.draw(self.st_start_end(ans))
        slc = ans.sessions.slice_indexer(start, end)
        has_break = ans.break_starts[slc].notna().any()

        closed_options = ["left", "neither", "right", "both"]
        if ans.sessions[slc].isin(ans.sessions_without_gap_after).any():
            closed_options = closed_options[:-1]  # lose "both" option
        closed = data.draw(st.sampled_from(closed_options))
        closed_right = closed in ["right", "both"]

        max_period = pd.Timedelta(1, "D") - one_min

        params_allow_overlap = closed_right and not (force_break_close and force_close)
        if params_allow_overlap:
            can_overlap = self.could_overlap(ans, slc, has_break)
        else:
            can_overlap = False

        if has_break and can_overlap:
            # filter out periods that will definitely overlap.
            max_period = (ans.break_ends[slc] - ans.opens[slc]).min()

        # guard against "neither" returning empty. Tested for under seprate test.
        if closed == "neither":
            if has_break:
                am_length = (ans.break_starts[slc] - ans.opens[slc]).min() - one_min
                pm_length = (ans.closes[slc] - ans.break_ends[slc]).min() - one_min
                max_period = min(max_period, am_length, pm_length)
            else:
                min_length = (ans.closes[slc] - ans.opens[slc]).min() - one_min
                max_period = min(max_period, min_length)

        period = data.draw(self.st_periods(maximum=max_period))

        if can_overlap:
            # assume no overlaps (i.e. reject test parameters if would overlap).
            op = operator.ge if closed == "both" else operator.gt
            if has_break:
                mask = ans.break_starts[slc].notna()
                overrun = self.evaluate_overrun(
                    ans.opens[slc][mask], ans.break_starts[slc][mask], period
                )
                break_duration = (ans.break_ends[slc] - ans.break_starts[slc]).dropna()
                assume(not op(overrun, break_duration).any())
            overrun = self.evaluate_overrun(ans.opens[slc], ans.closes[slc], period)
            sessions_gap = ans.opens[slc].shift(-1) - ans.closes[slc]
            assume(not op(overrun, sessions_gap).any())

        ti = m._TradingIndex(
            cal,
            start,
            end,
            period,
            closed,
            force_close,
            force_break_close,
            curtail_overlaps=False,
            ignore_breaks=False,
            align=align,
            align_pm=align_pm,
        )
        index = ti.trading_index()

        # Assertions

        assert isinstance(index, pd.DatetimeIndex)
        assert not index.empty

        lower_bounds, upper_bounds = self.sessions_bounds(
            ans, slc, period, closed, force_break_close, force_close, align, align_pm
        )

        assert lower_bounds.isin(index).all()
        assert upper_bounds.isin(index).all()

        # verify that all indices are within bounds of a session or subsession.
        bv = pd.Series(False, index)
        for lower_bound, upper_bound in zip(lower_bounds, upper_bounds):
            bv = bv | ((index >= lower_bound) & (index <= upper_bound))
        assert bv.all()

    @given(
        data=st.data(),
        force_break_close=st.booleans(),
        curtail=st.booleans(),
        align=st_align(),
        align_pm=st_align(),
    )
    @settings(deadline=None)
    def test_intervals_fuzz(
        self,
        data,
        calendars_with_answers,
        force_break_close: bool,
        curtail: bool,
        align: pd.Timedelta,
        align_pm: pd.Timedelta,
        one_min,
    ):
        """Fuzz for unexpected errors and options behaviour.

        Expected errors tested for separately.

        `period` limited to avoid IntervalsOverlapError.

        'start' and 'end' set to:
            be within calendar bounds.
            dates covering at least one session.
        """
        cal, ans = calendars_with_answers
        start, end = data.draw(self.st_start_end(ans))
        slc = ans.sessions.slice_indexer(start, end)
        has_break = ans.break_starts[slc].notna().any()

        force_close = data.draw(st.booleans())
        closed = data.draw(st.sampled_from(["left", "right"]))
        max_period = pd.Timedelta(1, "D") - one_min

        params_allow_overlap = not curtail and not (force_break_close and force_close)
        if params_allow_overlap:
            can_overlap = self.could_overlap(ans, slc, has_break)
        else:
            can_overlap = False

        if has_break and can_overlap:
            # filter out periods that will definitely overlap.
            max_period = (ans.break_ends[slc] - ans.opens[slc]).min()

        period = data.draw(self.st_periods(maximum=max_period))

        if can_overlap:
            # assume no overlaps
            if has_break:
                mask = ans.break_starts[slc].notna()
                overrun = self.evaluate_overrun(
                    ans.opens[slc][mask], ans.break_starts[slc][mask], period
                )
                break_duration = (ans.break_ends[slc] - ans.break_starts[slc]).dropna()
                assume(not (overrun > break_duration).any())
            overrun = self.evaluate_overrun(ans.opens[slc], ans.closes[slc], period)
            sessions_gap = ans.opens[slc].shift(-1) - ans.closes[slc]
            assume(not (overrun > sessions_gap).any())

        ti = m._TradingIndex(
            cal,
            start,
            end,
            period,
            closed,
            force_close,
            force_break_close,
            curtail,
            ignore_breaks=False,
            align=align,
            align_pm=align_pm,
        )
        index = ti.trading_index_intervals()

        # assertions

        assert isinstance(index, pd.IntervalIndex)
        assert not index.empty

        lower_bounds, upper_bounds = self.sessions_bounds(
            ans,
            slc,
            period,
            None,
            force_break_close,
            force_close,
            align,
            align_pm,
            curtail,
        )

        assert lower_bounds.isin(index.left).all()
        assert upper_bounds.isin(index.right).all()

        # verify that all intervals are within bounds of a session or subsession
        bv = pd.Series(False, index)
        for lower_bound, upper_bound in zip(lower_bounds, upper_bounds):
            bv = bv | ((index.left >= lower_bound) & (index.right <= upper_bound))

    @given(data=st.data(), calendar_name=st.sampled_from(["XLON", "XHKG"]))
    @settings(deadline=None)
    def test_for_empty_with_neither_fuzz(
        self, data, calendars, answers, calendar_name, one_min
    ):
        """Fuzz for specific condition that returns empty DatetimeIndex.

        Fuzz for expected empty DatetimeIndex when closed "neither" and
        period is longer than any session/subsession.
        """
        cal, ans = calendars[calendar_name], answers[calendar_name]
        start, end = data.draw(self.st_start_end(ans))
        slc = ans.sessions.slice_indexer(start, end)
        has_break = ans.break_starts[slc].notna().any()

        if has_break:
            max_am_length = (ans.break_starts[slc] - ans.opens[slc]).max()
            max_pm_length = (ans.closes[slc] - ans.break_ends[slc]).max()
            min_period = max(max_am_length, max_pm_length)
        else:
            min_period = (ans.closes[slc] - ans.opens[slc]).max()

        period = data.draw(self.st_periods(minimum=min_period))

        closed = "neither"
        forces = [False, False]

        ti = m._TradingIndex(
            cal, start, end, period, closed, *forces, False, False, one_min, one_min
        )
        index = ti.trading_index()
        assert index.empty

    @given(
        data=st.data(),
        intervals=st.booleans(),
        force_close=st.booleans(),
        force_break_close=st.booleans(),
        curtail_overlaps=st.booleans(),
    )
    @settings(deadline=None)
    def test_daily_fuzz(
        self,
        data,
        calendars_with_answers,
        intervals: bool,
        force_close: bool,
        force_break_close: bool,
        curtail_overlaps: bool,
    ):
        """Fuzz for unexpected errors and return behaviour."""
        cal, ans = calendars_with_answers

        if intervals:
            closed_options = ["left", "right"]
        else:
            closed_options = ["left", "right", "neither", "both"]
        closed = data.draw(st.sampled_from(closed_options))

        start, end = data.draw(self.st_start_end(ans))
        period = pd.Timedelta(1, "D")
        forces_and_curtails = [force_close, force_break_close, None, curtail_overlaps]

        index = cal.trading_index(
            start, end, period, intervals, closed, *forces_and_curtails, parse=False
        )
        assert isinstance(index, pd.DatetimeIndex)
        assert not index.empty
        pd.testing.assert_index_equal(index.normalize(), index)

    # Tests for expected errors.

    @pytest.mark.parametrize("name", ["XHKG", "24/7", "CMES"])
    @given(data=st.data(), closed=st.sampled_from(["right", "both"]))
    @settings(deadline=None)
    def test_overlap_error_fuzz(self, data, name, calendars, answers, closed, one_min):
        """Fuzz for expected IndicesOverlapError.

        NB. Test should exclude calendars, such as "XLON", for which
        indices cannot overlap. These are calendars where a
        session/subsession duration is less than the subsequent gap
        between that session/subsession and the next. Passing any slice of
        the answers for such a calendar to `could_overlap` would return
        False. That such calendars cannot have overlapping indices is
        verified by `test_indices_fuzz` and `test_intervals_fuzz` which
        place no restraints on the period that these calendars can be
        tested against (at least between 0 minutes and 1 day exclusive).
        """
        cal, ans = calendars[name], answers[name]
        start, end = data.draw(self.st_start_end(ans))
        slc = ans.sessions.slice_indexer(start, end)
        has_break = ans.break_starts[slc].notna().any()

        # filter out periods that will definitely not cause an overlap.
        if has_break:
            min_period = (ans.break_ends[slc] - ans.break_starts[slc]).min()
        else:
            min_period = (ans.opens.shift(-1)[slc] - ans.closes[slc]).min()

        period = data.draw(self.st_periods(minimum=max(one_min, min_period)))

        # assume overlaps (i.e. reject test parameters if does not overlap)
        op = operator.ge if closed == "both" else operator.gt
        if has_break:
            mask = ans.break_starts[slc].notna()
            overrun = self.evaluate_overrun(
                ans.opens[slc][mask], ans.break_starts[slc][mask], period
            )
            break_duration = (ans.break_ends[slc] - ans.break_starts[slc]).dropna()
            assume(op(overrun, break_duration).any())
        else:
            overrun = self.evaluate_overrun(ans.opens[slc], ans.closes[slc], period)
            sessions_gap = ans.opens[slc].shift(-1) - ans.closes[slc]
            assume(op(overrun, sessions_gap).any())

        ti = m._TradingIndex(
            cal,
            start,
            end,
            period,
            closed,
            force_close=False,
            force_break_close=False,
            curtail_overlaps=False,
            ignore_breaks=False,
            align=one_min,
            align_pm=one_min,
        )
        with pytest.raises(errors.IndicesOverlapError):
            ti.trading_index()

        if closed == "right":
            with pytest.raises(errors.IntervalsOverlapError):
                ti.trading_index_intervals()

    @pytest.fixture(params=[True, False])
    def curtail_all(self, request) -> abc.Iterator[bool]:
        """Parameterized fixture of all values for 'curtail_overlaps'."""
        yield request.param

    @pytest.fixture(scope="class")
    def cal_start_end(
        self, calendars
    ) -> abc.Iterator[tuple[ExchangeCalendar], pd.Timestamp, pd.Timestamp]:
        """(calendar, start, end) parameters for specific tests."""
        yield (
            calendars["XHKG"],
            pd.Timestamp("2018-01-01"),
            pd.Timestamp("2018-12-31"),
        )

    @pytest.fixture(params=itertools.product(("105T", "106T"), ("right", "both")))
    def ti_for_overlap(
        self, request, cal_start_end, curtail_all, one_min
    ) -> abc.Iterator[m._TradingIndex]:
        """_TradingIndex fixture against which to test for overlaps.

        '105T' is the edge case where last right indice of am subsession would
        coincide with first left indice of pm subsession.
        '106T' is one minute to the right of this.
        """
        cal, start, end = cal_start_end
        period, closed = request.param
        period = pd.Timedelta(period)
        yield m._TradingIndex(
            cal,
            start,
            end,
            period,
            closed,
            force_close=False,
            force_break_close=False,
            curtail_overlaps=curtail_all,
            ignore_breaks=False,
            align=one_min,
            align_pm=one_min,
        )

    def test_overlaps(self, ti_for_overlap, answers):
        """Test 'curtail_overlaps' and for overlaps against concrete parameters."""
        ti = ti_for_overlap
        period = pd.Timedelta(ti.interval_nanos)
        period_106 = period == pd.Timedelta("106T")

        if period_106 or ti.closed == "both":
            with pytest.raises(errors.IndicesOverlapError):
                ti.trading_index()

        if ti.closed == "both":
            return

        if not ti.curtail_overlaps and period_106:
            # won't raise on "105T" as right side of last interval of am
            # session won't clash on coinciding with left side of first
            # interval of pm session as one of these sides will always be
            # open (in this case the left side). NB can't close on both
            # sides.
            with pytest.raises(errors.IntervalsOverlapError):
                ti.trading_index_intervals()
        else:
            index = ti.trading_index_intervals()
            assert index.is_non_overlapping_monotonic
            assert index.right.isin(answers["XHKG"].break_ends).any()

    @pytest.fixture(params=("right", "both"))
    def ti_for_overlap_error_negative_case(
        self, request, cal_start_end, curtail_all, one_min
    ) -> abc.Iterator[m._TradingIndex]:
        """_TradingIndex fixture against which to test for no overlaps.

        104T is the edge case, one minute short of coinciding with pm subsession open.
        """
        cal, start, end = cal_start_end
        period, closed = pd.Timedelta("104T"), request.param
        yield m._TradingIndex(
            cal,
            start,
            end,
            period,
            closed,
            force_close=False,
            force_break_close=False,
            curtail_overlaps=curtail_all,
            ignore_breaks=True,
            align=one_min,
            align_pm=one_min,
        )

    def test_overlaps_2(self, ti_for_overlap_error_negative_case):
        """Test for no overlaps against concrete edge case."""
        ti = ti_for_overlap_error_negative_case
        index = ti.trading_index()
        assert isinstance(index, pd.DatetimeIndex)
        if ti.closed == "right":
            index = ti.trading_index_intervals()
            assert isinstance(index, pd.IntervalIndex)
            assert index.is_non_overlapping_monotonic

    # Tests for other options

    def test_force(self, cal_start_end):
        """Verify `force` option overrides `force_close` and `force_break_close`."""
        cal, start, end = cal_start_end
        kwargs = dict(start=start, end=end, period="1H", intervals=True)

        expected_true = cal.trading_index(
            **kwargs, force_close=True, force_break_close=True
        )
        expected_false = cal.trading_index(
            **kwargs, force_close=False, force_break_close=False
        )

        force_combos = itertools.product([True, False], repeat=2)
        for force_close, force_break_close in force_combos:
            rtrn_true = cal.trading_index(
                **kwargs,
                force_close=force_close,
                force_break_close=force_break_close,
                force=True,
            )

            assert_index_equal(rtrn_true, expected_true)

            rtrn_false = cal.trading_index(
                **kwargs,
                force_close=force_close,
                force_break_close=force_break_close,
                force=False,
            )

            assert_index_equal(rtrn_false, expected_false)

    def test_ignore_breaks(self, cal_start_end):
        """Verify effect of ignore_breaks option."""
        cal, start, end = cal_start_end
        assert cal.sessions_has_break(start, end)
        kwargs = dict(start=start, end=end, period="1H", intervals=True)

        # verify a difference
        index_false = cal.trading_index(**kwargs, ignore_breaks=False)
        index_true = cal.trading_index(**kwargs, ignore_breaks=True)
        with pytest.raises(AssertionError):
            assert_index_equal(index_false, index_true)

        # create an equivalent calendar without breaks
        delta = pd.Timedelta(10, "D")
        start_ = start - delta
        end_ = end + delta

        cal_amended = calendar_utils._default_calendar_factories[cal.name](start_, end_)
        cal_amended.break_starts_nanos[:] = pd.NaT.value
        cal_amended.break_ends_nanos[:] = pd.NaT.value
        cal_amended.schedule.loc[:, "break_start"] = pd.NaT
        cal_amended.schedule.loc[:, "break_end"] = pd.NaT

        # verify amended calendar returns as original with breaks ignored
        rtrn = cal_amended.trading_index(**kwargs, ignore_breaks=False)
        assert_index_equal(rtrn, index_true)

    @pytest.fixture(scope="class")
    def cal_with_ans_align(self) -> abc.Iterator[tuple[ExchangeCalendar, Answers]]:
        """Calendar with open and break_end times to test align options."""
        cal_name = "TEST"

        # NOTE Changing the timings of this test calendar class also requires
        # changing the corresponding test.csv answers file in the resources dir.
        class TESTCal(XTAEExchangeCalendar):
            name = cal_name
            break_start_times = ((None, time(15, 58)),)
            break_end_times = ((None, time(17, 28)),)
            close_times = ((None, time(19, 15)),)

        ans = Answers(cal_name, "left")
        cal = TESTCal(start=ans.first_session, end=ans.last_session)
        yield cal, ans

    @pytest.fixture(scope="class")
    def dates_align(
        self, cal_with_ans_align
    ) -> abc.Iterator[tuple[pd.Timestamp, pd.Timestamp]]:
        """Sessions over which to test effect of align parameters.

        Two contiguous sessions with times as asserted.
        """
        _, ans = cal_with_ans_align
        from_, to = pd.Timestamp("2020-12-10"), pd.Timestamp("2020-12-13")
        # assert assumed open / close times
        assert ans.opens[from_].time() == time(7, 59)
        assert ans.break_starts[from_].time() == time(13, 58)
        assert ans.break_ends[from_].time() == time(15, 28)
        assert ans.closes[from_].time() == time(17, 15)
        assert ans.opens[to].time() == time(7, 59)
        assert ans.break_starts[to] is ans.break_ends[to] is pd.NaT
        assert ans.closes[to].time() == time(13, 40)
        yield from_, to

    @given(
        data=st.data(),
        force_close=st.booleans(),
        force_break_close=st.booleans(),
        closed=st.sampled_from(["left", "right", "both", "neither"]),
        ignore_breaks=st.booleans(),
    )
    def test_align(
        self,
        data,
        cal_with_ans_align,
        dates_align,
        closed,
        force_close,
        force_break_close,
        ignore_breaks,
        one_min,
    ):
        """Test `align` option.

        Additional concrete test to verify effect of `align` and `align_pm' on
        'alignable' calendar. (Effect of these options is principally tested
        by `test_indices_fuzz` and `test_intervals_fuzz`.)
        """
        cal, ans = cal_with_ans_align
        from_, to = dates_align
        aligned_start_times = {
            "-1T": (time(7, 59), time(15, 28)),
            "-2T": (time(7, 58), time(15, 28)),
            "-3T": (time(7, 57), time(15, 27)),
            "-5T": (time(7, 55), time(15, 25)),
            "-15T": (time(7, 45), time(15, 15)),
            "-20T": (time(7, 40), time(15, 20)),
            "-30T": (time(7, 30), time(15)),
            "-60T": (time(7), time(15)),
            "1T": (time(7, 59), time(15, 28)),
            "2T": (time(8), time(15, 28)),
            "3T": (time(8), time(15, 30)),
            "5T": (time(8), time(15, 30)),
            "15T": (time(8), time(15, 30)),
            "20T": (time(8), time(15, 40)),
            "30T": (time(8), time(15, 30)),
            "60T": (time(8), time(16)),
        }
        alignments = list(aligned_start_times.keys())
        align = data.draw(st.sampled_from(alignments))
        align_pm = data.draw(st.one_of([st.sampled_from(alignments), st.booleans()]))
        period = data.draw(self.st_periods(maximum=pd.Timedelta(1, "H")))

        open_pm = ans.break_ends[from_]
        closes = (ans.break_starts[from_], ans.closes[from_], ans.closes[to])
        closes_ignore_breaks = (ans.closes[from_], ans.closes[to])

        closed_left = closed in ["left", "both"]
        closed_right = closed in ["right", "both"]
        tz = pytz.UTC

        def create_expected(
            starts: list[pd.Timestamp],
            ends: list[pd.Timestamp],
            period: pd.Timedelta,
            forces: list[bool],
        ) -> pd.DatetimeIndex:
            index_ = pd.DatetimeIndex([], tz=tz)
            for start, end, force in zip(starts, ends, forces):
                index = pd.date_range(start, end, freq=period, tz=tz)
                if not closed_left:
                    index = index[1:]
                if closed_right and end != index[-1]:
                    index = index.insert(len(index), index[-1] + period)
                if not closed_right and end == index[-1]:
                    index = index[:-1]
                if force and index[-1] > end:
                    index = index[:-1].insert(len(index) - 1, end)
                index_ = index_.union(index)
            return index_

        def create_expected_intervals(
            starts: list[pd.Timestamp],
            ends: list[pd.Timestamp],
            period: pd.Timedelta,
            forces: list[bool],
        ) -> pd.DatetimeIndex:
            left_ = pd.DatetimeIndex([], tz=tz)
            right_ = pd.DatetimeIndex([], tz=tz)
            for start, end, force in zip(starts, ends, forces):
                left = pd.date_range(start, end - one_min, freq=period, tz=tz)
                right = left + period
                if force and right[-1] > end:
                    right = right[:-1].insert(len(right) - 1, end)
                left_ = left_.union(left)
                right_ = right_.union(right)
            return pd.IntervalIndex.from_arrays(left_, right_, closed)

        combine = datetime.datetime.combine

        def get_start(date: pd.Timestamp, tm: time):
            return pd.Timestamp(combine(date.date(), tm), tz=pytz.UTC)

        aligned_time_am, _ = aligned_start_times[align]
        starts = [get_start(from_, aligned_time_am)]
        if not ignore_breaks:
            if align_pm:
                alignment_pm = align if align_pm is True else align_pm
                _, aligned_time_pm = aligned_start_times[alignment_pm]
                start = get_start(from_, aligned_time_pm)
            else:
                start = open_pm
            starts.append(start)
        starts.append(get_start(to, aligned_time_am))
        ends = closes_ignore_breaks if ignore_breaks else closes
        forces = (
            [force_close, force_close]
            if ignore_breaks
            else [force_break_close, force_close, force_close]
        )

        args = (from_, to, period)
        kwargs = dict(
            closed=closed,
            align=align,
            align_pm=align_pm,
            ignore_breaks=ignore_breaks,
            force_close=force_close,
            force_break_close=force_break_close,
        )

        intervals = False
        expected = create_expected(starts, ends, period, forces)
        rtrn = cal.trading_index(*args, intervals=intervals, **kwargs)
        assert_index_equal(rtrn, expected)
        # test passing start and end as times as opposed to sessions...
        alt_args = (expected[0] + one_min, expected[-1] - one_min, period)
        rtrn = cal.trading_index(*alt_args, intervals=intervals, **kwargs)
        assert_index_equal(rtrn, expected[1:-1])

        intervals = True
        if closed not in ["left", "right"]:
            return
        expected = create_expected_intervals(starts, ends, period, forces)
        rtrn = cal.trading_index(*args, intervals=intervals, **kwargs)
        # test passing start and end as times as opposed to sessions...
        alt_args = (expected[0].left + one_min, expected[-1].right - one_min, period)
        rtrn = cal.trading_index(*alt_args, intervals=intervals, **kwargs)
        assert_index_equal(rtrn, expected[1:-1])

    def test_align_overlap(self, cal_with_ans_align, dates_align, one_min):
        """Test align options can cause overlap error.

        Tests concrete case raises overlap errors due to alignment
        regardless that period is shorter than the break.
        """
        cal, _ = cal_with_ans_align

        kwargs = dict(closed="right", align="-5T")
        align_pm = "-1H"

        intervals = True
        # assert returns at edge
        period = pd.Timedelta(85, "T")
        rtrn = cal.trading_index(
            *dates_align, period, intervals=intervals, align_pm=align_pm, **kwargs
        )
        limit = pd.Timestamp(
            datetime.datetime.combine(dates_align[0], time(15)), tz=pytz.UTC
        )
        assert limit in rtrn.right

        # assert raises beyond edge
        period += one_min
        with pytest.raises(errors.IntervalsOverlapError):
            cal.trading_index(
                *dates_align, period, intervals=intervals, align_pm=align_pm, **kwargs
            )

        # assert returns beyond edge if curtail
        rtrn = cal.trading_index(
            *dates_align,
            period,
            intervals=intervals,
            align_pm=align_pm,
            curtail_overlaps=True,
            **kwargs,
        )
        assert not rtrn.empty

        # assert returns beyond edge if no pm alignment
        rtrn = cal.trading_index(
            *dates_align, period, intervals=intervals, align_pm=False, **kwargs
        )
        assert not rtrn.empty

        intervals = False
        # assert returns at edge
        period = pd.Timedelta(85, "T")
        rtrn = cal.trading_index(
            *dates_align, period, intervals=intervals, align_pm=align_pm, **kwargs
        )
        assert not rtrn.empty

        # assert raises beyond edge
        period += one_min
        with pytest.raises(errors.IndicesOverlapError):
            cal.trading_index(
                *dates_align, period, intervals=intervals, align_pm=align_pm, **kwargs
            )

        # assert returns beyond edge if no pm alignment
        rtrn = cal.trading_index(
            *dates_align, period, intervals=intervals, align_pm=False, **kwargs
        )
        assert not rtrn.empty

    def test_start_end_times(self, one_min, calendars):
        """Test effect of passing start and/or end as a time.

        Tests passing start / end as combinations of dates and/or times.

        Tests by comparing return with subset of return for start and end
        as sessions.

        Tests return with `intervals` as True (IntervalIndex) and False
        (DatetimeIndex). With `intervals` as False tests for all `closed`
        options.
        """
        cal = calendars["XHKG"]

        # Define a start session and end session as sessions of standard length
        start_s = pd.Timestamp("2021-12-06")
        end_s = pd.Timestamp("2021-12-20")

        # assert of standard length
        standard_length = pd.Timedelta(hours=6, minutes=30)
        start_s_open, start_s_close = cal.session_open_close(start_s)
        assert start_s_close - start_s_open == standard_length
        end_s_open, end_s_close = cal.session_open_close(end_s)
        assert end_s_close - end_s_open == standard_length

        f = cal.trading_index

        # Note: when intervals = False the return will include the indice coinciding
        # with `start` and `end` even if the period that indice represents falls,
        # respectively, before `start` or after `end`

        def assertions(
            starts: list[
                tuple[
                    pd.Timestamp,
                    int | None,
                    int | None,
                    int | None,
                    int | None,
                    int | None,
                ]
            ],
            ends: list[
                tuple[
                    pd.Timestamp,
                    int | None,
                    int | None,
                    int | None,
                    int | None,
                    int | None,
                ]
            ],
            period: pd.Timedelta | str,
            force: bool,
            ignore_breaks: bool,
            curtail_overlaps: bool = False,
        ):
            """Assert returns slice of return for sessions.

            Parameters
            ----------
            starts: list of tuple (see method signature) of:
                [0] value to pass as start.
                Other items define the start of slice of subset when start is [0] and:
                [1] intervals is True.
                [2] intervals is False and 'closed' is "left".
                [3] intervals is False and 'closed' is "right".
                [4] intervals is False and 'closed' is "both".
                [5] intervals is False and 'closed' is "neither".

            ends: list of tuple (see method signature) of:
                [0] value to pass as end.
                Other items define the end of slice of subset when end is [0] and:
                [1] intervals is True.
                [2] intervals is False and 'closed' is "left".
                [3] intervals is False and 'closed' is "right".
                [4] intervals is False and 'closed' is "both".
                [5] intervals is False and 'closed' is "neither".

            All other parameters will be passed thorugh to `trading_index`.
            """
            args_dates = (start_s, end_s, period)
            kwargs = dict(
                force=force,
                ignore_breaks=ignore_breaks,
                curtail_overlaps=curtail_overlaps,
            )
            for (start, slc_start, ssl, ssr, ssb, ssn), (
                end,
                slc_end,
                sel,
                ser,
                seb,
                sen,
            ) in itertools.product(starts, ends):
                args = (start, end, period)

                # verify for intervals index
                intervals = True
                index_dates = f(*args_dates, intervals, **kwargs)
                rtrn = f(*args, intervals=intervals, **kwargs)
                assert_index_equal(rtrn, index_dates[slc_start:slc_end])

                # verify for datetime index
                intervals = False
                closed = "left"
                rtrn = f(*args, intervals=intervals, closed=closed, **kwargs)
                index_dates = f(*args_dates, intervals, closed=closed, **kwargs)
                assert_index_equal(rtrn, index_dates[ssl:sel])

                closed = "right"
                rtrn = f(*args, intervals=intervals, closed=closed, **kwargs)
                index_dates = f(*args_dates, intervals, closed=closed, **kwargs)
                assert_index_equal(rtrn, index_dates[ssr:ser])

                closed = "both"
                rtrn = f(*args, intervals=intervals, closed=closed, **kwargs)
                index_dates = f(*args_dates, intervals, closed=closed, **kwargs)
                assert_index_equal(rtrn, index_dates[ssb:seb])

                closed = "neither"
                rtrn = f(*args, intervals=intervals, closed=closed, **kwargs)
                index_dates = f(*args_dates, intervals, closed=closed, **kwargs)
                assert_index_equal(rtrn, index_dates[ssn:sen])

        force, ignore_breaks = False, True

        period = one_min
        delta = period * 22

        starts = [
            (start_s, None, None, None, None, None),
            (start_s_open, None, None, None, None, None),
            (start_s_open + delta, 22, 22, 21, 22, 21),
            (start_s_open + delta - one_min, 21, 21, 20, 21, 20),
            (start_s_open + delta + one_min, 23, 23, 22, 23, 22),
        ]
        ends = [
            (end_s, None, None, None, None, None),
            (end_s_close, None, None, None, None, None),
            (end_s_close - delta, -22, -21, -22, -22, -21),
            (end_s_close - delta + one_min, -21, -20, -21, -21, -20),
            (end_s_close - delta - one_min, -23, -22, -23, -23, -22),
        ]

        assertions(starts, ends, period, force, ignore_breaks)

        period = pd.Timedelta(5, "T")
        delta = period * 2

        starts = [
            (start_s, None, None, None, None, None),
            (start_s_open, None, None, None, None, None),
            (start_s_open + delta, 2, 2, 1, 2, 1),
            (start_s_open + delta - one_min, 2, 2, 1, 2, 1),
            (start_s_open + delta + one_min, 3, 3, 2, 3, 2),
        ]
        ends = [
            (end_s, None, None, None, None, None),
            (end_s_close, None, None, None, None, None),
            (end_s_close - delta, -2, -1, -2, -2, -1),
            (end_s_close - delta + one_min, -2, -1, -2, -2, -1),
            (end_s_close - delta - one_min, -3, -2, -3, -3, -2),
        ]

        assertions(starts, ends, period, force, ignore_breaks)

        period = pd.Timedelta(1, "H")
        end_s_open = cal.session_open(end_s)

        # ignoring breaks...
        # assert assumption that end unaligned by 30mins
        assert (end_s_close - end_s_open) % period == pd.Timedelta(30, "T")

        end_s_aligned_post_close = end_s_close + pd.Timedelta(30, "T")
        end_s_break_end = cal.session_break_end(end_s)
        # assert assumption that pm session 3H duration
        assert end_s_close - end_s_break_end == pd.Timedelta(3, "H")

        starts = [
            (start_s, None, None, None, None, None),
            (start_s_open, None, None, None, None, None),
            (start_s_open + period, 1, 1, None, 1, None),
            (start_s_open + period - one_min, 1, 1, None, 1, None),
            (start_s_open + period + one_min, 2, 2, 1, 2, 1),
        ]
        ends = [
            (end_s, None, None, None, None, None),
            (end_s_aligned_post_close, None, None, None, None, None),
            (end_s_aligned_post_close + one_min, None, None, None, None, None),
            (end_s_aligned_post_close - one_min, -1, None, -1, -1, None),
            (end_s_close, -1, None, -1, -1, None),
            (end_s_aligned_post_close - period + one_min, -1, None, -1, -1, None),
            (end_s_aligned_post_close - period, -1, None, -1, -1, None),
            (end_s_aligned_post_close - period - one_min, -2, -1, -2, -2, -1),
            (end_s_break_end, -4, -3, -4, -4, -3),
            (end_s_break_end + pd.Timedelta(30, "T"), -3, -2, -3, -3, -2),
            (end_s_break_end + pd.Timedelta(29, "T"), -4, -3, -4, -4, -3),
            (end_s_break_end - pd.Timedelta(30, "T"), -4, -3, -4, -4, -3),
            (end_s_break_end - pd.Timedelta(31, "T"), -5, -4, -5, -5, -4),
        ]

        assertions(starts, ends, period, force, ignore_breaks)

        # verify effect of force
        starts = [
            (start_s, None, None, None, None, None),
            (start_s_open, None, None, None, None, None),
            (start_s_open + period, 1, 1, None, 1, None),
            (start_s_open + period - one_min, 1, 1, None, 1, None),
            (start_s_open + period + one_min, 2, 2, 1, 2, 1),
        ]
        ends = [
            (end_s, None, None, None, None, None),
            (end_s_aligned_post_close, None, None, None, None, None),
            (end_s_close, None, None, None, None, None),
            (end_s_close - one_min, -1, None, -1, -1, None),
            (end_s_close - pd.Timedelta(30, "T"), -1, None, -1, -1, None),
            (end_s_close - pd.Timedelta(31, "T"), -2, -1, -2, -2, -1),
            # break end as before...
            (end_s_break_end, -4, -3, -4, -4, -3),
            (end_s_break_end + pd.Timedelta(30, "T"), -3, -2, -3, -3, -2),
            (end_s_break_end + pd.Timedelta(29, "T"), -4, -3, -4, -4, -3),
            (end_s_break_end - pd.Timedelta(30, "T"), -4, -3, -4, -4, -3),
            (end_s_break_end - pd.Timedelta(31, "T"), -5, -4, -5, -5, -4),
        ]

        force = True
        assertions(starts, ends, period, force, ignore_breaks)

        # ACKNOWLEDGING BREAKS

        end_s_break_start = cal.session_break_start(end_s)
        # assert assumption that break start unaligned by 30mins
        assert (end_s_break_start - end_s_open) % period == pd.Timedelta(30, "T")

        starts = [
            (start_s, None, None, None, None, None),
            (start_s_open, None, None, None, None, None),
            (start_s_open + period, 1, 1, None, 1, None),
            (start_s_open + period - one_min, 1, 1, None, 1, None),
            (start_s_open + period + one_min, 2, 2, 1, 2, 1),
        ]
        ends = [
            (end_s, None, None, None, None, None),
            (end_s_aligned_post_close, None, None, None, None, None),
            (end_s_close, None, None, None, None, None),
            (end_s_close - one_min, -1, None, -1, -1, None),
            (end_s_close - period, -1, None, -1, -1, None),
            (end_s_close - period - one_min, -2, -1, -2, -2, -1),
            (end_s_break_end, -3, -2, -3, -3, -2),
            (end_s_break_end + one_min, -3, -2, -3, -3, -2),
            (end_s_break_end - one_min, -3, -3, -3, -4, -2),
            (end_s_break_start, -4, -3, -4, -5, -2),
            (end_s_break_start + pd.Timedelta(30, "T"), -3, -3, -3, -4, -2),
            (end_s_break_start + pd.Timedelta(29, "T"), -4, -3, -4, -5, -2),
            (end_s_break_start - pd.Timedelta(30, "T"), -4, -3, -4, -5, -2),
            (end_s_break_start - pd.Timedelta(31, "T"), -5, -4, -5, -6, -3),
        ]

        force, ignore_breaks = False, False
        # expected = expected_index(interval, force, ignore_breaks)
        assertions(starts, ends, period, force, ignore_breaks)

        # verifying effect of force when acknowledging breaks

        starts = [
            (start_s, None, None, None, None, None),
            (start_s_open, None, None, None, None, None),
            (start_s_open + period, 1, 1, None, 1, None),
            (start_s_open + period - one_min, 1, 1, None, 1, None),
            (start_s_open + period + one_min, 2, 2, 1, 2, 1),
        ]
        ends = [
            (end_s, None, None, None, None, None),
            (end_s_aligned_post_close, None, None, None, None, None),
            # end_s_close and end_s_break_end as before
            (end_s_close, None, None, None, None, None),
            (end_s_close - one_min, -1, None, -1, -1, None),
            (end_s_close - period, -1, None, -1, -1, None),
            (end_s_close - period - one_min, -2, -1, -2, -2, -1),
            (end_s_break_end, -3, -2, -3, -3, -2),
            (end_s_break_end + one_min, -3, -2, -3, -3, -2),
            (end_s_break_end - one_min, -3, -3, -3, -4, -2),
            # end_s_break_start affected by force
            (end_s_break_start, -3, -3, -3, -4, -2),
            (end_s_break_start - one_min, -4, -3, -4, -5, -2),
            (end_s_break_start - pd.Timedelta(30, "T"), -4, -3, -4, -5, -2),
            (end_s_break_start - pd.Timedelta(31, "T"), -5, -4, -5, -6, -3),
        ]

        force, ignore_breaks = True, False
        assertions(starts, ends, period, force, ignore_breaks)

    # PARSING TESTS

    def test_parsing_errors(self, cal_start_end):
        cal, start, end = cal_start_end
        error_msg = (
            "`period` cannot be greater than one day although received as"
            f" '{pd.Timedelta('2d')}'."
        )
        with pytest.raises(ValueError, match=error_msg):
            cal.trading_index(start, end, "2d", parse=False)

        error_msg = "If `intervals` is True then `closed` cannot be 'neither'."
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            cal.trading_index(
                start, end, "20T", intervals=True, closed="neither", parse=False
            )

        error_msg = "If `intervals` is True then `closed` cannot be 'both'."
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            cal.trading_index(
                start, end, "20T", intervals=True, closed="both", parse=False
            )

        # Verify raises error if period "1D" and start or end not passed as a date.
        start = pd.Timestamp("2018-05-01", tz=pytz.UTC)
        end = pd.Timestamp("2018-05-31")
        with pytest.raises(ValueError, match="a Date must be timezone naive"):
            cal.trading_index(start, end, "1D")

        start = pd.Timestamp("2018-05-01 00:01")
        with pytest.raises(
            ValueError, match="a Date must have a time component of 00:00"
        ):
            cal.trading_index(start, end, "1D")

        # verify raises wtih invalid values for `period`
        invalid_str = "X"
        error_msg = (
            f"`period` receieved as '{invalid_str}' although takes type"
            " 'pd.Timedelta' or a 'str' that is valid as a single input"
            " to 'pd.Timedelta'. Examples of valid input: pd.Timestamp('15T'),"
            " '15min', '15T', '1H', '4h', '1d', '5s', 500ms'."
        )
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            cal.trading_index(start, end, invalid_str)

        invalid_value = pd.Timedelta(1441, "T")
        error_msg = re.escape(
            "`period` cannot be greater than one day although received as"
            f" '{invalid_value}'."
        )
        with pytest.raises(ValueError, match=error_msg):
            cal.trading_index(start, end, invalid_value)

        # verify raises wtih invalid values for `align` and `align_pm`
        error_msg = (
            f"`align` receieved as '{invalid_str}' although takes type"
            f" 'pd.Timedelta' or a 'str' that is valid as a single input"
            " to 'pd.Timedelta'. Examples of valid input: pd.Timestamp('5T'),"
            " '5min', '5T', pd.Timedelta('-5T'), '-5min', '-5T'."
        )
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            cal.trading_index(start, end, "1h", align=invalid_str)

        error_msg = (
            f"`align_pm` receieved as '{invalid_str}' although takes type bool,"
            f" 'pd.Timedelta' or a 'str' that is valid as a single input"
            " to 'pd.Timedelta'. Examples of valid input: pd.Timestamp('5T'),"
            " '5min', '5T', pd.Timedelta('-5T'), '-5min', '-5T'."
        )
        with pytest.raises(ValueError, match=re.escape(error_msg)):
            cal.trading_index(start, end, "1H", align="5T", align_pm=invalid_str)

        invalid_values = [pd.Timedelta(7, "T"), pd.Timedelta(0), "0T"]
        for value in invalid_values:
            error_msg_end = (
                f" must be factor of 1H although received '{pd.Timedelta(value)}'."
            )
            with pytest.raises(ValueError, match=re.escape("`align`" + error_msg_end)):
                cal.trading_index(start, end, "1H", align=value)

            with pytest.raises(
                ValueError, match=re.escape("`align_pm`" + error_msg_end)
            ):
                cal.trading_index(start, end, "1H", align="5T", align_pm=value)

        invalid_minute_fractions = [3, pd.Timedelta(3600, "ms"), 3.6, "3s"]
        for value in invalid_minute_fractions:
            error_msg_end = (
                " cannot include a fraction of a minute although received "
                f"'{pd.Timedelta(value)}'."
            )
            with pytest.raises(ValueError, match=re.escape("`align`" + error_msg_end)):
                cal.trading_index(start, end, "1H", align=value)

            with pytest.raises(
                ValueError, match=re.escape("`align_pm`" + error_msg_end)
            ):
                cal.trading_index(start, end, "1H", align="5T", align_pm=value)
